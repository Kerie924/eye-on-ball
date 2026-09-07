"""Persist clips locally and upload them when the cloud is reachable."""

from __future__ import annotations

import json
import logging
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)


class UploadQueue:
    def __init__(
        self,
        data_dir: Path,
        *,
        max_hours: int = 48,
        max_mb: int = 4096,
    ) -> None:
        self.root = Path(data_dir) / "upload-queue"
        self.files_dir = self.root / "files"
        self.jobs_path = self.root / "jobs.json"
        self.max_hours = max(1, int(max_hours))
        self.max_bytes = max(50, int(max_mb)) * 1024 * 1024
        self._lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def enqueue(
        self,
        camera_index: int,
        clip_path: Path,
        triggered_at: datetime,
    ) -> dict:
        if not clip_path.exists() or clip_path.stat().st_size == 0:
            raise RuntimeError(f"Clip is missing or empty: {clip_path}")

        job_id = f"{int(time.time())}-{camera_index}-{uuid4().hex[:8]}"
        dest = self.files_dir / f"{job_id}.mp4"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(clip_path), dest)

        if triggered_at.tzinfo is None:
            triggered_at = triggered_at.replace(tzinfo=timezone.utc)

        job = {
            "id": job_id,
            "camera_index": int(camera_index),
            "clip_path": str(dest),
            "triggered_at": triggered_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
            "last_error": None,
        }
        with self._lock:
            jobs = self._read_jobs()
            jobs.append(job)
            self._write_jobs(jobs)
        self.prune()
        logger.info(
            "Queued clip %s for camera %s (%s bytes). Will upload when the API is reachable.",
            job_id,
            camera_index,
            dest.stat().st_size,
        )
        return job

    def pending(self) -> list[dict]:
        with self._lock:
            jobs = [job for job in self._read_jobs() if Path(job["clip_path"]).exists()]
            if len(jobs) != len(self._read_jobs()):
                self._write_jobs(jobs)
            return list(jobs)

    def next_job(self) -> dict | None:
        jobs = self.pending()
        return jobs[0] if jobs else None

    def mark_uploaded(self, job_id: str) -> None:
        with self._lock:
            jobs = self._read_jobs()
            kept = []
            for job in jobs:
                if job["id"] != job_id:
                    kept.append(job)
                    continue
                Path(job["clip_path"]).unlink(missing_ok=True)
            self._write_jobs(kept)

    def mark_failed(self, job_id: str, error: str) -> None:
        with self._lock:
            jobs = self._read_jobs()
            for job in jobs:
                if job["id"] == job_id:
                    job["attempts"] = int(job.get("attempts") or 0) + 1
                    job["last_error"] = error[:300]
                    break
            self._write_jobs(jobs)

    def recover_orphans(self, camera_indexes: list[int]) -> int:
        """Pick up leftover clips from older versions that uploaded inline."""
        added = 0
        with self._lock:
            jobs = self._read_jobs()
            known = {Path(job["clip_path"]).resolve() for job in jobs}
            for loose in sorted(self.files_dir.glob("*.mp4")):
                if loose.resolve() in known or loose.stat().st_size == 0:
                    continue
                camera_index = _camera_from_name(loose.name)
                mtime = loose.stat().st_mtime
                triggered = datetime.fromtimestamp(mtime, tz=timezone.utc)
                jobs.append(
                    {
                        "id": loose.stem,
                        "camera_index": camera_index,
                        "clip_path": str(loose),
                        "triggered_at": triggered.isoformat(),
                        "created_at": triggered.isoformat(),
                        "attempts": 0,
                        "last_error": None,
                    }
                )
                known.add(loose.resolve())
                added += 1
            for camera_index in camera_indexes:
                clips_dir = self.root.parent / f"camera-{camera_index}" / "clips"
                if not clips_dir.is_dir():
                    continue
                for clip_path in sorted(clips_dir.glob("clip_*.mp4")):
                    if clip_path.resolve() in known or clip_path.stat().st_size == 0:
                        continue
                    mtime = clip_path.stat().st_mtime
                    job_id = f"{int(mtime)}-{camera_index}-{uuid4().hex[:8]}"
                    dest = self.files_dir / f"{job_id}.mp4"
                    shutil.move(str(clip_path), dest)
                    triggered = datetime.fromtimestamp(mtime, tz=timezone.utc)
                    jobs.append(
                        {
                            "id": job_id,
                            "camera_index": camera_index,
                            "clip_path": str(dest),
                            "triggered_at": triggered.isoformat(),
                            "created_at": triggered.isoformat(),
                            "attempts": 0,
                            "last_error": None,
                        }
                    )
                    known.add(dest.resolve())
                    added += 1
            if added:
                self._write_jobs(jobs)
        if added:
            logger.info("Recovered %s leftover clip(s) into the upload queue", added)
        return added

    def prune(self) -> None:
        cutoff = time.time() - self.max_hours * 3600
        with self._lock:
            jobs = self._read_jobs()
            kept: list[dict] = []
            dropped = 0
            for job in jobs:
                path = Path(job["clip_path"])
                created = _parse_ts(job.get("created_at"))
                if not path.exists():
                    dropped += 1
                    continue
                if created < cutoff:
                    path.unlink(missing_ok=True)
                    dropped += 1
                    logger.warning(
                        "Dropped queued clip %s (older than %sh)",
                        job["id"],
                        self.max_hours,
                    )
                    continue
                kept.append(job)

            total = sum(Path(job["clip_path"]).stat().st_size for job in kept if Path(job["clip_path"]).exists())
            while kept and total > self.max_bytes:
                job = kept.pop(0)
                path = Path(job["clip_path"])
                size = path.stat().st_size if path.exists() else 0
                path.unlink(missing_ok=True)
                total -= size
                dropped += 1
                logger.warning("Dropped queued clip %s to stay under disk limit", job["id"])

            if dropped:
                self._write_jobs(kept)

    def _read_jobs(self) -> list[dict]:
        if not self.jobs_path.exists():
            return []
        try:
            payload = json.loads(self.jobs_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.exception("Upload queue index is unreadable; starting a new one")
            return []
        return payload if isinstance(payload, list) else []

    def _write_jobs(self, jobs: list[dict]) -> None:
        tmp = self.jobs_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
        tmp.replace(self.jobs_path)


def _camera_from_name(name: str) -> int:
    parts = name.split("-")
    if len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1])
    return 1


def _parse_ts(value: str | None) -> float:
    if not value:
        return time.time()
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        return time.time()
