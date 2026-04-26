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
