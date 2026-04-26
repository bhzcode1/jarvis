import argparse

from app.audio.recorder import record_microphone_audio
from app.audio.speaker import speak_text
from app.audio.transcriber import transcribe_audio_file
from app.audio.wake_word import wait_for_wake_word, wake_word_ready
from app.brain.assistant import generate_ai_response
from app.commands.router import route_command
from app.doctor import run_doctor_checks
from app.memory.extractor import detect_memory_action
from app.memory.store import read_memory_fact, store_memory_fact
from app.utils.logger import configure_logging, get_logger
from app.utils.runtime import get_runtime_base_dir, set_cwd_to_runtime_base_dir
from app.utils.env_bootstrap import ensure_env_file_exists
from config.settings import Settings, validate_runtime_settings

logger = get_logger(__name__)


def _process_transcript(transcript: str, settings: Settings) -> str:
    """Resolve transcript into memory/command/AI response."""
    if not transcript:
        return "I could not detect clear speech. Please try again."

    memory_action = detect_memory_action(transcript)
    if settings.memory_enabled and memory_action.action == "save":
        store_memory_fact(
            key=memory_action.key or "note",
            value=memory_action.value,
            settings=settings,
        )
        return f"I will remember that {memory_action.key or 'note'} is {memory_action.value}."
    if settings.memory_enabled and memory_action.action == "recall":
        remembered_value = read_memory_fact(memory_action.key)
        return (
            f"You told me {memory_action.key} is {remembered_value}."
            if remembered_value
            else f"I do not have anything saved about {memory_action.key} yet."
        )

    command_result = route_command(transcript, settings=settings)
    if command_result.handled:
        return command_result.response_text

    return generate_ai_response(user_text=transcript, settings=settings)


def run_single_turn(settings: Settings) -> None:
    """Run one record -> transcribe -> respond cycle."""
    try:
        saved_path = record_microphone_audio(settings=settings)
        transcript = transcribe_audio_file(audio_path=saved_path, settings=settings)
        response_text = _process_transcript(transcript=transcript, settings=settings)
    except Exception as error:  # pragma: no cover - runtime guard
        logger.exception("Single turn processing failed: %s", error)
        saved_path = None
        transcript = ""
        response_text = "I hit an internal error while processing your request."

    print(f"Done. File created at: {saved_path or '[Unavailable]'}")
    print(f"Transcript: {transcript or '[No speech detected]'}")
    print(f"Assistant: {response_text}")
    try:
        speak_text(text=response_text, settings=settings)
    except Exception as error:  # pragma: no cover - runtime guard
        logger.exception("TTS failed: %s", error)


def run_wake_word_loop(settings: Settings) -> None:
    """Keep listening for wake-word and process one request per detection."""
    print("Wake-word mode enabled. Press Ctrl+C to stop.")
    try:
        while True:
            detected = wait_for_wake_word(settings=settings)
            if detected:
                run_single_turn(settings=settings)
            else:
                break
    except KeyboardInterrupt:
        print("Wake-word loop stopped by user.")


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(description="Jarvis voice assistant runtime.")
    parser.add_argument(
        "--mode",
        choices=("auto", "once", "wake"),
        default="auto",
        help="Runtime mode: auto chooses wake if configured; once runs one request; wake loops.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run startup diagnostics and exit.",
    )
    return parser


def main() -> None:
    """Application entry point for voice assistant runtime."""
    set_cwd_to_runtime_base_dir()
    base_dir = get_runtime_base_dir()
    ensure_env_file_exists(runtime_base_dir=base_dir)
    configure_logging(log_file=base_dir / "data" / "logs" / "jarvis.log")
    args = _build_arg_parser().parse_args()
    settings = Settings()

    runtime_warnings = validate_runtime_settings(settings=settings)
    for warning in runtime_warnings:
        logger.warning("Config warning: %s", warning)

    if args.doctor:
        for check in run_doctor_checks(settings=settings):
            print(check)
        return

    if args.mode == "once":
        run_single_turn(settings=settings)
        return
    if args.mode == "wake":
        run_wake_word_loop(settings=settings)
        return

    if wake_word_ready(settings=settings):
        run_wake_word_loop(settings=settings)
    else:
        run_single_turn(settings=settings)


if __name__ == "__main__":
    main()
