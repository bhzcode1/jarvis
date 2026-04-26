from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryAction:
    """Represents a memory operation extracted from user text."""

    action: str
    key: str
    value: str


def detect_memory_action(user_text: str) -> MemoryAction:
    """Detect simple save/recall memory intents from plain text."""
    normalized = user_text.strip()
    lowered = normalized.lower()

    if lowered.startswith("remember that "):
        payload = normalized[len("remember that ") :].strip()
        if " is " in payload:
            key, value = payload.split(" is ", maxsplit=1)
            return MemoryAction(action="save", key=key.strip(), value=value.strip())
        return MemoryAction(action="save", key="note", value=payload)

    if lowered.startswith("remember "):
        payload = normalized[len("remember ") :].strip()
        if " is " in payload:
            key, value = payload.split(" is ", maxsplit=1)
            return MemoryAction(action="save", key=key.strip(), value=value.strip())

    if lowered.startswith("what do you remember about "):
        key = normalized[len("what do you remember about ") :].strip()
        return MemoryAction(action="recall", key=key, value="")

    if lowered.startswith("recall "):
        key = normalized[len("recall ") :].strip()
        return MemoryAction(action="recall", key=key, value="")

    return MemoryAction(action="none", key="", value="")
