"""
Wave 7: Instrument Geometry Router

Exposes endpoints for guitar instrument geometry calculations:
- Bridge location with compensation
- Compound radius profiles
- Standard guitar presets (convenience endpoints)

NOTE: Fret-specific endpoints (positions, outline, slots) moved to fret_router.py (December 2025)
See: /api/fret/table, /api/fret/board/outline, /api/fret/slots

All calculations use the instrument_geometry package.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

# Canonical imports (updated from shims - December 2025)
from ..instrument_geometry.neck.fret_math import compute_fret_positions_mm
from ..instrument_geometry.bridge.geometry import (
    compute_bridge_location_mm,
    compute_compensation_estimate,
)
from ..instrument_geometry.neck.radius_profiles import (
    compute_compound_radius_at_fret,
)

router = APIRouter(
    prefix="/api/instrument",
    tags=["instrument_geometry"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
# NOTE: Fret-related models moved to fret_router.py (December 2025)
# See: /api/fret/table, /api/fret/board/outline, /api/fret/slots
# ---------------------------------------------------------------------------

class BridgeLocationRequest(BaseModel):
    """Request for bridge saddle location."""
    scale_length_mm: float = Field(..., gt=0)
    saddle_compensation_mm: Optional[float] = Field(
        default=None, 
        description="Manual compensation offset (positive = further from nut)"
    )
    string_gauge_mm: Optional[float] = Field(
        default=None,
        description="String gauge for automatic compensation calculation"
    )
    action_height_mm: Optional[float] = Field(
        default=None,
        description="Action height at 12th fret for compensation"
    )


class BridgeLocationResponse(BaseModel):
    """Response with bridge location details."""
    scale_length_mm: float
    bridge_location_mm: float
    compensation_mm: float
    notes: str


class RadiusProfileRequest(BaseModel):
    """Request for compound radius profile."""
    fret_count: int = Field(..., gt=0, le=36)
    base_radius_mm: float = Field(..., gt=0, description="Radius at nut (e.g., 184mm = 7.25 inch)")
    end_radius_mm: float = Field(..., gt=0, description="Radius at last fret (e.g., 305mm = 12 inch)")


class RadiusProfileResponse(BaseModel):
    """Response with radius at each fret position."""
    radii_mm: List[float]
    base_radius_mm: float
    end_radius_mm: float
    is_compound: bool


class RadiusAtPositionRequest(BaseModel):
    """Request for radius at arbitrary position."""
    position_mm: float = Field(..., ge=0, description="Distance from nut in mm")
    fretboard_length_mm: float = Field(..., gt=0)
    base_radius_mm: float = Field(..., gt=0)
    end_radius_mm: float = Field(..., gt=0)


class RadiusAtPositionResponse(BaseModel):
    """Response with interpolated radius."""
    position_mm: float
    radius_mm: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
# NOTE: Fret endpoints moved to fret_router.py (December 2025)
# - /geometry/frets → /api/fret/table
# - /geometry/fretboard → /api/fret/board/outline
# - /geometry/fret-slots → /api/fret/slots
# ---------------------------------------------------------------------------

@router.post("/geometry/bridge", response_model=BridgeLocationResponse)
def get_bridge_location(payload: BridgeLocationRequest) -> BridgeLocationResponse:
    """
    Calculate bridge saddle location with compensation.
    
    Compensation can be:
    - Manual: provided via saddle_compensation_mm
    - Automatic: calculated from string_gauge_mm and action_height_mm
    - Default: uses basic scale length (no compensation)
    """
    base_location = compute_bridge_location_mm(scale_length_mm=payload.scale_length_mm)
    
    compensation = 0.0
    notes = "No compensation applied"
    
    if payload.saddle_compensation_mm is not None:
        compensation = payload.saddle_compensation_mm
        notes = f"Manual compensation: {compensation:.2f}mm"
    elif payload.string_gauge_mm is not None and payload.action_height_mm is not None:
        # Use compute_compensation_estimate for automatic calculation
        compensation = compute_compensation_estimate(
            string_gauge_mm=payload.string_gauge_mm,
            action_mm=payload.action_height_mm,
            scale_length_mm=payload.scale_length_mm,
        )
        notes = f"Calculated compensation for {payload.string_gauge_mm}mm string, {payload.action_height_mm}mm action"
    
    return BridgeLocationResponse(
        scale_length_mm=payload.scale_length_mm,
        bridge_location_mm=base_location + compensation,
        compensation_mm=compensation,
        notes=notes,
    )


@router.post("/geometry/radius-profile", response_model=RadiusProfileResponse)
def get_radius_profile(payload: RadiusProfileRequest) -> RadiusProfileResponse:
    """
    Calculate compound radius profile for all fret positions.
    
    Returns the fretboard radius at each fret, interpolated linearly
    from base_radius (at nut) to end_radius (at last fret).
    """
    radii: List[float] = []
    for fret_index in range(payload.fret_count):
        r = compute_compound_radius_at_fret(
            fret_index=fret_index,
            total_frets=payload.fret_count,
            start_radius_mm=payload.base_radius_mm,
            end_radius_mm=payload.end_radius_mm,
        )
        radii.append(r)

    is_compound = abs(payload.base_radius_mm - payload.end_radius_mm) > 0.1

    return RadiusProfileResponse(
        radii_mm=radii,
        base_radius_mm=payload.base_radius_mm,
        end_radius_mm=payload.end_radius_mm,
        is_compound=is_compound,
    )


@router.post("/geometry/radius-at-position", response_model=RadiusAtPositionResponse)
def get_radius_at_position(payload: RadiusAtPositionRequest) -> RadiusAtPositionResponse:
    """
    Calculate fretboard radius at any arbitrary position.
    
    Useful for CNC operations that need radius at specific X coordinates
    rather than at fret positions.
    """
    # Linear interpolation of radius based on position
    ratio = payload.position_mm / payload.fretboard_length_mm
    ratio = max(0.0, min(1.0, ratio))  # Clamp to [0, 1]
    
    radius = payload.base_radius_mm + (payload.end_radius_mm - payload.base_radius_mm) * ratio
    
    return RadiusAtPositionResponse(
        position_mm=payload.position_mm,
        radius_mm=radius,
    )


# ---------------------------------------------------------------------------
# Convenience endpoints for common use cases
# ---------------------------------------------------------------------------

class StandardGuitarRequest(BaseModel):
    """Request using standard guitar presets."""
    preset: str = Field(
        ..., 
        description="Preset name: 'fender_25.5', 'gibson_24.75', 'prs_25', 'classical'"
    )
    fret_count: int = Field(default=22, gt=0, le=36)


class StandardGuitarResponse(BaseModel):
    """Complete geometry for a standard guitar configuration."""
    preset: str
    scale_length_mm: float
    fret_count: int
    nut_width_mm: float
    frets_mm: List[float]
    bridge_location_mm: float


# Standard guitar presets
GUITAR_PRESETS = {
    "fender_25.5": {
        "scale_length_mm": 647.7,  # 25.5 inches
        "nut_width_mm": 42.86,     # 1 11/16 inches
        "heel_width_mm": 56.0,
    },
    "gibson_24.75": {
        "scale_length_mm": 628.65,  # 24.75 inches
        "nut_width_mm": 43.05,      # 1.695 inches
        "heel_width_mm": 55.0,
    },
    "prs_25": {
        "scale_length_mm": 635.0,   # 25 inches
        "nut_width_mm": 42.5,
        "heel_width_mm": 55.5,
    },
    "classical": {
        "scale_length_mm": 650.0,
        "nut_width_mm": 52.0,
        "heel_width_mm": 62.0,
    },
}


@router.post("/geometry/standard-guitar", response_model=StandardGuitarResponse)
def get_standard_guitar_geometry(payload: StandardGuitarRequest) -> StandardGuitarResponse:
    """
    Get complete geometry for a standard guitar preset.
    
    Available presets:
    - fender_25.5: Fender-style 25.5" scale
    - gibson_24.75: Gibson-style 24.75" scale  
    - prs_25: PRS-style 25" scale
    - classical: Classical guitar 650mm scale
    """
    preset_key = payload.preset.lower().replace(" ", "_")
    
    if preset_key not in GUITAR_PRESETS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown preset: {payload.preset}. Available: {list(GUITAR_PRESETS.keys())}"
        )
    
    preset = GUITAR_PRESETS[preset_key]
    
    frets = compute_fret_positions_mm(
        scale_length_mm=preset["scale_length_mm"],
        fret_count=payload.fret_count,
    )
    
    bridge = compute_bridge_location_mm(scale_length_mm=preset["scale_length_mm"])
    
    return StandardGuitarResponse(
        preset=payload.preset,
        scale_length_mm=preset["scale_length_mm"],
        fret_count=payload.fret_count,
        nut_width_mm=preset["nut_width_mm"],
        frets_mm=frets,
        bridge_location_mm=bridge,
    )


@router.get("/geometry/presets")
def list_presets():
    """List available guitar presets."""
    return {
        "presets": list(GUITAR_PRESETS.keys()),
        "details": GUITAR_PRESETS,
    }
