import app.commands.router as router
from config.settings import Settings
from app.commands.router import route_command


def _test_settings() -> Settings:
    return Settings(system_control_enabled=False)


def test_route_time_command() -> None:
    result = route_command("what is the time", settings=_test_settings())
    assert result.handled is True
    assert "current time" in result.response_text.lower()


def test_route_unknown_command() -> None:
    result = route_command("do something impossible", settings=_test_settings())
    assert result.handled is False


def test_route_disabled_system_control_message() -> None:
    result = route_command("shutdown the computer", settings=_test_settings())
    assert result.handled is True
    assert "system control is disabled" in result.response_text.lower()


def test_route_open_app_command(monkeypatch) -> None:
    monkeypatch.setattr(router, "open_application", lambda app_name: app_name == "chrome")

    result = route_command("open chrome", settings=_test_settings())
    assert result.handled is True
    assert "opening chrome" in result.response_text.lower()


def test_route_spotify_play_command(monkeypatch) -> None:
    monkeypatch.setattr(
        router,
        "spotify_play",
        lambda settings, query, item_type: type(
            "SpotifyResult",
            (),
            {"success": True, "message": f"Playing {query} as {item_type}."},
        )(),
    )

    result = route_command("play believer on spotify", settings=_test_settings())
    assert result.handled is True
    assert "playing believer as track" in result.response_text.lower()


def test_route_spotify_pause_command(monkeypatch) -> None:
    monkeypatch.setattr(
        router,
        "spotify_pause",
        lambda settings: type("SpotifyResult", (), {"success": True, "message": "Paused."})(),
    )

    result = route_command("pause spotify", settings=_test_settings())
    assert result.handled is True
    assert result.response_text == "Paused."


def test_route_spotify_current_track_command(monkeypatch) -> None:
    monkeypatch.setattr(
        router,
        "spotify_current_track",
        lambda settings: type(
            "SpotifyResult",
            (),
            {"success": True, "message": "That's Levitating by Dua Lipa."},
        )(),
    )

    result = route_command("what's playing", settings=_test_settings())
    assert result.handled is True
    assert "levitating" in result.response_text.lower()


def test_route_spotify_queue_command(monkeypatch) -> None:
    monkeypatch.setattr(
        router,
        "spotify_queue",
        lambda settings, query: type("SpotifyResult", (), {"success": True, "message": f"Queued {query}."})(),
    )

    result = route_command("queue levitating after this", settings=_test_settings())
    assert result.handled is True
    assert "queued levitating" in result.response_text.lower()


def test_route_translation_command() -> None:
    result = route_command("translate hello to hindi", settings=_test_settings())
    assert result.handled is True
    assert "in hindi" in result.response_text.lower()
    assert "namaste" in result.response_text.lower()


def test_route_translation_command_to_tamil() -> None:
    result = route_command("translate thank you to tamil", settings=_test_settings())
    assert result.handled is True
    assert "in tamil" in result.response_text.lower()
    assert "nandri" in result.response_text.lower()


def test_route_translation_command_language_alias() -> None:
    result = route_command("how do you say hello in bangla", settings=_test_settings())
    assert result.handled is True
    assert "in bengali" in result.response_text.lower()
    assert "nomoskar" in result.response_text.lower()


def test_route_translation_command_for_unsupported_phrase() -> None:
    result = route_command("translate quantum tunnel to hindi", settings=_test_settings())
    assert result.handled is True
    assert "common short phrases offline" in result.response_text.lower()
