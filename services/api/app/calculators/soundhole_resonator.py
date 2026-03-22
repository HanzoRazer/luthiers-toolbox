"""
soundhole_resonator.py — Two-Cavity Resonator Analysis for Acoustic Guitars
============================================================================

Extracted from soundhole_calc.py as part of DECOMP-002 Phase 2.

This module contains:
- TwoCavityResult dataclass for Selmer/Maccaferri resonator analysis
- analyze_two_cavity() — exact 2×2 eigenvalue solution for coupled resonators
- compute_sensitivity_curve() — f_H vs diameter design exploration

Depends on soundhole_physics.py (DECOMP-002 Phase 1) for:
- Physical constants (C_AIR, K0, GAMMA, PLATE_MASS_FACTOR)
- PortSpec dataclass
- Core Helmholtz functions

Physics references:
  Gore & Gilet, Contemporary Acoustic Guitar Design and Build, Vol. 1
  Fletcher & Rossing, The Physics of Musical Instruments, Ch. 9-10
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

from .soundhole_physics import (
    C_AIR,
    K0,
    GAMMA,
    PLATE_MASS_FACTOR,
    PortSpec,
    compute_port_neck_length,
    compute_helmholtz_multiport,
    exact_coupled_eigenfreq,
    hz_to_note,
    _hz_to_note,
)


# ── Sensitivity Curve ─────────────────────────────────────────────────────────

def compute_sensitivity_curve(
    volume_m3: float,
    current_diameter_mm: float,
    thickness_m: float = 0.0025,
    k0: float = K0,
    gamma: float = GAMMA,
    plate_mass_factor: float = PLATE_MASS_FACTOR,
    range_mm: float = 25.0,
    steps: int = 20,
) -> List[Dict]:
    """
    Compute f_H vs diameter curve around the current design point.

    Returns a list of {diameter_mm, f_hz} dicts spanning
    current_diameter ± range_mm in `steps` increments.

    Useful for showing how sensitive f_H is to small changes in diameter —
    a steep curve means careful sizing is critical; a flat curve means
    more design freedom.

    Args:
        volume_m3:           Body cavity volume (m³)
        current_diameter_mm: Current/nominal soundhole diameter (mm)
        thickness_m:         Plate thickness at soundhole (m)
        k0, gamma:           End-correction constants
        plate_mass_factor:   Plate-air coupling correction
        range_mm:            ± range to explore around current_diameter_mm
        steps:               Number of points in the curve

    Returns:
        List of {"diameter_mm": float, "f_hz": float} dicts
    """
    d_min = max(40.0, current_diameter_mm - range_mm)
    d_max = min(150.0, current_diameter_mm + range_mm)
    step = (d_max - d_min) / (steps - 1)
    curve = []
    for i in range(steps):
        d = d_min + i * step
        r = (d / 2) / 1000.0
        p = PortSpec(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r,
            location="top",
            thickness_m=thickness_m,
        )
        f, _ = compute_helmholtz_multiport(volume_m3, [p], k0, gamma, plate_mass_factor)
        curve.append({"diameter_mm": round(d, 1), "f_hz": round(f, 1)})
    return curve


# ═══════════════════════════════════════════════════════════════════════════════
# TWO-CAVITY ANALYSIS — Complete implementation (Option C analytic upgrade)
# Replaces the approximate 10% empirical repulsion with the exact 2×2
# eigenvalue solution for two coupled Helmholtz resonators.
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class TwoCavityResult:
    """
    Complete two-cavity Helmholtz analysis for Selmer/Maccaferri instruments.

    Physics:
        The Maccaferri internal resonator creates two coupled air cavities.
        The exact coupled-oscillator eigenvalue problem is:

            (ω² - ω₁²)(ω² - ω₂²) = κ⁴

        where ω₁, ω₂ are the UNCOUPLED angular frequencies of each cavity
        and κ is the coupling coefficient:

            κ² = c² × A_ap / (L_eff_ap × √(V_main × V_resonator))

        Analytic solution:
            ω±² = (ω₁² + ω₂²)/2 ± √(((ω₁² - ω₂²)/2)² + κ⁴)

        This is exact for any coupling strength, replacing the 10% empirical
        repulsion approximation in compute_two_cavity_helmholtz().

    Coupling regime:
        κ/(2π) << f_resonances : "Weak" — peaks slightly perturbed from uncoupled
        κ/(2π) ≈ f_resonances  : "Strong" — peaks strongly mixed, wide separation
        κ/(2π) >> f_resonances : "Very strong" — one peak pushed near zero

        Real Maccaferri instruments operate in the strong coupling regime.
        The lower mode is pushed well below both uncoupled frequencies.
        This is intentional — it extends bass response below ~80 Hz.

    Calibration status:
        The κ formula is derived from first principles (no calibration constant).
        It gives the exact eigenfrequencies for two Helmholtz resonators coupled
        through a shared aperture, assuming rigid cavity walls and uniform pressure
        within each cavity. Accuracy degrades for apertures larger than ~30% of
        the smaller cavity's cross-sectional area (non-uniform pressure assumption).
    """
    # Uncoupled resonances (before coupling)
    f_H1_uncoupled_hz: float     # main body resonance if resonator absent
    f_H2_uncoupled_hz: float     # resonator in isolation

    # Coupled normal modes (exact eigenvalue solution)
    f_lower_hz: float            # lower normal mode (predominantly body character)
    f_upper_hz: float            # upper normal mode (predominantly resonator character)
    f_lower_note: str
    f_upper_note: str

    # Coupling characterization
    coupling_hz: float           # κ/(2π) — coupling frequency
    coupling_regime: str         # "weak" | "moderate" | "strong" | "very_strong"
    separation_hz: float         # f_upper - f_lower (audible bandwidth)

    # Volume accounting
    v_main_effective_m3: float   # main cavity after subtracting resonator
    v_resonator_m3: float

    # Design guidance
    design_note: str
    tuning_guidance: List[str]

    def to_dict(self) -> Dict:
        return {
            "f_lower_hz": self.f_lower_hz,
            "f_upper_hz": self.f_upper_hz,
            "f_lower_note": self.f_lower_note,
            "f_upper_note": self.f_upper_note,
            "f_H1_uncoupled_hz": self.f_H1_uncoupled_hz,
            "f_H2_uncoupled_hz": self.f_H2_uncoupled_hz,
            "coupling_hz": self.coupling_hz,
            "coupling_regime": self.coupling_regime,
            "separation_hz": self.separation_hz,
        }


def analyze_two_cavity(
    # Main body
    main_ports: List[PortSpec],
    volume_total_m3: float,
    # Internal resonator
    volume_resonator_m3: float,
    aperture_diameter_mm: float,
    aperture_wall_thickness_mm: float = 5.0,
    # Physics constants
    k0: float = K0,
    gamma: float = GAMMA,
    plate_mass_factor: float = PLATE_MASS_FACTOR,
) -> TwoCavityResult:
    """
    Complete two-cavity analysis for Selmer/Maccaferri instruments.

    Uses the exact 2×2 eigenvalue solution for coupled Helmholtz resonators,
    replacing the previous 10% empirical repulsion approximation.

    Key design insight:
        The internal resonator is STRONGLY coupled to the main body in all
        practical Selmer-style instruments. The lower normal mode is pushed
        well below both uncoupled frequencies — extending bass response to
        70-90 Hz. The upper mode sits above both uncoupled frequencies.
        This broad bass response (spanning ~60-80 Hz from lower to upper mode)
        is the defining acoustic signature of Maccaferri-style instruments.

    Volume accounting:
        V_main_effective = V_total - V_resonator
        (The resonator occupies space that would otherwise be main cavity volume)

    Tuning the resonances:
        Lower mode  ↑ : increase aperture area, decrease resonator volume
        Lower mode  ↓ : decrease aperture area, increase resonator volume
        Upper mode  ↑ : decrease resonator volume (move f_H2 higher)
        Upper mode  ↓ : increase resonator volume (move f_H2 lower)
        Separation  ↑ : increase aperture area (stronger coupling)
        Separation  ↓ : decrease aperture area (weaker coupling)

    Args:
        main_ports:                  Ports from main body to outside (D-hole/oval)
        volume_total_m3:             Total body volume before resonator (m³)
        volume_resonator_m3:         Internal resonator volume (m³)
                                     Typical Maccaferri: 0.003–0.007 m³ (3–7 L)
        aperture_diameter_mm:        Aperture diameter (mm). For non-circular
                                     apertures, use equivalent diameter = 2√(A/π)
        aperture_wall_thickness_mm:  Wall/baffle thickness at aperture (mm)

    Returns:
        TwoCavityResult with both normal mode frequencies and design guidance
    """
    # Volume accounting
    V_main = volume_total_m3 - volume_resonator_m3
    V_main = max(V_main, 0.001)  # floor at 1L

    # Uncoupled f_H1: main body with ports to outside
    f_H1_unc, _ = compute_helmholtz_multiport(
        V_main, main_ports, k0, gamma, plate_mass_factor
    )

    # Aperture geometry
    r_ap = (aperture_diameter_mm / 2.0) / 1000.0
    A_ap = math.pi * r_ap ** 2
    P_ap = 2.0 * math.pi * r_ap
    t_ap = aperture_wall_thickness_mm / 1000.0
    L_ap = compute_port_neck_length(A_ap, P_ap, t_ap, k0, gamma)

    # Uncoupled f_H2: resonator with aperture coupling to main body
    # Treat main body as effectively "outside" for the resonator
    # No PMF for internal resonator (plate compliance irrelevant for internal cavity)
    f_H2_unc = (C_AIR / (2.0 * math.pi)) * math.sqrt(A_ap / (volume_resonator_m3 * L_ap))

    # Exact coupled eigenfrequencies
    f_lower, f_upper, kappa_hz = exact_coupled_eigenfreq(
        f_H1_unc, f_H2_unc, V_main, volume_resonator_m3, A_ap, L_ap
    )

    # Coupling regime classification
    min_f = min(f_H1_unc, f_H2_unc)
    kappa_ratio = kappa_hz / min_f if min_f > 0 else 0
    if kappa_ratio < 0.20:
        regime = "weak"
    elif kappa_ratio < 0.50:
        regime = "moderate"
    elif kappa_ratio < 1.0:
        regime = "strong"
    else:
        regime = "very_strong"

    separation = f_upper - f_lower

    # Design note
    design_note = (
        f"Lower mode {f_lower:.0f} Hz ({_hz_to_note(f_lower)}) · "
        f"Upper mode {f_upper:.0f} Hz ({_hz_to_note(f_upper)}) · "
        f"Separation {separation:.0f} Hz · "
        f"Coupling {regime} (κ = {kappa_hz:.0f} Hz). "
    )
    if regime in ("strong", "very_strong"):
        design_note += (
            f"Strong coupling pushes the lower mode well below both uncoupled "
            f"frequencies ({f_H1_unc:.0f} Hz and {f_H2_unc:.0f} Hz), "
            f"broadening bass response across {separation:.0f} Hz. "
            "This is the characteristic Maccaferri bass extension."
        )
    else:
        design_note += (
            f"Moderate coupling — peaks are near the uncoupled frequencies "
            f"({f_H1_unc:.0f} Hz and {f_H2_unc:.0f} Hz) with slight repulsion. "
            "Increase aperture area for stronger coupling and wider bass spread."
        )

    # Tuning guidance
    tuning = [
        f"Raise lower mode: increase aperture diameter (currently {aperture_diameter_mm:.0f}mm) "
        f"or decrease resonator volume (currently {volume_resonator_m3*1000:.1f}L)",
        f"Lower the lower mode: decrease aperture diameter or increase resonator volume",
        f"Raise upper mode: decrease resonator volume — this moves f_H2 higher",
        f"Widen separation: increase aperture diameter (stronger coupling)",
        f"Narrow separation: decrease aperture diameter (weaker coupling)",
    ]

    return TwoCavityResult(
        f_H1_uncoupled_hz=round(f_H1_unc, 1),
        f_H2_uncoupled_hz=round(f_H2_unc, 1),
        f_lower_hz=round(f_lower, 1),
        f_upper_hz=round(f_upper, 1),
        f_lower_note=_hz_to_note(f_lower),
        f_upper_note=_hz_to_note(f_upper),
        coupling_hz=round(kappa_hz, 1),
        coupling_regime=regime,
        separation_hz=round(separation, 1),
        v_main_effective_m3=round(V_main, 4),
        v_resonator_m3=round(volume_resonator_m3, 4),
        design_note=design_note,
        tuning_guidance=tuning,
    )
