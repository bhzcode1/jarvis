import threading
from threading import Event
from typing import Optional

from PIL import Image, ImageDraw
import pystray
import time

from app.audio.wake_word import wait_for_wake_word, wake_word_ready
from app.main import run_single_turn
from app.utils.logger import configure_logging, get_logger
from app.utils.env_bootstrap import ensure_env_file_exists
from app.utils.runtime import get_runtime_base_dir, set_cwd_to_runtime_base_dir
from config.settings import Settings

logger = get_logger(__name__)


def _create_default_icon() -> Image.Image:
    """Create a simple in-memory tray icon."""
    image = Image.new("RGB", (64, 64), color=(20, 20, 20))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(0, 153, 255))
    draw.text((22, 20), "J", fill=(255, 255, 255))
    return image


class JarvisTrayApp:
    """Windows tray app that runs Jarvis wake-word loop in background."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.stop_event: Event = Event()
        self.worker_thread: Optional[threading.Thread] = None
        self.icon = pystray.Icon(
            "Jarvis",
            _create_default_icon(),
            "Jarvis Assistant",
            menu=pystray.Menu(
                pystray.MenuItem("Run once (talk now)", self._on_run_once),
                pystray.MenuItem("Exit", self._on_exit),
            ),
        )

    def _ensure_worker_started(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            return

        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def _worker_loop(self) -> None:
        logger.info("Tray worker started.")
        while not self.stop_event.is_set():
            try:
                if not wake_word_ready(settings=self.settings):
                    logger.warning("Wake word not ready; retrying in 5 seconds.")
                    time.sleep(5.0)
                    continue

                logger.info("Wake-word listening active.")
                detected = wait_for_wake_word(settings=self.settings)
                if detected and not self.stop_event.is_set():
                    run_single_turn(settings=self.settings)
                if not detected:
                    time.sleep(2.0)
            except Exception as error:
                logger.exception("Background worker error: %s", error)
                time.sleep(2.0)

    def _on_run_once(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        try:
            run_single_turn(settings=self.settings)
        except Exception as error:
            logger.exception("Run-once failed: %s", error)

    def _on_exit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.stop_event.set()
        icon.stop()

    def run(self) -> None:
        self._ensure_worker_started()
        try:
            self.icon.run()
        except Exception as error:
            logger.exception("Tray icon loop failed: %s", error)

        # If the tray loop returns unexpectedly (common in some frozen setups),
        # keep the process alive so wake-word/background features can still run.
        logger.warning("Tray icon loop exited; keeping Jarvis alive in background.")
        while not self.stop_event.is_set():
            time.sleep(1.0)


def main() -> None:
    set_cwd_to_runtime_base_dir()
    base_dir = get_runtime_base_dir()
    ensure_env_file_exists(runtime_base_dir=base_dir)
    configure_logging(log_file=base_dir / "data" / "logs" / "jarvis_tray.log")
    settings = Settings()
    app = JarvisTrayApp(settings=settings)
    app.run()


if __name__ == "__main__":
    main()
