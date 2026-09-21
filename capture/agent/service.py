import logging
import shutil
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from agent.api_client import ApiClient
from agent.buffer import BufferRecorder, build_clip
from agent.buttons import ButtonListener
from agent.config import AgentConfig, CameraConfig, load_config
from agent.upload_queue import UploadQueue

logger = logging.getLogger(__name__)


class CaptureService:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.api = ApiClient(config.api_url, config.device_key)
        self.queue = UploadQueue(
            config.data_dir,
            max_hours=config.queue_max_hours,
            max_mb=config.queue_max_mb,
        )
        self.recorders: dict[int, BufferRecorder] = {}
        self.listeners: list[ButtonListener] = []
        self._stop = threading.Event()
        self._upload_ready = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self._upload_thread: threading.Thread | None = None
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

        recovered = self.queue.recover_orphans([camera.index for camera in self.config.cameras])
        self.queue.prune()
        if recovered or self.queue.next_job():
            self._upload_ready.set()

        self._upload_thread = threading.Thread(
            target=self._upload_loop, daemon=True, name="upload-queue"
        )
        self._upload_thread.start()

        logger.info("Capture service started for %s camera(s)", len(self.config.cameras))

    def handle_all_cameras(self) -> None:
        logger.info("Court button: recording %s camera(s) in parallel", len(self.recorders))
        threads = [
            threading.Thread(
                target=self.handle_trigger,
                args=(camera_index,),
                name=f"trigger-cam-{camera_index}",
                daemon=True,
            )
            for camera_index in sorted(self.recorders)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def handle_trigger(self, camera_index: int) -> None:
        lock = self._camera_locks.get(camera_index)
        if lock is None:
            logger.error("No recorder found for camera %s", camera_index)
            return
        if not lock.acquire(blocking=False):
            logger.warning("Clip already being built; ignoring trigger for camera %s", camera_index)
            return

        snap_dir: Path | None = None
        try:
            recorder = self.recorders.get(camera_index)
            if not recorder:
                logger.error("No recorder found for camera %s", camera_index)
                return

            snap_dir = (
                self.config.data_dir
                / f"camera-{camera_index}"
                / "snap"
                / str(int(time.time() * 1000))
            )
            segments = recorder.snapshot_segments(snap_dir)
            needed = self.config.segments_for_clip
            min_segments = max(1, -(-self.config.clip_seconds // self.config.segment_seconds))
            if len(segments) < min_segments:
                shutil.rmtree(snap_dir, ignore_errors=True)
                logger.warning(
                    "Not enough buffer segments for camera %s (%s/%s). "
                    "Wait ~%ss after start before triggering.",
                    camera_index,
                    len(segments),
                    min_segments,
                    self.config.clip_seconds,
                )
                return

            clip_segments = segments[-needed:] if len(segments) >= needed else segments
            clips_dir = self.config.data_dir / f"camera-{camera_index}" / "clips"
            clip_path = clips_dir / f"clip_{int(time.time())}_{camera_index}.mp4"

            logger.info(
                "Building %ss clip for camera %s from %s segments (watermark=%s)",
                self.config.clip_seconds,
                camera_index,
                len(clip_segments),
                bool(self.config.watermark_path and self.config.watermark_path.exists()),
            )
            build_clip(
                clip_segments,
                clip_path,
                clip_seconds=self.config.clip_seconds,
                watermark_path=self.config.watermark_path,
            )
            triggered_at = datetime.now(timezone.utc)
            self.queue.enqueue(camera_index, clip_path, triggered_at)
            self._upload_ready.set()
        except Exception:
            logger.exception("Failed to process trigger for camera %s", camera_index)
        finally:
            if snap_dir is not None:
                shutil.rmtree(snap_dir, ignore_errors=True)
            lock.release()

    def _heartbeat_loop(self) -> None:
        while not self._stop.is_set():
            threads = []
            for camera in self.config.cameras:
                thread = threading.Thread(
                    target=self._heartbeat_one,
                    args=(camera.index,),
                    name=f"heartbeat-cam-{camera.index}",
                    daemon=True,
                )
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
            self._stop.wait(self.config.heartbeat_seconds)

    def _heartbeat_one(self, camera_index: int) -> None:
        try:
            self.api.heartbeat(camera_index)
        except Exception as exc:
            logger.warning(
                "Heartbeat failed for camera %s (%s). Recording still works locally; "
                "upload needs internet to %s",
                camera_index,
                exc.__class__.__name__,
                self.config.api_url,
            )

    def _upload_loop(self) -> None:
        """Send queued clips when the API is reachable. Never delete until upload succeeds."""
        while not self._stop.is_set():
            self.queue.prune()
            job = self.queue.next_job()
            if not job:
                self._upload_ready.clear()
                self._upload_ready.wait(timeout=self.config.upload_retry_seconds)
                continue

            clip_path = Path(job["clip_path"])
            if not clip_path.exists():
                self.queue.mark_uploaded(job["id"])
                continue

            try:
                triggered_at = datetime.fromisoformat(job["triggered_at"])
                self.api.upload_recording(
                    int(job["camera_index"]),
                    clip_path,
                    triggered_at,
                    retries=1,
                )
                self.queue.mark_uploaded(job["id"])
                logger.info(
                    "Uploaded queued clip %s for camera %s",
                    job["id"],
                    job["camera_index"],
                )
            except Exception as exc:
                self.queue.mark_failed(job["id"], exc.__class__.__name__)
                logger.warning(
                    "Queued clip %s for camera %s not uploaded (%s). "
                    "Kept on disk; retry in %ss",
                    job["id"],
                    job["camera_index"],
                    exc.__class__.__name__,
                    self.config.upload_retry_seconds,
                )
                self._stop.wait(self.config.upload_retry_seconds)

    def _remote_trigger_loop(self) -> None:
        """Poll backend for mobile PRONTO / remote capture requests."""
        while not self._stop.is_set():
            try:
                pending = self.api.claim_pending_triggers()
                threads = []
                for item in pending:
                    camera_index = int(item.get("camera_index", 0))
                    if camera_index not in self.recorders:
                        logger.warning(
                            "Remote trigger #%s for unknown camera %s (configured: %s)",
                            item.get("id"),
                            camera_index,
                            sorted(self.recorders),
                        )
                        continue
                    logger.info(
                        "Remote trigger #%s for camera %s",
                        item.get("id"),
                        camera_index,
                    )
                    thread = threading.Thread(
                        target=self.handle_trigger,
                        args=(camera_index,),
                        name=f"trigger-cam-{camera_index}",
                        daemon=True,
                    )
                    thread.start()
                    threads.append(thread)
                for thread in threads:
                    thread.join()
            except Exception as exc:
                logger.warning("Failed to poll remote triggers (%s)", exc.__class__.__name__)
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
        self._upload_ready.set()
        if getattr(self, "_upload_thread", None):
            self._upload_thread.join(timeout=2)
        logger.info("Capture service stopped")

    def wait(self) -> None:
        while not self._stop.is_set():
            time.sleep(1)


def configure_logging(verbose: bool = False, log_file: Path | None = None) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file is not None:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def main(argv: list[str] | None = None) -> int:
    from agent.paths import default_config_path, default_log_dir, is_windows

    argv = argv or sys.argv[1:]
    config_path = str(default_config_path())
    verbose = False

    if "--config" in argv:
        config_path = argv[argv.index("--config") + 1]
    if "--verbose" in argv or "-v" in argv:
        verbose = True

    if is_windows():
        log_dir = default_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        configure_logging(verbose, log_file=log_dir / "capture.log")
    else:
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
