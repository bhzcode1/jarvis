from pathlib import Path

from app.utils.resources import get_bundled_resource_path


def ensure_env_file_exists(runtime_base_dir: Path) -> Path:
    """
    Ensure a .env file exists in the runtime base directory.

    If missing, create it from bundled .env.example so the EXE can start.
    """
    env_path = runtime_base_dir / ".env"
    if env_path.exists():
        return env_path

    template_path = get_bundled_resource_path(".env.example")
    if template_path.exists():
        env_path.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")
        return env_path

    env_path.write_text("", encoding="utf-8")
    return env_path

