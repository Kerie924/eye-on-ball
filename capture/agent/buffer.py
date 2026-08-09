import logging
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from agent.config import CameraConfig

logger = logging.getLogger(__name__)


class BufferRecorder:
    """Continuous RTSP recording into rolling MP4 segments."""

    def __init__(
        self,
        camera: CameraConfig,
        buffer_dir: Path,
        segment_seconds: int,
        buffer_seconds: int,
    ) -> None:
        self.camera = camera
        self.buffer_dir = buffer_dir
        self.segment_seconds = segment_seconds
        self.buffer_seconds = buffer_seconds
        self.process: subprocess.Popen | None = None
        self._stop = threading.Event()
        self._cleanup_thread: threading.Thread | None = None

    def start(self) -> None:
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        pattern = str(self.buffer_dir / "segment_%05d.mp4")

        if self.camera.rtsp_url.startswith("test://"):
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc=size=1280x720:rate=25",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-f",
                "segment",
                "-segment_time",
                str(self.segment_seconds),
                "-reset_timestamps",
                "1",
                "-segment_format",
                "mp4",
                pattern,
            ]
        else:
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-rtsp_transport",
                "tcp",
                "-i",
                self.camera.rtsp_url,
                "-an",
                "-c:v",
                "copy",
                "-f",
                "segment",
                "-segment_time",
                str(self.segment_seconds),
                "-reset_timestamps",
                "1",
                "-segment_format",
                "mp4",
                pattern,
            ]

        logger.info(
            "Starting buffer recorder for camera %s: %s",
            self.camera.index,
            self.camera.name,
        )
        self.process = subprocess.Popen(command)
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop, daemon=True, name=f"cleanup-cam{self.camera.index}"
        )
        self._cleanup_thread.start()

    def _cleanup_loop(self) -> None:
        while not self._stop.is_set():
            cutoff = time.time() - self.buffer_seconds
            for path in self.buffer_dir.glob("segment_*.mp4"):
                try:
                    if path.stat().st_mtime < cutoff:
                        path.unlink(missing_ok=True)
                except OSError:
                    logger.exception("Failed to delete old segment %s", path)
            time.sleep(5)

    def list_segments(self) -> list[Path]:
        segments = sorted(self.buffer_dir.glob("segment_*.mp4"), key=lambda p: p.stat().st_mtime)
        return segments

    def stop(self) -> None:
        self._stop.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2)

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None


def build_clip(segment_paths: list[Path], output_path: Path) -> None:
    if not segment_paths:
        raise RuntimeError("No buffer segments available for clip")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = output_path.with_suffix(".txt")

    with list_file.open("w", encoding="utf-8") as handle:
        for segment in segment_paths:
            handle.write(f"file '{segment.resolve()}'\n")

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    list_file.unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to build clip")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Generated clip is empty")


def clip_trigger_time(segment_paths: list[Path]) -> datetime:
    latest = max(segment_paths, key=lambda p: p.stat().st_mtime)
    return datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)
