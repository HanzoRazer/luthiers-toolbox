"""CAM Learning API - Train feed overrides from logged runs."""

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from ..learn.overrides_learner import train_overrides

router = APIRouter(tags=["cam-learn"])


class TrainIn(BaseModel):
    """Training parameters for feed override learning."""

    machine_id: str | None = None  # Legacy parameter (backward compat)
    machine_profile: str | None = None  # Preferred parameter (alias for machine_id)
    r_min_mm: float = 5.0  # Minimum radius threshold for "tight arc" rule


@router.post("/train")
def train(body: TrainIn) -> Dict[str, Any]:
    """
    Train feed overrides from logged CAM runs.

    Analyzes segment telemetry to learn scalar feed multipliers for:
    - Tight arcs (radius < r_min_mm): Average observed slowdown
    - Trochoidal moves: Average observed slowdown

    Requires minimum 50 samples per rule to avoid overfitting.

    Args:
        machine_id: Machine profile ID (legacy, backward compatible)
        machine_profile: Machine profile ID (preferred, alias for machine_id)
        r_min_mm: Minimum radius threshold for tight arc rule

    Returns:
        {
          "machine_id": "Mach4_Router_4x8",
          "machine_profile": "Mach4_Router_4x8",
          "rules": {
            "arc_tight_mm<=5.00": 0.75,
            "trochoid": 0.85
          },
          "meta": {"samples": 1234, "r_min": 5.0}
        }

    Saves model to: learn/models/overrides_{machine_id}.json
    """
    out = train_overrides(
        machine_id=body.machine_id,
        machine_profile=body.machine_profile,
        r_min_mm=body.r_min_mm
    )
    return out
