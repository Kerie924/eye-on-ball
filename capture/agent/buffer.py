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

    def list_segments(self, *, exclude_active: bool = True) -> list[Path]:
        """Return finished segments oldest→newest. Skip the file still being written."""
        segments = sorted(
            self.buffer_dir.glob("segment_*.mp4"),
            key=lambda p: p.stat().st_mtime,
        )
        if exclude_active and segments:
            newest = segments[-1]
            try:
                age = time.time() - newest.stat().st_mtime
                # Active segment is rewritten often; drop if still hot.
                if age < max(2.0, self.segment_seconds * 0.35):
                    segments = segments[:-1]
            except OSError:
                pass
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


def build_clip(
    segment_paths: list[Path],
    output_path: Path,
    *,
    clip_seconds: int = 30,
    watermark_path: Path | None = None,
) -> None:
    """Concat buffer segments, keep exactly clip_seconds from the end, burn bottom watermark."""
    if not segment_paths:
        raise RuntimeError("No buffer segments available for clip")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = output_path.with_suffix(".txt")
    concat_path = output_path.with_name(output_path.stem + "_concat.mp4")

    with list_file.open("w", encoding="utf-8") as handle:
        for segment in segment_paths:
            handle.write(f"file '{segment.resolve()}'\n")

    concat_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
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
        str(concat_path),
    ]
    result = subprocess.run(concat_cmd, capture_output=True, text=True, check=False)
    list_file.unlink(missing_ok=True)
    if result.returncode != 0 or not concat_path.exists():
        raise RuntimeError(result.stderr.strip() or "Failed to concatenate buffer segments")

    try:
        _render_final_clip(
            concat_path,
            output_path,
            clip_seconds=clip_seconds,
            watermark_path=watermark_path,
        )
    finally:
        concat_path.unlink(missing_ok=True)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Generated clip is empty")


def _render_final_clip(
    source: Path,
    output_path: Path,
    *,
    clip_seconds: int,
    watermark_path: Path | None,
) -> None:
    """Take the last N seconds and optionally overlay a bottom banner watermark."""
    if watermark_path and watermark_path.exists():
        _render_final_clip_simple(source, output_path, clip_seconds, watermark_path)
        return

    if watermark_path:
        logger.warning("Watermark file missing: %s", watermark_path)

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-sseof",
        f"-{clip_seconds}",
        "-i",
        str(source),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-t",
        str(clip_seconds),
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to render final clip")


def _render_final_clip_simple(
    source: Path,
    output_path: Path,
    clip_seconds: int,
    watermark_path: Path,
) -> None:
    """Bottom-centered banner (~82% width). Matches Meu Replay style ads."""
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-sseof",
        f"-{clip_seconds}",
        "-i",
        str(source),
        "-i",
        str(watermark_path.resolve()),
        "-filter_complex",
        (
            f"[0:v]trim=duration={clip_seconds},setpts=PTS-STARTPTS[base];"
            "[1:v][base]scale2ref=w=main_w*0.82:h=ow/mdar[wm][v];"
            "[v][wm]overlay=(W-w)/2:H-h-8[out]"
        ),
        "-map",
        "[out]",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-t",
        str(clip_seconds),
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        # Older ffmpeg: fixed-width scale fallback
        logger.warning("scale2ref failed; using fixed watermark width")
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-sseof",
            f"-{clip_seconds}",
            "-i",
            str(source),
            "-i",
            str(watermark_path.resolve()),
            "-filter_complex",
            (
                f"[0:v]trim=duration={clip_seconds},setpts=PTS-STARTPTS[base];"
                "[1:v]scale=1100:-1[wm];"
                "[base][wm]overlay=(W-w)/2:H-h-8[out]"
            ),
            "-map",
            "[out]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-t",
            str(clip_seconds),
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Failed to render watermarked clip")


def clip_trigger_time(segment_paths: list[Path]) -> datetime:
    latest = max(segment_paths, key=lambda p: p.stat().st_mtime)
    return datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)
