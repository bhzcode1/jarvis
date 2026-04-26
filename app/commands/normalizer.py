from __future__ import annotations

import re


def normalize_voice_command(text: str) -> str:
    """Clean common offline speech-recognition mistakes before routing."""
    normalized = text.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s']", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    replacements = (
        ("or when", "open"),
        ("oh when", "open"),
        ("open your to", "open youtube"),
        ("open you're too", "open youtube"),
        ("open you are too", "open youtube"),
        ("open you too", "open youtube"),
        ("open u tube", "open youtube"),
        ("open you tube", "open youtube"),
        ("you're too", "youtube"),
        ("you are too", "youtube"),
        ("your to", "youtube"),
        ("you too", "youtube"),
        ("u tube", "youtube"),
        ("you tube", "youtube"),
        ("what's the time", "what is the time"),
        ("tell me time", "what is the time"),
        ("what's date", "what is the date"),
        ("what's the date", "what is the date"),
    )
    for wrong, right in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        normalized = normalized.replace(wrong, right)

    words = normalized.split()
    if "youtube" in words and not normalized.startswith(("open ", "search ", "google ", "find ")):
        return "open youtube"

    return normalized
