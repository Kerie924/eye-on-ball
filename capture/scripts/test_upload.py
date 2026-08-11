#!/usr/bin/env python3
"""Upload a sample clip to verify API connectivity without cameras."""

import argparse
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.api_client import ApiClient
from agent.config import load_config


def make_test_clip(path: Path, seconds: int = 3) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=size=1280x720:rate=25:duration={seconds}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(path),
    ]
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Test upload to Lance On backend")
    parser.add_argument("--config", default="config.example.yaml")
    parser.add_argument("--camera", type=int, default=1)
    args = parser.parse_args()

    config = load_config(ROOT / args.config)
    api = ApiClient(config.api_url, config.device_key)

    if not api.health_check():
        print("Backend health check failed")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "test_clip.mp4"
        make_test_clip(clip)
        payload = api.upload_recording(args.camera, clip, datetime.now(timezone.utc))
        print("Upload ok:", payload)

    api.heartbeat(args.camera)
    print("Heartbeat ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
