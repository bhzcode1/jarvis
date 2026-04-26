from __future__ import annotations

import io
import json
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable, Optional

import numpy as np
import soundfile as sf
from openai import OpenAI
try:
    import pvporcupine
except ImportError:  # pragma: no cover
    pvporcupine = None
try:
    from vosk import KaldiRecognizer, Model, SetLogLevel
except ImportError:  # pragma: no cover
    KaldiRecognizer = None
    Model = None
    SetLogLevel = None

from speech.microphone_stream import AudioFrame, MicrophoneStream


class WakeDetectionUnavailableError(RuntimeError):
    """Raised when wake detection cannot continue with the configured provider."""


def is_openai_quota_error(error: Exception) -> bool:
    """Return True when OpenAI reports missing billing/quota."""
    error_text = str(error).lower()
    return "insufficient_quota" in error_text or "exceeded your current quota" in error_text


@dataclass(slots=True)
class KeywordDetectionResult:
    """Result returned when keyword detection loop finishes one cycle."""

    detected: bool
    transcript: str


class SimpleKeywordDetector:
    """
    Step 2 detector:
    - Collect microphone frames.
    - Run Porcupine keyword engine.
    - Trigger when keyword is detected.
    """

    def __init__(
        self,
        keyword: str = "hey gekko",
        access_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        sample_rate: int = 16000,
        fallback_window_seconds: float = 1.2,
        fallback_stride_seconds: float = 0.8,
        min_voice_rms: float = 0.003,
        min_transcribe_interval_seconds: float = 1.0,
        backend: str = "auto",
        vosk_model_path: Optional[str] = None,
        level_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.keyword = keyword.lower().strip()
        self.keyword_tokens = tuple(part for part in self.keyword.split() if part)
        self.keyword_aliases = self._build_keyword_aliases(self.keyword)
        self.access_key = (access_key or "").strip()
        self.backend = backend.lower().strip()
        self.vosk_model_path = Path(vosk_model_path or "data/models/vosk-model-small-en-us-0.15")
        self.sample_rate = sample_rate
        self.fallback_window_seconds = fallback_window_seconds
        self.fallback_stride_seconds = fallback_stride_seconds
        self.min_voice_rms = min_voice_rms
        self.min_transcribe_interval_seconds = min_transcribe_interval_seconds
        self.level_callback = level_callback
        self._openai_client: Optional[OpenAI] = None
        if openai_api_key and openai_api_key.strip():
            self._openai_client = OpenAI(api_key=openai_api_key.strip())

    def _build_keyword_aliases(self, keyword: str) -> tuple[str, ...]:
        """Return wake phrase variants that sound the same in speech recognition."""
        aliases = {keyword}
        final_token = keyword.split()[-1] if keyword.split() else keyword
        if final_token:
            aliases.add(final_token)
        if "gekko" in keyword or "gecko" in keyword:
            aliases.update(("hey gekko", "gekko", "hey gecko", "gecko"))
        return tuple(sorted(aliases, key=len, reverse=True))

    def _estimate_noise_floor(self, levels: deque[float]) -> float:
        """Estimate quiet-room microphone level from recent RMS values."""
        if not levels:
            return self.min_voice_rms
        sorted_levels = sorted(levels)
        quiet_count = max(1, len(sorted_levels) // 4)
        quiet_average = sum(sorted_levels[:quiet_count]) / quiet_count
        return max(quiet_average, 0.0001)

    def _window_has_voice(self, levels: deque[float], noise_floor: float) -> bool:
        """Return True when the current audio window is likely to contain speech."""
        if not levels:
            return False
        peak_level = max(levels)
        average_level = sum(levels) / len(levels)
        voice_threshold = max(self.min_voice_rms, noise_floor * 1.8)
        return peak_level >= voice_threshold or average_level >= voice_threshold * 0.5

    def _latest_samples(self, sample_chunks: deque[np.ndarray], required_samples: int) -> np.ndarray:
        """Return the newest required_samples from queued audio chunks."""
        samples = np.concatenate(list(sample_chunks))
        if samples.shape[0] <= required_samples:
            return samples
        return samples[-required_samples:]

    def _publish_level(self, rms_level: float) -> None:
        """Send a normalized microphone level to the UI, if one is connected."""
        if self.level_callback is None:
            return
        normalized_level = max(0.0, min(rms_level / 0.08, 1.0))
        self.level_callback(normalized_level)

    def _matches_keyword(self, transcript: str) -> bool:
        """Return True when transcript likely contains wake phrase."""
        normalized = transcript.strip().lower()
        if not normalized:
            return False
        for alias in self.keyword_aliases:
            if alias in normalized:
                return True
        return False

    def _parse_vosk_text(self, payload: str) -> str:
        """Extract recognized text from a Vosk JSON payload."""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return ""
        text = str(data.get("partial") or data.get("text") or "")
        return text.strip().lower()

    def _listen_with_vosk(
        self,
        stream: MicrophoneStream,
        stop_event: Optional[Event] = None,
    ) -> KeywordDetectionResult:
        """Detect the wake phrase locally with Vosk partial recognition."""
        if Model is None or KaldiRecognizer is None:
            raise WakeDetectionUnavailableError(
                "Vosk is not installed. Run: pip install vosk"
            )
        if not self.vosk_model_path.exists():
            raise WakeDetectionUnavailableError(
                f"Vosk model not found at {self.vosk_model_path}. Run Setup_Vosk_Offline_Wake.bat."
            )

        if SetLogLevel is not None:
            SetLogLevel(-1)

        model = Model(str(self.vosk_model_path))
        wake_grammar = list(self.keyword_aliases) + ["[unk]"]
        recognizer = KaldiRecognizer(model, self.sample_rate, json.dumps(wake_grammar))
        recognizer.SetWords(False)
        last_debug_print = 0.0
        last_heard_text = ""

        print(f"Using offline Vosk wake detection. Say: '{self.keyword}'")
        while stop_event is None or not stop_event.is_set():
            frame: Optional[AudioFrame] = stream.read_frame(timeout=0.5)
            now = time.time()
            if frame is None:
                continue

            self._publish_level(frame.rms_level)
            pcm_frame = np.clip(frame.samples, -1.0, 1.0)
            pcm_frame = (pcm_frame * 32767.0).astype(np.int16)

            if recognizer.AcceptWaveform(pcm_frame.tobytes()):
                transcript = self._parse_vosk_text(recognizer.Result())
            else:
                transcript = self._parse_vosk_text(recognizer.PartialResult())

            if transcript and transcript != last_heard_text:
                print(f"[offline] heard: {transcript}")
                last_heard_text = transcript

            if self._matches_keyword(transcript):
                return KeywordDetectionResult(detected=True, transcript=transcript)

            if now - last_debug_print > 3.0:
                print("[debug] offline wake detector alive")
                last_debug_print = now

        return KeywordDetectionResult(detected=False, transcript="")

    def _transcribe_with_openai(self, samples: np.ndarray) -> str:
        """Transcribe audio with OpenAI as fallback when Porcupine is unavailable."""
        if self._openai_client is None:
            raise RuntimeError(
                "Fallback transcription requires OPENAI_API_KEY when PORCUPINE_ACCESS_KEY is missing."
            )

        wav_bytes = io.BytesIO()
        sf.write(wav_bytes, samples, self.sample_rate, format="WAV")
        wav_bytes.seek(0)
        wav_bytes.name = "wake_window.wav"

        try:
            transcript = self._openai_client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=wav_bytes,
                language="en",
                timeout=20.0,
            )
        except Exception as error:
            if is_openai_quota_error(error):
                raise WakeDetectionUnavailableError(
                    "OpenAI quota is exhausted. Add billing/credits, or set a valid PORCUPINE_ACCESS_KEY."
                ) from error
            raise
        return (transcript.text or "").strip().lower()

    def _listen_with_openai_fallback(
        self,
        stream: MicrophoneStream,
        stop_event: Optional[Event] = None,
    ) -> KeywordDetectionResult:
        """Transcribe short windows and match keyword phrase."""
        required_samples = int(self.sample_rate * self.fallback_window_seconds)
        stride_samples = int(self.sample_rate * self.fallback_stride_seconds)
        max_buffer_samples = required_samples + max(stride_samples, 4096)
        sample_chunks: deque[np.ndarray] = deque()
        chunk_lengths: deque[int] = deque()
        chunk_levels: deque[float] = deque()
        recent_levels: deque[float] = deque(maxlen=120)
        buffered_count = 0
        samples_since_check = 0
        last_transcribe_at = 0.0
        last_debug_print = 0.0
        last_no_frame_print = 0.0
        last_heartbeat = 0.0
        last_silence_print = 0.0
        frames_seen = 0

        print(f"Using optimized OpenAI fallback wake detection. Say: '{self.keyword}'")
        while stop_event is None or not stop_event.is_set():
            now = time.time()
            if now - last_heartbeat > 2.0:
                print("[debug] detector loop alive")
                last_heartbeat = now

            frame: Optional[AudioFrame] = stream.read_frame(timeout=0.5)
            if frame is None:
                if now - last_no_frame_print > 2.0:
                    print("[debug] waiting for microphone frames...")
                    last_no_frame_print = now
                continue

            self._publish_level(frame.rms_level)
            frame_len = frame.samples.shape[0]
            sample_chunks.append(frame.samples)
            chunk_lengths.append(frame_len)
            chunk_levels.append(frame.rms_level)
            recent_levels.append(frame.rms_level)
            buffered_count += frame_len
            samples_since_check += frame_len
            frames_seen += 1

            # Keep a little more than one window so block-size rounding cannot
            # drop us just below the transcribe threshold forever.
            while buffered_count > max_buffer_samples and chunk_lengths:
                oldest = chunk_lengths.popleft()
                sample_chunks.popleft()
                chunk_levels.popleft()
                buffered_count -= oldest

            if now - last_debug_print > 2.0:
                noise_floor = self._estimate_noise_floor(recent_levels)
                print(
                    f"[debug] frames_seen={frames_seen} frame_len={frame_len} "
                    f"buffered={buffered_count}/{required_samples} "
                    f"noise={noise_floor:.5f}"
                )
                last_debug_print = now

            if buffered_count < required_samples:
                continue
            if samples_since_check < stride_samples:
                continue
            samples_since_check = 0

            if now - last_transcribe_at < self.min_transcribe_interval_seconds:
                continue

            noise_floor = self._estimate_noise_floor(recent_levels)
            if not self._window_has_voice(chunk_levels, noise_floor):
                if now - last_silence_print > 2.0:
                    print("[debug] silence/background skipped")
                    last_silence_print = now
                continue

            last_transcribe_at = now
            print(f"[debug] transcribing fallback window ({buffered_count} samples)")

            window = self._latest_samples(sample_chunks, required_samples)
            # Reset window after each attempt for predictable cadence.
            sample_chunks.clear()
            chunk_lengths.clear()
            chunk_levels.clear()
            buffered_count = 0
            samples_since_check = 0
            print("[debug] sending audio to OpenAI...")
            transcript = self._transcribe_with_openai(window)
            print("[debug] received transcription from OpenAI")
            print(f"Heard: {transcript or '[silence]'}")
            if self._matches_keyword(transcript):
                return KeywordDetectionResult(detected=True, transcript=transcript)

        return KeywordDetectionResult(detected=False, transcript="")

    def listen_until_detected(
        self,
        stream: MicrophoneStream,
        stop_event: Optional[Event] = None,
    ) -> KeywordDetectionResult:
        """Continuously read stream frames until keyword is found."""
        if self.backend in {"auto", "vosk"} and self.vosk_model_path.exists():
            return self._listen_with_vosk(stream=stream, stop_event=stop_event)
        if self.backend == "vosk":
            return self._listen_with_vosk(stream=stream, stop_event=stop_event)

        if self.backend == "openai" or (self.backend == "auto" and not self.access_key):
            return self._listen_with_openai_fallback(stream=stream, stop_event=stop_event)

        if pvporcupine is None or not self.access_key:
            return self._listen_with_vosk(stream=stream, stop_event=stop_event)

        porcupine_keyword = self.keyword_tokens[-1] if self.keyword_tokens else ""
        if porcupine_keyword != "jarvis":
            return self._listen_with_vosk(stream=stream, stop_event=stop_event)

        try:
            detector = pvporcupine.create(access_key=self.access_key, keywords=[porcupine_keyword])
        except Exception:
            if self.backend == "porcupine":
                raise
            return self._listen_with_vosk(stream=stream, stop_event=stop_event)

        pending_pcm = np.array([], dtype=np.int16)

        try:
            print(f"Using Porcupine wake detection. Say: '{porcupine_keyword}'")
            while stop_event is None or not stop_event.is_set():
                frame: Optional[AudioFrame] = stream.read_frame(timeout=0.5)
                if frame is None:
                    continue

                self._publish_level(frame.rms_level)
                pcm_frame = np.clip(frame.samples, -1.0, 1.0)
                pcm_frame = (pcm_frame * 32767.0).astype(np.int16)
                pending_pcm = np.concatenate((pending_pcm, pcm_frame))

                while pending_pcm.shape[0] >= detector.frame_length:
                    chunk = pending_pcm[: detector.frame_length]
                    pending_pcm = pending_pcm[detector.frame_length :]
                    if detector.process(chunk) >= 0:
                        return KeywordDetectionResult(detected=True, transcript=self.keyword)
            return KeywordDetectionResult(detected=False, transcript="")
        finally:
            detector.delete()
