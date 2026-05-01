from __future__ import annotations

import random


def pick_wake_acknowledgement(*, silent_ratio: float = 0.6) -> str:
    """Short wake acknowledgement (often silent)."""
    if random.random() < max(0.0, min(float(silent_ratio), 1.0)):
        return ""
    return random.choice(("Yeah?", "Listening.", "Go ahead.", "I'm here."))


def short_confirm() -> str:
    """Ultra-short task confirmation."""
    return random.choice(("Done.", "Got it.", "All set.", "Handled.", "Sorted."))


def short_working() -> str:
    """Short line while executing something."""
    return random.choice(("On it.", "One sec.", "Give me a second.", "Running that now."))


def short_failure(reason: str, alternative: str | None = None) -> str:
    """One-line failure in the requested voice/personality."""
    clean_reason = " ".join((reason or "").split()).strip()
    if not clean_reason:
        clean_reason = "that didn't go through"
    if alternative:
        return f"Hit a wall there — {clean_reason}. Want me to try {alternative}?"
    return f"Couldn't do that — {clean_reason}."

