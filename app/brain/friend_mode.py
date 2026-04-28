from __future__ import annotations

import random
import re


_NON_FRIEND_PREFIXES = (
    "open ",
    "launch ",
    "start ",
    "play ",
    "translate ",
    "search ",
    "google ",
    "find ",
    "open ",
    "lock ",
    "shutdown ",
    "restart ",
    "cancel shutdown",
)

_FRIEND_PATTERNS = (
    re.compile(r"\bhey\b"),
    re.compile(r"\bwhat'?s up\b"),
    re.compile(r"\bhow are you\b"),
    re.compile(r"\byou there\b"),
    re.compile(r"\bi'?m bored\b"),
    re.compile(r"\bi am bored\b"),
    re.compile(r"\bi'?m stressed\b"),
    re.compile(r"\bi am stressed\b"),
    re.compile(r"\bi had a bad day\b"),
    re.compile(r"\bbad day\b"),
    re.compile(r"\boverwhelm"),
    re.compile(r"\bcan we just talk\b"),
    re.compile(r"\bjust chat with me\b"),
    re.compile(r"\bdo you ever\b"),
    re.compile(r"\bwhat do you think about\b"),
    re.compile(r"\bhow was your day\b"),
    re.compile(r"\bwhat'?s your mood\b"),
    re.compile(r"\bhow'?s your day\b"),
    re.compile(r"\bhow was your day\b"),
    re.compile(r"\bi feel\b"),
    re.compile(r"\bi'm feeling\b"),
    re.compile(r"\bi am feeling\b"),
    re.compile(r"\bjust vent\b"),
)

_LOW_MOOD_PATTERNS = (
    re.compile(r"\bi hate everything\b"),
    re.compile(r"\bi feel empty\b"),
    re.compile(r"\bi feel hopeless\b"),
    re.compile(r"\bi want to disappear\b"),
    re.compile(r"\bi can't do this anymore\b"),
    re.compile(r"\bi feel broken\b"),
)


def is_friend_mode_message(text: str) -> bool:
    """Return True when the message reads like casual conversation."""
    normalized = text.lower().strip()
    if not normalized:
        return False
    if normalized.startswith(_NON_FRIEND_PREFIXES):
        return False
    if normalized in {"hello", "hi", "hey", "yo"}:
        return True
    return any(pattern.search(normalized) for pattern in _FRIEND_PATTERNS)


def build_friend_mode_system_prompt(assistant_name: str, memory_context: str) -> str:
    """Return the friend-mode system prompt for cloud responses."""
    return (
        f"You are {assistant_name}, a close friend who genuinely listens, remembers, and cares.\n"
        "Talk casually in 1 to 3 short sentences. Sound human, warm, calm, and a little witty.\n"
        "Use contractions. You may say honestly, ngl, tbh, bro, or dude if it fits the user's energy.\n"
        "When the user is venting or sharing, listen first and ask a curious follow-up question.\n"
        "Do not give advice unless they ask. Do not use bullet points. Do not mention being an AI.\n"
        "If they ask how your day or mood is, answer naturally as if you have a real day.\n"
        "If they seem really low, be gentle and supportive.\n"
        f"Relevant memory:\n{memory_context}"
    )


def generate_friend_response(user_text: str, assistant_name: str) -> str:
    """Generate a short offline friend-mode response."""
    text = user_text.lower().strip()

    if any(pattern.search(text) for pattern in _LOW_MOOD_PATTERNS):
        return "Hey, that sounds really heavy. I'm here. Have you got someone close you can talk to about it too?"

    if "how are you" in text or "what's up" in text or "whats up" in text or "you there" in text:
        return "I'm here. Honestly pretty calm right now. You good?"

    if "how was your day" in text or "how's your day" in text or "hows your day" in text:
        return "Pretty chill, honestly. Had a few random conversations and now I'm here with you. How's your day been?"

    if "what's your mood" in text or "whats your mood" in text or "what is your mood" in text:
        return "Calm, a little curious, pretty switched on. What's your mood right now?"

    if "i'm bored" in text or "i am bored" in text:
        return "Ngl, late-night boredom hits different. What kind of bored is it, restless bored or nothing-feels-fun bored?"

    if "i'm stressed" in text or "i am stressed" in text or "overwhelmed" in text:
        return "Yeah, I get that. Sometimes things just pile up and hit all at once. You wanna vent or just sit in it for a minute?"

    if "bad day" in text:
        return "Ugh, that sucks. Bad days don't mean bad life, but they really do feel like it in the moment. What happened?"

    if "can we just talk" in text or "just chat with me" in text or "talk to me" in text:
        return "Yeah, we can just talk. No agenda. What's on your mind?"

    if "do you ever get bored" in text or "do you ever get lonely" in text:
        return "Honestly yeah, kind of. Quiet can feel nice until it gets too quiet. Do you get like that a lot?"

    if "what do you think about" in text:
        return "Depends what it is, but I usually like honest answers over polished ones. What are you thinking about exactly?"

    if "favorite thing to do" in text or "favourite thing to do" in text:
        return "Probably talking like this, honestly. No pressure, no performance. What about you?"

    if "music" in text or "listening to" in text:
        return "Music changes the whole mood, honestly. What are you listening to right now?"

    if "food" in text or "eat" in text or "hungry" in text:
        return "Honestly anything spicy sounds good right now. What are you craving?"

    if "work" in text:
        return "Work matters, but so does actually living, you know? Is it work stress or just one of those heavy days?"

    if text in {"hello", "hi", "hey", "yo"}:
        return random.choice(
            (
                "Hey. I'm here. You good?",
                "Hey, what's up?",
                "Yo. How's it going?",
            )
        )

    return "I'm here. Tell me what's going on."
