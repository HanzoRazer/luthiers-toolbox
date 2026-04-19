"""
Scale Validation Gate — Pre-Export Dimension Check

Validates that extracted body dimensions are plausible before DXF export.
Catches scale errors (2.5× too large, 0.7× too small) that would otherwise
produce incorrect CAM output without warning.

Integration point: Called BEFORE export_to_dxf(), after dimensions are computed.

Usage:
    violation = validate_scale_before_export(
        width_mm=output_size_mm[0],
        height_mm=output_size_mm[1],
        spec_name="gibson_explorer",
    )
    if violation:
        # Set export_blocked=True on response, include violation message
        ...

Spec data source: instrument_geometry/instrument_specs.py (single source of truth)

Author: Production Shop
Date: 2026-04-14
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from ..instrument_geometry.instrument_specs import BODY_DIMENSIONS, get_body_dimensions

logger = logging.getLogger(__name__)

# Generic bounds when spec_name is not found or not provided
# (w_min, w_max, h_min, h_max) in mm
# These are intentionally wide — they catch extreme errors but allow
# instruments outside the known spec list to pass through.
GENERIC_BOUNDS_MM: Tuple[float, float, float, float] = (150.0, 700.0, 200.0, 900.0)

# Tolerance for spec-based validation (±20%)
SPEC_TOLERANCE = 0.20


def get_body_bounds(spec_name: Optional[str]) -> Tuple[float, float, float, float]:
    """
    Get (w_min, w_max, h_min, h_max) bounds for a spec.

    If spec_name is found, returns tight bounds (±SPEC_TOLERANCE).
    Otherwise returns GENERIC_BOUNDS_MM.

    Args:
        spec_name: Instrument spec name (e.g., "gibson_explorer", "dreadnought")

    Returns:
        Tuple of (width_min, width_max, height_min, height_max) in mm
    """
    if not spec_name:
        return GENERIC_BOUNDS_MM

    body = get_body_dimensions(spec_name)
    if body is None:
        logger.debug(f"Spec '{spec_name}' not found, using generic bounds")
        return GENERIC_BOUNDS_MM

    # body_length_mm = height, lower_bout_width_mm = width (max body width)
    height_mm = body.body_length_mm
    width_mm = body.lower_bout_width_mm

    # Apply tolerance
    w_min = width_mm * (1 - SPEC_TOLERANCE)
    w_max = width_mm * (1 + SPEC_TOLERANCE)
    h_min = height_mm * (1 - SPEC_TOLERANCE)
    h_max = height_mm * (1 + SPEC_TOLERANCE)

    return (w_min, w_max, h_min, h_max)


def validate_scale_before_export(
    width_mm: float,
    height_mm: float,
    spec_name: Optional[str] = None,
) -> Optional[str]:
    """
    Validate that extracted dimensions are plausible before DXF export.

    This is a hard correctness gate — a dimension outside bounds indicates
    a scale extraction error that would produce incorrect CAM output.

    Args:
        width_mm: Extracted body width in mm
        height_mm: Extracted body height in mm
        spec_name: Optional instrument spec name for tight validation

    Returns:
        None if validation passes.
        Error message string if validation fails (export should be blocked).

    Examples:
        # Cuatro extracted at 2.5× scale
        >>> validate_scale_before_export(524, 951, "cuatro")
        "Height 951mm outside expected range 300-450mm for cuatro"

        # Explorer extracted at 0.7× scale
        >>> validate_scale_before_export(302, 419, "gibson_explorer")
        "Width 302mm outside expected range 384-576mm for gibson_explorer"

        # Valid extraction
        >>> validate_scale_before_export(480, 475, "gibson_explorer")
        None
    """
    w_min, w_max, h_min, h_max = get_body_bounds(spec_name)
    spec_label = spec_name or "unknown"

    # Log the validation attempt
    logger.info(
        f"Scale validation: {width_mm:.0f}×{height_mm:.0f}mm vs "
        f"bounds w=[{w_min:.0f}-{w_max:.0f}] h=[{h_min:.0f}-{h_max:.0f}] "
        f"for {spec_label}"
    )

    # Check width first (the Explorer failure case)
    if not (w_min <= width_mm <= w_max):
        msg = (
            f"Width {width_mm:.0f}mm outside expected range "
            f"{w_min:.0f}-{w_max:.0f}mm for {spec_label}"
        )
        logger.warning(f"Scale validation FAILED: {msg}")
        return msg

    # Check height
    if not (h_min <= height_mm <= h_max):
        msg = (
            f"Height {height_mm:.0f}mm outside expected range "
            f"{h_min:.0f}-{h_max:.0f}mm for {spec_label}"
        )
        logger.warning(f"Scale validation FAILED: {msg}")
        return msg

    logger.info("Scale validation PASSED")
    return None


def compute_scale_correction(
    width_mm: float,
    height_mm: float,
    spec_name: Optional[str] = None,
) -> Tuple[float, str]:
    """
    Compute correction factor to bring dimensions into expected range.

    This is a recovery path when validation fails — it suggests what
    scale correction would fix the error, but does NOT auto-apply it.

    Args:
        width_mm: Extracted body width in mm
        height_mm: Extracted body height in mm
        spec_name: Optional instrument spec name

    Returns:
        Tuple of (correction_factor, explanation_message)
        correction_factor is multiplicative (e.g., 0.4 means divide by 2.5)
    """
    body = get_body_dimensions(spec_name) if spec_name else None

    if body:
        expected_h = body.body_length_mm
        expected_w = body.lower_bout_width_mm
    else:
        # Use midpoint of generic bounds as target
        expected_w = (GENERIC_BOUNDS_MM[0] + GENERIC_BOUNDS_MM[1]) / 2
        expected_h = (GENERIC_BOUNDS_MM[2] + GENERIC_BOUNDS_MM[3]) / 2

    # Average the width and height correction factors
    w_correction = expected_w / width_mm if width_mm > 0 else 1.0
    h_correction = expected_h / height_mm if height_mm > 0 else 1.0
    correction = (w_correction + h_correction) / 2

    explanation = (
        f"Extracted {width_mm:.0f}×{height_mm:.0f}mm, "
        f"expected ~{expected_w:.0f}×{expected_h:.0f}mm. "
        f"Suggested correction: {correction:.3f}× "
        f"(multiply mm_per_px by {correction:.3f})"
    )

    return (correction, explanation)


# For testing: allow cache reset (no-op now that we use Python module, kept for API compat)
def _reset_cache() -> None:
    pass
