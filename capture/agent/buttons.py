import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from agent.config import ButtonConfig, CameraConfig
from agent.paths import mock_trigger_path

logger = logging.getLogger(__name__)


def resolve_serial_port(preferred: str | None = None) -> str | None:
    """Pick a USB-serial adapter (Arduino / CH340 / CP210x) or an explicit COM port."""
    preferred = (preferred or "").strip()
    if preferred and preferred.lower() not in {"auto", "default", ""}:
        return preferred

    try:
        from serial.tools import list_ports
    except ImportError:
        logger.warning("pyserial not installed; cannot auto-detect COM port")
        return None

    ports = list(list_ports.comports())
    if not ports:
        return None

    keywords = (
        "arduino",
        "ch340",
        "ch341",
        "cp210",
        "usb serial",
        "usb-serial",
        "usb2.0-serial",
        "uart",
        "esp",
        "silicon labs",
        "wch",
    )
    for port in ports:
        blob = " ".join(
            filter(
                None,
                [port.device, port.description, port.manufacturer, port.hwid],
            )
        ).lower()
        if any(token in blob for token in keywords):
            logger.info("Auto-selected serial port %s (%s)", port.device, port.description)
            return port.device

    # Fallback: first COM/ttyUSB/ttyACM device
    first = ports[0].device
    logger.info("Using first serial port %s (%s)", first, ports[0].description)
    return first


class SerialHubListener:
    """One USB-serial board for all cameras (Arduino D2/D3 … D12/D13 pairs).

    Firmware prints the camera index (1–6) on each button press.
    """

    def __init__(
        self,
        on_trigger: Callable[[int], None],
        camera_indexes: list[int],
        *,
        port: str = "auto",
        baudrate: int = 115200,
        cooldown_seconds: float = 3.0,
    ) -> None:
        self.on_trigger = on_trigger
        self.camera_indexes = set(camera_indexes)
        self.port = port
        self.baudrate = baudrate
        self.cooldown_seconds = cooldown_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_trigger: dict[int, float] = {}

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="button-serial-hub"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _fire(self, camera_index: int) -> None:
        if camera_index not in self.camera_indexes:
            logger.warning("Serial hub got camera %s but it is not configured", camera_index)
            return
        now = time.time()
        last = self._last_trigger.get(camera_index, 0.0)
        if now - last < self.cooldown_seconds:
            return
        self._last_trigger[camera_index] = now
        logger.info("Serial hub triggered camera %s", camera_index)
        self.on_trigger(camera_index)

    def _parse_message(self, message: str) -> int | None:
        text = message.strip()
        if not text or text.upper() == "LANCEON_BUTTONS_READY":
            return None
        upper = text.upper()
        if upper.startswith("CAM"):
            text = text[3:].lstrip(" =:_-")
        if upper.startswith("CAMERA"):
            text = text[6:].lstrip(" =:_-")
        try:
            return int(text.split()[0])
        except (ValueError, IndexError):
            return None

    def _run(self) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("pyserial is required for Windows button hub") from exc

        while not self._stop.is_set():
            port = resolve_serial_port(self.port)
            if not port:
                logger.warning(
                    "No serial button board found. Plug in the Arduino (D2–D13 wiring) "
                    "or set button_hub.port in config. Retrying in 5s..."
                )
                time.sleep(5)
                continue
            try:
                with serial.Serial(port, self.baudrate, timeout=1) as device:
                    logger.info(
                        "Serial button hub on %s @ %s — cameras %s",
                        port,
                        self.baudrate,
                        sorted(self.camera_indexes),
                    )
                    while not self._stop.is_set():
                        raw = device.readline()
                        if not raw:
                            continue
                        message = raw.decode("utf-8", errors="ignore").strip()
                        if not message:
                            continue
                        camera_index = self._parse_message(message)
                        if camera_index is not None:
                            self._fire(camera_index)
            except Exception:
                logger.exception(
                    "Serial hub error on %s; reconnecting in 3s", port or "auto"
                )
                time.sleep(3)


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
        if not self.button.enabled:
            return
        target = {
            "serial": self._run_serial,
            "gpio": self._run_gpio,
            "keyboard": self._run_keyboard,
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

        gnd_pin = self.button.gnd_pin
        logger.info(
            "Listening GPIO pin %s (HIGH idle, LOW press) for camera %s%s",
            pin,
            self.camera.index,
            f"; driving GPIO {gnd_pin} LOW as GND" if gnd_pin is not None else "",
        )
        try:
            if hasattr(gpiod, "request_lines"):
                self._run_gpio_v2(gpiod, pin, gnd_pin)
            else:
                self._run_gpio_v1(gpiod, pin, gnd_pin)
        except Exception:
            logger.exception("GPIO listener failed for camera %s; falling back to mock", self.camera.index)
            self._run_mock()

    def _confirm_press(self, previous: int, current: int, reread) -> bool:
        """Falling edge HIGH->LOW, then wait to debounce bounce."""
        if not (previous == 1 and current == 0):
            return False
        time.sleep(0.08)
        return reread() == 0

    def _run_gpio_v2(self, gpiod, pin: int, gnd_pin: int | None = None) -> None:
        from gpiod.line import Bias, Direction, Value

        settings = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP)
        config = {pin: settings}
        if gnd_pin is not None:
            config[gnd_pin] = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)
        request = gpiod.request_lines(
            "/dev/gpiochip0",
            consumer=f"lanceon-cam{self.camera.index}",
            config=config,
        )

        def read() -> int:
            return 1 if request.get_value(pin) == Value.ACTIVE else 0

        previous = read()
        while not self._stop.is_set():
            current = read()
            if self._confirm_press(previous, current, read):
                self._fire()
                current = 0
            previous = current
            time.sleep(0.02)

    def _run_gpio_v1(self, gpiod, pin: int, gnd_pin: int | None = None) -> None:
        chip = gpiod.Chip("gpiochip0")
        if gnd_pin is not None:
            gnd_line = chip.get_line(gnd_pin)
            gnd_line.request(
                consumer=f"lanceon-cam{self.camera.index}-gnd",
                type=gpiod.LINE_REQ_DIR_OUT,
                default_vals=[0],
            )
        line = chip.get_line(pin)
        flags = 0
        if hasattr(gpiod, "LINE_REQ_FLAG_BIAS_PULL_UP"):
            flags = gpiod.LINE_REQ_FLAG_BIAS_PULL_UP
        line.request(
            consumer=f"lanceon-cam{self.camera.index}",
            type=gpiod.LINE_REQ_DIR_IN,
            flags=flags,
        )

        def read() -> int:
            return int(line.get_value())

        previous = read()
        while not self._stop.is_set():
            current = read()
            if self._confirm_press(previous, current, read):
                self._fire()
                current = 0
            previous = current
            time.sleep(0.02)

    def _run_keyboard(self) -> None:
        """Listen for a key press (USB arcade/HID buttons on Windows)."""
        key_name = (self.button.key or self.button.trigger_on or str(self.camera.index)).strip()
        if not key_name:
            raise RuntimeError(f"Keyboard key not configured for camera {self.camera.index}")

        try:
            from pynput import keyboard
        except ImportError:
            logger.warning(
                "pynput not installed; falling back to mock file trigger for camera %s",
                self.camera.index,
            )
            self._run_mock()
            return

        target = key_name.lower()
        logger.info(
            "Listening keyboard key %r for camera %s",
            target,
            self.camera.index,
        )

        def matches(key) -> bool:
            try:
                if hasattr(key, "char") and key.char:
                    return key.char.lower() == target
                name = str(key).replace("Key.", "").lower()
                return name == target or name == f"'{target}'"
            except Exception:
                return False

        def on_press(key) -> None:
            if matches(key):
                self._fire()

        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        try:
            while not self._stop.is_set():
                time.sleep(0.2)
        finally:
            listener.stop()
            listener.join(timeout=2)

    def _run_mock(self) -> None:
        mock_file = Path(self.button.mock_file or str(mock_trigger_path(self.camera.index)))
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
