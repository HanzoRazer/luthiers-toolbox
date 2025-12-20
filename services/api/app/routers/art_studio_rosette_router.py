
"""
Art Studio Rosette Router

Note: Circle generation math extracted to geometry/arc_utils.py
following the Fortran Rule (all math in subroutines).
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
import io

# Import canonical geometry functions - NO inline math in routers (Fortran Rule)
from ..geometry.arc_utils import generate_circle_points

from ..art_studio_rosette_store import (
    get_compare_snapshots,
    get_job,
    init_db,
    list_jobs,
    list_presets,
    save_compare_snapshot,
    save_job,
)
from ..services.art_job_store import create_art_job
from ..services import compare_risk_log  # Phase 28.1: Sync to legacy log

router = APIRouter()

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


# ---- Compare Mode models ----------------------------------------------------


class RosetteCompareIn(BaseModel):
    job_id_a: str = Field(..., description="Baseline job id (A)")
    job_id_b: str = Field(..., description="Variant job id (B)")


class RosetteDiffSummary(BaseModel):
    job_id_a: str
    job_id_b: str

    pattern_type_a: str
    pattern_type_b: str
    pattern_type_same: bool

    segments_a: int
    segments_b: int
    segments_delta: int

    inner_radius_a: float
    inner_radius_b: float
    inner_radius_delta: float

    outer_radius_a: float
    outer_radius_b: float
    outer_radius_delta: float

    units_a: str
    units_b: str
    units_same: bool

    bbox_union: Tuple[float, float, float, float]
    bbox_a: Tuple[float, float, float, float]
    bbox_b: Tuple[float, float, float, float]


class RosetteCompareOut(BaseModel):
    job_a: RosettePreviewOut
    job_b: RosettePreviewOut
    diff_summary: RosetteDiffSummary


# ---- Geometry stub - Delegates to geometry/arc_utils.py (Fortran Rule) ------


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


def _union_bbox(
    bbox_a: Tuple[float, float, float, float],
    bbox_b: Tuple[float, float, float, float],
) -> Tuple[float, float, float, float]:
    min_x = min(bbox_a[0], bbox_b[0])
    min_y = min(bbox_a[1], bbox_b[1])
    max_x = max(bbox_a[2], bbox_b[2])
    max_y = max(bbox_a[3], bbox_b[3])
    return (min_x, min_y, max_x, max_y)


# ---- Routes -----------------------------------------------------------------


@router.on_event("startup")
def _on_startup() -> None:
    # ensure DB tables & default presets exist
    init_db()


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


# ---- Compare Route ----------------------------------------------------------


@router.post("/compare", response_model=RosetteCompareOut)
def compare_rosette_jobs(body: RosetteCompareIn) -> RosetteCompareOut:
    """Compare two saved rosette jobs (A vs B) and return both previews + a diff summary."""
    stored_a = get_job(body.job_id_a)
    if not stored_a:
        raise HTTPException(status_code=404, detail=f"Unknown rosette job_id A '{body.job_id_a}'")

    stored_b = get_job(body.job_id_b)
    if not stored_b:
        raise HTTPException(status_code=404, detail=f"Unknown rosette job_id B '{body.job_id_b}'")

    preview_a = RosettePreviewOut(**stored_a["payload"])
    preview_b = RosettePreviewOut(**stored_b["payload"])

    bbox_union = _union_bbox(preview_a.bbox, preview_b.bbox)

    diff = RosetteDiffSummary(
        job_id_a=preview_a.job_id,
        job_id_b=preview_b.job_id,
        pattern_type_a=preview_a.pattern_type,
        pattern_type_b=preview_b.pattern_type,
        pattern_type_same=(preview_a.pattern_type == preview_b.pattern_type),
        segments_a=preview_a.segments,
        segments_b=preview_b.segments,
        segments_delta=(preview_b.segments - preview_a.segments),
        inner_radius_a=preview_a.inner_radius,
        inner_radius_b=preview_b.inner_radius,
        inner_radius_delta=(preview_b.inner_radius - preview_a.inner_radius),
        outer_radius_a=preview_a.outer_radius,
        outer_radius_b=preview_b.outer_radius,
        outer_radius_delta=(preview_b.outer_radius - preview_a.outer_radius),
        units_a=preview_a.units,
        units_b=preview_b.units,
        units_same=(preview_a.units == preview_b.units),
        bbox_union=bbox_union,
        bbox_a=preview_a.bbox,
        bbox_b=preview_b.bbox,
    )

    return RosetteCompareOut(
        job_a=preview_a,
        job_b=preview_b,
        diff_summary=diff,
    )


# ---- Phase 27.2: Risk Snapshot Routes ---------------------------------------


class CompareSnapshotIn(BaseModel):
    """Request to save a comparison snapshot to risk timeline."""
    job_id_a: str
    job_id_b: str
    risk_score: float = Field(..., ge=0, le=100, description="Risk score 0-100")
    diff_summary: Dict[str, Any]
    lane: Optional[str] = Field(None, description="Optional lane (e.g., 'production')")
    note: Optional[str] = Field(None, description="Optional note about this comparison")


class CompareSnapshotOut(BaseModel):
    """Snapshot record from risk timeline."""
    id: int
    job_id_a: str
    job_id_b: str
    lane: str
    risk_score: float
    diff_summary: Dict[str, Any]
    note: Optional[str]
    created_at: str


@router.post("/compare/snapshot", response_model=CompareSnapshotOut)
def save_snapshot(body: CompareSnapshotIn) -> CompareSnapshotOut:
    """
    Save a comparison snapshot to the risk timeline.
    
    Risk score calculation (client-side):
    - Base score from segment delta: abs(delta) / max(seg_a, seg_b) * 50
    - Radius delta contribution: abs(inner_delta + outer_delta) / 10 * 50
    - Clamp to 0-100
    
    Phase 28.1: Also syncs to compare_risk_log for cross-lab dashboard integration.
    """
    snapshot_id = save_compare_snapshot(
        job_id_a=body.job_id_a,
        job_id_b=body.job_id_b,
        risk_score=body.risk_score,
        diff_summary=body.diff_summary,
        lane=body.lane,
        note=body.note,
    )
    
    # Phase 28.1: Sync to legacy compare_risk_log for dashboard aggregation
    try:
        diff = body.diff_summary
        # Extract preset info from diff if available
        preset_a = diff.get("preset_a") or "(none)"
        preset_b = diff.get("preset_b") or "(none)"
        preset_label = f"{preset_a} vs {preset_b}"
        
        # Calculate path deltas from segments
        segments_a = diff.get("segments_a", 0)
        segments_b = diff.get("segments_b", 0)
        segments_delta = diff.get("segments_delta", 0)
        
        # Estimate path changes (rosette typically has 2 paths: inner + outer rings)
        # If segments increased, consider it "added" paths complexity
        # If segments decreased, consider it "removed" paths complexity
        added_paths = max(0, segments_delta) / 10.0  # Scale to reasonable numbers
        removed_paths = max(0, -segments_delta) / 10.0
        
        compare_risk_log.log_compare_diff(
            job_id=body.job_id_a,  # Use baseline job as reference
            lane="rosette",
            baseline_id=body.job_id_b,
            stats=type('CompareDiffStats', (), {
                'baseline_path_count': 2,  # Rosette always has 2 main paths
                'current_path_count': 2,
                'added_paths': added_paths,
                'removed_paths': removed_paths,
                'unchanged_paths': 2.0 - added_paths - removed_paths,
            })(),
            preset=preset_label,
        )
    except Exception as e:
        # Don't fail snapshot save if log sync fails
        print(f"Warning: Failed to sync snapshot to compare_risk_log: {e}")
    
    # Retrieve and return the saved snapshot
    snapshots = get_compare_snapshots(
        job_id_a=body.job_id_a,
        job_id_b=body.job_id_b,
        limit=1,
    )
    
    if not snapshots:
        raise HTTPException(status_code=500, detail="Failed to retrieve saved snapshot")
    
    snapshot = snapshots[0]
    return CompareSnapshotOut(
        id=snapshot["id"],
        job_id_a=snapshot["job_id_a"],
        job_id_b=snapshot["job_id_b"],
        lane=snapshot["lane"],
        risk_score=snapshot["risk_score"],
        diff_summary=snapshot["diff_summary"],
        note=snapshot["note"],
        created_at=snapshot["created_at"],
    )


@router.get("/compare/snapshots", response_model=List[CompareSnapshotOut])
def list_snapshots(
    job_id_a: Optional[str] = None,
    job_id_b: Optional[str] = None,
    lane: Optional[str] = None,
    limit: int = 50,
) -> List[CompareSnapshotOut]:
    """
    Retrieve comparison snapshots from risk timeline with optional filtering.
    
    Query params:
    - job_id_a: Filter by first job ID
    - job_id_b: Filter by second job ID
    - lane: Filter by lane (e.g., 'production', 'testing')
    - limit: Max results (default 50)
    """
    snapshots = get_compare_snapshots(
        job_id_a=job_id_a,
        job_id_b=job_id_b,
        lane=lane,
        limit=limit,
    )
    
    return [
        CompareSnapshotOut(
            id=s["id"],
            job_id_a=s["job_id_a"],
            job_id_b=s["job_id_b"],
            lane=s["lane"],
            risk_score=s["risk_score"],
            diff_summary=s["diff_summary"],
            note=s["note"],
            created_at=s["created_at"],
        )
        for s in snapshots
    ]


# ============================================================================
# Phase 27.3: CSV Export Endpoint
# ============================================================================


@router.get("/compare/export_csv")
def export_compare_csv(
    job_id_a: Optional[str] = None,
    job_id_b: Optional[str] = None,
    lane: Optional[str] = None,
    limit: int = 100,
):
    """
    Export comparison snapshots as CSV.

    Query params:
    - job_id_a: Filter by baseline job ID
    - job_id_b: Filter by variant job ID
    - lane: Filter by lane (production, testing, etc.)
    - limit: Max records (default 100)

    Returns CSV with columns:
    - timestamp: ISO timestamp of snapshot creation
    - job_id_a: Baseline job ID
    - job_id_b: Variant job ID
    - lane: Lane/category
    - risk_score: Calculated risk score (0-100)
    - segments_delta: Difference in segment count
    - inner_radius_delta: Difference in inner radius
    - outer_radius_delta: Difference in outer radius
    - pattern_type_a: Pattern type of baseline
    - pattern_type_b: Pattern type of variant
    - note: Optional note
    """
    try:
        # Fetch snapshots with same filtering as GET endpoint
        snapshots = get_compare_snapshots(
            job_id_a=job_id_a,
            job_id_b=job_id_b,
            lane=lane,
            limit=limit,
        )

        # Generate CSV in memory
        output = io.StringIO()
        
        # Write header
        output.write(
            "timestamp,job_id_a,job_id_b,lane,risk_score,"
            "segments_delta,inner_radius_delta,outer_radius_delta,"
            "pattern_type_a,pattern_type_b,note\n"
        )

        # Write rows
        for s in snapshots:
            diff = s.get("diff_summary", {})
            
            # Extract values with safe defaults
            timestamp = s.get("created_at", "")
            job_a = s.get("job_id_a", "")
            job_b = s.get("job_id_b", "")
            lane_val = s.get("lane", "")
            risk = s.get("risk_score", 0.0)
            
            seg_delta = diff.get("segments_delta", 0)
            inner_delta = diff.get("inner_radius_delta", 0.0)
            outer_delta = diff.get("outer_radius_delta", 0.0)
            pattern_a = diff.get("pattern_type_a", "")
            pattern_b = diff.get("pattern_type_b", "")
            note = s.get("note", "") or ""
            
            # Escape note if it contains commas/quotes
            note_escaped = note.replace('"', '""')
            if "," in note or '"' in note:
                note_escaped = f'"{note_escaped}"'
            
            # Write CSV row
            output.write(
                f"{timestamp},{job_a},{job_b},{lane_val},{risk:.2f},"
                f"{seg_delta},{inner_delta:.4f},{outer_delta:.4f},"
                f"{pattern_a},{pattern_b},{note_escaped}\n"
            )

        # Return as streaming response
        csv_content = output.getvalue()
        output.close()

        return StreamingResponse(
            io.BytesIO(csv_content.encode("utf-8")),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=rosette_compare_history.csv"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")


# ============================================================================
# Art Studio Bundle 5: CAM Integration Endpoints
# ============================================================================

# Import CAM bridge and job store
from app.services.rosette_cam_bridge import (
    plan_rosette_toolpath,
    postprocess_toolpath_grbl,
    RosetteGeometry,
    CamParams,
)
from app.services.art_jobs_store import create_art_job, get_art_job


# ---- CAM Models -------------------------------------------------------------


class RosetteToolpathPlanRequest(BaseModel):
    """Request to generate toolpath for a rosette design."""
    center_x: float = Field(0.0, description="Center X coordinate")
    center_y: float = Field(0.0, description="Center Y coordinate")
    inner_radius: float = Field(..., gt=0, description="Inner radius (mm)")
    outer_radius: float = Field(..., gt=0, description="Outer radius (mm)")
    units: str = Field("mm", description="Units (mm or inch)")
    
    tool_d: float = Field(..., gt=0, description="Tool diameter (mm)")
    stepover: float = Field(0.45, ge=0.1, le=0.9, description="Stepover as fraction (0.1-0.9)")
    stepdown: float = Field(1.5, gt=0, description="Stepdown per pass (mm)")
    feed_xy: float = Field(1200, gt=0, description="XY feed rate (mm/min)")
    feed_z: float = Field(400, gt=0, description="Z plunge rate (mm/min)")
    safe_z: float = Field(5, gt=0, description="Safe retract Z (mm)")
    cut_depth: float = Field(3.0, gt=0, description="Total cut depth (mm)")
    circle_segments: int = Field(64, ge=16, le=256, description="Circle approximation segments")


class RosetteToolpathPlanResponse(BaseModel):
    """Response with planned toolpath moves and stats."""
    moves: List[Dict[str, Any]] = Field(..., description="Neutral toolpath moves")
    stats: Dict[str, Any] = Field(..., description="Toolpath statistics")


class RosettePostGcodeRequest(BaseModel):
    """Request to generate G-code from toolpath moves."""
    moves: List[Dict[str, Any]] = Field(..., description="Toolpath moves to convert")
    units: str = Field("mm", description="Units (mm or inch)")
    spindle_rpm: int = Field(18000, ge=0, description="Spindle RPM")


class RosettePostGcodeResponse(BaseModel):
    """Response with generated G-code and stats."""
    gcode: str = Field(..., description="Generated G-code text")
    stats: Dict[str, Any] = Field(..., description="G-code statistics")


class RosetteCamJobCreateRequest(BaseModel):
    """Request to create a CAM job for pipeline handoff."""
    job_id: str = Field(..., description="Unique job ID")
    post_preset: str = Field("grbl", description="Post-processor preset (grbl, mach4, etc.)")
    rings: int = Field(..., gt=0, description="Number of radial passes")
    z_passes: int = Field(..., gt=0, description="Number of Z passes")
    length_mm: float = Field(..., gt=0, description="Total toolpath length (mm)")
    gcode_lines: int = Field(..., gt=0, description="Number of G-code lines")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RosetteCamJobIdResponse(BaseModel):
    """Response with created job ID."""
    job_id: str
    message: str


class RosetteCamJobResponse(BaseModel):
    """Response with full job details."""
    id: str
    job_type: str
    created_at: str
    post_preset: str
    rings: int
    z_passes: int
    length_mm: float
    gcode_lines: int
    meta: Dict[str, Any]


# ---- CAM Endpoints ----------------------------------------------------------


@router.post("/cam/plan_toolpath", response_model=RosetteToolpathPlanResponse)
def plan_rosette_cam_toolpath(body: RosetteToolpathPlanRequest) -> RosetteToolpathPlanResponse:
    """
    Generate toolpath moves for a rosette design.
    
    Uses concentric ring strategy with:
    - Radial passes based on tool diameter + stepover
    - Z passes based on cut depth + stepdown
    
    Returns neutral move list (code, x, y, z, f) + stats.
    """
    try:
        geom = RosetteGeometry(
            center_x=body.center_x,
            center_y=body.center_y,
            inner_radius=body.inner_radius,
            outer_radius=body.outer_radius,
            units=body.units,
        )
        
        params = CamParams(
            tool_d=body.tool_d,
            stepover=body.stepover,
            stepdown=body.stepdown,
            feed_xy=body.feed_xy,
            feed_z=body.feed_z,
            safe_z=body.safe_z,
            cut_depth=body.cut_depth,
        )
        
        moves, stats = plan_rosette_toolpath(geom, params, circle_segments=body.circle_segments)
        
        return RosetteToolpathPlanResponse(moves=moves, stats=stats)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Toolpath planning failed: {str(e)}")


@router.post("/cam/post_gcode", response_model=RosettePostGcodeResponse)
def post_rosette_gcode(body: RosettePostGcodeRequest) -> RosettePostGcodeResponse:
    """
    Generate G-code from toolpath moves.
    
    Uses GRBL-compatible post-processor with:
    - Header: G21/G20, G90, G17, M3 spindle on
    - Body: G0/G1 moves with coordinates
    - Footer: M5 spindle off, safe retract, M30
    
    Returns G-code text + stats (lines, bytes).
    """
    try:
        gcode, stats = postprocess_toolpath_grbl(
            body.moves,
            units=body.units,
            spindle_rpm=body.spindle_rpm,
        )
        
        return RosettePostGcodeResponse(gcode=gcode, stats=stats)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"G-code post-processing failed: {str(e)}")


@router.post("/jobs/cam_job", response_model=RosetteCamJobIdResponse)
def create_rosette_cam_job(body: RosetteCamJobCreateRequest) -> RosetteCamJobIdResponse:
    """
    Create a CAM job for pipeline handoff.
    
    Stores job metadata for later retrieval by PipelineLab.
    Job ID should be unique across all jobs.
    
    Returns job_id + success message.
    """
    try:
        create_art_job(
            job_id=body.job_id,
            job_type="rosette_cam",
            post_preset=body.post_preset,
            rings=body.rings,
            z_passes=body.z_passes,
            length_mm=body.length_mm,
            gcode_lines=body.gcode_lines,
            meta=body.meta,
        )
        
        return RosetteCamJobIdResponse(
            job_id=body.job_id,
            message=f"CAM job '{body.job_id}' created successfully",
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Job creation failed: {str(e)}")


@router.get("/jobs/{job_id}", response_model=RosetteCamJobResponse)
def get_rosette_cam_job(job_id: str) -> RosetteCamJobResponse:
    """
    Retrieve a CAM job by ID.
    
    Used by PipelineLab to load job details for pipeline execution.
    
    Returns full job details including metadata.
    """
    try:
        job = get_art_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        
        return RosetteCamJobResponse(
            id=job.id,
            job_type=job.job_type,
            created_at=job.created_at,
            post_preset=job.post_preset,
            rings=job.rings,
            z_passes=job.z_passes,
            length_mm=job.length_mm,
            gcode_lines=job.gcode_lines,
            meta=job.meta,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job retrieval failed: {str(e)}")




