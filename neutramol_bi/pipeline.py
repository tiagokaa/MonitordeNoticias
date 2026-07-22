"""
Pipeline logic: fetches data from ThingsBoard and stores it in SQLite.

Modes:
  - sync_latest    : fetch current values for all devices
  - sync_history   : fetch historical timeseries (incremental from last sync)
  - sync_alarms    : fetch all alarms for all devices
"""

import logging
import sqlite3
from datetime import datetime, timedelta, timezone

from registry import CALIBRATIONS, DEVICES, calibrate
from tb_client import ThingsBoardClient
from database import (
    get_last_sync_ts,
    insert_history_batch,
    set_last_sync_ts,
    upsert_alarms,
    upsert_latest,
    upsert_telemetry_keys,
)

logger = logging.getLogger(__name__)


def _parse_value(raw_str: str | None) -> float | None:
    if raw_str is None:
        return None
    try:
        return float(raw_str)
    except (ValueError, TypeError):
        return None


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


# ── Seed device registry ───────────────────────────────────────────────────

def seed_registry(conn: sqlite3.Connection) -> None:
    """Insert/update device and key metadata into the database."""
    from database import upsert_devices

    upsert_devices(conn, DEVICES)

    for dev in DEVICES:
        for key in dev["keys"]:
            cal = CALIBRATIONS.get((dev["id"], key))
            upsert_telemetry_keys(conn, dev["id"], key, cal=cal)

    conn.commit()
    logger.info("Device registry seeded: %d devices", len(DEVICES))


# ── Latest values ──────────────────────────────────────────────────────────

def sync_latest(client: ThingsBoardClient, conn: sqlite3.Connection) -> None:
    """Fetch the most recent value of every key for every device."""
    for dev in DEVICES:
        device_id = dev["id"]
        keys = dev["keys"]
        try:
            data = client.get_latest_telemetry(device_id, keys)
        except Exception as exc:
            logger.error("Failed latest telemetry for %s (%s): %s", dev["name"], device_id, exc)
            continue

        for key, records in data.items():
            if not records:
                continue
            rec = records[0]
            ts = rec["ts"]
            raw = _parse_value(rec.get("value"))
            cal_val = calibrate(raw, device_id, key) if raw is not None else None
            upsert_latest(conn, device_id, key, raw, cal_val, ts)

        conn.commit()
        logger.info("Latest synced: %s (%d keys)", dev["name"], len(data))


# ── Historical series ──────────────────────────────────────────────────────

def sync_history(
    client: ThingsBoardClient,
    conn: sqlite3.Connection,
    history_days: int = 30,
    batch_size: int = 5000,
) -> None:
    """
    Fetch historical timeseries incrementally.
    On first run: fetches last `history_days` days.
    On subsequent runs: fetches from last synced timestamp.
    """
    now_ms = _now_ms()

    for dev in DEVICES:
        device_id = dev["id"]
        keys = dev["keys"]

        last_ts = get_last_sync_ts(conn, device_id, "history")
        if last_ts:
            start_ts = last_ts + 1
            logger.info("Incremental history for %s from %s", dev["name"],
                        datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc).isoformat())
        else:
            start_ts = int((datetime.now(timezone.utc) - timedelta(days=history_days)).timestamp() * 1000)
            logger.info("Full history for %s (%d days)", dev["name"], history_days)

        if start_ts >= now_ms:
            logger.info("No new history for %s", dev["name"])
            continue

        try:
            data = client.get_timeseries(device_id, keys, start_ts, now_ms, limit=batch_size)
        except Exception as exc:
            logger.error("Failed history for %s (%s): %s", dev["name"], device_id, exc)
            continue

        rows = []
        max_ts = start_ts
        for key, records in data.items():
            for rec in records:
                ts = rec["ts"]
                raw = _parse_value(rec.get("value"))
                cal_val = calibrate(raw, device_id, key) if raw is not None else None
                ts_dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
                rows.append((device_id, key, raw, cal_val, ts, ts_dt))
                if ts > max_ts:
                    max_ts = ts

        inserted = insert_history_batch(conn, rows)

        if max_ts > start_ts:
            set_last_sync_ts(conn, device_id, "history", max_ts)

        conn.commit()
        logger.info("History synced: %s — %d new rows (out of %d fetched)",
                    dev["name"], inserted, len(rows))


# ── Alarms ─────────────────────────────────────────────────────────────────

def sync_alarms(client: ThingsBoardClient, conn: sqlite3.Connection) -> None:
    """Fetch all alarms for every device."""
    for dev in DEVICES:
        device_id = dev["id"]
        try:
            alarms = client.get_all_alarms(device_id)
        except Exception as exc:
            logger.error("Failed alarms for %s (%s): %s", dev["name"], device_id, exc)
            continue

        if alarms:
            count = upsert_alarms(conn, device_id, alarms)
            conn.commit()
            logger.info("Alarms synced: %s — %d alarms", dev["name"], count)
        else:
            logger.info("No alarms for %s", dev["name"])
