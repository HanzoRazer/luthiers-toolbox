"""
FastAPI router for retract pattern optimization.

Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Phase 5 Part 3: N.08 Retract Patterns
"""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..cam.retract_patterns import (
    LeadInConfig,
    RetractConfig,
    calculate_time_savings,
    generate_arc_lead_in,
    generate_incremental_retract,
    generate_linear_lead_in,
    generate_minimal_retract,
    generate_safe_retract,
    optimize_path_order,
)

router = APIRouter()

# Import RMOS run artifact persistence (OPERATION lane requirement)
from datetime import datetime, timezone
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)


class Point3DModel(BaseModel):
    """3D point model."""
    x: float
    y: float
    z: float


class RetractStrategyIn(BaseModel):
    """Input for retract strategy application."""
    features: List[List[List[float]]] = Field(..., description="List of feature paths (XYZ points)")
    strategy: str = Field("safe", description="Retract strategy: minimal, safe, incremental")
    safe_z: float = Field(10.0, description="Safe retract height (mm)")
    r_plane: float = Field(2.0, description="Retract plane for minimal hops (mm)")
    cutting_depth: float = Field(-15.0, description="Cutting depth (mm, negative)")
    min_hop: float = Field(2.0, description="Minimum hop height (mm)")
    short_move_threshold: float = Field(20.0, description="Short move threshold (mm)")
    long_move_threshold: float = Field(100.0, description="Long move threshold (mm)")
    feed_rate: float = Field(300.0, description="Cutting feed rate (mm/min)")
    optimize_path: str = Field("nearest_neighbor", description="Path optimization: none, nearest_neighbor, reverse")


class RetractStrategyOut(BaseModel):
    """Output from retract strategy."""
    gcode: List[str]
    stats: Dict[str, Any]


class LeadInPatternIn(BaseModel):
    """Input for lead-in pattern generation."""
    start_x: float
    start_y: float
    start_z: float
    entry_x: float
    entry_y: float
    pattern: str = Field("linear", description="Lead-in pattern: linear, arc")
    distance: float = Field(3.0, description="Lead distance (mm)")
    angle: float = Field(45.0, description="Entry angle (degrees)")
    radius: float = Field(2.0, description="Arc radius (mm)")
    feed_reduction: float = Field(0.5, description="Feed rate multiplier (0.5 = 50%)")
    feed_rate: float = Field(300.0, description="Base cutting feed rate (mm/min)")


class LeadInPatternOut(BaseModel):
    """Output from lead-in pattern generation."""
    gcode: List[str]


class StrategyListOut(BaseModel):
    """Output for strategy list."""
    strategies: List[Dict[str, Any]]


class TimeSavingsIn(BaseModel):
    """Input for time savings estimation."""
    strategy: str
    features_count: int
    avg_feature_distance: float = Field(50.0, description="Average distance between features (mm)")


class TimeSavingsOut(BaseModel):
    """Output for time savings estimation."""
    total_time_s: float
    z_time_s: float
    xy_time_s: float
    savings_pct: float


@router.get("/strategies", response_model=StrategyListOut)
def list_strategies() -> Dict[str, Any]:
    """List available retract strategies with descriptions."""
    strategies = [
        {
            "name": "minimal",
            "description": "Stay at r_plane for short hops (2-5mm)",
            "pros": "Fastest cycle time, reduced Z axis wear",
            "cons": "Collision risk with tall obstacles",
            "use_cases": ["Flat pocketing", "No fixtures/clamps", "Simple 2.5D operations"]
        },
        {
            "name": "safe",
            "description": "Always retract to safe_z between features",
            "pros": "Maximum safety, guaranteed clearance",
            "cons": "Slower cycle time (more Z moves)",
            "use_cases": ["Complex fixtures", "Vise jaws", "Work holding clamps"]
        },
        {
            "name": "incremental",
            "description": "Adaptive retract based on travel distance",
            "pros": "Balanced speed + safety",
            "cons": "More complex logic",
            "use_cases": ["General purpose", "Mixed operations", "Moderate complexity"],
            "logic": {
                "short_moves": "< 20mm: minimal retract",
                "medium_moves": "20-100mm: half retract",
                "long_moves": "> 100mm: full retract"
            }
        }
    ]
    
    return {"strategies": strategies}


@router.post("/apply", response_model=RetractStrategyOut)
def apply_retract_strategy(body: RetractStrategyIn) -> Dict[str, Any]:
    """
    Apply retract strategy to features.
    
    Optimizes toolpath with smart retract heights based on strategy.
    """
    # Validate strategy
    valid_strategies = ["minimal", "safe", "incremental"]
    if body.strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy '{body.strategy}'. Must be one of: {valid_strategies}"
        )
    
    # Validate features
    if not body.features:
        raise HTTPException(status_code=400, detail="At least one feature required")
    
    # Convert features to tuples
    features_tuples = []
    for feature in body.features:
        if not feature:
            continue
        
        # Validate each point has 3 coordinates
        feature_points = []
        for point in feature:
            if len(point) != 3:
                raise HTTPException(
                    status_code=400,
                    detail=f"Each point must have 3 coordinates (X, Y, Z), got {len(point)}"
                )
            feature_points.append(tuple(point))
        
        features_tuples.append(feature_points)
    
    # Optimize path order
    if body.optimize_path != "none":
        features_tuples = optimize_path_order(features_tuples, body.optimize_path)
    
    # Create retract config
    config = RetractConfig(
        strategy=body.strategy,
        safe_z=body.safe_z,
        r_plane=body.r_plane,
        cutting_depth=body.cutting_depth,
        min_hop=body.min_hop,
        short_move_threshold=body.short_move_threshold,
        long_move_threshold=body.long_move_threshold
    )
    
    # Apply strategy
    if body.strategy == "minimal":
        gcode_lines, stats = generate_minimal_retract(
            features_tuples, config, body.feed_rate
        )
    elif body.strategy == "safe":
        gcode_lines, stats = generate_safe_retract(
            features_tuples, config, body.feed_rate
        )
    else:  # incremental
        gcode_lines, stats = generate_incremental_retract(
            features_tuples, config, body.feed_rate
        )
    
    return {
        "gcode": gcode_lines,
        "stats": stats
    }


@router.post("/lead_in", response_model=LeadInPatternOut)
def generate_lead_in(body: LeadInPatternIn) -> Dict[str, Any]:
    """
    Generate lead-in pattern for smooth entry.
    
    Supports linear and arc patterns with configurable parameters.
    """
    # Validate pattern
    valid_patterns = ["linear", "arc"]
    if body.pattern not in valid_patterns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pattern '{body.pattern}'. Must be one of: {valid_patterns}"
        )
    
    # Create lead-in config
    config = LeadInConfig(
        pattern=body.pattern,
        distance=body.distance,
        angle=body.angle,
        radius=body.radius,
        feed_reduction=body.feed_reduction
    )
    
    # Generate lead-in
    if body.pattern == "linear":
        gcode_lines = generate_linear_lead_in(
            body.start_x, body.start_y, body.start_z,
            body.entry_x, body.entry_y,
            config, body.feed_rate
        )
    else:  # arc
        gcode_lines = generate_arc_lead_in(
            body.start_x, body.start_y, body.start_z,
            body.entry_x, body.entry_y,
            config, body.feed_rate
        )
    
    return {"gcode": gcode_lines}


@router.post("/estimate", response_model=TimeSavingsOut)
def estimate_time_savings(body: TimeSavingsIn) -> Dict[str, Any]:
    """
    Estimate time savings for different retract strategies.
    
    Compares strategy cycle time vs safe strategy baseline.
    """
    # Validate strategy
    valid_strategies = ["minimal", "safe", "incremental"]
    if body.strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy '{body.strategy}'. Must be one of: {valid_strategies}"
        )
    
    # Validate features count
    if body.features_count < 1:
        raise HTTPException(status_code=400, detail="Features count must be at least 1")
    
    # Calculate savings
    savings = calculate_time_savings(
        body.strategy,
        body.features_count,
        body.avg_feature_distance
    )
    
    return savings


@router.post("/gcode", response_class=Response)
def generate_simple_retract_gcode(
    strategy: str = "direct",
    current_z: float = -10.0,
    safe_z: float = 5.0,
    ramp_feed: float = 600.0,
    helix_radius: float = 5.0,
    helix_pitch: float = 1.0
) -> Response:
    """
    Generate simple retract G-code (for CAM Essentials Lab UI).
    
    Strategies:
    - direct: Rapid G0 to safe Z
    - ramped: Linear G1 ramp at controlled feed
    - helical: G2/G3 spiral with Z lift
    """
    gcode_lines = [
        "G21 G90",
        f"(Retract Strategy: {strategy})",
        f"(Current Z: {current_z}mm → Safe Z: {safe_z}mm)",
        ""
    ]
    
    z_travel = safe_z - current_z
    
    if strategy == "direct":
        # Instant rapid to safe Z
        gcode_lines.append(f"G0 Z{safe_z:.4f}")
        gcode_lines.append("(Direct rapid retract)")
        
    elif strategy == "ramped":
        # Linear ramp at controlled feed
        gcode_lines.append(f"G1 Z{safe_z:.4f} F{ramp_feed:.0f}")
        gcode_lines.append("(Ramped retract for delicate parts)")
        
    elif strategy == "helical":
        # Spiral up with Z lift (simplified for demonstration)
        revolutions = int(z_travel / helix_pitch) + 1
        for i in range(revolutions):
            z_step = current_z + (i + 1) * helix_pitch
            if z_step > safe_z:
                z_step = safe_z
            # Circular interpolation (simplified - full circle per step)
            gcode_lines.append(f"G2 X0 Y0 I{helix_radius:.4f} J0 Z{z_step:.4f} F{ramp_feed:.0f}")
            if z_step >= safe_z:
                break
        gcode_lines.append("(Helical retract - safest for finished surfaces)")
    
    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of retract sequence)")
    
    gcode_text = "\n".join(gcode_lines)
    
    resp = Response(
        content=gcode_text,
        media_type="text/plain",
        headers={"Content-Type": "text/plain"}
    )
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


# =============================================================================
# Governed Lane: Full RMOS artifact persistence and audit trail  
# =============================================================================

@router.post("/gcode_governed", response_class=Response)
def generate_simple_retract_gcode_governed(
    strategy: str = "direct",
    current_z: float = -10.0,
    safe_z: float = 5.0,
    ramp_feed: float = 600.0,
    helix_radius: float = 5.0,
    helix_pitch: float = 1.0
) -> Response:
    """
    Generate simple retract G-code (GOVERNED lane).
    
    Same toolpath as /gcode but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    gcode_lines = [
        "G21 G90",
        f"(Retract Strategy: {strategy})",
        f"(Current Z: {current_z}mm -> Safe Z: {safe_z}mm)",
        ""
    ]
    
    z_travel = safe_z - current_z
    
    if strategy == "direct":
        gcode_lines.append(f"G0 Z{safe_z:.4f}")
        gcode_lines.append("(Direct rapid retract)")
        
    elif strategy == "ramped":
        gcode_lines.append(f"G1 Z{safe_z:.4f} F{ramp_feed:.0f}")
        gcode_lines.append("(Ramped retract for delicate parts)")
        
    elif strategy == "helical":
        revolutions = int(z_travel / helix_pitch) + 1
        for i in range(revolutions):
            z_step = current_z + (i + 1) * helix_pitch
            if z_step > safe_z:
                z_step = safe_z
            gcode_lines.append(f"G2 X0 Y0 I{helix_radius:.4f} J0 Z{z_step:.4f} F{ramp_feed:.0f}")
            if z_step >= safe_z:
                break
        gcode_lines.append("(Helical retract - safest for finished surfaces)")
    
    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of retract sequence)")
    
    gcode_text = "\n".join(gcode_lines)
    
    # Create RMOS artifact
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj({
        "strategy": strategy,
        "current_z": current_z,
        "safe_z": safe_z,
        "ramp_feed": ramp_feed,
        "helix_radius": helix_radius,
        "helix_pitch": helix_pitch
    })
    gcode_hash = sha256_of_text(gcode_text)
    
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="retract_gcode",
        workflow_mode="retract",
        event_type="retract_gcode_execution",
        status="OK",
        request_hash=request_hash,
        gcode_hash=gcode_hash,
    )
    persist_run(artifact)
    
    resp = Response(
        content=gcode_text,
        media_type="text/plain",
        headers={"Content-Type": "text/plain"}
    )
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp


@router.post("/gcode/download")
def download_retract_gcode(body: RetractStrategyIn) -> Response:
    """
    Generate and download G-code with retract optimization.
    
    Returns .nc file ready for CNC controller.
    """
    # Apply strategy (reuse apply endpoint logic)
    result = apply_retract_strategy(body)
    
    # Build complete G-code
    gcode_lines = [
        "G21 G90",
        f"(Strategy: {body.strategy})",
        f"(Features: {len(body.features)})",
        ""
    ]
    gcode_lines.extend(result.gcode)
    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of program)")
    
    gcode_text = "\n".join(gcode_lines)
    
    # Return as downloadable file
    resp = Response(
        content=gcode_text,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=retract_{body.strategy}.nc"
        }
    )
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


@router.post("/gcode/download_governed")
def download_retract_gcode_governed(body: RetractStrategyIn) -> Response:
    """
    Generate and download G-code with retract optimization (GOVERNED lane).
    
    Same toolpath as /gcode/download but with full RMOS artifact persistence.
    Use this endpoint for production/machine execution.
    """
    # Apply strategy (reuse apply endpoint logic)
    result = apply_retract_strategy(body)
    
    # Build complete G-code
    gcode_lines = [
        "G21 G90",
        f"(Strategy: {body.strategy})",
        f"(Features: {len(body.features)})",
        ""
    ]
    gcode_lines.extend(result["gcode"])
    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of program)")
    
    gcode_text = "\n".join(gcode_lines)
    
    # Create RMOS artifact
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(body.model_dump(mode="json"))
    gcode_hash = sha256_of_text(gcode_text)
    
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="retract_download_gcode",
        workflow_mode="retract",
        event_type="retract_download_gcode_execution",
        status="OK",
        request_hash=request_hash,
        gcode_hash=gcode_hash,
    )
    persist_run(artifact)
    
    # Return as downloadable file
    resp = Response(
        content=gcode_text,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=retract_{body.strategy}.nc"
        }
    )
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp
