import json
from datetime import datetime

# -----------------------------
# Logger
# -----------------------------
DEBUG = True

def log(step: str, message: str = ""):
    if DEBUG:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{step}] {message}")

def save_investigation(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )