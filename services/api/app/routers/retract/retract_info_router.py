"""Retract Info Router - Strategy information and time estimation.

Provides:
- GET /strategies - List available retract strategies
- POST /estimate - Estimate time savings

Total: 2 routes for utility/info endpoints.

LANE: UTILITY
"""
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...cam.retract_patterns import calculate_time_savings

router = APIRouter(tags=["Retract", "Utility"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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


__all__ = [
    "router",
    "StrategyListOut",
    "TimeSavingsIn",
    "TimeSavingsOut",
]
