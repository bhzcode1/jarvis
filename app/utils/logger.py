import logging
from pathlib import Path
from typing import Optional


def configure_logging(log_file: Optional[Path] = None) -> None:
    """Configure app-wide logging format and level."""
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    """Return named logger instance."""
    return logging.getLogger(name)
