"""Retract Apply Router - Strategy application and lead-in patterns.

Provides:
- POST /apply - Apply retract strategy to features
- POST /lead_in - Generate lead-in patterns

Total: 2 routes for strategy application.

LANE: OPERATION
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...cam.retract_patterns import (
    LeadInConfig,
    RetractConfig,
    generate_arc_lead_in,
    generate_incremental_retract,
    generate_linear_lead_in,
    generate_minimal_retract,
    generate_safe_retract,
    optimize_path_order,
)

router = APIRouter(tags=["Retract", "Apply"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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


__all__ = [
    "router",
    "RetractStrategyIn",
    "RetractStrategyOut",
    "LeadInPatternIn",
    "LeadInPatternOut",
]
