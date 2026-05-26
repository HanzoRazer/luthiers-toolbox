"""
Pocketing Design Schema for CamIntentV1

Defines PocketDesignV1 for the design bucket of pocketing operations.

This schema describes WHAT to pocket (boundary, islands, depth, tool),
not HOW to pocket it (feed rates, spindle, strategy).

Part of the CAM Intent First-Endpoint Migration (ADR-003).

Scope (8J):
- entry_strategy: EXCLUDED - no L.1 core support (same as coolant_mode in 8I)
- stepover_percent: bounded to [30, 70] to match L.1's actual range
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class PocketPointV1(BaseModel):
    """A 2D point in the pocket boundary or island."""

    x: float = Field(..., description="X coordinate in mm")
    y: float = Field(..., description="Y coordinate in mm")


class PocketIslandV1(BaseModel):
    """An island (no-cut region) within the pocket."""

    boundary: List[PocketPointV1] = Field(
        ...,
        description="Island boundary as list of points",
        min_length=3,
    )

    @field_validator("boundary")
    @classmethod
    def validate_boundary_length(cls, v: List[PocketPointV1]) -> List[PocketPointV1]:
        """Validate island boundary has at least 3 points."""
        if len(v) < 3:
            raise ValueError("Island boundary must have at least 3 points")
        return v


class PocketDesignV1(BaseModel):
    """
    Design specification for a pocketing operation.

    Contains only design-defining fields (the "what"):
    - boundary geometry (must be a simple, non-self-intersecting polygon)
    - islands (no-cut regions, must be valid and within boundary)
    - pocket depth
    - tool geometry
    - stepover (bounded to L.1's valid range: 30-70%)
    - roughing/finishing configuration
    """

    # Boundary geometry
    boundary: List[PocketPointV1] = Field(
        ...,
        description="Pocket boundary as list of points (must form simple polygon)",
        min_length=3,
    )

    # Islands (no-cut regions)
    islands: List[PocketIslandV1] = Field(
        default_factory=list,
        description="Islands (no-cut regions) within the pocket",
    )

    # Depth
    pocket_depth_mm: float = Field(
        ...,
        gt=0,
        le=100.0,
        description="Total pocket depth in mm",
    )

    # Tool geometry
    tool_diameter_mm: float = Field(
        ...,
        gt=0.5,
        le=50.0,
        description="Tool diameter in mm (L.1 range: 0.5-50mm)",
    )

    # Stepover - bounded to L.1's actual range [0.3, 0.7] = [30%, 70%]
    stepover_percent: float = Field(
        40.0,
        ge=30.0,
        le=70.0,
        description="Stepover as percentage of tool diameter (30-70%)",
    )

    # Roughing/finishing configuration
    roughing_only: bool = Field(
        False,
        description="If True, skip finishing pass",
    )
    finish_pass: bool = Field(
        True,
        description="Whether to include a finishing pass",
    )
    finish_allowance_mm: float = Field(
        0.25,
        ge=0.0,
        le=5.0,
        description="Material left for finishing pass (mm)",
    )

    @field_validator("boundary")
    @classmethod
    def validate_boundary_length(cls, v: List[PocketPointV1]) -> List[PocketPointV1]:
        """Validate boundary has at least 3 points."""
        if len(v) < 3:
            raise ValueError("Boundary must have at least 3 points")
        return v

    @model_validator(mode="after")
    def validate_finish_coherence(self) -> "PocketDesignV1":
        """Validate finishing configuration coherence."""
        if self.roughing_only and self.finish_pass:
            # roughing_only takes precedence
            object.__setattr__(self, "finish_pass", False)
        return self


def validate_pocket_design(design_dict: dict) -> PocketDesignV1:
    """
    Validate a design dict against PocketDesignV1 schema.

    Args:
        design_dict: Raw design dictionary from CamIntentV1.design

    Returns:
        Validated PocketDesignV1 instance

    Raises:
        ValueError: If validation fails
    """
    try:
        return PocketDesignV1(**design_dict)
    except Exception as e:
        raise ValueError(f"Invalid Pocketing design: {e}") from e
