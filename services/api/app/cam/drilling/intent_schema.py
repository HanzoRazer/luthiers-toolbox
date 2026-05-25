"""
Drilling Design Schema for CamIntentV1

Defines DrillingDesignV1 for the design bucket of drilling operations.

This schema describes WHAT to drill (positions, depths, diameters),
not HOW to drill it (feed rates, spindle, peck strategy).

Part of the CAM Intent First-Endpoint Migration (ADR-003).

Scope (8I):
- hole_diameter_mm: Included for feasibility validation (depth/diameter ratio)
- through_hole: EXCLUDED - no core support for through-hole logic
- coolant_mode: EXCLUDED - no core support for coolant control
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DrillPointV1(BaseModel):
    """A single drill hole position with optional per-hole overrides."""

    x: float = Field(..., description="X position in mm")
    y: float = Field(..., description="Y position in mm")
    depth_mm: Optional[float] = Field(
        None,
        gt=0,
        le=200.0,
        description="Override depth for this hole (mm)",
    )
    label: str = Field("", description="Optional hole label (e.g., 'string_1')")


class DrillingDesignV1(BaseModel):
    """
    Design specification for a drilling operation.

    Contains only design-defining fields (the "what"):
    - hole positions
    - hole depth
    - hole diameter (for feasibility validation)
    - peck drilling configuration
    """

    # Hole positions
    holes: List[DrillPointV1] = Field(
        ...,
        description="List of hole positions",
        min_length=1,
    )

    # Depth (default for all holes, can be overridden per-hole)
    hole_depth_mm: float = Field(
        ...,
        gt=0,
        le=200.0,
        description="Default hole depth in mm",
    )

    # Hole diameter - included for feasibility validation (depth/diameter ratio)
    hole_diameter_mm: float = Field(
        ...,
        gt=0,
        le=50.0,
        description="Drill diameter in mm (enables feasibility validation)",
    )

    # Peck drilling configuration
    peck_drilling: bool = Field(
        True,
        description="Whether to use peck drilling (G83 vs G81)",
    )
    peck_depth_mm: Optional[float] = Field(
        None,
        gt=0,
        le=100.0,
        description="Depth per peck in mm (required when peck_drilling=True)",
    )

    # Dwell at bottom
    dwell_ms: int = Field(
        0,
        ge=0,
        le=5000,
        description="Dwell time at bottom of hole (ms)",
    )

    @field_validator("holes")
    @classmethod
    def validate_holes_not_empty(cls, v: List[DrillPointV1]) -> List[DrillPointV1]:
        """Validate at least one hole is specified."""
        if len(v) < 1:
            raise ValueError("At least one hole must be specified")
        return v

    @model_validator(mode="after")
    def validate_peck_depth_when_peck_drilling(self) -> "DrillingDesignV1":
        """
        Validate peck_depth_mm requirements when peck_drilling=True.

        Constraints:
        - If peck_drilling=True, peck_depth_mm must be > 0
        - peck_depth_mm must be < hole_depth_mm (otherwise no peck needed)
        """
        if self.peck_drilling:
            if self.peck_depth_mm is None or self.peck_depth_mm <= 0:
                raise ValueError(
                    "peck_depth_mm must be > 0 when peck_drilling is True"
                )
            if self.peck_depth_mm >= self.hole_depth_mm:
                raise ValueError(
                    f"peck_depth_mm ({self.peck_depth_mm}mm) must be < "
                    f"hole_depth_mm ({self.hole_depth_mm}mm)"
                )
        return self


def validate_drilling_design(design_dict: dict) -> DrillingDesignV1:
    """
    Validate a design dict against DrillingDesignV1 schema.

    Args:
        design_dict: Raw design dictionary from CamIntentV1.design

    Returns:
        Validated DrillingDesignV1 instance

    Raises:
        ValueError: If validation fails
    """
    try:
        return DrillingDesignV1(**design_dict)
    except Exception as e:
        raise ValueError(f"Invalid Drilling design: {e}") from e
