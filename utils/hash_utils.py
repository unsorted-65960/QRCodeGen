# utils/hash_utils.py
"""
Provides deterministic hashing for QR tracking.
Used to uniquely identify each QR code based on the text content
encoded in it (not on the database schema).
"""

import hashlib


def generate_row_hash(data: dict | str) -> str:
    """
    Generate a stable SHA256 hash for the given input.

    - If `data` is a dict, it sorts keys and serializes them as key=value pairs.
    - If `data` is a string, it hashes that string directly.
    """

    if isinstance(data, dict):
        serialized = "|".join(f"{k}={v}" for k, v in sorted(data.items()))
    elif isinstance(data, str):
        serialized = data
    else:
        raise TypeError("generate_row_hash() accepts dict or str only")

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
