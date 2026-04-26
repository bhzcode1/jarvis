import importlib.util
from typing import List

import sounddevice as sd

from config.settings import Settings, validate_runtime_settings


def _module_exists(module_name: str) -> bool:
    """Return whether a module can be imported."""
    return importlib.util.find_spec(module_name) is not None


def run_doctor_checks(settings: Settings) -> List[str]:
    """Run environment and dependency checks, returning human-readable results."""
    checks: List[str] = []

    checks.append("PASS: Python runtime is available.")
    checks.append(f"PASS: Assistant name is '{settings.assistant_name}'.")

    for warning in validate_runtime_settings(settings=settings):
        checks.append(f"WARN: {warning}")

    dependencies = {
        "openai": "OpenAI API integration",
        "faster_whisper": "Speech-to-text",
        "pyttsx3": "Offline text-to-speech",
        "sounddevice": "Microphone capture",
        "soundfile": "Audio file writing",
    }
    for module_name, purpose in dependencies.items():
        if _module_exists(module_name):
            checks.append(f"PASS: {module_name} installed ({purpose}).")
        else:
            checks.append(f"FAIL: {module_name} missing ({purpose}).")

    try:
        input_devices = [d for d in sd.query_devices() if d["max_input_channels"] > 0]
        if input_devices:
            checks.append(f"PASS: Found {len(input_devices)} microphone input device(s).")
        else:
            checks.append("FAIL: No microphone input device found.")
    except Exception as error:  # pragma: no cover - runtime hardware guard
        checks.append(f"FAIL: Could not query audio devices ({error}).")

    if settings.openai_api_key:
        checks.append("PASS: OPENAI_API_KEY appears configured.")
    else:
        checks.append("WARN: OPENAI_API_KEY is missing; AI fallback chat will not work.")

    if settings.wake_word_enabled:
        if _module_exists("pvporcupine") and settings.porcupine_access_key:
            try:
                import pvporcupine

                detector = pvporcupine.create(
                    access_key=settings.porcupine_access_key,
                    keywords=[settings.wake_word_phrase.lower().strip()],
                )
                detector.delete()
                checks.append("PASS: Wake word prerequisites are configured.")
            except Exception as error:  # pragma: no cover - runtime key validation
                checks.append(f"FAIL: Wake word initialization failed ({error}).")
        else:
            checks.append("WARN: Wake word enabled but prerequisites are incomplete.")

    return checks
