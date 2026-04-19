"""
curvature_correction_unmerged.py
================================
UNMERGED: Bi-arc joining and chord/sagitta math not yet integrated into
services/api/app/instrument_geometry/curvature_correction.py.
See SPRINTS.md for merge plan.

Curvature constraint tables and gap-correction math for the blueprint vectorizer.

Derived from direct vector extraction of three reference blueprints:
  - A003-Dreadnought-MM.pdf  (acoustic, thin-stroke, REJECT class — the problem file)
  - Acoustic_guitar_00_en.pdf (acoustic OM, same template — sanity check)
  - Gibson-Melody-Maker.pdf  (electric single-neck, PRODUCTION_READY — sanity check)
  - Gibson-Double-Neck-esd1275.pdf (electric SG/double-neck — sanity check)

Purpose:
  When a body outline contour is fragmented (thin-stroke PDF, low DPI raster,
  or extreme compression artifacts), the curvature profiler cannot measure a
  reliable radius from a short fragment alone.  This module provides:

  1. CONSTRAINT TABLES — known R ranges per instrument class and body zone,
     so the profiler can classify fragments by LOCATION + LENGTH even when
     radius measurement is noisy.

  2. CORRECTION RADII — the R to use when reconstructing a gap via bi-arc
     joining (curvemath_biarc.py).  Choosing the wrong R produces a visibly
     wrong contour.  Choosing the right R produces a geometrically plausible
     bridge that Fusion 360 will accept.

  3. THRESHOLD TABLES — the per-instrument-class thresholds for
     curvature_profiler.py (MIN_R, MAX_R, stability, min_arc_length).

Usage in curvature_profiler.py:
    from body_curvature_correction import get_instrument_profile, correct_fragment_radius
    profile = get_instrument_profile(spec_name)
    corrected_R = correct_fragment_radius(fragment, profile, neighbor_context)

Author: The Production Shop  Date: 2026-04-14
Data sources: measured from blueprint vector geometry (not estimated)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import math
import numpy as np


# ---------------------------------------------------------------------------
# Measured curvature data (scale-corrected to 1:1 real-world mm)
# ---------------------------------------------------------------------------

# fmt: off
# Source: vector circle-fit and curvature-profile extraction, RMS < 0.02mm

MEASURED_RADII = {
    # ── Acoustic instruments ─────────────────────────────────────────────
    # Source: A003-Dreadnought-MM.pdf + Acoustic_guitar_00_en.pdf
    # Both PDFs share identical vector geometry (same template)
    # Scale: ~1:1 (concentric circles match soundhole at 50mm radius)
    "acoustic": {
        "lower_bout":   {"R_min": 45.0, "R_max": 54.0, "R_nominal": 47.1,
                         "chord_mm": 94.2, "sagitta_mm": 47.1,
                         "arc_type": "full_circle",
                         "note": "Fitted circle: center=(628,789)mm, R=47.1-53.8mm"},
        "upper_bout":   {"R_min": 44.0, "R_max": 50.0, "R_nominal": 47.1,
                         "chord_mm": 94.2, "sagitta_mm": 47.1,
                         "arc_type": "full_circle",
                         "note": "Fitted circle: center=(258,325)mm, R=47.1mm"},
        "waist":        {"R_min": 42.0, "R_max": 48.0, "R_nominal": 45.0,
                         "chord_mm": 90.0, "sagitta_mm": 13.2,
                         "arc_type": "quarter_arc",
                         "note": "Waist curves: left (129,566), right (463,626), R=45mm"},
    },

    # ── Electric single-neck (SG-body style) ─────────────────────────────
    # Source: Gibson-Melody-Maker.pdf
    # Scale: ~1:1 (101%). Body outline = fragmented line segments, 235 pts/side.
    "electric_single": {
        "horn_tip":     {"R_min":  4.0, "R_max":  8.0, "R_nominal":  5.7,
                         "chord_mm": 8.0,  "sagitta_mm": 1.7,
                         "arc_type": "90deg_arc",
                         "note": "MM upper horn tip: R=5.7mm (0.23\"). BELOW old 30mm floor."},
        "horn_cutaway": {"R_min": 18.0, "R_max": 30.0, "R_nominal": 22.0,
                         "chord_mm": 22.0, "sagitta_mm": 2.9,
                         "arc_type": "60deg_arc",
                         "note": "MM waist cutaway: R=22mm. Inner cutaway R=32-40mm."},
        "waist":        {"R_min": 28.0, "R_max": 45.0, "R_nominal": 36.0,
                         "chord_mm": 36.0, "sagitta_mm": 4.8,
                         "arc_type": "60deg_arc",
                         "note": "MM outer waist: R=32-40mm."},
        "body_belly":   {"R_min": 80.0, "R_max": 200.0, "R_nominal": 118.0,
                         "chord_mm": 61.0, "sagitta_mm": 4.0,
                         "arc_type": "30deg_arc",
                         "note": "MM belly: median R=119mm over 229 measured points."},
        "near_flat":    {"R_min": 300.0, "R_max": 2000.0, "R_nominal": 400.0,
                         "chord_mm": 140.0, "sagitta_mm": 6.1,
                         "arc_type": "20deg_arc",
                         "note": "MM flat sections: R>400mm. Treat as tangent line."},
        "corner_tight": {"R_min": 18.0, "R_max": 28.0, "R_nominal": 23.0,
                         "chord_mm": 23.0, "sagitta_mm": 3.1,
                         "arc_type": "60deg_arc",
                         "note": "MM lower bout end corner: R=22.9mm."},
    },

    # ── Electric double-neck (SG-style body, EDS-1275) ───────────────────
    # Source: Gibson-Double-Neck-esd1275.pdf
    # Scale: ~113% (body drawn slightly larger than 1:1)
    # 332-338 pts/chain, 5 chains for full body outline
    "electric_sg": {
        "horn_tip":     {"R_min":  5.0, "R_max": 20.0, "R_nominal": 14.0,
                         "chord_mm": 19.8, "sagitta_mm": 4.1,
                         "arc_type": "90deg_arc",
                         "note": "SG horn tips: P5=5.1mm, P95=16.2mm. EDS larger than MM."},
        "horn_cutaway": {"R_min": 20.0, "R_max": 50.0, "R_nominal": 22.0,
                         "chord_mm": 22.0, "sagitta_mm": 2.9,
                         "arc_type": "60deg_arc",
                         "note": "SG outer horn / cutaway: median=36mm."},
        "waist":        {"R_min": 50.0, "R_max": 100.0, "R_nominal": 55.0,
                         "chord_mm": 42.1, "sagitta_mm": 4.2,
                         "arc_type": "45deg_arc",
                         "note": "SG waist: median=78mm, range 50-100mm."},
        "body_belly":   {"R_min": 100.0, "R_max": 300.0, "R_nominal": 115.0,
                         "chord_mm": 59.5, "sagitta_mm": 3.9,
                         "arc_type": "30deg_arc",
                         "note": "SG belly: median=145mm, consistent with MM at 118mm."},
        "near_flat":    {"R_min": 300.0, "R_max": 5650.0, "R_nominal": 500.0,
                         "chord_mm": 175.0, "sagitta_mm": 7.7,
                         "arc_type": "20deg_arc",
                         "note": "SG flat sections: P5=316mm, P95=2308mm."},
    },
}
# fmt: on


# ---------------------------------------------------------------------------
# Instrument class profiles
# ---------------------------------------------------------------------------

@dataclass
class InstrumentCurvatureProfile:
    """
    Thresholds and correction parameters for the curvature profiler.
    One instance per instrument class; selected by spec_name.
    """
    instrument_class: str          # "ACOUSTIC" | "ELECTRIC"
    spec_names: list               # spec_name values that map to this profile

    # CurvatureProfiler thresholds
    min_profile_radius_mm: float   # fragments below this → NOISE (not PROFILE_CURVE)
    max_profile_radius_mm: float   # fragments above this → ANNOTATION or STRAIGHT_LINE
    stability_threshold: float     # std/mean of local radii; below = PROFILE_CURVE
    min_arc_length_mm: float       # fragment shorter than this → NOISE before radius check
    fragment_parent_search: bool   # if True: short fragments near PROFILE_CURVE inherit class

    # Zone table for this instrument class (keys match MEASURED_RADII)
    zone_key: str                  # key into MEASURED_RADII

    # Epsilon table for approxPolyDP (per zone)
    epsilon_by_zone: Dict[str, float] = field(default_factory=dict)

    def correction_radius(self, zone: str) -> Optional[float]:
        """Return the nominal correction radius for bi-arc gap joining in this zone."""
        zones = MEASURED_RADII.get(self.zone_key, {})
        entry = zones.get(zone)
        return entry["R_nominal"] if entry else None

    def zone_contains_radius(self, zone: str, R_mm: float) -> bool:
        """True if R_mm is plausible for this zone."""
        zones = MEASURED_RADII.get(self.zone_key, {})
        entry = zones.get(zone)
        if not entry:
            return False
        return entry["R_min"] * 0.8 <= R_mm <= entry["R_max"] * 1.2


# Profiles keyed by spec_name
_PROFILES: Dict[str, InstrumentCurvatureProfile] = {}


def _build_profiles():
    global _PROFILES

    acoustic = InstrumentCurvatureProfile(
        instrument_class="ACOUSTIC",
        spec_names=["dreadnought", "om_000", "jumbo", "parlour",
                    "classical", "j45", "jumbo_archtop"],
        min_profile_radius_mm=30.0,
        max_profile_radius_mm=800.0,
        stability_threshold=0.5,
        min_arc_length_mm=10.0,
        fragment_parent_search=True,
        zone_key="acoustic",
        epsilon_by_zone={
            "lower_bout":  0.0005,
            "upper_bout":  0.0005,
            "waist":       0.0006,
        },
    )

    electric_single = InstrumentCurvatureProfile(
        instrument_class="ELECTRIC",
        spec_names=["stratocaster", "telecaster", "les_paul", "gibson_sg",
                    "melody_maker", "flying_v", "es335", "bass_4string",
                    "smart_guitar"],
        min_profile_radius_mm=5.0,
        max_profile_radius_mm=800.0,
        stability_threshold=0.6,
        min_arc_length_mm=3.0,
        fragment_parent_search=True,
        zone_key="electric_single",
        epsilon_by_zone={
            "horn_tip":     0.0003,   # very tight: preserve detail
            "horn_cutaway": 0.0004,
            "waist":        0.0005,
            "body_belly":   0.0006,
            "near_flat":    0.0010,
            "corner_tight": 0.0004,
        },
    )

    electric_sg = InstrumentCurvatureProfile(
        instrument_class="ELECTRIC",
        spec_names=["eds1275", "gibson_sg_double"],
        min_profile_radius_mm=5.0,
        max_profile_radius_mm=800.0,
        stability_threshold=0.6,
        min_arc_length_mm=3.0,
        fragment_parent_search=True,
        zone_key="electric_sg",
        epsilon_by_zone={
            "horn_tip":     0.0003,
            "horn_cutaway": 0.0004,
            "waist":        0.0005,
            "body_belly":   0.0006,
            "near_flat":    0.0010,
        },
    )

    for p in [acoustic, electric_single, electric_sg]:
        for spec in p.spec_names:
            _PROFILES[spec] = p

    # Default for unknown spec
    _PROFILES["__default__"] = electric_single


_build_profiles()


def get_instrument_profile(spec_name: Optional[str]) -> InstrumentCurvatureProfile:
    """Return the curvature profile for the given spec_name."""
    if spec_name is None:
        return _PROFILES["__default__"]
    return _PROFILES.get(spec_name, _PROFILES["__default__"])


# ---------------------------------------------------------------------------
# Fragment radius correction
# ---------------------------------------------------------------------------

def correct_fragment_radius(
    fragment_pts: np.ndarray,
    profile: InstrumentCurvatureProfile,
    measured_R: float,
    fragment_arc_length_mm: float,
    nearest_profile_curve_R: Optional[float] = None,
) -> Tuple[float, str, str]:
    """
    Given a fragment with a noisy measured radius, return a corrected radius
    suitable for bi-arc gap joining.

    The correction algorithm:
      1. If the fragment is long enough (> min_arc_length), trust the measured R
         if it falls within any known zone for this instrument class.
      2. If the fragment is short (< min_arc_length) and a nearby PROFILE_CURVE
         has a known R, inherit that radius.
      3. If no context is available, snap the measured R to the nearest
         zone nominal in the instrument profile.

    Args:
        fragment_pts:            numpy array (N,2) of fragment points in mm
        profile:                 InstrumentCurvatureProfile for this instrument
        measured_R:              radius measured by curvature_profiler (may be noisy)
        fragment_arc_length_mm:  arc length of the fragment in mm
        nearest_profile_curve_R: radius of nearest confirmed PROFILE_CURVE contour
                                  (None if unknown)

    Returns:
        (corrected_R_mm, zone_name, method_used)
    """
    zones = MEASURED_RADII.get(profile.zone_key, {})

    # Step 1: If fragment is substantial, check if measured R fits any zone
    if fragment_arc_length_mm >= profile.min_arc_length_mm:
        best_zone = None
        best_err  = float("inf")
        for zone_name, z in zones.items():
            if z["R_min"] * 0.75 <= measured_R <= z["R_max"] * 1.25:
                err = abs(measured_R - z["R_nominal"])
                if err < best_err:
                    best_err  = err
                    best_zone = zone_name
        if best_zone:
            # Trust measured R but clamp to zone bounds
            z = zones[best_zone]
            clamped = max(z["R_min"] * 0.9, min(measured_R, z["R_max"] * 1.1))
            return clamped, best_zone, "measured_clamped"

    # Step 2: Fragment too short — inherit from neighbor if available
    if nearest_profile_curve_R is not None:
        for zone_name, z in zones.items():
            if z["R_min"] * 0.75 <= nearest_profile_curve_R <= z["R_max"] * 1.25:
                return z["R_nominal"], zone_name, "inherited_from_neighbor"

    # Step 3: Snap measured_R to nearest zone nominal
    best_zone = None
    best_err  = float("inf")
    for zone_name, z in zones.items():
        err = abs(measured_R - z["R_nominal"])
        if err < best_err:
            best_err  = err
            best_zone = zone_name
    if best_zone:
        return zones[best_zone]["R_nominal"], best_zone, "snapped_to_nominal"

    # Fallback: return measured_R unchanged
    return measured_R, "unknown", "passthrough"


# ---------------------------------------------------------------------------
# Chord / sagitta utilities
# ---------------------------------------------------------------------------

def chord_and_sagitta(R: float, arc_angle_deg: float) -> Tuple[float, float]:
    """
    chord   = 2R·sin(θ/2)
    sagitta = R·(1 − cos(θ/2))
    """
    theta = math.radians(arc_angle_deg)
    return 2 * R * math.sin(theta / 2), R * (1 - math.cos(theta / 2))


def radius_from_chord_sagitta(chord: float, sagitta: float) -> float:
    """R = c²/(8s) + s/2  (standard sagitta formula)"""
    if sagitta <= 0:
        return float("inf")
    return (chord * chord) / (8.0 * sagitta) + sagitta / 2.0


def reconstruct_arc_midpoint(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    R: float,
    concave: bool = False,
) -> Tuple[float, float]:
    """
    Given two gap endpoints p1, p2 and a known radius R, compute
    the midpoint of the circular arc that joins them.

    If concave=False, the arc bulges away from the line p1→p2 (convex body).
    If concave=True, the arc curves inward (cutaway inner face).

    Returns the midpoint (x, y) of the arc, usable as an intermediate
    control point for the bi-arc joiner.
    """
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    chord = math.hypot(dx, dy)
    if chord < 1e-9:
        return p1

    half_chord = chord / 2.0
    if half_chord > R:
        # Chord longer than diameter: clamp R to minimum valid
        R = half_chord * 1.001

    # Sagitta: height of arc above chord midpoint
    sagitta = R - math.sqrt(R * R - half_chord * half_chord)

    # Perpendicular direction to the chord
    perp_x = -dy / chord
    perp_y =  dx / chord

    # Midpoint of chord
    mx = (p1[0] + p2[0]) / 2.0
    my = (p1[1] + p2[1]) / 2.0

    sign = -1.0 if concave else 1.0

    return (mx + sign * sagitta * perp_x,
            my + sign * sagitta * perp_y)


# ---------------------------------------------------------------------------
# Curvature zone table printout (diagnostic utility)
# ---------------------------------------------------------------------------

def print_correction_table(spec_name: Optional[str] = None) -> None:
    """Print the correction radii table for a given spec_name or all instruments."""
    specs = [spec_name] if spec_name else list(MEASURED_RADII.keys())
    for sk in specs:
        zones = MEASURED_RADII.get(sk, {})
        print(f"\n{'='*68}")
        print(f"  {sk.upper()} — Curvature Correction Table")
        print(f"{'='*68}")
        print(f"  {'Zone':18s}  {'R_nom':>7}  {'R_min':>7}  {'R_max':>7}  "
              f"{'Chord':>8}  {'Sag':>7}")
        print("  " + "-"*62)
        for zone, z in zones.items():
            print(f"  {zone:18s}  {z['R_nominal']:>7.1f}  {z['R_min']:>7.1f}  "
                  f"{z['R_max']:>7.1f}  {z['chord_mm']:>8.1f}  {z['sagitta_mm']:>7.1f}")


# ---------------------------------------------------------------------------
# Integration point (called from curvature_profiler.py)
# ---------------------------------------------------------------------------

def get_correction_epsilon(spec_name: Optional[str], zone: str) -> float:
    """
    Return the approxPolyDP epsilon factor for a given spec and zone.
    This replaces the global 0.001 default in edge_to_dxf.py.
    """
    profile = get_instrument_profile(spec_name)
    return profile.epsilon_by_zone.get(zone, 0.001)


if __name__ == "__main__":
    print_correction_table()

    print("\n\nCORRECTION DEMO:")
    print("Scenario: SG body, short horn fragment, measured R=8mm (noisy)")
    profile = get_instrument_profile("gibson_sg")
    R_corr, zone, method = correct_fragment_radius(
        fragment_pts=np.array([(0,0),(2,1),(4,0)]),
        profile=profile,
        measured_R=8.0,
        fragment_arc_length_mm=4.5,
        nearest_profile_curve_R=14.2,
    )
    print(f"  → Corrected R={R_corr:.1f}mm  zone={zone}  method={method}")

    print("\nScenario: SG body, short horn fragment, NO neighbor context")
    R_corr2, zone2, method2 = correct_fragment_radius(
        fragment_pts=np.array([(0,0),(2,1),(4,0)]),
        profile=profile,
        measured_R=8.0,
        fragment_arc_length_mm=2.0,
        nearest_profile_curve_R=None,
    )
    print(f"  → Corrected R={R_corr2:.1f}mm  zone={zone2}  method={method2}")

    print("\nScenario: Acoustic lower bout gap, R=47mm measured from good fragment")
    ac_profile = get_instrument_profile("dreadnought")
    R_corr3, zone3, method3 = correct_fragment_radius(
        fragment_pts=np.ndarray((20,2)),
        profile=ac_profile,
        measured_R=47.1,
        fragment_arc_length_mm=18.0,
    )
    print(f"  → Corrected R={R_corr3:.1f}mm  zone={zone3}  method={method3}")

    print("\nArc midpoint reconstruction demo:")
    p1, p2 = (0.0, 0.0), (22.0, 0.0)  # 22mm gap in horn cutaway
    mid = reconstruct_arc_midpoint(p1, p2, R=22.0, concave=False)
    print(f"  Gap endpoints: {p1} → {p2}")
    print(f"  R=22mm (horn cutaway nominal)")
    print(f"  Arc midpoint: ({mid[0]:.2f}, {mid[1]:.2f})mm")
    chord, sag = chord_and_sagitta(22.0, 60.0)
    print(f"  Expected sagitta for 60° arc at R=22mm: {sag:.2f}mm")
    print(f"  Midpoint y = {mid[1]:.2f}mm ≈ sagitta {sag:.2f}mm  ({'OK' if abs(mid[1]-sag)<0.1 else 'CHECK'})")
