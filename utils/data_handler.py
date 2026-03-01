import json
import os

DATA_FILE = "candidates.json"


def mask_phone(phone):
    return phone[:5] + "*****"


def save_candidate(data):

    # If file doesn't exist OR is empty → initialize it
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

    # Now safely read
    with open(DATA_FILE, "r") as f:
        try:
            existing = json.load(f)
        except json.JSONDecodeError:
            existing = []

    existing.append(data)

    with open(DATA_FILE, "w") as f:
        json.dump(existing, f, indent=4)