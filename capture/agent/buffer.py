import logging
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from agent.config import CameraConfig

logger = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform.startswith("win")
# Hide ffmpeg console windows only (do not use CREATE_NEW_PROCESS_GROUP — it broke startup).
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if _IS_WINDOWS else 0


def _ffmpeg_popen_flags() -> int:
    return _CREATE_NO_WINDOW if _IS_WINDOWS else 0


def _run_ffmpeg(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    if _IS_WINDOWS:
        kwargs.setdefault("creationflags", _CREATE_NO_WINDOW)
    return subprocess.run(command, **kwargs)


def _explain_exit_code(code: int | None) -> str:
    if code is None:
        return "ainda em execucao"
    # Windows NTSTATUS codes often returned as unsigned 32-bit
    if code in (3221225786, -1073741510, 0xC000013A):
        return (
            f"codigo {code} (console fechado/Ctrl+C) — "
            "ffmpeg nao deve abrir janela CMD; atualize buffer.py"
        )
    if code in (3221225477, -1073741819, 0xC0000005):
        return f"codigo {code} (access violation)"
    return f"codigo {code}"


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
        self._watch_thread: threading.Thread | None = None
        self._ffmpeg_lock = threading.Lock()
        self._stderr_path = self.buffer_dir / "ffmpeg.stderr.log"
        self._stderr_handle = None
        self.last_error: str | None = None
        self.healthy = False

    def start(self) -> None:
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        self._stderr_path = self.buffer_dir / "ffmpeg.stderr.log"
        self._stop.clear()
        self._start_ffmpeg()
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True,
                name=f"cleanup-cam{self.camera.index}",
            )
            self._cleanup_thread.start()
        if self._watch_thread is None or not self._watch_thread.is_alive():
            self._watch_thread = threading.Thread(
                target=self._watch_loop,
                daemon=True,
                name=f"watch-cam{self.camera.index}",
            )
            self._watch_thread.start()

    def _segment_glob(self) -> list[Path]:
        """Current (.ts) and legacy (.mp4) rolling segments, oldest → newest."""
        items = list(self.buffer_dir.glob("segment_*.ts")) + list(
            self.buffer_dir.glob("segment_*.mp4")
        )
        return sorted(items, key=lambda p: (p.stat().st_mtime, p.name))

    def _ffmpeg_command(self, pattern: str) -> list[str]:
        # MPEG-TS segments + stream copy: reliable durations under RTSP (MP4
        # fragments often probed as ~0s and blocked clip upload).
        common_tail = [
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
            "mpegts",
            pattern,
        ]
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
                "mpegts",
                pattern,
            ]
        return [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-fflags",
            "+genpts+discardcorrupt",
            "-i",
            self.camera.rtsp_url,
            *common_tail,
        ]

    def _read_stderr_tail(self, max_chars: int = 500) -> str:
        try:
            if not self._stderr_path.is_file():
                return ""
            text = self._stderr_path.read_text(encoding="utf-8", errors="ignore").strip()
            if len(text) > max_chars:
                return text[-max_chars:]
            return text
        except OSError:
            return ""

    def _start_ffmpeg(self) -> None:
        pattern = str(self.buffer_dir / "segment_%05d.ts")
        command = self._ffmpeg_command(pattern)
        logger.info(
            "Starting buffer recorder for camera %s: %s",
            self.camera.index,
            self.camera.name,
        )
        self.healthy = False
        if self._stderr_handle is not None:
            try:
                self._stderr_handle.close()
            except OSError:
                pass
            self._stderr_handle = None
        try:
            self._stderr_handle = self._stderr_path.open(
                "w", encoding="utf-8", errors="replace"
            )
            stderr_target = self._stderr_handle
        except OSError:
            stderr_target = subprocess.DEVNULL
        # stdin=PIPE so we can send "q" to flush/close the active segment cleanly.
        # On Windows, CREATE_NO_WINDOW stops the blank ffmpeg CMD flash that was
        # killing recorders with exit 3221225786 (STATUS_CONTROL_C_EXIT).
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=stderr_target,
            creationflags=_ffmpeg_popen_flags(),
        )

    def status_line(self) -> str:
        if self.healthy:
            return f"Camera {self.camera.index}: gravando OK"
        if self.last_error:
            return f"Camera {self.camera.index}: FALHOU — {self.last_error}"
        return f"Camera {self.camera.index}: iniciando..."

    def _watch_loop(self) -> None:
        """Detect RTSP/ffmpeg failures instead of silently 'waiting for triggers'."""
        while not self._stop.is_set():
            time.sleep(2.0)
            with self._ffmpeg_lock:
                proc = self.process
                if proc is None:
                    self.healthy = False
                    continue
                code = proc.poll()
                segments = [
                    p for p in self._segment_glob() if p.is_file() and p.stat().st_size > 0
                ]
                if code is None and segments:
                    if not self.healthy:
                        logger.info(
                            "Camera %s buffer healthy (%s segment(s))",
                            self.camera.index,
                            len(segments),
                        )
                    self.healthy = True
                    self.last_error = None
                    continue
                if code is None:
                    # Still starting — give RTSP a few more cycles
                    age_ok = False
                    try:
                        # process running but no segments yet
                        age_ok = True
                    except Exception:
                        pass
                    if age_ok and not segments:
                        self.healthy = False
                        self.last_error = (
                            "sem segmentos ainda — confira IP/usuario/senha RTSP da camera"
                        )
                    continue

                # ffmpeg exited
                self.healthy = False
                tail = self._read_stderr_tail()
                explained = _explain_exit_code(code)
                self.last_error = (
                    tail.splitlines()[-1] if tail else f"ffmpeg saiu com {explained}"
                )
                logger.error(
                    "Camera %s buffer stopped (%s). %s",
                    self.camera.index,
                    explained,
                    self.last_error,
                )
                if self._stop.is_set():
                    break
                time.sleep(3.0)
                if self._stop.is_set():
                    break
                try:
                    logger.info("Restarting buffer for camera %s...", self.camera.index)
                    self._start_ffmpeg()
                except Exception:
                    logger.exception(
                        "Failed to restart buffer for camera %s", self.camera.index
                    )

    def _close_stderr(self) -> None:
        if self._stderr_handle is None:
            return
        try:
            self._stderr_handle.close()
        except OSError:
            pass
        self._stderr_handle = None

    def _quit_ffmpeg(self) -> None:
        """Ask ffmpeg to exit so the open segment file is closed and readable."""
        proc = self.process
        self.process = None
        try:
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
        finally:
            self._close_stderr()

    def _cleanup_loop(self) -> None:
        while not self._stop.is_set():
            cutoff = time.time() - self.buffer_seconds
            for path in self._segment_glob():
                try:
                    if path.stat().st_mtime < cutoff:
                        path.unlink(missing_ok=True)
                except OSError:
                    logger.exception("Failed to delete old segment %s", path)
            time.sleep(5)

    def list_segments(self, *, exclude_active: bool = True) -> list[Path]:
        """Return finished segments oldest→newest. Skip the file still being written."""
        segments = self._segment_glob()
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
        if self._watch_thread:
            self._watch_thread.join(timeout=2)
            self._watch_thread = None
        self.healthy = False

    def snapshot_segments(self, dest_dir: Path, *, keep_seconds: float = 45.0) -> list[Path]:
        """Flush live segment at button press, remux only recent buffer, resume.

        Only the last ~keep_seconds of segments are copied/remuxed (not 100+ files).
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        with self._ffmpeg_lock:
            self._quit_ffmpeg()
            time.sleep(0.4)
            sources = self._segment_glob()
            # Drop tiny junk files
            sources = [p for p in sources if p.stat().st_size >= 1024]
            if sources:
                newest_mtime = sources[-1].stat().st_mtime
                sources = [
                    p
                    for p in sources
                    if newest_mtime - p.stat().st_mtime <= keep_seconds + self.segment_seconds
                ]
            max_count = max(8, int(keep_seconds / max(1, self.segment_seconds)) + 4)
            sources = sources[-max_count:]

            raw_copies: list[Path] = []
            for src in sources:
                dest = dest_dir / src.name
                try:
                    shutil.copy2(src, dest)
                except OSError:
                    logger.warning("Could not snapshot %s", src)
                    continue
                if dest.stat().st_size > 0:
                    raw_copies.append(dest)

            if not self._stop.is_set():
                try:
                    self._start_ffmpeg()
                except Exception:
                    logger.exception(
                        "Failed to restart buffer for camera %s after snapshot",
                        self.camera.index,
                    )

        if not raw_copies:
            return []

        finalized: list[Path] = []
        for index, raw in enumerate(raw_copies):
            closed = dest_dir / f"seg_{index:03d}.mp4"
            if _finalize_mp4(raw, closed):
                raw.unlink(missing_ok=True)
                finalized.append(closed)
            else:
                logger.warning("Could not remux segment %s", raw.name)

        total = estimate_buffer_seconds(finalized, fallback_each=float(self.segment_seconds))
        logger.info(
            "Camera %s snapshot: %s segment(s), ~%.1fs buffered (target window 30s)",
            self.camera.index,
            len(finalized),
            total,
        )
        return finalized


def _finalize_mp4(source: Path, output_path: Path) -> bool:
    """Remux a .ts/.mp4 segment into a normal MP4."""
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-fflags",
        "+genpts",
        "-i",
        str(source),
        "-an",
        "-c:v",
        "copy",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = _run_ffmpeg(command, capture_output=True, text=True, check=False)
    if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1024:
        return True
    # Copy failed. Re-encode from the frame count, not the camera PTS, or this
    # segment is already a frozen loop before the clip join runs.
    output_path.unlink(missing_ok=True)
    fps = _output_fps([source])
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-fflags",
        "+genpts+discardcorrupt",
        "-i",
        str(source),
        "-an",
        "-vf",
        f"setpts=N/({fps}*TB)",
        "-vsync",
        "cfr",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = _run_ffmpeg(command, capture_output=True, text=True, check=False)
    return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1024


def estimate_buffer_seconds(
    segment_paths: list[Path],
    *,
    fallback_each: float = 2.0,
) -> float:
    """How many real seconds these files cover.

    Court cameras often stamp a 2–5s GOP with a huge PTS gap. ffprobe then
    reports 20–30s for a file that only contains a few seconds of pictures,
    and the old probe-first sum made a frozen clip look like a full buffer.
    Wall-clock mtime (when ffmpeg closed each segment) is the real span.
    """
    if not segment_paths:
        return 0.0
    try:
        mtimes = [p.stat().st_mtime for p in segment_paths]
        span = max(mtimes) - min(mtimes)
        if span >= 1.0:
            return span + fallback_each
    except OSError:
        pass
    probed = 0.0
    known = 0
    for path in segment_paths:
        duration = media_duration(path)
        if duration > 0.05:
            probed += duration
            known += 1
    if known:
        if known < len(segment_paths):
            probed += (probed / known) * (len(segment_paths) - known)
        return probed
    return float(len(segment_paths)) * fallback_each


def select_segments_for_clip(
    segment_paths: list[Path],
    clip_seconds: int,
    *,
    fallback_each: float = 2.0,
) -> list[Path]:
    """Take the newest segments that cover clip_seconds of wall clock.

    Do not trust ffprobe duration here. A segment whose pictures last 5s can
    probe as 30s, and summing those durations kept only one GOP — which the
    encoder then held/repeated until the clip was 30s ("same 5s scene").
    """
    if not segment_paths:
        return []
    try:
        newest = max(p.stat().st_mtime for p in segment_paths)
        # One extra segment so the trim still has a frame before the window.
        cutoff = newest - float(clip_seconds) - float(fallback_each)
        chosen = [p for p in segment_paths if p.stat().st_mtime >= cutoff]
    except OSError:
        chosen = []
    if not chosen:
        count = max(1, int(float(clip_seconds) / max(0.5, float(fallback_each))) + 2)
        chosen = list(segment_paths[-count:])
    return chosen


def build_clip(
    segment_paths: list[Path],
    output_path: Path,
    *,
    clip_seconds: int = 30,
    watermark_path: Path | None = None,
    watermark_height_percent: float = 16.0,
) -> None:
    """Concat buffer segments, keep exactly clip_seconds from the end, burn bottom watermark."""
    if not segment_paths:
        raise RuntimeError("No buffer segments available for clip")

    selected = select_segments_for_clip(segment_paths, clip_seconds, fallback_each=2.0)
    if not selected:
        selected = segment_paths

    output_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = output_path.with_suffix(".txt")
    concat_path = output_path.with_name(output_path.stem + "_concat.mp4")

    with list_file.open("w", encoding="utf-8") as handle:
        for segment in selected:
            # concat demuxer needs escaped single quotes in paths
            path = str(segment.resolve()).replace("'", r"'\''")
            handle.write(f"file '{path}'\n")

    # Rebuild timestamps from the frame count. Camera PTS often has a multi-second
    # hole inside each GOP; the old encode filled that hole by repeating the last
    # picture, so a 5s moment became a 30s clip of the same scene. One coded
    # frame must become exactly 1/fps of output, then we trim.
    fps = _output_fps(selected)
    logger.info(
        "Joining %s segment(s) at %sfps (ignoring camera timestamps)",
        len(selected),
        fps,
    )
    concat_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-fflags",
        "+genpts+discardcorrupt",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-an",
        "-vf",
        f"setpts=N/({fps}*TB)",
        "-vsync",
        "cfr",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-g",
        str(fps),
        "-movflags",
        "+faststart",
        str(concat_path),
    ]
    result = _run_ffmpeg(concat_cmd, capture_output=True, text=True, check=False)
    list_file.unlink(missing_ok=True)
    if result.returncode != 0 or not concat_path.exists():
        concat_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise RuntimeError(result.stderr.strip() or "Failed to concatenate buffer segments")

    concat_duration = media_duration(concat_path)
    logger.info(
        "Concatenated %s segment(s) into %.2fs buffer; trimming last %ss",
        len(selected),
        concat_duration,
        clip_seconds,
    )
    if concat_duration > 0 and concat_duration + 0.75 < clip_seconds:
        logger.warning(
            "Buffer only has %.1fs (wanted %ss). Clip will be shorter — wait longer "
            "after start before pressing, or check camera RTSP stability.",
            concat_duration,
            clip_seconds,
        )

    try:
        _render_final_clip(
            concat_path,
            output_path,
            clip_seconds=clip_seconds,
            watermark_path=watermark_path,
            watermark_height_percent=watermark_height_percent,
        )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("Generated clip is empty")
        final_duration = assert_clip_playable(output_path)
    except Exception:
        # Never leave a broken file in clips/. The next start picks those up
        # and uploads them (unplayable recordings).
        output_path.unlink(missing_ok=True)
        raise
    finally:
        concat_path.unlink(missing_ok=True)

    logger.info("Final clip duration=%.2fs (target=%ss)", final_duration, clip_seconds)


def media_duration(path: Path) -> float:
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
    result = _run_ffmpeg(command, capture_output=True, text=True, check=False)
    text = (result.stdout or "").strip()
    if text and text.upper() != "N/A":
        try:
            return max(0.0, float(text))
        except ValueError:
            pass
    # Fallback: count packets / stream duration
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = _run_ffmpeg(command, capture_output=True, text=True, check=False)
    text = (result.stdout or "").strip().splitlines()
    for line in text:
        if line and line.upper() != "N/A":
            try:
                return max(0.0, float(line))
            except ValueError:
                continue
    return 0.0


def media_fps(path: Path) -> float:
    """Stream frame rate, or 0 when the metadata is missing or absurd."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = _run_ffmpeg(command, capture_output=True, text=True, check=False)
    text = (result.stdout or "").strip().splitlines()
    for line in text:
        if not line or line.upper() == "N/A":
            continue
        try:
            if "/" in line:
                num, den = line.split("/", 1)
                den_f = float(den)
                if den_f == 0:
                    continue
                return float(num) / den_f
            return float(line)
        except ValueError:
            continue
    return 0.0


def _output_fps(paths: list[Path]) -> int:
    for path in paths:
        fps = media_fps(path)
        if 10.0 <= fps <= 60.0:
            return int(round(fps))
    return 30


def assert_clip_playable(path: Path) -> float:
    """Refuse to upload a file that players cannot decode.

    A zero-length moov, a missing keyframe, or a clip shorter than a second
    used to be queued anyway. The API stores those bytes and the phone shows
    a recording that will not play.
    """
    if not path.exists() or path.stat().st_size < 4096:
        raise RuntimeError(f"Clip is missing or too small to play: {path.name}")
    duration = media_duration(path)
    if duration < 1.0:
        raise RuntimeError(f"Clip is {duration:.2f}s — not playable")
    command = [
        "ffmpeg",
        "-hide_banner",
        "-v",
        "error",
        "-xerror",
        "-i",
        str(path),
        "-f",
        "null",
        "-",
    ]
    result = _run_ffmpeg(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()
        tail = detail[-1] if detail else "decode failed"
        raise RuntimeError(f"Clip will not play: {tail[:240]}")
    return duration


# Alias for older service.py imports after partial court-PC updates
_media_duration = media_duration


def media_height(path: Path) -> int:
    """Return video frame height in pixels, or 0 if unknown."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=height",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = _run_ffmpeg(command, capture_output=True, text=True, check=False)
    text = (result.stdout or "").strip().splitlines()
    for line in text:
        if line.isdigit():
            return max(0, int(line))
    return 0


def _normalize_watermark_height_percent(height_percent: float) -> float:
    """Clamp logo size to a usable share of frame height (5–40%).

    Values above 40 were often saved under the old broken scale (main_h = logo
    pixels, not frame height). Map those to a sensible default so court PCs do
    not suddenly burn a near-fullscreen logo after the fix.
    """
    try:
        pct = float(height_percent)
    except (TypeError, ValueError):
        pct = 16.0
    if pct > 40.0:
        return 16.0
    return max(5.0, min(40.0, pct))


def _render_final_clip(
    source: Path,
    output_path: Path,
    *,
    clip_seconds: int,
    watermark_path: Path | None,
    watermark_height_percent: float = 16.0,
) -> None:
    """Keep the last N seconds, ending at the latest captured frame (button press)."""
    duration = media_duration(source)
    if duration <= 0:
        # Last resort: take whole file with -sseof
        start = None
    else:
        # End at the last frame (button press); start clip_seconds earlier
        start = max(0.0, duration - float(clip_seconds))

    logger.info(
        "Trim window: source=%.2fs start=%s length=%ss (ends at button press)",
        duration,
        f"{start:.3f}" if start is not None else "sseof",
        clip_seconds,
    )

    if watermark_path and watermark_path.exists():
        _render_final_clip_watermarked(
            source,
            output_path,
            clip_seconds,
            watermark_path,
            start=start,
            source_duration=duration,
            height_percent=watermark_height_percent,
        )
        return

    if watermark_path:
        logger.warning("Watermark file missing: %s", watermark_path)

    # Accurate trim: decode from start, hard-limit to clip_seconds
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
    result = _run_ffmpeg(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to render final clip")


def _render_final_clip_watermarked(
    source: Path,
    output_path: Path,
    clip_seconds: int,
    watermark_path: Path,
    start: float | None = None,
    source_duration: float = 0.0,
    height_percent: float = 16.0,
) -> None:
    """Bottom-centered watermark. height_percent = logo height vs video frame height."""
    pct = _normalize_watermark_height_percent(height_percent)
    # CRITICAL: use rh (reference / video height), NOT main_h (watermark image height).
    # Old main_h*pct made "80%" only ~80% of the logo file — tiny on 1080p.
    scale_h = f"rh*{pct / 100.0:.4f}"
    frame_h = media_height(source) or 1080
    fallback_h = str(max(64, int(round(frame_h * pct / 100.0))))
    logger.info(
        "Watermark size: %.1f%% of frame height (frame~%spx → logo~%spx)",
        pct,
        frame_h,
        fallback_h,
    )

    # Use filter trim from a known start so the window always ends at EOF (button).
    if start is not None and source_duration > 0:
        # trim end = source end; duration may be < clip_seconds if buffer is short
        actual_len = min(float(clip_seconds), max(0.1, source_duration - start))
        filter_trim = f"trim=start={start:.3f}:duration={actual_len:.3f},setpts=PTS-STARTPTS"
        input_seek: list[str] = []
    elif start is not None:
        filter_trim = "setpts=PTS-STARTPTS"
        input_seek = ["-ss", f"{start:.3f}"]
    else:
        filter_trim = "setpts=PTS-STARTPTS"
        input_seek = ["-sseof", f"-{clip_seconds}"]

    def run(filter_complex: str) -> subprocess.CompletedProcess:
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *input_seek,
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
        return _run_ffmpeg(command, capture_output=True, text=True, check=False)

    result = run(
        f"[0:v]{filter_trim}[base];"
        f"[1:v][base]scale2ref=h={scale_h}:w=oh*mdar[wm][v];"
        "[v][wm]overlay=(W-w)/2:H-h-16[out]"
    )
    if result.returncode != 0:
        logger.warning(
            "scale2ref(rh) failed; using fixed watermark height %s (%s)",
            fallback_h,
            (result.stderr or "").strip()[:240],
        )
        result = run(
            f"[0:v]{filter_trim}[base];"
            f"[1:v]scale=-1:{fallback_h}[wm];"
            "[base][wm]overlay=(W-w)/2:H-h-16[out]"
        )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to render watermarked clip")


def clip_trigger_time(segment_paths: list[Path]) -> datetime:
    latest = max(segment_paths, key=lambda p: p.stat().st_mtime)
    return datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)
