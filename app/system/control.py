import subprocess

from config.settings import Settings


def open_application(command_key: str) -> bool:
    """Open a known desktop application by key."""
    app_map = {
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "paint": ["mspaint.exe"],
        "explorer": ["explorer.exe"],
    }
    command = app_map.get(command_key.lower())
    if not command:
        return False

    subprocess.Popen(command)
    return True


def lock_workstation() -> bool:
    """Lock Windows workstation immediately."""
    try:
        subprocess.run(
            ["rundll32.exe", "user32.dll,LockWorkStation"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.SubprocessError:
        return False


def restart_pc(delay_seconds: int) -> bool:
    """Schedule PC restart after delay."""
    try:
        subprocess.run(
            ["shutdown", "/r", "/t", str(delay_seconds)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.SubprocessError:
        return False


def shutdown_pc(delay_seconds: int) -> bool:
    """Schedule PC shutdown after delay."""
    try:
        subprocess.run(
            ["shutdown", "/s", "/t", str(delay_seconds)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.SubprocessError:
        return False


def cancel_pending_shutdown() -> bool:
    """Abort pending restart/shutdown action."""
    try:
        subprocess.run(
            ["shutdown", "/a"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.SubprocessError:
        return False


def system_control_allowed(settings: Settings) -> bool:
    """Return whether system-level commands are enabled."""
    return settings.system_control_enabled
