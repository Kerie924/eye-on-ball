import logging
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, api_url: str, device_key: str, timeout: int = 120) -> None:
        self.api_url = api_url.rstrip("/")
        self.device_key = device_key
        self.timeout = timeout
        self.headers = {"X-Device-Key": device_key}

    def heartbeat(self, camera_index: int) -> None:
        response = requests.post(
            f"{self.api_url}/api/devices/heartbeat",
            json={"camera_index": camera_index},
            headers=self.headers,
            timeout=15,
        )
        response.raise_for_status()

    def claim_pending_triggers(self) -> list[dict]:
        response = requests.get(
            f"{self.api_url}/api/devices/pending-triggers",
            headers=self.headers,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else []

    def upload_recording(
        self,
        camera_index: int,
        clip_path: Path,
        triggered_at: datetime,
    ) -> dict:
        with clip_path.open("rb") as handle:
            response = requests.post(
                f"{self.api_url}/api/recordings/upload",
                headers=self.headers,
                data={
                    "camera_index": str(camera_index),
                    "triggered_at": triggered_at.isoformat(),
                },
                files={"file": (clip_path.name, handle, "video/mp4")},
                timeout=self.timeout,
            )
        response.raise_for_status()
        payload = response.json()
        logger.info(
            "Uploaded recording #%s for camera %s",
            payload.get("id"),
            camera_index,
        )
        return payload

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            return response.ok
        except requests.RequestException:
            return False
