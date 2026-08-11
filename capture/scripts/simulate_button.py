#!/usr/bin/env python3
"""Simulate a button press for mock mode testing."""

import sys
import time
from pathlib import Path


def main() -> int:
    camera_index = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    trigger_file = Path(f"/tmp/lanceon-button-{camera_index}.trigger")
    trigger_file.write_text(str(time.time()), encoding="utf-8")
    print(f"Triggered mock button for camera {camera_index}: {trigger_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
