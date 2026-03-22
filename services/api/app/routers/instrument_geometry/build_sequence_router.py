"""
Build Sequence Router — Complete build calculation sequence.

Endpoints:
- POST /build-sequence — Run complete build sequence
- GET  /build-sequence/options — List options

Total: 2 endpoints
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.build_sequence import (
    InstrumentType,
    BodyStyle,
    NeckJointType,
    create_dreadnought_spec,
    create_om_spec,
    create_classical_spec,
    run_build_sequence,
)

router = APIRouter(tags=["instrument-geometry", "build-sequence"])


# ─── Models ────────────────────────────────────────────────────────────────────

class BuildSequenceRequest(BaseModel):
    """Request for running a complete build sequence."""
    build_id: Optional[str] = Field(default=None, description="Unique build identifier")
    preset: str = Field(
        default="dreadnought",
        description="Preset type: dreadnought, om, classical"
    )
    scale_length_mm: Optional[float] = Field(default=None, gt=0)
    string_count: Optional[int] = Field(default=None, ge=4, le=12)
    fret_count: Optional[int] = Field(default=None, ge=12, le=36)
    top_species: Optional[str] = Field(default=None)
    back_species: Optional[str] = Field(default=None)
    finish_type: Optional[str] = Field(default=None)
    build_rh_pct: Optional[float] = Field(default=None, ge=0, le=100)
    target_rh_pct: Optional[float] = Field(default=None, ge=0, le=100)


class StageResultResponse(BaseModel):
    """Result of a single build stage."""
    stage_name: str
    status: str
    gate: str
    warnings: List[str] = []
    errors: List[str] = []
    duration_ms: Optional[float] = None


class BuildSequenceResponse(BaseModel):
    """Response from build sequence execution."""
    build_id: str
    overall_gate: str
    stages: Dict[str, StageResultResponse]
    warnings: List[str]
    errors: List[str]
    spec: Dict[str, Any]
    string_tension: Optional[Dict[str, Any]] = None
    bridge_geometry: Optional[Dict[str, Any]] = None
    wood_movement: Optional[Dict[str, Any]] = None
    finish_schedule: Optional[Dict[str, Any]] = None


class BuildSequenceOptionsResponse(BaseModel):
    """Available options for build sequence configuration."""
    presets: List[str]
    instrument_types: List[str]
    body_styles: List[str]
    neck_joint_types: List[str]


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/build-sequence",
    response_model=BuildSequenceResponse,
    summary="Run complete build calculation sequence (CONSTRUCTION-010)",
)
def run_build_sequence_endpoint(req: BuildSequenceRequest) -> BuildSequenceResponse:
    """
    Execute the complete build calculation sequence.

    Runs all calculation stages in order:
    - String tension
    - Bridge geometry
    - Wood movement
    - Finish schedule

    Each stage reads from and writes to the shared BuildSpec state.
    """
    # Create spec from preset
    if req.preset.lower() == "om":
        spec = create_om_spec(req.build_id)
    elif req.preset.lower() == "classical":
        spec = create_classical_spec(req.build_id)
    else:
        spec = create_dreadnought_spec(req.build_id)

    # Apply overrides from request
    if req.scale_length_mm is not None:
        spec.scale_length_mm = req.scale_length_mm
    if req.string_count is not None:
        spec.string_count = req.string_count
    if req.fret_count is not None:
        spec.fret_count = req.fret_count
    if req.top_species is not None:
        spec.top_species = req.top_species
    if req.back_species is not None:
        spec.back_species = req.back_species
    if req.finish_type is not None:
        spec.finish_type = req.finish_type
    if req.build_rh_pct is not None:
        spec.build_rh_pct = req.build_rh_pct
    if req.target_rh_pct is not None:
        spec.target_rh_pct = req.target_rh_pct

    # Run the sequence
    result = run_build_sequence(spec)

    # Build stage responses
    stage_responses = {}
    for name, stage_result in result.stages.items():
        stage_responses[name] = StageResultResponse(
            stage_name=stage_result.stage_name,
            status=stage_result.status.value,
            gate=stage_result.gate,
            warnings=stage_result.warnings,
            errors=stage_result.errors,
            duration_ms=stage_result.duration_ms,
        )

    def _safe_to_dict(obj: Any) -> Optional[Dict[str, Any]]:
        """Convert object to dict using to_dict() or asdict() as fallback."""
        if obj is None:
            return None
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        try:
            return asdict(obj)
        except (TypeError, ValueError):
            return None

    return BuildSequenceResponse(
        build_id=result.spec.build_id,
        overall_gate=result.overall_gate,
        stages=stage_responses,
        warnings=result.warnings,
        errors=result.errors,
        spec=result.spec.to_dict(),
        string_tension=_safe_to_dict(result.string_tension),
        bridge_geometry=_safe_to_dict(result.bridge_geometry),
        wood_movement=_safe_to_dict(result.wood_movement),
        finish_schedule=_safe_to_dict(result.finish_schedule),
    )


@router.get(
    "/build-sequence/options",
    response_model=BuildSequenceOptionsResponse,
    summary="List options for build sequence configuration",
)
def get_build_sequence_options() -> BuildSequenceOptionsResponse:
    """Return available presets and options for build sequence."""
    return BuildSequenceOptionsResponse(
        presets=["dreadnought", "om", "classical"],
        instrument_types=[t.value for t in InstrumentType],
        body_styles=[s.value for s in BodyStyle],
        neck_joint_types=[j.value for j in NeckJointType],
    )


__all__ = ["router"]
