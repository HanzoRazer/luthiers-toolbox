"""
Phase 27.0 + 27.1 + 27.2: Rosette Compare Mode MVP
Router endpoints for baseline management, geometry diffing, and compare history
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..models.compare_baseline import (
    CompareBaselineIn,
    CompareBaselineOut,
    CompareBaselineSummary,
    CompareDiffRequest,
    CompareDiffOut,
)
from ..services.baseline_storage import (
    save_baseline,
    list_baselines,
    load_baseline,
)
from ..services.geometry_diff import annotate_geometries_with_colors
from ..services.compare_risk_log import log_compare_diff, list_compare_history

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.post("/baselines", response_model=CompareBaselineOut)
def create_baseline(payload: CompareBaselineIn) -> CompareBaselineOut:
    """Save a new baseline geometry snapshot.
    
    Phase 27.0: Manual baseline naming for rosette, headstock, or relief.
    """
    baseline_id = str(uuid.uuid4())
    baseline = CompareBaselineOut(
        id=baseline_id,
        name=payload.name,
        lane=payload.lane,
        created_at=datetime.utcnow(),
        geometry=payload.geometry,
    )
    save_baseline(baseline)
    return baseline


@router.get("/baselines", response_model=List[CompareBaselineSummary])
def get_baselines(lane: str | None = None) -> List[CompareBaselineSummary]:
    """List all saved baselines, optionally filtered by lane.
    
    Phase 27.0: Supports rosette, headstock, relief lanes.
    """
    return list_baselines(lane=lane)


@router.get("/baselines/{baseline_id}", response_model=CompareBaselineOut)
def get_baseline(baseline_id: str) -> CompareBaselineOut:
    """Retrieve a single baseline by ID with full geometry.
    
    Phase 27.0: Returns complete baseline for diff computation.
    """
    baseline = load_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return baseline


@router.post("/diff", response_model=CompareDiffOut)
def compare_geometry(payload: CompareDiffRequest) -> CompareDiffOut:
    """Compare current geometry against a saved baseline.
    
    Phase 27.0: Basic path-count diff.
    Phase 27.1: Color-annotated geometry (green=added, red=removed, gray=unchanged).
    Phase 27.1: Optional job_id logging to compare_risk_log.json.
    """
    baseline = load_baseline(payload.baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    # Phase 27.1: Annotate geometries with color metadata
    stats, base_colored, curr_colored = annotate_geometries_with_colors(
        baseline.geometry, payload.current_geometry
    )

    # Phase 27.1: Log to risk/job snapshots if job_id provided
    if payload.job_id:
        log_compare_diff(
            job_id=payload.job_id,
            lane=payload.lane,
            baseline_id=payload.baseline_id,
            stats=stats,
            preset=payload.preset,
        )

    return CompareDiffOut(
        baseline_id=payload.baseline_id,
        lane=payload.lane,
        stats=stats,
        baseline_geometry=base_colored,
        current_geometry=curr_colored,
    )


@router.get("/history")
def get_compare_history(
    lane: str | None = None,
    job_id: str | None = None,
) -> List[Dict[str, Any]]:
    """Return compare history entries from compare_risk_log.json.
    
    Phase 27.2: Compare History pane for tracking geometry changes over time.
    
    Optional filters:
      - lane: e.g. 'rosette', 'headstock', 'relief'
      - job_id: exact job id string, e.g. 'rosette_job_001'
    """
    return list_compare_history(lane=lane, job_id=job_id)
