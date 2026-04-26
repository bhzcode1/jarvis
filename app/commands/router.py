from dataclasses import dataclass
from datetime import datetime
import webbrowser
from typing import Callable, Tuple

from app.system.control import (
    cancel_pending_shutdown,
    lock_workstation,
    open_application,
    restart_pc,
    shutdown_pc,
    system_control_allowed,
)
from config.settings import Settings



@dataclass(frozen=True)
class CommandResult:
    """Normalized output of command execution."""

    handled: bool
    response_text: str


CommandHandler = Callable[[str], CommandResult]


def _extract_query_from_search(text: str) -> str:
    """Extract user search query from common search phrases."""
    lowered = text.lower().strip()
    for prefix in ("search for ", "search ", "google ", "find "):
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip()
    return ""


def _handle_time_command(text: str) -> CommandResult:
    """Handle commands that ask for the current time."""
    lowered = text.lower()
    if "time" in lowered:
        current_time = datetime.now().strftime("%I:%M %p")
        return CommandResult(True, f"The current time is {current_time}.")
    return CommandResult(False, "")


def _handle_web_search_command(text: str) -> CommandResult:
    """Handle simple web-search commands in the default browser."""
    query = _extract_query_from_search(text=text)
    if not query:
        return CommandResult(False, "")

    encoded_query = query.replace(" ", "+")
    webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
    return CommandResult(True, f"Searching the web for {query}.")


def _handle_open_youtube_command(text: str) -> CommandResult:
    """Handle direct command to open YouTube."""
    lowered = text.lower()
    if "open youtube" not in lowered:
        return CommandResult(False, "")

    webbrowser.open("https://www.youtube.com")
    return CommandResult(True, "Opening YouTube.")


def _handle_open_app_command(text: str) -> CommandResult:
    """Handle opening known desktop applications."""
    lowered = text.lower().strip()
    prefixes = ("open ", "launch ", "start ")
    app_name = ""
    for prefix in prefixes:
        if lowered.startswith(prefix):
            app_name = lowered[len(prefix) :].strip()
            break

    if not app_name:
        return CommandResult(False, "")

    if open_application(app_name):
        return CommandResult(True, f"Opening {app_name}.")
    return CommandResult(False, "")


def _handle_system_control_command(text: str, settings: Settings) -> CommandResult:
    """Handle lock/restart/shutdown commands with safety toggle."""
    lowered = text.lower().strip()
    if not any(word in lowered for word in ("lock", "restart", "shutdown", "cancel")):
        return CommandResult(False, "")

    if not system_control_allowed(settings=settings):
        return CommandResult(
            True,
            "System control is disabled. Set SYSTEM_CONTROL_ENABLED=true in .env to allow this.",
        )

    if "lock" in lowered:
        return CommandResult(
            True,
            "Locking your workstation now." if lock_workstation() else "Failed to lock workstation.",
        )

    if "cancel" in lowered and "shutdown" in lowered:
        return CommandResult(
            True,
            "Canceled pending shutdown command."
            if cancel_pending_shutdown()
            else "No pending shutdown command to cancel.",
        )

    if "restart" in lowered:
        success = restart_pc(settings.system_shutdown_delay_seconds)
        return CommandResult(
            True,
            (
                f"Restart scheduled in {settings.system_shutdown_delay_seconds} seconds."
                if success
                else "Failed to schedule restart."
            ),
        )

    if "shutdown" in lowered:
        success = shutdown_pc(settings.system_shutdown_delay_seconds)
        return CommandResult(
            True,
            (
                f"Shutdown scheduled in {settings.system_shutdown_delay_seconds} seconds."
                if success
                else "Failed to schedule shutdown."
            ),
        )

    return CommandResult(False, "")


def _default_handlers() -> Tuple[CommandHandler, ...]:
    """Return non-system command handlers in routing order."""
    return (
        _handle_time_command,
        _handle_web_search_command,
        _handle_open_youtube_command,
        _handle_open_app_command,
    )


def route_command(text: str, settings: Settings) -> CommandResult:
    """Route user text to the first matching command handler."""
    normalized_text = text.strip()
    if not normalized_text:
        return CommandResult(False, "I did not hear a command.")

    for handler in _default_handlers():
        result = handler(normalized_text)
        if result.handled:
            return result

    system_result = _handle_system_control_command(normalized_text, settings=settings)
    if system_result.handled:
        return system_result

    return CommandResult(False, "I heard you, but I do not support that command yet.")
