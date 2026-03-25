#!/usr/bin/env python3
"""
coupled_2osc.py - 2-Oscillator Coupled Model (Top + Air, Rigid Back).

Use this model when the back plate is designed to be acoustically inactive:
- Back stiffness index >> top stiffness index
- Back (1,1) frequency >> highest coupled mode frequency
- Examples: laminate backs, heavily braced backs, archtop backs

Physics:
    The system is modeled as two coupled oscillators:
    - Top plate: mass m_t, stiffness k_t (from plate bending)
    - Air cavity: compliance C_a, soundhole inertance M_h

    Equations of motion:
        m_t * x_t'' + k_t * x_t + (1/C_a) * (x_t - x_a) = 0
        M_h * x_a'' + (1/C_a) * (x_a - x_t) = 0

    Closed-form eigenvalue solution:
        w^2 = 0.5 * [(w_t^2 + w_H^2 + w_c^2) -/+ sqrt(discriminant)]
    where:
        w_t = sqrt(k_t/m_t)         -- uncoupled top
        w_H = sqrt(1/(M_h * C_a))   -- Helmholtz
        w_c^2 = A_eff^2 / (m_t * C_a)  -- coupling strength

    The lower mode is air-dominated (Helmholtz-like).
    The upper mode is top-dominated (monopole-like).
    Without back participation, there is no third "out-of-phase" mode.

References:
    - Fletcher & Rossing, "The Physics of Musical Instruments", Ch. 9-10
    - Caldersmith, "Designing a Guitar Family", 1978
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .calibration import (
    BodyCalibration,
    AIR_DENSITY_KG_M3,
    AIR_SPEED_OF_SOUND_M_S,
)
from .thickness_calculator import (
    plate_modal_frequency,
    chladni_to_box_frequency,
    helmholtz_frequency,
)


# =============================================================================
# 2-Oscillator Coupled Model
# =============================================================================


def coupled_2osc_eigenfrequencies(
    # Top plate
    E_L_top: float,  # Pa
    E_C_top: float,  # Pa
    rho_top: float,  # kg/m3
    h_top: float,  # m
    a_top: float,  # m
    b_top: float,  # m
    A_eff_top: float,  # m2 - effective piston area
    eta_top: float,  # geometry factor
    gamma_top: float,  # Chladni-to-box transfer
    # Cavity (back treated as rigid boundary)
    volume: float,  # m3
    hole_area: float,  # m2
    L_eff: float,  # m
    # Air properties
    rho_air: float = AIR_DENSITY_KG_M3,
    c_air: float = AIR_SPEED_OF_SOUND_M_S,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    """
    Solve 2-oscillator coupled system for top-air interaction (rigid back).

    Args:
        E_L_top: Top longitudinal modulus (Pa)
        E_C_top: Top cross-grain modulus (Pa)
        rho_top: Top density (kg/m3)
        h_top: Top thickness (m)
        a_top: Top length along grain (m)
        b_top: Top width across grain (m)
        A_eff_top: Effective piston area (m2)
        eta_top: Geometry factor for modal frequency
        gamma_top: Chladni-to-box transfer coefficient
        volume: Cavity volume (m3)
        hole_area: Soundhole area (m2)
        L_eff: Effective soundhole length with end correction (m)
        rho_air: Air density (kg/m3)
        c_air: Speed of sound in air (m/s)

    Returns:
        Tuple of:
        - eigenfrequencies: Array of 2 frequencies (Hz), sorted ascending
        - eigenvectors: 2x2 array of mode shapes [top, air]
        - info: Dict with intermediate calculations
    """
    # Top plate modal frequency and effective parameters
    f_top_free = plate_modal_frequency(
        E_L_top, E_C_top, rho_top, h_top, a_top, b_top, eta=eta_top
    )
    f_top_box = chladni_to_box_frequency(f_top_free, gamma_top)
    m_top = rho_top * h_top * A_eff_top
    omega_top = 2.0 * math.pi * f_top_box
    k_top = m_top * omega_top**2

    # Helmholtz resonator parameters
    f_helmholtz = helmholtz_frequency(volume, hole_area, L_eff, c_air)

    # Cavity compliance: C_a = V / (rho_0 * c^2)
    C_a = volume / (rho_air * c_air**2)

    # Soundhole inertance: M_h = rho_0 * L_eff / A_hole
    M_h = rho_air * L_eff / hole_area

    # Angular frequencies squared
    omega_t_sq = omega_top**2
    omega_H_sq = 1.0 / (M_h * C_a)

    # Coupling strength: w_c^2 = A_eff^2 / (m_t * C_a)
    omega_c_sq = (A_eff_top**2) / (m_top * C_a)

    # Closed-form eigenvalue solution
    sum_omega_sq = omega_t_sq + omega_H_sq + omega_c_sq
    discriminant = sum_omega_sq**2 - 4.0 * omega_t_sq * omega_H_sq

    if discriminant < 0:
        # Shouldn't happen for physical systems, but handle gracefully
        omega1_sq = omega_H_sq
        omega2_sq = omega_t_sq
    else:
        omega1_sq = 0.5 * (sum_omega_sq - math.sqrt(discriminant))
        omega2_sq = 0.5 * (sum_omega_sq + math.sqrt(discriminant))

    # Ensure non-negative
    omega1_sq = max(0.0, omega1_sq)
    omega2_sq = max(0.0, omega2_sq)

    # Convert to Hz
    f1 = math.sqrt(omega1_sq) / (2.0 * math.pi)
    f2 = math.sqrt(omega2_sq) / (2.0 * math.pi)

    frequencies = np.array([f1, f2])

    # Mode shapes (approximate participation ratios)
    # x_t / x_a ratio from the equations
    if omega1_sq > 0 and omega_c_sq > 0:
        ratio1 = (omega1_sq - omega_H_sq) / omega_c_sq
    else:
        ratio1 = 0.0
    if omega2_sq > 0 and omega_c_sq > 0:
        ratio2 = (omega2_sq - omega_H_sq) / omega_c_sq
    else:
        ratio2 = 1.0

    # Normalize eigenvectors
    norm1 = math.sqrt(1 + ratio1**2) if ratio1 != 0 else 1.0
    norm2 = math.sqrt(1 + ratio2**2) if ratio2 != 0 else 1.0
    eigenvectors = np.array(
        [
            [ratio1 / norm1, 1.0 / norm1],  # Mode 1: [top, air]
            [ratio2 / norm2, 1.0 / norm2],  # Mode 2: [top, air]
        ]
    ).T

    # Coupling frequency (diagnostic)
    f_coupling = math.sqrt(omega_c_sq) / (2.0 * math.pi)

    # Info dict
    info = {
        "f_top_free_Hz": f_top_free,
        "f_top_box_Hz": f_top_box,
        "f_helmholtz_Hz": f_helmholtz,
        "m_top_kg": m_top,
        "k_top_N_m": k_top,
        "C_a_m3_Pa": C_a,
        "M_h_kg_m4": M_h,
        "f_coupling_Hz": f_coupling,
        "omega_t_rad_s": math.sqrt(omega_t_sq),
        "omega_H_rad_s": math.sqrt(omega_H_sq),
    }

    return frequencies, eigenvectors, info


# =============================================================================
# Back Activity Assessment
# =============================================================================


def back_activity_ratio(
    E_L_back: float,  # Pa
    E_C_back: float,  # Pa
    rho_back: float,  # kg/m3
    h_back: float,  # m
    a_back: float,  # m
    b_back: float,  # m
    f_coupled_max: float,  # Hz - highest coupled mode frequency
    eta_back: float = 1.0,
) -> Tuple[float, str]:
    """
    Compute back activity ratio to determine if 2-osc or 3-osc model applies.

    The ratio compares back (1,1) frequency to highest coupled mode:
        R = f_back / f_coupled_max

    Interpretation:
        R > 1.5  -> Back is effectively rigid, use 2-oscillator model
        R < 1.5  -> Back participates, use 3-oscillator model
        R < 1.0  -> Back strongly participates (lower than coupled modes)

    Args:
        E_L_back: Back longitudinal modulus (Pa)
        E_C_back: Back cross-grain modulus (Pa)
        rho_back: Back density (kg/m3)
        h_back: Back thickness (m)
        a_back: Back length (m)
        b_back: Back width (m)
        f_coupled_max: Highest coupled mode frequency (Hz)
        eta_back: Geometry factor

    Returns:
        Tuple of:
        - ratio: f_back / f_coupled_max
        - recommendation: "2-oscillator", "3-oscillator", or "strongly-coupled"
    """
    f_back = plate_modal_frequency(
        E_L_back, E_C_back, rho_back, h_back, a_back, b_back, eta=eta_back
    )

    ratio = f_back / f_coupled_max if f_coupled_max > 0 else float("inf")

    if ratio > 1.5:
        recommendation = "2-oscillator"
    elif ratio > 1.0:
        recommendation = "3-oscillator"
    else:
        recommendation = "strongly-coupled"

    return ratio, recommendation


def minimum_back_thickness_for_rigid(
    E_L_back: float,  # Pa
    E_C_back: float,  # Pa
    rho_back: float,  # kg/m3
    a_back: float,  # m
    b_back: float,  # m
    f_coupled_max: float,  # Hz
    safety_factor: float = 1.2,
    rigidity_ratio: float = 1.5,
    eta_back: float = 1.0,
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate minimum back thickness for effectively rigid behavior.

    Args:
        E_L_back: Back longitudinal modulus (Pa)
        E_C_back: Back cross-grain modulus (Pa)
        rho_back: Back density (kg/m3)
        a_back: Back length (m)
        b_back: Back width (m)
        f_coupled_max: Highest coupled mode to stay above (Hz)
        safety_factor: Additional margin (default 1.2)
        rigidity_ratio: Target f_back/f_coupled ratio (default 1.5)
        eta_back: Geometry factor

    Returns:
        Tuple of:
        - h_min_m: Minimum thickness in meters
        - info: Dict with diagnostic values
    """
    # Target back frequency
    f_target = f_coupled_max * rigidity_ratio * safety_factor

    # Invert plate_modal_frequency to get thickness
    # f = eta * (pi/2) * sqrt[(E_L/a^4 + E_C/b^4) / rho] * h
    # h = f / [eta * (pi/2) * sqrt[(E_L/a^4 + E_C/b^4) / rho]]

    term_L = E_L_back / (a_back**4)
    term_C = E_C_back / (b_back**4)
    stiffness_term = (term_L + term_C) / rho_back
    denominator = eta_back * (math.pi / 2.0) * math.sqrt(stiffness_term)

    h_min = f_target / denominator

    info = {
        "f_target_Hz": f_target,
        "f_coupled_max_Hz": f_coupled_max,
        "safety_factor": safety_factor,
        "rigidity_ratio": rigidity_ratio,
        "h_min_mm": h_min * 1000,
    }

    return h_min, info


# =============================================================================
# Result Data Class
# =============================================================================


@dataclass
class Coupled2OscResult:
    """Result of 2-oscillator coupled system analysis (rigid back)."""

    # Body style
    body_style: str

    # Eigenfrequencies (Hz)
    f1_Hz: float  # Lower (air-dominated)
    f2_Hz: float  # Upper (top-dominated)

    # Mode descriptions
    mode1_description: str
    mode2_description: str

    # Target comparison
    target_monopole_Hz: Optional[float]
    f2_vs_target_Hz: Optional[float]

    # Component frequencies (uncoupled)
    f_top_box_Hz: float
    f_helmholtz_Hz: float
    f_coupling_Hz: float

    # Plate details
    top_h_mm: float

    # Back assessment (why 2-osc is appropriate)
    back_activity_ratio: Optional[float]
    back_model_recommendation: Optional[str]

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
# High-Level Analysis Function
# =============================================================================


def analyze_coupled_2osc(
    body: BodyCalibration,
    # Top plate
    top_E_L_GPa: float,
    top_E_C_GPa: float,
    top_rho: float,
    top_h_mm: float,
    # Optional: back assessment
    back_E_L_GPa: Optional[float] = None,
    back_E_C_GPa: Optional[float] = None,
    back_rho: Optional[float] = None,
    back_h_mm: Optional[float] = None,
    # Target
    target_monopole_Hz: Optional[float] = None,
) -> Coupled2OscResult:
    """
    Analyze coupled top-air system with rigid back assumption.

    Args:
        body: Body calibration parameters
        top_*: Top plate properties (GPa, kg/m3, mm)
        back_*: Optional back plate properties for activity ratio check
        target_monopole_Hz: Target frequency for top-dominated mode

    Returns:
        Coupled2OscResult with eigenfrequencies and recommendations
    """
    warnings: List[str] = []

    # Convert to SI
    top_E_L_Pa = top_E_L_GPa * 1e9
    top_E_C_Pa = top_E_C_GPa * 1e9
    top_h_m = top_h_mm / 1000.0

    # Solve 2-oscillator system
    frequencies, eigenvectors, info = coupled_2osc_eigenfrequencies(
        E_L_top=top_E_L_Pa,
        E_C_top=top_E_C_Pa,
        rho_top=top_rho,
        h_top=top_h_m,
        a_top=body.top_a_m,
        b_top=body.top_b_m,
        A_eff_top=body.top_effective_area_m2,
        eta_top=body.eta_top,
        gamma_top=body.gamma_top,
        volume=body.volume_m3,
        hole_area=body.soundhole_area_m2,
        L_eff=body.soundhole_L_eff_m,
    )

    f1, f2 = frequencies

    # Mode descriptions
    mode1_desc = "Air-dominated mode (Helmholtz-like)"
    mode2_desc = "Top-dominated mode (monopole-like)"

    # Back activity assessment if back parameters provided
    back_ratio: Optional[float] = None
    back_recommendation: Optional[str] = None

    if all(v is not None for v in [back_E_L_GPa, back_E_C_GPa, back_rho, back_h_mm]):
        back_E_L_Pa = back_E_L_GPa * 1e9  # type: ignore
        back_E_C_Pa = back_E_C_GPa * 1e9  # type: ignore
        back_h_m = back_h_mm / 1000.0  # type: ignore

        back_ratio, back_recommendation = back_activity_ratio(
            E_L_back=back_E_L_Pa,
            E_C_back=back_E_C_Pa,
            rho_back=back_rho,  # type: ignore
            h_back=back_h_m,
            a_back=body.back_a_m,
            b_back=body.back_b_m,
            f_coupled_max=f2,
        )

        if back_recommendation != "2-oscillator":
            warnings.append(
                f"Back activity ratio = {back_ratio:.2f} suggests {back_recommendation} model. "
                "Results may underestimate coupling effects."
            )

    # Target comparison
    target = target_monopole_Hz or body.f_monopole_target
    f2_vs_target = f2 - target if target else None

    # Generate recommendation
    if f2_vs_target is not None:
        if abs(f2_vs_target) < 3:
            recommendation = f"Top mode ({f2:.1f} Hz) is on target ({target:.1f} Hz)."
        elif f2_vs_target > 0:
            recommendation = (
                f"Top mode ({f2:.1f} Hz) is {f2_vs_target:.1f} Hz HIGH. "
                "Consider thinning the top plate."
            )
        else:
            recommendation = (
                f"Top mode ({f2:.1f} Hz) is {-f2_vs_target:.1f} Hz LOW. "
                "Top may be too thin or material too soft."
            )
    else:
        recommendation = "No target specified. Review eigenfrequencies."

    # Warnings
    if f1 < 70:
        warnings.append(f"Air mode ({f1:.1f} Hz) is quite low. Check cavity volume.")
    if f1 > f2 * 0.9:
        warnings.append("Air mode close to top mode. Strong interaction expected.")

    return Coupled2OscResult(
        body_style=body.style.value,
        f1_Hz=round(f1, 1),
        f2_Hz=round(f2, 1),
        mode1_description=mode1_desc,
        mode2_description=mode2_desc,
        target_monopole_Hz=target,
        f2_vs_target_Hz=round(f2_vs_target, 1) if f2_vs_target else None,
        f_top_box_Hz=round(info["f_top_box_Hz"], 1),
        f_helmholtz_Hz=round(info["f_helmholtz_Hz"], 1),
        f_coupling_Hz=round(info["f_coupling_Hz"], 1),
        top_h_mm=round(top_h_mm, 2),
        back_activity_ratio=round(back_ratio, 2) if back_ratio else None,
        back_model_recommendation=back_recommendation,
        recommendation=recommendation,
        warnings=warnings,
    )


# =============================================================================
# Report Formatting
# =============================================================================


def format_2osc_report(result: Coupled2OscResult) -> str:
    """Format 2-oscillator analysis as text report."""
    lines = []
    lines.append("=" * 65)
    lines.append("2-Oscillator Coupled System Analysis (Rigid Back)")
    lines.append("=" * 65)

    lines.append(f"\nBody Style: {result.body_style}")

    lines.append("\nTop Plate:")
    lines.append(f"  Thickness  : {result.top_h_mm:.2f} mm")

    lines.append("\nUncoupled Component Frequencies:")
    lines.append(f"  Top (in box)    : {result.f_top_box_Hz:.1f} Hz")
    lines.append(f"  Helmholtz       : {result.f_helmholtz_Hz:.1f} Hz")
    lines.append(f"  Coupling        : {result.f_coupling_Hz:.1f} Hz")

    lines.append("\nCoupled Eigenfrequencies:")
    lines.append(f"  f1 = {result.f1_Hz:6.1f} Hz  -  {result.mode1_description}")
    lines.append(f"  f2 = {result.f2_Hz:6.1f} Hz  -  {result.mode2_description}")

    if result.back_activity_ratio is not None:
        lines.append("\nBack Assessment:")
        lines.append(f"  Activity ratio  : {result.back_activity_ratio:.2f}")
        lines.append(f"  Model fit       : {result.back_model_recommendation}")

    if result.target_monopole_Hz:
        lines.append(
            f"\nTarget: {result.target_monopole_Hz:.1f} Hz (top-dominated mode)"
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
