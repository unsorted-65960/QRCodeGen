# utils/config_manager.py
import json
from pathlib import Path

CONFIG_PATH = Path("data/connection.json")

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_config(data: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_active_config():
    config = load_config()
    if not config:
        print("⚠️ No active connection.json found.")
    return config
