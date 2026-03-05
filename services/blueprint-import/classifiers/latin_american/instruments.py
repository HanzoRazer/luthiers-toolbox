"""
Latin American Instrument Profiles
==================================

Defines characteristic measurements and features for each instrument type.

Author: Luthier's Toolbox
Version: 4.0.0-alpha
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class InstrumentFamily(Enum):
    """Instrument family classification."""
    CUATRO = "cuatro"
    TIPLE = "tiple"
    REQUINTO = "requinto"
    CHARANGO = "charango"
    BANDOLA = "bandola"
    GUITAR = "guitar"  # Reference baseline


@dataclass
class InstrumentProfile:
    """
    Profile defining characteristic dimensions for an instrument type.

    All dimensions in millimeters unless specified.
    Ranges given as (min, typical, max).
    """
    name: str
    family: InstrumentFamily

    # Scale length (nut to bridge saddle)
    scale_length: Tuple[float, float, float]  # (min, typical, max) mm

    # Body dimensions
    body_length: Tuple[float, float, float]
    upper_bout_width: Tuple[float, float, float]
    waist_width: Tuple[float, float, float]
    lower_bout_width: Tuple[float, float, float]
    body_depth: Tuple[float, float, float]

    # Soundhole
    soundhole_diameter: Tuple[float, float, float]
    soundhole_offset: Tuple[float, float, float]  # From body top

    # Neck
    nut_width: Tuple[float, float, float]
    neck_width_at_12th: Tuple[float, float, float]
    fret_count: Tuple[int, int, int]

    # Strings
    string_count: int
    course_count: int  # Paired strings count as 1 course

    # Distinctive features
    has_rosette: bool = True
    typical_rosette_style: str = "traditional"
    has_binding: bool = False
    typical_bracing: str = "fan"
    back_construction: str = "flat"  # flat, arched, bowl

    # Region/origin
    primary_region: str = ""
    alternate_names: List[str] = field(default_factory=list)

    def matches_scale(self, scale_mm: float, tolerance_pct: float = 0.05) -> float:
        """
        Calculate confidence that a scale length matches this instrument.

        Args:
            scale_mm: Measured scale length in mm
            tolerance_pct: Tolerance as percentage (default 5%)

        Returns:
            Confidence score 0.0 to 1.0
        """
        min_scale, typical, max_scale = self.scale_length

        # Exact typical match
        if abs(scale_mm - typical) < typical * 0.01:
            return 1.0

        # Within expected range
        if min_scale <= scale_mm <= max_scale:
            # Score based on distance from typical
            distance = abs(scale_mm - typical)
            range_size = max(typical - min_scale, max_scale - typical)
            return max(0.7, 1.0 - (distance / range_size) * 0.3)

        # Outside range but within tolerance
        expanded_min = min_scale * (1 - tolerance_pct)
        expanded_max = max_scale * (1 + tolerance_pct)

        if expanded_min <= scale_mm <= expanded_max:
            return 0.5

        return 0.0

    def matches_body_width(self, lower_bout_mm: float, tolerance_pct: float = 0.08) -> float:
        """
        Calculate confidence for body width match.

        Args:
            lower_bout_mm: Measured lower bout width in mm
            tolerance_pct: Tolerance as percentage

        Returns:
            Confidence score 0.0 to 1.0
        """
        min_w, typical, max_w = self.lower_bout_width

        if abs(lower_bout_mm - typical) < typical * 0.02:
            return 1.0

        if min_w <= lower_bout_mm <= max_w:
            distance = abs(lower_bout_mm - typical)
            range_size = max(typical - min_w, max_w - typical)
            return max(0.6, 1.0 - (distance / range_size) * 0.4)

        expanded_min = min_w * (1 - tolerance_pct)
        expanded_max = max_w * (1 + tolerance_pct)

        if expanded_min <= lower_bout_mm <= expanded_max:
            return 0.4

        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Export profile as dictionary."""
        return {
            'name': self.name,
            'family': self.family.value,
            'scale_length': self.scale_length,
            'body_length': self.body_length,
            'lower_bout_width': self.lower_bout_width,
            'string_count': self.string_count,
            'course_count': self.course_count,
            'primary_region': self.primary_region
        }


# ============================================================================
# Instrument Definitions
# ============================================================================

VenezuelanCuatro = InstrumentProfile(
    name="Venezuelan Cuatro",
    family=InstrumentFamily.CUATRO,

    # Scale: typically 520-540mm (shorter than guitar)
    scale_length=(510.0, 530.0, 550.0),

    # Body: smaller than guitar
    body_length=(380.0, 400.0, 420.0),
    upper_bout_width=(180.0, 195.0, 210.0),
    waist_width=(145.0, 155.0, 170.0),
    lower_bout_width=(240.0, 260.0, 280.0),
    body_depth=(70.0, 80.0, 90.0),

    # Soundhole
    soundhole_diameter=(75.0, 85.0, 95.0),
    soundhole_offset=(90.0, 100.0, 115.0),

    # Neck
    nut_width=(38.0, 42.0, 46.0),
    neck_width_at_12th=(48.0, 52.0, 56.0),
    fret_count=(14, 17, 19),

    # Strings: 4 single strings
    string_count=4,
    course_count=4,

    # Features
    has_rosette=True,
    typical_rosette_style="traditional_circular",
    has_binding=False,
    typical_bracing="ladder",
    back_construction="flat",

    primary_region="Venezuela",
    alternate_names=["Cuatro Venezolano", "Cuatro Llanero"]
)


PuertoRicanCuatro = InstrumentProfile(
    name="Puerto Rican Cuatro",
    family=InstrumentFamily.CUATRO,

    # Scale: longer than Venezuelan, 10 strings
    scale_length=(540.0, 560.0, 580.0),

    # Body: larger, violin-shaped
    body_length=(420.0, 450.0, 480.0),
    upper_bout_width=(200.0, 220.0, 240.0),
    waist_width=(150.0, 165.0, 180.0),
    lower_bout_width=(280.0, 310.0, 340.0),
    body_depth=(80.0, 90.0, 100.0),

    # Soundhole
    soundhole_diameter=(80.0, 90.0, 100.0),
    soundhole_offset=(100.0, 115.0, 130.0),

    # Neck
    nut_width=(42.0, 48.0, 52.0),
    neck_width_at_12th=(52.0, 58.0, 64.0),
    fret_count=(17, 19, 22),

    # Strings: 10 strings in 5 courses
    string_count=10,
    course_count=5,

    # Features
    has_rosette=True,
    typical_rosette_style="traditional_circular",
    has_binding=True,
    typical_bracing="fan",
    back_construction="arched",  # Distinctive arched back

    primary_region="Puerto Rico",
    alternate_names=["Cuatro Puertorriqueno", "Cuatro Antiguo"]
)


ColombianTiple = InstrumentProfile(
    name="Colombian Tiple",
    family=InstrumentFamily.TIPLE,

    # Scale: similar to guitar
    scale_length=(540.0, 560.0, 575.0),

    # Body: guitar-like but narrower
    body_length=(400.0, 430.0, 460.0),
    upper_bout_width=(200.0, 215.0, 230.0),
    waist_width=(155.0, 170.0, 185.0),
    lower_bout_width=(270.0, 290.0, 310.0),
    body_depth=(85.0, 95.0, 105.0),

    # Soundhole
    soundhole_diameter=(80.0, 88.0, 95.0),
    soundhole_offset=(95.0, 110.0, 125.0),

    # Neck
    nut_width=(44.0, 48.0, 52.0),
    neck_width_at_12th=(54.0, 58.0, 62.0),
    fret_count=(17, 19, 22),

    # Strings: 12 strings in 4 courses (3 per course)
    string_count=12,
    course_count=4,

    # Features
    has_rosette=True,
    typical_rosette_style="colombian_mosaic",
    has_binding=True,
    typical_bracing="fan",
    back_construction="flat",

    primary_region="Colombia",
    alternate_names=["Tiple Colombiano"]
)


Requinto = InstrumentProfile(
    name="Requinto",
    family=InstrumentFamily.REQUINTO,

    # Scale: shorter than guitar (typically 530-555mm)
    scale_length=(520.0, 540.0, 560.0),

    # Body: 7/8 guitar size
    body_length=(400.0, 420.0, 440.0),
    upper_bout_width=(210.0, 225.0, 240.0),
    waist_width=(165.0, 175.0, 190.0),
    lower_bout_width=(290.0, 310.0, 330.0),
    body_depth=(85.0, 92.0, 100.0),

    # Soundhole
    soundhole_diameter=(82.0, 90.0, 98.0),
    soundhole_offset=(100.0, 112.0, 125.0),

    # Neck
    nut_width=(48.0, 52.0, 56.0),
    neck_width_at_12th=(58.0, 62.0, 68.0),
    fret_count=(18, 19, 22),

    # Strings: 6 strings like guitar
    string_count=6,
    course_count=6,

    # Features
    has_rosette=True,
    typical_rosette_style="traditional_circular",
    has_binding=True,
    typical_bracing="fan",
    back_construction="flat",

    primary_region="Mexico",
    alternate_names=["Requinto Jarocho", "Guitarra Requinto"]
)


Charango = InstrumentProfile(
    name="Charango",
    family=InstrumentFamily.CHARANGO,

    # Scale: very short (typically 370mm)
    scale_length=(350.0, 370.0, 400.0),

    # Body: very small, often armadillo-shaped
    body_length=(230.0, 260.0, 290.0),
    upper_bout_width=(120.0, 140.0, 160.0),
    waist_width=(95.0, 110.0, 125.0),
    lower_bout_width=(160.0, 180.0, 200.0),
    body_depth=(55.0, 70.0, 85.0),

    # Soundhole
    soundhole_diameter=(45.0, 55.0, 65.0),
    soundhole_offset=(55.0, 65.0, 80.0),

    # Neck
    nut_width=(30.0, 35.0, 40.0),
    neck_width_at_12th=(38.0, 42.0, 48.0),
    fret_count=(15, 17, 20),

    # Strings: 10 strings in 5 courses
    string_count=10,
    course_count=5,

    # Features
    has_rosette=True,
    typical_rosette_style="andean_geometric",
    has_binding=False,
    typical_bracing="ladder",
    back_construction="bowl",  # Traditional armadillo shell or carved

    primary_region="Bolivia/Peru",
    alternate_names=["Charango Boliviano", "Charango Andino"]
)


Bandola = InstrumentProfile(
    name="Bandola",
    family=InstrumentFamily.BANDOLA,

    # Scale: varies by regional type
    scale_length=(420.0, 450.0, 480.0),

    # Body: pear-shaped or guitar-like
    body_length=(320.0, 350.0, 380.0),
    upper_bout_width=(180.0, 200.0, 220.0),
    waist_width=(140.0, 155.0, 170.0),
    lower_bout_width=(240.0, 265.0, 290.0),
    body_depth=(65.0, 75.0, 85.0),

    # Soundhole
    soundhole_diameter=(65.0, 75.0, 85.0),
    soundhole_offset=(75.0, 85.0, 100.0),

    # Neck
    nut_width=(32.0, 38.0, 44.0),
    neck_width_at_12th=(42.0, 48.0, 54.0),
    fret_count=(14, 17, 19),

    # Strings: varies (6-16 depending on type)
    string_count=8,  # Most common
    course_count=4,

    # Features
    has_rosette=True,
    typical_rosette_style="traditional_circular",
    has_binding=False,
    typical_bracing="ladder",
    back_construction="flat",

    primary_region="Venezuela/Colombia",
    alternate_names=["Bandola Llanera", "Bandola Andina", "Bandola Oriental"]
)


# All profiles for iteration
ALL_PROFILES: List[InstrumentProfile] = [
    VenezuelanCuatro,
    PuertoRicanCuatro,
    ColombianTiple,
    Requinto,
    Charango,
    Bandola
]


def get_profile_by_name(name: str) -> Optional[InstrumentProfile]:
    """
    Get instrument profile by name or alternate name.

    Args:
        name: Instrument name to search

    Returns:
        InstrumentProfile or None
    """
    name_lower = name.lower()

    for profile in ALL_PROFILES:
        if profile.name.lower() == name_lower:
            return profile
        if any(alt.lower() == name_lower for alt in profile.alternate_names):
            return profile

    return None


def get_profiles_by_family(family: InstrumentFamily) -> List[InstrumentProfile]:
    """Get all profiles in a family."""
    return [p for p in ALL_PROFILES if p.family == family]
