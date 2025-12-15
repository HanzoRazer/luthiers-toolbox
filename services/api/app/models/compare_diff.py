"""B22 Compare Lab diff models."""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class DiffSummary(BaseModel):
    """High-level breakdown of geometry differences."""

    segments_baseline: int = 0
    segments_current: int = 0
    added: int = 0
    removed: int = 0
    unchanged: int = 0
    overlap_ratio: float = 0.0


class DiffSegment(BaseModel):
    """Per-segment annotations surfaced to the frontend."""

    id: str
    type: Literal["line", "arc"]
    status: Literal["added", "removed", "match"]
    length: float = 0.0
    path_index: int = 0
    meta: Dict[str, Any] = Field(default_factory=dict)


class DiffResult(BaseModel):
    """Complete diff response for Compare Lab."""

    baseline_id: str
    baseline_name: str
    summary: DiffSummary
    segments: list[DiffSegment] = Field(default_factory=list)
    baseline_geometry: Optional[Dict[str, Any]] = None
    current_geometry: Optional[Dict[str, Any]] = None
