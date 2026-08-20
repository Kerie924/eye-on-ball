from dataclasses import dataclass
from pathlib import Path

import yaml

MAX_CAMERAS = 6


@dataclass
class ButtonConfig:
    type: str
    port: str | None = None
    baudrate: int = 115200
    trigger_on: str = "1"
    pin: int | None = None
    mock_file: str | None = None

    @property
    def enabled(self) -> bool:
        return self.type not in {"", "none", "disabled"}


@dataclass
class CameraConfig:
    index: int
    name: str
    rtsp_url: str
    button: ButtonConfig


@dataclass
class AgentConfig:
    api_url: str
    device_key: str
    buffer_seconds: int
    clip_seconds: int
    segment_seconds: int
    heartbeat_seconds: int
    button_cooldown_seconds: int
    data_dir: Path
    cameras: list[CameraConfig]
    court_button: ButtonConfig | None = None
    watermark_path: Path | None = None

    @property
    def segment_count(self) -> int:
        return max(1, self.buffer_seconds // self.segment_seconds)

    @property
    def segments_for_clip(self) -> int:
        """Finished segments needed to cover clip_seconds (plus one spare for trim)."""
        base = max(1, -(-self.clip_seconds // self.segment_seconds))
        return base + 1


def _parse_button(raw: dict | None, default_trigger: str = "1") -> ButtonConfig:
    button_raw = raw or {"type": "none"}
    return ButtonConfig(
        type=str(button_raw.get("type", "none")),
        port=button_raw.get("port"),
        baudrate=int(button_raw.get("baudrate", 115200)),
        trigger_on=str(button_raw.get("trigger_on", default_trigger)),
        pin=button_raw.get("pin"),
        mock_file=button_raw.get("mock_file"),
    )


def load_config(path: str | Path) -> AgentConfig:
    with open(path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    cameras = []
    for item in raw["cameras"]:
        index = int(item["index"])
        cameras.append(
            CameraConfig(
                index=index,
                name=item.get("name", f"Camera {index}"),
                rtsp_url=item["rtsp_url"],
                button=_parse_button(item.get("button"), default_trigger=str(index)),
            )
        )

    if not cameras:
        raise ValueError("At least one camera is required")
    if len(cameras) > MAX_CAMERAS:
        raise ValueError(f"Maximum {MAX_CAMERAS} cameras per court")

    indexes = [camera.index for camera in cameras]
    if any(index < 1 or index > MAX_CAMERAS for index in indexes):
        raise ValueError(f"Camera index must be between 1 and {MAX_CAMERAS}")
    if len(set(indexes)) != len(indexes):
        raise ValueError("Camera indexes must be unique")

    court_button_raw = raw.get("button")
    court_button = _parse_button(court_button_raw) if court_button_raw else None
    if court_button and not court_button.enabled:
        court_button = None

    config_dir = Path(path).resolve().parent
    watermark_raw = raw.get("watermark_path", "assets/video-watermark.jpeg")
    watermark_path = Path(watermark_raw)
    if not watermark_path.is_absolute():
        # Prefer path relative to config file, then relative to agent install dir.
        candidates = [
            config_dir / watermark_path,
            Path("/opt/lance-on/capture") / watermark_path,
            Path(__file__).resolve().parent.parent / watermark_path,
        ]
        watermark_path = next((p for p in candidates if p.exists()), candidates[0])

    return AgentConfig(
        api_url=raw["api_url"].rstrip("/"),
        device_key=raw["device_key"],
        buffer_seconds=int(raw.get("buffer_seconds", 300)),
        clip_seconds=int(raw.get("clip_seconds", 30)),
        segment_seconds=int(raw.get("segment_seconds", 10)),
        heartbeat_seconds=int(raw.get("heartbeat_seconds", 60)),
        button_cooldown_seconds=int(raw.get("button_cooldown_seconds", 3)),
        data_dir=Path(raw.get("data_dir", "/var/lib/lance-on")),
        cameras=cameras,
        court_button=court_button,
        watermark_path=watermark_path,
    )
