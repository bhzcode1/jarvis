from dataclasses import dataclass
from datetime import datetime
import re
import webbrowser
from typing import Callable, Tuple

from app.commands.translation import translate_offline_request
from app.system.control import (
    cancel_pending_shutdown,
    lock_workstation,
    open_application,
    restart_pc,
    shutdown_pc,
    system_control_allowed,
)
from app.system.spotify import (
    spotify_adjust_volume,
    spotify_create_playlist,
    spotify_current_track,
    spotify_like_current_track,
    spotify_pause,
    spotify_play,
    spotify_previous,
    spotify_queue,
    spotify_repeat,
    spotify_resume,
    spotify_set_volume,
    spotify_shuffle,
    spotify_skip,
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
    if "youtube" not in lowered:
        return CommandResult(False, "")

    webbrowser.open("https://www.youtube.com")
    return CommandResult(True, "Opening YouTube.")


def _extract_queue_query(text: str) -> str:
    """Extract song text from queue-style requests."""
    patterns = (
        r"^(?:queue|add) (?P<query>.+?) (?:after this|to queue|in queue)$",
        r"^queue (?P<query>.+)$",
        r"^add (?P<query>.+?) to queue$",
    )
    lowered = text.lower().strip()
    for pattern in patterns:
        match = re.match(pattern, lowered)
        if match:
            return match.group("query").strip()
    return ""


def _split_playlist_songs(text: str) -> list[str]:
    """Split a spoken song list into individual track queries."""
    normalized = re.sub(r"\s+and\s+", ",", text.strip(), flags=re.IGNORECASE)
    return [part.strip() for part in normalized.split(",") if part.strip()]


def _extract_playlist_request(text: str) -> tuple[str, list[str]] | None:
    """Extract a playlist name and song list from a spoken request."""
    match = re.match(
        r"^(?:create|make) playlist (?P<name>.+?) with (?P<songs>.+)$",
        text.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    name = match.group("name").strip()
    songs = _split_playlist_songs(match.group("songs"))
    if not name or not songs:
        return None
    return name, songs


def _extract_volume_level(text: str) -> int | None:
    """Extract an explicit Spotify volume percentage."""
    match = re.search(r"(?:spotify )?volume(?: to| at)? (?P<level>\d{1,3})", text.lower())
    if not match:
        return None
    return max(0, min(int(match.group("level")), 100))


def _spotify_playlist_shortcuts(text: str) -> tuple[str, str] | None:
    """Map vague mood/language music requests to a direct Spotify search."""
    lowered = text.lower().strip()
    exact_map = {
        "play something chill": ("chill vibes playlist", "playlist"),
        "play something for studying": ("lofi study beats", "playlist"),
        "play sad songs": ("sad songs playlist", "playlist"),
        "play something energetic": ("workout energy playlist", "playlist"),
        "surprise me": ("top global hits", "playlist"),
        "play tamil songs": ("tamil hits playlist", "playlist"),
        "play hindi songs": ("hindi top hits playlist", "playlist"),
        "play telugu songs": ("telugu hits playlist", "playlist"),
    }
    return exact_map.get(lowered)


def _extract_spotify_play_request(text: str) -> tuple[str, str] | None:
    """Extract the intended Spotify search query and media type."""
    shortcut = _spotify_playlist_shortcuts(text)
    if shortcut is not None:
        return shortcut

    lowered = text.lower().strip()
    blocked_queries = {
        "a joke",
        "joke",
        "a game",
        "game",
        "video",
        "the video",
        "a video",
    }
    patterns = (
        (r"^play something by (?P<query>.+)$", "artist"),
        (r"^play (?:the )?album (?P<query>.+)$", "album"),
        (r"^play (?:the )?playlist (?P<query>.+)$", "playlist"),
        (r"^play (?P<query>.+?) playlist$", "playlist"),
        (r"^play (?:the )?top hits of (?P<query>.+)$", "playlist"),
        (r"^play (?P<query>.+?) on spotify$", "track"),
        (r"^play (?P<query>.+?) in spotify$", "track"),
        (r"^spotify play (?P<query>.+)$", "track"),
        (r"^play spotify (?P<query>.+)$", "track"),
        (r"^play (?P<query>.+)$", "track"),
    )

    for pattern, item_type in patterns:
        match = re.match(pattern, lowered)
        if not match:
            continue
        query = match.group("query").strip()
        if query in {"music", "song", "songs", "playlist"} | blocked_queries:
            return None
        if item_type == "track" and pattern == r"^play (?P<query>.+)$" and len(query.split()) > 7:
            return None
        if "top hits of" in pattern:
            return (f"{query} top hits", "playlist")
        return query, item_type
    return None


def _handle_spotify_command(text: str, settings: Settings) -> CommandResult:
    """Handle Spotify playback, queue, save, and playlist commands."""
    raw_text = text.strip()
    lowered = raw_text.lower()

    playlist_request = _extract_playlist_request(raw_text)
    if playlist_request is not None:
        name, songs = playlist_request
        result = spotify_create_playlist(settings=settings, name=name, songs=songs)
        return CommandResult(True, result.message)

    if lowered in {"pause", "pause spotify", "pause music", "stop", "stop music", "stop spotify"}:
        result = spotify_pause(settings=settings)
        return CommandResult(True, result.message)

    if lowered in {"resume", "resume spotify", "continue", "continue spotify", "play again"}:
        result = spotify_resume(settings=settings)
        return CommandResult(True, result.message)

    if lowered in {"next", "next song", "skip", "skip song"}:
        result = spotify_skip(settings=settings)
        return CommandResult(True, result.message)

    if lowered in {"previous", "previous song", "go back", "last song"}:
        result = spotify_previous(settings=settings)
        return CommandResult(True, result.message)

    explicit_level = _extract_volume_level(lowered)
    if explicit_level is not None:
        result = spotify_set_volume(settings=settings, level=explicit_level)
        return CommandResult(True, result.message)

    if lowered in {"volume up", "spotify volume up", "music louder"}:
        result = spotify_adjust_volume(settings=settings, delta=10)
        return CommandResult(True, result.message)

    if lowered in {"volume down", "spotify volume down", "music quieter"}:
        result = spotify_adjust_volume(settings=settings, delta=-10)
        return CommandResult(True, result.message)

    if lowered in {"shuffle on", "turn shuffle on", "spotify shuffle on"}:
        result = spotify_shuffle(settings=settings, enabled=True)
        return CommandResult(True, result.message)

    if lowered in {"shuffle off", "turn shuffle off", "spotify shuffle off"}:
        result = spotify_shuffle(settings=settings, enabled=False)
        return CommandResult(True, result.message)

    if lowered in {"repeat this song", "repeat track", "repeat one"}:
        result = spotify_repeat(settings=settings, state="track")
        return CommandResult(True, result.message)

    if lowered in {"repeat on", "repeat playlist", "repeat context"}:
        result = spotify_repeat(settings=settings, state="context")
        return CommandResult(True, result.message)

    if lowered in {"repeat off", "turn repeat off"}:
        result = spotify_repeat(settings=settings, state="off")
        return CommandResult(True, result.message)

    if lowered in {"what's playing", "what is playing", "what song is this", "what is this song"}:
        result = spotify_current_track(settings=settings)
        return CommandResult(True, result.message)

    if lowered in {"like this", "like this song", "save this song", "save this track"}:
        result = spotify_like_current_track(settings=settings)
        return CommandResult(True, result.message)

    queue_query = _extract_queue_query(lowered)
    if queue_query:
        result = spotify_queue(settings=settings, query=queue_query)
        return CommandResult(True, result.message)

    play_request = _extract_spotify_play_request(lowered)
    if play_request is None:
        return CommandResult(False, "")

    query, item_type = play_request
    result = spotify_play(settings=settings, query=query, item_type=item_type)  # type: ignore[arg-type]
    return CommandResult(True, result.message)


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


def _handle_translation_command(text: str) -> CommandResult:
    """Handle short offline translation requests."""
    result = translate_offline_request(text)
    return CommandResult(result.handled, result.response_text)


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
        _handle_translation_command,
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

    spotify_result = _handle_spotify_command(normalized_text, settings=settings)
    if spotify_result.handled:
        return spotify_result

    system_result = _handle_system_control_command(normalized_text, settings=settings)
    if system_result.handled:
        return system_result

    return CommandResult(False, "I heard you, but I do not support that command yet.")
