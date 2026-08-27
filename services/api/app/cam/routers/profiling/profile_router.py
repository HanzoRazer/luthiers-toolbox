"""
CAM Profile Toolpath Router

Production perimeter profiling with holding tabs, lead-in/out arcs,
and multi-pass stepdown.

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /gcode     - Generate profiling G-code
    POST /preview   - Preview tab positions
    GET  /info      - Get operation info
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.safety import safety_critical
from app.rmos.api.rmos_feasibility_router import compute_feasibility_internal
from app.rmos.policies.safety_policy import SafetyPolicy
from app.rmos.runs_v2 import (
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
    validate_and_persist,
)

# Import production profiling module
from app.cam.profiling import (
    ProfileToolpath,
    ProfileConfig,
    TabGenerator,
    MillingDirection,
)

PROFILING_TOOL_ID = "profiling:gcode"
PROFILING_MODE = "profiling"

# ProfileRequest → ProfileConfig → compute_profile_feasibility.
# Every evaluator input has a runtime source. Finishing fields are
# ProfileConfig defaults that ProfileToolpath.generate() actually uses.
PROFILE_FEASIBILITY_SOURCES = (
    ("tool_diameter_mm", "ProfileConfig.tool_diameter_mm", "mm"),
    ("cut_depth_mm", "ProfileConfig.cut_depth_mm", "mm"),
    ("stepdown_mm", "ProfileConfig.stepdown_mm <- ProfileRequest.max_stepdown_mm", "mm"),
    ("feed_rate_mm_min", "ProfileConfig.feed_rate_xy <- ProfileRequest.feed_rate_mm_min", "mm/min"),
    ("plunge_rate_mm_min", "ProfileConfig.plunge_rate <- ProfileRequest.plunge_rate_mm_min", "mm/min"),
    ("safe_z_mm", "ProfileConfig.safe_z_mm", "mm"),
    ("retract_z_mm", "ProfileConfig.retract_z_mm", "mm"),
    ("contour_point_count", "len(ProfileRequest.contour)", "count"),
    ("tab_count", "ProfileConfig.tab_count", "count"),
    ("tab_height_mm", "ProfileConfig.tab_height_mm", "mm"),
    ("use_tabs", "ProfileRequest.use_tabs", "bool"),
    ("finishing_pass", "ProfileConfig.finishing_pass (runtime default)", "bool"),
    ("finishing_allowance_mm", "ProfileConfig.finishing_allowance_mm (runtime default)", "mm"),
)

router = APIRouter()


class Point2D(BaseModel):
    """2D point."""
    x: float
    y: float


class ProfileRequest(BaseModel):
    """Request for profile toolpath generation."""

    # Geometry
    contour: List[Point2D] = Field(..., description="Profile contour points")
    is_closed: bool = Field(True, description="Whether contour is closed")
    is_outside: bool = Field(True, description="Outside (True) or inside (False) cut")

    # Tool parameters
    tool_diameter_mm: float = Field(6.35, ge=0.5, le=50.0, description="Tool diameter")

    # Cut parameters
    cut_depth_mm: float = Field(6.0, ge=0.1, le=100.0, description="Total cut depth")
    max_stepdown_mm: float = Field(2.0, ge=0.1, le=20.0, description="Max depth per pass")

    # Tab parameters
    use_tabs: bool = Field(True, description="Add holding tabs")
    tab_count: int = Field(4, ge=0, le=20, description="Number of tabs")
    tab_width_mm: float = Field(6.0, ge=1.0, le=30.0, description="Tab width")
    tab_height_mm: float = Field(1.5, ge=0.5, le=10.0, description="Tab height")

    # Feed rates
    feed_rate_mm_min: float = Field(1200.0, ge=100.0, le=10000.0)
    plunge_rate_mm_min: float = Field(400.0, ge=50.0, le=2000.0)

    # Heights
    safe_z_mm: float = Field(5.0, ge=1.0, le=50.0)
    retract_z_mm: float = Field(2.0, ge=0.5, le=25.0)

    # Options
    climb_milling: bool = Field(True, description="Use climb milling")
    lead_in_radius_mm: Optional[float] = Field(None, description="Lead-in arc radius")


class TabPreviewRequest(BaseModel):
    """Request for tab position preview."""

    contour: List[Point2D]
    is_closed: bool = True
    tab_count: int = 4
    min_corner_distance_mm: float = 10.0


class TabInfo(BaseModel):
    """Tab position info."""

    index: int
    position: Point2D
    width_mm: float


def profile_config_from_request(req: ProfileRequest) -> ProfileConfig:
    """Map HTTP intent onto the generator dataclass the route actually runs."""
    return ProfileConfig(
        tool_diameter_mm=req.tool_diameter_mm,
        cut_depth_mm=req.cut_depth_mm,
        stepdown_mm=req.max_stepdown_mm,
        feed_rate_xy=req.feed_rate_mm_min,
        plunge_rate=req.plunge_rate_mm_min,
        safe_z_mm=req.safe_z_mm,
        retract_z_mm=req.retract_z_mm,
        tab_count=req.tab_count if req.use_tabs else 0,
        tab_width_mm=req.tab_width_mm,
        tab_height_mm=req.tab_height_mm,
        lead_in_radius_mm=(
            req.lead_in_radius_mm if req.lead_in_radius_mm is not None else 5.0
        ),
        direction=(
            MillingDirection.CLIMB if req.climb_milling
            else MillingDirection.CONVENTIONAL
        ),
        compensation_side="outside" if req.is_outside else "inside",
    )


def feasibility_req_from_config(
    config: ProfileConfig,
    *,
    contour_point_count: int,
    use_tabs: bool,
) -> Dict[str, Any]:
    """Evaluator inputs from the same ProfileConfig the generator receives."""
    return {
        "tool_id": PROFILING_TOOL_ID,
        "tool_diameter_mm": config.tool_diameter_mm,
        "cut_depth_mm": config.cut_depth_mm,
        "stepdown_mm": config.stepdown_mm,
        "feed_rate_mm_min": config.feed_rate_xy,
        "plunge_rate_mm_min": config.plunge_rate,
        "safe_z_mm": config.safe_z_mm,
        "retract_z_mm": config.retract_z_mm,
        "contour_point_count": contour_point_count,
        "tab_count": config.tab_count,
        "tab_height_mm": config.tab_height_mm,
        "use_tabs": use_tabs,
        "finishing_pass": config.finishing_pass,
        "finishing_allowance_mm": config.finishing_allowance_mm,
    }


def _authorize_profiling(
    *,
    config: ProfileConfig,
    contour_point_count: int,
    use_tabs: bool,
):
    """Evaluate then policy-gate. Returns only when generation is allowed.

    Generation is not reachable from this function. Callers must not build
    G-code before this returns.
    """
    feas_req = feasibility_req_from_config(
        config,
        contour_point_count=contour_point_count,
        use_tabs=use_tabs,
    )
    feasibility = compute_feasibility_internal(
        tool_id=PROFILING_TOOL_ID,
        req=feas_req,
        context="profiling_gcode",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)
    run_id = create_run_id()
    if SafetyPolicy.should_block(decision.risk_level):
        validate_and_persist(
            run_id=run_id,
            mode=PROFILING_MODE,
            tool_id=PROFILING_TOOL_ID,
            event_type="profiling_gcode_blocked",
            status="BLOCKED",
            request_summary=feas_req,
            feasibility=feasibility,
            feasibility_sha256=feas_hash,
            risk_level=risk_level,
            block_reason=f"Blocked by safety policy: {risk_level}",
            decision_warnings=list(decision.warnings),
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "Profiling G-code generation blocked by server-side safety policy.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
            headers={"X-Run-ID": run_id, "X-ToolBox-Lane": "governed"},
        )
    return run_id, feasibility, feas_hash, risk_level, feas_req


@router.post("/gcode", response_class=Response)
@safety_critical
def generate_profile_gcode(req: ProfileRequest) -> Response:
    """
    Generate perimeter profiling G-code with holding tabs.

    Authority (compute_profile_feasibility via compute_feasibility_internal
    and SafetyPolicy) runs before ProfileToolpath.generate().
    """
    if len(req.contour) < 3:
        raise HTTPException(
            status_code=400,
            detail="Contour must have at least 3 points"
        )

    points: List[Tuple[float, float]] = [
        (pt.x, pt.y) for pt in req.contour
    ]
    config = profile_config_from_request(req)
    run_id, feasibility, feas_hash, risk_level, feas_req = _authorize_profiling(
        config=config,
        contour_point_count=len(points),
        use_tabs=req.use_tabs,
    )

    profiler = ProfileToolpath(outline=points, config=config)
    result = profiler.generate()
    gcode_hash = sha256_of_text(result.gcode)
    validate_and_persist(
        run_id=run_id,
        mode=PROFILING_MODE,
        tool_id=PROFILING_TOOL_ID,
        event_type="profiling_gcode_execution",
        status="OK",
        request_summary=feas_req,
        feasibility=feasibility,
        feasibility_sha256=feas_hash,
        risk_level=risk_level,
        gcode_sha256=gcode_hash,
    )

    return Response(
        content=result.gcode,
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Pass-Count": str(result.pass_count),
            "X-Tab-Count": str(config.tab_count),
            "X-Total-Length-MM": f"{result.total_length_mm:.2f}",
            "X-Estimated-Time-S": f"{result.estimated_time_seconds:.1f}",
            "X-Run-ID": run_id,
            "X-GCode-SHA256": gcode_hash,
            "X-ToolBox-Lane": "governed",
            "X-Risk-Level": risk_level,
        }
    )


@router.post("/preview")
def preview_tabs(req: TabPreviewRequest) -> Dict[str, Any]:
    """
    Preview tab positions on a profile contour.

    Returns tab positions without generating G-code.
    """
    if len(req.contour) < 3:
        raise HTTPException(
            status_code=400,
            detail="Contour must have at least 3 points"
        )

    points: List[Tuple[float, float]] = [
        (pt.x, pt.y) for pt in req.contour
    ]

    generator = TabGenerator(
        contour=points,
        is_closed=req.is_closed,
        tab_count=req.tab_count,
        min_corner_distance_mm=req.min_corner_distance_mm,
    )

    tabs = generator.generate()

    return {
        "ok": True,
        "tab_count": len(tabs),
        "tabs": [
            {
                "index": i,
                "position": {"x": tab.position[0], "y": tab.position[1]},
                "width_mm": tab.width,
            }
            for i, tab in enumerate(tabs)
        ],
        "contour_length_mm": generator.contour_length,
    }


@router.get("/info")
def profile_info() -> Dict[str, Any]:
    """Get profiling operation information."""
    return {
        "operation": "profiling",
        "description": "Perimeter profiling with holding tabs",
        "features": [
            "Multi-pass stepdown for deep cuts",
            "Automatic holding tab placement",
            "Tab corner avoidance",
            "Lead-in/out arcs (optional)",
            "Climb/conventional milling selection",
            "Cutter radius compensation awareness",
        ],
        "resolves": ["OM-GAP-02", "BEN-GAP-03", "VINE-07", "FV-GAP-03"],
    }
