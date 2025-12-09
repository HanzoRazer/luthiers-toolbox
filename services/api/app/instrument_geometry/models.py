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
    
    Attributes:
        length_mm: Nominal scale length in millimeters
        fret_count: Number of frets (typically 20-24)
        multiscale: Whether this is a fanned-fret instrument
        bass_length_mm: Scale length on bass side (if multiscale)
        treble_length_mm: Scale length on treble side (if multiscale)
    """
    length_mm: float
    fret_count: int = 22
    multiscale: bool = False
    bass_length_mm: Optional[float] = None
    treble_length_mm: Optional[float] = None


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
    
    Attributes:
        nut_width_mm: Width at nut
        heel_width_mm: Width at heel/body joint
        thickness_1st_fret_mm: Neck thickness at 1st fret
        thickness_12th_fret_mm: Neck thickness at 12th fret
        profile_shape: Shape code ("C", "D", "V", "U", "asymmetric")
    """
    nut_width_mm: float
    heel_width_mm: float
    thickness_1st_fret_mm: float = 20.0
    thickness_12th_fret_mm: float = 22.0
    profile_shape: str = "C"


# Common scale lengths for quick reference
COMMON_SCALE_LENGTHS = {
    "fender": ScaleLengthSpec(648.0, 22),        # 25.5"
    "gibson": ScaleLengthSpec(628.65, 22),       # 24.75"
    "prs": ScaleLengthSpec(635.0, 24),           # 25"
    "classical": ScaleLengthSpec(650.0, 19),     # 25.6"
    "dreadnought": ScaleLengthSpec(645.16, 20),  # 25.4"
    "bass_long": ScaleLengthSpec(863.6, 21),     # 34"
    "bass_short": ScaleLengthSpec(762.0, 21),    # 30"
    "ukulele_soprano": ScaleLengthSpec(330.0, 12),
    "ukulele_concert": ScaleLengthSpec(381.0, 15),
    "ukulele_tenor": ScaleLengthSpec(432.0, 17),
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
