# services/api/app/rmos/models/__init__.py
#
# NOTE: A sibling models.py file exists but is shadowed by this package.
# SearchBudgetSpec and RosetteParamSpec are re-defined here so that
# ``from app.rmos.models import SearchBudgetSpec`` works correctly.

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .pattern import (
    RosettePoint,
    RosetteRing,
    RosettePattern,
    SlicePreviewRequest,
    SlicePreviewResponse,
    PipelineHandoffRequest,
    PipelineHandoffResponse,
)


class SearchBudgetSpec(BaseModel):
    """Budget constraints for AI/constraint-first search loops."""

    max_attempts: int = Field(
        default=50, ge=1, le=200,
        description="Maximum number of candidate evaluations.",
    )
    time_limit_seconds: float = Field(
        default=30.0, ge=0.1, le=60.0,
        description="Maximum wall-clock time for the search.",
    )
    min_feasibility_score: float = Field(
        default=0.0, ge=0.0, le=100.0,
        description="Minimum acceptable feasibility score.",
    )
    stop_on_first_green: bool = Field(
        default=True,
        description="Stop as soon as a GREEN candidate is found.",
    )
    deterministic: bool = Field(
        default=True,
        description="Use deterministic RNG for reproducibility.",
    )


class RosetteParamSpec(BaseModel):
    """Rosette design parameter specification."""

    version: str = Field(default="1.0", description="Schema version")
    outer_diameter_mm: float = Field(default=100.0, ge=10.0, le=500.0)
    inner_diameter_mm: float = Field(default=20.0, ge=0.0, le=400.0)
    ring_count: int = Field(default=3, ge=0, le=20)
    pattern_type: str = Field(default="herringbone")
    rings: List[Dict[str, Any]] = Field(default_factory=list)
    notes: str = Field(default="")

    class Config:
        extra = "allow"


__all__ = [
    "RosettePoint",
    "RosetteRing",
    "RosettePattern",
    "SlicePreviewRequest",
    "SlicePreviewResponse",
    "PipelineHandoffRequest",
    "PipelineHandoffResponse",
    "SearchBudgetSpec",
    "RosetteParamSpec",
]
