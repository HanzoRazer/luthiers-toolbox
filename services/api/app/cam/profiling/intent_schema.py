"""
Profile Design Schema for CamIntentV1

Defines ProfileDesignV1 for the design bucket of perimeter profiling operations.

This schema describes WHAT to profile (contour, tabs, finishing),
not HOW to profile it (feed rates, spindle, stepdown).

Part of the CAM Intent First-Endpoint Migration (ADR-003).
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ProfilePointV1(BaseModel):
    """A 2D point in the profile contour."""

    x: float
    y: float


class ProfileDesignV1(BaseModel):
    """
    Design specification for a profile operation.

    Contains only design-defining fields (the "what"):
    - contour geometry
    - inside/outside cut selection
    - tool geometry
    - tab configuration
    - finishing configuration
    """

    # Contour geometry
    contour: List[ProfilePointV1] = Field(
        ...,
        description="Profile contour as list of points (mm, normalized)",
        min_length=3,
    )
    is_closed: bool = Field(
        True,
        description="Whether contour is closed (returns to start)",
    )
    is_outside: bool = Field(
        True,
        description="Outside cut (True) or inside cut (False)",
    )

    # Tool geometry (design-relevant, not operational)
    tool_diameter_mm: float = Field(
        ...,
        gt=0,
        le=50.0,
        description="Tool diameter in mm",
    )

    # Cut depth
    cut_depth_mm: float = Field(
        ...,
        gt=0,
        le=100.0,
        description="Total cut depth in mm",
    )

    # Tab configuration
    use_tabs: bool = Field(
        True,
        description="Whether to add holding tabs",
    )
    tab_count: int = Field(
        4,
        ge=0,
        le=20,
        description="Number of holding tabs",
    )
    tab_width_mm: float = Field(
        6.0,
        ge=1.0,
        le=30.0,
        description="Tab width in mm",
    )
    tab_height_mm: float = Field(
        1.5,
        ge=0.5,
        le=10.0,
        description="Tab height in mm",
    )

    # Finishing configuration
    finishing_pass: bool = Field(
        True,
        description="Whether to include a finishing pass",
    )
    finishing_allowance_mm: float = Field(
        0.3,
        ge=0.0,
        le=5.0,
        description="Material allowance for finishing pass",
    )

    @field_validator("contour")
    @classmethod
    def validate_contour_length(cls, v: List[ProfilePointV1]) -> List[ProfilePointV1]:
        """Validate contour has at least 3 points."""
        if len(v) < 3:
            raise ValueError("Contour must have at least 3 points")
        return v

    @field_validator("tab_count")
    @classmethod
    def validate_tab_count_with_tabs(cls, v: int, info) -> int:
        """Validate tab_count is >= 1 when use_tabs is True."""
        # Access other fields via info.data
        use_tabs = info.data.get("use_tabs", True)
        if use_tabs and v < 1:
            raise ValueError("tab_count must be >= 1 when use_tabs is True")
        return v


def validate_profile_design(design_dict: dict) -> ProfileDesignV1:
    """
    Validate a design dict against ProfileDesignV1 schema.

    Args:
        design_dict: Raw design dictionary from CamIntentV1.design

    Returns:
        Validated ProfileDesignV1 instance

    Raises:
        ValueError: If validation fails
    """
    try:
        return ProfileDesignV1(**design_dict)
    except Exception as e:
        raise ValueError(f"Invalid Profile design: {e}") from e
