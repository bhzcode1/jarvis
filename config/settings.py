from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from app.utils.runtime import get_runtime_base_dir


class Settings(BaseSettings):
    """Application configuration loaded from environment and defaults."""

    assistant_name: str = "Anti Gravity"
    openai_api_key: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    ai_temperature: float = 0.4
    ai_max_tokens: int = 200
    sample_rate: int = 16_000
    channels: int = 1
    recording_duration_seconds: int = 5
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_language: str = "en"
    tts_rate: int = 155
    tts_volume: float = 1.0
    tts_voice_name: Optional[str] = None
    command_wait_for_speech_seconds: float = 10.0
    command_silence_timeout_seconds: float = 5.0
    command_max_duration_seconds: float = 20.0
    system_control_enabled: bool = False
    system_shutdown_delay_seconds: int = 30
    memory_enabled: bool = True
    memory_max_items: int = 200
    wake_word_enabled: bool = False
    wake_word_phrase: str = "hey gekko"
    porcupine_access_key: Optional[str] = None
    vosk_model_path: str = "data/models/vosk-model-small-en-us-0.15"
    wake_word_backend: str = "vosk"
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    spotify_redirect_uri: str = "http://127.0.0.1:8888/callback"
    spotify_device_name: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_project_root() -> Path:
    """Return absolute path to the project root directory."""
    return get_runtime_base_dir()


def get_recordings_dir() -> Path:
    """Return recordings directory path and ensure it exists."""
    recordings_dir = get_project_root() / "data" / "recordings"
    recordings_dir.mkdir(parents=True, exist_ok=True)
    return recordings_dir


def get_memory_file_path() -> Path:
    """Return path for persistent assistant memory file."""
    memory_dir = get_project_root() / "data" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir / "profile.json"


def validate_runtime_settings(settings: Settings) -> List[str]:
    """Return non-fatal runtime configuration warnings."""
    warnings: List[str] = []

    if settings.channels < 1:
        warnings.append("CHANNELS must be >= 1.")
    if settings.sample_rate < 8000:
        warnings.append("SAMPLE_RATE is very low; speech recognition quality may drop.")
    if settings.recording_duration_seconds <= 0:
        warnings.append("RECORDING_DURATION_SECONDS must be greater than 0.")
    if settings.command_wait_for_speech_seconds <= 0:
        warnings.append("COMMAND_WAIT_FOR_SPEECH_SECONDS must be greater than 0.")
    if settings.command_silence_timeout_seconds <= 0:
        warnings.append("COMMAND_SILENCE_TIMEOUT_SECONDS must be greater than 0.")
    if settings.command_max_duration_seconds <= 0:
        warnings.append("COMMAND_MAX_DURATION_SECONDS must be greater than 0.")
    if not 0.0 <= settings.tts_volume <= 1.0:
        warnings.append("TTS_VOLUME should be between 0.0 and 1.0.")
    if not 0.0 <= settings.ai_temperature <= 2.0:
        warnings.append("AI_TEMPERATURE should be between 0.0 and 2.0.")
    if settings.ai_max_tokens <= 0:
        warnings.append("AI_MAX_TOKENS must be greater than 0.")
    if settings.wake_word_enabled and not settings.porcupine_access_key:
        warnings.append("Wake word is enabled but PORCUPINE_ACCESS_KEY is missing; Vosk/offline mode may be used.")
    if settings.wake_word_backend not in {"auto", "porcupine", "vosk", "openai"}:
        warnings.append("WAKE_WORD_BACKEND must be one of: auto, porcupine, vosk, openai.")
    if bool(settings.spotify_client_id) != bool(settings.spotify_client_secret):
        warnings.append("Set both SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET for Spotify control.")
    if settings.system_control_enabled and settings.system_shutdown_delay_seconds < 5:
        warnings.append("SYSTEM_SHUTDOWN_DELAY_SECONDS should be at least 5 for safety.")

    return warnings
