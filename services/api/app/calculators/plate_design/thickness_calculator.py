#!/usr/bin/env python3
"""
thickness_calculator.py — Orthotropic plate thickness and coupled-system analysis.

Implements two core calculators for determining optimal plate thickness when
both top and back are acoustically active:

1. Orthotropic Plate Calculator:
   - Computes plate modal frequencies from E_L, E_C, ρ, h, dimensions
   - Solves for thickness given target frequency
   - Formula: f_mn = (η × π/2) × √[(E_L m²/a⁴ + E_C n²/b⁴) / ρ]

2. 3-Oscillator Coupled Model:
   - Top plate (mass + stiffness)
   - Back plate (mass + stiffness)
   - Air cavity (Helmholtz resonator)
   - Solves eigenvalue problem: det(K - ω²M) = 0
   - Returns three coupled eigenfrequencies

Physical Principles:
    Modal Scaling:     f ∝ h × √(E/ρ)
    Stiffness Index:   SI = E × h³
    Wave Speed:        c = √(E/ρ)
    Helmholtz:         f_H = (c_air / 2π) × √(A_hole / (V × L_eff))

Usage:
    # Simple thickness for target frequency
    python -m tap_tone_pi.design.thickness_calculator \\
        --target-freq 86 --material mahogany --body jumbo

    # Full coupled analysis
    python -m tap_tone_pi.design.thickness_calculator --mode coupled \\
        --body jumbo \\
        --top-EL 12.5 --top-EC 0.8 --top-rho 420 --top-h 2.8 \\
        --back-EL 10.2 --back-EC 0.65 --back-rho 540 --back-h 2.9

References:
    - Gore & Gilet, "Contemporary Acoustic Guitar Design and Build"
    - Fletcher & Rossing, "The Physics of Musical Instruments", Ch. 9-10
    - Caldersmith, "Designing a Guitar Family", 1978
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .calibration import (
    BodyCalibration,
    get_body_calibration,
    get_material_preset,
    list_body_styles,
    list_materials,
    AIR_DENSITY_KG_M3,
    AIR_SPEED_OF_SOUND_M_S,
)


# =============================================================================
# Core Physics Functions
# =============================================================================


def plate_modal_frequency(
    E_L_Pa: float,
    E_C_Pa: float,
    rho: float,
    h: float,
    a: float,
    b: float,
    m: int = 1,
    n: int = 1,
    eta: float = 1.0,
) -> float:
    """
    Compute modal frequency for an orthotropic rectangular plate.

    Uses the approximate formula for simply-supported orthotropic plates,
    modified by geometry factor η for real boundary conditions.

    f_mn = (η × π/2) × √[(E_L × m²/a⁴ + E_C × n²/b⁴) / ρ] × h

    Args:
        E_L_Pa: Longitudinal modulus (Pa)
        E_C_Pa: Cross-grain modulus (Pa)
        rho: Density (kg/m³)
        h: Thickness (m)
        a: Length along grain (m)
        b: Width across grain (m)
        m: Mode number along length (default 1)
        n: Mode number across width (default 1)
        eta: Geometry/boundary factor (default 1.0)

    Returns:
        Modal frequency in Hz

    Physics:
        The plate acts as a 2D resonator. E_L dominates the stiffness for
        modes along the grain, while E_C contributes for cross-grain modes.
        The (1,1) mode is the fundamental "monopole-like" motion.
    """
    if rho <= 0 or h <= 0 or a <= 0 or b <= 0:
        raise ValueError("All geometric and material parameters must be positive")

    # Effective bending stiffness per mode direction
    term_L = E_L_Pa * (m**2) / (a**4)
    term_C = E_C_Pa * (n**2) / (b**4)

    # Combined stiffness
    stiffness_term = (term_L + term_C) / rho

    # Frequency formula
    f = eta * (math.pi / 2.0) * math.sqrt(stiffness_term) * h

    return f


def thickness_for_target_frequency(
    f_target: float,
    E_L_Pa: float,
    E_C_Pa: float,
    rho: float,
    a: float,
    b: float,
    m: int = 1,
    n: int = 1,
    eta: float = 1.0,
) -> float:
    """
    Compute plate thickness required to achieve target modal frequency.

    Inverse of plate_modal_frequency:
    h = f_target / [η × (π/2) × √((E_L m²/a⁴ + E_C n²/b⁴) / ρ)]

    Args:
        f_target: Target frequency (Hz)
        E_L_Pa: Longitudinal modulus (Pa)
        E_C_Pa: Cross-grain modulus (Pa)
        rho: Density (kg/m³)
        a: Length along grain (m)
        b: Width across grain (m)
        m: Mode number along length (default 1)
        n: Mode number across width (default 1)
        eta: Geometry/boundary factor (default 1.0)

    Returns:
        Required thickness in meters
    """
    if f_target <= 0:
        raise ValueError("Target frequency must be positive")

    term_L = E_L_Pa * (m**2) / (a**4)
    term_C = E_C_Pa * (n**2) / (b**4)
    stiffness_term = (term_L + term_C) / rho

    denominator = eta * (math.pi / 2.0) * math.sqrt(stiffness_term)

    if denominator <= 0:
        raise ValueError("Invalid material/geometry combination")

    h = f_target / denominator
    return h


def helmholtz_frequency(
    volume: float,
    hole_area: float,
    L_eff: float,
    c_air: float = AIR_SPEED_OF_SOUND_M_S,
) -> float:
    """
    Compute Helmholtz resonance frequency for a cavity with soundhole.

    f_H = (c / 2π) × √(A / (V × L_eff))

    Args:
        volume: Cavity volume (m³)
        hole_area: Soundhole area (m²)
        L_eff: Effective hole length (m), includes end correction
        c_air: Speed of sound in air (m/s)

    Returns:
        Helmholtz frequency in Hz
    """
    if volume <= 0 or hole_area <= 0 or L_eff <= 0:
        raise ValueError("All parameters must be positive")

    f_H = (c_air / (2.0 * math.pi)) * math.sqrt(hole_area / (volume * L_eff))
    return f_H


def chladni_to_box_frequency(
    f_chladni: float,
    gamma: float,
) -> float:
    """
    Map free-plate Chladni frequency to assembled-box frequency.

    f_box = γ × f_chladni

    The transfer coefficient γ = √(α/β) accounts for:
    - Air loading on the plate
    - Boundary stiffening from glue joints
    - Cavity coupling effects

    Args:
        f_chladni: Free-plate Chladni pattern frequency (Hz)
        gamma: Transfer coefficient (typically 0.7-0.95)

    Returns:
        Predicted box frequency (Hz)
    """
    return gamma * f_chladni


def box_to_chladni_frequency(
    f_box: float,
    gamma: float,
) -> float:
    """
    Inverse mapping: what Chladni frequency gives desired box frequency?

    f_chladni = f_box / γ

    Args:
        f_box: Target assembled-box frequency (Hz)
        gamma: Transfer coefficient

    Returns:
        Required free-plate Chladni frequency (Hz)
    """
    if gamma <= 0:
        raise ValueError("Gamma must be positive")
    return f_box / gamma


# =============================================================================
# 3-Oscillator Coupled Model
# =============================================================================


def coupled_eigenfrequencies(
    # Top plate
    E_L_top: float,  # Pa
    E_C_top: float,  # Pa
    rho_top: float,  # kg/m³
    h_top: float,  # m
    a_top: float,  # m
    b_top: float,  # m
    A_eff_top: float,  # m² - effective piston area
    eta_top: float,  # geometry factor
    gamma_top: float,  # Chladni-to-box transfer
    # Back plate
    E_L_back: float,
    E_C_back: float,
    rho_back: float,
    h_back: float,
    a_back: float,
    b_back: float,
    A_eff_back: float,
    eta_back: float,
    gamma_back: float,
    # Cavity
    volume: float,  # m³
    hole_area: float,  # m²
    L_eff: float,  # m
    # Air properties
    rho_air: float = AIR_DENSITY_KG_M3,
    c_air: float = AIR_SPEED_OF_SOUND_M_S,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    """
    Solve 3-oscillator coupled system for top-air-back interaction.

    The system is modeled as three coupled oscillators:
    - Top plate: mass m_t, stiffness k_t
    - Back plate: mass m_b, stiffness k_b
    - Air cavity: compliance C_a, soundhole inertance M_h

    The eigenvalue problem det(K - ω²M) = 0 yields three frequencies
    corresponding to the three coupled modes.

    Args:
        (see parameter descriptions above)

    Returns:
        Tuple of:
        - eigenfrequencies: Array of 3 frequencies (Hz), sorted ascending
        - eigenvectors: 3x3 array of mode shapes
        - info: Dict with intermediate calculations

    Physics:
        The lowest mode is typically air-dominated (Helmholtz-like).
        The middle mode has top and back moving in phase.
        The highest mode has top and back moving out of phase.
    """
    # Plate modal stiffness (from free-plate fundamental)
    # k = m × (2πf)² where f is the fundamental frequency

    # Top plate
    f_top_free = plate_modal_frequency(
        E_L_top, E_C_top, rho_top, h_top, a_top, b_top, eta=eta_top
    )
    f_top_box = chladni_to_box_frequency(f_top_free, gamma_top)
    m_top = rho_top * h_top * A_eff_top  # Effective mass
    omega_top = 2.0 * math.pi * f_top_box
    k_top = m_top * omega_top**2

    # Back plate
    f_back_free = plate_modal_frequency(
        E_L_back, E_C_back, rho_back, h_back, a_back, b_back, eta=eta_back
    )
    f_back_box = chladni_to_box_frequency(f_back_free, gamma_back)
    m_back = rho_back * h_back * A_eff_back
    omega_back = 2.0 * math.pi * f_back_box
    k_back = m_back * omega_back**2

    # Helmholtz resonator
    f_helmholtz = helmholtz_frequency(volume, hole_area, L_eff, c_air)
    omega_H = 2.0 * math.pi * f_helmholtz

    # Cavity compliance: C_a = V / (ρ₀ × c²)
    C_a = volume / (rho_air * c_air**2)

    # Soundhole inertance: M_h = ρ₀ × L_eff / A_hole
    M_h = rho_air * L_eff / hole_area

    # Coupling coefficients (volume displacement coordinates)
    # α_t = A_eff_top / C_a,  α_b = A_eff_back / C_a
    alpha_t = A_eff_top / C_a if C_a > 0 else 0
    alpha_b = A_eff_back / C_a if C_a > 0 else 0

    # Build stiffness matrix K (3x3)
    # Coordinates: [x_top, x_back, x_air]
    # x represents volume displacement = A × displacement

    K = np.array(
        [
            [k_top + alpha_t * A_eff_top, alpha_t * A_eff_back, alpha_t],
            [alpha_b * A_eff_top, k_back + alpha_b * A_eff_back, alpha_b],
            [A_eff_top / C_a, A_eff_back / C_a, 1.0 / C_a],
        ]
    )

    # Build mass matrix M (3x3)
    M = np.array(
        [
            [m_top, 0, 0],
            [0, m_back, 0],
            [0, 0, M_h],
        ]
    )

    # Solve generalized eigenvalue problem: K v = λ M v
    # where λ = ω²
    try:
        eigenvalues, eigenvectors = np.linalg.eig(np.linalg.inv(M) @ K)
    except np.linalg.LinAlgError:
        # Fallback if singular
        eigenvalues = np.array([omega_top**2, omega_back**2, omega_H**2])
        eigenvectors = np.eye(3)

    # Convert eigenvalues to frequencies
    # Handle potential negative eigenvalues from numerical issues
    omega_squared = np.real(eigenvalues)
    omega_squared = np.clip(omega_squared, 0, None)
    frequencies = np.sqrt(omega_squared) / (2.0 * math.pi)

    # Sort by frequency
    sort_idx = np.argsort(frequencies)
    frequencies = frequencies[sort_idx]
    eigenvectors = eigenvectors[:, sort_idx]

    # Info dict for debugging/analysis
    info = {
        "f_top_free_Hz": f_top_free,
        "f_top_box_Hz": f_top_box,
        "f_back_free_Hz": f_back_free,
        "f_back_box_Hz": f_back_box,
        "f_helmholtz_Hz": f_helmholtz,
        "m_top_kg": m_top,
        "m_back_kg": m_back,
        "k_top_N_m": k_top,
        "k_back_N_m": k_back,
        "C_a_m3_Pa": C_a,
        "M_h_kg_m4": M_h,
    }

    return frequencies, eigenvectors, info


# =============================================================================
# Result Data Classes
# =============================================================================


@dataclass
class PlateThicknessResult:
    """Result of single-plate thickness analysis."""

    # Input summary
    material: str
    E_L_GPa: float
    E_C_GPa: float
    density_kg_m3: float
    length_mm: float
    width_mm: float

    # Current state
    current_h_mm: Optional[float]
    current_f_Hz: Optional[float]

    # Target
    target_f_Hz: float

    # Computed
    recommended_h_mm: float
    delta_h_mm: Optional[float]  # Remove this much (positive) or add (negative)

    # Diagnostics
    wave_speed_L_m_s: float
    wave_speed_C_m_s: float
    R_anis: float

    # Warnings
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        result = {}
        for k, v in d.items():
            if v is None:
                continue
            if isinstance(v, list) and len(v) == 0:
                continue
            result[k] = v
        return result


@dataclass
class CoupledSystemResult:
    """Result of 3-oscillator coupled system analysis."""

    # Body style
    body_style: str

    # Eigenfrequencies (Hz)
    f1_Hz: float  # Lowest (air-dominated)
    f2_Hz: float  # Middle (in-phase)
    f3_Hz: float  # Highest (out-of-phase)

    # Mode descriptions
    mode1_description: str
    mode2_description: str
    mode3_description: str

    # Target comparison
    target_monopole_Hz: Optional[float]
    f2_vs_target_Hz: Optional[float]

    # Component frequencies (uncoupled)
    f_top_box_Hz: float
    f_back_box_Hz: float
    f_helmholtz_Hz: float

    # Plate details
    top_h_mm: float
    back_h_mm: float

    # Recommendations
    recommendation: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        result = {}
        for k, v in d.items():
            if v is None:
                continue
            if isinstance(v, list) and len(v) == 0:
                continue
            result[k] = v
        return result


# =============================================================================
# High-Level Analysis Functions
# =============================================================================


def analyze_plate(
    E_L_GPa: float,
    E_C_GPa: float,
    density_kg_m3: float,
    length_mm: float,
    width_mm: float,
    target_f_Hz: float,
    current_h_mm: Optional[float] = None,
    eta: float = 1.0,
    material_name: str = "unknown",
) -> PlateThicknessResult:
    """
    Analyze plate and recommend thickness for target frequency.

    Args:
        E_L_GPa: Longitudinal modulus (GPa)
        E_C_GPa: Cross-grain modulus (GPa)
        density_kg_m3: Density (kg/m³)
        length_mm: Plate length along grain (mm)
        width_mm: Plate width across grain (mm)
        target_f_Hz: Target modal frequency (Hz)
        current_h_mm: Current thickness (mm), if known
        eta: Geometry factor (default 1.0)
        material_name: Material name for reporting

    Returns:
        PlateThicknessResult with recommendations
    """
    warnings = []

    # Convert to SI
    E_L_Pa = E_L_GPa * 1e9
    E_C_Pa = E_C_GPa * 1e9
    a_m = length_mm / 1000.0
    b_m = width_mm / 1000.0

    # Orthotropic ratio
    R_anis = E_L_GPa / E_C_GPa if E_C_GPa > 0 else float("inf")

    # Wave speeds
    c_L = math.sqrt(E_L_Pa / density_kg_m3)
    c_C = math.sqrt(E_C_Pa / density_kg_m3)

    # Compute recommended thickness
    h_target_m = thickness_for_target_frequency(
        target_f_Hz, E_L_Pa, E_C_Pa, density_kg_m3, a_m, b_m, eta=eta
    )
    h_target_mm = h_target_m * 1000.0

    # Current frequency if thickness given
    current_f = None
    delta_h = None
    if current_h_mm is not None:
        current_f = plate_modal_frequency(
            E_L_Pa, E_C_Pa, density_kg_m3, current_h_mm / 1000.0, a_m, b_m, eta=eta
        )
        delta_h = current_h_mm - h_target_mm

        if delta_h < 0:
            warnings.append(
                f"Current plate ({current_h_mm:.2f}mm) is thinner than target "
                f"({h_target_mm:.2f}mm). Need thicker stock."
            )
        elif delta_h > current_h_mm * 0.4:
            warnings.append(
                f"Removing {delta_h:.2f}mm ({100 * delta_h / current_h_mm:.0f}% of thickness) "
                "is aggressive. Consider a stiffer billet."
            )

    # Sanity checks
    if R_anis < 8:
        warnings.append(f"Low orthotropic ratio ({R_anis:.1f}). Check for runout.")
    elif R_anis > 25:
        warnings.append(f"High orthotropic ratio ({R_anis:.1f}). Verify measurements.")

    if h_target_mm < 1.5:
        warnings.append(f"Target thickness ({h_target_mm:.2f}mm) is very thin.")
    elif h_target_mm > 5.0:
        warnings.append(f"Target thickness ({h_target_mm:.2f}mm) is unusually thick.")

    return PlateThicknessResult(
        material=material_name,
        E_L_GPa=round(E_L_GPa, 3),
        E_C_GPa=round(E_C_GPa, 3),
        density_kg_m3=round(density_kg_m3, 1),
        length_mm=round(length_mm, 1),
        width_mm=round(width_mm, 1),
        current_h_mm=round(current_h_mm, 3) if current_h_mm else None,
        current_f_Hz=round(current_f, 1) if current_f else None,
        target_f_Hz=round(target_f_Hz, 1),
        recommended_h_mm=round(h_target_mm, 3),
        delta_h_mm=round(delta_h, 3) if delta_h else None,
        wave_speed_L_m_s=round(c_L, 0),
        wave_speed_C_m_s=round(c_C, 0),
        R_anis=round(R_anis, 2),
        warnings=warnings,
    )


def analyze_coupled_system(
    body: BodyCalibration,
    # Top plate
    top_E_L_GPa: float,
    top_E_C_GPa: float,
    top_rho: float,
    top_h_mm: float,
    # Back plate
    back_E_L_GPa: float,
    back_E_C_GPa: float,
    back_rho: float,
    back_h_mm: float,
    # Optional overrides
    target_monopole_Hz: Optional[float] = None,
) -> CoupledSystemResult:
    """
    Analyze coupled top-air-back system.

    Args:
        body: Body calibration parameters
        top_*: Top plate properties (GPa, kg/m³, mm)
        back_*: Back plate properties
        target_monopole_Hz: Target frequency for monopole-like mode

    Returns:
        CoupledSystemResult with eigenfrequencies and recommendations
    """
    warnings = []

    # Convert to SI
    top_E_L_Pa = top_E_L_GPa * 1e9
    top_E_C_Pa = top_E_C_GPa * 1e9
    top_h_m = top_h_mm / 1000.0

    back_E_L_Pa = back_E_L_GPa * 1e9
    back_E_C_Pa = back_E_C_GPa * 1e9
    back_h_m = back_h_mm / 1000.0

    # Solve coupled system
    frequencies, eigenvectors, info = coupled_eigenfrequencies(
        # Top
        E_L_top=top_E_L_Pa,
        E_C_top=top_E_C_Pa,
        rho_top=top_rho,
        h_top=top_h_m,
        a_top=body.top_a_m,
        b_top=body.top_b_m,
        A_eff_top=body.top_effective_area_m2,
        eta_top=body.eta_top,
        gamma_top=body.gamma_top,
        # Back
        E_L_back=back_E_L_Pa,
        E_C_back=back_E_C_Pa,
        rho_back=back_rho,
        h_back=back_h_m,
        a_back=body.back_a_m,
        b_back=body.back_b_m,
        A_eff_back=body.back_effective_area_m2,
        eta_back=body.eta_back,
        gamma_back=body.gamma_back,
        # Cavity
        volume=body.volume_m3,
        hole_area=body.soundhole_area_m2,
        L_eff=body.soundhole_L_eff_m,
    )

    f1, f2, f3 = frequencies

    # Mode descriptions based on typical behavior
    mode1_desc = "Air mode (Helmholtz-like)"
    mode2_desc = "Coupled mode (top+back in-phase)"
    mode3_desc = "Coupled mode (top+back out-of-phase)"

    # Target comparison
    target = target_monopole_Hz or body.f_monopole_target
    f2_vs_target = f2 - target if target else None

    # Generate recommendation
    if f2_vs_target is not None:
        if abs(f2_vs_target) < 3:
            recommendation = (
                f"Coupled mode ({f2:.1f} Hz) is on target ({target:.1f} Hz)."
            )
        elif f2_vs_target > 0:
            recommendation = (
                f"Coupled mode ({f2:.1f} Hz) is {f2_vs_target:.1f} Hz HIGH. "
                "Consider thinning plates slightly."
            )
        else:
            recommendation = (
                f"Coupled mode ({f2:.1f} Hz) is {-f2_vs_target:.1f} Hz LOW. "
                "Plates may be too thin or material too soft."
            )
    else:
        recommendation = "No target specified. Review eigenfrequencies."

    # Warnings
    if f1 < 70:
        warnings.append(f"Air mode ({f1:.1f} Hz) is quite low. Check cavity volume.")
    if f1 > f2 * 0.95:
        warnings.append(
            "Air mode very close to coupled mode. Strong interaction expected."
        )

    return CoupledSystemResult(
        body_style=body.style.value,
        f1_Hz=round(f1, 1),
        f2_Hz=round(f2, 1),
        f3_Hz=round(f3, 1),
        mode1_description=mode1_desc,
        mode2_description=mode2_desc,
        mode3_description=mode3_desc,
        target_monopole_Hz=target,
        f2_vs_target_Hz=round(f2_vs_target, 1) if f2_vs_target else None,
        f_top_box_Hz=round(info["f_top_box_Hz"], 1),
        f_back_box_Hz=round(info["f_back_box_Hz"], 1),
        f_helmholtz_Hz=round(info["f_helmholtz_Hz"], 1),
        top_h_mm=round(top_h_mm, 2),
        back_h_mm=round(back_h_mm, 2),
        recommendation=recommendation,
        warnings=warnings,
    )


# =============================================================================
# Report Formatting
# =============================================================================


def format_plate_report(result: PlateThicknessResult) -> str:
    """Format plate analysis as text report."""
    lines = []
    lines.append("=" * 65)
    lines.append("Plate Thickness Analysis")
    lines.append("=" * 65)

    lines.append(f"\nMaterial: {result.material}")
    lines.append(f"  E_L        : {result.E_L_GPa:.3f} GPa")
    lines.append(f"  E_C        : {result.E_C_GPa:.3f} GPa")
    lines.append(f"  E_L/E_C    : {result.R_anis:.2f}")
    lines.append(f"  Density    : {result.density_kg_m3:.1f} kg/m³")
    lines.append(f"  Wave c_L   : {result.wave_speed_L_m_s:.0f} m/s")
    lines.append(f"  Wave c_C   : {result.wave_speed_C_m_s:.0f} m/s")

    lines.append("\nGeometry:")
    lines.append(f"  Length     : {result.length_mm:.1f} mm (along grain)")
    lines.append(f"  Width      : {result.width_mm:.1f} mm (across grain)")

    if result.current_h_mm:
        lines.append("\nCurrent State:")
        lines.append(f"  Thickness  : {result.current_h_mm:.3f} mm")
        lines.append(f"  Frequency  : {result.current_f_Hz:.1f} Hz")

    lines.append("\nTarget:")
    lines.append(f"  Frequency  : {result.target_f_Hz:.1f} Hz")
    lines.append(f"  Thickness  : {result.recommended_h_mm:.3f} mm")

    if result.delta_h_mm is not None:
        if result.delta_h_mm > 0:
            lines.append(f"\n  >> Remove {result.delta_h_mm:.3f} mm")
        elif result.delta_h_mm < 0:
            lines.append(f"\n  >> Need {-result.delta_h_mm:.3f} mm more material")
        else:
            lines.append("\n  >> Already at target thickness")

    if result.warnings:
        lines.append("\nWarnings:")
        for w in result.warnings:
            lines.append(f"  * {w}")

    lines.append("")
    return "\n".join(lines)


def format_coupled_report(result: CoupledSystemResult) -> str:
    """Format coupled system analysis as text report."""
    lines = []
    lines.append("=" * 65)
    lines.append("3-Oscillator Coupled System Analysis")
    lines.append("=" * 65)

    lines.append(f"\nBody Style: {result.body_style}")

    lines.append("\nPlate Thicknesses:")
    lines.append(f"  Top        : {result.top_h_mm:.2f} mm")
    lines.append(f"  Back       : {result.back_h_mm:.2f} mm")

    lines.append("\nUncoupled Component Frequencies:")
    lines.append(f"  Top (in box)    : {result.f_top_box_Hz:.1f} Hz")
    lines.append(f"  Back (in box)   : {result.f_back_box_Hz:.1f} Hz")
    lines.append(f"  Helmholtz       : {result.f_helmholtz_Hz:.1f} Hz")

    lines.append("\nCoupled Eigenfrequencies:")
    lines.append(f"  f1 = {result.f1_Hz:6.1f} Hz  -  {result.mode1_description}")
    lines.append(f"  f2 = {result.f2_Hz:6.1f} Hz  -  {result.mode2_description}")
    lines.append(f"  f3 = {result.f3_Hz:6.1f} Hz  -  {result.mode3_description}")

    if result.target_monopole_Hz:
        lines.append(
            f"\nTarget: {result.target_monopole_Hz:.1f} Hz (monopole-like mode)"
        )
        if result.f2_vs_target_Hz is not None:
            sign = "+" if result.f2_vs_target_Hz > 0 else ""
            lines.append(f"  f2 vs target: {sign}{result.f2_vs_target_Hz:.1f} Hz")

    lines.append(f"\n{result.recommendation}")

    if result.warnings:
        lines.append("\nWarnings:")
        for w in result.warnings:
            lines.append(f"  * {w}")

    lines.append("")
    return "\n".join(lines)


# =============================================================================
# CLI Interface
# =============================================================================


# =============================================================================
# CLI Helpers — extracted from main() for complexity reduction
# =============================================================================


def _build_argument_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser for the thickness calculator CLI."""
    ap = argparse.ArgumentParser(
        description="Plate thickness and coupled-system calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple thickness calculation with material preset
  python -m tap_tone_pi.design.thickness_calculator \\
      --target-freq 86 --material mahogany --length 559 --width 241

  # With current thickness (how much to remove)
  python -m tap_tone_pi.design.thickness_calculator \\
      --target-freq 86 --EL 10.2 --EC 0.65 --rho 540 \\
      --length 559 --width 241 --current-h 3.5

  # Full 3-oscillator coupled analysis
  python -m tap_tone_pi.design.thickness_calculator --mode coupled \\
      --body jumbo \\
      --top-EL 12.5 --top-EC 0.8 --top-rho 420 --top-h 2.8 \\
      --back-EL 10.2 --back-EC 0.65 --back-rho 540 --back-h 2.9

  # List available presets
  python -m tap_tone_pi.design.thickness_calculator --list-materials
  python -m tap_tone_pi.design.thickness_calculator --list-bodies
""",
    )

    # Mode
    ap.add_argument(
        "--mode",
        choices=["plate", "coupled"],
        default="plate",
        help="Analysis mode: 'plate' (single plate) or 'coupled' (3-oscillator)",
    )

    # List options
    ap.add_argument(
        "--list-materials", action="store_true", help="List material presets"
    )
    ap.add_argument(
        "--list-bodies", action="store_true", help="List body style presets"
    )

    # Plate mode: material
    ap.add_argument("--material", type=str, help="Material preset name")
    ap.add_argument("--EL", type=float, help="E_L in GPa (overrides preset)")
    ap.add_argument("--EC", type=float, help="E_C in GPa (overrides preset)")
    ap.add_argument("--rho", type=float, help="Density in kg/m³ (overrides preset)")

    # Plate mode: geometry
    ap.add_argument("--length", type=float, help="Length along grain (mm)")
    ap.add_argument("--width", type=float, help="Width across grain (mm)")
    ap.add_argument("--current-h", type=float, help="Current thickness (mm)")

    # Plate mode: target
    ap.add_argument("--target-freq", type=float, help="Target frequency (Hz)")
    ap.add_argument(
        "--eta", type=float, default=1.0, help="Geometry factor (default 1.0)"
    )

    # Coupled mode: body
    ap.add_argument("--body", type=str, help="Body style preset")

    # Coupled mode: top plate
    ap.add_argument("--top-EL", type=float, help="Top E_L (GPa)")
    ap.add_argument("--top-EC", type=float, help="Top E_C (GPa)")
    ap.add_argument("--top-rho", type=float, help="Top density (kg/m³)")
    ap.add_argument("--top-h", type=float, help="Top thickness (mm)")
    ap.add_argument("--top-material", type=str, help="Top material preset")

    # Coupled mode: back plate
    ap.add_argument("--back-EL", type=float, help="Back E_L (GPa)")
    ap.add_argument("--back-EC", type=float, help="Back E_C (GPa)")
    ap.add_argument("--back-rho", type=float, help="Back density (kg/m³)")
    ap.add_argument("--back-h", type=float, help="Back thickness (mm)")
    ap.add_argument("--back-material", type=str, help="Back material preset")

    # Output
    ap.add_argument("--json", type=str, help="Output JSON file path")
    ap.add_argument("--quiet", action="store_true", help="Suppress console output")

    return ap


def _print_material_presets() -> None:
    """Print available material presets to stdout."""
    print("\nAvailable Material Presets:")
    print("=" * 65)
    for mat in list_materials():
        print(f"\n{mat['name']} ({mat['species']}):")
        print(f"  E_L: {mat['E_L_GPa']:.1f} GPa, E_C: {mat['E_C_GPa']:.2f} GPa")
        print(
            f"  Density: {mat['density_kg_m3']:.0f} kg/m³, R_anis: {mat['R_anis']:.1f}"
        )
        print(f"  Use: {mat['typical_use']}")
        if mat["notes"]:
            print(f"  Notes: {mat['notes']}")
    print()


def _print_body_presets() -> None:
    """Print available body style presets to stdout."""
    print("\nAvailable Body Styles:")
    print("=" * 65)
    for body in list_body_styles():
        print(f"\n{body['style']}:")
        print(f"  {body['description']}")
        print(f"  Volume: {body['volume_liters']:.1f} L")
        print(f"  Target monopole: {body['f_monopole_target']:.0f} Hz")
        if body["notes"]:
            print(f"  Notes: {body['notes']}")
    print()


def _resolve_material_properties(
    ap: argparse.ArgumentParser,
    args: argparse.Namespace,
    prefix: str = "",
) -> Tuple[float, float, float]:
    """Resolve E_L, E_C, rho from CLI args + optional preset.

    Args:
        ap: ArgumentParser (for error messages)
        args: Parsed namespace
        prefix: "" for plate mode, "top_" or "back_" for coupled mode

    Returns:
        (E_L, E_C, rho) in GPa, GPa, kg/m³
    """
    material_key = f"{prefix}material" if prefix else "material"
    EL_key = f"{prefix}EL" if prefix else "EL"
    EC_key = f"{prefix}EC" if prefix else "EC"
    rho_key = f"{prefix}rho" if prefix else "rho"

    material_name = getattr(args, material_key, None)
    E_L = getattr(args, EL_key, None)
    E_C = getattr(args, EC_key, None)
    rho = getattr(args, rho_key, None)

    if material_name:
        mat = get_material_preset(material_name)
        if not mat:
            ap.error(f"Unknown material: {material_name}")
        E_L = E_L or mat.E_L_GPa
        E_C = E_C or mat.E_C_GPa
        rho = rho or mat.density_kg_m3

    if not all([E_L, E_C, rho]):
        label = prefix.rstrip("_").title() + " " if prefix else ""
        ap.error(
            f"{label}Material properties required: "
            f"--{prefix.replace('_', '-')}EL, --{prefix.replace('_', '-')}EC, "
            f"--{prefix.replace('_', '-')}rho (or --{prefix.replace('_', '-')}material)"
        )

    return E_L, E_C, rho  # type: ignore[return-value]


def _run_coupled_mode(
    ap: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> Any:
    """Execute coupled 3-oscillator analysis from CLI args.

    Returns:
        Result object from analyze_coupled_system.
    """
    if not args.body:
        ap.error("--body is required for coupled mode")

    body = get_body_calibration(args.body)
    if not body:
        ap.error(f"Unknown body style: {args.body}")

    top_EL, top_EC, top_rho = _resolve_material_properties(ap, args, prefix="top_")

    if not args.top_h:
        ap.error("Top plate thickness required: --top-h")

    back_EL, back_EC, back_rho = _resolve_material_properties(ap, args, prefix="back_")

    if not args.back_h:
        ap.error("Back plate thickness required: --back-h")

    result = analyze_coupled_system(
        body=body,
        top_E_L_GPa=top_EL,
        top_E_C_GPa=top_EC,
        top_rho=top_rho,
        top_h_mm=args.top_h,
        back_E_L_GPa=back_EL,
        back_E_C_GPa=back_EC,
        back_rho=back_rho,
        back_h_mm=args.back_h,
        target_monopole_Hz=args.target_freq,
    )

    if not args.quiet:
        print(format_coupled_report(result))

    return result


def _run_plate_mode(
    ap: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> Any:
    """Execute single-plate analysis from CLI args.

    Returns:
        Result object from analyze_plate.
    """
    E_L, E_C, rho = _resolve_material_properties(ap, args)

    if not args.length or not args.width:
        ap.error("Geometry required: --length, --width")

    if not args.target_freq:
        ap.error("Target frequency required: --target-freq")

    result = analyze_plate(
        E_L_GPa=E_L,
        E_C_GPa=E_C,
        density_kg_m3=rho,
        length_mm=args.length,
        width_mm=args.width,
        target_f_Hz=args.target_freq,
        current_h_mm=args.current_h,
        eta=args.eta,
        material_name=getattr(args, "material", None) or "custom",
    )

    if not args.quiet:
        print(format_plate_report(result))

    return result


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """CLI entry point."""
    ap = _build_argument_parser()
    args = ap.parse_args()

    # List modes
    if args.list_materials:
        _print_material_presets()
        return

    if args.list_bodies:
        _print_body_presets()
        return

    # Run analysis
    if args.mode == "coupled":
        result = _run_coupled_mode(ap, args)
    else:
        result = _run_plate_mode(ap, args)

    # JSON output
    if args.json:
        out_path = Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
        if not args.quiet:
            print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
