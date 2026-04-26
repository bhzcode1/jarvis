import sys
from pathlib import Path


def get_bundled_resource_path(relative_name: str) -> Path:
    """
    Return path to a file bundled with PyInstaller.

    In frozen mode, resources live under sys._MEIPASS.
    In source mode, this returns project root / relative_name.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve() / relative_name

    return Path(__file__).resolve().parents[2] / relative_name

