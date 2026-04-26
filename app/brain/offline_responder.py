from __future__ import annotations

from datetime import datetime

from config.settings import Settings


def generate_offline_response(user_text: str, settings: Settings) -> str:
    """Return a useful local response when cloud AI is unavailable."""
    text = user_text.lower().strip()
    if not text:
        return "I did not hear a command. Please try again."

    if any(phrase in text for phrase in ("hello", "hi", "hey")):
        return "Hello. I am listening."

    if "how are you" in text or "are you okay" in text:
        return "I am running locally and ready to help."

    if "your name" in text or "who are you" in text:
        return f"I am {settings.assistant_name}, your desktop voice assistant."

    if "date" in text or "day" in text:
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."

    if "help" in text or "what can you do" in text:
        return (
            "I can answer basic offline questions, tell the time or date, "
            "open YouTube, search the web, open apps, and remember simple notes."
        )

    if "thank" in text:
        return "You are welcome."

    if "joke" in text:
        return "Here is one: I tried to make my computer sing, but it had too many processing issues."

    return (
        f"I heard you say: {user_text}. "
        "My offline brain is active, but cloud AI is unavailable right now. "
        "Try asking for the time, date, help, YouTube, search, or an app."
    )
