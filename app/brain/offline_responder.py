from __future__ import annotations

from datetime import datetime

from app.commands.translation import supported_translation_languages_text
from config.settings import Settings


def generate_offline_response(user_text: str, settings: Settings) -> str:
    """Return a useful local response when cloud AI is unavailable."""
    text = user_text.lower().strip()
    if not text:
        return "I did not hear a command. Please try again."

    if any(phrase in text for phrase in ("hello", "hi", "hey", "good evening", "good afternoon")):
        return f"Hello. This is {settings.assistant_name}. I am listening."

    if "good morning" in text:
        return f"Good morning. {settings.assistant_name} is ready."

    if "how are you" in text or "are you okay" in text:
        return "I am running locally and ready to help."

    if "talk to me" in text or "speak with me" in text:
        return "I can do that. Ask me something simple, ask for a translation, or tell me to open an app."

    if "your name" in text or "who are you" in text:
        return f"I am {settings.assistant_name}, your desktop voice assistant."

    if "what can you open" in text or "which apps can you open" in text:
        return "I can open common desktop apps, browsers, Start menu apps, and many installed programs by name. Try saying open chrome, open spotify, play believer on spotify, or open notepad."

    if "date" in text or "day" in text:
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."

    if "time" in text:
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}."

    if "translate" in text or "say" in text:
        return supported_translation_languages_text()

    if "help" in text or "what can you do" in text:
        return (
            "I can answer basic offline questions, tell the time or date, "
            "open apps, control Spotify playback, translate short phrases into Indian languages, search the web, and remember simple notes."
        )

    if "thank" in text:
        return "You are welcome."

    if "joke" in text:
        return "Here is one: I tried to make my computer sing, but it had too many processing issues."

    return "I didn't catch that clearly. Please repeat your request."
