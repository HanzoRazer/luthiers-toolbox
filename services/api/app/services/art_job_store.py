from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.rmos_db import get_rmos_db

# Legacy JSON path — retained ONLY as a one-time migration source. Runtime
# reads/writes now go to SQLite (art_studio_jobs table) instead of parsing and
# rewriting the entire ~730KB file on every create/read.
# See PERFORMANCE_AUDIT_2026-07-04.md finding N1.
JOBS_PATH = Path("data/art_jobs.json")

_TABLE = "art_studio_jobs"
_initialized = False


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
        return 0.0


def _row_to_job_dict(row: Any) -> Dict[str, Any]:
    raw = row["payload_json"]
    try:
        payload = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        payload = {}
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
    except (OSError, json.JSONDecodeError, ValueError):
        return
    if not isinstance(rows, list):
        return
    for r in rows:
        if not isinstance(r, dict) or "lane" not in r or "payload" not in r:
            continue  # skip plural-shaped rows (owned by art_jobs_store)
        payload = r.get("payload")
        if not isinstance(payload, str):
            payload = json.dumps(payload, default=str)
        db.execute_update(
            f"INSERT INTO {_TABLE} (id, lane, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (r.get("id"), r.get("lane"), payload, _coerce_float(r.get("created_at"))),
        )


def _init() -> None:
    """Ensure the table exists and, once, import legacy JSON rows."""
    global _initialized
    if _initialized:
        return
    db = get_rmos_db()
    db.execute_update(
        f"CREATE TABLE IF NOT EXISTS {_TABLE} "
        "(id TEXT PRIMARY KEY, lane TEXT, payload_json TEXT, created_at REAL)"
    )
    if _scalar(db.execute_query(f"SELECT COUNT(*) AS n FROM {_TABLE}")) == 0 and JOBS_PATH.exists():
        _migrate_from_json(db)
    _initialized = True


def _load() -> List[Dict[str, Any]]:
    _init()
    db = get_rmos_db()
    rows = db.execute_query(
        f"SELECT id, lane, payload_json, created_at FROM {_TABLE}"
    )
    return [_row_to_job_dict(r) for r in rows]


def create_art_job(lane: str, payload: Dict[str, Any], job_id: str | None = None) -> ArtJob:
    _init()
    jid = job_id or f"{lane}_job_{int(time.time() * 1000)}"
    created_at = time.time()
    payload_json = payload if isinstance(payload, str) else json.dumps(payload, default=str)
    db = get_rmos_db()
    # Upsert (delete-then-insert) so re-registering an existing job_id is safe;
    # the legacy JSON store silently appended duplicates, latest-effective wins.
    db.execute_update(f"DELETE FROM {_TABLE} WHERE id = ?", (jid,))
    db.execute_update(
        f"INSERT INTO {_TABLE} (id, lane, payload_json, created_at) VALUES (?, ?, ?, ?)",
        (jid, lane, payload_json, created_at),
    )
    return ArtJob(id=jid, lane=lane, created_at=created_at, payload=payload)


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
