from app.brain.friend_mode import (
    generate_friend_response,
    is_friend_mode_message,
)


def test_detect_friend_mode_for_casual_chat() -> None:
    assert is_friend_mode_message("hey what's up") is True
    assert is_friend_mode_message("i'm stressed") is True


def test_do_not_detect_friend_mode_for_commands() -> None:
    assert is_friend_mode_message("open chrome") is False
    assert is_friend_mode_message("translate hello to hindi") is False


def test_friend_response_for_bad_day() -> None:
    response = generate_friend_response("i had a bad day", assistant_name="Anti Gravity")
    assert "what happened" in response.lower() or "bad days" in response.lower()


def test_friend_response_for_how_are_you() -> None:
    response = generate_friend_response("how are you", assistant_name="Anti Gravity")
    assert "you good" in response.lower() or "pretty calm" in response.lower()


def test_friend_response_for_song_on_repeat() -> None:
    response = generate_friend_response("i've been listening to this song on repeat", assistant_name="Anti Gravity")
    assert "what song" in response.lower()
