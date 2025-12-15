# services/api/app/rmos/models.py
"""
RMOS 2.0 Data Models
Search budget, param specs, and shared types for AI workflows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .api_contracts import RiskBucket


class SearchBudgetSpec(BaseModel):
    """
    Budget constraints for AI/constraint-first search loops.
    """
    max_attempts: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of candidate evaluations."
    )
    time_limit_seconds: float = Field(
        default=30.0,
        ge=0.1,
        le=60.0,
        description="Maximum wall-clock time for the search."
    )
    min_feasibility_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Minimum acceptable feasibility score."
    )
    stop_on_first_green: bool = Field(
        default=True,
        description="Stop as soon as a GREEN candidate is found."
    )
    deterministic: bool = Field(
        default=True,
        description="Use deterministic RNG for reproducibility."
    )


class RosetteParamSpec(BaseModel):
    """
    Rosette design parameter specification.
    Minimal stub that can be extended by Art Studio schemas.
    """
    version: str = Field(default="1.0", description="Schema version")
    outer_diameter_mm: float = Field(default=100.0, ge=10.0, le=500.0)
    inner_diameter_mm: float = Field(default=20.0, ge=0.0, le=400.0)
    ring_count: int = Field(default=3, ge=0, le=20)
    pattern_type: str = Field(default="herringbone")
    rings: List[Dict[str, Any]] = Field(default_factory=list)
    notes: str = Field(default="")

    class Config:
        extra = "allow"  # Allow additional fields from Art Studio


class RmosFeasibilityResultEx(BaseModel):
    """
    Extended feasibility result with overall_score alias.
    """
    score: float = Field(default=0.0, ge=0, le=100)
    overall_score: float = Field(default=0.0, ge=0, le=100)
    risk_bucket: RiskBucket = Field(default=RiskBucket.RED)
    warnings: List[str] = Field(default_factory=list)
    efficiency: Optional[float] = None
    estimated_cut_time_seconds: Optional[float] = None
    calculator_results: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(self, **data):
        # Sync score and overall_score
        if "score" in data and "overall_score" not in data:
            data["overall_score"] = data["score"]
        elif "overall_score" in data and "score" not in data:
            data["score"] = data["overall_score"]
        super().__init__(**data)
