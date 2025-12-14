# File: services/api/app/routers/job_intelligence_router.py
# NEW – Job Intelligence API endpoints for CAM pipeline run history

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from ..services.job_int_favorites import (
    DEFAULT_FAVORITES_PATH,
    get_job_favorite,
    load_job_favorites,
    update_job_favorite,
)
from ..services.job_int_log import (
    DEFAULT_LOG_PATH,
    find_job_log_by_run_id,
    load_all_job_logs,
)

router = APIRouter()


# ===== Response Models =====


class JobIntLogEntryOut(BaseModel):
    """Lightweight job log entry for listing."""
    
    run_id: str
    job_name: Optional[str] = None
    machine_id: Optional[str] = None
    post_id: Optional[str] = None
    gcode_key: Optional[str] = None
    use_helical: bool = False
    favorite: bool = False
    
    sim_time_s: Optional[float] = None
    sim_energy_j: Optional[float] = None
    sim_move_count: Optional[int] = None
    
    sim_issue_count: Optional[int] = None
    sim_max_dev_pct: Optional[float] = None
    
    created_at: str
    source: str = "pipeline_run"


class JobIntLogEntryDetail(BaseModel):
    """Detailed job log entry with full simulation data."""
    
    run_id: str
    job_name: Optional[str] = None
    machine_id: Optional[str] = None
    post_id: Optional[str] = None
    gcode_key: Optional[str] = None
    use_helical: bool = False
    favorite: bool = False
    
    sim_time_s: Optional[float] = None
    sim_energy_j: Optional[float] = None
    sim_move_count: Optional[int] = None
    
    sim_issue_count: Optional[int] = None
    sim_max_dev_pct: Optional[float] = None
    
    created_at: str
    source: str = "pipeline_run"
    
    # Full raw blobs for detailed analysis / cloning:
    sim_stats: Dict[str, Any] = {}
    sim_issues: Dict[str, Any] = {}


class JobIntLogListResponse(BaseModel):
    """Paginated list of job log entries."""
    
    total: int
    items: List[JobIntLogEntryOut]


class JobIntFavoriteUpdate(BaseModel):
    """Request to update favorite flag."""
    
    favorite: bool = True


# ===== Endpoints =====


@router.get("/log", response_model=JobIntLogListResponse)
def list_job_int_log(
    machine_id: Optional[str] = Query(default=None, description="Filter by machine ID"),
    post_id: Optional[str] = Query(default=None, description="Filter by post-processor ID"),
    helical_only: bool = Query(default=False, description="Show only helical jobs"),
    favorites_only: bool = Query(default=False, description="Show only favorited jobs"),
    limit: int = Query(default=50, ge=1, le=500, description="Max results per page"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
) -> JobIntLogListResponse:
    """
    List job intelligence log entries with filtering and pagination.
    
    Supports filtering by machine, post-processor, helical flag, and favorites.
    Returns lightweight summaries without full sim_stats/sim_issues blobs.
    """
    all_entries = load_all_job_logs(DEFAULT_LOG_PATH)
    
    # Load favorites once
    favorites_map = load_job_favorites(path=DEFAULT_FAVORITES_PATH)
    
    # Apply filters
    filtered: List[Dict[str, Any]] = []
    for rec in all_entries:
        if machine_id and rec.get("machine_id") != machine_id:
            continue
        if post_id and rec.get("post_id") != post_id:
            continue
        if helical_only and not rec.get("use_helical", False):
            continue
        
        run_id = rec.get("run_id")
        fav_rec = favorites_map.get(run_id) if run_id else None
        favorite_flag = bool(fav_rec.get("favorite", False)) if isinstance(fav_rec, dict) else False
        
        if favorites_only and not favorite_flag:
            continue
        
        # Attach favorite flag into the record so later code can reuse
        rec = dict(rec)
        rec["_favorite_flag"] = favorite_flag
        
        filtered.append(rec)
    
    total = len(filtered)
    
    # Sort newest-first by created_at if present
    filtered.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    
    sliced = filtered[offset : offset + limit]
    
    items: List[JobIntLogEntryOut] = []
    for rec in sliced:
        try:
            run_id = rec["run_id"]
            # Prefer precomputed favorite flag, fallback to map lookup
            favorite_flag = bool(
                rec.get("_favorite_flag")
                or (favorites_map.get(run_id) or {}).get("favorite", False)
            )
            
            item = JobIntLogEntryOut(
                run_id=run_id,
                job_name=rec.get("job_name"),
                machine_id=rec.get("machine_id"),
                post_id=rec.get("post_id"),
                gcode_key=rec.get("gcode_key"),
                use_helical=bool(rec.get("use_helical", False)),
                favorite=favorite_flag,
                sim_time_s=rec.get("sim_time_s"),
                sim_energy_j=rec.get("sim_energy_j"),
                sim_move_count=rec.get("sim_move_count"),
                sim_issue_count=rec.get("sim_issue_count"),
                sim_max_dev_pct=rec.get("sim_max_dev_pct"),
                created_at=rec.get("created_at", ""),
                source=rec.get("source", "pipeline_run"),
            )
        except Exception:  # noqa: BLE001
            continue
        items.append(item)
    
    return JobIntLogListResponse(total=total, items=items)


@router.get("/log/{run_id}", response_model=JobIntLogEntryDetail)
def get_job_int_log_entry(
    run_id: str = Path(..., description="Pipeline run ID to retrieve"),
) -> JobIntLogEntryDetail:
    """
    Get detailed job log entry by run_id.
    
    Includes full sim_stats and sim_issues blobs for analysis or cloning.
    """
    rec = find_job_log_by_run_id(run_id, path=DEFAULT_LOG_PATH)
    
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"JobInt entry not found for run_id={run_id!r}",
        )
    
    favorite_flag = get_job_favorite(run_id, path=DEFAULT_FAVORITES_PATH)
    
    return JobIntLogEntryDetail(
        run_id=rec["run_id"],
        job_name=rec.get("job_name"),
        machine_id=rec.get("machine_id"),
        post_id=rec.get("post_id"),
        gcode_key=rec.get("gcode_key"),
        use_helical=bool(rec.get("use_helical", False)),
        favorite=favorite_flag,
        sim_time_s=rec.get("sim_time_s"),
        sim_energy_j=rec.get("sim_energy_j"),
        sim_move_count=rec.get("sim_move_count"),
        sim_issue_count=rec.get("sim_issue_count"),
        sim_max_dev_pct=rec.get("sim_max_dev_pct"),
        created_at=rec.get("created_at", ""),
        source=rec.get("source", "pipeline_run"),
        sim_stats=rec.get("sim_stats") or {},
        sim_issues=rec.get("sim_issues") or {},
    )


@router.post("/favorites/{run_id}", response_model=JobIntLogEntryDetail)
def set_job_favorite(
    run_id: str = Path(..., description="Pipeline run ID to mark favorite"),
    body: JobIntFavoriteUpdate = ...,
) -> JobIntLogEntryDetail:
    """
    Toggle favorite flag for a given job and return the updated detail view.
    
    Creates favorite entry if it doesn't exist, updates if it does.
    """
    # First validate that the run exists
    target = find_job_log_by_run_id(run_id, path=DEFAULT_LOG_PATH)
    
    if target is None:
        raise HTTPException(
            status_code=404,
            detail=f"JobInt entry not found for run_id={run_id!r}",
        )
    
    # Update favorite on disk
    new_fav = update_job_favorite(
        run_id=run_id,
        favorite=body.favorite,
        path=DEFAULT_FAVORITES_PATH,
    )
    
    # Build updated detail using the same pattern as get_job_int_log_entry
    return JobIntLogEntryDetail(
        run_id=target["run_id"],
        job_name=target.get("job_name"),
        machine_id=target.get("machine_id"),
        post_id=target.get("post_id"),
        gcode_key=target.get("gcode_key"),
        use_helical=bool(target.get("use_helical", False)),
        favorite=new_fav,
        sim_time_s=target.get("sim_time_s"),
        sim_energy_j=target.get("sim_energy_j"),
        sim_move_count=target.get("sim_move_count"),
        sim_issue_count=target.get("sim_issue_count"),
        sim_max_dev_pct=target.get("sim_max_dev_pct"),
        created_at=target.get("created_at", ""),
        source=target.get("source", "pipeline_run"),
        sim_stats=target.get("sim_stats") or {},
        sim_issues=target.get("sim_issues") or {},
    )
