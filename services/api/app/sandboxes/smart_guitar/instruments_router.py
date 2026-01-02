"""
Smart Guitar Instruments Router (SG-SBX-0.1)
============================================

Design truth endpoints for Smart Guitar.
Mounted at: /api/instruments/smart-guitar/*
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from .planner import generate_plan
from .presets import standard_all
from .schemas import SmartGuitarSpec, PlanError, PlanWarning
from .validators import validate_spec


router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class ValidateResponse(BaseModel):
    """Validation response with errors, warnings, and normalized spec."""
    ok: bool
    warnings: List[dict]
    errors: List[dict]
    normalized_spec: SmartGuitarSpec


class InfoResponse(BaseModel):
    """Model info response."""
    model_id: str
    contract_version: str
    variants: List[str]
    handedness: List[str]
    notes: List[str]


class PresetsResponse(BaseModel):
    """Presets response."""
    contract_version: str
    presets: dict


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/info", response_model=InfoResponse)
def info():
    """
    Get Smart Guitar model information.
    
    Returns model metadata including available variants and handedness options.
    """
    return InfoResponse(
        model_id="smart_guitar",
        contract_version="1.0",
        variants=["headed", "headless"],
        handedness=["RH", "LH"],
        notes=[
            "Sandbox-local (Option C).",
            "Instruments router is design truth; CAM router is projection.",
        ],
    )


@router.get("/presets/standard", response_model=PresetsResponse)
def presets_standard():
    """
    Get standard presets for both headed and headless variants.
    
    Returns fully configured specs with all required electronics components.
    """
    presets = standard_all()
    return PresetsResponse(
        contract_version="1.0",
        presets={k: v.model_dump() for k, v in presets.items()},
    )


@router.post("/spec/validate", response_model=ValidateResponse)
def spec_validate(spec: SmartGuitarSpec):
    """
    Validate a Smart Guitar specification.
    
    Checks:
    - Body dimension constraints (rim, skin, spine)
    - Hollow/pod depth budgets
    - Required electronics components
    - Thermal configuration
    
    Returns:
        Validation result with ok flag, errors, warnings, and normalized spec
    """
    errors, warnings, normalized = validate_spec(spec)
    return ValidateResponse(
        ok=(len(errors) == 0),
        warnings=[w.model_dump() for w in warnings],
        errors=[e.model_dump() for e in errors],
        normalized_spec=normalized,
    )


@router.post("/cam/plan")
def cam_plan(spec: SmartGuitarSpec):
    """
    Generate a CAM plan from a specification.
    
    This is a convenience endpoint on the instruments router.
    The canonical CAM endpoint is at /api/cam/smart-guitar/plan.
    
    Returns:
        SmartCamPlan with cavities, brackets, channels, and toolpath ops
    """
    plan = generate_plan(spec)
    return plan.model_dump()
