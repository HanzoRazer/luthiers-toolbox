"""
CAM Optimization Router

API endpoints for what-if optimization, cycle time estimation, and feeds/speeds.

Migrated from: routers/cam_opt_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /what_if      - What-if optimizer for feed/stepover/RPM parameters
    POST /feeds-speeds - Calculate optimal feeds and speeds for tool/material/strategy
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...time_estimator_v2 import estimate_cycle_time_v2
from ...whatif_opt import optimize_feed_stepover
from ....routers.machines_consolidated_router import get_profile
from ....cam_core.feeds_speeds import calculate_feed_plan

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class LoopIn(BaseModel):
    pts: List[List[float]]


class OptIn(BaseModel):
    moves: Optional[List[Dict[str, Any]]] = None  # Precomputed moves from /plan
    loops: Optional[List[LoopIn]] = None  # Alternative: compute moves first (not implemented)
    machine_profile_id: str
    z_total: float = -3.0
    stepdown: float = 1.0
    safe_z: float = 5.0
    bounds: Dict[str, List[float]] = Field(
        default={
            "feed": [600, 9000],
            "stepover": [0.25, 0.85],
            "rpm": [8000, 24000]
        }
    )
    tool: Dict[str, Any] = Field(
        default={
            "flutes": 2,
            "chipload_target_mm": 0.05
        }
    )
    grid: List[int] = Field(default=[6, 6])


class FeedsSpeedsRequest(BaseModel):
    """Request model for feeds/speeds calculation."""
    tool_id: str = Field(..., description="Tool identifier (e.g., 'upcut_1_4', 'ballnose_1_8')")
    material: str = Field(..., description="Material type (e.g., 'hardwood', 'softwood', 'mdf')")
    strategy: str = Field(default="roughing", description="Machining strategy (roughing, finishing, parallel, contour)")
    flutes: Optional[int] = Field(default=None, description="Number of flutes (overrides tool default)")
    diameter_mm: Optional[float] = Field(default=None, description="Tool diameter in mm (overrides default)")
    stickout_mm: Optional[float] = Field(default=None, description="Tool stickout in mm (overrides default)")


class FeedsSpeedsResponse(BaseModel):
    """Response model for feeds/speeds calculation."""
    tool_id: str
    material: str
    strategy: str
    feed_xy: float = Field(..., description="XY feed rate in mm/min")
    feed_z: float = Field(..., description="Z feed rate in mm/min (typically 50% of XY)")
    rpm: int = Field(..., description="Spindle speed in RPM")
    stepdown_mm: float = Field(..., description="Depth per pass in mm")
    stepover_mm: float = Field(..., description="Lateral step in mm")
    chipload_mm: float = Field(..., description="Calculated chipload in mm per tooth")
    heat_rating: str = Field(..., description="Heat risk assessment (COOL, WARM, HOT)")
    deflection_mm: float = Field(..., description="Estimated tool deflection in mm")
    notes: str = Field(..., description="Calculation source notes")


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/what_if")
def what_if_opt(body: OptIn) -> Dict[str, Any]:
    """
    What-if optimizer for feed/stepover/RPM parameters.

    Performs grid search to find optimal cutting parameters that:
    - Minimize cycle time
    - Honor machine profile limits (feed, accel, jerk)
    - Meet chipload targets for tool longevity
    - Stay within RPM bounds

    Args:
        body: OptIn model with:
            - moves: Prebuilt G-code moves from /plan (required)
            - machine_profile_id: Machine profile to optimize for
            - z_total: Total depth (negative, e.g., -3.0)
            - stepdown: Depth per pass (positive, e.g., 1.0)
            - safe_z: Safe retract height (positive, e.g., 5.0)
            - bounds: {feed:[lo,hi], stepover:[lo,hi], rpm:[lo,hi]}
            - tool: {flutes, chipload_target_mm}
            - grid: [feed_steps, stepover_steps]

    Returns:
        {
            baseline: {time_s, xy_time_one_pass_s, passes, hop_count, caps}
            opt: {
                best: {feed_mm_min, stepover, rpm, time_s, score}
                neighbors: List of 6 nearby samples
                grid: Grid bounds and step counts
            }
        }

    Raises:
        HTTPException 400: If moves not provided or machine profile not found
    """
    # Get machine profile
    profile = get_profile(body.machine_profile_id)

    # Validate moves present
    if body.moves is None:
        raise HTTPException(
            400,
            "M.2 expects prebuilt moves for accuracy; call /plan first and pass its moves."
        )

    # Run optimizer
    res = optimize_feed_stepover(
        body.moves,
        profile,
        z_total=body.z_total,
        stepdown=body.stepdown,
        safe_z=body.safe_z,
        bounds={k: tuple(v) for k, v in body.bounds.items()},
        tool=body.tool,
        grid=tuple(body.grid)
    )

    # Calculate baseline with current move settings for comparison
    baseline = estimate_cycle_time_v2(
        body.moves,
        profile,
        z_total=body.z_total,
        stepdown=body.stepdown,
        safe_z=body.safe_z
    )

    return {"baseline": baseline, "opt": res}


@router.post("/feeds-speeds", response_model=FeedsSpeedsResponse)
def calculate_feeds_speeds(body: FeedsSpeedsRequest) -> FeedsSpeedsResponse:
    """
    Calculate optimal feeds and speeds for a tool/material/strategy combination.

    Uses preset lookup tables when available, falls back to physics-based
    calculation from tool geometry when no preset exists.

    The calculation considers:
    - Material hardness and cutting characteristics
    - Tool geometry (diameter, flutes, stickout)
    - Strategy requirements (roughing vs finishing)
    - Chipload targets for tool longevity
    - Heat generation estimates
    - Tool deflection under cutting load

    Args:
        body: FeedsSpeedsRequest with tool_id, material, strategy, and optional overrides

    Returns:
        FeedsSpeedsResponse with calculated parameters:
        - feed_xy: XY feed rate (mm/min)
        - feed_z: Z feed rate (mm/min)
        - rpm: Spindle speed
        - stepdown_mm: Depth per pass
        - stepover_mm: Lateral step
        - chipload_mm: Chip thickness per tooth
        - heat_rating: Thermal risk level
        - deflection_mm: Expected tool deflection
        - notes: Source of calculation (preset or geometry-based)
    """
    # Build tool dict with optional overrides
    tool: Dict[str, Any] = {"id": body.tool_id}
    if body.flutes is not None:
        tool["flutes"] = body.flutes
    if body.diameter_mm is not None:
        tool["diameter_mm"] = body.diameter_mm
    if body.stickout_mm is not None:
        tool["stickout_mm"] = body.stickout_mm

    # Calculate using cam_core engine
    result = calculate_feed_plan(tool, body.material, body.strategy)

    return FeedsSpeedsResponse(**result)
