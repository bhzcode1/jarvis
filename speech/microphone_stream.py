from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
import sounddevice as sd


@dataclass(slots=True)
class AudioFrame:
    """Single chunk of microphone audio with a precomputed loudness value."""

    samples: np.ndarray
    rms_level: float


class MicrophoneStream:
    """Thread-safe microphone stream using sounddevice callback mode."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        block_size: int = 1024,
        max_queue_size: int = 128,
        input_device: Optional[int] = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        self.input_device = input_device
        self._queue: queue.Queue[AudioFrame] = queue.Queue(maxsize=max_queue_size)
        self._stop_event = threading.Event()
        self._stream: Optional[sd.InputStream] = None

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        """Capture audio chunks and enqueue lightweight frame data."""
        del frames, time_info
        # Do not drop frames on status flags; many are non-fatal warnings.
        # We keep processing so wake detection continues under minor glitches.
        _ = status

        mono = np.squeeze(indata).astype(np.float32, copy=False)
        rms = float(np.sqrt(np.mean(np.square(mono))) + 1e-10)
        frame = AudioFrame(samples=mono.copy(), rms_level=rms)

        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            # Drop oldest frame to keep real-time behavior.
            _ = self._queue.get_nowait()
            self._queue.put_nowait(frame)

    def start(self) -> None:
        """Start microphone capture."""
        if self._stream is not None:
            return

        self._stop_event.clear()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocksize=self.block_size,
            device=self.input_device,
            callback=self._audio_callback,
        )
        self._stream.start()

    def read_frame(self, timeout: float = 0.5) -> Optional[AudioFrame]:
        """Return one audio frame, or None on timeout/stop."""
        if self._stop_event.is_set():
            return None
        deadline = time.monotonic() + max(0.0, timeout)
        while not self._stop_event.is_set() and time.monotonic() < deadline:
            try:
                return self._queue.get_nowait()
            except queue.Empty:
                time.sleep(0.01)
        return None

    def clear_buffer(self) -> None:
        """Remove any queued audio frames that were captured earlier."""
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    def stop(self) -> None:
        """Stop microphone capture and release system resources."""
        self._stop_event.set()
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
