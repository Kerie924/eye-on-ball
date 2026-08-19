import logging
import signal
import sys
import threading
import time
from pathlib import Path

from agent.api_client import ApiClient
from agent.buffer import BufferRecorder, build_clip, clip_trigger_time
from agent.buttons import ButtonListener
from agent.config import AgentConfig, CameraConfig, load_config

logger = logging.getLogger(__name__)


class CaptureService:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.api = ApiClient(config.api_url, config.device_key)
        self.recorders: dict[int, BufferRecorder] = {}
        self.listeners: list[ButtonListener] = []
        self._stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self._camera_locks: dict[int, threading.Lock] = {}

    def start(self) -> None:
        if not self.api.health_check():
            logger.warning("Backend health check failed; continuing anyway")

        for camera in self.config.cameras:
            self._camera_locks[camera.index] = threading.Lock()
            buffer_dir = self.config.data_dir / f"camera-{camera.index}" / "buffer"
            recorder = BufferRecorder(
                camera=camera,
                buffer_dir=buffer_dir,
                segment_seconds=self.config.segment_seconds,
                buffer_seconds=self.config.buffer_seconds,
            )
            recorder.start()
            self.recorders[camera.index] = recorder

            if camera.button.enabled:
                listener = ButtonListener(
                    camera=camera,
                    on_trigger=self.handle_trigger,
                    cooldown_seconds=self.config.button_cooldown_seconds,
                )
                listener.start()
                self.listeners.append(listener)

        if self.config.court_button and self.config.court_button.enabled:
            court_camera = CameraConfig(
                index=0,
                name="Court button",
                rtsp_url="",
                button=self.config.court_button,
            )
            listener = ButtonListener(
                camera=court_camera,
                on_trigger=lambda _index: self.handle_all_cameras(),
                cooldown_seconds=self.config.button_cooldown_seconds,
            )
            listener.start()
            self.listeners.append(listener)
            logger.info(
                "Court button enabled (%s) — press records all %s camera(s)",
                self.config.court_button.type,
                len(self.config.cameras),
            )

        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="heartbeat"
        )
        self._heartbeat_thread.start()

        self._remote_thread = threading.Thread(
            target=self._remote_trigger_loop, daemon=True, name="remote-triggers"
        )
        self._remote_thread.start()

        logger.info("Capture service started for %s camera(s)", len(self.config.cameras))

    def handle_all_cameras(self) -> None:
        for camera_index in sorted(self.recorders):
            self.handle_trigger(camera_index)

    def handle_trigger(self, camera_index: int) -> None:
        lock = self._camera_locks.get(camera_index)
        if lock is None:
            logger.error("No recorder found for camera %s", camera_index)
            return
        if not lock.acquire(blocking=False):
            logger.warning("Upload already in progress; ignoring trigger for camera %s", camera_index)
            return

        try:
            recorder = self.recorders.get(camera_index)
            if not recorder:
                logger.error("No recorder found for camera %s", camera_index)
                return

            segments = recorder.list_segments()
            needed = self.config.segments_for_clip
            if len(segments) < needed:
                logger.warning(
                    "Not enough buffer segments for camera %s (%s/%s)",
                    camera_index,
                    len(segments),
                    needed,
                )
                return

            clip_segments = segments[-needed:]
            clips_dir = self.config.data_dir / f"camera-{camera_index}" / "clips"
            clip_path = clips_dir / f"clip_{int(time.time())}.mp4"

            build_clip(clip_segments, clip_path)
            triggered_at = clip_trigger_time(clip_segments)

            self.api.upload_recording(camera_index, clip_path, triggered_at)
            clip_path.unlink(missing_ok=True)
        except Exception:
            logger.exception("Failed to process trigger for camera %s", camera_index)
        finally:
            lock.release()

    def _heartbeat_loop(self) -> None:
        while not self._stop.is_set():
            for camera in self.config.cameras:
                try:
                    self.api.heartbeat(camera.index)
                except Exception:
                    logger.exception("Heartbeat failed for camera %s", camera.index)
            self._stop.wait(self.config.heartbeat_seconds)

    def _remote_trigger_loop(self) -> None:
        """Poll backend for mobile PRONTO / remote capture requests."""
        while not self._stop.is_set():
            try:
                pending = self.api.claim_pending_triggers()
                for item in pending:
                    camera_index = int(item.get("camera_index", 0))
                    if camera_index in self.recorders:
                        logger.info(
                            "Remote trigger #%s for camera %s",
                            item.get("id"),
                            camera_index,
                        )
                        self.handle_trigger(camera_index)
            except Exception:
                logger.exception("Failed to poll remote triggers")
            self._stop.wait(1.5)

    def stop(self) -> None:
        self._stop.set()
        for listener in self.listeners:
            listener.stop()
        for recorder in self.recorders.values():
            recorder.stop()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2)
        if getattr(self, "_remote_thread", None):
            self._remote_thread.join(timeout=2)
        logger.info("Capture service stopped")

    def wait(self) -> None:
        while not self._stop.is_set():
            time.sleep(1)


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    config_path = "/etc/lance-on/config.yaml"
    verbose = False

    if "--config" in argv:
        config_path = argv[argv.index("--config") + 1]
    if "--verbose" in argv or "-v" in argv:
        verbose = True

    configure_logging(verbose)
    config = load_config(config_path)
    service = CaptureService(config)

    def shutdown(_signum, _frame) -> None:
        logger.info("Shutdown signal received")
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    service.start()
    service.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
