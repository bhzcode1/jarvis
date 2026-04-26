from __future__ import annotations

import math
import time

from ui.floating_window import FloatingAssistantWindow


def main() -> None:
    """Demo runner for the floating window and waveform animation."""
    window = FloatingAssistantWindow()
    window.set_status("Listening", "Say 'Hey Gekko'")

    def pulse() -> None:
        level = (math.sin(time.monotonic() * 3.0) + 1.0) / 2.0
        window.set_audio_level(level)
        window.root.after(50, pulse)

    pulse()
    window.run()


if __name__ == "__main__":
    main()
