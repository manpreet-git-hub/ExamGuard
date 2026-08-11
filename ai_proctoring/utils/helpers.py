# ── utils/helpers.py — Miscellaneous utility functions ────────────────────────

import os


def safe_makedirs(path: str):
    """Create directory (and parents) if it doesn't already exist."""
    os.makedirs(path, exist_ok=True)
