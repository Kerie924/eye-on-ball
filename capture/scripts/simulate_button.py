#!/usr/bin/env python3
"""Simulate a button press for mock mode testing."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.paths import mock_trigger_path


def main() -> int:
    camera_index = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    trigger_file = mock_trigger_path(camera_index)
    trigger_file.parent.mkdir(parents=True, exist_ok=True)
    trigger_file.write_text("trigger\n", encoding="utf-8")
    print(f"Triggered mock button for camera {camera_index}: {trigger_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
