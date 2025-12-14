"""
specs.py

Typed dataclasses for instrument model specifications.

JSON presets are defined in INCHES; this module provides
inch → mm helpers so the rest of the system can work in mm.

Wave 19 Module - Fan-Fret CAM Foundation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


INCH_TO_MM = 25.4


def inch_to_mm(value_in: float) -> float:
    """Convert inches to millimeters."""
    return value_in * INCH_TO_MM


# ---------------------------------------------------------------------------
# Scale specifications
# ---------------------------------------------------------------------------


@dataclass
class MultiScaleSpec:
    """
    Reserved for future multiscale (fanned-fret) instruments.

    All values in inches. Use properties to access mm.
    """
    bass_scale_length_in: float
    treble_scale_length_in: float
    fan_start_fret: int

    @property
    def bass_scale_length_mm(self) -> float:
        return inch_to_mm(self.bass_scale_length_in)

    @property
    def treble_scale_length_mm(self) -> float:
        return inch_to_mm(self.treble_scale_length_in)


@dataclass
class ScaleSpec:
    """
    Single-scale specification for a fretted instrument.

    JSON stores inches; properties expose mm.
    """
    scale_length_in: float
    num_frets: int
    joint_fret: Optional[int] = None
    fingerboard_overhang_frets: int = 0

    # Optional multiscale extension: if set, callers may choose to
    # treat this as a fanned-fret instrument instead of single-scale.
    multiscale: Optional[MultiScaleSpec] = None

    @property
    def scale_length_mm(self) -> float:
        return inch_to_mm(self.scale_length_in)


# ---------------------------------------------------------------------------
# Neck joint / pocket / bridge specs
# ---------------------------------------------------------------------------


@dataclass
class NeckJointSpec:
    """
    Neck joint geometry, in inches in the underlying JSON.

    The mm properties make it convenient for geometry/CAM code.
    """
    type: str  # e.g. "mortise_tenon", "dovetail", "bolt_on"
    body_join_fret: int
    pocket_depth_in: float
    pocket_length_in: float
    pocket_width_in: float
    heel_thickness_in: float
    neck_angle_degrees: float

    @property
    def pocket_depth_mm(self) -> float:
        return inch_to_mm(self.pocket_depth_in)

    @property
    def pocket_length_mm(self) -> float:
        return inch_to_mm(self.pocket_length_in)

    @property
    def pocket_width_mm(self) -> float:
        return inch_to_mm(self.pocket_width_in)

    @property
    def heel_thickness_mm(self) -> float:
        return inch_to_mm(self.heel_thickness_in)


@dataclass
class BridgeSpec:
    """
    Bridge / saddle configuration.

    Any length values are in inches in the JSON.
    """
    type: str  # e.g. "floating_archtop", "fixed_tom", "tele_plate"
    reference_line: str  # e.g. "theoretical_scale_length"
    saddle_profile: Optional[str] = None
    # Optional raw inches offset for the whole bridge line (e.g. average comp)
    base_offset_in: float = 0.0

    @property
    def base_offset_mm(self) -> float:
        return inch_to_mm(self.base_offset_in)


# ---------------------------------------------------------------------------
# Strings / string sets
# ---------------------------------------------------------------------------


@dataclass
class StringSpec:
    index: int
    name: str
    gauge_in: float
    wound: bool = False

    @property
    def gauge_mm(self) -> float:
        return inch_to_mm(self.gauge_in)


@dataclass
class StringSetSpec:
    string_set_id: str
    description: str
    strings: List[StringSpec] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DXF mappings
# ---------------------------------------------------------------------------


@dataclass
class DXFMappingSpec:
    body_outline_id: Optional[str] = None
    fretboard_outline_id: Optional[str] = None
    bridge_footprint_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Top-level GuitarModelSpec
# ---------------------------------------------------------------------------


@dataclass
class GuitarModelSpec:
    """
    Top-level typed model used by RMOS, Art Studio, CAM, etc.
    """
    model_id: str
    display_name: str
    description: str
    scale: ScaleSpec
    neck_joint: Optional[NeckJointSpec] = None
    bridge: Optional[BridgeSpec] = None
    string_set: Optional[StringSetSpec] = None
    # Compensation per string index, in mm (even though JSON holds inches)
    reference_compensation_mm: Dict[int, float] = field(default_factory=dict)
    dxf_mappings: Optional[DXFMappingSpec] = None
    notes: List[str] = field(default_factory=list)
