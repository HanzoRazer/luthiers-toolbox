"""
soundhole_stiffness.py — Top Plate Stiffness Reduction from Soundhole
=====================================================================

DECOMP-002 Phase 4: extracted from soundhole_calc.py.

This module contains:
- StiffnessResult dataclass for plate modal frequency analysis
- compute_top_stiffness_reduction() — Gore-calibrated stiffness model
- BracingIndicatorResult dataclass for construction prescriptions
- get_bracing_implication() — derive bracing prescription from StiffnessResult
- _BRACING_PRESCRIPTIONS — lookup table for bracing requirements

Physics reference:
  Gore & Gilet, Contemporary Acoustic Guitar Design and Build, Vol. 1
  Leissa, Vibration of Plates

Calibration status:
  K = 0.798 (single-point calibration against Gore's empirical data)
  Update this constant as measured instrument data becomes available.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional


# ── Calibration constants ────────────────────────────────────────────────────

# Calibration constant K — derived from Gore & Gilet empirical data
# K = 0.798 gives 6.0% frequency drop for standard OM config:
#   96mm hole, 165mm from neck block, 495×380mm plate, no bracing
# This matches Gore's reported 5–8% range for soundhole cutting.
# Single calibration point — update when measured instrument data becomes available.
STIFFNESS_K: float = 0.798

# Bracing restoration factor — fraction of stiffness loss recovered by bracing.
# 0.70 = standard flat-top: soundhole patch + 2 radial braces restores ~70%
# 0.00 = unbraced (free plate, pre-brace tap tone measurement)
# 0.90 = heavily braced / archtop (minimal net loss)
BRACING_RESTORE_DEFAULT: float = 0.70


# ── StiffnessResult dataclass ────────────────────────────────────────────────

@dataclass
class StiffnessResult:
    """
    Top plate stiffness analysis — effect of soundhole on plate modal frequency.

    Physics basis:
        The soundhole removes material from the top plate, reducing both mass
        and stiffness in the region of the hole. The net effect on the plate's
        fundamental (1,1) mode frequency depends on:
        1. How much area is removed (area_ratio)
        2. Where in the mode shape the hole sits (mode_coupling)
        3. How much stiffness the bracing restores (bracing_restore)

        Formula (Leissa/Gore calibrated power law):
            raw_reduction = K × (A_hole/A_plate)^0.75 × sin(π × x/body_length)
            net_reduction = raw_reduction × (1 - bracing_restore)
            freq_ratio    = 1 - net_reduction

    Calibration:
        K = 0.798, calibrated to Gore & Gilet empirical data:
        ~6% frequency drop for 96mm hole at 165mm on standard OM (no bracing).
        Bracing restoration factor 0.70 typical for soundhole patch + radial braces.

    Status:
        Single-point calibration. Accuracy improves with measured instrument data.
    """
    # Inputs
    plate_area_m2: float
    hole_area_m2: float
    x_from_neck_mm: float
    body_length_mm: float
    bracing_restore: float

    # Intermediate
    area_ratio: float
    mode_coupling: float            # sin(π × x/body_length)
    raw_reduction_pct: float        # before bracing restoration
    bracing_recovered_pct: float    # stiffness bracing gives back

    # Outputs
    net_reduction_pct: float        # actual net drop in plate modal frequency
    freq_ratio: float               # f_with_hole / f_no_hole
    status: str                     # "minimal" | "moderate" | "significant"

    # Optional: actual frequencies if material properties supplied
    f_plate_no_hole_hz: Optional[float] = None
    f_plate_with_hole_hz: Optional[float] = None

    @property
    def construction_note(self) -> str:
        if self.status == "minimal":
            return (
                f"Net stiffness reduction {self.net_reduction_pct:.1f}% — "
                "standard soundhole patch adequate. No additional radial braces required."
            )
        elif self.status == "moderate":
            return (
                f"Net stiffness reduction {self.net_reduction_pct:.1f}% — "
                "soundhole patch required. Consider 2 short radial braces flanking the hole "
                "to restore longitudinal stiffness in the neck-to-bridge band."
            )
        else:
            return (
                f"Net stiffness reduction {self.net_reduction_pct:.1f}% — "
                "significant. Soundhole patch plus radial braces mandatory. "
                "Consider reducing hole diameter by 5–10mm or moving hole "
                "closer to neck block to reduce mode coupling."
            )


# ── Main computation ─────────────────────────────────────────────────────────

def compute_top_stiffness_reduction(
    hole_area_m2: float,
    x_from_neck_mm: float,
    body_length_mm: float,
    plate_length_mm: float,
    plate_width_mm: float,
    bracing_restore: float = BRACING_RESTORE_DEFAULT,
    K: float = STIFFNESS_K,
    # Optional: material properties for absolute frequency output
    E_L_Pa: Optional[float] = None,
    E_C_Pa: Optional[float] = None,
    rho_kg_m3: Optional[float] = None,
    thickness_mm: Optional[float] = None,
    eta: float = 1.0,
) -> StiffnessResult:
    """
    Compute the effect of a soundhole on the top plate's fundamental modal frequency.

    Uses a power-law stiffness reduction model calibrated against Gore & Gilet
    empirical measurements. Optionally computes absolute frequencies if material
    properties are supplied.

    The model treats the entire plate (neck block to tail block) as the reference
    plate, with the soundhole position expressed as a fraction of body length.
    This choice of reference length matches Gore's measurement convention and
    gives the correct mode coupling values for the traditional 1/3 placement.

    Args:
        hole_area_m2:      Total port area (top ports only — side ports excluded)
        x_from_neck_mm:    Soundhole center distance from neck block (mm)
        body_length_mm:    Total internal body length (mm)
        plate_length_mm:   Top plate length along grain (mm) — typically = body_length
        plate_width_mm:    Top plate width across grain (mm) — typically = lower bout
        bracing_restore:   Fraction of stiffness loss recovered by bracing (0–1)
                           Default 0.70 = soundhole patch + 2 radial braces
                           Use 0.00 for free plate (pre-brace tap tone measurement)
        K:                 Calibration constant (default 0.798, Gore-calibrated)
        E_L_Pa:            Longitudinal Young's modulus (Pa) — optional
        E_C_Pa:            Cross-grain Young's modulus (Pa) — optional
        rho_kg_m3:         Wood density (kg/m³) — optional
        thickness_mm:      Plate thickness (mm) — optional
        eta:               Boundary condition factor (default 1.0 free plate)

    Returns:
        StiffnessResult with reduction percentages, freq_ratio, and construction note
    """
    plate_area_m2 = (plate_length_mm / 1000.0) * (plate_width_mm / 1000.0)
    area_ratio = hole_area_m2 / plate_area_m2 if plate_area_m2 > 0 else 0.0

    # Mode coupling: sin(π × x_hole / body_length)
    # This uses body_length (not effective plate length) because Gore's calibration
    # data measures from the neck block. At the traditional 1/3 position:
    # sin(π × 0.333) = 0.866 — matching the calibration point.
    x_frac = x_from_neck_mm / body_length_mm if body_length_mm > 0 else 0.333
    x_frac = max(0.0, min(1.0, x_frac))
    mode_coupling = math.sin(math.pi * x_frac)

    # Raw stiffness reduction (no bracing, free plate)
    raw_reduction = K * (area_ratio ** 0.75) * mode_coupling if area_ratio > 0 else 0.0

    # Net reduction after bracing restoration
    bracing_recovered = raw_reduction * bracing_restore
    net_reduction = raw_reduction * (1.0 - bracing_restore)

    freq_ratio = 1.0 - net_reduction
    freq_ratio = max(0.5, freq_ratio)  # physical floor

    # Status classification
    if net_reduction * 100 < 1.5:
        status = "minimal"
    elif net_reduction * 100 < 3.0:
        status = "moderate"
    else:
        status = "significant"

    # Optional absolute frequencies
    f_no_hole: Optional[float] = None
    f_with_hole: Optional[float] = None

    if all(v is not None for v in [E_L_Pa, E_C_Pa, rho_kg_m3, thickness_mm]):
        try:
            # Import here to avoid circular dependency if plate_design not available
            from .plate_design.thickness_calculator import plate_modal_frequency
            h_m = thickness_mm / 1000.0  # type: ignore[operator]
            a_m = plate_length_mm / 1000.0
            b_m = plate_width_mm / 1000.0
            f_no_hole = plate_modal_frequency(
                E_L_Pa, E_C_Pa, rho_kg_m3, h_m, a_m, b_m, eta=eta  # type: ignore[arg-type]
            )
            f_with_hole = f_no_hole * freq_ratio
        except ImportError:
            pass  # plate_design not available — freq values remain None

    return StiffnessResult(
        plate_area_m2=round(plate_area_m2, 4),
        hole_area_m2=round(hole_area_m2, 6),
        x_from_neck_mm=x_from_neck_mm,
        body_length_mm=body_length_mm,
        bracing_restore=bracing_restore,
        area_ratio=round(area_ratio, 4),
        mode_coupling=round(mode_coupling, 4),
        raw_reduction_pct=round(raw_reduction * 100, 2),
        bracing_recovered_pct=round(bracing_recovered * 100, 2),
        net_reduction_pct=round(net_reduction * 100, 2),
        freq_ratio=round(freq_ratio, 4),
        status=status,
        f_plate_no_hole_hz=round(f_no_hole, 1) if f_no_hole else None,
        f_plate_with_hole_hz=round(f_with_hole, 1) if f_with_hole else None,
    )


# ── Bracing prescriptions ────────────────────────────────────────────────────

# Prescription thresholds based on raw_reduction_pct (free plate, no bracing)
# These are calibrated to the K=0.798 model at the standard 1/3 body position.
# The raw_reduction (not net) drives the prescription because the builder is
# deciding what bracing to INSTALL — before bracing is in place.

BRACING_PRESCRIPTIONS: List[Dict] = [
    {
        "raw_reduction_max_pct": 3.0,
        "level": "none",
        "status": "OK",
        "label": "No reinforcement required",
        "patch_required": False,
        "radial_braces": 0,
        "brace_spec": None,
        "description": (
            "Hole removes less than 3% of plate stiffness — within the natural "
            "variation of tap-tuned tops. No soundhole patch or radial braces needed. "
            "Standard rosette glue joint provides adequate edge support."
        ),
        "construction": [
            "Cut rosette channel, glue rosette, level flush.",
            "Cut soundhole. Clean edge with sharp chisel.",
            "Rosette glue joint provides sufficient ring support.",
        ],
    },
    {
        "raw_reduction_max_pct": 5.0,
        "level": "patch",
        "status": "RECOMMENDED",
        "label": "Soundhole patch recommended",
        "patch_required": False,
        "radial_braces": 0,
        "brace_spec": None,
        "description": (
            "Hole removes 3–5% of plate stiffness. A soundhole patch is recommended "
            "but not strictly required — omitting it on a thin or soft top may produce "
            "gradual top bellying near the soundhole over time. Classical guitars and "
            "cedar tops in this range should always use a patch."
        ),
        "construction": [
            "Soundhole patch: 1.5mm spruce ring, grain parallel to top grain.",
            "Width 15–18mm, glued flush to underside around full perimeter.",
            "Patch restores approximately 30–35% of lost stiffness.",
        ],
    },
    {
        "raw_reduction_max_pct": 6.5,
        "level": "patch_braces_light",
        "status": "REQUIRED",
        "label": "Patch + 2 radial braces required",
        "patch_required": True,
        "radial_braces": 2,
        "brace_spec": {"width_mm": 5.0, "height_mm": 5.0, "length_mm": 70.0, "profile": "parabolic"},
        "description": (
            "Standard acoustic guitar range (90–105mm holes). Patch alone is insufficient — "
            "2 short radial braces flanking the hole in the upper and lower positions "
            "are required to restore longitudinal stiffness in the neck-to-bridge band. "
            "This is the construction used on all standard Martin and Gibson flat-tops."
        ),
        "construction": [
            "Soundhole patch: 1.5–2mm spruce ring, 15mm wide, full perimeter.",
            "2 radial braces: 5mm wide × 5mm tall × 70mm long, parabolic profile.",
            "Position: one above the hole (toward neck), one below (toward tail).",
            "Braces run along the top's grain direction, centered on the hole.",
            "Patch + 2 braces restores approximately 60–70% of lost stiffness.",
        ],
    },
    {
        "raw_reduction_max_pct": 8.0,
        "level": "patch_braces_heavy",
        "status": "REQUIRED",
        "label": "Patch + 2 tall radial braces required",
        "patch_required": True,
        "radial_braces": 2,
        "brace_spec": {"width_mm": 5.0, "height_mm": 8.0, "length_mm": 80.0, "profile": "parabolic"},
        "description": (
            "Larger holes (105–120mm). Taller braces needed for adequate stiffness "
            "restoration. Consider whether the hole size is justified — at this range "
            "the bracing adds significant mass that partially offsets the acoustic "
            "benefit of the larger opening. Some builders prefer 2 side braces + "
            "2 end braces (4 total in a cross pattern) at this diameter."
        ),
        "construction": [
            "Soundhole patch: 2mm spruce ring, 18mm wide, full perimeter.",
            "2 radial braces: 5mm wide × 8mm tall × 80mm long, parabolic profile.",
            "Optional: additional cross-grain brace on upper side of hole.",
            "Patch + 2 tall braces restores approximately 65–75% of lost stiffness.",
        ],
    },
    {
        "raw_reduction_max_pct": 999.0,
        "level": "full_reinforcement",
        "status": "CRITICAL",
        "label": "Full reinforcement required",
        "patch_required": True,
        "radial_braces": 4,
        "brace_spec": {"width_mm": 6.0, "height_mm": 8.0, "length_mm": 80.0, "profile": "parabolic"},
        "description": (
            "Hole exceeds 120mm or sits in a high-mode-coupling position (>40% of body length). "
            "Full reinforcement required: patch ring plus 4 radial braces in a cross pattern, "
            "OR a doubler plate (thin spruce plate glued over the entire upper bout interior). "
            "At this level, consider whether the acoustic benefit of the larger opening "
            "outweighs the structural and mass consequences. Side-port + smaller main hole "
            "may be a better design choice."
        ),
        "construction": [
            "Soundhole patch: 2.5mm spruce ring, 20mm wide, full perimeter.",
            "4 radial braces: 6mm wide × 8mm tall × 80mm long, parabolic profile.",
            "Braces at 12, 3, 6, and 9 o'clock positions around hole.",
            "OR: doubler plate (1.5mm spruce sheet covering full soundhole region).",
            "Consider redesigning with smaller main hole + side port(s).",
        ],
    },
]


# ── BracingIndicatorResult dataclass ─────────────────────────────────────────

@dataclass
class BracingIndicatorResult:
    """
    Bracing prescription for a soundhole based on stiffness reduction analysis.

    Derived from compute_top_stiffness_reduction() raw_reduction_pct —
    the free-plate stiffness loss before any bracing is installed.
    This drives the prescription because the builder chooses bracing BEFORE
    installing it, not after.

    Connection to bracing_calc.py:
        brace_spec dimensions (width_mm, height_mm, length_mm) are compatible
        with BracingCalcInput fields in calculators/bracing_calc.py.
        To compute brace section area: BracingCalcInput(**brace_spec, profile_type='parabolic')
        To compute brace mass: estimate_mass_grams(BracingCalcInput(**brace_spec))
        This connection is intentionally not made here to avoid the Pydantic
        dependency — the caller can bridge to bracing_calc.py if needed.
    """
    # Inputs
    hole_diameter_equiv_mm: float
    raw_reduction_pct: float         # stiffness loss without bracing
    x_from_neck_mm: float
    body_length_mm: float

    # Prescription
    level: str                        # "none" | "patch" | "patch_braces_light" | etc.
    status: str                       # "OK" | "RECOMMENDED" | "REQUIRED" | "CRITICAL"
    label: str
    patch_required: bool
    radial_braces: int
    brace_spec: Optional[Dict]        # width_mm, height_mm, length_mm, profile

    # Text
    description: str
    construction_steps: List[str]

    # Cross-reference to bracing_calc.py
    bracing_calc_compatible: bool = True
    bracing_calc_note: str = (
        "brace_spec dimensions are compatible with BracingCalcInput. "
        "Call calculate_brace_section(BracingCalcInput(**brace_spec)) "
        "for cross-section area, or estimate_mass_grams() for brace mass."
    )

    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "label": self.label,
            "patch_required": self.patch_required,
            "radial_braces": self.radial_braces,
            "brace_spec": self.brace_spec,
            "raw_reduction_pct": self.raw_reduction_pct,
            "construction_steps": self.construction_steps,
        }


def get_bracing_implication(
    stiffness: StiffnessResult,
    main_port_diameter_equiv_mm: Optional[float] = None,
) -> BracingIndicatorResult:
    """
    Derive bracing prescription from a StiffnessResult.

    Uses raw_reduction_pct (not net) because the builder chooses bracing
    BEFORE installing it. The net reduction depends on what bracing is
    installed, but the prescription tells you what to install.

    Args:
        stiffness:                   StiffnessResult from compute_top_stiffness_reduction()
        main_port_diameter_equiv_mm: Equivalent diameter of the main soundhole (mm).
                                     If None, computed from stiffness.hole_area_m2.

    Returns:
        BracingIndicatorResult with prescription level, status, and construction steps
    """
    raw_pct = stiffness.raw_reduction_pct

    # Find the right prescription tier
    prescription = BRACING_PRESCRIPTIONS[-1]   # default to most severe
    for p in BRACING_PRESCRIPTIONS:
        if raw_pct <= p["raw_reduction_max_pct"]:
            prescription = p
            break

    # Derive equivalent diameter if not supplied
    if main_port_diameter_equiv_mm is None:
        main_port_diameter_equiv_mm = 2.0 * math.sqrt(
            stiffness.hole_area_m2 / math.pi
        ) * 1000.0

    return BracingIndicatorResult(
        hole_diameter_equiv_mm=round(main_port_diameter_equiv_mm, 1),
        raw_reduction_pct=round(raw_pct, 2),
        x_from_neck_mm=stiffness.x_from_neck_mm,
        body_length_mm=stiffness.body_length_mm,
        level=prescription["level"],
        status=prescription["status"],
        label=prescription["label"],
        patch_required=prescription["patch_required"],
        radial_braces=prescription["radial_braces"],
        brace_spec=prescription["brace_spec"],
        description=prescription["description"],
        construction_steps=prescription["construction"],
    )
