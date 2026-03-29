# String Tension Router - Migrated from instrument_router.py (2026-03-29)
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from ...calculators.string_tension import (
    StringSpec as StringSpecCalc,
    compute_set_tension,
    get_preset_set,
    list_preset_sets,
    SCALE_LENGTHS_MM,
)
from ...calculators.saddle_force_calc import (
    compute_saddle_force,
)

router = APIRouter(tags=["string-tension"])


class StringSpecRequest(BaseModel):
    name: str = Field(..., description="String name")
    gauge_inch: float = Field(..., gt=0)
    is_wound: bool
    note: str
    frequency_hz: float = Field(..., gt=0)


class StringTensionRequest(BaseModel):
    scale_length_mm: float = Field(..., gt=0)
    string_set: Optional[str] = None
    custom_strings: Optional[List[StringSpecRequest]] = None


class StringTensionResponse(BaseModel):
    scale_length_mm: float
    set_name: str
    strings: List[dict]
    total_tension_lb: float
    total_tension_n: float


class SaddleForceRequest(BaseModel):
    string_tensions_n: List[float] = Field(..., min_length=1, max_length=12)
    break_angles_deg: List[float] = Field(..., min_length=1, max_length=12)
    body_depth_at_bridge_mm: float = Field(default=100.0, gt=0)
    pin_to_tailblock_mm: float = Field(default=250.0, gt=0)
    string_names: Optional[List[str]] = None


class StringForceResponse(BaseModel):
    string_name: str
    tension_n: float
    break_angle_deg: float
    behind_angle_deg: float
    vertical_force_n: float


class SaddleForceResponse(BaseModel):
    string_forces: List[StringForceResponse]
    total_vertical_force_n: float
    total_vertical_force_lbs: float
    gate: str
    notes: List[str]


@router.post("/string-tension", response_model=StringTensionResponse)
def calculate_string_tension(payload: StringTensionRequest) -> StringTensionResponse:
    if payload.custom_strings:
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
        try:
            strings = get_preset_set(payload.string_set)
            set_name = payload.string_set
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
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


@router.get("/string-tension/presets")
def list_string_presets():
    return {
        "string_sets": list_preset_sets(),
        "scale_lengths_mm": SCALE_LENGTHS_MM,
    }


@router.post("/saddle-force", response_model=SaddleForceResponse)
def calculate_saddle_force(payload: SaddleForceRequest) -> SaddleForceResponse:
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
