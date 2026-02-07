"""
Learned Overrides API - Lane-based parameter learning endpoints.

Endpoints:
- GET    /api/feeds/learned/lanes                     - List all lanes
- GET    /api/feeds/learned/lanes/{lane_id}           - Get specific lane
- POST   /api/feeds/learned/override                  - Set parameter override
- POST   /api/feeds/learned/lane_scale                - Update lane scale
- POST   /api/feeds/learned/merge                     - Merge baseline with overrides
- POST   /api/feeds/learned/record_run                - Record successful run
- GET    /api/feeds/learned/audit                     - Get audit trail
- GET    /api/feeds/learned/stats                     - Get statistics
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, Dict, List, Any
from pydantic import BaseModel

from .._experimental.cnc_production.feeds_speeds.core.learned_overrides import (
    get_learned_overrides_store,
    LaneKey,
    LaneOverrides,
    ParameterOverride,
    OverrideSource,
    AuditEntry
)


router = APIRouter(prefix="/feeds/learned", tags=["Feeds & Speeds", "Learning"])


# ============================================================================
# Request Models
# ============================================================================

class SetOverrideRequest(BaseModel):
    """Request to set parameter override."""
    lane_key: LaneKey
    param_name: str
    value: float
    source: OverrideSource
    scale: Optional[float] = None
    confidence: float = 1.0
    operator: Optional[str] = None
    notes: Optional[str] = None
    reason: Optional[str] = None


class UpdateLaneScaleRequest(BaseModel):
    """Request to update lane scale."""
    lane_key: LaneKey
    lane_scale: float
    source: OverrideSource = OverrideSource.AUTO_LEARN
    operator: Optional[str] = None
    reason: Optional[str] = None


class MergeParametersRequest(BaseModel):
    """Request to merge baseline with overrides."""
    baseline: Dict[str, float]
    lane_key: LaneKey


class RecordRunRequest(BaseModel):
    """Request to record run."""
    lane_key: LaneKey
    success: bool = True


# ============================================================================
# Response Models
# ============================================================================

class MergeResult(BaseModel):
    """Result of parameter merge."""
    merged: Dict[str, float]
    baseline: Dict[str, float]
    lane_key: LaneKey
    overrides_applied: List[str]
    lane_scale: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/lanes", response_model=List[LaneOverrides])
def list_lanes(
    tool_id: Optional[str] = Query(None),
    material: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    machine_profile: Optional[str] = Query(None)
):
    """
    List learned override lanes.
    
    Query params for filtering:
    - tool_id: Filter by blade/tool ID
    - material: Filter by material family
    - mode: Filter by operation mode
    - machine_profile: Filter by machine
    
    Returns:
        List of lanes matching filters
    """
    store = get_learned_overrides_store()
    
    try:
        lanes = store.list_lanes(
            tool_id=tool_id,
            material=material,
            mode=mode,
            machine_profile=machine_profile
        )
        return lanes
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list lanes: {str(e)}"
        )


@router.get("/lanes/{tool_id}/{material}/{mode}/{machine_profile}", response_model=LaneOverrides)
def get_lane(
    tool_id: str,
    material: str,
    mode: str,
    machine_profile: str
):
    """
    Get specific lane by 4-tuple key.
    
    Args:
        tool_id: Blade/tool ID
        material: Material family
        mode: Operation mode
        machine_profile: Machine identifier
        
    Returns:
        Lane overrides
        
    Raises:
        404: Lane not found
    """
    store = get_learned_overrides_store()
    
    lane_key = LaneKey(
        tool_id=tool_id,
        material=material,
        mode=mode,
        machine_profile=machine_profile
    )
    
    lane = store.get_lane(lane_key)
    
    if lane is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lane not found: {tool_id}|{material}|{mode}|{machine_profile}"
        )
    
    return lane


@router.post("/override", response_model=ParameterOverride)
def set_override(req: SetOverrideRequest):
    """
    Set parameter override for lane.
    
    Creates lane if doesn't exist. Records audit entry.
    
    Returns:
        Created parameter override
    """
    store = get_learned_overrides_store()
    
    try:
        override = store.set_override(
            lane_key=req.lane_key,
            param_name=req.param_name,
            value=req.value,
            source=req.source,
            scale=req.scale,
            confidence=req.confidence,
            operator=req.operator,
            notes=req.notes,
            reason=req.reason
        )
        return override
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set override: {str(e)}"
        )


@router.post("/lane_scale")
def update_lane_scale(req: UpdateLaneScaleRequest):
    """
    Update overall lane scale factor.
    
    Lane scale is multiplied with all parameters in the lane.
    Records audit entry.
    
    Returns:
        Success message
    """
    store = get_learned_overrides_store()
    
    try:
        store.update_lane_scale(
            lane_key=req.lane_key,
            lane_scale=req.lane_scale,
            source=req.source,
            operator=req.operator,
            reason=req.reason
        )
        return {"success": True, "message": f"Lane scale updated to {req.lane_scale}"}
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lane scale: {str(e)}"
        )


@router.post("/merge", response_model=MergeResult)
def merge_parameters(req: MergeParametersRequest):
    """
    Merge baseline parameters with learned overrides.
    
    Formula: final = (baseline + learned_override) * lane_scale
    
    Returns:
        Merged parameters with metadata
    """
    store = get_learned_overrides_store()
    
    try:
        merged = store.merge_parameters(req.baseline, req.lane_key)
        
        # Get lane for metadata
        lane = store.get_lane(req.lane_key)
        overrides_applied = list(lane.overrides.keys()) if lane else []
        lane_scale = lane.lane_scale if lane else 1.0
        
        return MergeResult(
            merged=merged,
            baseline=req.baseline,
            lane_key=req.lane_key,
            overrides_applied=overrides_applied,
            lane_scale=lane_scale
        )
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge parameters: {str(e)}"
        )


@router.post("/record_run")
def record_run(req: RecordRunRequest):
    """
    Record successful/failed run for lane.
    
    Updates:
    - run_count
    - success_rate (exponential moving average)
    - last_run timestamp
    
    Returns:
        Success message
    """
    store = get_learned_overrides_store()
    
    try:
        store.record_run(req.lane_key, req.success)
        return {
            "success": True,
            "message": f"Run recorded ({'success' if req.success else 'failure'})"
        }
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record run: {str(e)}"
        )


@router.get("/audit", response_model=List[AuditEntry])
def get_audit_trail(
    tool_id: Optional[str] = Query(None),
    material: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    machine_profile: Optional[str] = Query(None),
    param_name: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get audit trail entries.
    
    Query params for filtering:
    - tool_id, material, mode, machine_profile: Filter by lane
    - param_name: Filter by parameter
    - limit: Max entries to return (1-1000)
    
    Returns:
        List of audit entries (newest first)
    """
    store = get_learned_overrides_store()
    
    try:
        # Build lane key if components provided
        lane_key = None
        if tool_id and material and mode and machine_profile:
            lane_key = LaneKey(
                tool_id=tool_id,
                material=material,
                mode=mode,
                machine_profile=machine_profile
            )
        
        entries = store.get_audit_trail(
            lane_key=lane_key,
            param_name=param_name,
            limit=limit
        )
        return entries
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit trail: {str(e)}"
        )


@router.get("/stats")
def get_statistics():
    """
    Get learned overrides statistics.
    
    Returns:
        Statistics dictionary:
        - total_lanes
        - total_audit_entries
        - overrides_by_source
        - lanes_by_machine
    """
    store = get_learned_overrides_store()
    
    try:
        stats = store.get_statistics()
        return stats
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
