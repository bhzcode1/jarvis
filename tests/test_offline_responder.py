from app.brain.offline_responder import generate_offline_response
from config.settings import Settings


def test_offline_responder_asks_to_repeat_for_unknown_text() -> None:
    response = generate_offline_response("blurred unclear request", Settings())
    assert "repeat" in response.lower()
