# File: services/api/app/schemas/relief_sim.py
# Phase 24.3: Relief Simulation Bridge - Pydantic Models

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .relief import ReliefMove


class ReliefSimIssue(BaseModel):
    type: str = Field(
        ...,
        description="Issue category, e.g. 'thin_floor', 'over_depth', 'high_load'",
    )
    severity: Literal["info", "low", "medium", "high", "critical"] = "medium"
    x: float
    y: float
    z: Optional[float] = None
    extra_time_s: Optional[float] = Field(
        default=None,
        description="Optional extra time associated with this issue (if any).",
    )
    note: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReliefSimOverlayOut(BaseModel):
    type: str = Field(
        ...,
        description="Overlay type, e.g. 'load_hotspot', 'thin_floor_zone'",
    )
    x: float
    y: float
    z: Optional[float] = None
    intensity: Optional[float] = Field(
        default=None,
        description="Normalized intensity (0..1) for heatmap-like display.",
    )
    severity: Optional[Literal["info", "low", "medium", "high", "critical"]] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReliefSimStats(BaseModel):
    cell_count: int
    avg_floor_thickness: float
    min_floor_thickness: float
    max_load_index: float
    avg_load_index: float
    total_removed_volume: float


class ReliefSimIn(BaseModel):
    moves: List[ReliefMove] = Field(
        ..., description="Finishing (or roughing) toolpath moves in machine space."
    )
    stock_thickness: float = Field(
        ...,
        description="Stock thickness above the relief reference (typically positive).",
    )
    origin_x: float = 0.0
    origin_y: float = 0.0
    cell_size_xy: float = 0.5
    units: Literal["mm", "inch"] = "mm"

    # thresholds
    min_floor_thickness: float = Field(
        0.6,
        description="Below this, we consider the floor too thin.",
    )
    high_load_index: float = Field(
        2.0,
        description="Above this normalized load index, mark as high-load hotspot.",
    )
    med_load_index: float = Field(
        1.0,
        description="Above this normalized load index, mark as medium-load hotspot.",
    )


class ReliefSimOut(BaseModel):
    issues: List[ReliefSimIssue] = Field(default_factory=list)
    overlays: List[ReliefSimOverlayOut] = Field(default_factory=list)
    stats: ReliefSimStats
