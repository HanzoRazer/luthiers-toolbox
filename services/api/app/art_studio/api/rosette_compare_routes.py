"""
Rosette Compare Routes - Phase 5 Consolidation

Comparison, risk snapshots, and CSV export for rosette jobs.

Migrated from:
    - routers/art_studio_rosette_router.py (lines 304-590)

Endpoints:
    POST /compare           - Compare two saved rosette jobs
    POST /compare/snapshot  - Save comparison snapshot to risk timeline
    GET  /compare/snapshots - List comparison snapshots
    GET  /compare/export_csv - Export comparison history as CSV
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...art_studio_rosette_store import (
    get_compare_snapshots,
    get_job,
    save_compare_snapshot,
)
from ...services import compare_risk_log  # Phase 28.1: Sync to legacy log

router = APIRouter(
    prefix="/api/art/rosette",
    tags=["art_studio_rosette_compare"],
)


# ---- Pydantic models --------------------------------------------------------


class RosettePath(BaseModel):
    points: List[Tuple[float, float]]


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
    bbox: Tuple[float, float, float, float]


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


# ---- Helpers ----------------------------------------------------------------


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
    except (OSError, ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
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

    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")
