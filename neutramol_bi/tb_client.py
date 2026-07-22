"""ThingsBoard REST API client with automatic JWT token management."""

import time
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ThingsBoardClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._token: str | None = None
        self._token_expires_at: float = 0
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # ── Authentication ─────────────────────────────────────────────────────

    def _login(self) -> None:
        url = f"{self.base_url}/api/auth/login"
        resp = self.session.post(url, json={"username": self.username, "password": self.password}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        self._token = data["token"]
        # TB tokens expire in ~2.5h; refresh every 2h to be safe
        self._token_expires_at = time.time() + 7200
        self.session.headers.update({"X-Authorization": f"Bearer {self._token}"})
        logger.info("ThingsBoard login successful")

    def _ensure_token(self) -> None:
        if self._token is None or time.time() >= self._token_expires_at:
            self._login()

    def _get(self, path: str, params: dict | None = None) -> Any:
        self._ensure_token()
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params, timeout=60)
        if resp.status_code == 401:
            # Token expired — force refresh and retry once
            self._token = None
            self._ensure_token()
            resp = self.session.get(url, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()

    # ── Telemetry ──────────────────────────────────────────────────────────

    def get_latest_telemetry(self, device_id: str, keys: list[str]) -> dict[str, list[dict]]:
        """
        Returns latest values for each key.
        Response shape: {"AI1": [{"ts": 1234567890, "value": "123.4"}], ...}
        """
        path = f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
        params = {"keys": ",".join(keys)}
        return self._get(path, params)

    def get_timeseries(
        self,
        device_id: str,
        keys: list[str],
        start_ts: int,
        end_ts: int,
        limit: int = 5000,
        agg: str = "NONE",
        interval_ms: int | None = None,
    ) -> dict[str, list[dict]]:
        """
        Returns historical timeseries data for the given time range.
        Iterates automatically when the response hits the limit.
        """
        path = f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
        all_results: dict[str, list[dict]] = {k: [] for k in keys}

        current_end = end_ts
        while True:
            params: dict = {
                "keys": ",".join(keys),
                "startTs": start_ts,
                "endTs": current_end,
                "limit": limit,
                "agg": agg,
                "orderBy": "DESC",
            }
            if interval_ms:
                params["interval"] = interval_ms

            data = self._get(path, params)

            total_new = 0
            oldest_ts = current_end
            for key in keys:
                records = data.get(key, [])
                all_results[key].extend(records)
                total_new += len(records)
                if records:
                    oldest_ts = min(oldest_ts, min(r["ts"] for r in records))

            logger.debug("Fetched %d records for %s up to %s", total_new, device_id, current_end)

            # Stop if we got fewer than limit (no more data) or reached start
            if total_new < limit or oldest_ts <= start_ts:
                break

            # Move window back to fetch older data
            current_end = oldest_ts - 1

        return all_results

    def get_attributes(self, device_id: str) -> dict:
        """Returns all server-side and shared attributes."""
        path = f"/api/plugins/telemetry/DEVICE/{device_id}/values/attributes"
        return self._get(path)

    # ── Alarms ────────────────────────────────────────────────────────────

    def get_alarms(
        self,
        device_id: str,
        page: int = 0,
        page_size: int = 100,
        status_filter: str | None = None,
        fetch_originator: bool = True,
    ) -> dict:
        """Returns alarm page for a device."""
        path = f"/api/alarm/DEVICE/{device_id}"
        params = {
            "page": page,
            "pageSize": page_size,
            "fetchOriginator": str(fetch_originator).lower(),
            "sortProperty": "createdTime",
            "sortOrder": "DESC",
        }
        if status_filter:
            params["statusList"] = status_filter
        return self._get(path, params)

    def get_all_alarms(self, device_id: str) -> list[dict]:
        """Fetches all alarm pages for a device."""
        all_alarms = []
        page = 0
        while True:
            data = self.get_alarms(device_id, page=page)
            alarms = data.get("data", [])
            all_alarms.extend(alarms)
            if data.get("hasNext", False):
                page += 1
            else:
                break
        return all_alarms
