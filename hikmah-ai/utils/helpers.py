"""
Shared utility helpers for HIKMAH AI.
"""

from __future__ import annotations

import re
from typing import List


def clean_text(text: str) -> str:
    """Remove excessive whitespace and normalise line endings."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(text: str, max_chars: int = 300, suffix: str = "…") -> str:
    """Truncate text to max_chars, appending suffix if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + suffix


def chunk_list(lst: list, size: int) -> List[list]:
    """Split a list into chunks of *size*."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def format_citation(source: str, metadata: dict) -> str:
    """Build a human-readable citation string from metadata."""
    if source == "quran":
        surah = metadata.get("surah_name", "")
        surah_num = metadata.get("surah_number", "")
        ayah = metadata.get("ayah_number", "")
        return f"Quran {surah_num}:{ayah} ({surah})"
    elif source == "sahih_bukhari":
        book = metadata.get("book_name", "Sahih Bukhari")
        num = metadata.get("hadith_number", "")
        return f"Sahih Bukhari #{num} — {book}"
    return metadata.get("citation", "Unknown source")
