"""
Rosette Jobs Routes - Phase 5 Consolidation

Job CRUD operations for rosette previews and presets.

Migrated from:
    - routers/art_studio_rosette_router.py (lines 206-299)

Endpoints:
    POST /preview  - Generate rosette geometry preview
    POST /save     - Save rosette job
    GET  /jobs     - List saved jobs
    GET  /presets  - List available presets
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# Import canonical geometry functions - NO inline math in routers (Fortran Rule)
from ...geometry.arc_utils import generate_circle_points

from ...art_studio_rosette_store import (
    get_job,
    init_db,
    list_jobs,
    list_presets,
    save_job,
)
from ...services.art_job_store import create_art_job

router = APIRouter(
    prefix="/api/art/rosette",
    tags=["art_studio_rosette_jobs"],
)


# ---- Pydantic models --------------------------------------------------------


class RosettePreviewIn(BaseModel):
    pattern_type: str = Field(..., description="e.g. 'herringbone', 'rope', 'simple_ring'")
    segments: int = Field(64, ge=8, le=720)
    inner_radius: float = Field(40.0, gt=0)
    outer_radius: float = Field(45.0, gt=0)
    units: str = Field("mm", pattern="^(mm|inch)$")
    preset: Optional[str] = Field(None, description="Optional preset name")
    name: Optional[str] = Field(None, description="Optional friendly job name for saving")

    @validator("outer_radius")
    def check_radii(cls, v, values):
        inner = values.get("inner_radius", None)
        if inner is not None and v <= inner:
            raise ValueError("outer_radius must be greater than inner_radius")
        return v


class RosettePath(BaseModel):
    points: List[Tuple[float, float]]  # [ [x,y], ... ]


class RosettePreviewOut(BaseModel):
    job_id: str
    pattern_type: str
    segments: int
    inner_radius: float
    outer_radius: float
    units: str
    preset: Optional[str]
    name: Optional[str]
    paths: List[RosettePath]
    bbox: Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)


class RosetteSaveIn(BaseModel):
    """Save a rosette job with full preview data"""
    preview: RosettePreviewOut
    name: Optional[str] = None
    preset: Optional[str] = None


class RosetteJobOut(BaseModel):
    job_id: str
    name: Optional[str]
    preset: Optional[str]
    created_at: str
    preview: RosettePreviewOut


class RosettePresetOut(BaseModel):
    name: str
    pattern_type: str
    segments: int
    inner_radius: float
    outer_radius: float
    metadata: Dict[str, Any]


# ---- Geometry helpers (Fortran Rule - delegates to geometry/arc_utils) ------


def _generate_simple_ring_paths(
    segments: int,
    inner_radius: float,
    outer_radius: float,
) -> List[List[Tuple[float, float]]]:
    """
    Generate two concentric circles as polygons.

    Delegates to canonical generate_circle_points() from geometry/arc_utils.py.
    """
    inner = generate_circle_points(inner_radius, segments, closed=True)
    outer = generate_circle_points(outer_radius, segments, closed=True)
    return [inner, outer]


def _generate_rosette_paths(body: RosettePreviewIn) -> List[List[Tuple[float, float]]]:
    """Stub rosette generator; later we can plug in the true Art Studio kernel.

    For now:
    - pattern_type 'simple_ring' or unknown => two concentric circles.
    - pattern_type 'herringbone' => same geometry, different metadata (future ready).
    - pattern_type 'rope' => same geometry, but you can tweak radii slightly if desired.
    """
    segments = body.segments
    inner_radius = body.inner_radius
    outer_radius = body.outer_radius

    # you can branch by pattern_type here later
    return _generate_simple_ring_paths(segments, inner_radius, outer_radius)


def _compute_bbox(paths: List[List[Tuple[float, float]]]) -> Tuple[float, float, float, float]:
    xs: List[float] = []
    ys: List[float] = []
    for path in paths:
        for (x, y) in path:
            xs.append(x)
            ys.append(y)
    if not xs:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


# ---- Startup ----------------------------------------------------------------

# Flag to track if DB is available (set during startup)
_db_available: bool = False


@router.on_event("startup")
def _on_startup() -> None:
    """Initialize SQLite database - fail gracefully in CI/Docker environments."""
    global _db_available
    try:
        init_db()
        _db_available = True
        logger.info("Rosette jobs SQLite database initialized successfully")
    except Exception as e:
        # In CI/Docker, the database may not be writable due to volume mount permissions
        # This is non-fatal - the health check and core APIs will still work
        _db_available = False
        logger.warning(
            f"Rosette jobs database unavailable (non-fatal in CI): {e}. "
            "Rosette job persistence will be disabled."
        )


# ---- Routes -----------------------------------------------------------------


@router.post("/preview", response_model=RosettePreviewOut)
def preview_rosette(body: RosettePreviewIn) -> RosettePreviewOut:
    """Generate a stub rosette geometry preview (paths + bbox)."""
    job_id = f"rosette_{uuid.uuid4().hex[:12]}"
    paths_xy = _generate_rosette_paths(body)
    bbox = _compute_bbox(paths_xy)
    paths = [RosettePath(points=p) for p in paths_xy]

    return RosettePreviewOut(
        job_id=job_id,
        pattern_type=body.pattern_type,
        segments=body.segments,
        inner_radius=body.inner_radius,
        outer_radius=body.outer_radius,
        units=body.units,
        preset=body.preset,
        name=body.name,
        paths=paths,
        bbox=bbox,
    )


@router.post("/save", response_model=RosetteJobOut)
def save_rosette_job(body: RosetteSaveIn) -> RosetteJobOut:
    """Persist a rosette preview payload to the database."""
    global _db_available
    if not _db_available:
        # Best-effort on-demand initialization for test environments
        try:
            init_db()
            _db_available = True
            logger.info("On-demand DB init succeeded for /save endpoint")
        except Exception as e:
            logger.warning(f"On-demand DB init failed for /save endpoint: {e}")
            raise HTTPException(
                status_code=503,
                detail="Rosette job persistence unavailable (database not initialized)"
            )
    preview = body.preview

    # Override name/preset if provided in save request
    if body.name:
        preview.name = body.name
    if body.preset:
        preview.preset = body.preset

    save_job(
        job_id=preview.job_id,
        name=preview.name or preview.job_id,
        preset=preview.preset,
        payload=preview.dict(),
    )

    # Verify it was saved
    stored = get_job(preview.job_id)
    if not stored:
        raise HTTPException(status_code=500, detail="Failed to save rosette job")

    # Register job within the Art Studio job spine for global timelines
    try:
        create_art_job("rosette", stored, job_id=stored["job_id"])
    except Exception:
        # Non-fatal: job timelines will simply omit this entry if persistence fails
        pass

    return RosetteJobOut(
        job_id=stored["job_id"],
        name=stored["name"],
        preset=stored["preset"],
        created_at=stored["created_at"],
        preview=preview,
    )


@router.get("/jobs", response_model=List[RosetteJobOut])
def list_rosette_jobs(limit: int = 20) -> List[RosetteJobOut]:
    if not _db_available:
        # Return empty list when DB unavailable (graceful degradation)
        return []
    jobs = list_jobs(limit=limit)
    out: List[RosetteJobOut] = []
    for j in jobs:
        preview = RosettePreviewOut(**j["payload"])
        out.append(
            RosetteJobOut(
                job_id=j["job_id"],
                name=j["name"],
                preset=j["preset"],
                created_at=j["created_at"],
                preview=preview,
            )
        )
    return out


@router.get("/presets", response_model=List[RosettePresetOut])
def get_rosette_presets() -> List[RosettePresetOut]:
    if not _db_available:
        # Return empty list when DB unavailable (graceful degradation)
        return []
    rows = list_presets()
    return [
        RosettePresetOut(
            name=r["name"],
            pattern_type=r["pattern_type"],
            segments=r["segments"],
            inner_radius=r["inner_radius"],
            outer_radius=r["outer_radius"],
            metadata=r["metadata"],
        )
        for r in rows
    ]
