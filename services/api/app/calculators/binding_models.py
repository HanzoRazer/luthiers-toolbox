# services/api/app/calculators/binding_models.py

"""
Binding Models — Data classes for binding geometry calculations.

Extracted from binding_geometry.py for modularity.

Contains:
- BindingChannelSpec: Multi-layer channel specification
- BendRadiusCheck: Bend radius validation result
- MiterJoint: Corner miter specification
- NeckBindingGeometry: Neck binding computation result
- HeadstockBindingGeometry: Headstock binding computation result
- InstallationMethod: Installation method enum
- BindingStripEstimate: Strip length calculation result
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Literal, Dict, Any
from enum import Enum

from .binding_materials import (
    BindingMaterial,
    PurflingStripSpec,
    PURFLING_STRIP_PATTERNS,
)


# Type aliases
Pt2D = Tuple[float, float]
Pt3D = Tuple[float, float, float]


# =============================================================================
# BIND-GAP-04: MULTI-LAYER CHANNEL MODEL
# =============================================================================

@dataclass
class BindingChannelSpec:
    """
    Multi-layer binding channel specification.

    Les Paul spec defines the pattern:
    - primary_channel: 2.375mm width × 3.0mm depth (outer binding)
    - inner_ledge: 1.6mm width × 2.0mm depth (purfling inset)

    This supports the common multi-layer binding pattern where:
    1. Outer binding strip sits in the primary channel
    2. Purfling strip sits in the shallower inner ledge

    Reference: specs/guitars/gibson_les_paul.json
    """
    primary_width_mm: float = 2.375
    primary_depth_mm: float = 3.0
    inner_ledge_width_mm: float = 1.6
    inner_ledge_depth_mm: float = 2.0
    material: BindingMaterial = BindingMaterial.ABS_PLASTIC
    purfling: Optional[PurflingStripSpec] = None

    @property
    def total_width_mm(self) -> float:
        """Total channel width (primary + inner ledge)."""
        return self.primary_width_mm + self.inner_ledge_width_mm

    @property
    def step_depth_mm(self) -> float:
        """Depth of the step between primary and inner ledge."""
        return self.primary_depth_mm - self.inner_ledge_depth_mm

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_width_mm": round(self.primary_width_mm, 3),
            "primary_depth_mm": round(self.primary_depth_mm, 3),
            "inner_ledge_width_mm": round(self.inner_ledge_width_mm, 3),
            "inner_ledge_depth_mm": round(self.inner_ledge_depth_mm, 3),
            "total_width_mm": round(self.total_width_mm, 3),
            "step_depth_mm": round(self.step_depth_mm, 3),
            "material": self.material.value,
            "purfling": self.purfling.to_dict() if self.purfling else None,
        }


# Preset channel specs for common instruments
BINDING_CHANNEL_PRESETS: Dict[str, BindingChannelSpec] = {
    "les_paul": BindingChannelSpec(
        primary_width_mm=2.375,
        primary_depth_mm=3.0,
        inner_ledge_width_mm=1.6,
        inner_ledge_depth_mm=2.0,
        material=BindingMaterial.CELLULOID,
        purfling=PURFLING_STRIP_PATTERNS.get("spanish_wave"),
    ),
    "om_acoustic": BindingChannelSpec(
        primary_width_mm=2.5,
        primary_depth_mm=2.8,
        inner_ledge_width_mm=1.5,
        inner_ledge_depth_mm=1.8,
        material=BindingMaterial.WOOD_MAPLE,
    ),
    "dreadnought": BindingChannelSpec(
        primary_width_mm=3.0,
        primary_depth_mm=3.2,
        inner_ledge_width_mm=1.8,
        inner_ledge_depth_mm=2.0,
        material=BindingMaterial.ABS_PLASTIC,
    ),
}


# =============================================================================
# VALIDATION DATA CLASSES
# =============================================================================

@dataclass
class BendRadiusCheck:
    """Result of checking if a bend radius is safe for a material."""
    position_mm: float  # Distance along binding path
    actual_radius_mm: float
    minimum_radius_mm: float
    is_safe: bool
    severity: Literal["ok", "warning", "critical"]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_mm": round(self.position_mm, 2),
            "actual_radius_mm": round(self.actual_radius_mm, 2),
            "minimum_radius_mm": round(self.minimum_radius_mm, 2),
            "is_safe": self.is_safe,
            "severity": self.severity,
            "recommendation": self.recommendation,
        }


@dataclass
class MiterJoint:
    """Miter joint specification at a corner."""
    position: Pt2D  # Corner position
    angle_degrees: float  # Miter cut angle (half the corner angle)
    corner_angle_degrees: float  # Full corner angle (interior)
    piece_1_direction: Tuple[float, float]  # Unit vector of incoming piece
    piece_2_direction: Tuple[float, float]  # Unit vector of outgoing piece
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": [round(p, 3) for p in self.position],
            "angle_degrees": round(self.angle_degrees, 2),
            "corner_angle_degrees": round(self.corner_angle_degrees, 2),
            "piece_1_direction": [round(d, 4) for d in self.piece_1_direction],
            "piece_2_direction": [round(d, 4) for d in self.piece_2_direction],
            "notes": self.notes,
        }


# =============================================================================
# GEOMETRY RESULT DATA CLASSES
# =============================================================================

@dataclass
class NeckBindingGeometry:
    """Complete neck binding geometry specification."""
    # Input parameters
    scale_length_mm: float
    nut_width_mm: float
    heel_width_mm: float
    fretboard_length_mm: float
    fretboard_radius_mm: Optional[float]  # None for flat
    compound_radius: Optional[Tuple[float, float]]  # (nut_radius, heel_radius)
    binding_width_mm: float
    binding_thickness_mm: float

    # Computed geometry
    left_edge_points: List[Pt3D]  # 3D points along left binding path
    right_edge_points: List[Pt3D]  # 3D points along right binding path
    taper_angle_degrees: float  # Angle of fretboard taper
    total_length_mm: float  # Total binding length per side

    # Validation
    bend_radius_checks: List[BendRadiusCheck] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scale_length_mm": round(self.scale_length_mm, 2),
            "nut_width_mm": round(self.nut_width_mm, 2),
            "heel_width_mm": round(self.heel_width_mm, 2),
            "fretboard_length_mm": round(self.fretboard_length_mm, 2),
            "fretboard_radius_mm": round(self.fretboard_radius_mm, 2) if self.fretboard_radius_mm else None,
            "compound_radius": [round(r, 2) for r in self.compound_radius] if self.compound_radius else None,
            "binding_width_mm": round(self.binding_width_mm, 2),
            "binding_thickness_mm": round(self.binding_thickness_mm, 2),
            "taper_angle_degrees": round(self.taper_angle_degrees, 3),
            "total_length_mm": round(self.total_length_mm, 2),
            "left_edge_point_count": len(self.left_edge_points),
            "right_edge_point_count": len(self.right_edge_points),
            "bend_radius_checks": [c.to_dict() for c in self.bend_radius_checks],
            "warnings": self.warnings,
        }


@dataclass
class HeadstockBindingGeometry:
    """Complete headstock binding geometry specification."""
    # Input parameters
    outline_points: List[Pt2D]  # Headstock outline (closed polygon)
    binding_width_mm: float
    binding_thickness_mm: float
    material: BindingMaterial

    # Computed geometry
    binding_path: List[Pt2D]  # Offset path for binding channel
    total_length_mm: float
    minimum_radius_mm: float  # Tightest curve in the outline
    minimum_radius_position: Pt2D  # Where the tightest curve occurs

    # Validation
    bend_radius_checks: List[BendRadiusCheck] = field(default_factory=list)
    miter_joints: List[MiterJoint] = field(default_factory=list)
    is_manufacturable: bool = True
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outline_point_count": len(self.outline_points),
            "binding_width_mm": round(self.binding_width_mm, 2),
            "binding_thickness_mm": round(self.binding_thickness_mm, 2),
            "material": self.material.value,
            "binding_path_point_count": len(self.binding_path),
            "total_length_mm": round(self.total_length_mm, 2),
            "minimum_radius_mm": round(self.minimum_radius_mm, 2),
            "minimum_radius_position": [round(p, 2) for p in self.minimum_radius_position],
            "bend_radius_checks": [c.to_dict() for c in self.bend_radius_checks],
            "miter_joints": [m.to_dict() for m in self.miter_joints],
            "is_manufacturable": self.is_manufacturable,
            "warnings": self.warnings,
        }


# =============================================================================
# STRIP LENGTH CALCULATION MODELS (BIND-GAP-04)
# =============================================================================

class InstallationMethod(str, Enum):
    """Binding installation method affecting strip length calculation."""
    SINGLE_CONTINUOUS = "single_continuous"  # One piece wraps entire perimeter
    TOP_AND_BACK = "top_and_back"  # Separate strips for top/back edges
    SECTIONAL = "sectional"  # Multiple sections with butt joints
    TRADITIONAL_ACOUSTIC = "traditional_acoustic"  # Top rim, back rim, side strips


@dataclass
class BindingStripEstimate:
    """
    Binding strip length estimate for material ordering.

    BIND-GAP-04: Provides accurate strip length calculation including
    waste allowances for proper material ordering.
    """
    # Core measurements
    perimeter_mm: float
    installation_method: str

    # Allowances
    overlap_allowance_mm: float
    miter_waste_mm: float
    handling_waste_mm: float

    # Results
    minimum_length_mm: float  # Absolute minimum (no waste)
    recommended_length_mm: float  # With standard allowances
    order_length_mm: float  # Rounded up for ordering

    # Breakdown by section (for multi-piece installations)
    sections: List[Dict[str, Any]] = field(default_factory=list)

    # Material info
    material: Optional[str] = None
    strip_width_mm: Optional[float] = None

    # Notes
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "perimeter_mm": round(self.perimeter_mm, 2),
            "installation_method": self.installation_method,
            "overlap_allowance_mm": round(self.overlap_allowance_mm, 2),
            "miter_waste_mm": round(self.miter_waste_mm, 2),
            "handling_waste_mm": round(self.handling_waste_mm, 2),
            "minimum_length_mm": round(self.minimum_length_mm, 2),
            "recommended_length_mm": round(self.recommended_length_mm, 2),
            "order_length_mm": round(self.order_length_mm, 2),
            "sections": self.sections,
            "material": self.material,
            "strip_width_mm": self.strip_width_mm,
            "notes": self.notes,
        }


# Standard allowances (mm)
DEFAULT_OVERLAP_ALLOWANCE_MM = 10.0  # Overlap at joint
DEFAULT_MITER_WASTE_PER_CORNER_MM = 3.0  # Waste from miter cuts
DEFAULT_HANDLING_WASTE_PERCENT = 0.05  # 5% for handling, mistakes


__all__ = [
    # Type aliases
    "Pt2D",
    "Pt3D",
    # Channel spec
    "BindingChannelSpec",
    "BINDING_CHANNEL_PRESETS",
    # Validation
    "BendRadiusCheck",
    "MiterJoint",
    # Geometry results
    "NeckBindingGeometry",
    "HeadstockBindingGeometry",
    # Strip length
    "InstallationMethod",
    "BindingStripEstimate",
    "DEFAULT_OVERLAP_ALLOWANCE_MM",
    "DEFAULT_MITER_WASTE_PER_CORNER_MM",
    "DEFAULT_HANDLING_WASTE_PERCENT",
]
