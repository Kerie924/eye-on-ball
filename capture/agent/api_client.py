import logging
import time
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Heartbeat/poll: fail fast. Uploads: long timeout — Windows applies the
# connect timeout to socket *writes*, so a 20s connect killed 7–8MB POSTs
# ("The write operation timed out") on slow court uplinks.
_HEARTBEAT_TIMEOUT = (8, 15)
_POLL_TIMEOUT = (8, 15)
_UPLOAD_TIMEOUT = (300, 300)
_UPLOAD_RETRIES = 3
_UPLOAD_RETRY_DELAY = 5


class ApiClient:
    def __init__(self, api_url: str, device_key: str, timeout: int = 300) -> None:
        self.api_url = api_url.rstrip("/")
        self.device_key = device_key
        self.timeout = timeout
        self.headers = {"X-Device-Key": device_key, "Connection": "close"}

    def heartbeat(self, camera_index: int) -> None:
        response = requests.post(
            f"{self.api_url}/api/devices/heartbeat",
            json={"camera_index": camera_index},
            headers=self.headers,
            timeout=_HEARTBEAT_TIMEOUT,
        )
        response.raise_for_status()

    def claim_pending_triggers(self) -> list[dict]:
        response = requests.get(
            f"{self.api_url}/api/devices/pending-triggers",
            headers=self.headers,
            timeout=_POLL_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else []

    def upload_recording(
        self,
        camera_index: int,
        clip_path: Path,
        triggered_at: datetime,
        retries: int = _UPLOAD_RETRIES,
    ) -> dict:
        last_error: Exception | None = None
        attempts = max(1, retries)
        for attempt in range(1, attempts + 1):
            try:
                with clip_path.open("rb") as handle:
                    response = requests.post(
                        f"{self.api_url}/api/recordings/upload",
                        headers=self.headers,
                        data={
                            "camera_index": str(camera_index),
                            "triggered_at": triggered_at.isoformat(),
                        },
                        files={"file": (clip_path.name, handle, "video/mp4")},
                        timeout=_UPLOAD_TIMEOUT,
                    )
                response.raise_for_status()
                payload = response.json()
                logger.info(
                    "Uploaded recording #%s for camera %s",
                    payload.get("id"),
                    camera_index,
                )
                return payload
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                logger.warning(
                    "Upload for camera %s failed (%s: %s); retry %s/%s in %ss",
                    camera_index,
                    exc.__class__.__name__,
                    str(exc).replace("\n", " ")[:180],
                    attempt,
                    attempts,
                    _UPLOAD_RETRY_DELAY,
                )
                time.sleep(_UPLOAD_RETRY_DELAY)
            except requests.HTTPError as exc:
                last_error = exc
                status = exc.response.status_code if exc.response is not None else "?"
                body = ""
                if exc.response is not None:
                    try:
                        body = (exc.response.text or "")[:180]
                    except Exception:
                        body = ""
                logger.warning(
                    "Upload for camera %s HTTP %s: %s",
                    camera_index,
                    status,
                    body,
                )
                break
        assert last_error is not None
        raise last_error

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            return response.ok
        except requests.RequestException:
            return False
