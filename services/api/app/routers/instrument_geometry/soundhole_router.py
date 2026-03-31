"""
Soundhole Router — Soundhole specification, position validation, and spiral geometry.

Endpoints:
- POST /soundhole — Calculate soundhole spec (supports round, oval, spiral, fhole types)
- POST /soundhole/check-position — Check soundhole position validity
- GET  /soundhole/options — List body styles
- GET  /soundhole/body-styles — List body styles with standard diameters
- GET  /soundhole/types — List supported soundhole types
- POST /soundhole/spiral/geometry — Compute dual-spiral geometry (JSON)
- POST /soundhole/spiral/dxf — Export dual-spiral DXF
- POST /soundhole/spiral/validate — Validate dual-spiral spec
- GET  /soundhole/spiral/default — Default Carlos Jumbo dual-spiral spec

Total: 9 endpoints
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from app.calculators.soundhole_calc import (
    SoundholeSpec,
    compute_soundhole_spec,
    check_soundhole_position,
    list_body_styles,
    STANDARD_DIAMETERS_MM,
)
from app.calculators.soundhole_facade import (
    SoundholeType,
    SpiralParams,
    list_soundhole_types,
)
from app.calculators.soundhole_presets import (
    list_spiral_presets,
    SPIRAL_PRESETS,
)
from app.instrument_geometry.soundhole.spiral_geometry import (
    SpiralSpec,
    DualSpiralSpec,
    compute_dual_geometry,
    generate_dxf,
    default_carlos_jumbo_spec,
    dual_geo_to_dict,
    spec_to_dict,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["instrument-geometry", "soundhole"])


# ─── Models ────────────────────────────────────────────────────────────────────

class SpiralParamsRequest(BaseModel):
    """Parameters for spiral soundhole geometry."""
    slot_width_mm: float = Field(14.0, ge=8.0, le=30.0, description="Slot width in mm (14-20mm optimal)")
    start_radius_mm: float = Field(10.0, ge=5.0, le=25.0, description="Starting radius r0 in mm")
    growth_rate_k: float = Field(0.18, ge=0.05, le=0.40, description="Growth rate k per radian")
    turns: float = Field(1.1, ge=0.5, le=2.5, description="Number of full turns")
    rotation_deg: float = Field(0.0, ge=0.0, le=360.0, description="Rotation offset in degrees")
    center_x_mm: float = Field(0.0, description="Center X position (mm from centerline)")
    center_y_mm: float = Field(0.0, description="Center Y position (mm from bridge)")


class SoundholeRequest(BaseModel):
    """Request for soundhole specification."""
    body_style: str = Field(..., description="Body style (dreadnought, om_000, parlor, classical, etc.)")
    body_length_mm: float = Field(..., gt=0, description="Body length from neck block to tail block in mm")
    custom_diameter_mm: Optional[float] = Field(None, gt=0, description="Custom diameter override in mm")
    soundhole_type: str = Field(
        "round",
        description="Soundhole type: round, oval, spiral, or fhole"
    )
    spiral_params: Optional[SpiralParamsRequest] = Field(
        None,
        description="Parameters for spiral soundhole (only used when soundhole_type='spiral')"
    )


class SoundholeResponse(BaseModel):
    """Response with soundhole specification."""
    diameter_mm: float
    position_from_neck_block_mm: float
    body_style: str
    gate: str
    notes: List[str]
    soundhole_type: str = "round"
    spiral_params: Optional[Dict] = None
    area_mm2: Optional[float] = None
    perimeter_mm: Optional[float] = None
    pa_ratio_mm_inv: Optional[float] = None


class SoundholePositionCheckRequest(BaseModel):
    """Request to check soundhole position validity."""
    diameter_mm: float = Field(..., gt=0, description="Soundhole diameter in mm")
    position_mm: float = Field(..., gt=0, description="Position from neck block in mm")
    body_length_mm: float = Field(..., gt=0, description="Body length in mm")


class SoundholePositionCheckResponse(BaseModel):
    """Response with position check result."""
    gate: str
    diameter_mm: float
    position_mm: float
    body_length_mm: float


class SoundholeOptionsResponse(BaseModel):
    """Response with supported body styles."""
    body_styles: List[str]


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/soundhole",
    response_model=SoundholeResponse,
    summary="Calculate soundhole specification",
)
def calculate_soundhole(req: SoundholeRequest) -> SoundholeResponse:
    """
    Calculate soundhole specification for body style.

    Supports multiple soundhole types:
    - round: Traditional circular soundhole (default)
    - oval: Oval/elliptical (Selmer/Maccaferri style)
    - spiral: Logarithmic spiral slot (Williams 2019 acoustic research)
    - fhole: F-holes (redirects to f-hole calculator)
    """
    # Parse soundhole type
    try:
        sh_type = SoundholeType(req.soundhole_type.lower())
    except ValueError:
        sh_type = SoundholeType.ROUND

    # Convert spiral params if provided
    spiral_params = None
    if req.spiral_params and sh_type == SoundholeType.SPIRAL:
        spiral_params = SpiralParams(
            slot_width_mm=req.spiral_params.slot_width_mm,
            start_radius_mm=req.spiral_params.start_radius_mm,
            growth_rate_k=req.spiral_params.growth_rate_k,
            turns=req.spiral_params.turns,
            rotation_deg=req.spiral_params.rotation_deg,
            center_x_mm=req.spiral_params.center_x_mm,
            center_y_mm=req.spiral_params.center_y_mm,
        )

    spec: SoundholeSpec = compute_soundhole_spec(
        body_style=req.body_style,
        body_length_mm=req.body_length_mm,
        custom_diameter_mm=req.custom_diameter_mm,
        soundhole_type=sh_type,
        spiral_params=spiral_params,
    )
    return SoundholeResponse(**spec.to_dict())


@router.post(
    "/soundhole/check-position",
    response_model=SoundholePositionCheckResponse,
    summary="Check soundhole position validity",
)
def check_soundhole_position_endpoint(req: SoundholePositionCheckRequest) -> SoundholePositionCheckResponse:
    """Check if soundhole position is valid."""
    gate = check_soundhole_position(
        diameter_mm=req.diameter_mm,
        position_mm=req.position_mm,
        body_length_mm=req.body_length_mm,
    )
    return SoundholePositionCheckResponse(
        gate=gate,
        diameter_mm=req.diameter_mm,
        position_mm=req.position_mm,
        body_length_mm=req.body_length_mm,
    )


@router.get(
    "/soundhole/options",
    response_model=SoundholeOptionsResponse,
    summary="List supported body styles for soundhole calculation",
)
def get_soundhole_options() -> SoundholeOptionsResponse:
    """Return list of supported body styles."""
    return SoundholeOptionsResponse(body_styles=list_body_styles())


@router.get(
    "/soundhole/body-styles",
    summary="List body styles with standard soundhole diameters",
)
def list_soundhole_body_styles():
    """
    List supported body styles and their standard soundhole diameters.

    Migrated from instrument_router.py — provides extended response
    with standard_diameters_mm lookup table.
    """
    return {
        "body_styles": list_body_styles(),
        "standard_diameters_mm": STANDARD_DIAMETERS_MM,
    }


@router.get(
    "/soundhole/types",
    summary="List supported soundhole types",
)
def get_soundhole_types():
    """
    List supported soundhole types for the generator dropdown.

    Returns available types: round, oval, spiral, fhole
    with descriptions and any type-specific notes.
    """
    return {
        "types": list_soundhole_types(),
        "spiral_presets": list_spiral_presets(),
    }


# ─── Spiral request/response models ──────────────────────────────────────────

class SpiralSpecRequest(BaseModel):
    center_x_mm: float = Field(..., ge=-250, le=250, description="X position of spiral center (mm)")
    center_y_mm: float = Field(..., ge=-250, le=300, description="Y position of spiral center (mm)")
    start_radius_mm: float = Field(..., ge=3.0, le=40.0, description="Inner starting radius r0 (mm)")
    growth_rate_k: float = Field(..., ge=0.02, le=0.60, description="Logarithmic growth rate k per radian")
    turns: float = Field(..., ge=0.25, le=3.0, description="Number of full turns")
    slot_width_mm: float = Field(..., ge=4.0, le=30.0, description="Slot width (mm)")
    rotation_deg: float = Field(..., ge=0.0, le=360.0, description="Rotation offset of spiral start (degrees)")
    label: str = Field(default="", max_length=64)

    @field_validator("growth_rate_k")
    @classmethod
    def k_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("growth_rate_k must be positive")
        return v

    @field_validator("slot_width_mm")
    @classmethod
    def slot_width_acoustic_note(cls, v):
        if v < 10.0:
            logger.warning(
                "slot_width_mm=%.1f is below Williams 2019 optimum range (14-20mm). "
                "P:A will be higher but area will be very small.", v
            )
        return v


class DualSpiralRequest(BaseModel):
    upper: SpiralSpecRequest
    lower: SpiralSpecRequest
    body_type: str = Field(default="carlos_jumbo", max_length=64)
    notes: str = Field(default="", max_length=256)

    class Config:
        json_schema_extra = {
            "example": {
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                    "label": "Upper bass-side spiral"
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 90.0,
                    "label": "Lower treble-side spiral"
                },
                "body_type": "carlos_jumbo",
                "notes": "Displaced f-hole logic with logarithmic spiral geometry"
            }
        }


def _request_to_spec(req: SpiralSpecRequest) -> SpiralSpec:
    return SpiralSpec(
        center_x_mm=req.center_x_mm,
        center_y_mm=req.center_y_mm,
        start_radius_mm=req.start_radius_mm,
        growth_rate_k=req.growth_rate_k,
        turns=req.turns,
        slot_width_mm=req.slot_width_mm,
        rotation_deg=req.rotation_deg,
        label=req.label,
    )


def _request_to_dual(req: DualSpiralRequest) -> DualSpiralSpec:
    return DualSpiralSpec(
        upper=_request_to_spec(req.upper),
        lower=_request_to_spec(req.lower),
        body_type=req.body_type,
        notes=req.notes,
    )


# ─── Spiral endpoints ────────────────────────────────────────────────────────

@router.get(
    "/soundhole/spiral/default",
    summary="Default Carlos Jumbo dual-spiral specification",
)
def get_spiral_default():
    """
    Return the default Carlos Jumbo dual-spiral specification.
    Use as a starting point for the designer.
    """
    spec = default_carlos_jumbo_spec()
    return {
        "upper": spec_to_dict(spec.upper),
        "lower": spec_to_dict(spec.lower),
        "body_type": spec.body_type,
        "notes": spec.notes,
    }


@router.post(
    "/soundhole/spiral/geometry",
    summary="Compute dual-spiral soundhole geometry",
)
def compute_spiral_geometry_endpoint(req: DualSpiralRequest):
    """
    Compute dual-spiral soundhole geometry.

    Returns centerline points, wall points, area, perimeter,
    P:A ratio, and acoustic analysis for both spirals.

    P:A note: For a constant-width spiral slot, P:A = 2/slot_width_mm.
    This is independent of k, turns, and overall size.
    Target P:A > 0.10 mm⁻¹ for significant acoustic efficiency gain
    over a round hole (Williams 2019, mwguitars.com.au).
    """
    try:
        dual_spec = _request_to_dual(req)
        dual_geo = compute_dual_geometry(dual_spec)
        result = dual_geo_to_dict(dual_geo)

        u_pa = dual_geo.upper.pa_ratio_mm_inv
        l_pa = dual_geo.lower.pa_ratio_mm_inv

        def pa_verdict(pa):
            if pa >= 0.10:
                return "above_threshold"
            elif pa >= 0.08:
                return "approaching_threshold"
            else:
                return "below_threshold"

        result["acoustic_verdict"] = {
            "upper": pa_verdict(u_pa),
            "lower": pa_verdict(l_pa),
            "recommendation": (
                "Both spirals above Williams threshold — good acoustic efficiency."
                if u_pa >= 0.10 and l_pa >= 0.10
                else "Increase slot width or check geometry — one or both spirals below P:A threshold."
            )
        }

        logger.info(
            "Spiral geometry computed: upper area=%.1f mm² P:A=%.3f | "
            "lower area=%.1f mm² P:A=%.3f | total=%.1f mm²",
            dual_geo.upper.area_mm2, u_pa,
            dual_geo.lower.area_mm2, l_pa,
            dual_geo.total_area_mm2,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Spiral geometry computation failed")
        raise HTTPException(status_code=500, detail=f"Geometry computation failed: {e}")


@router.post(
    "/soundhole/spiral/dxf",
    summary="DXF R2000 export of dual-spiral soundhole",
)
async def export_spiral_dxf(req: DualSpiralRequest):
    """
    Generate a DXF R2000 file for the dual-spiral soundhole.

    DXF layers:
      SPIRAL_OUTER_WALL  — CNC cut path
      SPIRAL_INNER_WALL  — CNC cut path
      SPIRAL_CENTERLINE  — reference only
      BODY_REFERENCE     — body outline reference
      BRACE_KEEPOUT      — brace zone reference

    Coordinate system: origin at bridge centerline, mm units.
    """
    try:
        dual_spec = _request_to_dual(req)

        with tempfile.NamedTemporaryFile(
            suffix=".dxf",
            delete=False,
            prefix="spiral_soundhole_"
        ) as tmp:
            tmp_path = tmp.name

        generate_dxf(dual_spec, tmp_path)

        filename = f"spiral_soundhole_{req.body_type}.dxf"

        return FileResponse(
            path=tmp_path,
            filename=filename,
            media_type="application/dxf",
            background=None,
        )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("DXF generation failed")
        raise HTTPException(status_code=500, detail=f"DXF generation failed: {e}")


@router.post(
    "/soundhole/spiral/validate",
    summary="Validate dual-spiral soundhole spec",
)
def validate_spiral_spec(req: DualSpiralRequest):
    """
    Validate a dual-spiral spec without computing full geometry.
    Returns warnings about structural or acoustic concerns.
    """
    warnings = []
    info = []

    for label, spec in [("upper", req.upper), ("lower", req.lower)]:
        pa = 2.0 / spec.slot_width_mm
        if pa < 0.08:
            warnings.append(
                f"{label}: P:A = {pa:.3f} mm⁻¹ — below Williams threshold. "
                f"Increase slot width above {2/0.08:.0f}mm or this shape has no acoustic advantage over round."
            )
        elif pa < 0.10:
            warnings.append(
                f"{label}: P:A = {pa:.3f} mm⁻¹ — approaching threshold. "
                f"Narrow slot slightly to cross 0.10."
            )
        else:
            info.append(
                f"{label}: P:A = {pa:.3f} mm⁻¹ — above threshold. "
                f"Williams 2019 data supports +60% efficiency gain."
            )

        if spec.slot_width_mm < 10.0:
            warnings.append(
                f"{label}: slot_width_mm={spec.slot_width_mm} is narrow. "
                "Minimum practical CNC cut on spruce is approximately 8-10mm."
            )

        if spec.growth_rate_k > 0.35:
            warnings.append(
                f"{label}: growth_rate_k={spec.growth_rate_k} is high — "
                "spiral expands very rapidly, may not conform to bout radius."
            )

    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "info": info,
    }


__all__ = ["router"]
