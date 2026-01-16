import subprocess
import re
from parameter import ABC_LIB_PATH
from lookup_seq import cached_qor, save_cache
#command dictionary mapping 4-bit codes to ABC commands
#11010001110001011101010100010101110001001010110001110011101100111000000011110010#
COMMAND_LOOKUP = {
    "0000": "rewrite",
    "0001": "rewrite -z",
    "0010": "refactor",
    "0011": "refactor -z",
    "0100": "resub",
    "0101": "resub -z",
    "0110": "balance",
    "0111": "ifraig",
    "1000": "rewrite", 
    "1001": "refactor -z",
    "1010": "rewrite -z",
    "1011": "balance",
    "1100": "dfraig",
    "1101": "&get -n; &sopb; &put",
    "1110": "&get -n; &blut; &put", 
    "1111": "&get -n; &dsdb; &put",
}

ref_lut = None
ref_levels = None
def decode_command(command_4bit):
    """Decode a 4-bit string into its corresponding ABC command."""
    return COMMAND_LOOKUP.get(command_4bit, "")


def parse_stats(output):
    """Extract LUT and level counts from ABC output."""
    try:
        text = output.decode("utf-8")
        for line in reversed(text.splitlines()):
            if 'lev' in line and 'nd' in line:
                levels = int(re.search(r'lev\s*=\s*(\d+)', line).group(1))
                lut = int(re.search(r'nd\s*=\s*(\d+)', line).group(1))
                return levels, lut
        print("[ERROR] Could not find 'lev' and 'nd' in ABC output.")
        print(">>> ABC Output (tail):", "\n".join(text.splitlines()[-5:]))
        return -1, -1
    except Exception as e:
        print(f"[EXCEPTION] Failed to parse stats: {e}")
        return -1, -1


def get_QoR(command_string, design_path, qor_mode="combined", verbose=0):
    """Evaluate the quality of a synthesis sequence."""
    global ref_lut, ref_levels

    # Check the cache first
    if command_string in cached_qor:
       # print("I")
        return cached_qor[command_string]
   
    # Build the ABC command sequence
#    base_cmd = f"read_blif {design_path}; read {ABC_LIB_PATH}; strash; "
    base_cmd = f"read_blif {design_path}; strash; "    
    logic_sequence = ""

    for i in range(0, len(command_string), 4):
        bin_chunk = command_string[i:i+4]
        abc_cmd = decode_command(bin_chunk)
        if abc_cmd:
            logic_sequence += abc_cmd + "; "

    abc_script = base_cmd + logic_sequence + "if -K 6; print_stats;"
#    abc_script = base_cmd + logic_sequence + "if -K 6; print_stats;"

    if verbose:
        print("[ABC RUN] Evaluating:\n", abc_script)

    try:
        output = subprocess.check_output(["yosys-abc", "-c", abc_script])
        levels, lut = parse_stats(output)
        if levels == -1 or lut == -1:
            return -1

        # Get reference QoR once
        if ref_lut is None or ref_levels is None:
            print("Calculating Reference QoR...")
            ref_cmd = (
                base_cmd +
#                "balance; rewrite; refactor; balance; rewrite; rewrite -z; "
#                "balance; refactor -z; rewrite -z; balance; if -K 6; print_stats;"
                "alias; resyn2; if -K 6; print_stats;"
#                "balance; refactor -z; rewrite -z; balance; if -K 6; print_stats;"
            )
            ref_out = subprocess.check_output(["yosys-abc", "-c", ref_cmd])
            ref_levels, ref_lut = parse_stats(ref_out)
            print(f"ref_lut = {ref_lut:.4f}/ ref_levels = {ref_levels:.4f}")

        if ref_lut <= 0 or ref_levels <= 0:
            return -1

        # Calculate normalized QoR
        if qor_mode == "lut":
            QoR = lut / ref_lut
        elif qor_mode == "level":
            QoR = levels / ref_levels
        else:
            QoR = (lut / ref_lut) + (levels / ref_levels) 

        # Save result in lookup
        cached_qor[command_string] = QoR
        save_cache()

        if verbose:
            print(f"=======[QoR mode={qor_mode}] LUT={lut}/{ref_lut}, Levels={levels}/{ref_levels} → QoR={QoR:.4f}, improve {((2.0-QoR)*50):.1f}")

        return QoR

    except subprocess.CalledProcessError as e:
        print("[ABC ERROR] Failed subprocess:")
        print(e.output.decode())
        return -1

