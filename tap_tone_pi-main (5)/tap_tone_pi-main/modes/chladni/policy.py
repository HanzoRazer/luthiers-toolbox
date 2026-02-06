"""Chladni frequency mismatch policy — tolerance checks and enrichment.

Frequency Mismatch Policy (G.2):
  - Warn + keep if delta_hz > 0
  - FAIL if delta_hz > CHLADNI_FREQ_TOLERANCE_HZ (default 5.0 Hz)
"""
from __future__ import annotations

import os

# Frequency mismatch tolerance (Hz) - configurable via environment
CHLADNI_FREQ_TOLERANCE_HZ = float(os.getenv("CHLADNI_FREQ_TOLERANCE_HZ", "5.0"))


def attach_pattern_record(rec: dict, detected_peaks_hz: list[float]) -> float:
    """
    Enrich pattern record with nearest detected peak and delta.
    Returns delta_hz for policy evaluation.
    """
    freq_hz = rec["freq_hz"]
    image_freq_tag_hz = rec.get("image_freq_tag_hz", freq_hz)

    # Find nearest detected peak
    nearest = None
    if detected_peaks_hz:
        nearest = float(min(detected_peaks_hz, key=lambda p: abs(p - freq_hz)))

    # Compute delta from image tag to nearest detected peak
    delta = abs(image_freq_tag_hz - (nearest if nearest is not None else freq_hz))

    rec["nearest_detected_hz"] = nearest
    rec["delta_hz"] = round(delta, 4)

    # Add warning if mismatch detected
    if delta > 0:
        rec.setdefault("_warnings", []).append(f"freq_mismatch: delta_hz={delta:.2f}")

    return delta


def finalize_run(
    chladni_run: dict, tolerance_hz: float = CHLADNI_FREQ_TOLERANCE_HZ
) -> None:
    """
    Finalize chladni_run with policy checks.
    Raises SystemExit(2) if worst delta exceeds tolerance.
    """
    patterns = chladni_run.get("patterns", [])
    worst = max((p.get("delta_hz") or 0.0) for p in patterns) if patterns else 0.0

    # Record policy metadata
    chladni_run.setdefault("_policy", {})
    chladni_run["_policy"]["freq_tolerance_hz"] = tolerance_hz
    chladni_run["_policy"]["worst_delta_hz"] = worst

    # Check tolerance
    if worst > tolerance_hz:
        chladni_run.setdefault("_errors", []).append(
            f"max delta_hz {worst:.2f} exceeds tolerance {tolerance_hz:.2f}"
        )
        raise SystemExit(2)
