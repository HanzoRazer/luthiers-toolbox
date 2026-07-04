# services/api/app/services/art_jobs_store.py

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.stores.sqlite_art_jobs_store import SQLiteArtJobsStore

# Legacy JSON path — retained ONLY as a one-time migration source. Runtime
# reads/writes now go to SQLite (art_jobs table via SQLiteArtJobsStore) instead
# of parsing and rewriting the entire ~730KB file on every create/read.
# See PERFORMANCE_AUDIT_2026-07-04.md finding N1.
JOBS_PATH = Path("data/art_jobs.json")

_store: Optional[SQLiteArtJobsStore] = None
_migrated = False

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
    created_at: float
    post_preset: Optional[str] = None
    rings: Optional[int] = None
    z_passes: Optional[int] = None
    length_mm: Optional[float] = None
    gcode_lines: Optional[int] = None
    meta: Dict[str, Any] = field(default_factory=dict)


def _get_store() -> SQLiteArtJobsStore:
    global _store
    if _store is None:
        _store = SQLiteArtJobsStore()
        _migrate_from_json(_store)
    return _store


def _migrate_from_json(store: SQLiteArtJobsStore) -> None:
    """One-time import of legacy plural-shaped rows (id/job_type/...) if the table is empty.

    Note: the historical data/art_jobs.json holds singular (lane/payload) rows
    owned by art_job_store; those are skipped here. Plural-shaped rows, if any,
    are imported (created_at becomes migration time, since none exist in practice).
    """
    global _migrated
    if _migrated:
        return
    _migrated = True
    try:
        if store.count() > 0 or not JOBS_PATH.exists():
            return
        rows = json.loads(JOBS_PATH.read_text(encoding="utf-8") or "[]")
    except (OSError, json.JSONDecodeError, ValueError):
        return
    if not isinstance(rows, list):
        return
    for r in rows:
        if not isinstance(r, dict) or "job_type" not in r:
            continue  # skip singular-shaped rows (owned by art_job_store)
        store.create_art_job(
            job_id=r.get("id"),
            job_type=r.get("job_type"),
            post_preset=r.get("post_preset"),
            rings=r.get("rings"),
            z_passes=r.get("z_passes"),
            length_mm=r.get("length_mm"),
            gcode_lines=r.get("gcode_lines"),
            meta=r.get("meta") or {},
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
    row = _get_store().create_art_job(
        job_id=job_id,
        job_type=job_type,
        post_preset=post_preset,
        rings=rings,
        z_passes=z_passes,
        length_mm=length_mm,
        gcode_lines=gcode_lines,
        meta=meta or {},
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
