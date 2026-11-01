import logging
import shutil
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
        self._ffmpeg_lock = threading.Lock()

    def start(self) -> None:
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        self._stop.clear()
        self._start_ffmpeg()
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True,
                name=f"cleanup-cam{self.camera.index}",
            )
            self._cleanup_thread.start()

    def _ffmpeg_command(self, pattern: str) -> list[str]:
        if self.camera.rtsp_url.startswith("test://"):
            return [
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
                "-segment_format_options",
                "movflags=+frag_keyframe+empty_moov+default_base_moof",
                pattern,
            ]
        return [
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
            "-segment_format_options",
            "movflags=+frag_keyframe+empty_moov+default_base_moof",
            pattern,
        ]

    def _start_ffmpeg(self) -> None:
        pattern = str(self.buffer_dir / "segment_%05d.mp4")
        command = self._ffmpeg_command(pattern)
        logger.info(
            "Starting buffer recorder for camera %s: %s",
            self.camera.index,
            self.camera.name,
        )
        # stdin=PIPE so we can send "q" to flush/close the active segment cleanly
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _quit_ffmpeg(self) -> None:
        """Ask ffmpeg to exit so the open segment file is closed and readable."""
        proc = self.process
        self.process = None
        if proc is None:
            return
        if proc.poll() is not None:
            return
        try:
            if proc.stdin is not None:
                proc.stdin.write(b"q")
                proc.stdin.flush()
            proc.wait(timeout=8)
            return
        except Exception:
            logger.debug("ffmpeg quit via stdin failed; terminating", exc_info=True)
        try:
            proc.terminate()
            proc.wait(timeout=4)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

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
                if age < max(1.0, self.segment_seconds * 0.35):
                    segments = segments[:-1]
            except OSError:
                pass
        return segments

    def stop(self) -> None:
        self._stop.set()
        with self._ffmpeg_lock:
            self._quit_ffmpeg()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2)
            self._cleanup_thread = None

    def snapshot_segments(self, dest_dir: Path) -> list[Path]:
        """Flush the live segment (ends at button press), copy buffer, resume recording.

        Previously the in-progress segment was often dropped, so clips ended up to
        ~segment_seconds (10s) *before* the press. Flushing ffmpeg with 'q' closes
        that file so the clip includes the action.
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        with self._ffmpeg_lock:
            self._quit_ffmpeg()
            # Allow filesystem to finish writing the closed segment
            time.sleep(0.25)
            sources = sorted(
                self.buffer_dir.glob("segment_*.mp4"),
                key=lambda p: (p.stat().st_mtime, p.name),
            )
            copies: list[Path] = []
            for src in sources:
                dest = dest_dir / src.name
                try:
                    shutil.copy2(src, dest)
                except OSError:
                    logger.warning("Could not snapshot %s", src)
                    continue
                try:
                    if dest.stat().st_size > 0:
                        copies.append(dest)
                except OSError:
                    continue

            # Resume rolling buffer immediately (unless service is shutting down)
            if not self._stop.is_set():
                try:
                    self._start_ffmpeg()
                except Exception:
                    logger.exception(
                        "Failed to restart buffer for camera %s after snapshot",
                        self.camera.index,
                    )

        if not copies:
            return []

        # Remux newest in case it is still fragmented; keep it even if remux fails
        newest = copies[-1]
        closed = dest_dir / f"{newest.stem}_closed.mp4"
        if _finalize_mp4(newest, closed):
            newest.unlink(missing_ok=True)
            copies[-1] = closed
        return copies


def _finalize_mp4(source: Path, output_path: Path) -> bool:
    """Remux a fragmented MP4 into a file concat can read."""
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-an",
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0


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
    if result.returncode != 0 or not concat_path.exists():
        logger.warning("Concat copy failed; re-encoding buffer join")
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
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
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


def _media_duration(path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    try:
        return max(0.0, float((result.stdout or "").strip()))
    except ValueError:
        return 0.0


def _render_final_clip(
    source: Path,
    output_path: Path,
    *,
    clip_seconds: int,
    watermark_path: Path | None,
) -> None:
    """Keep the last N seconds, ending at the latest captured frame (button press)."""
    duration = _media_duration(source)
    start = max(0.0, duration - clip_seconds) if duration > 0 else None
    if watermark_path and watermark_path.exists():
        _render_final_clip_watermarked(
            source, output_path, clip_seconds, watermark_path, start=start
        )
        return

    if watermark_path:
        logger.warning("Watermark file missing: %s", watermark_path)

    # Input options must come before -i
    if start is not None:
        seek = ["-ss", f"{start:.3f}"]
    else:
        seek = ["-sseof", f"-{clip_seconds}"]
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        *seek,
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


def _render_final_clip_watermarked(
    source: Path,
    output_path: Path,
    clip_seconds: int,
    watermark_path: Path,
    start: float | None = None,
) -> None:
    """Bottom-centered watermark (~28% of frame height)."""
    scale_h = "main_h*0.28"
    fallback_h = "300"
    if start is not None:
        trim = f"trim=start={start:.3f}:duration={clip_seconds},setpts=PTS-STARTPTS"
        seek_in: list[str] = []
        input_seek: list[str] = ["-ss", f"{start:.3f}"]
        # Prefer filter trim when we know duration; also seek input for speed
        use_filter_trim = True
    else:
        trim = "setpts=PTS-STARTPTS"
        seek_in = []
        input_seek = ["-sseof", f"-{clip_seconds}"]
        use_filter_trim = False

    def run(filter_complex: str, *, with_input_seek: bool) -> subprocess.CompletedProcess:
        prefix = input_seek if with_input_seek else seek_in
        # When using input seek for watermarked path with known start, skip filter trim start
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *prefix,
            "-i",
            str(source),
            "-i",
            str(watermark_path.resolve()),
            "-filter_complex",
            filter_complex,
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
        return subprocess.run(command, capture_output=True, text=True, check=False)

    if use_filter_trim and start is not None:
        # Seek to start then take clip_seconds (simpler than trim=start on long files)
        fc_base = (
            f"[0:v]setpts=PTS-STARTPTS[base];"
            f"[1:v][base]scale2ref=h={scale_h}:w=oh*mdar[wm][v];"
            "[v][wm]overlay=(W-w)/2:H-h-12[out]"
        )
        result = run(fc_base, with_input_seek=True)
        if result.returncode != 0:
            logger.warning("scale2ref failed; using fixed watermark height")
            result = run(
                "[0:v]setpts=PTS-STARTPTS[base];"
                f"[1:v]scale=-1:{fallback_h}[wm];"
                "[base][wm]overlay=(W-w)/2:H-h-12[out]",
                with_input_seek=True,
            )
    else:
        result = run(
            f"[0:v]{trim}[base];"
            f"[1:v][base]scale2ref=h={scale_h}:w=oh*mdar[wm][v];"
            "[v][wm]overlay=(W-w)/2:H-h-12[out]",
            with_input_seek=True,
        )
        if result.returncode != 0:
            logger.warning("scale2ref failed; using fixed watermark height")
            result = run(
                f"[0:v]{trim}[base];"
                f"[1:v]scale=-1:{fallback_h}[wm];"
                "[base][wm]overlay=(W-w)/2:H-h-12[out]",
                with_input_seek=True,
            )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to render watermarked clip")


def clip_trigger_time(segment_paths: list[Path]) -> datetime:
    latest = max(segment_paths, key=lambda p: p.stat().st_mtime)
    return datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)
