"""
Instrument Geometry: Model Enumerations

Wave 14 Module - Instrument Geometry Core

Defines the canonical 19-model enum and status tracking for all supported
guitar/bass/ukulele models in the Luthier's Tool Box.

Usage:
    from instrument_geometry.models import InstrumentModelId, InstrumentModelStatus
    
    model = InstrumentModelId.STRAT
    print(model.value)  # "stratocaster"
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class InstrumentModelId(str, Enum):
    """
    Canonical instrument model identifiers.
    
    19 supported models covering:
    - Electric guitars: Strat, Tele, Les Paul, PRS, SG, ES-335, Flying V, Explorer, Firebird, Moderne
    - Acoustic guitars: Dreadnought, OM/000, J-45, Jumbo J-200, Gibson L-00, Classical
    - Bass: Jazz Bass
    - Other: Archtop, Ukulele
    
    Each value is a lowercase slug used in:
    - JSON registry keys
    - File naming conventions
    - API endpoint parameters
    """
    # Electric - Fender style
    STRAT = "stratocaster"
    TELE = "telecaster"
    
    # Electric - Gibson style
    LES_PAUL = "les_paul"
    SG = "sg"
    ES_335 = "es_335"
    FLYING_V = "flying_v"
    EXPLORER = "explorer"
    FIREBIRD = "firebird"
    MODERNE = "moderne"
    
    # Electric - Other
    PRS = "prs"
    ARCHTOP = "archtop"
    
    # Acoustic - Steel string
    DREADNOUGHT = "dreadnought"
    OM_000 = "om_000"
    J_45 = "j_45"
    JUMBO_J200 = "jumbo_j200"
    GIBSON_L_00 = "gibson_l_00"
    
    # Acoustic - Nylon string
    CLASSICAL = "classical"
    
    # Bass
    JAZZ_BASS = "jazz_bass"
    
    # Other
    UKULELE = "ukulele"


class InstrumentModelStatus(str, Enum):
    """
    Implementation status for each instrument model.
    
    Used by the registry to track which models have:
    - Full geometry implementations
    - Partial stubs
    - Reference data only
    
    Statuses:
    - PRODUCTION: Fully implemented, tested, production-ready
    - PARTIAL: Some geometry available, missing features
    - STUB: Skeleton only, placeholder values
    - ASSETS_ONLY: DXF/PDF assets exist but no code implementation
    - REFERENCE: Documentation/specs only, no code
    - PLANNED: On roadmap but not started
    - LEGACY: Old implementation, needs migration
    - TEST_REF: Used for testing, not production
    """
    PRODUCTION = "PRODUCTION"
    PARTIAL = "PARTIAL"
    STUB = "STUB"
    ASSETS_ONLY = "ASSETS_ONLY"
    REFERENCE = "REFERENCE"
    PLANNED = "PLANNED"
    LEGACY = "LEGACY"
    TEST_REF = "TEST_REF"


class InstrumentCategory(str, Enum):
    """
    Instrument category for grouping models.
    """
    ELECTRIC_GUITAR = "electric_guitar"
    ACOUSTIC_GUITAR = "acoustic_guitar"
    BASS = "bass"
    UKULELE = "ukulele"
    ARCHTOP = "archtop"


@dataclass
class ScaleLengthSpec:
    """
    Scale length specification for fret calculations.
    
    Wave 16: Extended with model_id and description for registry lookups.
    
    Attributes:
        scale_length_mm: Nominal scale length in millimeters (alias: length_mm)
        num_frets: Number of frets (typically 20-24) (alias: fret_count)
        model_id: Optional InstrumentModelId this spec belongs to
        description: Human-readable description
        multiscale: Whether this is a fanned-fret instrument
        bass_length_mm: Scale length on bass side (if multiscale)
        treble_length_mm: Scale length on treble side (if multiscale)
    """
    scale_length_mm: float
    num_frets: int = 22
    model_id: Optional["InstrumentModelId"] = None
    description: str = ""
    multiscale: bool = False
    bass_length_mm: Optional[float] = None
    treble_length_mm: Optional[float] = None
    
    # Backward compat aliases
    @property
    def length_mm(self) -> float:
        return self.scale_length_mm
    
    @property
    def fret_count(self) -> int:
        return self.num_frets


@dataclass
class FretPosition:
    """
    Single fret position result.
    
    Attributes:
        fret_number: Fret number (1 = first fret)
        distance_from_nut_mm: Distance from nut to fret in mm
        spacing_from_previous_mm: Distance from previous fret (or nut) in mm
    """
    fret_number: int
    distance_from_nut_mm: float
    spacing_from_previous_mm: float


@dataclass 
class NeckProfileSpec:
    """
    Neck profile specification.
    
    Wave 16: Extended with model_id, twelve_fret_width, radius values, and description.
    
    Attributes:
        model_id: Optional InstrumentModelId this spec belongs to
        nut_width_mm: Width at nut
        twelve_fret_width_mm: Width at 12th fret (heel_width_mm alias for compat)
        thickness_1st_mm: Neck thickness at 1st fret
        thickness_12th_mm: Neck thickness at 12th fret
        radius_nut_mm: Fretboard radius at nut (mm)
        radius_12th_mm: Fretboard radius at 12th fret (mm) - same as nut for non-compound
        description: Human-readable description
        profile_shape: Shape code ("C", "D", "V", "U", "asymmetric")
    """
    model_id: Optional["InstrumentModelId"] = None
    nut_width_mm: float = 43.0
    twelve_fret_width_mm: float = 53.0
    thickness_1st_mm: float = 21.0
    thickness_12th_mm: float = 23.0
    radius_nut_mm: float = 300.0
    radius_12th_mm: float = 300.0
    description: str = ""
    profile_shape: str = "C"
    
    # Backward compat aliases
    @property
    def heel_width_mm(self) -> float:
        return self.twelve_fret_width_mm
    
    @property
    def thickness_1st_fret_mm(self) -> float:
        return self.thickness_1st_mm
    
    @property
    def thickness_12th_fret_mm(self) -> float:
        return self.thickness_12th_mm


@dataclass
class StringSpec:
    """
    Specification for a single guitar string.
    
    Wave 17: Added for GuitarModelSpec integration.
    
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


@dataclass
class ScaleProfile:
    """
    Complete scale length profile with multiscale support.
    
    Wave 17: Added for GuitarModelSpec integration.
    
    Attributes:
        id: Profile identifier (e.g. "fender_25_5", "gibson_24_75")
        scale_length_mm: Primary scale length in mm
        num_frets: Number of frets (typically 20-24)
        description: Human-readable description
        treble_scale_mm: Treble-side scale for multiscale (fanned fret)
        bass_scale_mm: Bass-side scale for multiscale
        perpendicular_fret: Fret number where strings are perpendicular (multiscale pivot)
    """
    id: str
    scale_length_mm: float
    num_frets: int
    description: str = ""
    treble_scale_mm: Optional[float] = None
    bass_scale_mm: Optional[float] = None
    perpendicular_fret: Optional[int] = None


# Common scale lengths for quick reference
COMMON_SCALE_LENGTHS = {
    "fender": ScaleLengthSpec(scale_length_mm=648.0, num_frets=22),        # 25.5"
    "gibson": ScaleLengthSpec(scale_length_mm=628.65, num_frets=22),       # 24.75"
    "prs": ScaleLengthSpec(scale_length_mm=635.0, num_frets=24),           # 25"
    "classical": ScaleLengthSpec(scale_length_mm=650.0, num_frets=19),     # 25.6"
    "dreadnought": ScaleLengthSpec(scale_length_mm=645.16, num_frets=20),  # 25.4"
    "bass_long": ScaleLengthSpec(scale_length_mm=863.6, num_frets=21),     # 34"
    "bass_short": ScaleLengthSpec(scale_length_mm=762.0, num_frets=21),    # 30"
    "ukulele_soprano": ScaleLengthSpec(scale_length_mm=330.0, num_frets=12),
    "ukulele_concert": ScaleLengthSpec(scale_length_mm=381.0, num_frets=15),
    "ukulele_tenor": ScaleLengthSpec(scale_length_mm=432.0, num_frets=17),
}


# Model category mapping
MODEL_CATEGORIES = {
    InstrumentModelId.STRAT: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.TELE: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.LES_PAUL: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.SG: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.ES_335: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.FLYING_V: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.EXPLORER: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.FIREBIRD: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.MODERNE: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.PRS: InstrumentCategory.ELECTRIC_GUITAR,
    InstrumentModelId.ARCHTOP: InstrumentCategory.ARCHTOP,
    InstrumentModelId.DREADNOUGHT: InstrumentCategory.ACOUSTIC_GUITAR,
    InstrumentModelId.OM_000: InstrumentCategory.ACOUSTIC_GUITAR,
    InstrumentModelId.J_45: InstrumentCategory.ACOUSTIC_GUITAR,
    InstrumentModelId.JUMBO_J200: InstrumentCategory.ACOUSTIC_GUITAR,
    InstrumentModelId.GIBSON_L_00: InstrumentCategory.ACOUSTIC_GUITAR,
    InstrumentModelId.CLASSICAL: InstrumentCategory.ACOUSTIC_GUITAR,
    InstrumentModelId.JAZZ_BASS: InstrumentCategory.BASS,
    InstrumentModelId.UKULELE: InstrumentCategory.UKULELE,
}
