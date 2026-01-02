"""
Instrument Geometry: Guitar Model Specification

Wave 17 - Instrument Geometry Integration

High-level guitar model specification that ties together:
- Scale profile
- String set and tunings
- Neck taper configuration
- Spacing rules (nut/bridge)
- Body outline mapping

This is the NEW canonical model definition system.
It produces InstrumentSpec (existing system) for backward compatibility.

Usage:
    from instrument_geometry.model_spec import PRESET_MODELS, guitar_model_to_instrument_spec
    
    model = PRESET_MODELS["strat_25_5"]
    instrument_spec = guitar_model_to_instrument_spec(model)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .models import ScaleProfile


# ---------------------------------------------------------------------------
# Local StringSpec for this module (full-featured version with tuning info)
# Note: models/specs.py has a simpler StringSpec for JSON loading
# ---------------------------------------------------------------------------

@dataclass
class StringSpec:
    """
    Specification for a single guitar string with tuning info.
    
    This is the full-featured version used in preset models.
    
    Attributes:
        name: String designation (e.g. "E4", "B3", "G3")
        gauge_in: String gauge in inches (e.g. 0.009, 0.046)
        is_wound: True for wound strings, False for plain
        frequency_hz: Open string fundamental frequency in Hz
        open_note: Musical note name (e.g. "E4", "A3")
        material: String material (default "steel")
    """
    name: str
    gauge_in: float
    is_wound: bool
    frequency_hz: float
    open_note: str = ""
    material: str = "steel"


# ---------------------------------------------------------------------------
# Standard scale profiles (replaces scattered definitions)
# ---------------------------------------------------------------------------

STANDARD_SCALE_PROFILES: Dict[str, ScaleProfile] = {
    "fender_25_5": ScaleProfile(
        id="fender_25_5",
        scale_length_mm=648.0,  # 25.5"
        num_frets=22,
        description="Fender-style 25.5\" scale (Strat, Tele, Jazz Bass)",
    ),
    "gibson_24_75": ScaleProfile(
        id="gibson_24_75",
        scale_length_mm=628.65,  # 24.75"
        num_frets=22,
        description="Gibson-style 24.75\" scale (Les Paul, SG, ES-335)",
    ),
    "prs_25": ScaleProfile(
        id="prs_25",
        scale_length_mm=635.0,  # 25"
        num_frets=24,
        description="PRS-style 25\" scale",
    ),
    "classical_650": ScaleProfile(
        id="classical_650",
        scale_length_mm=650.0,
        num_frets=19,
        description="Classical guitar 650mm scale",
    ),
    "acoustic_martin": ScaleProfile(
        id="acoustic_martin",
        scale_length_mm=645.0,  # 25.4"
        num_frets=20,
        description="Martin-style acoustic 25.4\" scale (Dreadnought, OM)",
    ),
    "ukulele_soprano": ScaleProfile(
        id="ukulele_soprano",
        scale_length_mm=349.0,
        num_frets=15,
        description="Soprano ukulele ~13.75\" scale",
    ),
}


# ---------------------------------------------------------------------------
# Neck taper & spacing specs
# ---------------------------------------------------------------------------

@dataclass
class NeckTaperSpec:
    """
    Parametric neck width specification.

    This does NOT attempt to encode the full neck *profile* (thickness,
    back carve, etc.). It only handles width across the fretboard surface.

    We model width as a linear function of "distance from nut":
        width(L) = nut_width_mm + (heel_width_mm - nut_width_mm) * (L / taper_length_in)

    where:
        L is between 0 and taper_length_in (usually ≈ scale_length or slightly less).
        
    Attributes:
        nut_width_mm: Width at nut (e.g. 42.0 mm, 43.0 mm)
        heel_width_mm: Width at body joint (e.g. ~56–60 mm)
        taper_length_in: Distance from nut to heel (inches)
    """
    nut_width_mm: float
    heel_width_mm: float
    taper_length_in: float

    def width_at_distance_in(self, distance_in: float) -> float:
        """
        Compute the interpolated width at a given distance from the nut.

        For now, we assume a simple linear taper; future versions could
        allow more complex curves or multiple segments.
        
        Args:
            distance_in: Distance from nut in inches
            
        Returns:
            Interpolated width in mm
        """
        if distance_in <= 0.0:
            return self.nut_width_mm
        if distance_in >= self.taper_length_in:
            return self.heel_width_mm

        frac = distance_in / self.taper_length_in
        return self.nut_width_mm + (self.heel_width_mm - self.nut_width_mm) * frac


@dataclass
class StringSpacingSpec:
    """
    Describes string spacing strategy at a given station (nut, bridge).

    Attributes:
        num_strings: Number of strings
        e_to_e_mm: E-to-E span (distance between outer strings)
        bass_edge_margin_mm: Optional edge margin for nut-style spacing
        treble_edge_margin_mm: Optional edge margin for nut-style spacing

    You can use this config in combination with spacing.py utilities
    to derive actual coordinates.
    """
    num_strings: int
    e_to_e_mm: float
    bass_edge_margin_mm: float = 0.0
    treble_edge_margin_mm: float = 0.0


# ---------------------------------------------------------------------------
# Guitar model spec (canonical model definition)
# ---------------------------------------------------------------------------

@dataclass
class GuitarModelSpec:
    """
    Generalized specification for a guitar model from the instrument
    geometry perspective.

    This is NOT a full CAD or CAM spec – just the key parameters that
    geometry, calculators, RMOS and Art Studio will need.

    Fields:
        id: Machine-readable ID ("strat_25_5", "lp_24_75", etc.)
        display_name: Human-readable model name
        scale_profile_id: Key into STANDARD_SCALE_PROFILES
        num_strings: Usually 6, but can be 7, 8, etc.
        strings: List of StringSpec describing the tuned string set
        nut_spacing: StringSpacingSpec for the nut
        bridge_spacing: StringSpacingSpec for the bridge
        neck_taper: NeckTaperSpec with nut/heel widths and taper length
        body_outline_id: Reference to a DXF/SVG/template asset (optional)
    """
    id: str
    display_name: str
    scale_profile_id: str
    num_strings: int
    strings: List[StringSpec]
    nut_spacing: StringSpacingSpec
    bridge_spacing: StringSpacingSpec
    neck_taper: NeckTaperSpec
    body_outline_id: Optional[str] = None

    def scale_profile(self) -> ScaleProfile:
        """
        Resolve the associated ScaleProfile from STANDARD_SCALE_PROFILES.

        Returns:
            ScaleProfile instance

        Raises:
            KeyError: If the profile is not defined
        """
        return STANDARD_SCALE_PROFILES[self.scale_profile_id]


# ---------------------------------------------------------------------------
# Example preset models (placeholder numbers - refine from real data later)
# ---------------------------------------------------------------------------

# Basic 10–46 set tuned E standard (placeholders – refine later)
STANDARD_10_46_E_STANDARD: List[StringSpec] = [
    StringSpec(name="E4", gauge_in=0.010, is_wound=False, frequency_hz=329.63, open_note="E4"),
    StringSpec(name="B3", gauge_in=0.013, is_wound=False, frequency_hz=246.94, open_note="B3"),
    StringSpec(name="G3", gauge_in=0.017, is_wound=False, frequency_hz=196.00, open_note="G3"),
    StringSpec(name="D3", gauge_in=0.026, is_wound=True,  frequency_hz=146.83, open_note="D3"),
    StringSpec(name="A2", gauge_in=0.036, is_wound=True,  frequency_hz=110.00, open_note="A2"),
    StringSpec(name="E2", gauge_in=0.046, is_wound=True,  frequency_hz=82.41,  open_note="E2"),
]

# Example Strat-style model
STRAT_25_5_MODEL = GuitarModelSpec(
    id="strat_25_5",
    display_name="Strat-style 25.5\"",
    scale_profile_id="fender_25_5",
    num_strings=6,
    strings=STANDARD_10_46_E_STANDARD,
    nut_spacing=StringSpacingSpec(
        num_strings=6,
        e_to_e_mm=35.0,           # placeholder: ~35 mm string spread at nut
        bass_edge_margin_mm=3.0,  # more wood outside low E
        treble_edge_margin_mm=2.5,
    ),
    bridge_spacing=StringSpacingSpec(
        num_strings=6,
        e_to_e_mm=52.0,           # typical 52 mm E-to-E at bridge
    ),
    neck_taper=NeckTaperSpec(
        nut_width_mm=42.0,        # 42 mm nut (Tier 1 real value)
        heel_width_mm=56.0,       # placeholder; refine later
        taper_length_in=16.0,     # distance from nut to heel (approx)
    ),
    body_outline_id="strat_body_v1",  # maps to DXF registry
)

# Example LP-style model
LP_24_75_MODEL = GuitarModelSpec(
    id="lp_24_75",
    display_name="LP-style 24.75\"",
    scale_profile_id="gibson_24_75",
    num_strings=6,
    strings=STANDARD_10_46_E_STANDARD,
    nut_spacing=StringSpacingSpec(
        num_strings=6,
        e_to_e_mm=35.0,
        bass_edge_margin_mm=3.0,
        treble_edge_margin_mm=2.5,
    ),
    bridge_spacing=StringSpacingSpec(
        num_strings=6,
        e_to_e_mm=50.0,           # many TOM bridges are ≈50 mm spread
    ),
    neck_taper=NeckTaperSpec(
        nut_width_mm=43.0,        # 43 mm nut (Tier 1 real value)
        heel_width_mm=57.0,       # placeholder
        taper_length_in=16.0,
    ),
    body_outline_id="lp_body_v1",
)

PRESET_MODELS: Dict[str, GuitarModelSpec] = {
    STRAT_25_5_MODEL.id: STRAT_25_5_MODEL,
    LP_24_75_MODEL.id: LP_24_75_MODEL,
}


# ---------------------------------------------------------------------------
# Factory: GuitarModelSpec → InstrumentSpec (backward compatibility)
# ---------------------------------------------------------------------------

def guitar_model_to_instrument_spec(model: GuitarModelSpec):
    """
    Factory function: Convert GuitarModelSpec → InstrumentSpec.
    
    This allows the new GuitarModelSpec system to feed the existing
    InstrumentSpec consumers (RMOS, Art Studio, CAM) without breaking them.
    
    Args:
        model: GuitarModelSpec instance
        
    Returns:
        InstrumentSpec from neck.neck_profiles
        
    Example:
        >>> from instrument_geometry.model_spec import PRESET_MODELS, guitar_model_to_instrument_spec
        >>> model = PRESET_MODELS["strat_25_5"]
        >>> spec = guitar_model_to_instrument_spec(model)
        >>> spec.scale_length_mm
        648.0
    """
    from .neck.neck_profiles import InstrumentSpec
    
    profile = model.scale_profile()
    
    # Determine instrument type based on scale/category
    if profile.scale_length_mm > 800:
        instrument_type = "bass"
    elif profile.scale_length_mm < 400:
        instrument_type = "ukulele"
    elif profile.num_frets <= 19:
        instrument_type = "classical"
    elif "acoustic" in profile.id or "martin" in profile.id:
        instrument_type = "flat_top"
    else:
        instrument_type = "electric"
    
    # Simple tuning list from strings
    tuning = [s.open_note for s in model.strings] if model.strings else None
    
    return InstrumentSpec(
        instrument_type=instrument_type,
        scale_length_mm=profile.scale_length_mm,
        fret_count=profile.num_frets,
        string_count=model.num_strings,
        base_radius_mm=None,  # Not in GuitarModelSpec yet
        end_radius_mm=None,   # Not in GuitarModelSpec yet
        tuning=tuning,
        multiscale=profile.treble_scale_mm is not None,
        bass_scale_length_mm=profile.bass_scale_mm,
        treble_scale_length_mm=profile.treble_scale_mm,
    )
