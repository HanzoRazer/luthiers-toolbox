"""
CAM Geometry Extraction from FretboardEcosphere

Sprint FRET-CONSOLIDATION-1 Commit 1: Bridge module connecting ecosphere
to existing CAM toolpath generation.

This module extracts CAM-ready geometry from the canonical FretboardEcosphere
document without duplicating any fret position math. The ecosphere contains
pre-computed, validated geometry; this module transforms it into the format
expected by existing CAM generators.

Architecture:
    FretboardEcosphere (canonical source)
           ↓
    extract_slot_geometry() / ecosphere_to_fretboard_spec()
           ↓
    Existing CAM generators (fret_slots_cam.py, fret_slots_fan_cam.py)

Rules:
    1. No fret math here — ecosphere already computed it
    2. Silent fallback forbidden — ValueError on invalid geometry
    3. Must handle both standard and multiscale transparently
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import List, Tuple, Optional

from ..instrument_geometry.neck.fretboard_ecosphere import (
    FretboardEcosphere,
    FretboardInput,
    FretLine,
    ScaleType,
)
from ..instrument_geometry.neck.neck_profiles import FretboardSpec


@dataclass(frozen=True)
class SlotGeometry:
    """CAM-ready geometry for a single fret slot.

    Extracted directly from FretLine without recomputation.
    """
    fret_number: int
    bass_point: Tuple[float, float]
    treble_point: Tuple[float, float]
    center_x_mm: float
    slot_width_mm: float
    angle_rad: float
    is_perpendicular: bool

    @property
    def slot_length_mm(self) -> float:
        """Length from bass to treble endpoint."""
        dx = self.treble_point[0] - self.bass_point[0]
        dy = self.treble_point[1] - self.bass_point[1]
        return sqrt(dx * dx + dy * dy)


def extract_slot_geometry(eco: FretboardEcosphere) -> List[SlotGeometry]:
    """Extract CAM slot geometry from ecosphere fret lines.

    Args:
        eco: Computed FretboardEcosphere document.

    Returns:
        List of SlotGeometry objects, one per fret (excluding nut).

    Raises:
        ValueError: If ecosphere has no fret lines or insufficient points.

    Notes:
        - Skips fret 0 (nut) — CAM only cuts frets 1+
        - Uses ecosphere's slot_width_mm from input_params
        - Preserves angle_rad and is_perpendicular for fan-fret handling
    """
    if not eco.fret_lines:
        raise ValueError("Ecosphere contains no fret lines")

    slot_width = eco.input_params.slot_width_mm
    slots: List[SlotGeometry] = []

    for fl in eco.fret_lines:
        if fl.fret_number == 0:
            continue  # Skip nut

        if len(fl.points) < 2:
            raise ValueError(
                f"Fret {fl.fret_number} has {len(fl.points)} points; "
                "minimum 2 required for CAM slot"
            )

        bass_pt = fl.points[0]
        treble_pt = fl.points[-1]

        slots.append(SlotGeometry(
            fret_number=fl.fret_number,
            bass_point=(bass_pt.x_mm, bass_pt.y_mm),
            treble_point=(treble_pt.x_mm, treble_pt.y_mm),
            center_x_mm=fl.center_x_mm,
            slot_width_mm=slot_width,
            angle_rad=fl.angle_rad,
            is_perpendicular=fl.is_perpendicular,
        ))

    return slots


def ecosphere_to_fretboard_spec(eco: FretboardEcosphere) -> FretboardSpec:
    """Convert ecosphere input params to legacy FretboardSpec.

    Enables backward compatibility with existing CAM generators that
    expect FretboardSpec. Use this adapter when refactoring CAM code
    to consume ecosphere incrementally.

    Args:
        eco: Computed FretboardEcosphere document.

    Returns:
        FretboardSpec populated from ecosphere input parameters.

    Notes:
        - Extracts radius from nested RadiusSpec
        - Uses actual computed heel_width if heel_width_mm was None in input
    """
    inp = eco.input_params

    # Extract radius values from RadiusSpec
    base_radius = inp.radius.nut_radius_mm
    end_radius = inp.radius.heel_radius_mm

    # Use computed heel width from ecosphere (handles None case in input)
    heel_width = inp.heel_width_mm
    if heel_width is None:
        heel_width = eco.max_width_mm  # Computed from default taper

    return FretboardSpec(
        nut_width_mm=inp.nut_width_mm,
        heel_width_mm=heel_width,
        scale_length_mm=inp.scale_length_mm,
        fret_count=inp.fret_count,
        base_radius_mm=base_radius,
        end_radius_mm=end_radius,
        extension_mm=inp.extension_mm,
    )


def is_fan_fret(eco: FretboardEcosphere) -> bool:
    """Check if ecosphere represents a fan-fret (multiscale) configuration.

    Args:
        eco: Computed FretboardEcosphere document.

    Returns:
        True if scale_type is MULTISCALE, False otherwise.
    """
    return eco.input_params.scale_type == ScaleType.MULTISCALE


def get_fan_fret_params(
    eco: FretboardEcosphere,
) -> Optional[Tuple[float, float, int]]:
    """Extract fan-fret parameters if ecosphere is multiscale.

    Args:
        eco: Computed FretboardEcosphere document.

    Returns:
        Tuple of (treble_scale_mm, bass_scale_mm, perpendicular_fret)
        if multiscale, None otherwise.
    """
    if not is_fan_fret(eco):
        return None

    inp = eco.input_params
    return (
        inp.scale_length_mm,        # treble scale
        inp.bass_scale_length_mm,   # bass scale
        inp.perpendicular_fret,
    )


def extract_slot_endpoints(
    eco: FretboardEcosphere,
) -> List[Tuple[int, Tuple[float, float], Tuple[float, float]]]:
    """Extract minimal slot endpoint data for G-code generation.

    Lightweight extraction when only fret number and endpoints are needed.

    Args:
        eco: Computed FretboardEcosphere document.

    Returns:
        List of (fret_number, bass_point, treble_point) tuples.

    Raises:
        ValueError: If ecosphere has no fret lines.
    """
    if not eco.fret_lines:
        raise ValueError("Ecosphere contains no fret lines")

    endpoints = []
    for fl in eco.fret_lines:
        if fl.fret_number == 0:
            continue
        if len(fl.points) < 2:
            continue  # Skip degenerate frets silently for endpoint extraction

        bass_pt = (fl.points[0].x_mm, fl.points[0].y_mm)
        treble_pt = (fl.points[-1].x_mm, fl.points[-1].y_mm)
        endpoints.append((fl.fret_number, bass_pt, treble_pt))

    return endpoints


def validate_ecosphere_for_cam(eco: FretboardEcosphere) -> None:
    """Validate ecosphere contains required geometry for CAM operations.

    Args:
        eco: FretboardEcosphere to validate.

    Raises:
        ValueError: With specific message if validation fails.

    Checks:
        - At least 1 fret line beyond nut
        - All fret lines have >= 2 points
        - slot_width_mm is positive
        - No NaN/inf in coordinates
    """
    if not eco.fret_lines:
        raise ValueError("Ecosphere has no fret lines")

    non_nut_frets = [fl for fl in eco.fret_lines if fl.fret_number > 0]
    if not non_nut_frets:
        raise ValueError("Ecosphere has no frets beyond nut (fret 0)")

    slot_width = eco.input_params.slot_width_mm
    if slot_width <= 0:
        raise ValueError(f"Invalid slot_width_mm: {slot_width}")

    import math
    for fl in eco.fret_lines:
        if fl.fret_number == 0:
            continue
        if len(fl.points) < 2:
            raise ValueError(
                f"Fret {fl.fret_number} has insufficient points "
                f"({len(fl.points)}); CAM requires at least 2"
            )
        for pt in fl.points:
            if math.isnan(pt.x_mm) or math.isinf(pt.x_mm):
                raise ValueError(
                    f"Fret {fl.fret_number} has invalid x_mm: {pt.x_mm}"
                )
            if math.isnan(pt.y_mm) or math.isinf(pt.y_mm):
                raise ValueError(
                    f"Fret {fl.fret_number} has invalid y_mm: {pt.y_mm}"
                )
