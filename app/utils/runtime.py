import os
import sys
from pathlib import Path


def get_runtime_base_dir() -> Path:
    """
    Return a stable base directory for runtime files.

    - In source/dev: project root (folder containing 'app/')
    - In a packaged exe: the folder containing the executable
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


def set_cwd_to_runtime_base_dir() -> Path:
    """Set current working directory to runtime base dir and return it."""
    base_dir = get_runtime_base_dir()
    os.chdir(base_dir)
    return base_dir

