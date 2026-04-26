import json
from pathlib import Path
from typing import Dict

from config.settings import Settings, get_memory_file_path


def load_memory() -> Dict[str, str]:
    """Load memory dictionary from disk, returning empty on first run."""
    memory_path = get_memory_file_path()
    if not memory_path.exists():
        return {}

    try:
        with memory_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}

    return {str(key): str(value) for key, value in raw_data.items()}


def save_memory(memory_data: Dict[str, str], settings: Settings) -> None:
    """Persist memory dictionary to disk with item cap."""
    memory_path = get_memory_file_path()
    trimmed_items = list(memory_data.items())[-settings.memory_max_items :]
    safe_payload = {key: value for key, value in trimmed_items}

    with memory_path.open("w", encoding="utf-8") as file:
        json.dump(safe_payload, file, indent=2)


def store_memory_fact(key: str, value: str, settings: Settings) -> None:
    """Store one memory key-value pair."""
    memory_data = load_memory()
    memory_data[key.strip().lower()] = value.strip()
    save_memory(memory_data=memory_data, settings=settings)


def read_memory_fact(key: str) -> str:
    """Read a memory value by key."""
    memory_data = load_memory()
    return memory_data.get(key.strip().lower(), "")


def format_memory_context() -> str:
    """Render saved memory as a compact context string for AI prompts."""
    memory_data = load_memory()
    if not memory_data:
        return "No saved memory."

    lines = [f"- {key}: {value}" for key, value in memory_data.items()]
    return "\n".join(lines)
