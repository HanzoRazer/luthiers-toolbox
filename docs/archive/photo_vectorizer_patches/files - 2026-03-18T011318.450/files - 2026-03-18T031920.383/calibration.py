#!/usr/bin/env python3
"""
calibration.py — Body style and material calibration tables for thickness design.

Provides empirical calibration coefficients for different guitar body styles
and common tonewood materials.

Calibration Coefficients:
    η (eta):     Geometry factor for plate modal frequency calculation
                 Accounts for boundary conditions and effective stiffness region

    γ (gamma):   Transfer coefficient = √(α/β)
                 Maps free-plate Chladni frequencies to assembled-box frequencies

    α (alpha):   Numerator in Chladni-to-box mapping
                 Related to air loading and boundary stiffening

    β (beta):    Denominator in Chladni-to-box mapping
                 Related to plate mass and cavity compliance

Body Style Parameters:
    V:           Cavity volume (m³)
    A_hole:      Soundhole area (m²)
    L_eff:       Effective soundhole length for Helmholtz calculation (m)
    a_top, b_top:    Top plate effective dimensions (m)
    a_back, b_back:  Back plate effective dimensions (m)

Material Properties:
    E_L:         Longitudinal modulus (GPa)
    E_C:         Cross-grain modulus (GPa)
    rho:         Density (kg/m³)
    R_anis:      Orthotropic ratio E_L/E_C

References:
    - Gore & Gilet, "Contemporary Acoustic Guitar Design and Build"
    - Fletcher & Rossing, "The Physics of Musical Instruments"
    - Empirical data from luthier community
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# =============================================================================
# Body Style Definitions
# =============================================================================


class BodyStyle(str, Enum):
    """Guitar body style enumeration."""

    DREADNOUGHT = "dreadnought"
    JUMBO = "jumbo"
    OM = "om"
    OOO = "000"
    PARLOR = "parlor"
    CLASSICAL = "classical"
    CONCERT_CLASSICAL = "concert_classical"
    GRAND_AUDITORIUM = "grand_auditorium"
    ARCHTOP = "archtop"
    CUSTOM = "custom"


@dataclass(frozen=True)
class BodyCalibration:
    """Calibration parameters for a guitar body style.

    All dimensions in SI units (m, m², m³).
    """

    style: BodyStyle
    description: str

    # Cavity parameters
    volume_m3: float  # Cavity volume
    soundhole_area_m2: float  # Soundhole area
    soundhole_L_eff_m: float  # Effective length for Helmholtz

    # Top plate effective dimensions
    top_a_m: float  # Length (along grain)
    top_b_m: float  # Width (across grain)
    top_area_m2: float  # Total top plate area
    top_effective_area_m2: float  # Acoustically active area

    # Back plate effective dimensions
    back_a_m: float  # Length (along grain)
    back_b_m: float  # Width (across grain)
    back_area_m2: float  # Total back plate area
    back_effective_area_m2: float  # Acoustically active area

    # Calibration coefficients (empirical)
    eta_top: float = 1.0  # Geometry factor for top
    eta_back: float = 1.0  # Geometry factor for back
    gamma_top: float = 1.0  # Chladni-to-box transfer (top)
    gamma_back: float = 1.0  # Chladni-to-box transfer (back)

    # Target frequencies (Hz)
    f_monopole_target: float = 100.0  # Target monopole-like mode
    f_air_target: float = 95.0  # Target air resonance (Helmholtz)

    notes: str = ""


# Body style calibration database
# Values derived from Gore & Gilet + empirical measurements
_BODY_CALIBRATIONS: Dict[BodyStyle, BodyCalibration] = {
    BodyStyle.JUMBO: BodyCalibration(
        style=BodyStyle.JUMBO,
        description="Jumbo body (e.g., Gibson J-200, Guild F-50)",
        volume_m3=0.025,  # ~25 liters
        soundhole_area_m2=0.0079,  # ~100mm diameter
        soundhole_L_eff_m=0.085,  # Effective length = h + 1.6×r
        top_a_m=0.520,  # 520mm length
        top_b_m=0.430,  # 430mm lower bout
        top_area_m2=0.180,  # ~1800 cm²
        top_effective_area_m2=0.140,  # ~77% effective
        back_a_m=0.559,  # 559mm (from user's mahogany spec)
        back_b_m=0.241,  # 241mm effective width
        back_area_m2=0.135,  # ~1350 cm²
        back_effective_area_m2=0.100,  # ~74% effective
        eta_top=0.92,
        eta_back=0.88,
        gamma_top=0.85,
        gamma_back=0.82,
        f_monopole_target=86.0,  # User's target
        f_air_target=90.0,
        notes="Large body, warm fundamental, strong bass",
    ),
    BodyStyle.DREADNOUGHT: BodyCalibration(
        style=BodyStyle.DREADNOUGHT,
        description="Dreadnought (e.g., Martin D-28, D-18)",
        volume_m3=0.022,  # ~22 liters
        soundhole_area_m2=0.0079,  # ~100mm diameter
        soundhole_L_eff_m=0.085,
        top_a_m=0.505,  # 505mm length
        top_b_m=0.400,  # 400mm lower bout
        top_area_m2=0.160,
        top_effective_area_m2=0.120,
        back_a_m=0.505,
        back_b_m=0.400,
        back_area_m2=0.160,
        back_effective_area_m2=0.115,
        eta_top=0.95,
        eta_back=0.90,
        gamma_top=0.88,
        gamma_back=0.85,
        f_monopole_target=98.0,
        f_air_target=105.0,
        notes="Classic steel-string, strong midrange projection",
    ),
    BodyStyle.OM: BodyCalibration(
        style=BodyStyle.OM,
        description="Orchestra Model (e.g., Martin OM-28, 000)",
        volume_m3=0.018,  # ~18 liters
        soundhole_area_m2=0.0071,  # ~95mm diameter
        soundhole_L_eff_m=0.080,
        top_a_m=0.495,
        top_b_m=0.380,
        top_area_m2=0.140,
        top_effective_area_m2=0.105,
        back_a_m=0.495,
        back_b_m=0.380,
        back_area_m2=0.140,
        back_effective_area_m2=0.100,
        eta_top=0.97,
        eta_back=0.92,
        gamma_top=0.90,
        gamma_back=0.87,
        f_monopole_target=105.0,
        f_air_target=115.0,
        notes="Balanced response, fingerstyle friendly",
    ),
    BodyStyle.OOO: BodyCalibration(
        style=BodyStyle.OOO,
        description="000/Auditorium (e.g., Martin 000-28)",
        volume_m3=0.016,  # ~16 liters
        soundhole_area_m2=0.0071,
        soundhole_L_eff_m=0.080,
        top_a_m=0.485,
        top_b_m=0.370,
        top_area_m2=0.130,
        top_effective_area_m2=0.098,
        back_a_m=0.485,
        back_b_m=0.370,
        back_area_m2=0.130,
        back_effective_area_m2=0.095,
        eta_top=0.98,
        eta_back=0.93,
        gamma_top=0.91,
        gamma_back=0.88,
        f_monopole_target=110.0,
        f_air_target=120.0,
        notes="Slightly smaller than OM, articulate",
    ),
    BodyStyle.PARLOR: BodyCalibration(
        style=BodyStyle.PARLOR,
        description="Parlor guitar (small body, intimate)",
        volume_m3=0.012,  # ~12 liters
        soundhole_area_m2=0.0064,  # ~90mm diameter
        soundhole_L_eff_m=0.076,
        top_a_m=0.440,
        top_b_m=0.340,
        top_area_m2=0.110,
        top_effective_area_m2=0.080,
        back_a_m=0.440,
        back_b_m=0.340,
        back_area_m2=0.110,
        back_effective_area_m2=0.078,
        eta_top=1.0,
        eta_back=0.95,
        gamma_top=0.93,
        gamma_back=0.90,
        f_monopole_target=125.0,
        f_air_target=135.0,
        notes="Small body, focused midrange, vintage character",
    ),
    BodyStyle.CLASSICAL: BodyCalibration(
        style=BodyStyle.CLASSICAL,
        description="Classical guitar (nylon string)",
        volume_m3=0.014,  # ~14 liters
        soundhole_area_m2=0.0064,  # ~90mm diameter
        soundhole_L_eff_m=0.076,
        top_a_m=0.480,
        top_b_m=0.370,
        top_area_m2=0.135,
        top_effective_area_m2=0.100,
        back_a_m=0.480,
        back_b_m=0.370,
        back_area_m2=0.135,
        back_effective_area_m2=0.095,
        eta_top=0.90,
        eta_back=0.85,
        gamma_top=0.82,
        gamma_back=0.78,
        f_monopole_target=95.0,
        f_air_target=100.0,
        notes="Traditional fan bracing, warm fundamental",
    ),
    BodyStyle.GRAND_AUDITORIUM: BodyCalibration(
        style=BodyStyle.GRAND_AUDITORIUM,
        description="Grand Auditorium (e.g., Taylor 814)",
        volume_m3=0.019,  # ~19 liters
        soundhole_area_m2=0.0079,
        soundhole_L_eff_m=0.085,
        top_a_m=0.500,
        top_b_m=0.405,
        top_area_m2=0.155,
        top_effective_area_m2=0.118,
        back_a_m=0.500,
        back_b_m=0.405,
        back_area_m2=0.155,
        back_effective_area_m2=0.112,
        eta_top=0.96,
        eta_back=0.91,
        gamma_top=0.89,
        gamma_back=0.86,
        f_monopole_target=100.0,
        f_air_target=110.0,
        notes="Modern versatile body, balanced projection",
    ),
    BodyStyle.ARCHTOP: BodyCalibration(
        style=BodyStyle.ARCHTOP,
        description="Archtop guitar (carved top/back)",
        volume_m3=0.024,
        soundhole_area_m2=0.010,  # f-holes combined
        soundhole_L_eff_m=0.095,
        top_a_m=0.520,
        top_b_m=0.430,
        top_area_m2=0.175,
        top_effective_area_m2=0.130,
        back_a_m=0.520,
        back_b_m=0.430,
        back_area_m2=0.175,
        back_effective_area_m2=0.125,
        eta_top=0.75,  # Carved reduces effective area
        eta_back=0.70,
        gamma_top=0.70,
        gamma_back=0.65,
        f_monopole_target=120.0,
        f_air_target=130.0,
        notes="Carved plates, f-holes, jazz voicing",
    ),
}


def get_body_calibration(style: BodyStyle | str) -> Optional[BodyCalibration]:
    """Get calibration parameters for a body style.

    Args:
        style: Body style enum or string name

    Returns:
        BodyCalibration or None if not found
    """
    if isinstance(style, str):
        try:
            style = BodyStyle(style.lower())
        except ValueError:
            return None
    return _BODY_CALIBRATIONS.get(style)


def list_body_styles() -> List[Dict[str, Any]]:
    """List all available body styles with summary info."""
    return [
        {
            "style": cal.style.value,
            "description": cal.description,
            "volume_liters": round(cal.volume_m3 * 1000, 1),
            "f_monopole_target": cal.f_monopole_target,
            "notes": cal.notes,
        }
        for cal in _BODY_CALIBRATIONS.values()
    ]


# =============================================================================
# Material Presets
# =============================================================================


@dataclass(frozen=True)
class MaterialPreset:
    """Material properties for common tonewoods.

    All values are typical/average. Actual wood varies significantly.
    """

    name: str
    species: str

    # Elastic moduli (GPa)
    E_L_GPa: float  # Longitudinal (along grain)
    E_C_GPa: float  # Cross-grain (radial/tangential average)

    # Density (kg/m³)
    density_kg_m3: float

    # Derived
    R_anis: float  # Orthotropic ratio E_L/E_C

    # Quality indicators
    typical_use: str  # "top", "back", "both"
    quality_notes: str = ""

    # Ranges for validation
    E_L_range: tuple = field(default=(0.0, 100.0))
    E_C_range: tuple = field(default=(0.0, 10.0))
    density_range: tuple = field(default=(200, 1200))


# Common tonewood presets
_MATERIAL_PRESETS: Dict[str, MaterialPreset] = {
    # Soundboard woods (tops)
    "sitka_spruce": MaterialPreset(
        name="sitka_spruce",
        species="Picea sitchensis",
        E_L_GPa=12.5,
        E_C_GPa=0.85,
        density_kg_m3=420,
        R_anis=14.7,
        typical_use="top",
        quality_notes="Most common steel-string top, balanced response",
        E_L_range=(10.0, 16.0),
        E_C_range=(0.6, 1.2),
        density_range=(380, 480),
    ),
    "engelmann_spruce": MaterialPreset(
        name="engelmann_spruce",
        species="Picea engelmannii",
        E_L_GPa=11.0,
        E_C_GPa=0.80,
        density_kg_m3=380,
        R_anis=13.8,
        typical_use="top",
        quality_notes="Lighter, more responsive than Sitka",
        E_L_range=(9.0, 14.0),
        E_C_range=(0.5, 1.1),
        density_range=(340, 440),
    ),
    "european_spruce": MaterialPreset(
        name="european_spruce",
        species="Picea abies",
        E_L_GPa=14.0,
        E_C_GPa=0.75,
        density_kg_m3=440,
        R_anis=18.7,
        typical_use="top",
        quality_notes="Higher E_L/E_C ratio, pronounced overtones",
        E_L_range=(12.0, 17.0),
        E_C_range=(0.5, 1.0),
        density_range=(400, 500),
    ),
    "adirondack_spruce": MaterialPreset(
        name="adirondack_spruce",
        species="Picea rubens",
        E_L_GPa=13.5,
        E_C_GPa=0.90,
        density_kg_m3=430,
        R_anis=15.0,
        typical_use="top",
        quality_notes="Strong, loud, favored for flatpicking",
        E_L_range=(11.0, 16.0),
        E_C_range=(0.7, 1.2),
        density_range=(390, 480),
    ),
    "western_red_cedar": MaterialPreset(
        name="western_red_cedar",
        species="Thuja plicata",
        E_L_GPa=8.5,
        E_C_GPa=0.70,
        density_kg_m3=350,
        R_anis=12.1,
        typical_use="top",
        quality_notes="Warm, responsive, classical favorite",
        E_L_range=(6.5, 11.0),
        E_C_range=(0.5, 0.9),
        density_range=(300, 420),
    ),
    "redwood": MaterialPreset(
        name="redwood",
        species="Sequoia sempervirens",
        E_L_GPa=9.0,
        E_C_GPa=0.65,
        density_kg_m3=360,
        R_anis=13.8,
        typical_use="top",
        quality_notes="Similar to cedar, slightly brighter",
        E_L_range=(7.0, 12.0),
        E_C_range=(0.4, 0.9),
        density_range=(320, 420),
    ),
    # Back/side woods
    "mahogany": MaterialPreset(
        name="mahogany",
        species="Swietenia macrophylla",
        E_L_GPa=10.2,
        E_C_GPa=0.65,
        density_kg_m3=540,
        R_anis=15.7,
        typical_use="back",
        quality_notes="Warm, punchy midrange, great for backs",
        E_L_range=(8.0, 13.0),
        E_C_range=(0.4, 0.9),
        density_range=(480, 620),
    ),
    "indian_rosewood": MaterialPreset(
        name="indian_rosewood",
        species="Dalbergia latifolia",
        E_L_GPa=12.8,
        E_C_GPa=0.90,
        density_kg_m3=830,
        R_anis=14.2,
        typical_use="back",
        quality_notes="Complex overtones, strong fundamental",
        E_L_range=(10.0, 16.0),
        E_C_range=(0.7, 1.2),
        density_range=(750, 950),
    ),
    "brazilian_rosewood": MaterialPreset(
        name="brazilian_rosewood",
        species="Dalbergia nigra",
        E_L_GPa=14.0,
        E_C_GPa=1.00,
        density_kg_m3=880,
        R_anis=14.0,
        typical_use="back",
        quality_notes="Legendary tone, CITES restricted",
        E_L_range=(11.0, 17.0),
        E_C_range=(0.8, 1.3),
        density_range=(800, 1000),
    ),
    "maple": MaterialPreset(
        name="maple",
        species="Acer saccharum",
        E_L_GPa=12.0,
        E_C_GPa=1.10,
        density_kg_m3=710,
        R_anis=10.9,
        typical_use="back",
        quality_notes="Bright, reflective, archtop favorite",
        E_L_range=(10.0, 15.0),
        E_C_range=(0.8, 1.4),
        density_range=(650, 800),
    ),
    "sapele": MaterialPreset(
        name="sapele",
        species="Entandrophragma cylindricum",
        E_L_GPa=11.0,
        E_C_GPa=0.75,
        density_kg_m3=620,
        R_anis=14.7,
        typical_use="back",
        quality_notes="Similar to mahogany, slightly brighter",
        E_L_range=(9.0, 14.0),
        E_C_range=(0.5, 1.0),
        density_range=(550, 720),
    ),
    "koa": MaterialPreset(
        name="koa",
        species="Acacia koa",
        E_L_GPa=11.5,
        E_C_GPa=0.85,
        density_kg_m3=600,
        R_anis=13.5,
        typical_use="both",
        quality_notes="Balanced, opens up with playing",
        E_L_range=(9.0, 14.0),
        E_C_range=(0.6, 1.1),
        density_range=(520, 700),
    ),
    "walnut": MaterialPreset(
        name="walnut",
        species="Juglans nigra",
        E_L_GPa=11.2,
        E_C_GPa=0.80,
        density_kg_m3=610,
        R_anis=14.0,
        typical_use="back",
        quality_notes="Warm, sustainable alternative",
        E_L_range=(9.0, 14.0),
        E_C_range=(0.6, 1.0),
        density_range=(540, 700),
    ),
    "ovangkol": MaterialPreset(
        name="ovangkol",
        species="Guibourtia ehie",
        E_L_GPa=12.5,
        E_C_GPa=0.85,
        density_kg_m3=780,
        R_anis=14.7,
        typical_use="back",
        quality_notes="Rosewood alternative, good projection",
        E_L_range=(10.0, 15.0),
        E_C_range=(0.6, 1.1),
        density_range=(700, 880),
    ),
}


def get_material_preset(name: str) -> Optional[MaterialPreset]:
    """Get material preset by name.

    Args:
        name: Material name (e.g., "sitka_spruce", "mahogany")

    Returns:
        MaterialPreset or None if not found
    """
    return _MATERIAL_PRESETS.get(name.lower().replace(" ", "_").replace("-", "_"))


def list_materials(use_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all available material presets.

    Args:
        use_filter: Optional filter by use ("top", "back", "both")

    Returns:
        List of material summaries
    """
    results = []
    for mat in _MATERIAL_PRESETS.values():
        if use_filter and mat.typical_use != use_filter and mat.typical_use != "both":
            continue
        results.append(
            {
                "name": mat.name,
                "species": mat.species,
                "E_L_GPa": mat.E_L_GPa,
                "E_C_GPa": mat.E_C_GPa,
                "density_kg_m3": mat.density_kg_m3,
                "R_anis": mat.R_anis,
                "typical_use": mat.typical_use,
                "notes": mat.quality_notes,
            }
        )
    return results


# =============================================================================
# Air Properties
# =============================================================================

# Standard air properties at 20°C, sea level
AIR_DENSITY_KG_M3 = 1.204
AIR_SPEED_OF_SOUND_M_S = 343.0
