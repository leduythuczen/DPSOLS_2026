import json, os

def get_design_key():
    from parameter import DESIGN_PATH
    base = os.path.basename(DESIGN_PATH)
    return os.path.splitext(base)[0]  # "adder" from "adder.blif"

DESIGN_KEY = get_design_key()
CACHE_FILE = f"logs/qor_cache_{DESIGN_KEY}.json"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cached_qor = json.load(f)
else:
    cached_qor = {}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(cached_qor, f, indent=2)

