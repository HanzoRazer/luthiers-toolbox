"""
String Tension Router - String tension and saddle force calculations.

Migrated from instrument_router.py (Wave 7 decomposition).

Endpoints:
- POST /string-tension — Calculate string set tension
- GET  /string-tension/presets — List string set presets
- POST /saddle-force — Calculate saddle force decomposition

Total: 3 endpoints
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.calculators.string_tension import (
    StringSpec as StringSpecCalc,
    TensionResult,
    SetTensionResult,
    compute_string_tension_from_spec,
    compute_set_tension,
    get_preset_set,
    list_preset_sets,
    STRING_SETS,
    SCALE_LENGTHS_MM,
)
from app.calculators.saddle_force_calc import (
    compute_saddle_force,
    SaddleForceResult,
    StringForce,
)

router = APIRouter(tags=["instrument-geometry", "string-tension"])


# ─── Models ────────────────────────────────────────────────────────────────────


class StringSpecRequest(BaseModel):
    """Specification for a single string."""
    name: str = Field(..., description="String name (e.g., '1' or 'e')")
    gauge_inch: float = Field(..., gt=0, description="String diameter in inches")
    is_wound: bool = Field(..., description="True if wound string")
    note: str = Field(..., description="Note name (e.g., 'E4', 'B3')")
    frequency_hz: float = Field(..., gt=0, description="Target frequency in Hz")


class StringTensionRequest(BaseModel):
    """Request for string tension calculation."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    string_set: Optional[str] = Field(
        default=None,
        description="Preset string set name (e.g., 'light_012', 'medium_013')"
    )
    custom_strings: Optional[List[StringSpecRequest]] = Field(
        default=None,
        description="Custom string specifications (overrides string_set)"
    )


class StringTensionResponse(BaseModel):
    """Response with tension calculations."""
    scale_length_mm: float
    set_name: str
    strings: List[dict]
    total_tension_lb: float
    total_tension_n: float


class StringPresetsResponse(BaseModel):
    """Response with available string set presets."""
    string_sets: List[str]
    scale_lengths_mm: dict


class SaddleForceRequest(BaseModel):
    """Request for saddle force calculation."""
    string_tensions_n: List[float] = Field(
        ...,
        description="Tension for each string in Newtons",
        min_length=1,
        max_length=12,
    )
    break_angles_deg: List[float] = Field(
        ...,
        description="Break angle over saddle for each string (degrees)",
        min_length=1,
        max_length=12,
    )
    body_depth_at_bridge_mm: float = Field(
        default=100.0,
        gt=0,
        description="Depth of body at bridge location (mm)",
    )
    pin_to_tailblock_mm: float = Field(
        default=250.0,
        gt=0,
        description="Distance from bridge pins to tailblock (mm)",
    )
    string_names: Optional[List[str]] = Field(
        default=None,
        description="Optional names for each string (e.g., ['E2', 'A2', ...])",
    )


class StringForceResponse(BaseModel):
    """Force contribution from a single string."""
    string_name: str
    tension_n: float
    break_angle_deg: float
    behind_angle_deg: float
    vertical_force_n: float


class SaddleForceResponse(BaseModel):
    """Response with saddle force decomposition."""
    string_forces: List[StringForceResponse]
    total_vertical_force_n: float
    total_vertical_force_lbs: float
    gate: str
    notes: List[str]


# ─── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/string-tension",
    response_model=StringTensionResponse,
    summary="Calculate string set tension (CONSTRUCTION-004)",
)
def calculate_string_tension(payload: StringTensionRequest) -> StringTensionResponse:
    """
    Calculate string tension for a guitar string set.

    Uses the physics formula: T = (2 * f * L)^2 * mu

    Can use either:
    - A preset string set (light_012, medium_013, etc.)
    - Custom string specifications

    Returns tension for each string and total tension.
    Useful for bracing calculations and bridge plate sizing.
    """
    if payload.custom_strings:
        # Use custom strings
        strings = [
            StringSpecCalc(
                name=s.name,
                gauge_inch=s.gauge_inch,
                is_wound=s.is_wound,
                note=s.note,
                frequency_hz=s.frequency_hz,
            )
            for s in payload.custom_strings
        ]
        set_name = "custom"
    elif payload.string_set:
        # Use preset
        try:
            strings = get_preset_set(payload.string_set)
            set_name = payload.string_set
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Default to light gauge
        strings = get_preset_set("light_012")
        set_name = "light_012"

    result = compute_set_tension(strings, payload.scale_length_mm, set_name=set_name)

    return StringTensionResponse(
        scale_length_mm=result.scale_length_mm,
        set_name=result.set_name,
        strings=[
            {
                "name": s.name,
                "gauge_inch": s.gauge_inch,
                "gauge_mm": s.gauge_mm,
                "note": s.note,
                "is_wound": s.is_wound,
                "tension_lb": s.tension_lb,
                "tension_n": s.tension_n,
            }
            for s in result.strings
        ],
        total_tension_lb=result.total_tension_lb,
        total_tension_n=result.total_tension_n,
    )


@router.get(
    "/string-tension/presets",
    response_model=StringPresetsResponse,
    summary="List string set presets and scale lengths",
)
def list_string_presets() -> StringPresetsResponse:
    """List available string set presets and scale lengths."""
    return StringPresetsResponse(
        string_sets=list_preset_sets(),
        scale_lengths_mm=SCALE_LENGTHS_MM,
    )


@router.post(
    "/saddle-force",
    response_model=SaddleForceResponse,
    summary="Calculate saddle force decomposition (ACOUSTIC-002)",
)
def calculate_saddle_force(payload: SaddleForceRequest) -> SaddleForceResponse:
    """
    Calculate saddle force from string tensions and break angles.

    ACOUSTIC-002: Decomposes saddle break angle into vertical downbearing
    force component (bridge plate load).

    Formula: F_saddle_i = T_i * (sin(theta_front_i) + sin(theta_behind_i))

    Gate thresholds:
    - GREEN: total < 500 N (normal range)
    - YELLOW: 500 <= total < 700 N (heavy strings, monitor)
    - RED: total >= 700 N (excessive, risk of failure)
    """
    if len(payload.string_tensions_n) != len(payload.break_angles_deg):
        raise HTTPException(
            status_code=422,
            detail=f"Mismatched lengths: {len(payload.string_tensions_n)} tensions vs {len(payload.break_angles_deg)} break angles",
        )

    result = compute_saddle_force(
        string_tensions_n=payload.string_tensions_n,
        break_angles_deg=payload.break_angles_deg,
        body_depth_at_bridge_mm=payload.body_depth_at_bridge_mm,
        pin_to_tailblock_mm=payload.pin_to_tailblock_mm,
        string_names=payload.string_names,
    )

    return SaddleForceResponse(
        string_forces=[
            StringForceResponse(
                string_name=sf.string_name,
                tension_n=sf.tension_n,
                break_angle_deg=sf.break_angle_deg,
                behind_angle_deg=sf.behind_angle_deg,
                vertical_force_n=sf.vertical_force_n,
            )
            for sf in result.string_forces
        ],
        total_vertical_force_n=result.total_vertical_force_n,
        total_vertical_force_lbs=result.total_vertical_force_lbs,
        gate=result.gate,
        notes=result.notes,
    )


__all__ = ["router"]
