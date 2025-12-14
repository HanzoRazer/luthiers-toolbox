"""
Instrument Geometry: Profile Dataclasses

High-level instrument description dataclasses used by RMOS / Art Studio
to derive neck/fretboard/bridge geometry.

See docs/KnowledgeBase/Instrument_Geometry/ for theory and references.

Moved from: instrument_geometry/profiles.py (Wave 14 reorg)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..models import InstrumentModelId, NeckProfileSpec


@dataclass
class InstrumentSpec:
    """
    High-level instrument description.

    This is the object RMOS / Art Studio should use when they want
    to derive neck/fretboard/bridge geometry.

    Example:
        InstrumentSpec(
            instrument_type="electric",
            scale_length_mm=648.0,  # 25.5"
            fret_count=22,
            string_count=6,
            base_radius_mm=241.3,   # 9.5"
            end_radius_mm=304.8,    # 12"
        )

    Common Scale Lengths:
        - Fender: 648.0 mm (25.5")
        - Gibson: 628.65 mm (24.75")
        - PRS: 635.0 mm (25")
        - Acoustic Dreadnought: 645.16 mm (25.4")

    Common Radius Values:
        - Vintage Fender: 184.15 mm (7.25")
        - Modern Fender: 241.3 mm (9.5")
        - Gibson: 304.8 mm (12")
        - Ibanez: 400+ mm (15.75"+) or flat
    """

    instrument_type: str  # "electric", "flat_top", "archtop", "classical", "bass"
    scale_length_mm: float
    fret_count: int
    string_count: int

    base_radius_mm: Optional[float] = None
    end_radius_mm: Optional[float] = None  # for compound radius
    tuning: Optional[List[str]] = None     # e.g. ["E", "A", "D", "G", "B", "E"]

    # Optional multi-scale parameters
    multiscale: bool = False
    bass_scale_length_mm: Optional[float] = None  # for fanned frets
    treble_scale_length_mm: Optional[float] = None

    def is_compound_radius(self) -> bool:
        """Check if this instrument has compound radius."""
        return (
            self.base_radius_mm is not None
            and self.end_radius_mm is not None
            and self.base_radius_mm != self.end_radius_mm
        )

    def is_multiscale(self) -> bool:
        """Check if this is a multiscale/fanned fret instrument."""
        return (
            self.multiscale
            and self.bass_scale_length_mm is not None
            and self.treble_scale_length_mm is not None
        )


@dataclass
class FretboardSpec:
    """
    Fretboard geometric parameters.

    This is narrower than InstrumentSpec and focuses on the board itself.
    Used for generating fretboard outlines, fret slot positions, and
    radius profiles.

    Example:
        FretboardSpec(
            nut_width_mm=42.0,      # 1.65"
            heel_width_mm=56.0,     # ~2.2"
            scale_length_mm=648.0,  # 25.5"
            fret_count=22,
            base_radius_mm=241.3,   # 9.5"
            end_radius_mm=304.8,    # 12"
        )
    """

    nut_width_mm: float
    heel_width_mm: float
    scale_length_mm: float
    fret_count: int

    base_radius_mm: Optional[float] = None
    end_radius_mm: Optional[float] = None  # for compound radius

    # Optional: fretboard extension past last fret (common on acoustics)
    extension_mm: float = 0.0

    # Optional: overhang past the nut (for binding, etc.)
    nut_overhang_mm: float = 0.0

    def taper_per_mm(self) -> float:
        """
        Calculate the taper rate (width increase per mm of length).

        Returns:
            Width increase per mm from nut to heel.
        """
        if self.scale_length_mm <= 0:
            return 0.0
        # Approximation: heel is typically at last fret position
        # For exact calculation, use fret position at fret_count
        return (self.heel_width_mm - self.nut_width_mm) / self.scale_length_mm


@dataclass
class BridgeSpec:
    """
    Bridge-related parameters for both flat-top and archtop instruments.

    For electric guitars, this can represent the reference line where
    saddles sit; for archtops, it can describe a floating bridge.

    Example (Electric):
        BridgeSpec(
            scale_length_mm=648.0,
            intonation_offsets_mm={
                "E6": 2.5,   # Low E
                "A5": 2.0,
                "D4": 1.5,
                "G3": 1.0,
                "B2": 1.5,
                "E1": 2.0,   # High E
            },
            base_height_mm=12.0,
            radius_mm=241.3,
        )

    Example (Archtop):
        BridgeSpec(
            scale_length_mm=635.0,
            intonation_offsets_mm={"E6": 3.0, "E1": 2.0},
            base_height_mm=25.0,  # Floating bridge height
            radius_mm=355.6,      # 14" radius
        )
    """

    scale_length_mm: float
    intonation_offsets_mm: Dict[str, float] = field(default_factory=dict)
    base_height_mm: float = 0.0
    radius_mm: Optional[float] = None  # bridge top radius, if applicable

    # Archtop-specific
    is_floating: bool = False
    foot_width_mm: Optional[float] = None
    foot_length_mm: Optional[float] = None

    def get_compensated_position_mm(self, string_id: str) -> float:
        """
        Get the compensated saddle position for a specific string.

        Args:
            string_id: String identifier (e.g., "E6", "B2")

        Returns:
            Distance from nut to saddle in mm.
        """
        offset = self.intonation_offsets_mm.get(string_id, 0.0)
        return self.scale_length_mm + offset


@dataclass
class RadiusProfile:
    """
    Describes a radius profile for the fretboard.

    Supports:
    - Single radius (constant across fretboard)
    - Compound radius (linear interpolation from base to end)
    - Custom radius curve (for non-linear transitions)
    """

    base_radius_mm: float
    end_radius_mm: Optional[float] = None  # None = single radius

    # For custom curves, specify radius at specific fret positions
    # Format: {fret_number: radius_mm}
    custom_radii: Optional[Dict[int, float]] = None

    def is_compound(self) -> bool:
        """Check if this is a compound radius profile."""
        return self.end_radius_mm is not None and self.end_radius_mm != self.base_radius_mm

    def get_radius_at_position(self, position_ratio: float) -> float:
        """
        Get the radius at a given position along the fretboard.

        Args:
            position_ratio: 0.0 = nut, 1.0 = end of fretboard

        Returns:
            Radius in mm at that position.
        """
        if not self.is_compound():
            return self.base_radius_mm

        # Linear interpolation for compound radius
        position_ratio = max(0.0, min(1.0, position_ratio))
        return self.base_radius_mm + (self.end_radius_mm - self.base_radius_mm) * position_ratio


# =============================================================================
# Wave 16: get_default_neck_profile() - Real Tier 1 Geometry
# =============================================================================

def get_default_neck_profile(model_id: InstrumentModelId) -> NeckProfileSpec:
    """
    Return a default neck profile for a given model.

    Wave 16: Real Tier 1 geometry for:
      - Stratocaster
      - Les Paul
      - Dreadnought acoustic

    All other models get a generic placeholder that we can refine in later waves.
    """

    # --- Tier 1: Stratocaster (modern C, 9.5" radius) ----------------------
    if model_id == InstrumentModelId.STRAT:
        return NeckProfileSpec(
            model_id=model_id,
            nut_width_mm=42.0,
            twelve_fret_width_mm=52.0,
            thickness_1st_mm=21.0,
            thickness_12th_mm=23.0,
            radius_nut_mm=241.3,   # 9.5"
            radius_12th_mm=241.3,  # uniform radius for now
            description="Stratocaster: modern C, 9.5\" radius (Tier 1 real geometry)",
        )

    # --- Tier 1: Les Paul (approx '59 style) -------------------------------
    if model_id == InstrumentModelId.LES_PAUL:
        return NeckProfileSpec(
            model_id=model_id,
            nut_width_mm=43.0,
            twelve_fret_width_mm=52.0,
            thickness_1st_mm=22.0,
            thickness_12th_mm=24.0,
            radius_nut_mm=304.8,   # 12"
            radius_12th_mm=304.8,  # uniform radius for now
            description="Les Paul style: ~'59 neck, 12\" radius (Tier 1 real geometry)",
        )

    # --- Tier 1: Dreadnought acoustic -------------------------------------
    if model_id == InstrumentModelId.DREADNOUGHT:
        return NeckProfileSpec(
            model_id=model_id,
            nut_width_mm=44.5,
            twelve_fret_width_mm=55.5,
            thickness_1st_mm=21.0,
            thickness_12th_mm=23.0,
            radius_nut_mm=406.4,   # 16"
            radius_12th_mm=406.4,  # uniform radius for now
            description="Dreadnought acoustic: 16\" radius (Tier 1 real geometry)",
        )

    # --- Optional: reasonable defaults for closely related models ----------

    if model_id == InstrumentModelId.TELE:
        # Tele often shares similar neck specs with Strat (varies by era)
        return NeckProfileSpec(
            model_id=model_id,
            nut_width_mm=42.0,
            twelve_fret_width_mm=52.0,
            thickness_1st_mm=21.5,
            thickness_12th_mm=23.5,
            radius_nut_mm=241.3,
            radius_12th_mm=241.3,
            description="Telecaster: modern C, 9.5\" radius (aligned with Strat family)",
        )

    if model_id in (
        InstrumentModelId.J_45,
        InstrumentModelId.OM_000,
        InstrumentModelId.JUMBO_J200,
        InstrumentModelId.GIBSON_L_00,
    ):
        # Share a general steel-string acoustic neck profile for now
        return NeckProfileSpec(
            model_id=model_id,
            nut_width_mm=44.5,
            twelve_fret_width_mm=55.5,
            thickness_1st_mm=21.0,
            thickness_12th_mm=23.0,
            radius_nut_mm=406.4,
            radius_12th_mm=406.4,
            description="Steel-string acoustic family neck (to be refined per model)",
        )

    if model_id == InstrumentModelId.CLASSICAL:
        return NeckProfileSpec(
            model_id=model_id,
            nut_width_mm=52.0,
            twelve_fret_width_mm=62.0,
            thickness_1st_mm=21.5,
            thickness_12th_mm=23.0,
            radius_nut_mm=10_000.0,  # effectively flat; classical boards are usually flat
            radius_12th_mm=10_000.0,
            description="Classical guitar: wide, nearly flat board (placeholder)",
        )

    # --- Fallback generic profile ------------------------------------------

    return NeckProfileSpec(
        model_id=model_id,
        nut_width_mm=43.0,
        twelve_fret_width_mm=53.0,
        thickness_1st_mm=21.0,
        thickness_12th_mm=23.0,
        radius_nut_mm=300.0,
        radius_12th_mm=300.0,
        description="Generic neck profile placeholder (Wave 16 fallback)",
    )
