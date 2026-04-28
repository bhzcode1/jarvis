from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TranslationResult:
    """Normalized result for offline translation requests."""

    handled: bool
    response_text: str


LANGUAGE_ALIASES = {
    "english": "english",
    "eng": "english",
    "assamese": "assamese",
    "asamiya": "assamese",
    "bengali": "bengali",
    "bangla": "bengali",
    "bodo": "bodo",
    "dogri": "dogri",
    "gujarati": "gujarati",
    "hindi": "hindi",
    "kannada": "kannada",
    "kashmiri": "kashmiri",
    "konkani": "konkani",
    "maithili": "maithili",
    "malayalam": "malayalam",
    "manipuri": "manipuri",
    "meitei": "manipuri",
    "marathi": "marathi",
    "nepali": "nepali",
    "odia": "odia",
    "oriya": "odia",
    "punjabi": "punjabi",
    "panjabi": "punjabi",
    "sanskrit": "sanskrit",
    "santali": "santali",
    "santhali": "santali",
    "sindhi": "sindhi",
    "tamil": "tamil",
    "telugu": "telugu",
    "urdu": "urdu",
}

SUPPORTED_INDIAN_LANGUAGES = tuple(
    language
    for language in (
        "assamese",
        "bengali",
        "bodo",
        "dogri",
        "gujarati",
        "hindi",
        "kannada",
        "kashmiri",
        "konkani",
        "maithili",
        "malayalam",
        "manipuri",
        "marathi",
        "nepali",
        "odia",
        "punjabi",
        "sanskrit",
        "santali",
        "sindhi",
        "tamil",
        "telugu",
        "urdu",
    )
)

PHRASEBOOK = {
    "hello": {
        "english": "hello",
        "assamese": "namaskar",
        "bengali": "nomoskar",
        "bodo": "namaskar",
        "dogri": "namaskar",
        "gujarati": "namaste",
        "hindi": "namaste",
        "kannada": "namaskara",
        "kashmiri": "adaab",
        "konkani": "namaskar",
        "maithili": "pranam",
        "malayalam": "namaskaram",
        "manipuri": "khurumjari",
        "marathi": "namaskar",
        "nepali": "namaste",
        "odia": "namaskar",
        "punjabi": "sat sri akaal",
        "sanskrit": "namaste",
        "santali": "johar",
        "sindhi": "adaab",
        "tamil": "vanakkam",
        "telugu": "namaskaram",
        "urdu": "adaab",
    },
    "thank you": {
        "english": "thank you",
        "assamese": "dhanyabad",
        "bengali": "dhonnobad",
        "bodo": "dhanyabad",
        "dogri": "dhanyavaad",
        "gujarati": "aabhar",
        "hindi": "dhanyavaad",
        "kannada": "dhanyavaadagalu",
        "kashmiri": "shukriya",
        "konkani": "dev borem korum",
        "maithili": "dhanyabaad",
        "malayalam": "nanni",
        "manipuri": "thagatchari",
        "marathi": "dhanyavaad",
        "nepali": "dhanyabad",
        "odia": "dhanyabad",
        "punjabi": "dhanvaad",
        "sanskrit": "dhanyavaadah",
        "santali": "dhanyabad",
        "sindhi": "mehrbani",
        "tamil": "nandri",
        "telugu": "dhanyavaadalu",
        "urdu": "shukriya",
    },
    "yes": {
        "english": "yes",
        "assamese": "hoi",
        "bengali": "haan",
        "bodo": "hoy",
        "dogri": "haan",
        "gujarati": "haa",
        "hindi": "haan",
        "kannada": "haudu",
        "kashmiri": "aah",
        "konkani": "hoi",
        "maithili": "haan",
        "malayalam": "athe",
        "manipuri": "hoi",
        "marathi": "ho",
        "nepali": "ho",
        "odia": "han",
        "punjabi": "haanji",
        "sanskrit": "aam",
        "santali": "he",
        "sindhi": "haa",
        "tamil": "aam",
        "telugu": "avunu",
        "urdu": "ji haan",
    },
    "no": {
        "english": "no",
        "assamese": "nohoi",
        "bengali": "na",
        "bodo": "nanga",
        "dogri": "na",
        "gujarati": "naa",
        "hindi": "nahin",
        "kannada": "illa",
        "kashmiri": "na",
        "konkani": "na",
        "maithili": "nai",
        "malayalam": "illa",
        "manipuri": "natte",
        "marathi": "nahi",
        "nepali": "hoina",
        "odia": "naa",
        "punjabi": "nahin",
        "sanskrit": "na",
        "santali": "bang",
        "sindhi": "na",
        "tamil": "illai",
        "telugu": "kaadu",
        "urdu": "nahin",
    },
    "good morning": {
        "english": "good morning",
        "assamese": "suprabhat",
        "bengali": "shubho shokal",
        "bodo": "gwd moning",
        "dogri": "shubh savera",
        "gujarati": "suprabhat",
        "hindi": "suprabhat",
        "kannada": "shubhodaya",
        "kashmiri": "subah bakhair",
        "konkani": "dev borem dis",
        "maithili": "subh prabhat",
        "malayalam": "suprabhaatham",
        "manipuri": "nongalei nungshi",
        "marathi": "shubh prabhat",
        "nepali": "shubh prabhat",
        "odia": "suprabhat",
        "punjabi": "sat sri akaal",
        "sanskrit": "suprabhatam",
        "santali": "bhalo sakal",
        "sindhi": "subah jo salam",
        "tamil": "kalai vanakkam",
        "telugu": "shubhodhayam",
        "urdu": "subah bakhair",
    },
    "open chrome": {
        "english": "open chrome",
        "assamese": "chrome khola",
        "bengali": "chrome kholo",
        "bodo": "chrome khula",
        "dogri": "chrome kholo",
        "gujarati": "chrome kholo",
        "hindi": "chrome kholo",
        "kannada": "chrome tere",
        "kashmiri": "chrome kholiv",
        "konkani": "chrome ugad",
        "maithili": "chrome kholu",
        "malayalam": "chrome thurakku",
        "manipuri": "chrome hang-u",
        "marathi": "chrome ughad",
        "nepali": "chrome khola",
        "odia": "chrome khola",
        "punjabi": "chrome kholo",
        "sanskrit": "chrome udghataya",
        "santali": "chrome jhij",
        "sindhi": "chrome kholo",
        "tamil": "chrome thira",
        "telugu": "chrome teruvu",
        "urdu": "chrome kholo",
    },
    "open youtube": {
        "english": "open youtube",
        "assamese": "youtube khola",
        "bengali": "youtube kholo",
        "bodo": "youtube khula",
        "dogri": "youtube kholo",
        "gujarati": "youtube kholo",
        "hindi": "youtube kholo",
        "kannada": "youtube tere",
        "kashmiri": "youtube kholiv",
        "konkani": "youtube ugad",
        "maithili": "youtube kholu",
        "malayalam": "youtube thurakku",
        "manipuri": "youtube hang-u",
        "marathi": "youtube ughad",
        "nepali": "youtube khola",
        "odia": "youtube khola",
        "punjabi": "youtube kholo",
        "sanskrit": "youtube udghataya",
        "santali": "youtube jhij",
        "sindhi": "youtube kholo",
        "tamil": "youtube thira",
        "telugu": "youtube teruvu",
        "urdu": "youtube kholo",
    },
}

TRANSLATION_PATTERNS = (
    re.compile(r"^translate (?P<text>.+?) to (?P<language>[a-z ]+)$"),
    re.compile(r"^how do you say (?P<text>.+?) in (?P<language>[a-z ]+)$"),
    re.compile(r"^say (?P<text>.+?) in (?P<language>[a-z ]+)$"),
)


def _normalize_phrase(text: str) -> str:
    """Return a lowercase phrase suitable for phrasebook lookup."""
    normalized = re.sub(r"[^a-z0-9\s']", " ", text.lower()).strip()
    return re.sub(r"\s+", " ", normalized)


def _resolve_language(language: str) -> str | None:
    """Return the canonical language key, if supported."""
    return LANGUAGE_ALIASES.get(_normalize_phrase(language))


def _find_phrase_entry(text: str) -> dict[str, str] | None:
    """Find a phrasebook row by matching any supported language text."""
    normalized_text = _normalize_phrase(text)
    for row in PHRASEBOOK.values():
        for value in row.values():
            if _normalize_phrase(value) == normalized_text:
                return row
    return None


def build_translation_grammar_phrases() -> list[str]:
    """Return useful translation phrases for the offline Vosk grammar."""
    phrases: list[str] = []
    for language in SUPPORTED_INDIAN_LANGUAGES:
        phrases.append(f"translate hello to {language}")
        phrases.append(f"translate thank you to {language}")
        phrases.append(f"how do you say hello in {language}")
    return phrases


def supported_translation_languages_text() -> str:
    """Return a spoken list of supported Indian languages."""
    names = ", ".join(language.title() for language in SUPPORTED_INDIAN_LANGUAGES)
    return f"I can translate short phrases into these Indian languages: {names}."


def translate_offline_request(text: str) -> TranslationResult:
    """Translate short, common phrases without cloud services."""
    normalized_text = _normalize_phrase(text)
    for pattern in TRANSLATION_PATTERNS:
        match = pattern.match(normalized_text)
        if not match:
            continue

        target_language = _resolve_language(match.group("language"))
        if target_language is None:
            return TranslationResult(
                handled=True,
                response_text=supported_translation_languages_text(),
            )

        phrase = match.group("text").strip(" '\"")
        row = _find_phrase_entry(phrase)
        if row is None:
            return TranslationResult(
                handled=True,
                response_text=(
                    "I can translate common short phrases offline. "
                    "Try hello, thank you, yes, no, good morning, open chrome, or open youtube."
                ),
            )

        translated = row.get(target_language)
        if not translated:
            return TranslationResult(
                handled=True,
                response_text=f"I could not translate that into {target_language.title()} offline yet.",
            )

        return TranslationResult(
            handled=True,
            response_text=f"In {target_language.title()}: {translated}.",
        )

    return TranslationResult(handled=False, response_text="")
