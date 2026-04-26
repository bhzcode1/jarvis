from pathlib import Path

from faster_whisper import WhisperModel

from config.settings import Settings


def transcribe_audio_file(audio_path: Path, settings: Settings) -> str:
    """Transcribe a WAV file to text using Faster-Whisper."""
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = WhisperModel(
        model_size_or_path=settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )

    segments, _ = model.transcribe(
        str(audio_path),
        language=settings.whisper_language,
        vad_filter=True,
    )

    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    return transcript
