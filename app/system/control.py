import os
import re
import subprocess
import webbrowser
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from config.settings import Settings


def _normalize_app_name(name: str) -> str:
    """Return a lowercase app key that ignores punctuation and spacing."""
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _shell_start(command: str) -> bool:
    """Launch a command through the Windows shell."""
    try:
        subprocess.Popen(["cmd", "/c", "start", "", command])
        return True
    except OSError:
        return False


def _powershell_string(value: str) -> str:
    """Escape a Python string for a PowerShell single-quoted literal."""
    return value.replace("'", "''")


def _start_menu_lookup(query: str) -> bool:
    """Try launching an installed app from the Start menu catalog."""
    escaped_query = _powershell_string(query)
    script = (
        "$query = '{query}'; "
        "$normalized = ($query.ToLower() -replace '[^a-z0-9]', ''); "
        "$apps = Get-StartApps | Where-Object {{ $_.Name }}; "
        "$app = $apps | Where-Object {{ "
        "((($_.Name).ToLower() -replace '[^a-z0-9]', '') -eq $normalized) -or "
        "((($_.Name).ToLower() -replace '[^a-z0-9]', '') -like ('*' + $normalized + '*')) "
        "}} | Select-Object -First 1; "
        "if ($app) {{ Start-Process ('shell:AppsFolder\\' + $app.AppID); exit 0 }} "
        "exit 1"
    ).format(query=escaped_query)
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            check=False,
            creationflags=creation_flags,
            capture_output=True,
            text=True,
            timeout=12,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@lru_cache(maxsize=1)
def _start_menu_shortcuts() -> tuple[tuple[str, str], ...]:
    """Index common Start menu shortcuts for classic desktop apps."""
    shortcut_dirs = (
        Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    )
    shortcuts: list[tuple[str, str]] = []
    for root in shortcut_dirs:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".lnk", ".url", ".appref-ms"}:
                continue
            shortcuts.append((_normalize_app_name(path.stem), str(path)))
    return tuple(shortcuts)


def _shortcut_lookup(query: str) -> bool:
    """Launch the best matching Start menu shortcut."""
    normalized = _normalize_app_name(query)
    if not normalized:
        return False

    exact_match: str | None = None
    partial_match: str | None = None
    for shortcut_name, shortcut_path in _start_menu_shortcuts():
        if shortcut_name == normalized:
            exact_match = shortcut_path
            break
        if partial_match is None and (normalized in shortcut_name or shortcut_name in normalized):
            partial_match = shortcut_path

    target = exact_match or partial_match
    if not target:
        return False

    try:
        os.startfile(target)  # type: ignore[attr-defined]
        return True
    except OSError:
        return False


def play_on_spotify(query: str) -> bool:
    """Open Spotify and search for a requested song, album, or artist."""
    cleaned_query = query.strip()
    if not cleaned_query:
        return open_application("spotify")

    encoded_query = quote(cleaned_query, safe="")
    launch_targets = (
        f"spotify:search:{encoded_query}",
        f"https://open.spotify.com/search/{encoded_query}",
    )

    for target in launch_targets:
        try:
            if target.startswith("spotify:"):
                subprocess.Popen(["cmd", "/c", "start", "", target])
            else:
                webbrowser.open(target)
            return True
        except OSError:
            continue

    return False


def open_application(command_key: str) -> bool:
    """Open a desktop application by alias, Start menu entry, or known path."""
    normalized = command_key.lower().strip()
    app_map = {
        "notepad": [["notepad.exe"]],
        "calculator": [["calc.exe"]],
        "calc": [["calc.exe"]],
        "paint": [["mspaint.exe"]],
        "explorer": [["explorer.exe"]],
        "file explorer": [["explorer.exe"]],
        "chrome": [
            ["cmd", "/c", "start", "", "chrome"],
            [r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
            [r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
        ],
        "google chrome": [
            ["cmd", "/c", "start", "", "chrome"],
            [r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
            [r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
        ],
        "edge": [
            ["cmd", "/c", "start", "", "msedge"],
            [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
            [r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"],
        ],
        "microsoft edge": [
            ["cmd", "/c", "start", "", "msedge"],
            [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
            [r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"],
        ],
        "spotify": [["cmd", "/c", "start", "", "spotify"]],
        "vs code": [["cmd", "/c", "start", "", "code"]],
        "visual studio code": [["cmd", "/c", "start", "", "code"]],
    }

    commands = app_map.get(normalized)
    if not commands:
        if normalized in {"browser", "default browser"}:
            webbrowser.open("about:blank")
            return True
        if _start_menu_lookup(normalized):
            return True
        return _shortcut_lookup(normalized)

    for command in commands:
        executable = command[0]
        if len(command) == 1 and "\\" in executable and not Path(executable).exists():
            continue
        try:
            subprocess.Popen(command)
            return True
        except OSError:
            continue

    if normalized in {"chrome", "google chrome", "edge", "microsoft edge"}:
        try:
            webbrowser.open("about:blank")
            return True
        except OSError:
            return False

    if _shell_start(normalized):
        return True
    if _start_menu_lookup(normalized):
        return True
    return _shortcut_lookup(normalized)


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
