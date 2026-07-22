"""SQLite database schema and operations for the Neutramol BI pipeline."""

import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS devices (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    client      TEXT NOT NULL,
    active      INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS telemetry_keys (
    device_id   TEXT NOT NULL,
    key         TEXT NOT NULL,
    label       TEXT,
    cal_x0      REAL,
    cal_x1      REAL,
    cal_y0      REAL,
    cal_y1      REAL,
    PRIMARY KEY (device_id, key)
);

-- Latest value per device+key (upserted on every fetch)
CREATE TABLE IF NOT EXISTS telemetry_latest (
    device_id         TEXT NOT NULL,
    key               TEXT NOT NULL,
    raw_value         REAL,
    calibrated_value  REAL,
    ts                INTEGER,
    ts_dt             TEXT,
    fetched_at        TEXT,
    PRIMARY KEY (device_id, key)
);

-- Full historical series (append-only, deduplicated by device+key+ts)
CREATE TABLE IF NOT EXISTS telemetry_history (
    device_id         TEXT    NOT NULL,
    key               TEXT    NOT NULL,
    raw_value         REAL,
    calibrated_value  REAL,
    ts                INTEGER NOT NULL,
    ts_dt             TEXT,
    PRIMARY KEY (device_id, key, ts)
);

-- Alarms
CREATE TABLE IF NOT EXISTS alarms (
    id            TEXT PRIMARY KEY,
    device_id     TEXT,
    alarm_type    TEXT,
    severity      TEXT,
    status        TEXT,
    created_time  INTEGER,
    created_dt    TEXT,
    end_time      INTEGER,
    end_dt        TEXT,
    details       TEXT,
    synced_at     TEXT
);

-- Track last successful sync per device to enable incremental updates
CREATE TABLE IF NOT EXISTS sync_state (
    device_id   TEXT    NOT NULL,
    sync_type   TEXT    NOT NULL,   -- 'history' | 'latest' | 'alarms'
    last_ts     INTEGER,            -- last timestamp successfully synced
    synced_at   TEXT,
    PRIMARY KEY (device_id, sync_type)
);

-- Indexes for BI queries
CREATE INDEX IF NOT EXISTS idx_history_device_key_ts
    ON telemetry_history (device_id, key, ts DESC);

CREATE INDEX IF NOT EXISTS idx_alarms_device
    ON alarms (device_id, created_time DESC);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(DDL)
    conn.commit()
    logger.info("Database ready: %s", db_path)
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts_to_iso(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()


# ── Devices & Keys ─────────────────────────────────────────────────────────

def upsert_devices(conn: sqlite3.Connection, devices: list[dict]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO devices (id, name, client) VALUES (?, ?, ?)",
        [(d["id"], d["name"], d["client"]) for d in devices],
    )
    conn.commit()


def upsert_telemetry_keys(
    conn: sqlite3.Connection,
    device_id: str,
    key: str,
    label: str | None = None,
    cal: tuple | None = None,
) -> None:
    x0, x1, y0, y1 = cal if cal else (None, None, None, None)
    conn.execute(
        """INSERT OR REPLACE INTO telemetry_keys
           (device_id, key, label, cal_x0, cal_x1, cal_y0, cal_y1)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (device_id, key, label, x0, x1, y0, y1),
    )


# ── Telemetry ──────────────────────────────────────────────────────────────

def upsert_latest(
    conn: sqlite3.Connection,
    device_id: str,
    key: str,
    raw_value: float | None,
    calibrated_value: float | None,
    ts: int,
) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO telemetry_latest
           (device_id, key, raw_value, calibrated_value, ts, ts_dt, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (device_id, key, raw_value, calibrated_value, ts, _ts_to_iso(ts), _now_iso()),
    )


def insert_history_batch(
    conn: sqlite3.Connection,
    rows: list[tuple],  # (device_id, key, raw, calibrated, ts, ts_dt)
) -> int:
    """Insert rows, ignoring duplicates. Returns number of rows inserted."""
    cur = conn.executemany(
        """INSERT OR IGNORE INTO telemetry_history
           (device_id, key, raw_value, calibrated_value, ts, ts_dt)
           VALUES (?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return cur.rowcount


# ── Alarms ─────────────────────────────────────────────────────────────────

def upsert_alarms(conn: sqlite3.Connection, device_id: str, alarms: list[dict]) -> int:
    rows = []
    for a in alarms:
        alarm_id = a.get("id", {}).get("id") or a.get("id")
        created = a.get("createdTime")
        end = a.get("endTs")
        rows.append((
            alarm_id,
            device_id,
            a.get("type"),
            a.get("severity"),
            a.get("status"),
            created,
            _ts_to_iso(created) if created else None,
            end,
            _ts_to_iso(end) if end else None,
            str(a.get("details") or ""),
            _now_iso(),
        ))
    cur = conn.executemany(
        """INSERT OR REPLACE INTO alarms
           (id, device_id, alarm_type, severity, status,
            created_time, created_dt, end_time, end_dt, details, synced_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return cur.rowcount


# ── Sync state ─────────────────────────────────────────────────────────────

def get_last_sync_ts(conn: sqlite3.Connection, device_id: str, sync_type: str) -> int | None:
    row = conn.execute(
        "SELECT last_ts FROM sync_state WHERE device_id=? AND sync_type=?",
        (device_id, sync_type),
    ).fetchone()
    return row["last_ts"] if row else None


def set_last_sync_ts(
    conn: sqlite3.Connection, device_id: str, sync_type: str, last_ts: int
) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO sync_state (device_id, sync_type, last_ts, synced_at)
           VALUES (?, ?, ?, ?)""",
        (device_id, sync_type, last_ts, _now_iso()),
    )
