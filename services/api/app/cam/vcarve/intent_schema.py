"""
V-Carve Design Schema for CamIntentV1

Defines VCarveDesignV1 — the typed shape of the `design` payload
for V-Carve operations routed through CamIntentV1.

This schema documents exactly what keys the V-Carve design dict must contain.
It is NOT CamIntentV1 — it validates the design bucket for this specific mode.

Design bucket contains: what is being cut (geometry + cut intent)
Context bucket contains: how the machine gets there (feeds, speeds, options)
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class PathPoint(BaseModel):
    """2D point for V-carve path."""

    x: float
    y: float


class VCarvePathV1(BaseModel):
    """Single path for V-carving."""

    points: List[PathPoint] = Field(
        ...,
        min_length=2,
        description="Path points (minimum 2 required)",
    )
    is_closed: bool = Field(
        default=False,
        description="Whether path forms a closed loop",
    )


class VCarveDesignV1(BaseModel):
    """
    V-Carve design descriptor for CamIntentV1.design bucket.

    This defines WHAT is being cut — geometry and cut intent.
    Operational parameters (feeds, speeds, corner handling) belong in context.

    Design-defining fields only:
    - paths: the geometry to carve
    - bit_angle_deg: V-bit angle (defines cut profile)
    - target_line_width_mm: desired width at surface (defines depth)
    - target_depth_mm: optional override for calculated depth
    """

    paths: List[VCarvePathV1] = Field(
        ...,
        min_length=1,
        description="Paths to V-carve (at least one required)",
    )

    bit_angle_deg: float = Field(
        ...,
        ge=10.0,
        le=120.0,
        description="V-bit included angle in degrees",
    )

    target_line_width_mm: float = Field(
        ...,
        ge=0.1,
        le=20.0,
        description="Desired line width at surface in mm",
    )

    target_depth_mm: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=20.0,
        description="Override calculated depth (optional)",
    )

    tip_diameter_mm: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Tip flat diameter in mm (0 for sharp tip)",
    )

    @field_validator("paths")
    @classmethod
    def validate_paths_have_points(cls, v: List[VCarvePathV1]) -> List[VCarvePathV1]:
        """Ensure all paths have at least 2 points."""
        for i, path in enumerate(v):
            if len(path.points) < 2:
                raise ValueError(f"Path {i} must have at least 2 points")
        return v


def validate_vcarve_design(design_dict: dict) -> VCarveDesignV1:
    """
    Validate a design dict against VCarveDesignV1 schema.

    Raises:
        ValueError: If design is missing required keys or has invalid values.
    """
    try:
        return VCarveDesignV1.model_validate(design_dict)
    except Exception as e:
        raise ValueError(f"Invalid V-Carve design: {e}") from e
