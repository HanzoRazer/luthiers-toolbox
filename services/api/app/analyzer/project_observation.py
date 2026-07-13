# services/api/app/analyzer/project_observation.py
"""
Analyzer → Project Spine observation mapping (SPINE-002).

Maps a completed Analyzer ``InterpretationResult`` into the canonical
``AnalyzerObservation`` schema defined by ADR-002 (the Instrument Project Graph).

Boundary (ADR-002 + ADR-004):
    - The Analyzer OWNS interpretation content, confidence, run identity, evidence.
    - The Project Spine OWNS association, append-only storage, canonical serialization.
    - Writing an observation is ADVISORY. It confers no geometry, material, CAM, or
      RMOS/manufacturing authority, and never overrides spec / bridge_state /
      material_selection / manufacturing_state.

This module contains mapping + validation ONLY. It performs no persistence and no HTTP.
Persistence goes through ``app.projects.service.append_analyzer_observation``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..schemas.instrument_project import AnalyzerObservation
from .schemas import InterpretationResult

# Keys an interpretation mode-dict may use for its frequency; tried in order.
_FREQUENCY_KEYS = ("frequency_hz", "freq_hz", "frequency", "freq", "hz")


def validate_analyzer_observation_source(
    interpretation: InterpretationResult,
    run_id: str,
) -> None:
    """
    Validate that the required identity/provenance for a canonical observation is
    actually present. Raises ``ValueError`` on a missing required fact — never fabricates.

    Required (per ``AnalyzerObservation``): ``run_id``, ``specimen_id``, ``observed_at``.
    """
    if not run_id or not run_id.strip():
        raise ValueError("run_id is required and must be a non-empty measurement/run identifier.")
    if not interpretation.specimen_id or not interpretation.specimen_id.strip():
        raise ValueError("interpretation.specimen_id is required and must be non-empty.")
    if not interpretation.interpreted_at or not interpretation.interpreted_at.strip():
        raise ValueError("interpretation.interpreted_at is required (maps to observed_at).")


def _extract_mode_frequencies(primary_modes: List[Dict[str, Any]]) -> List[float]:
    """
    Extract modal frequencies (Hz) from the interpretation's loose ``primary_modes``
    dicts. Tolerant: tries known frequency keys, skips entries without a numeric one.
    Never invents a value.
    """
    frequencies: List[float] = []
    for mode in primary_modes or []:
        if not isinstance(mode, dict):
            continue
        for key in _FREQUENCY_KEYS:
            value = mode.get(key)
            if value is None:
                continue
            try:
                frequencies.append(float(value))
            except (TypeError, ValueError):
                continue
            break
    return frequencies


def build_analyzer_observation(
    interpretation: InterpretationResult,
    run_id: str,
    *,
    wsi: Optional[float] = None,
    interpretation_confidence: float = 0.0,
) -> AnalyzerObservation:
    """
    Map a completed ``InterpretationResult`` + an explicit ``run_id`` into a canonical
    ``AnalyzerObservation``.

    ``run_id`` is supplied by the caller (the measurement/RMOS run id) — it is NOT
    present on ``InterpretationResult`` and must never be inferred. ``wsi`` (from the
    input viewer-pack's wolf metrics) and ``interpretation_confidence`` are optional and
    only carried when the caller supplies them; absent provenance is left empty, not
    fabricated.
    """
    validate_analyzer_observation_source(interpretation, run_id)

    findings = [r.message for r in interpretation.recommendations if getattr(r, "message", None)]
    reference_instrument = next(
        (r.reference_instrument for r in interpretation.recommendations if r.reference_instrument),
        None,
    )
    # The interpretation's human-readable wolf assessment is advisory finding text.
    if interpretation.wolf_assessment:
        findings = [interpretation.wolf_assessment, *findings]

    return AnalyzerObservation(
        run_id=run_id.strip(),
        specimen_id=interpretation.specimen_id.strip(),
        observed_at=interpretation.interpreted_at.strip(),
        primary_modes_hz=_extract_mode_frequencies(interpretation.primary_modes),
        wsi=wsi,
        tonal_character=interpretation.tonal_character,
        findings=findings,
        reference_instrument=reference_instrument,
        interpretation_confidence=interpretation_confidence,
    )
