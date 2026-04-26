from datetime import datetime
from pathlib import Path

import sounddevice as sd
import soundfile as sf

from config.settings import Settings, get_recordings_dir


def build_recording_path() -> Path:
    """Create a timestamped path for a new recording file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return get_recordings_dir() / f"recording_{timestamp}.wav"


def record_microphone_audio(settings: Settings) -> Path:
    """Record microphone audio for configured duration and save as WAV."""
    total_frames = settings.sample_rate * settings.recording_duration_seconds

    print(
        f"Recording for {settings.recording_duration_seconds} seconds "
        f"at {settings.sample_rate} Hz..."
    )

    audio_data = sd.rec(
        frames=total_frames,
        samplerate=settings.sample_rate,
        channels=settings.channels,
        dtype="float32",
    )
    sd.wait()

    output_path = build_recording_path()
    sf.write(
        file=output_path,
        data=audio_data,
        samplerate=settings.sample_rate,
    )

    print(f"Recording saved to: {output_path}")
    return output_path
