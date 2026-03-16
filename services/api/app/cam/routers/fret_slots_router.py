"""
Fret Slots Router

Fret slot preview endpoint for guitar neck CAM operations.
Extracted from stub_routes.py during decomposition.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.instrument_geometry import load_model_spec
from app.instrument_geometry.neck.neck_profiles import FretboardSpec
from app.calculators.fret_slots_cam import generate_fret_slot_toolpaths, compute_cam_statistics
from app.rmos.context import RmosContext


router = APIRouter(tags=["cam", "fret-slots"])


class FretSlotsPreviewRequest(BaseModel):
    """Request for fret slot preview."""
    model_id: str
    fret_count: int = Field(22, ge=1, le=36)
    slot_width_mm: float = Field(0.58, gt=0, le=2.0)
    slot_depth_mm: float = Field(3.0, gt=0, le=10.0)
    bit_diameter_mm: float = Field(0.58, gt=0, le=10.0)
    mode: Optional[str] = Field("standard", pattern="^(standard|fan_fret)$")
    perpendicular_fret: Optional[int] = None
    bass_scale_mm: Optional[float] = None
    treble_scale_mm: Optional[float] = None


class FretSlotOut(BaseModel):
    """Single fret slot data."""
    fret: int
    stringIndex: int = 0
    positionMm: float
    widthMm: float
    depthMm: float
    angleRad: Optional[float] = None
    isPerpendicular: bool = False


class RmosMessageOut(BaseModel):
    """RMOS validation message."""
    code: str
    severity: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    hint: Optional[str] = None


class FretSlotsPreviewResponse(BaseModel):
    """Response for fret slot preview."""
    model_id: str
    fret_count: int
    slots: List[FretSlotOut]
    messages: List[RmosMessageOut]
    statistics: Optional[Dict[str, Any]] = None


@router.post("/fret_slots/preview")
def preview_fret_slots(req: FretSlotsPreviewRequest) -> FretSlotsPreviewResponse:
    """Preview fret slot positions using real calculator."""
    messages: List[RmosMessageOut] = []

    try:
        model_spec = load_model_spec(req.model_id)
        scale_length_mm = model_spec.scale.scale_length_mm
        nut_width_mm = 42.0
        heel_width_mm = 56.0
    except (FileNotFoundError, KeyError, ValueError, TypeError, AttributeError):
        messages.append(RmosMessageOut(
            code="MODEL_NOT_FOUND",
            severity="warning",
            message=f"Model '{req.model_id}' not found, using defaults",
            context={"model_id": req.model_id},
            hint="Check model registry for available model IDs",
        ))
        scale_length_mm = 648.0
        nut_width_mm = 42.0
        heel_width_mm = 56.0

    spec = FretboardSpec(
        nut_width_mm=nut_width_mm,
        heel_width_mm=heel_width_mm,
        scale_length_mm=scale_length_mm,
        fret_count=req.fret_count,
    )

    context = RmosContext(model_id=req.model_id, model_spec={})

    try:
        toolpaths = generate_fret_slot_toolpaths(
            spec=spec,
            context=context,
            slot_depth_mm=req.slot_depth_mm,
            slot_width_mm=req.slot_width_mm,
        )
        statistics = compute_cam_statistics(toolpaths)
    except (ValueError, TypeError, KeyError, AttributeError, ZeroDivisionError) as e:
        messages.append(RmosMessageOut(
            code="CALCULATION_ERROR",
            severity="error",
            message=f"Fret slot calculation failed: {str(e)}",
            context={},
        ))
        toolpaths = []
        statistics = None

    slots = [
        FretSlotOut(
            fret=tp.fret_number,
            positionMm=tp.position_mm,
            widthMm=tp.width_mm,
            depthMm=tp.slot_depth_mm,
            angleRad=tp.angle_rad if hasattr(tp, 'angle_rad') else None,
            isPerpendicular=tp.is_perpendicular if hasattr(tp, 'is_perpendicular') else False,
        )
        for tp in toolpaths
    ]

    if req.bit_diameter_mm > req.slot_width_mm * 1.5:
        messages.append(RmosMessageOut(
            code="BIT_TOO_LARGE",
            severity="warning",
            message=f"Bit diameter ({req.bit_diameter_mm}mm) exceeds slot width ({req.slot_width_mm}mm)",
            context={"bit_diameter_mm": req.bit_diameter_mm, "slot_width_mm": req.slot_width_mm},
            hint="Use a smaller bit or increase slot width",
        ))

    if req.slot_depth_mm > 5.0:
        messages.append(RmosMessageOut(
            code="SLOT_DEPTH_HIGH",
            severity="info",
            message=f"Slot depth ({req.slot_depth_mm}mm) is deeper than typical (2.5-3.5mm)",
            context={"slot_depth_mm": req.slot_depth_mm},
        ))

    return FretSlotsPreviewResponse(
        model_id=req.model_id,
        fret_count=req.fret_count,
        slots=slots,
        messages=messages,
        statistics=statistics,
    )
