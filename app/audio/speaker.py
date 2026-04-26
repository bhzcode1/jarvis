import pyttsx3

from config.settings import Settings


def speak_text(text: str, settings: Settings) -> None:
    """Convert text to speech using offline pyttsx3 engine."""
    if not text.strip():
        return

    engine = pyttsx3.init()
    engine.setProperty("rate", settings.tts_rate)
    engine.setProperty("volume", settings.tts_volume)
    engine.say(text)
    engine.runAndWait()
