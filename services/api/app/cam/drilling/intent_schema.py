"""
Drilling Design Schema for CamIntentV1

Defines DrillingDesignV1 for the design bucket of peck-drilling operations.

This schema describes WHAT to drill (hole positions, depths, diameter, peck mode),
not HOW to drill it (feed rate, spindle, safe/retract heights, dwell) — those are
operational and arrive via CamIntentV1.context.

Part of the CAM Intent First-Endpoint Migration (Dev Order 8I), following 8G/8H.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class DrillPointV1(BaseModel):
    """A single hole position in the drilling design."""

    x: float = Field(..., description="X coordinate in mm")
    y: float = Field(..., description="Y coordinate in mm")
    depth_mm: Optional[float] = Field(
        None,
        gt=0,
        le=200.0,
        description="Per-hole depth override in mm (defaults to design hole_depth_mm)",
    )
    label: str = Field("", description="Optional label, e.g. 'string_1', 'bolt_neck_1'")


class DrillingDesignV1(BaseModel):
    """
    Design specification for a peck-drilling operation.

    Contains only design-defining fields (the "what"):
    - hole positions
    - default hole depth
    - drill diameter (functional feasibility input, NOT decorative)
    - peck configuration
    """

    # Hole geometry
    holes: List[DrillPointV1] = Field(
        ...,
        description="Hole positions to drill",
        min_length=1,
    )
    hole_depth_mm: float = Field(
        ...,
        gt=0,
        le=200.0,
        description="Default total hole depth in mm (per-hole depth_mm overrides)",
    )

    # Drill geometry — functional feasibility input
    hole_diameter_mm: float = Field(
        ...,
        gt=0,
        le=50.0,
        description="Drill diameter in mm (drives depth:diameter feasibility)",
    )

    # Peck configuration
    peck_drilling: bool = Field(
        True,
        description="Use peck (G83) cycle to clear chips on deep holes",
    )
    peck_depth_mm: float = Field(
        ...,
        gt=0,
        le=200.0,
        description="Depth per peck (G83 Q value) in mm",
    )

    @field_validator("holes")
    @classmethod
    def validate_holes_length(cls, v: List[DrillPointV1]) -> List[DrillPointV1]:
        """Validate at least one hole is specified."""
        if len(v) < 1:
            raise ValueError("holes must contain at least 1 hole")
        return v


def validate_drilling_design(design_dict: dict) -> DrillingDesignV1:
    """
    Validate a design dict against DrillingDesignV1 schema.

    Args:
        design_dict: Raw design dictionary from CamIntentV1.design

    Returns:
        Validated DrillingDesignV1 instance

    Raises:
        ValueError: If validation fails (no silent defaults — wood-data discipline)
    """
    try:
        return DrillingDesignV1(**design_dict)
    except Exception as e:
        raise ValueError(f"Invalid Drilling design: {e}") from e
