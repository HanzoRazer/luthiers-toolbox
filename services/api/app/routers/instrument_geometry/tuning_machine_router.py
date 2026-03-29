"""
Tuning Machine Router (GEOMETRY-008)

Split router for tuning machine calculations:
- Break angle calculation
- String tree recommendation
- Post height requirements
- Wrap count estimation

Migrated from instrument_router.py as part of router decomposition.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...calculators.tuning_machine_calc import (
    TuningMachineSpec,
    compute_tuning_machine_spec,
    compute_required_post_height,
    check_string_tree_needed,
    compute_wrap_count,
    list_standard_post_heights,
    get_string_tree_spec,
    STRING_TREE_SPECS,
    STANDARD_POST_HEIGHTS,
)

router = APIRouter(
    prefix="/tuning-machine",
    tags=["Tuning Machine"],
)


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class TuningMachineRequest(BaseModel):
    """Request for tuning machine specification."""

    headstock_angle_deg: float = Field(
        ...,
        ge=0,
        le=20,
        description="Headstock pitch angle in degrees (0 for flat/Fender, 14-17 for Gibson)",
    )
    nut_to_post_mm: float = Field(
        ...,
        gt=0,
        description="Distance from nut to tuner post center in mm",
    )
    post_height_mm: float = Field(
        ...,
        gt=0,
        description="Height of tuner post above headstock face in mm",
    )
    string_name: str = Field(
        ...,
        description="String identifier: E, A, D, G, B, e (or 6, 5, 4, 3, 2, 1)",
    )
    string_gauge_inch: Optional[float] = Field(
        default=0.010,
        gt=0,
        description="String diameter in inches (default: 0.010)",
    )


class TuningMachineResponse(BaseModel):
    """Response with tuning machine specification."""

    post_height_mm: float
    break_angle_deg: float
    string_tree_needed: bool
    string_tree_type: str
    wrap_count: float
    gate: str
    notes: List[str]


class PostHeightRequest(BaseModel):
    """Request for required post height calculation."""

    headstock_angle_deg: float = Field(..., ge=0, le=20)
    nut_to_post_mm: float = Field(..., gt=0)
    target_break_angle_deg: float = Field(default=9.0, ge=5, le=15)


class PostHeightResponse(BaseModel):
    """Response with required post height."""

    required_post_height_mm: float
    target_break_angle_deg: float
    headstock_angle_deg: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=TuningMachineResponse)
def get_tuning_machine_spec(payload: TuningMachineRequest) -> TuningMachineResponse:
    """
    Calculate tuning machine specification for a string.

    Computes break angle, string tree recommendation, and wrap count.

    Break angle formula (angled headstock):
    break_angle = arctan(
        (nut_to_tuner × sin(headstock_angle) - post_height)
        / (nut_to_tuner × cos(headstock_angle))
    )

    String tree needed if:
    - break_angle < 7° AND string is G or B

    Minimum recommended break angle: 7-10°
    Maximum before string breakage risk: 20°
    """
    spec = compute_tuning_machine_spec(
        headstock_angle_deg=payload.headstock_angle_deg,
        nut_to_post_mm=payload.nut_to_post_mm,
        post_height_mm=payload.post_height_mm,
        string_name=payload.string_name,
        string_gauge_inch=payload.string_gauge_inch or 0.010,
    )

    return TuningMachineResponse(
        post_height_mm=spec.post_height_mm,
        break_angle_deg=spec.break_angle_deg,
        string_tree_needed=spec.string_tree_needed,
        string_tree_type=spec.string_tree_type,
        wrap_count=spec.wrap_count,
        gate=spec.gate,
        notes=spec.notes,
    )


@router.post("/required-height", response_model=PostHeightResponse)
def get_required_post_height(payload: PostHeightRequest) -> PostHeightResponse:
    """
    Calculate required tuner post height to achieve target break angle.

    Useful for selecting tuning machines when designing a headstock.
    """
    required_height = compute_required_post_height(
        headstock_angle_deg=payload.headstock_angle_deg,
        nut_to_post_mm=payload.nut_to_post_mm,
        target_break_angle_deg=payload.target_break_angle_deg,
    )

    return PostHeightResponse(
        required_post_height_mm=required_height,
        target_break_angle_deg=payload.target_break_angle_deg,
        headstock_angle_deg=payload.headstock_angle_deg,
    )


@router.get("/post-heights")
def list_post_heights():
    """List standard tuner post heights by brand."""
    return {
        "post_heights_mm": list_standard_post_heights(),
    }


@router.get("/string-trees")
def list_string_trees():
    """List available string tree types and specifications."""
    return {
        "string_tree_types": list(STRING_TREE_SPECS.keys()),
        "specifications": STRING_TREE_SPECS,
    }
