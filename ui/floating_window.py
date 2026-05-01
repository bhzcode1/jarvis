from __future__ import annotations

import math
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class FloatingAssistantWindow:
    """Always-on-top floating window with a live audio waveform."""

    def __init__(
        self,
        title: str = "Anti Gravity",
        width: int = 380,
        height: int = 220,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        self.width = width
        self.height = height
        self._on_close = on_close
        self._ui_thread_id = threading.get_ident()
        self._events: queue.Queue[tuple[str, tuple[object, ...]]] = queue.Queue()
        self._level_lock = threading.Lock()
        self._target_level = 0.0
        self._display_level = 0.0
        self._phase = 0.0
        self._is_closed = False
        self._state = "idle"
        self._error_flash_until = 0.0

        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#07111f")

        self._status_var = tk.StringVar(value="Idle")
        self._hint_var = tk.StringVar(value="Starting microphone...")

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Card.TFrame", background="#07111f")
        style.configure("Title.TLabel", background="#07111f", foreground="#7dd3fc", font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", background="#07111f", foreground="#ffffff", font=("Segoe UI", 18, "bold"))
        style.configure("Hint.TLabel", background="#07111f", foreground="#b6c2d2", font=("Segoe UI", 10))

        card = ttk.Frame(container, style="Card.TFrame")
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="ANTI GRAVITY", style="Title.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=self._status_var, style="Status.TLabel").pack(anchor="w", pady=(8, 0))
        ttk.Label(card, textvariable=self._hint_var, style="Hint.TLabel").pack(anchor="w", pady=(8, 0))

        self.canvas = tk.Canvas(
            card,
            width=width - 24,
            height=84,
            bg="#07111f",
            highlightthickness=0,
        )
        self.canvas.pack(fill="x", pady=(18, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(40, self._poll_events)
        self.root.after(16, self._animate)

    def set_state(self, state: str, hint: str | None = None) -> None:
        """Request a state update (idle/wake/listening/processing/speaking/error/friend/spotify)."""
        if self._is_ui_thread():
            self._apply_state(state, hint)
            return
        self._events.put(("state", (state, hint)))

    def set_status(self, status: str, hint: str | None = None) -> None:
        """Request a visible status update from any thread."""
        if self._is_ui_thread():
            self._apply_status(status, hint)
            return
        self._events.put(("status", (status, hint)))

    def set_audio_level(self, level: float) -> None:
        """Receive a live microphone loudness value from any thread."""
        clean_level = max(0.0, min(float(level), 1.0))
        with self._level_lock:
            self._target_level = clean_level

    def _is_ui_thread(self) -> bool:
        """Return True when code is currently running on the Tkinter thread."""
        return threading.get_ident() == self._ui_thread_id

    def _apply_status(self, status: str, hint: str | None = None) -> None:
        """Apply a status update on the Tkinter thread."""
        self._status_var.set(status)
        if hint is not None:
            self._hint_var.set(hint)
        self.root.update_idletasks()

    def _apply_state(self, state: str, hint: str | None = None) -> None:
        clean_state = (state or "").strip().lower() or "idle"
        if clean_state == "error":
            self._error_flash_until = time.monotonic() + 0.65
        self._state = clean_state
        display = {
            "idle": "Idle",
            "wake": "Listening",
            "listening": "Listening",
            "processing": "Thinking",
            "speaking": "Speaking",
            "error": "Error",
            "friend": "Chilling",
            "spotify": "Music",
        }.get(clean_state, clean_state.title())
        self._status_var.set(display)
        if hint is not None:
            self._hint_var.set(hint)
        self.root.update_idletasks()

    def _poll_events(self) -> None:
        """Apply queued worker-thread events on the Tkinter thread."""
        if self._is_closed:
            return
        while True:
            try:
                event_name, args = self._events.get_nowait()
            except queue.Empty:
                break
            if event_name == "status":
                status, hint = args
                self._apply_status(str(status), None if hint is None else str(hint))
            if event_name == "state":
                state, hint = args
                self._apply_state(str(state), None if hint is None else str(hint))
        self.root.after(40, self._poll_events)

    def _state_palette(self) -> tuple[str, str]:
        now = time.monotonic()
        if now < self._error_flash_until:
            return ("#ef4444", "#fecaca")
        state = self._state
        if state == "wake":
            return ("#38bdf8", "#a7f3d0")
        if state == "processing":
            return ("#8b5cf6", "#38bdf8")
        if state == "speaking":
            return ("#fbbf24", "#fde68a")
        if state == "friend":
            return ("#22c55e", "#bbf7d0")
        if state == "spotify":
            return ("#10b981", "#60a5fa")
        if state == "listening":
            return ("#38bdf8", "#a7f3d0")
        return ("#38bdf8", "#a7f3d0")

    def _animate(self) -> None:
        """Draw one waveform animation frame and schedule the next frame."""
        if self._is_closed:
            return

        with self._level_lock:
            target_level = self._target_level
        self._display_level += (target_level - self._display_level) * 0.22
        self._phase += 0.18

        self.canvas.delete("all")
        canvas_width = int(self.canvas.winfo_width() or (self.width - 24))
        canvas_height = int(self.canvas.winfo_height() or 84)
        center_y = canvas_height / 2
        amplitude = 8.0 + (self._display_level * 46.0)
        primary, secondary = self._state_palette()
        pulse = (math.sin(self._phase * 0.6) + 1.0) / 2.0
        border_width = 2 + int(pulse * 3) if self._state == "wake" else 2

        if self._state != "idle":
            self.canvas.create_rectangle(
                2,
                2,
                canvas_width - 2,
                canvas_height - 2,
                outline=primary,
                width=border_width,
            )
        points = []

        point_count = 56
        for index in range(point_count):
            x = (canvas_width - 8) * index / (point_count - 1) + 4
            envelope = math.sin(math.pi * index / (point_count - 1))
            wave_a = math.sin(self._phase + index * 0.48)
            wave_b = math.sin((self._phase * 0.63) + index * 0.19)
            y = center_y + ((wave_a * 0.72) + (wave_b * 0.28)) * amplitude * envelope
            points.extend((x, y))

        self.canvas.create_line(points, fill=primary, width=3, smooth=True, capstyle=tk.ROUND)
        self.canvas.create_line(points, fill=secondary, width=1, smooth=True, capstyle=tk.ROUND)

        dot_radius = 3 + self._display_level * 5
        self.canvas.create_oval(
            8,
            center_y - dot_radius,
            8 + dot_radius * 2,
            center_y + dot_radius,
            fill=secondary,
            outline="",
        )

        self.root.after(16, self._animate)

    def close(self) -> None:
        """Close UI window safely."""
        if self._is_closed:
            return
        self._is_closed = True
        if self._on_close is not None:
            self._on_close()
        if self.root.winfo_exists():
            self.root.destroy()

    def run(self) -> None:
        """Start Tkinter event loop."""
        self.root.mainloop()
