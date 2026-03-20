# services/api/app/calculators/binding_materials.py

"""
Binding Materials — Material definitions, feed settings, and purfling patterns.

Extracted from binding_geometry.py for modularity.

Contains:
- BindingMaterial enum with bend radius characteristics
- MaterialFeedSettings for CAM operations
- PurflingStripProfile and PurflingStripSpec for decorative strips
- Material catalogs and presets
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Any
from enum import Enum


# =============================================================================
# BINDING MATERIALS
# =============================================================================

class BindingMaterial(str, Enum):
    """Binding material types with bend radius characteristics."""
    CELLULOID = "celluloid"        # Classic, moderate flexibility
    ABS_PLASTIC = "abs_plastic"    # Common, good flexibility
    WOOD_MAPLE = "wood_maple"      # Rigid, requires kerfing or steaming
    WOOD_ROSEWOOD = "wood_rosewood"  # Very rigid
    FIBER = "fiber"                # Black/white fiber, flexible
    IVOROID = "ivoroid"            # Synthetic ivory, moderate
    ABALONE_SHELL = "abalone_shell"  # Fragile natural shell, cannot cold-bend tight radius (BIND-GAP-01)
    WOOD_EBONY = "wood_ebony"          # Very hard, slow feed required


# Minimum bend radii by material (mm) - below this risks cracking
MINIMUM_BEND_RADII_MM: Dict[BindingMaterial, float] = {
    BindingMaterial.CELLULOID: 6.0,
    BindingMaterial.ABS_PLASTIC: 3.0,
    BindingMaterial.WOOD_MAPLE: 15.0,
    BindingMaterial.WOOD_ROSEWOOD: 20.0,
    BindingMaterial.FIBER: 4.0,
    BindingMaterial.IVOROID: 5.0,
    BindingMaterial.ABALONE_SHELL: 8.0,  # Fragile shell, requires gentle curves (BIND-GAP-01)
    BindingMaterial.WOOD_EBONY: 25.0,      # Very hard, requires kerfing
}

# Standard binding widths (mm)
BINDING_WIDTHS = {
    "delicate": 1.5,
    "vintage_acoustic": 2.0,
    "standard": 2.5,
    "medium": 3.0,
    "bold": 5.0,
    "archtop": 7.0,
}


# =============================================================================
# MATERIAL FEED SETTINGS (OM-PURF-06)
# =============================================================================

@dataclass
class MaterialFeedSettings:
    """Feed rate and spindle settings for a material."""
    feed_rate_xy: float  # XY feed rate mm/min
    spindle_rpm: int     # Spindle speed RPM
    plunge_rate: float = 100.0  # Default plunge rate


MATERIAL_FEED_RATES: Dict[BindingMaterial, MaterialFeedSettings] = {
    BindingMaterial.ABALONE_SHELL: MaterialFeedSettings(feed_rate_xy=800.0, spindle_rpm=18000),
    BindingMaterial.WOOD_MAPLE: MaterialFeedSettings(feed_rate_xy=1200.0, spindle_rpm=16000),
    BindingMaterial.WOOD_ROSEWOOD: MaterialFeedSettings(feed_rate_xy=900.0, spindle_rpm=17000),
    BindingMaterial.WOOD_EBONY: MaterialFeedSettings(feed_rate_xy=700.0, spindle_rpm=18000),
    BindingMaterial.CELLULOID: MaterialFeedSettings(feed_rate_xy=1500.0, spindle_rpm=14000),
    BindingMaterial.ABS_PLASTIC: MaterialFeedSettings(feed_rate_xy=1800.0, spindle_rpm=12000),
    BindingMaterial.FIBER: MaterialFeedSettings(feed_rate_xy=1400.0, spindle_rpm=15000),
    BindingMaterial.IVOROID: MaterialFeedSettings(feed_rate_xy=1200.0, spindle_rpm=15000),
}

# Default feed settings when material is unknown
DEFAULT_FEED_SETTINGS = MaterialFeedSettings(feed_rate_xy=1000.0, spindle_rpm=16000)


def get_material_feed_settings(material: Optional[BindingMaterial]) -> MaterialFeedSettings:
    """
    Get feed rate and spindle settings for a binding material.

    OM-PURF-06: Material-aware feed rates for binding/purfling operations.

    Args:
        material: BindingMaterial enum value, or None for default

    Returns:
        MaterialFeedSettings with feed_rate_xy, spindle_rpm, plunge_rate
    """
    if material is None:
        return DEFAULT_FEED_SETTINGS
    return MATERIAL_FEED_RATES.get(material, DEFAULT_FEED_SETTINGS)


# =============================================================================
# PURFLING STRIP PATTERNS (BIND-GAP-02)
# =============================================================================

class PurflingStripProfile(str, Enum):
    """Purfling strip profile shapes. (BIND-GAP-02)"""
    SOLID = "solid"              # Flat strip, no pattern
    HERRINGBONE = "herringbone"  # V-chevron zigzag
    SINUSOIDAL = "sinusoidal"    # Smooth wave (spanish_wave)
    ROPE = "rope"                # Traditional twisted rope pattern


@dataclass
class PurflingStripSpec:
    """
    Purfling strip specification for bending/installation.

    Purfling is the thin decorative line inset from binding.
    Spec includes dimensions and profile for CAM and visual preview.
    """
    id: str
    name: str
    width_mm: float       # Strip width (perpendicular to body edge)
    height_mm: float      # Strip height (visible from top)
    profile: PurflingStripProfile
    wavelength_mm: Optional[float] = None  # For wave patterns
    amplitude_mm: Optional[float] = None   # For wave patterns
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "profile": self.profile.value,
            "wavelength_mm": self.wavelength_mm,
            "amplitude_mm": self.amplitude_mm,
            "notes": self.notes,
        }


# Purfling strip pattern catalog (BIND-GAP-02)
PURFLING_STRIP_PATTERNS: Dict[str, PurflingStripSpec] = {
    "solid_standard": PurflingStripSpec(
        id="solid_standard",
        name="Solid Standard",
        width_mm=1.5,
        height_mm=0.6,
        profile=PurflingStripProfile.SOLID,
        notes="Basic solid purfling strip, no pattern",
    ),
    "herringbone_standard": PurflingStripSpec(
        id="herringbone_standard",
        name="Herringbone Standard",
        width_mm=2.0,
        height_mm=1.0,
        profile=PurflingStripProfile.HERRINGBONE,
        notes="Classic V-chevron herringbone purfling",
    ),
    "spanish_wave": PurflingStripSpec(
        id="spanish_wave",
        name="Spanish Wave",
        width_mm=2.2,
        height_mm=6.0,
        profile=PurflingStripProfile.SINUSOIDAL,
        wavelength_mm=12.0,    # Sinusoidal period
        amplitude_mm=0.5,       # Wave amplitude from centerline
        notes="Traditional Spanish sinusoidal wave purfling. "
              "2.2mm width × 6.0mm height. Smooth flowing visual effect.",
    ),
    "rope_fine": PurflingStripSpec(
        id="rope_fine",
        name="Rope Fine",
        width_mm=1.8,
        height_mm=0.8,
        profile=PurflingStripProfile.ROPE,
        notes="Fine twisted rope pattern purfling",
    ),
}


__all__ = [
    "BindingMaterial",
    "MINIMUM_BEND_RADII_MM",
    "BINDING_WIDTHS",
    "MaterialFeedSettings",
    "MATERIAL_FEED_RATES",
    "DEFAULT_FEED_SETTINGS",
    "get_material_feed_settings",
    "PurflingStripProfile",
    "PurflingStripSpec",
    "PURFLING_STRIP_PATTERNS",
]
