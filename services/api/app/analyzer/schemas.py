"""
Analyzer schemas — Types for viewer_pack consumption and interpretation output.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# INPUT: viewer_pack_v1 (from tap_tone_pi)
# ============================================================================

class PeakData(BaseModel):
    """A detected frequency peak from FFT analysis."""
    frequency_hz: float
    amplitude_db: float
    phase_deg: Optional[float] = None
    damping_ratio: Optional[float] = None


class TransferFunctionPoint(BaseModel):
    """Single point in H(f) transfer function."""
    frequency_hz: float
    magnitude_db: float
    phase_deg: float
    coherence: float  # γ²(f), 0-1


class WolfMetrics(BaseModel):
    """Wolf tone susceptibility metrics."""
    wsi: float = Field(..., description="Wolf Susceptibility Index, 0-1")
    wsi_frequency_hz: Optional[float] = None
    wsi_bandwidth_hz: Optional[float] = None


class ModeShape(BaseModel):
    """Modal shape data for visualization."""
    mode_index: int
    frequency_hz: float
    damping_ratio: float
    shape_coefficients: List[float]  # For rendering


class ViewerPackV1(BaseModel):
    """
    The contract between tap_tone_pi and luthiers-toolbox.

    This is the ONLY input we accept from tap_tone_pi.
    We NEVER import tap_tone_pi code.
    """
    schema_version: str = "viewer_pack_v1"
    measurement_only: bool = True
    interpretation: str = "deferred"  # Deferred to US

    # Metadata
    specimen_id: str
    capture_timestamp: str
    capture_device: Optional[str] = None

    # Measurement data (tap_tone_pi's job to populate)
    peaks: List[PeakData] = []
    transfer_function: List[TransferFunctionPoint] = []
    wolf_metrics: Optional[WolfMetrics] = None
    mode_shapes: List[ModeShape] = []

    # Raw data references (SHA256 of attachments)
    spectrum_csv_sha256: Optional[str] = None
    audio_wav_sha256: Optional[str] = None


# ============================================================================
# OUTPUT: Interpretation (our job)
# ============================================================================

class RecommendationSeverity(str, Enum):
    INFO = "info"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    CRITICAL = "critical"


class DesignRecommendation(BaseModel):
    """A design recommendation based on measurement interpretation."""
    severity: RecommendationSeverity
    category: str  # "bracing", "thickness", "material", etc.
    message: str
    details: Optional[str] = None
    reference_instrument: Optional[str] = None  # e.g., "Martin D-28 1937"


class InterpretationResult(BaseModel):
    """The output of our interpretation layer."""
    specimen_id: str
    interpreted_at: str

    # What we figured out
    primary_modes: List[Dict[str, Any]]  # Identified modal frequencies
    wolf_assessment: Optional[str] = None  # Human-readable wolf analysis
    tonal_character: Optional[str] = None  # "bright", "warm", "balanced"

    # What to do about it
    recommendations: List[DesignRecommendation] = []

    # Comparison to reference (if requested)
    reference_comparison: Optional[Dict[str, Any]] = None


class AppendObservationRequest(BaseModel):
    """
    Request to append a completed interpretation to a project as an advisory
    AnalyzerObservation (SPINE-002 — ADR-002 enrichment edge).

    ``run_id`` is the explicit measurement/RMOS run identifier (not present on the
    interpretation; never inferred). ``wsi`` (from the source viewer-pack's wolf metrics)
    and ``interpretation_confidence`` are optional provenance carried only when supplied.
    """
    interpretation: InterpretationResult
    run_id: str = Field(..., description="Explicit measurement/RMOS run identifier.")
    wsi: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Wolf Susceptibility Index from the source viewer-pack, if available.",
    )
    interpretation_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Confidence in the interpretation (0-1); advisory only.",
    )


class SpectrumDisplayData(BaseModel):
    """Data formatted for UI spectrum visualization."""
    frequencies_hz: List[float]
    magnitudes_db: List[float]
    peak_markers: List[Dict[str, float]]  # [{freq, mag, label}]
    coherence_overlay: Optional[List[float]] = None
