# services/api/app/blueprint/project_writer.py
"""
Blueprint Project Writer (BLUE-001/002)

Maps the outputs of the 4-phase Blueprint pipeline into BlueprintDerivedGeometry
and writes it into the Instrument Project Graph.

This module is the bridge between:
    Blueprint pipeline (Phase 1 AI → Phase 1.5 Calibration → Phase 2 Vectorization → Phase 4 Dimension Linking)
and:
    InstrumentProjectData.blueprint_geometry (Layer 0 project state)

Pipeline output mapping:
    Phase 1  analysis.blueprint_type / detected_model  → instrument_classification
    Phase 1  analysis.scale_confidence                 → confidence
    Phase 1.5 DimensionResponse.scale_length_inches    → scale_length_detected_mm
    Phase 1.5 DimensionResponse.body_length_mm         → body_length_mm
    Phase 1.5 DimensionResponse.lower/upper_bout_*     → lower_bout_mm, upper_bout_mm
    Phase 3  body_size_mm                              → body_length_mm / lower_bout_mm fallback
    instrument_geometry/body/centerline.py             → centerline_x_mm, symmetry, symmetry_score
    body_size_mm width / 2                             → centerline_x_mm (fallback, symmetric assumption)

Provenance rules:
    - source is always recorded (photo | dxf | manual)
    - confidence 0-1 comes from the best available signal
    - blueprint_original preserves pre-override values when source becomes MANUAL

See docs/PLATFORM_ARCHITECTURE.md — Layer 2 / Blueprint.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..schemas.instrument_project import (
    BlueprintDerivedGeometry,
    BlueprintSource,
    BodySymmetry,
)

logger = logging.getLogger(__name__)

# Instrument type string normalisation: maps blueprint_type/detected_model
# strings from Phase 1 AI into the canonical InstrumentCategory values.
_CLASSIFICATION_MAP: Dict[str, str] = {
    # Electric guitar variations
    "electric": "electric_guitar",
    "electric_guitar": "electric_guitar",
    "electric guitar": "electric_guitar",
    "stratocaster": "electric_guitar",
    "telecaster": "electric_guitar",
    "les paul": "electric_guitar",
    "les_paul": "electric_guitar",
    "sg": "electric_guitar",
    # Acoustic guitar variations
    "acoustic": "acoustic_guitar",
    "acoustic_guitar": "acoustic_guitar",
    "acoustic guitar": "acoustic_guitar",
    "steel string": "acoustic_guitar",
    "dreadnought": "acoustic_guitar",
    "om": "acoustic_guitar",
    "parlor": "acoustic_guitar",
    # Other families
    "archtop": "archtop",
    "classical": "classical",
    "classical guitar": "classical",
    "nylon string": "classical",
    "bass": "bass",
    "electric bass": "bass",
    "violin": "violin",
    "viola": "violin",
    "mandolin": "mandolin",
    "ukulele": "ukulele",
    "uke": "ukulele",
    "banjo": "banjo",
}


def _normalise_classification(raw: Optional[str]) -> Optional[str]:
    """Map Phase 1 blueprint_type/detected_model to InstrumentCategory value."""
    if not raw:
        return None
    key = raw.lower().strip()
    return _CLASSIFICATION_MAP.get(key)


def _parse_confidence(analysis: Dict[str, Any]) -> float:
    """
    Extract best available confidence from Phase 1 analysis dict.

    Phase 1 AI returns:
      analysis.scale_confidence  — string like "high" | "medium" | "low" | float string
      analysis.dimensions[].confidence  — per-dimension confidence

    Returns float 0.0-1.0.
    """
    conf_raw = analysis.get("scale_confidence", "")
    if isinstance(conf_raw, (int, float)):
        return float(min(max(conf_raw, 0.0), 1.0))
    if isinstance(conf_raw, str):
        mapping = {"high": 0.85, "medium": 0.60, "low": 0.35, "": 0.0}
        lower = conf_raw.lower().strip()
        if lower in mapping:
            return mapping[lower]
        try:
            return float(min(max(float(lower), 0.0), 1.0))
        except ValueError:
            return 0.0
    return 0.0


def _compute_centerline_simple(body_width_mm: Optional[float]) -> Tuple[Optional[float], BodySymmetry, float]:
    """
    Simple symmetric centerline: width / 2.

    Used when no body outline point list is available.
    Returns (centerline_x_mm, symmetry, symmetry_score).
    """
    if not body_width_mm or body_width_mm <= 0:
        return None, BodySymmetry.UNKNOWN, 0.0
    return body_width_mm / 2.0, BodySymmetry.SYMMETRIC, 0.7


def _compute_centerline_from_outline(
    outline: List[Tuple[float, float]],
) -> Tuple[float, BodySymmetry, float]:
    """
    Compute centerline using instrument_geometry/body/centerline.py when
    a body outline coordinate list is available.

    Returns (centerline_x_mm, symmetry, symmetry_score).
    """
    try:
        from ..instrument_geometry.body.centerline import (
            compute_body_centerline,
            BodySymmetry as _BS,
        )
        result = compute_body_centerline(outline, assume_symmetric=True)
        symmetry_map = {
            _BS.SYMMETRIC: BodySymmetry.SYMMETRIC,
            _BS.ASYMMETRIC: BodySymmetry.ASYMMETRIC,
            _BS.OFFSET: BodySymmetry.OFFSET,
            _BS.UNKNOWN: BodySymmetry.UNKNOWN,
        }
        return (
            result.centerline_x_mm,
            symmetry_map.get(result.symmetry, BodySymmetry.UNKNOWN),
            result.symmetry_score,
        )
    except Exception as exc:  # audited: project-write-best-effort
        logger.warning("Centerline computation failed, using simple fallback: %s", exc)
        return 0.0, BodySymmetry.UNKNOWN, 0.0


def build_blueprint_derived_geometry(
    *,
    # Phase 1 outputs
    analysis_result: Optional[Dict[str, Any]] = None,
    # Phase 1.5 outputs
    calibration_result: Optional[Dict[str, Any]] = None,
    dimension_result: Optional[Dict[str, Any]] = None,
    # Phase 3 outputs
    phase3_body_size_mm: Optional[Dict[str, float]] = None,
    # Phase 4 outputs
    phase4_linked_dimensions: Optional[List[Dict[str, Any]]] = None,
    # Body outline points (if extracted from vectorizer)
    body_outline_mm: Optional[List[Tuple[float, float]]] = None,
    # Provenance
    source: BlueprintSource = BlueprintSource.PHOTO,
) -> BlueprintDerivedGeometry:
    """
    Build BlueprintDerivedGeometry from pipeline phase outputs.

    Collects the best available values from each phase, falls back gracefully
    when phases are missing or unavailable.

    Args:
        analysis_result:   Phase 1 AI output (analysis dict from AnalysisResponse)
        calibration_result: Phase 1.5 calibration output dict
        dimension_result:  Phase 1.5 DimensionResponse dict
        phase3_body_size_mm: Phase 3 body_size_mm dict {"width": x, "height": y}
        phase4_linked_dimensions: Phase 4 linked dimensions list
        body_outline_mm:   Optional body outline as [(x,y)...] in mm
        source:            BlueprintSource enum

    Returns:
        BlueprintDerivedGeometry ready to write into InstrumentProjectData
    """
    notes: List[str] = []
    analysis = analysis_result or {}

    # --- Confidence ---
    confidence = _parse_confidence(analysis)

    # --- Instrument classification ---
    blueprint_type = analysis.get("blueprint_type") or analysis.get("detected_model")
    instrument_classification = _normalise_classification(blueprint_type)
    if blueprint_type and not instrument_classification:
        notes.append(f"Unknown instrument classification from AI: '{blueprint_type}'")

    # --- Scale length ---
    scale_length_detected_mm: Optional[float] = None
    if dimension_result:
        sl_inches = dimension_result.get("scale_length_inches")
        if sl_inches:
            scale_length_detected_mm = round(float(sl_inches) * 25.4, 2)
            notes.append(f"Scale length detected: {scale_length_detected_mm}mm")

    # --- Body dimensions — prefer calibration DimensionResponse, fallback Phase 3 ---
    body_length_mm: Optional[float] = None
    lower_bout_mm: Optional[float] = None
    upper_bout_mm: Optional[float] = None
    waist_mm: Optional[float] = None

    if dimension_result:
        body_length_mm = dimension_result.get("body_length_mm")
        lower_bout_w = dimension_result.get("lower_bout_width_inches")
        upper_bout_w = dimension_result.get("upper_bout_width_inches")
        waist_w = dimension_result.get("waist_width_inches")
        if lower_bout_w:
            lower_bout_mm = round(float(lower_bout_w) * 25.4, 1)
        if upper_bout_w:
            upper_bout_mm = round(float(upper_bout_w) * 25.4, 1)
        if waist_w:
            waist_mm = round(float(waist_w) * 25.4, 1)

    # Fallback to Phase 3 body_size_mm
    if phase3_body_size_mm:
        if not body_length_mm:
            body_length_mm = phase3_body_size_mm.get("height") or phase3_body_size_mm.get("body_length")
        if not lower_bout_mm:
            lower_bout_mm = phase3_body_size_mm.get("width") or phase3_body_size_mm.get("lower_bout")
        if body_length_mm or lower_bout_mm:
            notes.append("Body dimensions from Phase 3 vectorizer.")

    # --- Centerline computation ---
    centerline_x_mm: Optional[float] = None
    axis_angle_deg: float = 0.0
    symmetry = BodySymmetry.UNKNOWN
    symmetry_score = 0.0

    if body_outline_mm and len(body_outline_mm) >= 6:
        centerline_x_mm, symmetry, symmetry_score = _compute_centerline_from_outline(body_outline_mm)
        notes.append(f"Centerline computed from outline ({len(body_outline_mm)} points). Symmetry: {symmetry.value} ({symmetry_score:.2f})")
    elif lower_bout_mm:
        centerline_x_mm, symmetry, symmetry_score = _compute_centerline_simple(lower_bout_mm)
        notes.append(f"Centerline estimated from lower bout width ({lower_bout_mm}mm). Assumed symmetric.")
    else:
        notes.append("Centerline unavailable — no outline or body width detected.")

    # --- Phase 4 dimension extraction ---
    if phase4_linked_dimensions:
        linked_count = len(phase4_linked_dimensions)
        notes.append(f"Phase 4 linked {linked_count} dimension(s) to geometry features.")

    return BlueprintDerivedGeometry(
        source=source,
        confidence=round(confidence, 3),
        body_outline_mm=body_outline_mm,
        centerline_x_mm=round(centerline_x_mm, 2) if centerline_x_mm is not None else None,
        axis_angle_deg=round(axis_angle_deg, 2),
        symmetry=symmetry,
        symmetry_score=round(symmetry_score, 3),
        body_length_mm=round(body_length_mm, 1) if body_length_mm else None,
        lower_bout_mm=round(lower_bout_mm, 1) if lower_bout_mm else None,
        upper_bout_mm=round(upper_bout_mm, 1) if upper_bout_mm else None,
        waist_mm=round(waist_mm, 1) if waist_mm else None,
        scale_length_detected_mm=scale_length_detected_mm,
        instrument_classification=instrument_classification,
        captured_at=datetime.now(timezone.utc).isoformat(),
        notes=notes,
        blueprint_original=None,   # Set by caller when overriding existing geometry
    )


def apply_manual_override(
    existing: BlueprintDerivedGeometry,
    override_fields: Dict[str, Any],
) -> BlueprintDerivedGeometry:
    """
    Apply a manual user override to BlueprintDerivedGeometry.

    Preserves the original pipeline-derived geometry in `blueprint_original`
    so the provenance of every edit is traceable.

    Args:
        existing:        Current BlueprintDerivedGeometry in project state
        override_fields: Dict of field names → new values to apply

    Returns:
        Updated BlueprintDerivedGeometry with source=MANUAL and blueprint_original set.
    """
    # Preserve original on first manual override
    if existing.source != BlueprintSource.MANUAL:
        original_data = existing.model_dump(mode="json", exclude={"blueprint_original"})
    else:
        # Already manual — keep the original baseline
        original_data = existing.blueprint_original

    updated = existing.model_copy(
        update={
            **override_fields,
            "source": BlueprintSource.MANUAL,
            "blueprint_original": original_data,
        }
    )
    return updated
