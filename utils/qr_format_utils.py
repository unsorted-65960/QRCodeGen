"""
Formats any database row (dict) into a human-readable string
for QR encoding and label printing.
Supports any number of columns dynamically selected by the admin.
"""
from utils.config_manager import get_active_config


def format_row_for_qr(row: dict) -> str:
    """
    Convert a row dict into a readable multi-line string
    following the column order from connection.json.
    """
    config = get_active_config() or {}
    ordered_keys = config.get("columns", list(row.keys()))  # fallback to dict order

    lines = []
    for key in ordered_keys:
        if key not in row:
            continue
        key_label = key.replace("_", " ").title()
        value = row.get(key, "")
        lines.append(f"{key_label}: {value}")
    return "\n".join(lines)


def make_preview_text(row: dict, limit: int = 3) -> str:
    """
    Generate a short preview for QR tracking (for database storage).
    Uses connection.json column order and limits the number of pairs.
    """
    config = get_active_config() or {}
    ordered_keys = config.get("columns", list(row.keys()))

    pairs = []
    for i, key in enumerate(ordered_keys):
        if i >= limit:
            break
        if key not in row:
            continue
        key_label = key.replace("_", " ").title()
        pairs.append(f"{key_label}: {row.get(key, '')}")
    return " | ".join(pairs)
