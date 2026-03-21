"""
Back Bracing Geometry — ladder bracing for acoustic guitar backs.

Previously missing from instrument_geometry/bracing/. This module provides
body-profile-aware brace placement, scallop geometry, camber calculation,
and center seam protection analysis for ladder-braced backs.

The back is a reflector, not a primary radiator. The primary structural job
of back bracing is preventing the center seam (two bookmatched halves) from
splitting under seasonal humidity cycling. Ladder braces run perpendicular to
the seam, distributing seasonal movement forces as shear rather than tension.

All geometry formulas are exact (chord-sagitta, parabolic profile).
Placement positions and dimension ranges are empirical consensus from
Gore & Gilet Vol.1, Siminoff, and Martin production specifications.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# body profile data is self-contained in this module


# ── Constants ────────────────────────────────────────────────────────────────

MAX_SEAM_SPAN_MM: float    = 120.0  # max unsupported seam between brace CL
LINING_CLEARANCE_MM: float = 5.0    # clearance from brace end to side lining


# ── Geometry functions ───────────────────────────────────────────────────────

def brace_camber_mm(length_mm: float, radius_mm: float) -> float:
    """
    Camber (arch height) for a brace pre-bent to dish radius R.
    chord-sagitta: camber = L² / (8R)
    """
    if radius_mm <= 0:
        return 0.0
    return length_mm ** 2 / (8.0 * radius_mm)


def scallop_height_at(
    x: float,
    length: float,
    h_center: float,
    h_end: float,
    scallop_length: float,
) -> float:
    """
    Brace height at position x from left end.
    Parabolic scallop at each end, constant h_center in the middle.
    h(x) = h_end + (h_center - h_end) × (dist_from_end / scallop_length)²
    """
    if x < 0 or x > length:
        return 0.0
    dist = min(x, length - x)
    if dist >= scallop_length:
        return h_center
    t = dist / scallop_length
    return h_end + (h_center - h_end) * t ** 2


def scallop_mean_area(
    length: float,
    width: float,
    h_center: float,
    h_end: float,
    scallop_length: float,
    steps: int = 200,
) -> float:
    """Mean cross-section area for mass calculation (integrates scallop profile)."""
    dx = length / steps
    total = 0.0
    for i in range(steps):
        x = (i + 0.5) * dx
        h = scallop_height_at(x, length, h_center, h_end, scallop_length)
        total += (2.0 / 3.0) * width * h * dx
    return total / length if length > 0 else 0.0


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class BackBrace:
    """A single back brace with full geometry."""
    index: int
    station_mm: float          # distance from neck block
    body_width_mm: float       # back plate width at this station
    length_mm: float           # brace length (body_width - 2×lining_clearance)
    width_mm: float
    h_center_mm: float
    h_end_mm: float
    scallop_length_mm: float
    back_radius_mm: float      # dish radius this brace is cambered to
    camber_mm: float           # pre-bend height
    mean_area_mm2: float
    mass_g: float
    span_to_prev_mm: float     # gap to previous brace or neck block
    span_to_next_mm: float     # gap to next brace or tail block
    seam_risk: str             # "OK" | "WARNING" | "RISK"

    @property
    def full_height_length_mm(self) -> float:
        return max(0.0, self.length_mm - 2.0 * self.scallop_length_mm)

    def scallop_points(self, n: int = 40) -> List[Tuple[float, float]]:
        """(x, height) pairs for CNC toolpath or visualisation."""
        L = self.length_mm
        return [
            (
                round(L * i / (n - 1), 2),
                round(scallop_height_at(
                    L * i / (n - 1), L,
                    self.h_center_mm, self.h_end_mm, self.scallop_length_mm,
                ), 3),
            )
            for i in range(n)
        ]


@dataclass
class BackBracePattern:
    """Complete back bracing specification."""
    body_style: str
    back_radius_mm: float
    braces: List[BackBrace]
    total_mass_g: float
    max_seam_span_mm: float
    seam_adequate: bool
    seam_warning: Optional[str] = None


# ── Body profile registry ────────────────────────────────────────────────────

_BACK_PROFILES: Dict[str, Dict] = {
    "martin_om": {
        "label": "Martin OM / 000",
        "body_length_mm": 489, "lower_bout_mm": 375,
        "waist_mm": 235, "upper_bout_mm": 285, "waist_station_mm": 218,
        "default_back_radius_ft": 20,
        "reference_stations": [55, 130, 220, 310, 390, 450],
    },
    "martin_d28": {
        "label": "Martin Dreadnought",
        "body_length_mm": 508, "lower_bout_mm": 394,
        "waist_mm": 244, "upper_bout_mm": 291, "waist_station_mm": 228,
        "default_back_radius_ft": 20,
        "reference_stations": [55, 135, 230, 320, 405, 465],
    },
    "martin_000": {
        "label": "Martin 000",
        "body_length_mm": 478, "lower_bout_mm": 370,
        "waist_mm": 230, "upper_bout_mm": 280, "waist_station_mm": 212,
        "default_back_radius_ft": 20,
        "reference_stations": [52, 125, 212, 302, 380, 440],
    },
    "taylor_grand_auditorium": {
        "label": "Taylor Grand Auditorium",
        "body_length_mm": 495, "lower_bout_mm": 381,
        "waist_mm": 241, "upper_bout_mm": 292, "waist_station_mm": 220,
        "default_back_radius_ft": 25,
        "reference_stations": [60, 140, 225, 320, 405, 460],
    },
    "parlor": {
        "label": "Parlor",
        "body_length_mm": 445, "lower_bout_mm": 340,
        "waist_mm": 215, "upper_bout_mm": 260, "waist_station_mm": 198,
        "default_back_radius_ft": 20,
        "reference_stations": [50, 118, 200, 284, 355, 410],
    },
}


def _width_at(p: Dict, station: float) -> float:
    """Back width at station using linear interpolation through body profile."""
    L   = p["body_length_mm"]
    ub  = p["upper_bout_mm"]
    wst = p["waist_mm"]
    lb  = p["lower_bout_mm"]
    ws  = p["waist_station_mm"]
    s   = max(0.0, min(station, L))
    if s <= ws:
        t = s / ws if ws > 0 else 0.0
        return ub + (wst - ub) * t
    else:
        lower_L = L - ws
        t = (s - ws) / lower_L if lower_L > 0 else 0.0
        peak_t = 0.55
        tail_w = ub
        if t <= peak_t:
            return wst + (lb - wst) * (t / peak_t)
        else:
            return lb + (tail_w - lb) * ((t - peak_t) / (1.0 - peak_t))


# ── Main factory ─────────────────────────────────────────────────────────────

# Wood densities (g/mm³)
_DENSITY: Dict[str, float] = {
    "sitka_spruce": 4.0e-4, "engelmann_spruce": 3.6e-4,
    "mahogany": 5.6e-4, "maple": 6.4e-4, "cedar": 3.5e-4,
}


def generate_back_bracing(
    body_style: str = "martin_om",
    stations_mm: Optional[List[float]] = None,
    width_mm: float = 6.5,
    h_center_mm: float = 10.0,
    h_end_mm: float = 3.5,
    scallop_length_mm: float = 40.0,
    back_radius_ft: Optional[float] = None,
    material: str = "sitka_spruce",
) -> BackBracePattern:
    """
    Generate a complete ladder-brace back pattern.

    Args:
        body_style:       Key in _BACK_PROFILES
        stations_mm:      Brace centerline distances from neck block.
                          None → uses profile reference positions.
        width_mm:         Brace width
        h_center_mm:      Center height
        h_end_mm:         Scallop tip height
        scallop_length_mm: Scallop taper length each end
        back_radius_ft:   Dish radius in feet. None → profile default.
        material:         Wood species for mass calculation

    Returns:
        BackBracePattern
    """
    if body_style not in _BACK_PROFILES:
        raise ValueError(f"Unknown body style: {body_style!r}. "
                         f"Available: {list(_BACK_PROFILES)}")

    prof   = _BACK_PROFILES[body_style]
    r_ft   = back_radius_ft if back_radius_ft is not None else prof["default_back_radius_ft"]
    r_mm   = r_ft * 304.8
    dens   = _DENSITY.get(material, 4.0e-4)
    L_body = prof["body_length_mm"]

    stations = sorted(stations_mm if stations_mm is not None else prof["reference_stations"])
    all_st   = [0.0] + stations + [float(L_body)]

    braces: List[BackBrace] = []
    for i, st in enumerate(stations):
        body_w  = _width_at(prof, st)
        brace_L = max(0.0, body_w - 2.0 * LINING_CLEARANCE_MM)
        camber  = brace_camber_mm(brace_L, r_mm)
        mean_a  = scallop_mean_area(brace_L, width_mm, h_center_mm, h_end_mm, scallop_length_mm)
        mass    = mean_a * brace_L * dens   # mm² × mm × g/mm³ = g

        idx      = i + 1
        sp_prev  = all_st[idx] - all_st[idx - 1]
        sp_next  = all_st[idx + 1] - all_st[idx]
        max_sp   = max(sp_prev, sp_next)
        seam_risk = (
            "RISK"    if max_sp > MAX_SEAM_SPAN_MM else
            "WARNING" if max_sp > MAX_SEAM_SPAN_MM * 0.85 else
            "OK"
        )

        braces.append(BackBrace(
            index=i + 1,
            station_mm=round(st, 1),
            body_width_mm=round(body_w, 1),
            length_mm=round(brace_L, 1),
            width_mm=width_mm,
            h_center_mm=h_center_mm,
            h_end_mm=h_end_mm,
            scallop_length_mm=scallop_length_mm,
            back_radius_mm=round(r_mm, 1),
            camber_mm=round(camber, 3),
            mean_area_mm2=round(mean_a, 2),
            mass_g=round(mass, 2),
            span_to_prev_mm=round(sp_prev, 1),
            span_to_next_mm=round(sp_next, 1),
            seam_risk=seam_risk,
        ))

    max_span = max(all_st[j + 1] - all_st[j] for j in range(len(all_st) - 1))
    seam_ok  = max_span <= MAX_SEAM_SPAN_MM
    warning  = None
    if not seam_ok:
        warning = (
            f"Unsupported seam span {max_span:.0f}mm exceeds {MAX_SEAM_SPAN_MM:.0f}mm limit. "
            "Add a brace or redistribute to close the gap."
        )

    return BackBracePattern(
        body_style=body_style,
        back_radius_mm=round(r_mm, 1),
        braces=braces,
        total_mass_g=round(sum(b.mass_g for b in braces), 2),
        max_seam_span_mm=round(max_span, 1),
        seam_adequate=seam_ok,
        seam_warning=warning,
    )


def list_body_styles() -> List[str]:
    return list(_BACK_PROFILES.keys())


def get_profile_label(body_style: str) -> str:
    return _BACK_PROFILES.get(body_style, {}).get("label", body_style)
