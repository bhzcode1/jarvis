from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from config.settings import Settings, get_project_root
from app.system.control import open_application

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
except ImportError:  # pragma: no cover - optional dependency at runtime
    spotipy = None
    SpotifyOAuth = None


SpotifyItemType = Literal["track", "artist", "album", "playlist"]
SpotifyRepeatState = Literal["track", "context", "off"]

SPOTIFY_SCOPES = (
    "user-modify-playback-state "
    "user-read-playback-state "
    "user-library-modify "
    "playlist-modify-public "
    "playlist-modify-private"
)


@dataclass(frozen=True)
class SpotifyActionResult:
    """Result of a Spotify control action."""

    success: bool
    message: str


def _spotify_cache_path() -> str:
    """Return on-disk cache location for Spotify OAuth tokens."""
    auth_dir = get_project_root() / "data" / "auth"
    auth_dir.mkdir(parents=True, exist_ok=True)
    return str(auth_dir / ".spotify-cache")


@lru_cache(maxsize=4)
def _build_client(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    cache_path: str,
):
    """Build and cache an authenticated Spotipy client."""
    if spotipy is None or SpotifyOAuth is None:
        raise RuntimeError("Spotify support needs spotipy installed.")

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SPOTIFY_SCOPES,
        cache_path=cache_path,
        show_dialog=False,
        open_browser=True,
    )
    return spotipy.Spotify(
        auth_manager=auth_manager,
        requests_timeout=10,
        retries=2,
        status_retries=2,
        backoff_factor=0.2,
    )


def _get_client(settings: Settings):
    """Return an authenticated Spotipy client or raise a setup error."""
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        raise RuntimeError("Spotify needs API keys in .env.")

    return _build_client(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        cache_path=_spotify_cache_path(),
    )


def _normalize_name(text: str) -> str:
    """Normalize device names for fuzzy matching."""
    return "".join(char for char in text.lower() if char.isalnum())


def _open_spotify_if_needed() -> bool:
    """Launch Spotify desktop app and give it a moment to register a device."""
    launched = open_application("spotify")
    if launched:
        time.sleep(2.0)
    return launched


def _pick_device(client, settings: Settings):
    """Choose the best playback device currently visible to Spotify."""
    devices_response = client.devices() or {}
    devices = devices_response.get("devices") or []
    if not devices:
        return None

    active_device = next(
        (device for device in devices if device.get("is_active") and not device.get("is_restricted")),
        None,
    )
    if active_device is not None:
        return active_device

    preferred_name = _normalize_name(settings.spotify_device_name or "")
    if preferred_name:
        named_device = next(
            (
                device
                for device in devices
                if preferred_name in _normalize_name(str(device.get("name", "")))
                and not device.get("is_restricted")
            ),
            None,
        )
        if named_device is not None:
            return named_device

    for device_type in ("computer", "smartphone", "speaker"):
        typed_device = next(
            (
                device
                for device in devices
                if str(device.get("type", "")).lower() == device_type and not device.get("is_restricted")
            ),
            None,
        )
        if typed_device is not None:
            return typed_device

    return next((device for device in devices if not device.get("is_restricted")), None)


def _ensure_playback_device(client, settings: Settings):
    """Return an active playback device and whether Spotify was launched."""
    playback = client.current_playback()
    if playback and playback.get("device") and not playback["device"].get("is_restricted"):
        return playback["device"], False

    launched = _open_spotify_if_needed()
    device = _pick_device(client, settings)
    if device is None:
        raise RuntimeError("No Spotify device is ready.")

    device_id = device.get("id")
    if device_id:
        client.transfer_playback(device_id=device_id, force_play=False)
        time.sleep(0.8)
    return device, launched


def _spotify_error_message(error: Exception) -> str:
    """Map Spotify/runtime errors to short user-facing responses."""
    if isinstance(error, RuntimeError):
        return str(error)

    if spotipy is not None and isinstance(error, spotipy.SpotifyException):
        status = getattr(error, "http_status", None)
        message = str(getattr(error, "msg", "") or error).lower()

        if status == 401:
            return "Spotify sign-in expired."
        if status == 403 and "premium" in message:
            return "Spotify Premium is required."
        if status == 403 and "restriction" in message:
            return "Spotify refused that on this device."
        if status == 404 or "no active device" in message:
            return "No Spotify device is ready."
        if status == 429:
            return "Spotify rate-limited that request."
        return "Spotify command failed."

    return "Spotify command failed."


def _search_first(client, query: str, item_type: SpotifyItemType):
    """Return the top Spotify search match for a query."""
    results = client.search(q=query, type=item_type, limit=1, market="from_token")
    key = f"{item_type}s"
    items = ((results or {}).get(key) or {}).get("items") or []
    return items[0] if items else None


def spotify_play(settings: Settings, query: str, item_type: SpotifyItemType) -> SpotifyActionResult:
    """Search Spotify and begin playback of a track, artist, album, or playlist."""
    try:
        client = _get_client(settings)
        device, launched = _ensure_playback_device(client, settings)
        device_id = device.get("id") if isinstance(device, dict) else None
        item = _search_first(client, query, item_type)
        if item is None:
            return SpotifyActionResult(False, "I couldn't find that on Spotify.")

        if item_type == "track":
            artists = ", ".join(artist["name"] for artist in item.get("artists", [])[:2])
            client.start_playback(device_id=device_id, uris=[item["uri"]])
            prefix = "Opening Spotify now. " if launched else ""
            return SpotifyActionResult(True, f"{prefix}Playing {item['name']} by {artists}.")

        client.start_playback(device_id=device_id, context_uri=item["uri"])
        prefix = "Opening Spotify now. " if launched else ""
        return SpotifyActionResult(True, f"{prefix}Playing {item['name']}.")
    except Exception as error:  # pragma: no cover - runtime/network/device guard
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_pause(settings: Settings) -> SpotifyActionResult:
    """Pause current Spotify playback."""
    try:
        client = _get_client(settings)
        device, _ = _ensure_playback_device(client, settings)
        client.pause_playback(device_id=device.get("id") if isinstance(device, dict) else None)
        return SpotifyActionResult(True, "Paused.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_resume(settings: Settings) -> SpotifyActionResult:
    """Resume current Spotify playback."""
    try:
        client = _get_client(settings)
        device, launched = _ensure_playback_device(client, settings)
        client.start_playback(device_id=device.get("id") if isinstance(device, dict) else None)
        return SpotifyActionResult(True, "Opening Spotify now. Resumed." if launched else "Resumed.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_skip(settings: Settings) -> SpotifyActionResult:
    """Skip to the next Spotify track."""
    try:
        client = _get_client(settings)
        device, _ = _ensure_playback_device(client, settings)
        client.next_track(device_id=device.get("id") if isinstance(device, dict) else None)
        return SpotifyActionResult(True, "Skipping.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_previous(settings: Settings) -> SpotifyActionResult:
    """Go back to the previous Spotify track."""
    try:
        client = _get_client(settings)
        device, _ = _ensure_playback_device(client, settings)
        client.previous_track(device_id=device.get("id") if isinstance(device, dict) else None)
        return SpotifyActionResult(True, "Previous track.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_set_volume(settings: Settings, level: int) -> SpotifyActionResult:
    """Set Spotify playback volume."""
    clamped_level = max(0, min(level, 100))
    try:
        client = _get_client(settings)
        device, _ = _ensure_playback_device(client, settings)
        if isinstance(device, dict) and not device.get("supports_volume", True):
            return SpotifyActionResult(False, "This Spotify device has fixed volume.")
        client.volume(volume_percent=clamped_level, device_id=device.get("id") if isinstance(device, dict) else None)
        return SpotifyActionResult(True, f"Volume {clamped_level}.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_adjust_volume(settings: Settings, delta: int) -> SpotifyActionResult:
    """Raise or lower Spotify volume relative to current playback state."""
    try:
        client = _get_client(settings)
        device, _ = _ensure_playback_device(client, settings)
        current_level = 50
        if isinstance(device, dict) and device.get("volume_percent") is not None:
            current_level = int(device["volume_percent"])
        return spotify_set_volume(settings, current_level + delta)
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_shuffle(settings: Settings, enabled: bool) -> SpotifyActionResult:
    """Turn Spotify shuffle mode on or off."""
    try:
        client = _get_client(settings)
        device, _ = _ensure_playback_device(client, settings)
        client.shuffle(state=enabled, device_id=device.get("id") if isinstance(device, dict) else None)
        return SpotifyActionResult(True, "Shuffle on." if enabled else "Shuffle off.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_repeat(settings: Settings, state: SpotifyRepeatState) -> SpotifyActionResult:
    """Set Spotify repeat mode."""
    try:
        client = _get_client(settings)
        device, _ = _ensure_playback_device(client, settings)
        client.repeat(state=state, device_id=device.get("id") if isinstance(device, dict) else None)
        if state == "track":
            return SpotifyActionResult(True, "Repeating this song.")
        if state == "context":
            return SpotifyActionResult(True, "Repeat on.")
        return SpotifyActionResult(True, "Repeat off.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_queue(settings: Settings, query: str) -> SpotifyActionResult:
    """Add a track to the current Spotify queue."""
    try:
        client = _get_client(settings)
        _ensure_playback_device(client, settings)
        item = _search_first(client, query, "track")
        if item is None:
            return SpotifyActionResult(False, "I couldn't find that track.")
        client.add_to_queue(item["uri"])
        return SpotifyActionResult(True, "Queued. It'll play next.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_current_track(settings: Settings) -> SpotifyActionResult:
    """Return the currently playing Spotify track."""
    try:
        client = _get_client(settings)
        playback = client.current_playback()
        item = (playback or {}).get("item")
        if not item:
            return SpotifyActionResult(False, "Nothing is playing.")

        artists = ", ".join(artist["name"] for artist in item.get("artists", [])[:2])
        return SpotifyActionResult(True, f"That's {item['name']} by {artists}.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_like_current_track(settings: Settings) -> SpotifyActionResult:
    """Save the current Spotify track to liked songs."""
    try:
        client = _get_client(settings)
        playback = client.current_playback()
        item = (playback or {}).get("item")
        track_id = (item or {}).get("id")
        if not track_id:
            return SpotifyActionResult(False, "No track is playing.")
        client.current_user_saved_tracks_add(tracks=[track_id])
        return SpotifyActionResult(True, "Saved to liked songs.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))


def spotify_create_playlist(
    settings: Settings,
    name: str,
    songs: list[str],
) -> SpotifyActionResult:
    """Create a private playlist and add the requested songs."""
    clean_name = name.strip()
    clean_songs = [song.strip() for song in songs if song.strip()]
    if not clean_name or not clean_songs:
        return SpotifyActionResult(False, "Playlist name or songs are missing.")

    try:
        client = _get_client(settings)
        user = client.current_user()
        uris: list[str] = []
        for song in clean_songs:
            item = _search_first(client, song, "track")
            if item is not None:
                uris.append(item["uri"])

        if not uris:
            return SpotifyActionResult(False, "I couldn't find those songs.")

        playlist = client.user_playlist_create(
            user=user["id"],
            name=clean_name,
            public=False,
            description="Created by Anti Gravity",
        )
        client.playlist_add_items(playlist_id=playlist["id"], items=uris)
        return SpotifyActionResult(True, f"Created {clean_name}.")
    except Exception as error:  # pragma: no cover
        return SpotifyActionResult(False, _spotify_error_message(error))
