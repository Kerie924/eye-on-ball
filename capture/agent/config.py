from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ButtonConfig:
    type: str
    port: str | None = None
    baudrate: int = 115200
    trigger_on: str = "1"
    pin: int | None = None
    mock_file: str | None = None


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

    @property
    def segment_count(self) -> int:
        return max(1, self.buffer_seconds // self.segment_seconds)

    @property
    def segments_for_clip(self) -> int:
        return max(1, -(-self.clip_seconds // self.segment_seconds))


def load_config(path: str | Path) -> AgentConfig:
    with open(path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    cameras = []
    for item in raw["cameras"]:
        button_raw = item.get("button", {"type": "mock"})
        cameras.append(
            CameraConfig(
                index=int(item["index"]),
                name=item.get("name", f"Camera {item['index']}"),
                rtsp_url=item["rtsp_url"],
                button=ButtonConfig(
                    type=button_raw.get("type", "mock"),
                    port=button_raw.get("port"),
                    baudrate=int(button_raw.get("baudrate", 115200)),
                    trigger_on=str(button_raw.get("trigger_on", str(item["index"]))),
                    pin=button_raw.get("pin"),
                    mock_file=button_raw.get("mock_file"),
                ),
            )
        )

    return AgentConfig(
        api_url=raw["api_url"].rstrip("/"),
        device_key=raw["device_key"],
        buffer_seconds=int(raw.get("buffer_seconds", 300)),
        clip_seconds=int(raw.get("clip_seconds", 30)),
        segment_seconds=int(raw.get("segment_seconds", 10)),
        heartbeat_seconds=int(raw.get("heartbeat_seconds", 60)),
        button_cooldown_seconds=int(raw.get("button_cooldown_seconds", 3)),
        data_dir=Path(raw.get("data_dir", "/var/lib/olho-no-lance")),
        cameras=cameras,
    )
