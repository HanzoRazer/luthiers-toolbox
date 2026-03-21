# services/api/app/calculators/saddle_compensation_calc.py
"""
Saddle Compensation Calculator — Elmendorp Predictive Model
GEOMETRY-008

Predictive saddle compensation from physical string parameters, before
the instrument is strung or measured. Uses equations derived by
Sjaak Elmendorp in "It's All About the Core, or How to Estimate
Compensation," American Lutherie #104, 2010.

Source honesty
==============

This module implements equations that are **physically derived with
experimental validation** — a different category from the empirical
k-factor approach rejected in the previous nut compensation attempt.

EXACT MATHEMATICS (no empiricism):
    Equations [1]–[12] are derived from first principles:
    - String frequency equation (textbook physics)
    - Hooke's Law for elastic stretch (engineering mechanics)
    - Pythagorean geometry for string depression (high-school math)
    - Euler-Bernoulli stiff-string frequency correction
      (Hall, Musical Acoustics, 3rd ed., p.197)
    - Taylor approximation √(1+x) ≈ 1 + x/2 (valid for small x)

    The master formula [11] follows algebraically from these. It
    contains no fitted coefficients. Given correct inputs it is exact
    within the approximation error of the Taylor expansion (<1%,
    confirmed by Elmendorp numerically).

EMPIRICAL INPUTS (you measure these):
    - a₁₂  : action at 12th fret — measured with calipers
    - d     : core diameter — measured with calipers (critical)
    - T₀    : string tension — from manufacturer data or calculated
    - E     : Young's modulus — from literature (steel) or measured
              by the octave-drop method (nylon)

VALIDATED ACCURACY:
    Elmendorp compared predicted vs measured compensation on four
    string sets (Elixir lights, LaBella XHT nylon, Alchemy bass steel,
    Tomastik nylon bass). Agreement within ±0.5mm across all strings.
    This is the practical measurement limit — the formula is more
    precise than the measurements used to validate it.

PRINCIPAL SENSITIVITY:
    Core diameter d enters the bending term as d⁴ under a square root,
    making the effective sensitivity d². A 5% error in d produces
    approximately 10% error in the bending compensation term.
    Elmendorp states this explicitly: "this term appears in the equation
    cubed, implying that any measurement error is magnified by a factor
    of 2." (For d² in sqrt(d⁴): d appears cubed before the sqrt,
    so actual sensitivity is d² ≈ factor of 2 amplification.)
    Measure core diameter carefully with a digital caliper.

The master formula
==================

    Comp = Comp_stretch + Comp_bend

    Comp_stretch = a₁₂² × E × S / (2 × T₀ × L₀)   [Eq. 8]

    Comp_bend    = 2 × √(E × J / T₀)                [Eq. 10]

    where:
        S = π × d² / 4     (cross-sectional area of core)
        J = π × d⁴ / 64    (second moment of area of core)
        a₁₂ = action at 12th fret (m)
        E   = Young's modulus of string core material (Pa)
        T₀  = string tension at pitch (N)
        L₀  = nominal scale length (m)
        d   = core diameter (m)  — USE CORE, NOT WOUND DIAMETER

    For wound strings: d is the CORE diameter, not the total string
    diameter. Elmendorp shows theoretically and experimentally that
    windings contribute negligibly to bending stiffness. The wound
    portion does not appear in the formula.

    For hex-core strings (e.g. many bass strings):
        S → S × 1.10
        J → J × 1.20
    This 10%/20% correction accounts for the geometry of a
    hexagonal cross-section vs circular. Source: Elmendorp footnote
    on Alchemy hex-core bass strings.

The stretch term
================

    Starting from the Pythagorean geometry of a depressed string:

        ΔL_str = a² × (L_n + L_f) / (2 × L_n × L_f)   [Eq. 4]

    where L_n = nut-to-fret distance, L_f = fret-to-saddle distance.

    This feeds into the tension increase:

        ΔT_str = E × S × ΔL_str / L_string              [Eq. 3]

    After Taylor expansion and algebraic simplification:

        Comp_str(fret n) = (L_n × L_f / 4L₀) × a² × ES/T₀  [Eq. 6]

    This is fret-dependent. Elmendorp removes the fret dependence by
    using the flat-fretboard assumption that action scales linearly:

        a = 2 × a₁₂ × (L_n / L₀)                       [Eq. 7]

    Substituting [7] into [6] and simplifying yields the
    fret-independent form [Eq. 8]:

        Comp_stretch = a₁₂² × E × S / (2 × T₀ × L₀)

    This is exact under the flat-fretboard approximation. Real guitars
    have some relief, which introduces a small secondary error.

The bending stiffness term
==========================

    A string with finite bending stiffness vibrates at:

        f ≈ (1/2Lf) × √(T₀/ρ) × (1 + 2√(EJ/T₀) / Lf)  [Eq. 9]

    Source: Donald E. Hall, Musical Acoustics, 3rd ed., p.197.

    The compensation required to restore the theoretical pitch:

        Comp_bend = 2 × √(E × J / T₀)                   [Eq. 10]

    This is independent of action and scale length. It depends only
    on string stiffness and tension. This is why nylon guitars with
    high action (4–5mm) do not have dramatically worse intonation than
    those with low action — the bending stiffness term dominates for
    nylon and is independent of action.

Why the B string needs more compensation than any other
=======================================================

    The B string (.016" plain steel) has:
    - Relatively low tension (~49N vs 72–84N for wound bass strings)
    - Plain steel core (high MOE = 200 GPa)
    - Relatively large diameter for its tension

    The bending term = 2√(EJ/T). Low T and high E both increase this.
    The B string's large d relative to its tension produces the highest
    Comp_bend of any string in a standard set — typically 4–5mm out
    of total compensation of 5–7mm at normal action.

    This is the mathematical explanation for the universal observation
    that the B string of a steel-string guitar requires the most saddle
    compensation, often placing the B saddle contact point noticeably
    further back than adjacent strings.

References
==========
    Elmendorp, Sjaak. "It's All About the Core, or How to Estimate
        Compensation." American Lutherie #104, 2010. Guild of American
        Luthiers. Primary source for all equations in this module.

    Hall, Donald E. Musical Acoustics, 3rd edition. Brooks/Cole, 2002.
        p.197. Source for the stiff-string frequency equation [9].

    D'Addario String Tension Specifications (published). Source for
        tension values in STRING_SETS reference data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Material constants
# ─────────────────────────────────────────────────────────────────────────────

# Young's moduli — source: Elmendorp AL#104 + literature
MATERIAL_MOE: Dict[str, float] = {
    "steel":        200e9,   # Pa — confirmed 200–210 GPa (literature + experiment)
    "nylon_solid":  3.5e9,   # Pa — 3–4 GPa; measure per string via octave-drop
    "nylon_floss":  11e9,    # Pa — 10–12 GPa for wound nylon cores
    "gut":          3.0e9,   # Pa — approximate; variable, measure per string
}

# Hex core correction factors (Elmendorp footnote on Alchemy bass hex core)
HEX_CORE_S_FACTOR: float = 1.10   # multiply S by this for hex core
HEX_CORE_J_FACTOR: float = 1.20   # multiply J by this for hex core


# ─────────────────────────────────────────────────────────────────────────────
# Core geometry
# ─────────────────────────────────────────────────────────────────────────────

def core_area(d_m: float, hex_core: bool = False) -> float:
    """
    Cross-sectional area S of string core.  [Eq. 12a]

    S = π × d² / 4   (circular)
    S × 1.10          (hexagonal)
    """
    S = math.pi * d_m**2 / 4
    return S * HEX_CORE_S_FACTOR if hex_core else S


def core_moment(d_m: float, hex_core: bool = False) -> float:
    """
    Second moment of area J of string core.  [Eq. 12b]

    J = π × d⁴ / 64   (circular)
    J × 1.20           (hexagonal)
    """
    J = math.pi * d_m**4 / 64
    return J * HEX_CORE_J_FACTOR if hex_core else J


# ─────────────────────────────────────────────────────────────────────────────
# Elmendorp formula components
# ─────────────────────────────────────────────────────────────────────────────

def comp_stretch(
    a12_m: float,
    E_Pa: float,
    d_core_m: float,
    T0_N: float,
    L0_m: float,
    hex_core: bool = False,
) -> float:
    """
    Compensation due to fretting stretch.  [Eq. 8]

    Comp_stretch = a₁₂² × E × S / (2 × T₀ × L₀)

    Derivation path:
        String depression geometry [Eq. 4]
        → Elastic tension increase [Eq. 3]
        → Compensation required [Eq. 6]
        → Flat-fretboard action scaling [Eq. 7]
        → Fret-independent form [Eq. 8]

    Args:
        a12_m:      Action at 12th fret (meters)
        E_Pa:       Young's modulus of core material (Pa)
        d_core_m:   Core diameter (meters) — NOT wound diameter
        T0_N:       Open string tension at pitch (N)
        L0_m:       Nominal scale length (meters)
        hex_core:   True for hexagonal core strings

    Returns:
        Stretch compensation (meters)
    """
    S = core_area(d_core_m, hex_core)
    return a12_m**2 * E_Pa * S / (2 * T0_N * L0_m)


def comp_bending(
    E_Pa: float,
    d_core_m: float,
    T0_N: float,
    hex_core: bool = False,
) -> float:
    """
    Compensation due to string bending stiffness.  [Eq. 10]

    Comp_bend = 2 × √(E × J / T₀)

    Derivation path:
        Stiff-string frequency equation [Eq. 9] (Hall, Musical Acoustics)
        → Equate to ideal frequency [Eq. 1]
        → Solve for required length increase
        → Comp_bend = 2√(EJ/T₀) [Eq. 10]

    Note: This term is INDEPENDENT of action and scale length.
    It depends only on string stiffness and tension.

    Args:
        E_Pa:       Young's modulus of core material (Pa)
        d_core_m:   Core diameter (meters)
        T0_N:       Open string tension at pitch (N)
        hex_core:   True for hexagonal core strings

    Returns:
        Bending stiffness compensation (meters)
    """
    J = core_moment(d_core_m, hex_core)
    return 2 * math.sqrt(E_Pa * J / T0_N)


def comp_total(
    a12_m: float,
    E_Pa: float,
    d_core_m: float,
    T0_N: float,
    L0_m: float,
    hex_core: bool = False,
) -> tuple[float, float, float]:
    """
    Total saddle compensation.  [Eq. 11]

    Comp = a₁₂² × E × S / (2 × T₀ × L₀)  +  2√(E × J / T₀)
           ────────────────────────────────    ───────────────
                 stretch term                  bending term

    Returns:
        Tuple of (comp_stretch_m, comp_bend_m, comp_total_m)
    """
    cs = comp_stretch(a12_m, E_Pa, d_core_m, T0_N, L0_m, hex_core)
    cb = comp_bending(E_Pa, d_core_m, T0_N, hex_core)
    return cs, cb, cs + cb


def moe_from_octave_drop(
    T0_N: float,
    L_string_m: float,
    d_core_m: float,
    delta_L_oct_m: float,
    hex_core: bool = False,
) -> float:
    """
    Young's modulus from the octave-drop measurement method.  [Eq. 13]

    Procedure: mark string position at nut. Drop tuning by one full
    octave (halve frequency → tension reduces to T₀/4, so ΔT = 3T₀/4).
    Measure string compression ΔL_oct. Then:

        E = (3 × T₀ × L_string) / (4 × ΔL_oct × S)

    This is the field method for nylon strings, where E cannot be
    found in tables. For steel, use E = 200 GPa from literature.

    Args:
        T0_N:          Open string tension at pitch (N)
        L_string_m:    Compensated open string length (≈ scale length) (m)
        d_core_m:      Core diameter (m)
        delta_L_oct_m: String compression when detuned one full octave (m)
        hex_core:      True for hex core

    Returns:
        Estimated Young's modulus (Pa)
    """
    S = core_area(d_core_m, hex_core)
    return (3 * T0_N * L_string_m) / (4 * delta_L_oct_m * S)


# ─────────────────────────────────────────────────────────────────────────────
# String definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StringDef:
    """
    A single string specification.

    Core diameter is the critical measurement. For plain strings,
    core_dia_in = total_dia_in. For wound strings, core_dia_in is
    the diameter of the inner core only — not the wound diameter.
    """
    name: str
    total_dia_in: float      # total string diameter (inches)
    core_dia_in: float       # core diameter only (inches) — KEY INPUT
    wound: bool
    hex_core: bool
    material: str            # key into MATERIAL_MOE
    tension_N: float         # at standard pitch, 25.5" scale
    pitch_hz: float          # standard tuning pitch

    @property
    def core_dia_m(self) -> float:
        return self.core_dia_in * 0.0254

    @property
    def total_dia_m(self) -> float:
        return self.total_dia_in * 0.0254


# Reference string sets
# Tension data: D'Addario published string tension charts
# Core diameters: D'Addario technical specs (round core unless noted)
STRING_SETS: Dict[str, List[StringDef]] = {

    "acoustic_light_012": [  # D'Addario EJ16 Phosphor Bronze Light
        StringDef("High e", 0.012, 0.012, False, False, "steel", 71.7,  329.63),
        StringDef("B",      0.016, 0.016, False, False, "steel", 49.0,  246.94),
        StringDef("G",      0.024, 0.011, True,  False, "steel", 63.1,  196.00),
        StringDef("D",      0.032, 0.012, True,  False, "steel", 72.6,  146.83),
        StringDef("A",      0.042, 0.014, True,  False, "steel", 78.7,  110.00),
        StringDef("Low E",  0.053, 0.017, True,  False, "steel", 84.4,  82.41),
    ],

    "acoustic_medium_013": [  # D'Addario EJ17 Phosphor Bronze Medium
        StringDef("High e", 0.013, 0.013, False, False, "steel", 83.9,  329.63),
        StringDef("B",      0.017, 0.017, False, False, "steel", 55.4,  246.94),
        StringDef("G",      0.026, 0.012, True,  False, "steel", 73.9,  196.00),
        StringDef("D",      0.035, 0.013, True,  False, "steel", 84.5,  146.83),
        StringDef("A",      0.045, 0.015, True,  False, "steel", 90.3,  110.00),
        StringDef("Low E",  0.056, 0.018, True,  False, "steel", 96.1,  82.41),
    ],

    "electric_light_009": [  # D'Addario EXL110 Regular Light
        StringDef("High e", 0.009, 0.009, False, False, "steel", 40.3,  329.63),
        StringDef("B",      0.011, 0.011, False, False, "steel", 29.3,  246.94),
        StringDef("G",      0.016, 0.016, False, False, "steel", 44.8,  196.00),
        StringDef("D",      0.024, 0.010, True,  False, "steel", 55.5,  146.83),
        StringDef("A",      0.032, 0.011, True,  False, "steel", 56.0,  110.00),
        StringDef("Low E",  0.042, 0.014, True,  False, "steel", 59.9,  82.41),
    ],

    "classical_normal": [  # D'Addario EJ27N / La Bella 820 Normal tension
        StringDef("High e", 0.028, 0.028, False, False, "nylon_solid",  71.0, 329.63),
        StringDef("B",      0.032, 0.032, False, False, "nylon_solid",  49.0, 246.94),
        StringDef("G",      0.040, 0.040, False, False, "nylon_solid",  55.0, 196.00),
        StringDef("D",      0.030, 0.021, True,  False, "nylon_floss",  63.0, 146.83),
        StringDef("A",      0.036, 0.025, True,  False, "nylon_floss",  74.0, 110.00),
        StringDef("Low E",  0.043, 0.030, True,  False, "nylon_floss",  77.0, 82.41),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StringCompensation:
    """Compensation result for a single string."""
    string_def: StringDef

    # Inputs used
    scale_m: float
    a12_m: float
    E_Pa: float

    # Geometry
    S_m2: float      # core cross-sectional area
    J_m4: float      # core second moment of area

    # Results
    comp_stretch_m: float
    comp_bend_m: float
    comp_total_m: float

    # Design constraint flags (set by CompensationSpec after all strings computed)
    anomaly: bool = False
    anomaly_note: str = ""

    @property
    def comp_stretch_mm(self) -> float:
        return self.comp_stretch_m * 1000

    @property
    def comp_bend_mm(self) -> float:
        return self.comp_bend_m * 1000

    @property
    def comp_total_mm(self) -> float:
        return self.comp_total_m * 1000

    @property
    def stretch_fraction(self) -> float:
        """Fraction of total compensation from stretch term."""
        if self.comp_total_m == 0:
            return 0.0
        return self.comp_stretch_m / self.comp_total_m

    @property
    def bend_fraction(self) -> float:
        """Fraction of total compensation from bending stiffness term."""
        return 1.0 - self.stretch_fraction

    @property
    def sensitivity_note(self) -> str:
        """Human-readable note on measurement sensitivity."""
        d_mm = self.string_def.core_dia_m * 1000
        pct_5 = self.comp_bend_m * 0.10  # 5% d error → ~10% bend error
        return (
            f"5% error in core diameter ({d_mm:.3f}mm) → "
            f"±{pct_5*1000:.2f}mm error in bending compensation. "
            f"Bending is {self.bend_fraction*100:.0f}% of total."
        )


@dataclass
class SaddleDesignConstraint:
    """
    A compensation anomaly that cannot be resolved by saddle positioning alone.

    The formula reveals when a string requires compensation so far from its
    neighbours that no shared straight or simply angled saddle can serve all
    strings adequately. This is not a calculation error — it is a design
    constraint embedded in the physics of that string's gauge and material.

    The formula manifests the phenomenon. It does not compensate for it.
    Resolving it requires a change to the instrument design or string choice.
    """
    string_name: str
    comp_required_mm: float
    neighbour_avg_mm: float
    deviation_mm: float

    # What the builder can actually do about it
    design_options: List[str]

    # Plain language explanation
    explanation: str


@dataclass
class CompensationSpec:
    """Complete saddle compensation specification for an instrument."""
    scale_length_in: float
    scale_length_mm: float
    action_at_12th_mm: float
    string_set_key: str

    strings: List[StringCompensation]

    # Straight saddle geometry
    straight_saddle_first_mm: float   # compensation at string 1 (high e)
    straight_saddle_last_mm: float    # compensation at string 6 (low E)

    # Design constraint warnings — strings whose compensation is incompatible
    # with a shared saddle arrangement
    design_constraints: List[SaddleDesignConstraint] = None

    source: str = (
        "Elmendorp, S. 'It's All About the Core, or How to Estimate "
        "Compensation.' American Lutherie #104, 2010."
    )
    accuracy_note: str = (
        "Predicted accuracy: ±0.5mm (limited by core diameter measurement "
        "precision and saddle witness point location). Core diameter error "
        "is magnified by factor of 2 in the bending term."
    )

    def __post_init__(self):
        if self.design_constraints is None:
            self.design_constraints = []


# ─────────────────────────────────────────────────────────────────────────────
# Main analysis function
# ─────────────────────────────────────────────────────────────────────────────

def _detect_design_constraints(
    results: List[StringCompensation],
) -> List[SaddleDesignConstraint]:
    """
    Identify strings whose compensation requirement is incompatible with a
    shared saddle arrangement.

    The formula manifests the phenomenon — it does not resolve it. When a
    string's required compensation deviates significantly from the linear
    trend across all strings, no positioning of a shared straight or simply
    angled saddle can serve it adequately.

    Method: fit a linear trend to all string compensations by position (0..N-1).
    Flag strings that deviate more than 1.5mm from that trend. A straight or
    gently angled saddle can follow a linear trend; it cannot follow outliers.

    Practical wound string alternatives: only suggested for strings where wound
    construction is actually used in practice (not high e, not classical trebles).
    """
    import statistics

    constraints: List[SaddleDesignConstraint] = []
    n = len(results)
    if n < 2:
        return constraints

    comps = [r.comp_total_mm for r in results]
    positions = list(range(n))

    # Linear regression: trend line across string positions
    mean_x = sum(positions) / n
    mean_y = sum(comps) / n
    ss_xx = sum((x - mean_x)**2 for x in positions)
    ss_xy = sum((positions[i] - mean_x) * (comps[i] - mean_y) for i in range(n))
    slope = ss_xy / ss_xx if ss_xx != 0 else 0
    intercept = mean_y - slope * mean_x

    for i, r in enumerate(results):
        trend_value = intercept + slope * i
        deviation = r.comp_total_mm - trend_value

        if abs(deviation) >= 1.5:
            s = r.string_def
            bend_pct = int(r.bend_fraction * 100)

            explanation = (
                f"The {s.name} string requires {r.comp_total_mm:.2f}mm compensation, "
                f"which is {deviation:+.2f}mm from the linear saddle trend "
                f"({trend_value:.2f}mm). "
                f"{bend_pct}% of this is bending stiffness — independent of action "
                f"and scale, driven by this string's {s.material} core diameter "
                f"({s.core_dia_in:.3f}\") and tension ({s.tension_N:.0f}N). "
                f"A shared saddle following the trend line would leave this string "
                f"{abs(deviation):.1f}mm out of compensation. "
                f"The formula reveals a design constraint, not a number to cut toward."
            )

            options: List[str] = []

            # Wound alternative — only for strings where wound is practical
            wound_practical = (
                not s.wound
                and s.material == "steel"
                and s.name not in ("High e",)   # wound high e not practical
                and s.total_dia_in >= 0.014     # not too thin for wound
            )
            if wound_practical:
                options.append(
                    f"Switch to a wound {s.name} string — wound construction "
                    f"uses a thin steel core, dramatically reducing the bending "
                    f"stiffness term. This is the most common fix for plain G "
                    f"intonation on electric guitars."
                )

            options.append(
                f"Use a compensated saddle with an individual witness point for "
                f"the {s.name} string (broken saddle, stepped slot, or per-string "
                f"bridge) positioned at the required {r.comp_total_mm:.1f}mm."
            )
            options.append(
                "Distribute compensation across nut and saddle — nut set-forward "
                "reduces the required saddle setback, softening the outlier effect."
            )
            if abs(deviation) >= 2.5:
                options.append(
                    f"This deviation ({deviation:+.1f}mm) is large enough that a "
                    f"straight saddle compromise will leave this string audibly "
                    f"out of tune in first-position chords regardless of saddle angle."
                )

            r.anomaly = True
            r.anomaly_note = (
                f"Design constraint: {r.comp_total_mm:.2f}mm required, "
                f"{deviation:+.2f}mm from saddle trend line."
            )

            constraints.append(SaddleDesignConstraint(
                string_name=s.name,
                comp_required_mm=round(r.comp_total_mm, 3),
                neighbour_avg_mm=round(trend_value, 3),
                deviation_mm=round(deviation, 3),
                design_options=options,
                explanation=explanation,
            ))

    return constraints


def analyze_compensation(
    scale_length_in: float,
    string_set_key: str = "acoustic_light_012",
    action_at_12th_mm: float = 2.0,
) -> CompensationSpec:
    """
    Predict per-string saddle compensation from physical parameters.

    Uses Elmendorp [11]:
        Comp = a₁₂² × E × S / (2 × T₀ × L₀)  +  2√(E × J / T₀)

    The formula predicts how much saddle setback each string requires.
    Where a string's requirement is incompatible with a shared saddle
    arrangement, a SaddleDesignConstraint is raised in the result. This
    is the formula manifesting a physical phenomenon — the required response
    is a change to string choice or saddle design, not a positioning target.

    Args:
        scale_length_in:   Nominal scale length (inches)
        string_set_key:    Key from STRING_SETS
        action_at_12th_mm: Action at 12th fret (mm). Default 2.0mm.

    Returns:
        CompensationSpec with per-string results and any design constraints.
    """
    if string_set_key not in STRING_SETS:
        raise ValueError(
            f"Unknown string set: {string_set_key!r}. "
            f"Available: {list(STRING_SETS.keys())}"
        )

    L0_m = scale_length_in * 0.0254
    a12_m = action_at_12th_mm / 1000.0

    results: List[StringCompensation] = []
    for s in STRING_SETS[string_set_key]:
        E = MATERIAL_MOE[s.material]
        S = core_area(s.core_dia_m, s.hex_core)
        J = core_moment(s.core_dia_m, s.hex_core)
        cs, cb, ct = comp_total(a12_m, E, s.core_dia_m, s.tension_N, L0_m, s.hex_core)

        results.append(StringCompensation(
            string_def=s,
            scale_m=L0_m,
            a12_m=a12_m,
            E_Pa=E,
            S_m2=S,
            J_m4=J,
            comp_stretch_m=cs,
            comp_bend_m=cb,
            comp_total_m=ct,
        ))

    # Detect design constraints — strings incompatible with shared saddle
    constraints = _detect_design_constraints(results)

    comps = [r.comp_total_mm for r in results]

    return CompensationSpec(
        scale_length_in=scale_length_in,
        scale_length_mm=round(scale_length_in * 25.4, 2),
        action_at_12th_mm=action_at_12th_mm,
        string_set_key=string_set_key,
        strings=results,
        straight_saddle_first_mm=round(comps[0], 3),
        straight_saddle_last_mm=round(comps[-1], 3),
        design_constraints=constraints,
    )


def compensation_for_string(
    scale_length_in: float,
    core_dia_in: float,
    tension_N: float,
    material: str = "steel",
    action_at_12th_mm: float = 2.0,
    hex_core: bool = False,
) -> tuple[float, float, float]:
    """
    Single-string compensation calculation.

    Args:
        scale_length_in: Nominal scale length (inches)
        core_dia_in:     Core diameter (inches) — NOT wound diameter
        tension_N:       Open string tension at pitch (N)
        material:        Core material key (steel/nylon_solid/nylon_floss/gut)
        action_at_12th_mm: Action at 12th fret (mm)
        hex_core:        True for hexagonal core

    Returns:
        Tuple of (comp_stretch_mm, comp_bend_mm, comp_total_mm)
    """
    E = MATERIAL_MOE.get(material, MATERIAL_MOE["steel"])
    L0_m = scale_length_in * 0.0254
    a12_m = action_at_12th_mm / 1000.0
    d_m = core_dia_in * 0.0254
    cs, cb, ct = comp_total(a12_m, E, d_m, tension_N, L0_m, hex_core)
    return round(cs * 1000, 3), round(cb * 1000, 3), round(ct * 1000, 3)
