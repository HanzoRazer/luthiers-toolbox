# services/api/app/calculators/back_brace_calc.py
"""
Back Brace Pattern and Geometry Calculator — STRUCTURE-001

Ladder bracing for acoustic guitar backs: placement rules, brace
cross-section dimensions, scallop profiles, seam protection geometry,
and stiffness-to-mass analysis.

Why back bracing is structurally and acoustically different from top bracing
=============================================================================

TOP BRACING (X-brace, fan brace):
    The top is the primary acoustic radiator. String energy travels through
    the bridge into the top, and the top vibrates to move air. Brace geometry
    is acoustically optimized: X-brace diagonal geometry resists belly while
    allowing controlled stiffness gradients for radiation efficiency.

BACK BRACING (ladder brace):
    The back serves two distinct roles:

    Structural: The center seam runs along the wood grain. Wood is dimensionally
    unstable perpendicular to grain — a 200mm back half moves ~10mm over a
    20% humidity swing. Without cross-grain bracing spanning the seam, the
    differential expansion/contraction of the two halves pries the seam apart
    every seasonal cycle. The braces resist this. Every brace must span the
    seam completely; a split brace acts as a lever prying the seam open.

    Acoustic: The back is a secondary radiator contributing to low-frequency
    body resonance via air-back coupling. The back flexes in response to
    internal air pressure changes caused by top vibration. This coupling
    primarily affects bass response. Stiffer backs produce brighter, more
    focused sound; more flexible backs allow greater bass coupling and warmth.
    Back wood choice (stiff maple vs flexible mahogany/rosewood) interacts
    directly with brace stiffness to set this balance.

Brace geometry: why scalloping makes mechanical sense
======================================================

A rectangular brace has uniform EI = E × b × h³/12 along its length.
The structural work — spanning the center seam against humidity stress — is
concentrated at and near the seam. The ends of the brace, approaching the
kerfing, carry much less structural load.

Scalloping removes material from the ends while preserving full height at
the seam. The peak stiffness (at seam crossing) is identical between a
scalloped and unscalloped brace. The cosine scallop removes approximately
60% of the end-section mass with no change to peak stiffness. That removed
mass would otherwise damp back vibration without contributing structural benefit.

The cosine profile is preferred over linear taper because:
    1. No stress concentrations at the transition from flat to scallop
    2. Smooth stiffness gradient — no abrupt inflection point
    3. Crack-resistant geometry — linear transitions initiate cracks

Seam protection — the structural requirement that governs everything
=====================================================================

    Tangential shrinkage (mahogany, cross-grain): ~0.27% per % RH
    For a 200mm back half over 20% seasonal RH swing:
        ΔL = 200mm × 0.0027 × 20 = 10.8mm per half

    Both halves move in opposite directions (the seam is the pivot point
    for the hygroscopic stress). The seam adhesive and braces must resist
    this differential every year for the life of the instrument.

    MANDATORY RULES derived from this:
    1. Every brace must span the seam completely — no gap, no split brace.
    2. Full brace height must extend ≥ 20mm on each side of the center seam.
    3. The back strip (a separate longitudinal element along the seam, inside
       face) reinforces the seam against longitudinal splitting.
    4. Kerfing must seat cleanly under brace ends to prevent rocking.

Beam stiffness formula
======================

    EI = E × b × h³ / 12

    where:
        E  = Young's modulus of brace wood along grain (Pa)
        b  = brace width (m)
        h  = brace height at the point of interest (m)
        I  = b × h³ / 12  (second moment of area, rectangular cross-section)

    Height h dominates: doubling h increases EI by 8×.
    Width b is linear: doubling b doubles EI.
    This is why luthiers adjust brace height to tune back stiffness, not width.

Scallop profile formula (cosine)
=================================

    The cosine scallop from position x=0 (peak) to x=L_scallop (end):

        h(x) = h_min + (h_max - h_min) × (1 + cos(π × x / L_scallop)) / 2

    At x=0 (seam side of scallop): h = h_max  (peak stiffness preserved)
    At x=L_scallop (brace end):    h = h_min  (minimum gluing height)

    The scallop begins at a distance seam_flat_mm from the seam center,
    where the brace height transitions from full to tapered.

Source attribution
==================

DERIVED — no empirical constants:
    EI formula: engineering mechanics (second moment of area)
    Cosine scallop formula: geometric construction
    Seam stress estimate: dimensional stability mechanics + Hooke's Law

EMPIRICAL — practitioner consensus:
    Brace cross-section dimensions (h_max, b, h_min):
        Siminoff, "The Luthier's Handbook." Calibrated against
        decades of production instrument measurement.

    Brace position fractions (as proportion of body length):
        Derived from published Martin factory plans and cross-referenced
        with Siminoff. Position proportions scale with body length;
        the fractions are empirically established, not derived from
        acoustics first principles.

    Scallop length fraction (35% of half-brace from each end):
        Luthier practice consensus. No first-principles derivation exists
        for this — it is a range (25–45%) that experienced builders find
        produces good structural and acoustic results.

    Seam flat section minimum (40mm each side):
        Structural rule of thumb from Siminoff and GAL technical discussions.
        Relates to the minimum brace area needed to resist the seam stress
        estimated above.

    Back resonance target frequencies:
        180–220 Hz for OM/D style, as reported in practitioner tap-tone
        literature (Gore & Gilet Vol. 1, Siminoff). Not derivable from
        plate equations without full FEA of the specific back geometry.

    Humidity cycling numbers:
        Tangential shrinkage coefficient for mahogany (~0.27%/% RH)
        from Forest Products Laboratory wood data (USDA FPL-GTR-190).

References:
    Siminoff, R.H. "The Luthier's Handbook." Hal Leonard, 2002.
    Gore, T. & Gilet, G. "Contemporary Acoustic Guitar Design and Build."
        Vol. 1. Trevor Gore, 2011.
    USDA Forest Products Laboratory. "Wood Handbook." FPL-GTR-190, 2010.
        (Dimensional stability coefficients.)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Material properties
# ─────────────────────────────────────────────────────────────────────────────

# Young's modulus along grain (Pa) — brace material
# Source: Forest Products Laboratory FPL-GTR-190
BRACE_MOE: Dict[str, float] = {
    "sitka_spruce":   10.0e9,   # standard brace wood
    "adirondack":     11.5e9,   # stiffer; pre-war Martin style
    "engelmann":       8.5e9,   # softer; some classical
    "cedar":           8.0e9,   # used in some classical bracing
    "douglas_fir":    13.0e9,   # stiff; used in some backs
}

# Cross-grain shrinkage coefficient per 1% RH change
# Used for seam stress estimation
# Source: USDA FPL-GTR-190, Table 3-12
SHRINKAGE_TANGENTIAL: Dict[str, float] = {
    "mahogany":    0.0027,   # mm/mm per % RH, tangential
    "rosewood":    0.0030,
    "maple":       0.0035,   # stiffest; most humidity stress
    "walnut":      0.0027,
    "koa":         0.0025,
}

# Minimum height at brace end (for gluing surface)
H_MIN_GLUE_MM: float = 2.5   # mm

# Minimum flat section each side of seam for structural integrity
SEAM_FLAT_MIN_MM: float = 40.0   # mm each side of center


# ─────────────────────────────────────────────────────────────────────────────
# Brace cross-section geometry
# ─────────────────────────────────────────────────────────────────────────────

def brace_EI(E_Pa: float, b_mm: float, h_mm: float) -> float:
    """
    Bending stiffness EI for a rectangular brace cross-section.

        EI = E × b × h³ / 12     [N·m²]

    This is the exact formula for the second moment of area of a
    rectangle × Young's modulus. No approximations.

    Args:
        E_Pa:  Young's modulus along grain (Pa)
        b_mm:  Brace width (mm)
        h_mm:  Brace height (mm)

    Returns:
        EI in N·m²
    """
    b = b_mm / 1000.0
    h = h_mm / 1000.0
    return E_Pa * b * h**3 / 12.0


def cosine_scallop_height(
    x_mm: float,
    h_max_mm: float,
    h_min_mm: float,
    scallop_length_mm: float,
) -> float:
    """
    Brace height at position x from the start of the scallop zone.

    Profile:
        h(x) = h_min + (h_max - h_min) × (1 + cos(π × x / L)) / 2

    At x=0:             h = h_max  (seam side of scallop, full height)
    At x=L_scallop:     h = h_min  (brace end, minimum gluing height)

    The transition is smooth with zero derivative at both ends —
    no stress concentrations.

    Args:
        x_mm:              Distance from scallop start (mm, 0 = seam side)
        h_max_mm:          Full brace height (mm)
        h_min_mm:          Minimum height at brace end (mm)
        scallop_length_mm: Length over which scallop occurs (mm)

    Returns:
        Height (mm) at position x
    """
    if x_mm <= 0:
        return h_max_mm
    if x_mm >= scallop_length_mm:
        return h_min_mm
    t = x_mm / scallop_length_mm
    return h_min_mm + (h_max_mm - h_min_mm) * (1.0 + math.cos(math.pi * t)) / 2.0


def scallop_mass_ratio(
    h_max_mm: float,
    h_min_mm: float,
    scallop_length_mm: float,
    flat_length_mm: float,
    b_mm: float,
    rho_kg_m3: float = 430.0,
    n: int = 200,
) -> Tuple[float, float, float]:
    """
    Compute mass and peak stiffness for one half of a scalloped brace.

    Returns:
        Tuple of (mass_unscalloped_g, mass_scalloped_g, peak_EI_Nm2)
        Peak stiffness is identical for both — scalloping does not reduce it.
    """
    b = b_mm / 1000.0

    # Flat section (full height, centered on seam)
    flat_L = flat_length_mm / 1000.0
    scallop_L = scallop_length_mm / 1000.0
    h_max = h_max_mm / 1000.0
    h_min = h_min_mm / 1000.0

    # Peak EI — same for scalloped and unscalloped
    peak_EI = 10.0e9 * b * h_max**3 / 12.0  # using reference E

    # Mass of unscalloped half
    half_total = flat_L + scallop_L
    mass_rect = rho_kg_m3 * b * h_max * half_total * 1000.0  # grams

    # Mass of scalloped half (numerical integration)
    dx = (scallop_length_mm / n) / 1000.0
    mass_scallop_zone = 0.0
    for i in range(n):
        x_mm = (i + 0.5) * scallop_length_mm / n
        h = cosine_scallop_height(x_mm, h_max_mm, h_min_mm, scallop_length_mm) / 1000.0
        mass_scallop_zone += rho_kg_m3 * b * h * dx

    mass_flat_zone = rho_kg_m3 * b * h_max * flat_L
    mass_scalloped = (mass_flat_zone + mass_scallop_zone) * 1000.0  # grams

    return mass_rect, mass_scalloped, peak_EI


# ─────────────────────────────────────────────────────────────────────────────
# Back body geometry
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BackBodyDimensions:
    """
    Guitar back dimensions for brace layout calculation.

    All dimensions in mm. Body length measured inside (tail block to
    neck block face). Width at each zone used to compute brace lengths.
    """
    body_length_mm: float       # total inside body length
    lower_bout_width_mm: float  # maximum lower bout width
    upper_bout_width_mm: float  # maximum upper bout width
    waist_width_mm: float       # waist width
    kerfing_inset_mm: float = 9.0   # depth kerfing extends under back (each side)

    def brace_length_at(self, width_mm: float) -> float:
        """
        Usable brace length at a given body width location.
        Brace goes from kerfing to kerfing.
        """
        return width_mm - 2.0 * self.kerfing_inset_mm

    @property
    def lower_bout_brace_length(self) -> float:
        return self.brace_length_at(self.lower_bout_width_mm)

    @property
    def upper_bout_brace_length(self) -> float:
        return self.brace_length_at(self.upper_bout_width_mm)


BODY_PRESETS: Dict[str, BackBodyDimensions] = {
    "martin_000_om": BackBodyDimensions(
        body_length_mm=480,
        lower_bout_width_mm=380,
        upper_bout_width_mm=285,
        waist_width_mm=228,
    ),
    "martin_d": BackBodyDimensions(
        body_length_mm=505,
        lower_bout_width_mm=406,
        upper_bout_width_mm=295,
        waist_width_mm=238,
    ),
    "martin_00": BackBodyDimensions(
        body_length_mm=460,
        lower_bout_width_mm=355,
        upper_bout_width_mm=272,
        waist_width_mm=215,
    ),
    "martin_000_small": BackBodyDimensions(
        body_length_mm=456,
        lower_bout_width_mm=355,
        upper_bout_width_mm=270,
        waist_width_mm=220,
    ),
    "classical": BackBodyDimensions(
        body_length_mm=485,
        lower_bout_width_mm=370,
        upper_bout_width_mm=280,
        waist_width_mm=225,
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Brace specification
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BraceDef:
    """
    A single back brace definition.

    Positions are measured from the tail block end of the body.
    Brace dimensions follow from body width at that position.
    """
    name: str
    role: str                       # "structural" | "seam" | "acoustic" | "edge"
    position_fraction: float        # fraction of body_length from tail block

    # Cross-section
    width_mm: float                 # brace width (b)
    height_max_mm: float            # full height at seam (h_max)
    height_min_mm: float            # minimum height at ends (h_min)
    scallop_fraction: float         # fraction of half-brace that is scalloped
    seam_flat_mm: float             # half-width of full-height flat zone at seam

    # Material
    material: str = "sitka_spruce"

    def position_mm(self, body_length_mm: float) -> float:
        return self.position_fraction * body_length_mm

    def brace_length_mm(self, bout_width_mm: float, kerfing_inset_mm: float = 9.0) -> float:
        return bout_width_mm - 2.0 * kerfing_inset_mm

    def half_length_mm(self, bout_width_mm: float, kerfing_inset_mm: float = 9.0) -> float:
        return self.brace_length_mm(bout_width_mm, kerfing_inset_mm) / 2.0

    def scallop_length_mm(self, bout_width_mm: float, kerfing_inset_mm: float = 9.0) -> float:
        """Length of the scalloped zone at each end of the brace."""
        half_L = self.half_length_mm(bout_width_mm, kerfing_inset_mm)
        available = half_L - self.seam_flat_mm
        return max(0.0, available * self.scallop_fraction)

    def peak_EI(self, material: Optional[str] = None) -> float:
        """Peak stiffness at seam crossing (full height section)."""
        E = BRACE_MOE.get(material or self.material, BRACE_MOE["sitka_spruce"])
        return brace_EI(E, self.width_mm, self.height_max_mm)


@dataclass
class BackStripDef:
    """
    The back strip — a continuous along-grain reinforcement strip
    running the full body length along the inside face of the center seam.

    This is NOT a brace. It does not add cross-grain stiffness.
    It resists longitudinal splitting of the seam and provides additional
    glue area for the center joint.
    """
    width_mm: float = 20.0
    thickness_mm: float = 2.0
    material: str = "sitka_spruce"   # typically same as back or top wood


# ─────────────────────────────────────────────────────────────────────────────
# Standard brace patterns
# ─────────────────────────────────────────────────────────────────────────────

def standard_ladder_pattern(style: str = "martin_light") -> List[BraceDef]:
    """
    Standard ladder brace pattern for acoustic guitar back.

    Position fractions are empirically derived from Martin production
    measurements (Siminoff). They scale proportionally with body length.

    Styles:
        "martin_light"   — Martin OM/000 style, lighter bracing
        "martin_medium"  — Martin D/HD style, heavier bracing
        "classical"      — Classical guitar back bracing
        "parlor"         — Small body, lighter bracing
    """
    patterns = {
        "martin_light": [
            BraceDef(
                name="tail_brace",
                role="edge",
                position_fraction=0.07,
                width_mm=6.0, height_max_mm=9.0, height_min_mm=2.5,
                scallop_fraction=0.45,
                seam_flat_mm=40.0,
                material="sitka_spruce",
            ),
            BraceDef(
                name="lower_bout_brace_1",
                role="structural",
                position_fraction=0.22,
                width_mm=6.5, height_max_mm=12.0, height_min_mm=2.5,
                scallop_fraction=0.40,
                seam_flat_mm=45.0,
                material="sitka_spruce",
            ),
            BraceDef(
                name="lower_bout_brace_2",
                role="structural",
                position_fraction=0.37,
                width_mm=6.5, height_max_mm=11.0, height_min_mm=2.5,
                scallop_fraction=0.38,
                seam_flat_mm=42.0,
                material="sitka_spruce",
            ),
            BraceDef(
                name="waist_brace",
                role="structural",
                position_fraction=0.54,
                width_mm=6.0, height_max_mm=9.0, height_min_mm=2.5,
                scallop_fraction=0.40,
                seam_flat_mm=40.0,
                material="sitka_spruce",
            ),
            BraceDef(
                name="upper_bout_brace_1",
                role="structural",
                position_fraction=0.70,
                width_mm=6.0, height_max_mm=10.0, height_min_mm=2.5,
                scallop_fraction=0.38,
                seam_flat_mm=40.0,
                material="sitka_spruce",
            ),
            BraceDef(
                name="upper_bout_brace_2",
                role="edge",
                position_fraction=0.86,
                width_mm=6.0, height_max_mm=9.0, height_min_mm=2.5,
                scallop_fraction=0.42,
                seam_flat_mm=40.0,
                material="sitka_spruce",
            ),
        ],

        "martin_medium": [
            BraceDef("tail_brace",         "edge",       0.07, 6.5, 10.0, 2.5, 0.42, 40.0),
            BraceDef("lower_bout_brace_1", "structural", 0.22, 7.0, 14.0, 2.5, 0.38, 48.0),
            BraceDef("lower_bout_brace_2", "structural", 0.37, 7.0, 13.0, 2.5, 0.36, 46.0),
            BraceDef("waist_brace",        "structural", 0.54, 6.5, 10.0, 2.5, 0.40, 40.0),
            BraceDef("upper_bout_brace_1", "structural", 0.70, 6.5, 11.0, 2.5, 0.36, 42.0),
            BraceDef("upper_bout_brace_2", "edge",       0.86, 6.5, 10.0, 2.5, 0.40, 40.0),
        ],

        "classical": [
            BraceDef("tail_brace",         "edge",       0.07, 5.0,  8.0, 2.0, 0.45, 40.0),
            BraceDef("lower_bout_brace_1", "structural", 0.22, 5.5, 10.0, 2.0, 0.42, 40.0),
            BraceDef("lower_bout_brace_2", "structural", 0.38, 5.5,  9.0, 2.0, 0.40, 40.0),
            BraceDef("waist_brace",        "structural", 0.55, 5.0,  8.0, 2.0, 0.42, 40.0),
            BraceDef("upper_bout_brace",   "structural", 0.72, 5.0,  8.0, 2.0, 0.40, 40.0),
            BraceDef("neck_area_brace",    "edge",       0.87, 5.0,  7.0, 2.0, 0.42, 40.0),
        ],

        "parlor": [
            BraceDef("tail_brace",         "edge",       0.07, 5.5,  8.0, 2.5, 0.45, 40.0),
            BraceDef("lower_bout_brace_1", "structural", 0.23, 6.0, 10.0, 2.5, 0.42, 40.0),
            BraceDef("lower_bout_brace_2", "structural", 0.39, 6.0,  9.5, 2.5, 0.40, 40.0),
            BraceDef("waist_brace",        "structural", 0.56, 5.5,  8.5, 2.5, 0.42, 40.0),
            BraceDef("upper_bout_brace",   "structural", 0.73, 5.5,  9.0, 2.5, 0.40, 40.0),
            BraceDef("neck_area_brace",    "edge",       0.87, 5.5,  8.0, 2.5, 0.42, 40.0),
        ],
    }

    if style not in patterns:
        raise ValueError(
            f"Unknown brace pattern: {style!r}. "
            f"Available: {list(patterns.keys())}"
        )
    return patterns[style]


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BraceResult:
    """
    Computed geometry and properties for a single back brace.

    Dimensions are for the physical brace as cut — ready for layout.
    """
    brace_def: BraceDef

    # Absolute position
    position_from_tail_mm: float

    # Physical dimensions
    total_length_mm: float          # kerfing to kerfing
    half_length_mm: float
    scallop_length_mm: float        # scalloped zone at each end
    seam_flat_mm: float             # full-height flat zone each side of seam

    # Stiffness
    peak_EI_Nm2: float              # at seam crossing, full height
    peak_EI_label: str              # human-readable

    # Mass efficiency
    mass_unscalloped_g: float       # if rectangular (not scalloped)
    mass_scalloped_g: float         # actual scalloped mass
    mass_reduction_pct: float       # % mass removed by scalloping

    # Seam validation
    seam_coverage_ok: bool          # True if flat zone >= SEAM_FLAT_MIN_MM
    seam_warning: Optional[str] = None

    # Profile samples (for plotting/CNC)
    profile_points: List[Tuple[float, float]] = field(default_factory=list)
    # Each tuple: (x_from_seam_mm, height_mm) — half-profile, seam at x=0


@dataclass
class BackBraceLayout:
    """
    Complete back brace layout for a guitar body.
    """
    body: BackBodyDimensions
    brace_style: str
    back_strip: BackStripDef

    braces: List[BraceResult]

    # Seam protection summary
    all_seams_covered: bool
    seam_warnings: List[str]

    # Overall stiffness character
    stiffness_character: str        # "light" | "medium" | "heavy"
    acoustic_note: str

    # Source declaration
    source_note: str = (
        "Brace positions: empirical from Martin production measurements "
        "(Siminoff). Dimensions: practitioner calibration (Siminoff, Gore & Gilet). "
        "EI formula: engineering mechanics (exact). "
        "Scallop profile: geometric construction (exact). "
        "Seam stress estimate: dimensional stability mechanics "
        "(USDA FPL-GTR-190 shrinkage coefficients)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Profile generation
# ─────────────────────────────────────────────────────────────────────────────

def profile_points(
    brace: BraceDef,
    half_length_mm: float,
    n_points: int = 40,
) -> List[Tuple[float, float]]:
    """
    Generate (x_from_seam, height) sample points for one half of the brace.

    x=0 at seam center, x=half_length at brace end (kerfing).
    Points are evenly spaced along the half-brace.
    Used for plotting and CNC toolpath generation.
    """
    scallop_L = max(0.0, half_length_mm - brace.seam_flat_mm)
    scallop_fraction = brace.scallop_fraction
    effective_scallop = min(scallop_L, half_length_mm * scallop_fraction + brace.seam_flat_mm)
    scallop_start = half_length_mm - scallop_L * scallop_fraction

    points: List[Tuple[float, float]] = []
    for i in range(n_points + 1):
        x = i * half_length_mm / n_points
        if x <= scallop_start:
            h = brace.height_max_mm
        else:
            x_into_scallop = x - scallop_start
            scallop_zone = half_length_mm - scallop_start
            h = cosine_scallop_height(
                x_into_scallop,
                brace.height_max_mm,
                brace.height_min_mm,
                scallop_zone,
            )
        points.append((round(x, 2), round(h, 3)))
    return points


# ─────────────────────────────────────────────────────────────────────────────
# Main analyzer
# ─────────────────────────────────────────────────────────────────────────────

def compute_back_layout(
    body_key: str = "martin_000_om",
    brace_style: str = "martin_light",
    material: str = "sitka_spruce",
    back_material: str = "mahogany",
    generate_profiles: bool = True,
) -> BackBraceLayout:
    """
    Compute complete back brace layout for a guitar body.

    Args:
        body_key:          Key from BODY_PRESETS
        brace_style:       Key from standard_ladder_pattern()
        material:          Brace wood key from BRACE_MOE
        back_material:     Back plate wood key from SHRINKAGE_TANGENTIAL
        generate_profiles: Whether to compute profile point arrays

    Returns:
        BackBraceLayout with all brace dimensions, positions, and analysis.
    """
    if body_key not in BODY_PRESETS:
        raise ValueError(f"Unknown body: {body_key!r}. Available: {list(BODY_PRESETS.keys())}")

    body = BODY_PRESETS[body_key]
    brace_defs = standard_ladder_pattern(brace_style)
    E = BRACE_MOE.get(material, BRACE_MOE["sitka_spruce"])

    seam_warnings: List[str] = []
    results: List[BraceResult] = []

    for bd in brace_defs:
        pos_mm = bd.position_mm(body.body_length_mm)

        # Interpolate back width at this position
        # Simplified: use lower bout width for lower half, upper for upper half
        waist_pos = 0.54 * body.body_length_mm
        if pos_mm < waist_pos:
            # Lower bout region: interpolate between lower bout and waist
            frac = pos_mm / waist_pos
            width = body.lower_bout_width_mm * (1 - frac) + body.waist_width_mm * frac
            # Actually: near tail use lower bout, near waist use waist
            frac2 = (pos_mm / waist_pos)
            width = body.lower_bout_width_mm + (body.waist_width_mm - body.lower_bout_width_mm) * frac2
        else:
            # Upper bout region
            upper_frac = (pos_mm - waist_pos) / (body.body_length_mm - waist_pos)
            width = body.waist_width_mm + (body.upper_bout_width_mm - body.waist_width_mm) * upper_frac

        total_L = body.brace_length_at(width)
        half_L  = total_L / 2.0
        scallop_zone = max(0.0, half_L - bd.seam_flat_mm) * bd.scallop_fraction

        # Peak EI at seam (full height)
        peak_EI = brace_EI(E, bd.width_mm, bd.height_max_mm)
        ei_label = f"{peak_EI:.2f} N·m²"

        # Mass analysis
        mass_rect, mass_scalloped, _ = scallop_mass_ratio(
            bd.height_max_mm, bd.height_min_mm,
            scallop_zone, bd.seam_flat_mm,
            bd.width_mm,
            rho_kg_m3=430.0,
        )
        mass_red = (1.0 - mass_scalloped / mass_rect) * 100.0 if mass_rect > 0 else 0.0

        # Seam coverage check
        seam_ok = bd.seam_flat_mm >= SEAM_FLAT_MIN_MM
        seam_warn = None
        if not seam_ok:
            seam_warn = (
                f"{bd.name}: seam flat zone ({bd.seam_flat_mm:.0f}mm) is below "
                f"minimum ({SEAM_FLAT_MIN_MM:.0f}mm). Risk of insufficient seam "
                f"reinforcement under humidity cycling."
            )
            seam_warnings.append(seam_warn)

        # Profile points
        pts = profile_points(bd, half_L) if generate_profiles else []

        results.append(BraceResult(
            brace_def=bd,
            position_from_tail_mm=round(pos_mm, 1),
            total_length_mm=round(total_L, 1),
            half_length_mm=round(half_L, 1),
            scallop_length_mm=round(scallop_zone, 1),
            seam_flat_mm=bd.seam_flat_mm,
            peak_EI_Nm2=round(peak_EI, 4),
            peak_EI_label=ei_label,
            mass_unscalloped_g=round(mass_rect, 3),
            mass_scalloped_g=round(mass_scalloped, 3),
            mass_reduction_pct=round(mass_red, 1),
            seam_coverage_ok=seam_ok,
            seam_warning=seam_warn,
            profile_points=pts,
        ))

    # Stiffness character from peak EI of main lower bout brace
    main_brace = next((r for r in results if "lower_bout_brace_1" in r.brace_def.name), results[0])
    ei = main_brace.peak_EI_Nm2
    if ei < 6.0:
        stiffness = "light"
        acoustic = (
            "Light back bracing allows more back flexion — greater bass coupling "
            "via air-back resonance. Warm, round tone character. "
            "Appropriate for fingerstyle instruments and smaller body sizes."
        )
    elif ei < 10.0:
        stiffness = "medium"
        acoustic = (
            "Medium back bracing balances structural integrity against acoustic "
            "flexibility. The back contributes to body resonance without "
            "dominating the tone character. General-purpose setting."
        )
    else:
        stiffness = "heavy"
        acoustic = (
            "Heavy back bracing stiffens the back, reducing its acoustic "
            "contribution. Tone tends toward bright and focused, with less "
            "bass warmth. Appropriate for larger bodies (D, jumbo) where "
            "the body volume already provides sufficient bass."
        )

    back_strip = BackStripDef(
        width_mm=20.0,
        thickness_mm=2.0,
        material=material,
    )

    return BackBraceLayout(
        body=body,
        brace_style=brace_style,
        back_strip=back_strip,
        braces=results,
        all_seams_covered=len(seam_warnings) == 0,
        seam_warnings=seam_warnings,
        stiffness_character=stiffness,
        acoustic_note=acoustic,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Seam stress utility
# ─────────────────────────────────────────────────────────────────────────────

def seam_stress_estimate(
    back_half_width_mm: float,
    back_material: str = "mahogany",
    rh_swing_pct: float = 20.0,
) -> dict:
    """
    Estimate cross-grain dimensional change across the back seam.

    This is the environmental stress that back braces must resist.
    Both halves move in opposite directions, doubling the relative motion.

    Args:
        back_half_width_mm: Width of one back half (mm)
        back_material:      Key from SHRINKAGE_TANGENTIAL
        rh_swing_pct:       Seasonal humidity swing (% RH)

    Returns:
        Dict with dimensional change estimates.
    """
    shrink = SHRINKAGE_TANGENTIAL.get(back_material, 0.0027)
    delta_half = back_half_width_mm * shrink * rh_swing_pct
    delta_total = delta_half * 2

    return {
        "back_half_width_mm": back_half_width_mm,
        "rh_swing_pct": rh_swing_pct,
        "shrinkage_coeff": shrink,
        "delta_per_half_mm": round(delta_half, 2),
        "delta_total_mm": round(delta_total, 2),
        "note": (
            f"Each back half moves ±{delta_half:.1f}mm seasonally. "
            f"The seam must accommodate {delta_total:.1f}mm of total relative "
            f"movement annually. Every brace must cross the seam and maintain "
            f"full height for ≥{SEAM_FLAT_MIN_MM:.0f}mm each side."
        ),
    }
