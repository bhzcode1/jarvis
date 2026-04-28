import io
import json
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None
try:
    from vosk import KaldiRecognizer, Model, SetLogLevel
except ImportError:  # pragma: no cover
    KaldiRecognizer = None
    Model = None
    SetLogLevel = None

from app.audio.speaker import speak_text
from app.brain.assistant import generate_ai_response
from app.commands.normalizer import normalize_voice_command
from app.commands.router import route_command
from app.commands.translation import build_translation_grammar_phrases
from app.memory.extractor import detect_memory_action
from app.memory.store import read_memory_fact, store_memory_fact
from app.utils.env_bootstrap import ensure_env_file_exists
from app.utils.runtime import get_runtime_base_dir, set_cwd_to_runtime_base_dir
from config.settings import Settings
from speech.microphone_stream import MicrophoneStream
from ui.floating_window import FloatingAssistantWindow
from wakeword.simple_keyword_detector import (
    SimpleKeywordDetector,
    WakeDetectionUnavailableError,
    is_openai_quota_error,
)


_VOSK_MODEL_CACHE: dict[str, object] = {}

_COMMAND_GRAMMAR = [
    "open youtube",
    "youtube",
    "open chrome",
    "open notepad",
    "open calculator",
    "open spotify",
    "play on spotify",
    "play music on spotify",
    "spotify play",
    "pause spotify",
    "resume spotify",
    "next song",
    "previous song",
    "what's playing",
    "save this song",
    "like this song",
    "shuffle on",
    "shuffle off",
    "repeat this song",
    "repeat off",
    "queue song",
    "create playlist",
    "open edge",
    "what time is it",
    "what is the time",
    "what is the date",
    "what day is it",
    "who are you",
    "what is your name",
    "what can you do",
    "what can you open",
    "help",
    "hello",
    "hey",
    "what's up",
    "you there",
    "how are you",
    "how was your day",
    "what's your mood",
    "talk to me",
    "can we just talk",
    "just chat with me",
    "i'm bored",
    "i'm stressed",
    "i had a bad day",
    "what do you think about",
    "do you ever get bored",
    "thank you",
    "translate hello to hindi",
    "translate hello to spanish",
    "translate thank you to french",
    "translate good morning to german",
    "how do you say hello in hindi",
    "search",
    "google",
    "find",
    "[unk]",
] + build_translation_grammar_phrases()


def _pick_input_device() -> int | None:
    """Pick a likely-real microphone device instead of virtual mappers."""
    try:
        devices = sd.query_devices()
    except Exception:
        return None

    candidates: list[int] = []
    for index, device in enumerate(devices):
        if device.get("max_input_channels", 0) <= 0:
            continue
        name = str(device.get("name", "")).lower()
        if "sound mapper" in name or "stereo mix" in name:
            continue
        candidates.append(index)

    return candidates[0] if candidates else None


def _hint_text(text: str, max_length: int = 54) -> str:
    """Return compact text that fits inside the floating window hint line."""
    clean_text = " ".join(text.split())
    if len(clean_text) <= max_length:
        return clean_text
    return f"{clean_text[: max_length - 3]}..."


def _notify_wake(settings: Settings) -> None:
    """Play a quick wake beep so user knows Anti Gravity heard them."""
    if winsound is not None:
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass


def _process_command_transcript(transcript: str, settings: Settings) -> str:
    """Resolve transcript into memory, local command, or AI response."""
    normalized_transcript = normalize_voice_command(transcript)
    if transcript and normalized_transcript != transcript.lower().strip():
        print(f"Normalized command: {normalized_transcript}")

    if not normalized_transcript:
        return "I didn't catch that. Please repeat your command."

    memory_action = detect_memory_action(normalized_transcript)
    if settings.memory_enabled and memory_action.action == "save":
        store_memory_fact(
            key=memory_action.key or "note",
            value=memory_action.value,
            settings=settings,
        )
        return f"I will remember that {memory_action.key or 'note'} is {memory_action.value}."
    if settings.memory_enabled and memory_action.action == "recall":
        remembered_value = read_memory_fact(memory_action.key)
        if remembered_value:
            return f"You told me {memory_action.key} is {remembered_value}."
        return f"I do not have anything saved about {memory_action.key} yet."

    command_result = route_command(normalized_transcript, settings=settings)
    if command_result.handled:
        return command_result.response_text

    return generate_ai_response(user_text=normalized_transcript, settings=settings)


def _get_vosk_model(settings: Settings) -> object | None:
    """Load and cache the offline Vosk model once per app process."""
    if Model is None:
        return None

    model_path = str(Path(settings.vosk_model_path))
    if not Path(model_path).exists():
        return None

    if model_path not in _VOSK_MODEL_CACHE:
        if SetLogLevel is not None:
            SetLogLevel(-1)
        _VOSK_MODEL_CACHE[model_path] = Model(model_path)
    return _VOSK_MODEL_CACHE[model_path]


def _parse_vosk_payload(payload: str) -> str:
    """Extract text from a Vosk JSON result payload."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return ""
    return str(data.get("partial") or data.get("text") or "").strip()


def _listen_for_command_with_vosk(
    stream: MicrophoneStream,
    settings: Settings,
    window: FloatingAssistantWindow,
    stop_event: threading.Event,
) -> str:
    """Listen to one command using Vosk streaming partial recognition."""
    model = _get_vosk_model(settings=settings)
    if model is None or KaldiRecognizer is None:
        return ""

    recognizer = KaldiRecognizer(model, settings.sample_rate, json.dumps(_COMMAND_GRAMMAR))
    recognizer.SetWords(False)

    started_at = time.monotonic()
    speech_started = False
    last_voice_at = started_at
    last_partial_text = ""
    best_text = ""
    recent_levels: list[float] = []

    wait_for_speech_seconds = float(settings.command_wait_for_speech_seconds)
    max_command_seconds = float(settings.command_max_duration_seconds)
    silence_after_speech_seconds = float(settings.command_silence_timeout_seconds)
    min_command_seconds = 0.9
    min_voice_rms = 0.00045

    print("Command listener ready. Speak now...")
    while not stop_event.is_set():
        now = time.monotonic()
        frame = stream.read_frame(timeout=0.4)
        if frame is None:
            if not speech_started and now - started_at > wait_for_speech_seconds:
                break
            if speech_started and now - last_voice_at > silence_after_speech_seconds:
                break
            continue

        level = max(0.0, min(frame.rms_level / 0.08, 1.0))
        window.set_audio_level(level)
        recent_levels.append(frame.rms_level)
        if len(recent_levels) > 80:
            recent_levels.pop(0)

        sorted_levels = sorted(recent_levels)
        quiet_count = max(1, len(sorted_levels) // 4)
        noise_floor = sum(sorted_levels[:quiet_count]) / quiet_count
        voice_threshold = max(min_voice_rms, noise_floor * 2.0)

        if frame.rms_level >= voice_threshold:
            speech_started = True
            last_voice_at = now

        pcm_frame = np.clip(frame.samples, -1.0, 1.0)
        pcm_frame = (pcm_frame * 32767.0).astype(np.int16)
        if recognizer.AcceptWaveform(pcm_frame.tobytes()):
            final_text = _parse_vosk_payload(recognizer.Result())
            if final_text:
                best_text = final_text
                print(f"[command] final: {final_text}")
                window.set_status("Listening", _hint_text(final_text))
        else:
            partial_text = _parse_vosk_payload(recognizer.PartialResult())
            if partial_text and partial_text != last_partial_text:
                best_text = partial_text
                last_partial_text = partial_text
                print(f"[command] partial: {partial_text}")
                window.set_status("Listening", _hint_text(partial_text))

        heard_enough = now - started_at >= min_command_seconds
        user_stopped = speech_started and now - last_voice_at >= silence_after_speech_seconds
        no_speech = not speech_started and now - started_at >= wait_for_speech_seconds
        too_long = now - started_at >= max_command_seconds
        if heard_enough and (user_stopped or no_speech or too_long):
            break

    final_text = _parse_vosk_payload(recognizer.FinalResult())
    if final_text:
        best_text = final_text
        print(f"[command] final: {final_text}")
    return best_text.strip()


def _record_command_samples(
    stream: MicrophoneStream,
    window: FloatingAssistantWindow,
    stop_event: threading.Event,
    sample_rate: int,
    settings: Settings,
) -> np.ndarray:
    """Collect command audio and stop early after the user finishes speaking."""
    max_samples = int(sample_rate * float(settings.command_max_duration_seconds))
    min_samples = int(sample_rate * 0.8)
    voice_threshold = 0.0008
    silence_after_speech_seconds = float(settings.command_silence_timeout_seconds)
    max_wait_for_speech_seconds = float(settings.command_wait_for_speech_seconds)
    chunks: list[np.ndarray] = []
    collected = 0
    started_at = time.monotonic()
    last_voice_at = started_at
    speech_started = False

    while collected < max_samples and not stop_event.is_set():
        now = time.monotonic()
        frame = stream.read_frame(timeout=0.3)
        if frame is None:
            if now - started_at > float(settings.command_max_duration_seconds) + 2.0:
                break
            continue

        level = max(0.0, min(frame.rms_level / 0.08, 1.0))
        window.set_audio_level(level)
        chunks.append(frame.samples)
        collected += frame.samples.shape[0]

        if frame.rms_level >= voice_threshold:
            speech_started = True
            last_voice_at = now

        recorded_enough = collected >= min_samples
        user_stopped_talking = speech_started and (now - last_voice_at) >= silence_after_speech_seconds
        no_speech_timeout = not speech_started and (now - started_at) >= max_wait_for_speech_seconds
        if recorded_enough and (user_stopped_talking or no_speech_timeout):
            break

    if not chunks:
        return np.array([], dtype=np.float32)
    return np.concatenate(chunks)


def _transcribe_command(samples: np.ndarray, settings: Settings) -> str:
    """Transcribe command audio with offline Vosk, then OpenAI as fallback."""
    if samples.size == 0:
        return ""

    vosk_text = _transcribe_command_with_vosk(samples=samples, settings=settings)
    if vosk_text:
        return vosk_text
    if settings.wake_word_backend == "vosk":
        return ""

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for command transcription.")

    wav_bytes = io.BytesIO()
    sf.write(wav_bytes, samples, settings.sample_rate, format="WAV")
    wav_bytes.seek(0)
    wav_bytes.name = "anti_gravity_command.wav"

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=wav_bytes,
            language="en",
            timeout=30.0,
        )
    except Exception as error:
        if is_openai_quota_error(error):
            raise RuntimeError(
                "OpenAI quota is exhausted. Add billing/credits before voice transcription can work."
            ) from error
        raise
    return (transcript.text or "").strip()


def _transcribe_command_with_vosk(samples: np.ndarray, settings: Settings) -> str:
    """Transcribe command audio locally using Vosk when the model is installed."""
    if KaldiRecognizer is None:
        return ""

    model = _get_vosk_model(settings=settings)
    if model is None:
        return ""
    recognizer = KaldiRecognizer(model, settings.sample_rate)
    recognizer.SetWords(False)

    pcm_samples = np.clip(samples, -1.0, 1.0)
    pcm_samples = (pcm_samples * 32767.0).astype(np.int16)
    recognizer.AcceptWaveform(pcm_samples.tobytes())

    try:
        data = json.loads(recognizer.FinalResult())
    except json.JSONDecodeError:
        return ""
    return str(data.get("text") or "").strip()


def _run_command_turn(
    stream: MicrophoneStream,
    settings: Settings,
    window: FloatingAssistantWindow,
    stop_event: threading.Event,
) -> None:
    """Listen for one post-wake command, answer it, then return to wake mode."""
    stream.clear_buffer()
    window.set_status("Listening", "Speak your command now")
    print("Listening for command...")

    if settings.wake_word_backend == "vosk":
        transcript = _listen_for_command_with_vosk(
            stream=stream,
            settings=settings,
            window=window,
            stop_event=stop_event,
        )
    else:
        samples = _record_command_samples(
            stream=stream,
            window=window,
            stop_event=stop_event,
            sample_rate=settings.sample_rate,
            settings=settings,
        )
        if stop_event.is_set():
            return
        transcript = _transcribe_command(samples=samples, settings=settings)

    if stop_event.is_set():
        return

    window.set_audio_level(0.0)
    window.set_status("Thinking", "Understanding your command")
    print(f"Command transcript: {transcript or '[No speech detected]'}")

    window.set_status("Thinking", _hint_text(transcript or "No clear speech detected"))
    response_text = _process_command_transcript(transcript=transcript, settings=settings)
    print(f"Assistant: {response_text}")

    if stop_event.is_set():
        return
    window.set_status("Speaking", _hint_text(response_text))
    try:
        speak_text(text=response_text, settings=settings)
    except Exception as error:
        print(f"[warn] TTS failed: {error}")


def _assistant_worker(window: FloatingAssistantWindow, stop_event: threading.Event) -> None:
    """Run microphone, wake detection, command processing, and speech in background."""
    settings = Settings()
    selected_device = _pick_input_device()
    stream = MicrophoneStream(
        sample_rate=settings.sample_rate,
        channels=settings.channels,
        block_size=512,
        input_device=selected_device,
    )
    detector = SimpleKeywordDetector(
        keyword=settings.wake_word_phrase,
        access_key=settings.porcupine_access_key,
        openai_api_key=settings.openai_api_key,
        sample_rate=settings.sample_rate,
        fallback_window_seconds=2.0,
        fallback_stride_seconds=0.7,
        min_voice_rms=0.0008,
        min_transcribe_interval_seconds=1.4,
        backend=settings.wake_word_backend,
        vosk_model_path=settings.vosk_model_path,
        level_callback=window.set_audio_level,
    )

    print("Starting microphone stream...")
    print(f"Input device index: {selected_device if selected_device is not None else 'default'}")
    print(f"Say '{settings.wake_word_phrase}' to trigger detection.")
    print("Listening...")
    window.set_status("Listening", f"Say '{settings.wake_word_phrase}'")

    try:
        stream.start()
        while not stop_event.is_set():
            result = detector.listen_until_detected(stream=stream, stop_event=stop_event)
            if not result.detected:
                break

            window.set_status("Awake", f"{settings.assistant_name} heard you")
            print("Wake phrase detected.")
            print(f"Matched transcript: {result.transcript}")
            _notify_wake(settings=settings)
            time.sleep(0.25)
            _run_command_turn(
                stream=stream,
                settings=settings,
                window=window,
                stop_event=stop_event,
            )
            if not stop_event.is_set():
                window.set_status("Listening", f"Say '{settings.wake_word_phrase}'")
    except WakeDetectionUnavailableError as error:
        print("Wake-word provider unavailable.")
        print(f"Reason: {error}")
        window.set_status("Quota needed", "Add OpenAI billing or use Porcupine key")
    except Exception as error:
        print("Wake-word runtime failed.")
        print(f"Reason: {error}")
        window.set_status("Setup problem", _hint_text(str(error)))
    finally:
        window.set_audio_level(0.0)
        stream.stop()


def main() -> None:
    """Run Anti Gravity with a floating reactive UI and background wake detection."""
    set_cwd_to_runtime_base_dir()
    ensure_env_file_exists(runtime_base_dir=get_runtime_base_dir())

    stop_event = threading.Event()
    window = FloatingAssistantWindow(on_close=stop_event.set)
    worker = threading.Thread(
        target=_assistant_worker,
        args=(window, stop_event),
        daemon=True,
        name="anti-gravity-assistant-worker",
    )
    worker.start()

    try:
        window.run()
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        stop_event.set()
        worker.join(timeout=2.0)


if __name__ == "__main__":
    main()
