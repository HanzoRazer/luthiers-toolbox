"""
Rosette Parameter Specification - Design-First Mode

This is the canonical data model for rosette designs in Art Studio.
It represents the parametric specification that feeds into:
- SVG Preview
- Feasibility scoring
- (Future) CAM promotion

Phase 31.0 - Design-First Mode only.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RingParam(BaseModel):
    """
    A single ring band in the rosette design.
    """
    model_config = ConfigDict(extra="forbid")

    ring_index: int = Field(..., ge=0, description="0-indexed ring position")
    width_mm: float = Field(..., gt=0, description="Ring width in mm")
    pattern_type: str = Field(
        default="SOLID",
        description="Pattern type: SOLID, MOSAIC, HATCH, DOTS, STIPPLE, etc."
    )
    tile_length_mm: Optional[float] = Field(
        default=None,
        ge=0.1,
        description="Tile length for patterned rings (e.g., MOSAIC)"
    )


class RosetteParamSpec(BaseModel):
    """
    Canonical parametric specification for a rosette design.

    This is the Design-First Mode representation:
    - outer_diameter_mm: Overall rosette diameter
    - inner_diameter_mm: Inner boundary (sound hole)
    - ring_params: List of concentric ring bands from inner to outer
    """
    model_config = ConfigDict(extra="forbid")

    outer_diameter_mm: float = Field(
        ...,
        gt=0,
        description="Outer diameter of the rosette in mm"
    )
    inner_diameter_mm: float = Field(
        ...,
        gt=0,
        description="Inner diameter (sound hole boundary) in mm"
    )
    ring_params: List[RingParam] = Field(
        default_factory=list,
        description="List of ring bands from inner to outer"
    )

    def radial_span_mm(self) -> float:
        """Calculate the radial span available for rings."""
        return (self.outer_diameter_mm - self.inner_diameter_mm) / 2.0

    def total_ring_width_mm(self) -> float:
        """Sum of all ring widths."""
        return sum(r.width_mm for r in self.ring_params)
