from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from ..core.rmos_db import get_rmos_db

# Legacy JSON path - retained ONLY as a one-time migration source. Runtime
# reads/writes now go to SQLite (art_studio_jobs table) instead of parsing and
# rewriting the entire ~730KB file on every create/read.
# See PERFORMANCE_AUDIT_2026-07-04.md finding N1.
JOBS_PATH = Path("data/art_jobs.json")

_TABLE = "art_studio_jobs"
_initialized = False
_initialized_for: Optional[str] = None
_init_lock = RLock()
logger = logging.getLogger(__name__)


@dataclass
class ArtJob:
    id: str
    lane: str
    created_at: float
    payload: Dict[str, Any]


def _scalar(rows: List[Any]) -> int:
    if not rows:
        return 0
    row = rows[0]
    try:
        return int(row["n"])
    except (TypeError, KeyError, IndexError):
        return int(row[0])


def _coerce_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.warning("Invalid legacy art job created_at %r; using current time", value)
        return time.time()


def _db_identity(db: Any) -> str:
    return str(getattr(db, "db_path", None) or getattr(db, "_pg_url", None) or id(db))


def _execute(db: Any, cursor: Any, query: str, params: tuple = ()) -> None:
    if getattr(db, "backend_type", "") == "postgresql":
        query = query.replace("?", "%s")
    cursor.execute(query, params)


def _payload_to_json(payload: Any) -> str:
    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("Non-JSON string art job payload stored as raw payload wrapper")
            return json.dumps({"_raw_payload": payload}, default=str)
        if isinstance(decoded, dict):
            return payload
        logger.warning("Non-object JSON art job payload stored under value wrapper")
        return json.dumps({"value": decoded}, default=str)
    if not isinstance(payload, dict):
        logger.warning("Non-dict art job payload %r stored under value wrapper", type(payload).__name__)
        return json.dumps({"value": payload}, default=str)
    return json.dumps(payload, default=str)


def _row_to_job_dict(row: Any) -> Dict[str, Any]:
    raw = row["payload_json"]
    try:
        payload = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        logger.warning("Invalid stored art job payload JSON for %r; preserving raw payload", row["id"])
        payload = {"_raw_payload_json": raw}
    if not isinstance(payload, dict):
        payload = {"value": payload}
    return {
        "id": row["id"],
        "lane": row["lane"],
        "created_at": row["created_at"],
        "payload": payload,
    }


def _migrate_from_json(db) -> None:
    """One-time import of legacy singular-shaped rows (id/lane/payload/created_at)."""
    try:
        rows = json.loads(JOBS_PATH.read_text(encoding="utf-8") or "[]")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("Skipping legacy art job migration from %s: %s", JOBS_PATH, exc)
        return
    if not isinstance(rows, list):
        logger.warning("Skipping legacy art job migration: expected list in %s", JOBS_PATH)
        return
    imported = skipped = duplicates = 0
    seen_ids: set[str] = set()
    with db.get_connection(row_factory=False) as conn:
        cursor = conn.cursor()
        for r in rows:
            if not isinstance(r, dict) or "lane" not in r or "payload" not in r:
                skipped += 1
                continue  # skip plural-shaped rows (owned by art_jobs_store)
            row_id = r.get("id")
            if not row_id:
                skipped += 1
                logger.warning("Skipping legacy art job row without id")
                continue
            if row_id in seen_ids:
                duplicates += 1
                logger.warning("Skipping duplicate legacy singular art job id %r", row_id)
                continue
            seen_ids.add(row_id)
            _execute(
                db,
                cursor,
                f"INSERT INTO {_TABLE} (id, lane, payload_json, created_at) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
                (row_id, r.get("lane"), _payload_to_json(r.get("payload")), _coerce_float(r.get("created_at"))),
            )
            imported += 1
    if imported or skipped or duplicates:
        logger.info(
            "Legacy singular art job migration complete: imported=%s skipped=%s duplicates=%s",
            imported,
            skipped,
            duplicates,
        )


def _init() -> None:
    """Ensure the table exists and, once, import legacy JSON rows."""
    global _initialized, _initialized_for
    db = get_rmos_db()
    db_identity = _db_identity(db)
    if _initialized and _initialized_for == db_identity:
        return
    with _init_lock:
        if _initialized and _initialized_for == db_identity:
            return
        db.execute_update(
            f"CREATE TABLE IF NOT EXISTS {_TABLE} "
            "(id TEXT PRIMARY KEY, lane TEXT, payload_json TEXT, created_at REAL)"
        )
        db.execute_update(
            f"CREATE INDEX IF NOT EXISTS idx_{_TABLE}_created_at ON {_TABLE}(created_at DESC)"
        )
        if _scalar(db.execute_query(f"SELECT COUNT(*) AS n FROM {_TABLE}")) == 0 and JOBS_PATH.exists():
            _migrate_from_json(db)
        _initialized = True
        _initialized_for = db_identity


def _load() -> List[Dict[str, Any]]:
    _init()
    db = get_rmos_db()
    rows = db.execute_query(
        f"SELECT id, lane, payload_json, created_at FROM {_TABLE} ORDER BY created_at DESC, id ASC"
    )
    return [_row_to_job_dict(r) for r in rows]


def create_art_job(lane: str, payload: Dict[str, Any], job_id: str | None = None) -> ArtJob:
    _init()
    jid = job_id or f"{lane}_job_{int(time.time() * 1000)}"
    created_at = time.time()
    payload_json = _payload_to_json(payload)
    stored_payload = _row_to_job_dict({
        "id": jid,
        "lane": lane,
        "payload_json": payload_json,
        "created_at": created_at,
    })["payload"]
    db = get_rmos_db()
    db.execute_update(
        f"INSERT INTO {_TABLE} (id, lane, payload_json, created_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET "
        "lane = excluded.lane, payload_json = excluded.payload_json, created_at = excluded.created_at",
        (jid, lane, payload_json, created_at),
    )
    return ArtJob(id=jid, lane=lane, created_at=created_at, payload=stored_payload)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    _init()
    db = get_rmos_db()
    rows = db.execute_query(
        f"SELECT id, lane, payload_json, created_at FROM {_TABLE} WHERE id = ?",
        (job_id,),
    )
    if not rows:
        return None
    return _row_to_job_dict(rows[0])


def _reset_for_tests() -> None:
    global _initialized, _initialized_for
    with _init_lock:
        _initialized = False
        _initialized_for = None
