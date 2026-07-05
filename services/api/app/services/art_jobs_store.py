# services/api/app/services/art_jobs_store.py

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from app.core.rmos_db import get_rmos_db
from app.stores.sqlite_art_jobs_store import SQLiteArtJobsStore

# Legacy JSON path - retained ONLY as a one-time migration source. Runtime
# reads/writes now go to SQLite (art_jobs table via SQLiteArtJobsStore) instead
# of parsing and rewriting the entire ~730KB file on every create/read.
# See PERFORMANCE_AUDIT_2026-07-04.md finding N1.
JOBS_PATH = Path("data/art_jobs.json")

_store: Optional[SQLiteArtJobsStore] = None
_store_for: Optional[str] = None
_migrated = False
_migrated_for: Optional[str] = None
_store_lock = RLock()
logger = logging.getLogger(__name__)

# Keys of the ArtJob dataclass that come straight from a stored row.
_ARTJOB_FIELDS = (
    "id", "job_type", "created_at", "post_preset",
    "rings", "z_passes", "length_mm", "gcode_lines", "meta",
)


@dataclass
class ArtJob:
    """Simple art job record (rosette CAM, etc.)."""
    id: str
    job_type: str
    created_at: Any
    post_preset: Optional[str] = None
    rings: Optional[int] = None
    z_passes: Optional[int] = None
    length_mm: Optional[float] = None
    gcode_lines: Optional[int] = None
    meta: Dict[str, Any] = field(default_factory=dict)


def _db_identity(db: Any) -> str:
    return str(getattr(db, "db_path", None) or getattr(db, "_pg_url", None) or id(db))


def _execute(db: Any, cursor: Any, query: str, params: tuple = ()) -> None:
    if getattr(db, "backend_type", "") == "postgresql":
        query = query.replace("?", "%s")
    cursor.execute(query, params)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_created_at(value: Any) -> str:
    if value is None:
        return _utc_now_iso()
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return _utc_now_iso()
        try:
            return datetime.fromtimestamp(float(stripped), timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            return stripped
    logger.warning("Invalid legacy plural art job created_at %r; using current time", value)
    return _utc_now_iso()


def _coerce_meta(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    logger.warning("Non-dict plural art job meta %r stored under value wrapper", type(value).__name__)
    return {"value": value}


def _row_payload_from_legacy(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("id"),
        "job_type": row.get("job_type"),
        "post_preset": row.get("post_preset"),
        "rings": row.get("rings"),
        "z_passes": row.get("z_passes"),
        "length_mm": row.get("length_mm"),
        "gcode_lines": row.get("gcode_lines"),
        "meta": _coerce_meta(row.get("meta")),
        "created_at": _coerce_created_at(row.get("created_at")),
        "updated_at": _utc_now_iso(),
    }


def _upsert_art_job_row(store: SQLiteArtJobsStore, row: Dict[str, Any]) -> Dict[str, Any]:
    db = store.db
    row_data = store._dict_to_row_data(row)
    fields = list(row_data.keys())
    placeholders = ",".join(["?"] * len(fields))
    updates = ",".join(f"{field} = excluded.{field}" for field in fields if field != store.id_field)
    query = (
        f"INSERT INTO {store.table_name} ({','.join(fields)}) VALUES ({placeholders}) "
        f"ON CONFLICT({store.id_field}) DO UPDATE SET {updates}"
    )
    with db.get_connection() as conn:
        cursor = conn.cursor()
        _execute(db, cursor, query, tuple(row_data.values()))
    return row


def _get_store() -> SQLiteArtJobsStore:
    global _store, _store_for, _migrated
    db = get_rmos_db()
    identity = _db_identity(db)
    with _store_lock:
        if _store is None or _store_for != identity:
            _store = SQLiteArtJobsStore(db)
            _store_for = identity
            _migrated = False
        _migrate_from_json(_store, identity)
        return _store


def _insert_legacy_row(
    row: Any,
    seen_ids: set,
    store: SQLiteArtJobsStore,
    db: Any,
    cursor: Any,
) -> tuple:
    """Validate and insert a single legacy row. Returns (imported, skipped, duplicates) deltas."""
    if not isinstance(row, dict) or "job_type" not in row:
        return 0, 1, 0  # singular-shaped rows owned by art_job_store — skip silently
    row_id = row.get("id")
    if not row_id:
        logger.warning("Skipping legacy plural art job row without id")
        return 0, 1, 0
    if row_id in seen_ids:
        logger.warning("Skipping duplicate legacy plural art job id %r", row_id)
        return 0, 0, 1
    seen_ids.add(row_id)
    row_data = store._dict_to_row_data(_row_payload_from_legacy(row))
    fields = list(row_data.keys())
    placeholders = ",".join(["?"] * len(fields))
    _execute(
        db,
        cursor,
        f"INSERT INTO {store.table_name} ({','.join(fields)}) VALUES ({placeholders}) "
        f"ON CONFLICT({store.id_field}) DO NOTHING",
        tuple(row_data.values()),
    )
    return 1, 0, 0


def _migrate_from_json(store: SQLiteArtJobsStore, identity: Optional[str] = None) -> None:
    """One-time import of legacy plural-shaped rows (id/job_type/...) if the table is empty.

    Note: the historical data/art_jobs.json holds singular (lane/payload) rows
    owned by art_job_store; those are skipped here. Plural-shaped rows, if any,
    are imported with their legacy created_at preserved when present.
    """
    global _migrated, _migrated_for
    identity = identity or _db_identity(store.db)
    if _migrated and _migrated_for == identity:
        return
    try:
        if store.count() > 0 or not JOBS_PATH.exists():
            _migrated = True
            _migrated_for = identity
            return
        rows = json.loads(JOBS_PATH.read_text(encoding="utf-8") or "[]")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("Skipping legacy plural art job migration from %s: %s", JOBS_PATH, exc)
        return
    if not isinstance(rows, list):
        logger.warning("Skipping legacy plural art job migration: expected list in %s", JOBS_PATH)
        return
    imported = skipped = duplicates = 0
    seen_ids: set[str] = set()
    db = store.db
    with db.get_connection() as conn:
        cursor = conn.cursor()
        for r in rows:
            delta_imported, delta_skipped, delta_duplicates = _insert_legacy_row(r, seen_ids, store, db, cursor)
            imported += delta_imported
            skipped += delta_skipped
            duplicates += delta_duplicates
    _migrated = True
    _migrated_for = identity
    if imported or skipped or duplicates:
        logger.info(
            "Legacy plural art job migration complete: imported=%s skipped=%s duplicates=%s",
            imported,
            skipped,
            duplicates,
        )


def _to_artjob(row: Dict[str, Any]) -> ArtJob:
    return ArtJob(**{k: row.get(k) for k in _ARTJOB_FIELDS if k in row})


def create_art_job(
    job_id: str,
    job_type: str,
    post_preset: Optional[str] = None,
    rings: Optional[int] = None,
    z_passes: Optional[int] = None,
    length_mm: Optional[float] = None,
    gcode_lines: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> ArtJob:
    """Create and store a new art job."""
    store = _get_store()
    now = _utc_now_iso()
    row = _upsert_art_job_row(
        store,
        {
            "id": job_id,
            "job_type": job_type,
            "post_preset": post_preset,
            "rings": rings,
            "z_passes": z_passes,
            "length_mm": length_mm,
            "gcode_lines": gcode_lines,
            "meta": meta or {},
            "created_at": now,
            "updated_at": now,
        },
    )
    return _to_artjob(row)


def get_art_job(job_id: str) -> Optional[ArtJob]:
    """Retrieve an art job by ID."""
    row = _get_store().get_by_id(job_id)
    if not row:
        return None
    return _to_artjob(row)


def _load_jobs() -> List[Dict[str, Any]]:
    """Return all art jobs as raw dicts (plural shape)."""
    return _get_store().get_all()


def _reset_for_tests() -> None:
    global _store, _store_for, _migrated, _migrated_for
    with _store_lock:
        _store = None
        _store_for = None
        _migrated = False
        _migrated_for = None
