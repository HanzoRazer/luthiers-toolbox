from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

JOBS_PATH = Path("data/art_jobs.json")


@dataclass
class ArtJob:
    id: str
    lane: str
    created_at: float
    payload: Dict[str, Any]


def _load() -> List[Dict[str, Any]]:
    if not JOBS_PATH.exists():
        return []
    try:
        raw = JOBS_PATH.read_text(encoding="utf-8")
        if not raw.strip():
            return []
        return json.loads(raw)
    except Exception:
        return []


def _save(rows: List[Dict[str, Any]]) -> None:
    JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOBS_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def create_art_job(lane: str, payload: Dict[str, Any], job_id: str | None = None) -> ArtJob:
    rows = _load()
    jid = job_id or f"{lane}_job_{int(time.time()*1000)}"
    job = ArtJob(id=jid, lane=lane, created_at=time.time(), payload=payload)
    rows.append(asdict(job))
    _save(rows)
    return job


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    rows = _load()
    for row in rows:
        if row.get("id") == job_id:
            return row
    return None
