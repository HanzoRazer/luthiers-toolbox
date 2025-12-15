# server/app/schemas/manufacturing_plan.py
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.rosette_pattern import RosettePatternInDB


class RingRequirement(BaseModel):
    """
    Per-ring tile requirement summary.
    """
    ring_index: int
    strip_family_id: str

    radius_mm: float
    width_mm: float
    circumference_mm: float

    tiles_per_guitar: int
    total_tiles: int
    tile_length_mm: float


class StripFamilyPlan(BaseModel):
    """
    Aggregated requirement for one strip family across all its rings.
    """
    strip_family_id: str
    color_hint: Optional[str] = None
    slice_angle_deg: float = 0.0

    tile_length_mm: float
    total_tiles_needed: int
    tiles_per_meter: int

    total_strip_length_m: float
    suggested_stick_length_mm: float = 300.0
    sticks_needed: int

    ring_indices: list[int] = Field(
        default_factory=list,
        description="Indices of rings that use this strip family.",
    )


class ManufacturingPlan(BaseModel):
    """
    Multi-family rosette manufacturing plan.
    - Each ring has its own ring requirement.
    - Each strip family gets its own aggregated strip plan.
    """
    pattern: RosettePatternInDB
    guitars: int

    ring_requirements: List[RingRequirement]
    strip_plans: List[StripFamilyPlan]

    notes: Optional[str] = None
