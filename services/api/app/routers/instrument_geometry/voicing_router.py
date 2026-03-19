"""
Voicing Router — Tap tone analysis and frequency prediction.

Endpoints:
- POST /voicing/analyze — Analyze voicing progress
- POST /voicing/predict — Predict frequency at target thickness
- GET  /voicing/targets/{body_style} — Get target frequencies
- GET  /voicing/stages — List build stages

Total: 4 endpoints
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.voicing_history_calc import (
    TapToneMeasurement,
    VoicingSession,
    analyze_voicing_progress,
    predict_final_frequency,
    get_target_frequencies,
    list_build_stages,
)

router = APIRouter(tags=["instrument-geometry", "voicing"])


# ─── Models ────────────────────────────────────────────────────────────────────

class TapToneMeasurementModel(BaseModel):
    """Single tap tone measurement."""
    stage: str = Field(..., description="Build stage")
    thickness_mm: float = Field(..., gt=0, description="Plate thickness in mm")
    tap_frequency_hz: float = Field(..., gt=0, description="Measured frequency in Hz")
    timestamp: str = Field(..., description="ISO format timestamp")
    notes: str = Field(default="", description="Optional notes (include 'top' or 'back')")


class VoicingSessionRequest(BaseModel):
    """Request for voicing analysis."""
    instrument_id: str = Field(..., description="Unique instrument identifier")
    top_species: str = Field(..., description="Top wood species")
    back_species: str = Field(..., description="Back wood species")
    body_style: str = Field(..., description="Body style (dreadnought, om_000, etc.)")
    measurements: List[TapToneMeasurementModel] = Field(..., description="List of tap tone measurements")
    target_top_hz: float = Field(..., gt=0, description="Target top frequency in Hz")
    target_back_hz: float = Field(..., gt=0, description="Target back frequency in Hz")


class VoicingReportResponse(BaseModel):
    """Response with voicing analysis."""
    instrument_id: str
    current_stage: str
    top_status: str
    back_status: str
    top_frequency_hz: Optional[float]
    back_frequency_hz: Optional[float]
    top_delta_hz: float
    back_delta_hz: float
    predicted_top_hz: Optional[float]
    predicted_back_hz: Optional[float]
    trend_slope: float
    gate: str
    notes: List[str]


class FrequencyPredictionRequest(BaseModel):
    """Request for frequency prediction."""
    current_thickness_mm: float = Field(..., gt=0, description="Current thickness in mm")
    current_frequency_hz: float = Field(..., gt=0, description="Current frequency in Hz")
    target_thickness_mm: float = Field(..., gt=0, description="Target thickness in mm")


class FrequencyPredictionResponse(BaseModel):
    """Response with predicted frequency."""
    current_thickness_mm: float
    current_frequency_hz: float
    target_thickness_mm: float
    predicted_frequency_hz: float


class TargetFrequenciesResponse(BaseModel):
    """Response with target frequencies for body style."""
    body_style: str
    top_hz: float
    back_hz: float


class BuildStagesResponse(BaseModel):
    """Response with list of build stages."""
    stages: List[str]


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/voicing/analyze",
    response_model=VoicingReportResponse,
    summary="Analyze voicing progress",
)
def analyze_voicing(req: VoicingSessionRequest) -> VoicingReportResponse:
    """Analyze voicing progress for an instrument."""
    measurements = [
        TapToneMeasurement(
            stage=m.stage,
            thickness_mm=m.thickness_mm,
            tap_frequency_hz=m.tap_frequency_hz,
            timestamp=m.timestamp,
            notes=m.notes,
        )
        for m in req.measurements
    ]
    session = VoicingSession(
        instrument_id=req.instrument_id,
        top_species=req.top_species,
        back_species=req.back_species,
        body_style=req.body_style,
        measurements=measurements,
        target_top_hz=req.target_top_hz,
        target_back_hz=req.target_back_hz,
    )
    report = analyze_voicing_progress(session)
    return VoicingReportResponse(**report.to_dict())


@router.post(
    "/voicing/predict",
    response_model=FrequencyPredictionResponse,
    summary="Predict frequency at target thickness",
)
def predict_voicing_frequency(req: FrequencyPredictionRequest) -> FrequencyPredictionResponse:
    """Predict frequency at target thickness."""
    predicted = predict_final_frequency(
        current_thickness_mm=req.current_thickness_mm,
        current_frequency_hz=req.current_frequency_hz,
        target_thickness_mm=req.target_thickness_mm,
    )
    return FrequencyPredictionResponse(
        current_thickness_mm=req.current_thickness_mm,
        current_frequency_hz=req.current_frequency_hz,
        target_thickness_mm=req.target_thickness_mm,
        predicted_frequency_hz=round(predicted, 1),
    )


@router.get(
    "/voicing/targets/{body_style}",
    response_model=TargetFrequenciesResponse,
    summary="Get target frequencies for body style",
)
def get_voicing_targets(body_style: str) -> TargetFrequenciesResponse:
    """Get typical target frequencies for a body style."""
    targets = get_target_frequencies(body_style)
    return TargetFrequenciesResponse(
        body_style=body_style,
        top_hz=targets["top"],
        back_hz=targets["back"],
    )


@router.get(
    "/voicing/stages",
    response_model=BuildStagesResponse,
    summary="List build stages for voicing",
)
def get_voicing_stages() -> BuildStagesResponse:
    """Return list of build stages in order."""
    return BuildStagesResponse(stages=list_build_stages())


__all__ = ["router"]
