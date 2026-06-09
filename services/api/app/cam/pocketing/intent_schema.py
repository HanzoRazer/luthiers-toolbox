"""
Pocketing Design Schema for CamIntentV1

Defines PocketDesignV1 for the design bucket of adaptive pocket-clearing operations.

Describes WHAT to clear (boundary, islands, depth, tool, stepover, finishing), not
HOW (feeds, heights, strategy) — those arrive via CamIntentV1.context.

Reconstructed from preserved bytecode (Dev Order 8J); follows 8G/8H/8I.
"""
from __future__ import annotations

from typing import List

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
    Design specification for an adaptive pocket-clearing operation.

    Contains only design-defining fields (the "what"):
    - pocket boundary (simple polygon) and islands (no-cut regions)
    - depth, tool diameter, stepover
    - roughing/finishing configuration
    """

    boundary: List[PocketPointV1] = Field(
        ...,
        description="Pocket boundary as list of points (must form simple polygon)",
        min_length=3,
    )
    islands: List[PocketIslandV1] = Field(
        default_factory=list,
        description="Islands (no-cut regions) within the pocket",
    )
    pocket_depth_mm: float = Field(
        ...,
        gt=0,
        le=200.0,
        description="Total pocket depth in mm",
    )
    tool_diameter_mm: float = Field(
        ...,
        ge=0.5,
        le=50.0,
        description="Tool diameter in mm (L.1 range: 0.5-50mm)",
    )
    stepover_percent: float = Field(
        50.0,
        ge=30.0,
        le=70.0,
        description="Stepover as percentage of tool diameter (30-70%)",
    )
    roughing_only: bool = Field(
        False,
        description="If True, skip finishing pass",
    )
    finish_pass: bool = Field(
        True,
        description="Whether to include a finishing pass",
    )
    finish_allowance_mm: float = Field(
        0.3,
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
        """Validate finishing configuration coherence: roughing_only forces finish off."""
        if self.roughing_only and self.finish_pass:
            object.__setattr__(self, "finish_pass", False)
        return self


def validate_pocket_design(design_dict: dict) -> PocketDesignV1:
    """
    Validate a design dict against PocketDesignV1 schema.

    Raises:
        ValueError: If validation fails (no silent defaults — wood-data discipline).
    """
    try:
        return PocketDesignV1(**design_dict)
    except Exception as e:
        raise ValueError(f"Invalid Pocketing design: {e}") from e
