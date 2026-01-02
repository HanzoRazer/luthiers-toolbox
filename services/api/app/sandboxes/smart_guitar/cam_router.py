"""
Smart Guitar CAM Router (SG-SBX-0.1)
====================================

Manufacturing projection endpoints for Smart Guitar.
Mounted at: /api/cam/smart-guitar/*
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from .planner import generate_plan
from .schemas import SmartGuitarSpec


router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class TemplatesResponse(BaseModel):
    """Available CAM templates response."""
    cavities: List[str]
    brackets: List[str]
    channels: List[str]
    notes: List[str]


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/templates", response_model=TemplatesResponse)
def templates():
    """
    Get available CAM template IDs.
    
    v0.1: Returns known template ids.
    Future: Will return geometry parameters.
    """
    return TemplatesResponse(
        cavities=[
            "cavity_bass_main_v1",
            "cavity_treble_main_v1",
            "cavity_tail_wing_v1",
            "pod_rh_v1",
            "pod_lh_v1",
        ],
        brackets=[
            "bracket_pi5_v1",
            "bracket_arduino_uno_r4_v1",
            "bracket_hifiberry_dac_adc_v1",
            "bracket_battery_pack_v1",
            "bracket_fan_40mm_v1",
        ],
        channels=[
            "wire_routes_rh_v1",
            "wire_routes_lh_v1",
            "drill_passages_rh_v1",
            "drill_passages_lh_v1",
        ],
        notes=["Templates are intent-level in v0.1; no DXF export yet."],
    )


@router.post("/plan")
def plan(spec: SmartGuitarSpec):
    """
    Generate a CAM plan from a Smart Guitar specification.
    
    The plan includes:
    - Cavity definitions with depths and template references
    - Bracket mounting templates for each electronics component
    - Wire channel routes (routed and drilled)
    - Toolpath operations with conservative defaults
    
    Returns:
        SmartCamPlan with all manufacturing data, plus validation warnings/errors
    """
    return generate_plan(spec).model_dump()


@router.get("/health")
def health():
    """CAM subsystem health check."""
    return {
        "ok": True,
        "subsystem": "smart_guitar_cam",
        "model_id": "smart_guitar",
        "contract_version": "1.0",
        "capabilities": [
            "plan",
            "templates",
        ],
        "notes": ["v0.1: Intent-level planning. DXF export pending."],
    }
