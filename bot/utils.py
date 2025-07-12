"""Utility helpers for the bot that are reused across modules."""
from __future__ import annotations

import os
import random
import string
from typing import Set

import pandas as pd

from .config import EXCEL_FILE_PATH


def _load_existing_codes() -> Set[str]:
    """Return a set of codes already present in the Excel file.
    If the file or the column is missing, return an empty set.
    """
    if not os.path.exists(EXCEL_FILE_PATH):
        return set()

    try:
        df = pd.read_excel(EXCEL_FILE_PATH, engine="openpyxl")
    except Exception:
        # corrupted or unreadable file – just treat as no codes
        return set()

    if "Уникальный код" not in df.columns:
        return set()

    # Cast to str to avoid numpy types
    return set(df["Уникальный код"].astype(str).tolist())


def generate_unique_code(length: int = 6) -> str:
    """Generate a truly unique code of given length.

    The code is checked against the Excel database before returning.
    If a collision is detected, a new one is generated.
    """
    existing = _load_existing_codes()
    alphabet = string.ascii_uppercase + string.digits

    while True:
        new_code = "".join(random.choice(alphabet) for _ in range(length))
        if new_code not in existing:
            return new_code
