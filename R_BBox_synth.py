import subprocess
import re
from parameter import ABC_LIB_PATH
from lookup_seq import cached_qor, save_cache

# Custom ABC action space (from the table you sent)
COMMAND_LOOKUP = {
    "0000": "&st",
    "0001": "&blut",
    "0010": "&b",
    "0011": "&dsdb",
    "0100": "&sopb",
    "0101": "&if -g",
    "0110": "&if -y",
    "0111": "&dc2",
    "1000": "&dch",
    "1001": "&kf",
    "1010": "&jf",
    "1011": "&mf",
    "1100": "&lf",
    "1101": "&if",
    "1110": "&speedup",
    "1111": "&mfs",  # you can add &satlut as a 5th-bit option if needed
}

ref_lut = None
ref_levels = None

def decode_command(command_4bit):
    return COMMAND_LOOKUP.get(command_4bit, "")

def parse_stats(output):
    try:
        text = output.decode("utf-8")
        for line in reversed(text.splitlines()):
            if 'lev' in line and 'nd' in line:
                levels = int(re.search(r'lev\s*=\s*(\d+)', line).group(1))
                lut = int(re.search(r'nd\s*=\s*(\d+)', line).group(1))
                return levels, lut
        print("[ERROR] 'lev' and 'nd' not found.")
        return -1, -1
    except Exception as e:
        print(f"[PARSE ERROR] {e}")
        return -1, -1

def get_QoR(command_string, design_path, qor_mode="combined", verbose=True):
    global ref_lut, ref_levels

    if command_string in cached_qor:
        return cached_qor[command_string]

    base_cmd = f"read_blif {design_path}; &get "
    logic_sequence = ""

    for i in range(0, len(command_string), 4):
        bin_chunk = command_string[i:i+4]
        abc_cmd = decode_command(bin_chunk)
        if abc_cmd:
            logic_sequence += abc_cmd + "; "

    abc_script = base_cmd + logic_sequence + "if -v -K 6; print_stats;"

    if verbose:
        print("[ABC RUN] Evaluating:\n", abc_script)

    try:
        output = subprocess.check_output(["yosys-abc", "-c", abc_script])
        levels, lut = parse_stats(output)
        if levels == -1 or lut == -1:
            return -1

        if ref_lut is None or ref_levels is None:
            print("Calculating Reference QoR...")
            ref_cmd = (
                base_cmd +
                "&blut; &sopb; &if -g; &dch; &lf; if -v -K 6; print_stats;"
            )
            ref_out = subprocess.check_output(["yosys-abc", "-c", ref_cmd])
            ref_levels, ref_lut = parse_stats(ref_out)

        if ref_lut <= 0 or ref_levels <= 0:
            return -1

        if qor_mode == "lut":
            QoR = lut / ref_lut
        elif qor_mode == "level":
            QoR = levels / ref_levels
        else:
            QoR = (lut / ref_lut) + (levels / ref_levels)

        cached_qor[command_string] = QoR
        save_cache()

        if verbose:
            print(f"[QoR {qor_mode}] LUT={lut}/{ref_lut}, Levels={levels}/{ref_levels} → QoR={QoR:.4f}")

        return QoR

    except subprocess.CalledProcessError as e:
        print("[ABC ERROR]", e.output.decode())
        return -1
