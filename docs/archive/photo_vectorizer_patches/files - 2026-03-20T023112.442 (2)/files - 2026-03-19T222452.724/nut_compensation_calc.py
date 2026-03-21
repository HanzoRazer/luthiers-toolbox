# services/api/app/calculators/nut_compensation_calc.py
"""
Nut Compensation Calculator — GEOMETRY-007

Covers: zero-fret vs traditional nut systems, nut setback calculation,
nut slot depth requirements, open string tone character, and fret
position formula (12-TET).

Source honesty — three categories of formulas used here
========================================================

1. EXACT MATHEMATICS — no empiricism, fully derived:
   The 12-TET fret position formula is pure Euclidean/logarithmic arithmetic.
   Given a scale length L and fret number n:

       d_n_from_saddle = L / 2^(n/12)
       d_n_from_nut    = L × (1 - 1/2^(n/12))

   These produce the fret positions at which a stopped string produces
   exactly one semitone per fret in equal temperament. No constants, no
   empirical fitting, no uncertainty. Results are exact for any scale length.

2. EMPIRICAL WITH THEORETICAL BACKING — saddle compensation:
   The physical mechanism is understood: string bending stiffness and
   fretting-induced tension increase both raise the pitch of fretted notes,
   requiring the saddle to be set back from the theoretical nut position.

   The formula C_saddle ≈ k_gauge × gauge_diameter is an empirical fit to
   measured compensation on real instruments. Gore & Gilet (Vol. 1, "Contemporary
   Acoustic Guitar Design and Build") derive this from string mechanics and
   validate against measured instruments. The k_gauge factor (typically 0.6–1.0
   for acoustic strings) is a fit coefficient, not a derived constant.

   Uncertainty: ±15–20%, setup-dependent.

3. EMPIRICAL — nut compensation and zero-fret compensation:
   The dominant physical mechanism for nut compensation is the bending stiffness
   correction at the short open-string segment from nut to the string's first
   vibrational node. This is NOT simple Pythagorean string stretching from
   fretting action (which gives values ~20× too small).

   The practical formula C_nut ≈ C_saddle × k_nut uses k_nut = 0.20–0.40,
   with heavier wound strings toward the lower end and light plain strings
   toward the upper end. These k_nut values are from:
     - Gore & Gilet Vol. 1 spreadsheet methodology
     - Luthier practice consensus (Siminoff, StewMac instructional content)
     - Calibrated against measured nut positions on production instruments

   Uncertainty: ±30% — meaningfully less precise than saddle compensation.
   The correct value is setup-specific: action height, string brand, and
   playing style all shift the optimal nut position.

   Zero-fret compensation: residual ~30% of traditional nut compensation.
   The open string on a zero-fret guitar sits at fret crown height (same as
   all frets), reducing the bending stiffness mismatch between open and fretted
   notes. A small correction may still be applied on precision builds.
   Even less published data exists for this figure than for traditional nut.

Physical mechanism: why nut compensation exists
================================================

When a string is fretted, it contacts the fret crown. The portion of the string
between the fret and the nut is no longer vibrating — but the string still bends
around the fret crown. The energy stored in this bend raises the effective pitch
above what pure tension mechanics predicts.

For the OPEN string, the vibrating segment goes from nut to saddle. The nut is
a different constraint geometry than a fret crown. The bending correction is
different between open and fretted conditions.

Additionally, the vibrating length of an open string is L (scale length).
The vibrating length of a string fretted at fret 1 is L/2^(1/12).
For a string with finite bending stiffness, shorter vibrating segments produce
pitches slightly higher than pure-tension theory predicts. The nut compensation
adjusts the open string length to pre-compensate for this asymmetry.

The nut must be set back (toward headstock) from the theoretical position so that
the open string is slightly flat relative to the idealized pitch, which after
the bending stiffness correction lands at the correct pitch.

Zero-fret vs traditional nut: the open string tone argument
===========================================================

Traditional nut:
  Open strings contact a different material (bone, TUSQ, brass, etc.) than
  fretted strings (fret wire, nickel-silver or harder alloys).
  This material difference produces a subtly different attack envelope on
  open strings compared to fretted strings — detectable particularly in
  close-mic recording and classical technique.

Zero-fret:
  Open strings contact the same fret wire material as all fretted notes.
  This eliminates the material discontinuity. Open strings and fretted strings
  have matching attack character. The zero fret also wears under open string
  playing, which is the main practical downside.

Sources:
    - Gore & Gilet, "Contemporary Acoustic Guitar Design and Build" Vol. 1
      (string mechanics, compensation theory, k_nut values)
    - Siminoff, "The Luthier's Handbook" (nut slot depth practice)
    - StewMac instructional content (zero fret installation, nut slot specs)
    - Luthier practice consensus (k_nut range, zero fret residual compensation)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Physical constants and empirical coefficients
# ─────────────────────────────────────────────────────────────────────────────

# ── EXACT (no empiricism) ─────────────────────────────────────────────────────
# Semitone ratio for 12-TET equal temperament
SEMITONE_RATIO: float = 2 ** (1 / 12)    # 1.05946...

# ── EMPIRICAL — saddle compensation coefficient ───────────────────────────────
# C_saddle ≈ K_SADDLE × gauge_diameter
# Source: Gore & Gilet Vol.1; calibrated against measured instruments
# Uncertainty: ±15%
K_SADDLE_WOUND: float = 0.80   # wound strings (bass strings)
K_SADDLE_PLAIN: float = 0.60   # plain strings (treble strings)

# ── EMPIRICAL — nut compensation factor ───────────────────────────────────────
# C_nut ≈ C_saddle × K_NUT
# Source: Gore & Gilet methodology; luthier practice consensus
# Uncertainty: ±30%
K_NUT_WOUND: float  = 0.22    # heavy wound strings (low E, A)
K_NUT_PLAIN: float  = 0.35    # plain strings (G, B, high e)
K_NUT_LIGHT_WOUND: float = 0.28  # light wound (D, G wound)

# ── EMPIRICAL — zero fret residual compensation ───────────────────────────────
# Residual compensation for zero-fret vs theoretical position
# Source: luthier practice; limited published data
# Uncertainty: ±50% — treat as order-of-magnitude estimate only
K_ZERO_FRET_RESIDUAL: float = 0.30  # fraction of traditional nut compensation

# ── NUT SLOT DEPTH TARGETS ────────────────────────────────────────────────────
# Target string clearance above fret 1 crown, at the nut-fret-1 position
# String bottom should clear fret 1 by this amount
# Source: Siminoff; StewMac; shop practice
NUT_CLEARANCE_PLAIN_IN: float  = 0.012   # plain strings
NUT_CLEARANCE_WOUND_IN: float  = 0.017   # wound strings

# Typical nut blank height
NUT_BLANK_HEIGHT_IN: float = 0.200  # standard acoustic nut blank

# Distance the zero-fret nut sits behind the zero fret
ZERO_FRET_NUT_SETBACK_IN: float = 0.375  # 3/8" typical behind zero fret


# ─────────────────────────────────────────────────────────────────────────────
# String definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StringSpec:
    """A single string in the set."""
    name: str              # e.g., "Low E"
    gauge_in: float        # diameter in inches
    wound: bool            # wound vs plain
    open_note: str         # open note name (e.g., "E2")


# Standard 6-string acoustic sets
STRING_SETS: Dict[str, List[StringSpec]] = {
    "acoustic_light_012": [
        StringSpec("Low E",    0.053, True,  "E2"),
        StringSpec("A",        0.042, True,  "A2"),
        StringSpec("D",        0.032, True,  "D3"),
        StringSpec("G",        0.024, True,  "G3"),
        StringSpec("B",        0.016, False, "B3"),
        StringSpec("High e",   0.012, False, "E4"),
    ],
    "acoustic_medium_013": [
        StringSpec("Low E",    0.056, True,  "E2"),
        StringSpec("A",        0.045, True,  "A2"),
        StringSpec("D",        0.035, True,  "D3"),
        StringSpec("G",        0.026, True,  "G3"),
        StringSpec("B",        0.017, False, "B3"),
        StringSpec("High e",   0.013, False, "E4"),
    ],
    "electric_light_009": [
        StringSpec("Low E",    0.042, True,  "E2"),
        StringSpec("A",        0.032, True,  "A2"),
        StringSpec("D",        0.024, True,  "D3"),
        StringSpec("G",        0.016, False, "G3"),
        StringSpec("B",        0.011, False, "B3"),
        StringSpec("High e",   0.009, False, "E4"),
    ],
    "electric_medium_010": [
        StringSpec("Low E",    0.046, True,  "E2"),
        StringSpec("A",        0.036, True,  "A2"),
        StringSpec("D",        0.026, True,  "D3"),
        StringSpec("G",        0.017, False, "G3"),
        StringSpec("B",        0.013, False, "B3"),
        StringSpec("High e",   0.010, False, "E4"),
    ],
    "nylon_classical": [
        StringSpec("Low E",    0.043, False, "E2"),  # treble-style monofilament
        StringSpec("A",        0.032, False, "A2"),
        StringSpec("D",        0.028, False, "D3"),
        StringSpec("G",        0.029, False, "G3"),  # approx rectified
        StringSpec("B",        0.029, False, "B3"),
        StringSpec("High e",   0.028, False, "E4"),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Core geometry: fret positions
# ─────────────────────────────────────────────────────────────────────────────

def fret_position_from_saddle(scale_length_in: float, fret_n: int) -> float:
    """
    Distance from saddle to fret n (12-TET equal temperament).

    FORMULA SOURCE: Exact mathematics — 12-TET equal temperament.
    No empirical constants. Result is exact for any scale length.

        d = L / 2^(n/12)

    Args:
        scale_length_in: Nominal scale length (inches)
        fret_n:          Fret number (0 = nut/zero-fret position)

    Returns:
        Distance from saddle to fret n (inches)
    """
    return scale_length_in / (SEMITONE_RATIO ** fret_n)


def fret_position_from_nut(scale_length_in: float, fret_n: int) -> float:
    """
    Distance from nut to fret n (12-TET).

    FORMULA SOURCE: Exact mathematics.

        d = L × (1 - 1/2^(n/12))
    """
    return scale_length_in - fret_position_from_saddle(scale_length_in, fret_n)


def all_fret_positions(
    scale_length_in: float,
    num_frets: int = 20,
) -> List[Dict]:
    """
    Return all fret positions for a given scale length.

    Returns list of dicts with keys: fret, from_nut_in, from_saddle_in,
    from_nut_mm, from_saddle_mm.
    """
    return [
        {
            "fret": n,
            "from_nut_in":    round(fret_position_from_nut(scale_length_in, n), 4),
            "from_saddle_in": round(fret_position_from_saddle(scale_length_in, n), 4),
            "from_nut_mm":    round(fret_position_from_nut(scale_length_in, n) * 25.4, 3),
            "from_saddle_mm": round(fret_position_from_saddle(scale_length_in, n) * 25.4, 3),
        }
        for n in range(num_frets + 1)
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Compensation calculations
# ─────────────────────────────────────────────────────────────────────────────

def saddle_compensation(string: StringSpec) -> float:
    """
    Estimated saddle setback for a single string.

    FORMULA SOURCE: Empirical — Gore & Gilet Vol.1 methodology.
    Uncertainty: ±15%.

    C_saddle ≈ k × gauge_diameter
    k = 0.80 (wound) or 0.60 (plain)
    """
    k = K_SADDLE_WOUND if string.wound else K_SADDLE_PLAIN
    return k * string.gauge_in


def nut_compensation_traditional(string: StringSpec) -> float:
    """
    Estimated nut setback for a single string, traditional nut system.

    FORMULA SOURCE: Empirical — Gore & Gilet methodology + luthier consensus.
    Uncertainty: ±30%. This is a working estimate, not a precision value.

    C_nut ≈ C_saddle × k_nut
    k_nut = 0.22 (heavy wound) / 0.28 (light wound) / 0.35 (plain)

    Physical mechanism: bending stiffness correction at the short open
    string segment. See module docstring for full explanation.
    """
    C_s = saddle_compensation(string)
    if not string.wound:
        k = K_NUT_PLAIN
    elif string.gauge_in >= 0.040:
        k = K_NUT_WOUND
    else:
        k = K_NUT_LIGHT_WOUND
    return C_s * k


def nut_compensation_zero_fret(string: StringSpec) -> float:
    """
    Residual zero-fret position offset (small or zero for most builds).

    FORMULA SOURCE: Empirical — very limited published data.
    Uncertainty: ±50%. Treat as order-of-magnitude estimate.

    On precision builds: C_zero ≈ C_nut_traditional × 0.30
    On standard builds:  zero fret placed at theoretical position (0.0")

    Physical reason: the zero fret is already at fret crown height,
    so the bending stiffness mismatch between open and fretted conditions
    is much smaller than with a traditional nut.
    """
    return nut_compensation_traditional(string) * K_ZERO_FRET_RESIDUAL


# ─────────────────────────────────────────────────────────────────────────────
# Nut slot depth
# ─────────────────────────────────────────────────────────────────────────────

def nut_slot_depth(
    string: StringSpec,
    fret_crown_height_in: float = 0.045,
    nut_blank_height_in: float = NUT_BLANK_HEIGHT_IN,
) -> float:
    """
    Required nut slot depth for traditional nut system.

    Slot depth = nut blank height − fret crown height − target clearance

    Target clearance = how much above fret 1 crown the string bottom sits.
    Source: Siminoff; StewMac; shop practice.
    Wound strings need slightly more clearance than plain strings.

    Args:
        string:               StringSpec
        fret_crown_height_in: Crown height of fret wire in use
        nut_blank_height_in:  Height of nut blank before slotting

    Returns:
        Slot depth measured from top of nut blank (inches).
        This is how deep to cut: the string bottom will sit at this depth.
    """
    clearance = NUT_CLEARANCE_WOUND_IN if string.wound else NUT_CLEARANCE_PLAIN_IN
    depth = nut_blank_height_in - fret_crown_height_in - clearance
    return max(0.0, round(depth, 4))


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StringCompensation:
    """Per-string compensation and slot specification."""
    string: StringSpec

    # Saddle
    saddle_setback_in: float
    saddle_setback_mm: float

    # Traditional nut
    nut_setback_traditional_in: float
    nut_setback_traditional_mm: float
    nut_slot_depth_in: float
    nut_slot_depth_mm: float

    # Zero fret
    zero_fret_offset_in: float
    zero_fret_offset_mm: float

    # Source flags
    saddle_source: str = "Empirical — Gore & Gilet (±15%)"
    nut_source: str    = "Empirical — Gore & Gilet / shop practice (±30%)"
    zero_source: str   = "Empirical — limited data (±50%)"


@dataclass
class FretPositionTable:
    """Fret position table for a given scale length."""
    scale_length_in: float
    scale_length_mm: float
    positions: List[Dict]
    formula_source: str = "Exact — 12-TET equal temperament mathematics"


@dataclass
class NutSpec:
    """
    Complete nut compensation specification for an instrument.

    Contains per-string compensation values and a system comparison
    between traditional nut and zero fret approaches.
    """
    # Inputs
    scale_length_in: float
    string_set_key: str
    fret_crown_height_in: float

    # Per-string results
    strings: List[StringCompensation]

    # System comparison
    nut_system_notes: Dict[str, str]

    # Fret 1 geometry
    fret_1_distance_from_nut_in: float
    fret_1_distance_from_nut_mm: float

    # Zero fret geometry
    zero_fret_nut_setback_in: float  # how far behind zero fret the nut sits
    zero_fret_nut_height_note: str

    # Source declaration
    source_statement: str = (
        "Fret positions: exact (12-TET). "
        "Saddle compensation: empirical ±15% (Gore & Gilet). "
        "Nut compensation: empirical ±30% (Gore & Gilet / shop practice). "
        "Zero fret offset: empirical ±50% (limited published data)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# High-level analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_nut_compensation(
    scale_length_in: float,
    string_set_key: str = "acoustic_light_012",
    fret_crown_height_in: float = 0.045,
) -> NutSpec:
    """
    Complete nut compensation specification for an instrument.

    Args:
        scale_length_in:      Nominal scale length (inches)
        string_set_key:       Key from STRING_SETS
        fret_crown_height_in: Crown height of fret wire in use (default: medium 6160)

    Returns:
        NutSpec with per-string compensation and system comparison.
    """
    if string_set_key not in STRING_SETS:
        raise ValueError(
            f"Unknown string set: {string_set_key!r}. "
            f"Available: {list(STRING_SETS.keys())}"
        )

    strings_raw = STRING_SETS[string_set_key]
    fret_1_dist = fret_position_from_nut(scale_length_in, 1)

    string_comps = []
    for s in strings_raw:
        C_s  = saddle_compensation(s)
        C_nt = nut_compensation_traditional(s)
        C_zf = nut_compensation_zero_fret(s)
        slot = nut_slot_depth(s, fret_crown_height_in)

        string_comps.append(StringCompensation(
            string=s,
            saddle_setback_in=round(C_s, 4),
            saddle_setback_mm=round(C_s * 25.4, 3),
            nut_setback_traditional_in=round(C_nt, 4),
            nut_setback_traditional_mm=round(C_nt * 25.4, 3),
            nut_slot_depth_in=slot,
            nut_slot_depth_mm=round(slot * 25.4, 3),
            zero_fret_offset_in=round(C_zf, 4),
            zero_fret_offset_mm=round(C_zf * 25.4, 3),
        ))

    nut_system_notes = {
        "traditional": (
            "Nut sets open string height and acts as intonation reference. "
            "Slot depth is critical — too high causes sharp fret 1; too low causes buzz. "
            "Open strings contact nut material (bone/TUSQ/etc.); fretted strings contact "
            "fret wire. Subtle tonal difference between open and fretted notes."
        ),
        "zero_fret": (
            "Zero fret is installed at the theoretical nut position. "
            "Open and fretted strings both contact the same fret wire material — "
            "open string attack character matches fretted notes. "
            "The nut sits behind the zero fret (toward headstock) and guides string "
            "spacing only — slot depth is non-critical for intonation or height. "
            "Tradeoff: zero fret wears with open string playing; replacement is a "
            "fret job, not a nut replacement."
        ),
    }

    return NutSpec(
        scale_length_in=scale_length_in,
        string_set_key=string_set_key,
        fret_crown_height_in=fret_crown_height_in,
        strings=string_comps,
        nut_system_notes=nut_system_notes,
        fret_1_distance_from_nut_in=round(fret_1_dist, 4),
        fret_1_distance_from_nut_mm=round(fret_1_dist * 25.4, 3),
        zero_fret_nut_setback_in=ZERO_FRET_NUT_SETBACK_IN,
        zero_fret_nut_height_note=(
            "Zero fret nut slots are cut just below the zero fret crown height. "
            "String bottom in nut slot should be 0.005-0.010\" above zero fret top — "
            "strings ride on zero fret, not on nut. Nut is a lateral guide only."
        ),
    )


def fret_table(
    scale_length_in: float,
    num_frets: int = 20,
) -> FretPositionTable:
    """
    12-TET fret position table for a given scale length.

    Positions are exact — no empirical constants.

    Args:
        scale_length_in: Nominal scale length (inches)
        num_frets:       Number of frets (default 20)

    Returns:
        FretPositionTable with all fret positions
    """
    return FretPositionTable(
        scale_length_in=scale_length_in,
        scale_length_mm=round(scale_length_in * 25.4, 3),
        positions=all_fret_positions(scale_length_in, num_frets),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Standard scale presets
# ─────────────────────────────────────────────────────────────────────────────

SCALE_LENGTHS_IN: Dict[str, float] = {
    "martin_long":    25.4,   # Martin dreadnought, OM
    "gibson_short":   24.75,  # Gibson Les Paul, J-45
    "fender_strat":   25.5,   # Fender Stratocaster, Telecaster
    "prs_standard":   25.0,   # PRS
    "martin_short":   24.9,   # Martin 000, OOO
    "baritone":       27.0,   # Baritone guitar
    "classical":      25.6,   # Classical / flamenco
}
