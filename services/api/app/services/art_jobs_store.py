# services/api/app/services/art_jobs_store.py

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


JOBS_PATH = Path("data/art_jobs.json")


@dataclass
class ArtJob:
    """Simple file-based art job storage."""
    id: str
    job_type: str  # "rosette_cam", etc.
    created_at: float
    
    # Rosette CAM specific
    post_preset: Optional[str] = None
    rings: Optional[int] = None
    z_passes: Optional[int] = None
    length_mm: Optional[float] = None
    gcode_lines: Optional[int] = None
    
    # Generic metadata
    meta: Dict[str, Any] = field(default_factory=dict)


def _load_jobs() -> List[Dict[str, Any]]:
    """Load jobs from JSON file."""
    if not JOBS_PATH.exists():
        JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
        return []
    try:
        with open(JOBS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_jobs(jobs: List[Dict[str, Any]]) -> None:
    """Save jobs to JSON file."""
    JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)


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
    job = ArtJob(
        id=job_id,
        job_type=job_type,
        created_at=time.time(),
        post_preset=post_preset,
        rings=rings,
        z_passes=z_passes,
        length_mm=length_mm,
        gcode_lines=gcode_lines,
        meta=meta or {}
    )
    
    jobs = _load_jobs()
    jobs.append(asdict(job))
    _save_jobs(jobs)
    
    return job


def get_art_job(job_id: str) -> Optional[ArtJob]:
    """Retrieve an art job by ID."""
    jobs = _load_jobs()
    for job_dict in jobs:
        if job_dict.get("id") == job_id:
            return ArtJob(**job_dict)
    return None
