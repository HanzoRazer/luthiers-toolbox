# server/app/schemas/rosette_pattern.py
from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field


class RosetteRingBand(BaseModel):
    """
    A single concentric ring in the rosette pattern.
    """
    id: str

    # 0 = outermost (or your chosen convention, but keep consistent).
    index: int = Field(..., ge=0, description="0 = outermost ring")

    # Geometry
    radius_mm: float = Field(..., ge=0.0)
    width_mm: float = Field(..., ge=0.0)

    # UI / visualization only
    color_hint: Optional[str] = None

    # NEW: strip family + cut angle + tile length override
    strip_family_id: str = Field(
        ...,
        description="Logical family for this ring's tiles (e.g. 'bw_checker_main').",
    )
    slice_angle_deg: float = Field(
        0.0,
        description="Angle at which strip is sliced vs board, used in strip recipe descriptions.",
    )
    tile_length_override_mm: Optional[float] = Field(
        None,
        description="If set, overrides default tile_length_mm used in the planner.",
    )


class RosettePatternBase(BaseModel):
    """
    Base fields shared by all RosettePattern variants.
    """
    name: str

    center_x_mm: float = 0.0
    center_y_mm: float = 0.0

    ring_bands: List[RosetteRingBand] = Field(default_factory=list)

    default_slice_thickness_mm: float = Field(
        ...,
        ge=0.3,
        le=2.5,
        description="Default slice thickness for tiles derived from this pattern.",
    )
    default_passes: int = Field(
        ...,
        ge=1,
        description="Default number of passes for saw cuts (can be overridden later).",
    )
    default_workholding: str = Field(
        ...,
        description="vacuum | screw_fixture | jig | hybrid",
    )
    default_tool_id: Optional[str] = Field(
        None,
        description="Optional saw tool id used by default for this pattern.",
    )


class RosettePatternCreate(RosettePatternBase):
    """
    Payload for creating a pattern; id is provided by caller.
    """
    id: str = Field(..., description="Pattern id, e.g. 'rosette_default'")


class RosettePatternUpdate(BaseModel):
    """
    Partial update; any field may be omitted.
    """
    name: Optional[str] = None
    center_x_mm: Optional[float] = None
    center_y_mm: Optional[float] = None
    ring_bands: Optional[List[RosetteRingBand]] = None

    default_slice_thickness_mm: Optional[float] = None
    default_passes: Optional[int] = None
    default_workholding: Optional[str] = None
    default_tool_id: Optional[str] = None


class RosettePatternInDB(RosettePatternBase):
    """
    Canonical pattern shape stored and returned by the API.
    """
    id: str
