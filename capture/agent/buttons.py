import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from agent.config import ButtonConfig, CameraConfig

logger = logging.getLogger(__name__)


class ButtonListener:
    def __init__(
        self,
        camera: CameraConfig,
        on_trigger: Callable[[int], None],
        cooldown_seconds: int,
    ) -> None:
        self.camera = camera
        self.button = camera.button
        self.on_trigger = on_trigger
        self.cooldown_seconds = cooldown_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_trigger = 0.0

    def start(self) -> None:
        target = {
            "serial": self._run_serial,
            "gpio": self._run_gpio,
            "mock": self._run_mock,
        }.get(self.button.type, self._run_mock)

        self._thread = threading.Thread(
            target=target,
            daemon=True,
            name=f"button-cam{self.camera.index}",
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _fire(self) -> None:
        now = time.time()
        if now - self._last_trigger < self.cooldown_seconds:
            return
        self._last_trigger = now
        logger.info("Button triggered for camera %s", self.camera.index)
        self.on_trigger(self.camera.index)

    def _run_serial(self) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("pyserial is required for serial button type") from exc

        port = self.button.port
        if not port:
            raise RuntimeError(f"Serial port not configured for camera {self.camera.index}")

        while not self._stop.is_set():
            try:
                with serial.Serial(port, self.button.baudrate, timeout=1) as device:
                    logger.info("Listening serial button on %s for camera %s", port, self.camera.index)
                    while not self._stop.is_set():
                        raw = device.readline()
                        if not raw:
                            continue
                        message = raw.decode("utf-8", errors="ignore").strip()
                        if message == self.button.trigger_on or message.upper() == "TRIGGER":
                            self._fire()
            except Exception:
                logger.exception(
                    "Serial listener error for camera %s on %s; retrying in 3s",
                    self.camera.index,
                    port,
                )
                time.sleep(3)

    def _run_gpio(self) -> None:
        pin = self.button.pin
        if pin is None:
            raise RuntimeError(f"GPIO pin not configured for camera {self.camera.index}")

        try:
            import gpiod
        except ImportError:
            logger.warning(
                "gpiod not installed; falling back to mock file trigger for camera %s",
                self.camera.index,
            )
            self._run_mock()
            return

        chip = gpiod.Chip("gpiochip0")
        line = chip.get_line(pin)
        line.request(consumer=f"olho-cam{self.camera.index}", type=gpiod.LINE_REQ_DIR_IN)

        previous = line.get_value()
        while not self._stop.is_set():
            current = line.get_value()
            if previous == 1 and current == 0:
                self._fire()
            previous = current
            time.sleep(0.05)

    def _run_mock(self) -> None:
        mock_file = Path(
            self.button.mock_file or f"/tmp/olho-button-{self.camera.index}.trigger"
        )
        logger.info(
            "Mock button for camera %s watching %s",
            self.camera.index,
            mock_file,
        )
        last_mtime = 0.0
        while not self._stop.is_set():
            try:
                if mock_file.exists():
                    mtime = mock_file.stat().st_mtime
                    if mtime > last_mtime:
                        last_mtime = mtime
                        self._fire()
                        mock_file.unlink(missing_ok=True)
            except OSError:
                logger.exception("Mock button watch failed for camera %s", self.camera.index)
            time.sleep(0.2)
