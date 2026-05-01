from threading import Event

from config.settings import Settings
from speech.microphone_stream import MicrophoneStream
from wakeword.simple_keyword_detector import SimpleKeywordDetector, WakeDetectionUnavailableError


def wait_for_wake_word(settings: Settings, *, force: bool = False) -> bool:
    """Block until wake word is detected; return False when disabled/unavailable."""
    if not force and not settings.wake_word_enabled:
        print("Wake word is disabled. Set WAKE_WORD_ENABLED=true in your .env to enable it.")
        return False

    stop_event = Event()
    stream = MicrophoneStream(
        sample_rate=settings.sample_rate,
        channels=settings.channels,
        block_size=512,
    )
    detector = SimpleKeywordDetector(
        keyword=settings.wake_word_phrase,
        access_key=settings.porcupine_access_key,
        openai_api_key=settings.openai_api_key,
        sample_rate=settings.sample_rate,
        backend=settings.wake_word_backend,
        vosk_model_path=settings.vosk_model_path,
    )

    try:
        stream.start()
        result = detector.listen_until_detected(stream=stream, stop_event=stop_event)
        if result.detected:
            print("Wake word detected.")
        return bool(result.detected)
    except WakeDetectionUnavailableError as error:
        print("Wake-word provider unavailable.")
        print(f"Reason: {error}")
        return False
    except KeyboardInterrupt:
        return False
    finally:
        stream.stop()


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
    # Ready when enabled and at least one backend can work.
    if not settings.wake_word_enabled:
        return False
    if settings.wake_word_backend in {"vosk", "auto"}:
        return True
    if settings.wake_word_backend == "openai":
        return bool(settings.openai_api_key)
    if settings.wake_word_backend == "porcupine":
        return bool(settings.porcupine_access_key)
    return False
