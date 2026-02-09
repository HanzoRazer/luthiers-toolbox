"""
Pydantic schemas for blueprint_cam_bridge.py

Extracted as part of Phase 9 god-object decomposition.
Contains schemas for Blueprint → CAM integration endpoints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field


class Loop(BaseModel):
    """Polygon loop (closed path) - matches adaptive_router.py"""
    pts: List[Tuple[float, float]]


class BlueprintToAdaptiveRequest(BaseModel):
    """Request for Blueprint → Adaptive pocket toolpath generation"""
    # DXF parsing
    layer_name: str = Field(
        default="GEOMETRY",
        description="DXF layer to extract contours from"
    )

    # Adaptive pocket parameters (required)
    tool_d: float = Field(
        ...,
        description="Tool diameter in mm",
        gt=0
    )
    stepover: float = Field(
        default=0.45,
        description="Stepover as fraction of tool diameter",
        gt=0,
        le=1.0
    )
    stepdown: float = Field(
        default=2.0,
        description="Depth per pass in mm",
        gt=0
    )
    margin: float = Field(
        default=0.5,
        description="Margin from boundary in mm",
        ge=0
    )
    strategy: str = Field(
        default="Spiral",
        description="Toolpath strategy: Spiral or Lanes"
    )
    smoothing: float = Field(
        default=0.3,
        description="Arc tolerance for rounded joins (mm)",
        ge=0.05,
        le=1.0
    )

    # Machining parameters
    climb: bool = Field(
        default=True,
        description="Climb milling (true) or conventional (false)"
    )
    feed_xy: float = Field(
        default=1200,
        description="Cutting feed rate in mm/min",
        gt=0
    )
    feed_z: float = Field(
        default=600,
        description="Plunge feed rate in mm/min",
        gt=0
    )
    rapid: float = Field(
        default=3000,
        description="Rapid traverse rate in mm/min",
        gt=0
    )
    safe_z: float = Field(
        default=5,
        description="Safe Z height in mm",
        gt=0
    )
    z_rough: float = Field(
        default=-1.5,
        description="Cutting depth in mm",
        lt=0
    )

    # Optional: Units (always mm internally)
    units: str = Field(
        default="mm",
        description="Output units (mm or inch)"
    )


class BlueprintToAdaptiveResponse(BaseModel):
    """Response with adaptive pocket toolpath"""
    loops_extracted: int = Field(
        ...,
        description="Number of closed loops extracted from DXF"
    )
    loops: List[Loop] = Field(
        ...,
        description="Extracted loops (first=outer, rest=islands)"
    )
    moves: List[Dict[str, Any]] = Field(
        ...,
        description="Toolpath moves (G0/G1/G2/G3)"
    )
    stats: Dict[str, Any] = Field(
        ...,
        description="Toolpath statistics (length, time, volume)"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal issues during processing"
    )
