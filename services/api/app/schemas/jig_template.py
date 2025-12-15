from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class JigRingSpec(BaseModel):
    ring_index: int
    strip_family_id: str
    radius_mm: float
    width_mm: float
    circumference_mm: float
    tiles_per_guitar: int
    tile_length_mm: float
    slice_angle_deg: float
    color_hint: Optional[str] = None


class JigTemplate(BaseModel):
    pattern_id: str
    pattern_name: str
    guitars: int = 1
    tile_length_mm: float = 8.0
    scrap_factor: float = 0.12
    base_center_x_mm: float = 0.0
    base_center_y_mm: float = 0.0
    rings: List[JigRingSpec]
    total_tiles_all_rings: int
    notes: Optional[str] = None
