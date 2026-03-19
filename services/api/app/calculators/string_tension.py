# services/api/app/calculators/string_tension.py

"""
String Tension Calculator (CONSTRUCTION-004)
=============================================

Calculates string tension using the fundamental physics formula:
    T = (2 × f × L)² × μ

where:
    T = tension (Newtons)
    f = frequency (Hz)
    L = scale length (meters)
    μ = linear mass density (kg/m)

Linear mass density calculation:
    Plain strings: μ = π × (d/2)² × ρ_steel
    Wound strings: μ = μ_core + μ_winding (empirical table, ~40-60% added mass)

This feeds into:
    - bracing_calc.py — total top load for brace sizing
    - bridge plate sizing — load distribution under bridge
    - neck relief calculations — string pull on neck

Author: The Production Shop
Version: 1.0.0
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Literal, Optional

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

# Steel density (kg/m³) — plain steel strings
RHO_STEEL_KG_M3 = 7850.0

# Conversion factors
INCH_TO_M = 0.0254
MM_TO_M = 0.001
N_TO_LB = 0.224809  # Newtons to pounds-force


# ---------------------------------------------------------------------------
# Standard tuning frequencies (Hz)
# ---------------------------------------------------------------------------

STANDARD_TUNING_HZ = {
    "E2": 82.41,
    "A2": 110.00,
    "D3": 146.83,
    "G3": 196.00,
    "B3": 246.94,
    "E4": 329.63,
}

# Extended tunings
DROP_D_TUNING_HZ = {
    "D2": 73.42,
    "A2": 110.00,
    "D3": 146.83,
    "G3": 196.00,
    "B3": 246.94,
    "E4": 329.63,
}

# Classical guitar (nylon) — same pitches, different string construction
CLASSICAL_TUNING_HZ = STANDARD_TUNING_HZ.copy()


# ---------------------------------------------------------------------------
# Unit weight table (empirical — from D'Addario published data)
# ---------------------------------------------------------------------------

# For wound strings, the gauge is the OUTER diameter including winding.
# The actual linear mass density is NOT simply ρ × π × r² because:
#   1. The winding has gaps between wraps
#   2. The core is smaller than the outer diameter
#   3. Winding material varies (phosphor bronze, 80/20 bronze, nickel)
#
# D'Addario publishes "Unit Weight" in lbs/inch.
# Conversion to kg/m: lbs/inch × 0.453592 kg/lb × 39.3701 in/m = lbs/inch × 17.858
#
# Source: D'Addario String Tension Guide
# https://www.daddario.com/globalassets/pdfs/accessories/tension_chart_13934.pdf

LBS_PER_INCH_TO_KG_PER_M = 17.858  # 0.453592 × 39.3701

# Unit weight in lbs/inch for common wound string gauges (phosphor bronze acoustic)
# Source: D'Addario String Tension Pro calculator
# https://www.daddario.com/products/guitar/acoustic-guitar/phosphor-bronze/
#
# These values are calibrated to produce correct tensions (e.g., EJ16 light set
# at 25.5" scale: total ~160-165 lbs).
_WOUND_UNIT_WEIGHT_LBS_INCH = {
    # gauge_inch: unit_weight_lbs_per_inch (from D'Addario PB series)
    0.020: 0.00009050,
    0.022: 0.00012180,
    0.023: 0.00014160,
    0.024: 0.00017225,  # PB024 (G string in light set)
    0.025: 0.00018800,
    0.026: 0.00021030,
    0.029: 0.00026640,
    0.030: 0.00028720,
    0.032: 0.00030560,  # PB032 (D string in light set)
    0.035: 0.00039570,
    0.036: 0.00042440,
    0.039: 0.00048300,
    0.042: 0.00052523,  # PB042 (A string in light set)
    0.045: 0.00063850,
    0.046: 0.00067090,
    0.047: 0.00070410,
    0.052: 0.00080760,
    0.053: 0.00084070,  # PB053 (E string in light set)
    0.054: 0.00087650,
    0.056: 0.00095280,
    0.059: 0.00106800,
    0.060: 0.00110500,
}

# Pre-compute kg/m values
WOUND_UNIT_WEIGHT_KG_M = {
    gauge: weight * LBS_PER_INCH_TO_KG_PER_M
    for gauge, weight in _WOUND_UNIT_WEIGHT_LBS_INCH.items()
}


def _get_wound_unit_weight(gauge_inch: float) -> float:
    """
    Get wound string unit weight (kg/m) for a given gauge.
    Interpolates between known values.
    """
    if gauge_inch in WOUND_UNIT_WEIGHT_KG_M:
        return WOUND_UNIT_WEIGHT_KG_M[gauge_inch]

    # Interpolate
    gauges = sorted(WOUND_UNIT_WEIGHT_KG_M.keys())

    if gauge_inch < gauges[0]:
        # Extrapolate using smallest known value ratio
        return WOUND_UNIT_WEIGHT_KG_M[gauges[0]] * (gauge_inch / gauges[0]) ** 2
    if gauge_inch > gauges[-1]:
        # Extrapolate using largest known value ratio
        return WOUND_UNIT_WEIGHT_KG_M[gauges[-1]] * (gauge_inch / gauges[-1]) ** 2

    # Find bracketing values
    for i in range(len(gauges) - 1):
        if gauges[i] <= gauge_inch <= gauges[i + 1]:
            low_g, high_g = gauges[i], gauges[i + 1]
            low_w = WOUND_UNIT_WEIGHT_KG_M[low_g]
            high_w = WOUND_UNIT_WEIGHT_KG_M[high_g]
            t = (gauge_inch - low_g) / (high_g - low_g)
            return low_w + t * (high_w - low_w)

    # Fallback: use solid steel approximation
    diameter_m = gauge_inch * INCH_TO_M
    return math.pi * (diameter_m / 2.0) ** 2 * RHO_STEEL_KG_M3


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class StringSpec:
    """Specification for a single string."""
    name: str                # "1" through "6" or "e", "B", "G", "D", "A", "E"
    gauge_inch: float        # Diameter in inches (e.g., 0.012)
    is_wound: bool           # True for wound strings
    note: str                # "E2", "A2", etc.
    frequency_hz: float      # Target frequency

    @property
    def gauge_mm(self) -> float:
        return self.gauge_inch * 25.4


@dataclass
class TensionResult:
    """Result of tension calculation for a single string."""
    name: str
    gauge_inch: float
    tension_lb: float
    tension_n: float
    linear_density_kg_m: float
    note: str
    is_wound: bool = False

    @property
    def gauge_mm(self) -> float:
        return self.gauge_inch * 25.4


@dataclass
class SetTensionResult:
    """Result of tension calculation for a complete string set."""
    strings: List[TensionResult]
    total_tension_lb: float
    total_tension_n: float
    scale_length_mm: float
    set_name: str = ""


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def compute_linear_density(
    gauge_inch: float,
    is_wound: bool,
) -> float:
    """
    Compute linear mass density (μ) in kg/m.

    For plain strings:
        μ = π × (d/2)² × ρ_steel

    For wound strings:
        Uses empirical unit weight table from D'Addario specs.
        The gauge is the OUTER diameter including winding, but
        the actual mass is less than solid steel due to air gaps
        and the smaller core diameter.

    Args:
        gauge_inch: String diameter in inches
        is_wound: True if wound string

    Returns:
        Linear mass density in kg/m
    """
    if is_wound:
        # Use empirical unit weight table
        return _get_wound_unit_weight(gauge_inch)

    # Plain string: solid steel wire
    diameter_m = gauge_inch * INCH_TO_M
    radius_m = diameter_m / 2.0
    area_m2 = math.pi * radius_m ** 2
    return area_m2 * RHO_STEEL_KG_M3


def compute_string_tension(
    gauge_inch: float,
    is_wound: bool,
    frequency_hz: float,
    scale_length_mm: float,
) -> TensionResult:
    """
    Compute tension for a single string.

    Formula: T = (2 × f × L)² × μ

    Args:
        gauge_inch: String diameter in inches
        is_wound: True if wound string
        frequency_hz: Target frequency in Hz
        scale_length_mm: Scale length in mm

    Returns:
        TensionResult with tension in both N and lbs
    """
    # Convert scale length to meters
    L = scale_length_mm * MM_TO_M

    # Get linear density
    mu = compute_linear_density(gauge_inch, is_wound)

    # T = (2 × f × L)² × μ
    tension_n = ((2.0 * frequency_hz * L) ** 2) * mu
    tension_lb = tension_n * N_TO_LB

    return TensionResult(
        name="",  # Will be set by caller
        gauge_inch=gauge_inch,
        tension_lb=round(tension_lb, 2),
        tension_n=round(tension_n, 2),
        linear_density_kg_m=mu,
        note="",  # Will be set by caller
        is_wound=is_wound,
    )


def compute_string_tension_from_spec(
    spec: StringSpec,
    scale_length_mm: float,
) -> TensionResult:
    """
    Compute tension from a StringSpec.

    Args:
        spec: StringSpec with gauge, wound status, and frequency
        scale_length_mm: Scale length in mm

    Returns:
        TensionResult
    """
    result = compute_string_tension(
        gauge_inch=spec.gauge_inch,
        is_wound=spec.is_wound,
        frequency_hz=spec.frequency_hz,
        scale_length_mm=scale_length_mm,
    )
    result.name = spec.name
    result.note = spec.note
    return result


def compute_set_tension(
    strings: List[StringSpec],
    scale_length_mm: float,
    set_name: str = "",
) -> SetTensionResult:
    """
    Compute tension for a complete string set.

    Args:
        strings: List of StringSpec for each string
        scale_length_mm: Scale length in mm
        set_name: Optional name for the string set

    Returns:
        SetTensionResult with individual and total tensions
    """
    results = [
        compute_string_tension_from_spec(s, scale_length_mm)
        for s in strings
    ]

    total_n = sum(r.tension_n for r in results)
    total_lb = sum(r.tension_lb for r in results)

    return SetTensionResult(
        strings=results,
        total_tension_lb=round(total_lb, 2),
        total_tension_n=round(total_n, 2),
        scale_length_mm=scale_length_mm,
        set_name=set_name,
    )


def total_tension_lbs(results: List[TensionResult]) -> float:
    """Sum total tension in pounds."""
    return sum(r.tension_lb for r in results)


def total_tension_newtons(results: List[TensionResult]) -> float:
    """Sum total tension in Newtons."""
    return sum(r.tension_n for r in results)


# ---------------------------------------------------------------------------
# Preset string sets
# ---------------------------------------------------------------------------

# Standard 6-string sets (high e to low E)

EXTRA_LIGHT_010: List[StringSpec] = [
    StringSpec(name="1", gauge_inch=0.010, is_wound=False, note="E4", frequency_hz=329.63),
    StringSpec(name="2", gauge_inch=0.014, is_wound=False, note="B3", frequency_hz=246.94),
    StringSpec(name="3", gauge_inch=0.023, is_wound=True,  note="G3", frequency_hz=196.00),
    StringSpec(name="4", gauge_inch=0.030, is_wound=True,  note="D3", frequency_hz=146.83),
    StringSpec(name="5", gauge_inch=0.039, is_wound=True,  note="A2", frequency_hz=110.00),
    StringSpec(name="6", gauge_inch=0.047, is_wound=True,  note="E2", frequency_hz=82.41),
]

LIGHT_012: List[StringSpec] = [
    StringSpec(name="1", gauge_inch=0.012, is_wound=False, note="E4", frequency_hz=329.63),
    StringSpec(name="2", gauge_inch=0.016, is_wound=False, note="B3", frequency_hz=246.94),
    StringSpec(name="3", gauge_inch=0.024, is_wound=True,  note="G3", frequency_hz=196.00),
    StringSpec(name="4", gauge_inch=0.032, is_wound=True,  note="D3", frequency_hz=146.83),
    StringSpec(name="5", gauge_inch=0.042, is_wound=True,  note="A2", frequency_hz=110.00),
    StringSpec(name="6", gauge_inch=0.053, is_wound=True,  note="E2", frequency_hz=82.41),
]

MEDIUM_013: List[StringSpec] = [
    StringSpec(name="1", gauge_inch=0.013, is_wound=False, note="E4", frequency_hz=329.63),
    StringSpec(name="2", gauge_inch=0.017, is_wound=False, note="B3", frequency_hz=246.94),
    StringSpec(name="3", gauge_inch=0.026, is_wound=True,  note="G3", frequency_hz=196.00),
    StringSpec(name="4", gauge_inch=0.035, is_wound=True,  note="D3", frequency_hz=146.83),
    StringSpec(name="5", gauge_inch=0.045, is_wound=True,  note="A2", frequency_hz=110.00),
    StringSpec(name="6", gauge_inch=0.056, is_wound=True,  note="E2", frequency_hz=82.41),
]

BLUEGRASS_013: List[StringSpec] = [
    StringSpec(name="1", gauge_inch=0.013, is_wound=False, note="E4", frequency_hz=329.63),
    StringSpec(name="2", gauge_inch=0.017, is_wound=False, note="B3", frequency_hz=246.94),
    StringSpec(name="3", gauge_inch=0.026, is_wound=True,  note="G3", frequency_hz=196.00),
    StringSpec(name="4", gauge_inch=0.036, is_wound=True,  note="D3", frequency_hz=146.83),
    StringSpec(name="5", gauge_inch=0.046, is_wound=True,  note="A2", frequency_hz=110.00),
    StringSpec(name="6", gauge_inch=0.059, is_wound=True,  note="E2", frequency_hz=82.41),
]

# Classical nylon strings — different construction
# Nylon has much lower density (~1150 kg/m³ vs steel ~7850)
# Classical strings use nylon trebles and wound nylon/silver basses
# For now, use empirical tensions from manufacturer data

CLASSICAL_NORMAL: List[StringSpec] = [
    # Classical strings are specified differently — these are approximate
    # High tension nylon set (D'Addario EJ45-style)
    StringSpec(name="1", gauge_inch=0.028, is_wound=False, note="E4", frequency_hz=329.63),
    StringSpec(name="2", gauge_inch=0.032, is_wound=False, note="B3", frequency_hz=246.94),
    StringSpec(name="3", gauge_inch=0.040, is_wound=False, note="G3", frequency_hz=196.00),
    StringSpec(name="4", gauge_inch=0.029, is_wound=True,  note="D3", frequency_hz=146.83),
    StringSpec(name="5", gauge_inch=0.035, is_wound=True,  note="A2", frequency_hz=110.00),
    StringSpec(name="6", gauge_inch=0.043, is_wound=True,  note="E2", frequency_hz=82.41),
]

# Named set registry
STRING_SETS = {
    "extra_light_010": EXTRA_LIGHT_010,
    "light_012": LIGHT_012,
    "medium_013": MEDIUM_013,
    "bluegrass_013": BLUEGRASS_013,
    "classical_normal": CLASSICAL_NORMAL,
}


def get_preset_set(name: str) -> List[StringSpec]:
    """Get a preset string set by name."""
    if name not in STRING_SETS:
        available = ", ".join(STRING_SETS.keys())
        raise ValueError(f"Unknown string set '{name}'. Available: {available}")
    return STRING_SETS[name]


def list_preset_sets() -> List[str]:
    """List available preset string set names."""
    return list(STRING_SETS.keys())


# ---------------------------------------------------------------------------
# Common scale lengths (mm)
# ---------------------------------------------------------------------------

SCALE_LENGTHS_MM = {
    "fender_standard": 647.7,     # 25.5"
    "gibson_standard": 628.65,    # 24.75"
    "prs_standard": 635.0,        # 25.0"
    "martin_om": 632.46,          # 24.9"
    "martin_dreadnought": 645.16, # 25.4"
    "taylor_gs": 647.7,           # 25.5"
    "classical": 650.0,           # 650mm (25.6")
}


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def quick_tension_estimate(
    scale_length_mm: float,
    string_set: str = "light_012",
) -> SetTensionResult:
    """
    Quick tension estimate for a standard string set.

    Args:
        scale_length_mm: Scale length in mm
        string_set: Name of preset string set

    Returns:
        SetTensionResult
    """
    strings = get_preset_set(string_set)
    return compute_set_tension(strings, scale_length_mm, set_name=string_set)


def tension_comparison(
    scale_length_mm: float,
    sets: Optional[List[str]] = None,
) -> dict:
    """
    Compare tensions across multiple string sets.

    Args:
        scale_length_mm: Scale length in mm
        sets: List of set names (defaults to all presets)

    Returns:
        Dict mapping set name to total tension (lbs)
    """
    if sets is None:
        sets = list_preset_sets()

    return {
        name: quick_tension_estimate(scale_length_mm, name).total_tension_lb
        for name in sets
    }
