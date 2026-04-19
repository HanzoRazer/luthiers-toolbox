"""
Curvature Correction — Instrument-Specific Profile Thresholds
=============================================================

Provides instrument-specific curvature thresholds for the CurvatureProfiler.
Each instrument has different expected radius ranges and stability thresholds
based on its body shape (e.g., Explorer has sharp horn tips, dreadnought has
smooth bouts).

Zone-specific thresholds enable the profiler to:
- Accept tight curves in horn_tip zones that would be rejected as noise elsewhere
- Apply instrument-appropriate stability thresholds
- Use spec-based epsilon values for simplification

Integration: CurvatureProfiler accepts InstrumentCurvatureProfile at init time.

Location: instrument_geometry/curvature_correction.py (moved from services/)

Author: Production Shop
Date: 2026-04-14
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Zone names for body regions
ZONE_WAIST = "waist"
ZONE_BOUT = "bout"            # Upper and lower bouts
ZONE_HORN_TIP = "horn_tip"    # Explorer, Flying V tips
ZONE_CUTAWAY = "cutaway"      # Florentine/Venetian cutaways
ZONE_DEFAULT = "default"


# Empirically measured radii by zone and instrument (mm)
# Source: Production Shop measurements on physical templates
MEASURED_RADII: Dict[str, Dict[str, float]] = {
    "stratocaster": {
        "waist": 180.0,
        "bout": 250.0,
        "horn_tip": 45.0,
        "cutaway": 80.0,
    },
    "telecaster": {
        "waist": 200.0,
        "bout": 240.0,
        "horn_tip": 55.0,
    },
    "les_paul": {
        "waist": 120.0,
        "bout": 200.0,
        "cutaway": 70.0,
    },
    "gibson_explorer": {
        "waist": 150.0,
        "bout": 100.0,      # Explorer has short straight sections, not bouts
        "horn_tip": 25.0,   # Very sharp angular tips
    },
    "flying_v": {
        "waist": 80.0,      # Narrow center
        "bout": 60.0,       # No traditional bouts
        "horn_tip": 20.0,   # Sharp V tips
    },
    "dreadnought": {
        "waist": 140.0,
        "bout": 280.0,
        "default": 200.0,
    },
    "jumbo": {
        "waist": 160.0,
        "bout": 320.0,
        "default": 220.0,
    },
    "classical": {
        "waist": 130.0,
        "bout": 260.0,
        "default": 180.0,
    },
    "cuatro": {
        "waist": 90.0,
        "bout": 160.0,
        "default": 120.0,
    },
    "om_000": {
        "bout": 47.1,
        "waist": 45.0,
        "default": 200.0,
    },
    "melody_maker": {
        "bout": 118.0,
        "waist": 36.0,
        "horn_tip": 5.7,
        "cutaway": 22.0,
        "default": 200.0,
    },
}


# Default zone stability thresholds (used when profile not available)
DEFAULT_STABILITY_BY_ZONE: Dict[str, float] = {
    ZONE_WAIST: 0.45,      # Tighter curves at waist
    ZONE_BOUT: 0.55,       # Smoother curves at bouts
    ZONE_HORN_TIP: 0.70,   # Allow more variation at sharp tips
    ZONE_CUTAWAY: 0.60,    # Moderate for cutaways
    ZONE_DEFAULT: 0.50,    # Global default
}


@dataclass
class InstrumentCurvatureProfile:
    """
    Instrument-specific curvature thresholds for CurvatureProfiler.

    Replaces class constants with per-instrument values.
    """
    spec_name: str

    # Global stability threshold (replaces STABILITY_THRESHOLD_PROFILE)
    stability_threshold: float = 0.5

    # Zone-specific stability thresholds
    stability_by_zone: Dict[str, float] = field(default_factory=dict)

    # Radius bounds (replaces MIN_PROFILE_RADIUS_MM, MAX_PROFILE_RADIUS_MM)
    min_profile_radius_mm: float = 30.0
    max_profile_radius_mm: float = 800.0

    # Zone-specific expected radii (from MEASURED_RADII)
    expected_radii_by_zone: Dict[str, float] = field(default_factory=dict)

    # Epsilon factors by curvature class
    epsilon_profile_curve: float = 0.0005
    epsilon_thin_stroke: float = 0.00075
    epsilon_annotation: float = 0.001
    epsilon_straight_line: float = 0.002
    epsilon_noise: float = 0.01

    def get_stability(self, zone: str = ZONE_DEFAULT) -> float:
        """Get stability threshold for a specific zone."""
        if zone in self.stability_by_zone:
            return self.stability_by_zone[zone]
        return self.stability_threshold

    def get_expected_radius(self, zone: str = ZONE_DEFAULT) -> Optional[float]:
        """Get expected radius for a zone (None if not defined)."""
        return self.expected_radii_by_zone.get(zone)

    def is_radius_plausible(
        self,
        radius_mm: float,
        zone: str = ZONE_DEFAULT,
        tolerance: float = 2.0,
    ) -> bool:
        """
        Check if radius is plausible for this instrument/zone.

        Args:
            radius_mm: Measured radius in mm
            zone: Body zone (waist, bout, horn_tip, etc.)
            tolerance: Multiplier for expected radius range

        Returns:
            True if radius is within expected range for zone
        """
        expected = self.get_expected_radius(zone)
        if expected is None:
            # No zone-specific expectation, use global bounds
            return self.min_profile_radius_mm <= radius_mm <= self.max_profile_radius_mm

        # Zone-specific check with tolerance
        low = expected / tolerance
        high = expected * tolerance
        return low <= radius_mm <= high


def get_instrument_profile(spec_name: Optional[str] = None) -> InstrumentCurvatureProfile:
    """
    Load or create curvature profile for an instrument.

    Args:
        spec_name: Instrument spec name (e.g., "gibson_explorer", "dreadnought")
                   If None, returns default generic profile.

    Returns:
        InstrumentCurvatureProfile with instrument-specific thresholds
    """
    if spec_name is None:
        return InstrumentCurvatureProfile(
            spec_name="generic",
            stability_by_zone=DEFAULT_STABILITY_BY_ZONE.copy(),
        )

    # Normalize spec name
    spec_key = spec_name.lower().replace("-", "_").replace(" ", "_")

    # Load measured radii if available
    expected_radii = MEASURED_RADII.get(spec_key, {})

    # Build zone stability thresholds
    # Instruments with angular shapes (Explorer, Flying V) get looser thresholds
    stability_by_zone = DEFAULT_STABILITY_BY_ZONE.copy()

    if spec_key in ("gibson_explorer", "flying_v"):
        # Angular instruments: allow more curvature variation
        stability_by_zone[ZONE_HORN_TIP] = 0.85
        stability_by_zone[ZONE_BOUT] = 0.65
        stability_by_zone[ZONE_DEFAULT] = 0.60
        min_radius = 15.0  # Sharp tips allowed
        max_radius = 600.0
    elif spec_key in ("les_paul", "es335", "gibson_sg"):
        # Cutaway guitars: moderate stability
        stability_by_zone[ZONE_CUTAWAY] = 0.65
        min_radius = 25.0
        max_radius = 700.0
    elif spec_key in ("dreadnought", "jumbo", "om_000", "classical", "j45"):
        # Acoustic guitars: smooth curves
        stability_by_zone[ZONE_BOUT] = 0.50
        stability_by_zone[ZONE_WAIST] = 0.40
        min_radius = 40.0
        max_radius = 900.0
    elif spec_key == "cuatro":
        # Small acoustic: tighter radii
        min_radius = 30.0
        max_radius = 500.0
    else:
        # Default values
        min_radius = 30.0
        max_radius = 800.0

    return InstrumentCurvatureProfile(
        spec_name=spec_key,
        stability_by_zone=stability_by_zone,
        min_profile_radius_mm=min_radius,
        max_profile_radius_mm=max_radius,
        expected_radii_by_zone=expected_radii,
    )


def get_correction_epsilon(
    spec_name: Optional[str],
    zone: str = ZONE_DEFAULT,
    classification: str = "profile_curve",
) -> float:
    """
    Get recommended epsilon for simplification based on instrument and zone.

    Args:
        spec_name: Instrument spec name (or None for default)
        zone: Body zone
        classification: Curvature classification (profile_curve, thin_stroke, etc.)

    Returns:
        Epsilon factor for approxPolyDP
    """
    profile = get_instrument_profile(spec_name)

    # Map classification to epsilon
    epsilon_map = {
        "profile_curve": profile.epsilon_profile_curve,
        "profile_curve_fragment": profile.epsilon_profile_curve,
        "micro_fragment": 0.0,  # No simplification for micro fragments
        "thin_stroke": profile.epsilon_thin_stroke,
        "annotation": profile.epsilon_annotation,
        "straight_line": profile.epsilon_straight_line,
        "noise": profile.epsilon_noise,
    }

    base_epsilon = epsilon_map.get(classification, profile.epsilon_annotation)

    # Zone-based adjustment: horn tips and cutaways get tighter epsilon
    if zone == ZONE_HORN_TIP:
        return base_epsilon * 0.5  # Preserve sharp corners
    elif zone == ZONE_CUTAWAY:
        return base_epsilon * 0.75

    return base_epsilon
