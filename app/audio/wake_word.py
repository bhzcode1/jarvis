from threading import Event

import numpy as np
import sounddevice as sd

from config.settings import Settings

try:
    import pvporcupine
except ImportError:  # pragma: no cover - handled by runtime message
    pvporcupine = None

SUPPORTED_BUILTIN_KEYWORDS = {
    "alexa",
    "americano",
    "blueberry",
    "bumblebee",
    "computer",
    "grapefruit",
    "grasshopper",
    "hey google",
    "hey siri",
    "jarvis",
    "ok google",
    "picovoice",
    "porcupine",
    "terminator",
}


def wait_for_wake_word(settings: Settings) -> bool:
    """Block until wake word is detected; return False when disabled/unavailable."""
    if not settings.wake_word_enabled:
        return False

    if pvporcupine is None:
        print("Wake word engine unavailable. Install pvporcupine to enable it.")
        return False

    if not settings.porcupine_access_key:
        print("PORCUPINE_ACCESS_KEY is missing. Wake word disabled.")
        return False

    keyword = settings.wake_word_phrase.lower().strip()
    if keyword not in SUPPORTED_BUILTIN_KEYWORDS:
        print(f"Unsupported wake phrase '{settings.wake_word_phrase}'.")
        print("Use one of the built-in Porcupine keywords instead.")
        return False

    try:
        detector = pvporcupine.create(
            access_key=settings.porcupine_access_key,
            keywords=[keyword],
        )
    except Exception as error:  # pragma: no cover - runtime access key / init guard
        print(f"Wake word initialization failed: {error}")
        return False

    print(f"Listening for wake word: {settings.wake_word_phrase}")
    try:
        with sd.InputStream(
            samplerate=detector.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=detector.frame_length,
        ) as stream:
            while True:
                frame, _ = stream.read(detector.frame_length)
                pcm = np.squeeze(frame).astype(np.int16)
                if detector.process(pcm) >= 0:
                    print("Wake word detected.")
                    return True
    finally:
        detector.delete()


def wake_word_loop(settings: Settings, stop_event: Event) -> bool:
    """Return True when wake word detected, False if stopped/unavailable."""
    while not stop_event.is_set():
        detected = wait_for_wake_word(settings=settings)
        if detected:
            return True
        return False

    return False


def wake_word_ready(settings: Settings) -> bool:
    """Return True when wake-word feature is configured and available."""
    return (
        settings.wake_word_enabled
        and pvporcupine is not None
        and bool(settings.porcupine_access_key)
    )
