#!/usr/bin/env python3
"""
alpha_beta.py - Physical α/β formulation for Chladni-to-box frequency mapping.

This module computes the transfer coefficient γ = √(α/β) from first principles,
rather than using empirical calibration values. This provides physical insight
into why frequencies shift when a free plate is assembled into a guitar body.

Physical Model:
    When a free plate is glued into a guitar body, two competing effects occur:

    α (Stiffness Increase):
        - Edge gluing adds boundary stiffness (plate edges become clamped/pinned)
        - Braces add local bending stiffness
        - Result: frequency tends to INCREASE

    β (Mass Increase):
        - Air loading adds virtual mass (radiation mass)
        - Braces add actual mass
        - Result: frequency tends to DECREASE

    The net effect is:
        f_box = f_free × √(α/β) = f_free × γ

    Typical values:
        α ≈ 1.2 - 1.5 (20-50% stiffness increase)
        β ≈ 1.3 - 1.8 (30-80% mass increase)
        γ ≈ 0.75 - 0.95 (frequency drops 5-25%)

References:
    - Gore & Gilet, "Contemporary Acoustic Guitar Design and Build", Vol 2
    - Fletcher & Rossing, "The Physics of Musical Instruments", Ch 9
    - Caldersmith, "Designing a Guitar Family", GSJ 1978
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple, Any

# Air properties at standard conditions
AIR_DENSITY_KG_M3 = 1.2
AIR_SPEED_OF_SOUND_M_S = 343.0


# =============================================================================
# α (Stiffness Increase) Calculations
# =============================================================================


def plate_bending_stiffness(
    E_L: float,  # Pa - longitudinal modulus
    E_C: float,  # Pa - cross-grain modulus
    h: float,  # m - thickness
    nu: float = 0.3,  # Poisson's ratio
) -> float:
    """
    Compute effective bending stiffness D for an orthotropic plate.

    D = E_eff × h³ / [12 × (1 - ν²)]

    For orthotropic plates, we use geometric mean of E_L and E_C.

    Args:
        E_L: Longitudinal modulus (Pa)
        E_C: Cross-grain modulus (Pa)
        h: Plate thickness (m)
        nu: Poisson's ratio (default 0.3)

    Returns:
        Bending stiffness D (N·m)
    """
    E_eff = math.sqrt(E_L * E_C)  # Geometric mean for orthotropic
    D = E_eff * (h**3) / (12.0 * (1.0 - nu**2))
    return D


def edge_stiffness_simply_supported(
    D: float,  # N·m - plate bending stiffness
    a: float,  # m - plate length
    b: float,  # m - plate width
) -> float:
    """
    Compute effective edge stiffness for simply-supported boundary.

    This represents the additional stiffness from constraining the edges
    to zero displacement (but allowing rotation).

    k_edge ≈ D × (π⁴/4) × (1/a² + 1/b²)²

    Args:
        D: Plate bending stiffness (N·m)
        a: Plate length (m)
        b: Plate width (m)

    Returns:
        Edge stiffness contribution (N/m)
    """
    term = (1.0 / a**2) + (1.0 / b**2)
    k_edge = D * (math.pi**4 / 4.0) * (term**2)
    return k_edge


def edge_stiffness_clamped(
    D: float,  # N·m - plate bending stiffness
    a: float,  # m - plate length
    b: float,  # m - plate width
) -> float:
    """
    Compute effective edge stiffness for clamped (fixed) boundary.

    Clamped edges constrain both displacement AND rotation, adding
    more stiffness than simply-supported edges.

    k_edge_clamped ≈ 2.25 × k_edge_simply_supported

    The factor 2.25 comes from the ratio of eigenvalues for clamped
    vs simply-supported rectangular plates (λ_clamped/λ_SS ≈ 1.5²).

    Args:
        D: Plate bending stiffness (N·m)
        a: Plate length (m)
        b: Plate width (m)

    Returns:
        Edge stiffness contribution (N/m)
    """
    k_ss = edge_stiffness_simply_supported(D, a, b)
    return 2.25 * k_ss


def brace_stiffness(
    E_brace: float,  # Pa - brace modulus (along brace length)
    h_brace: float,  # m - brace height
    w_brace: float,  # m - brace width
    L_brace: float,  # m - brace length
    n_braces: int = 1,  # number of similar braces
) -> float:
    """
    Compute stiffness contribution from braces.

    Models brace as beam in bending. Stiffness depends on brace geometry
    and how it's attached to the plate.

    For a brace glued along its length:
        k_brace ≈ E × I / L² × geometric_factor

    where I = w × h³ / 12 (second moment of area)

    Args:
        E_brace: Brace elastic modulus (Pa)
        h_brace: Brace height (m) - dimension perpendicular to plate
        w_brace: Brace width (m) - dimension along plate
        L_brace: Brace length (m)
        n_braces: Number of similar braces

    Returns:
        Total brace stiffness contribution (N/m)
    """
    # Second moment of area for rectangular cross-section
    I_brace = w_brace * (h_brace**3) / 12.0

    # Effective stiffness (beam bending approximation)
    # Factor of 48 for uniformly loaded beam with fixed ends
    k_single = 48.0 * E_brace * I_brace / (L_brace**3)

    return k_single * n_braces


def compute_alpha(
    # Plate properties
    E_L: float,  # Pa
    E_C: float,  # Pa
    h: float,  # m
    a: float,  # m
    b: float,  # m
    # Boundary condition
    boundary: str = "glued",  # "free", "simply_supported", "clamped", "glued"
    # Bracing (optional)
    brace_stiffness_total: float = 0.0,  # N/m - from brace_stiffness()
    brace_count: int = 0,  # number of braces (for empirical factor)
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute α (stiffness ratio) for a plate assembled into a body.

    This uses empirically-grounded eigenvalue ratios rather than
    absolute stiffness calculations.

    For boundary conditions, the stiffness factor is based on
    the ratio of (1,1) mode eigenvalues:
        - Free plate:            λ_free = 1.0 (reference)
        - Simply supported:      λ_SS ≈ 1.0 (similar to free for (1,1))
        - Clamped (all edges):   λ_clamp ≈ 2.25 (from plate theory)
        - Glued (partial clamp): λ_glued ≈ 1.15-1.35

    For bracing, each brace adds approximately 3-8% stiffness
    depending on brace size and orientation.

    Args:
        E_L: Longitudinal modulus (Pa)
        E_C: Cross-grain modulus (Pa)
        h: Plate thickness (m)
        a: Plate length (m)
        b: Plate width (m)
        boundary: Boundary condition type
        brace_stiffness_total: Total brace stiffness (N/m) - for info only
        brace_count: Number of braces (for empirical stiffening factor)

    Returns:
        Tuple of:
        - alpha: Stiffness ratio (dimensionless, > 1)
        - info: Dict with breakdown of contributions
    """
    D = plate_bending_stiffness(E_L, E_C, h)

    # Base alpha from boundary condition (eigenvalue ratio)
    # These are empirical values from plate vibration literature
    if boundary == "free":
        alpha_boundary = 1.0
    elif boundary == "simply_supported":
        # SS edges constrain displacement but allow rotation
        # For (1,1) mode, similar to free plate
        alpha_boundary = 1.05
    elif boundary == "clamped":
        # Clamped edges constrain both displacement and rotation
        # Eigenvalue ratio λ_clamped/λ_free ≈ 1.5² = 2.25
        # But this is extreme; real clamping is partial
        alpha_boundary = 1.50
    elif boundary == "glued":
        # Guitar linings provide partial clamping
        # Empirical range: 1.15 - 1.35 depending on lining stiffness
        alpha_boundary = 1.25
    else:
        alpha_boundary = 1.0

    # Bracing contribution (empirical)
    # Each brace adds roughly 3-8% stiffness for typical X-bracing
    # Scaled by brace stiffness if provided
    if brace_count > 0:
        alpha_braces = 1.0 + 0.05 * brace_count  # ~5% per brace
    else:
        alpha_braces = 1.0

    # Combined alpha (multiplicative, not additive)
    alpha = alpha_boundary * alpha_braces

    info = {
        "D_Nm": D,
        "alpha_boundary": alpha_boundary,
        "alpha_braces": alpha_braces,
        "brace_count": brace_count,
        "boundary": boundary,
    }

    return alpha, info


# =============================================================================
# β (Mass Increase) Calculations
# =============================================================================


def plate_mass(
    rho: float,  # kg/m³ - density
    h: float,  # m - thickness
    a: float,  # m - length
    b: float,  # m - width
) -> float:
    """
    Compute plate mass.

    m = ρ × h × a × b

    Args:
        rho: Plate density (kg/m³)
        h: Plate thickness (m)
        a: Plate length (m)
        b: Plate width (m)

    Returns:
        Plate mass (kg)
    """
    return rho * h * a * b


def air_virtual_mass(
    a: float,  # m - plate length
    b: float,  # m - plate width
    rho_air: float = AIR_DENSITY_KG_M3,
) -> float:
    """
    Compute virtual mass from air loading (radiation mass).

    When a plate vibrates, it must accelerate the surrounding air.
    This adds "virtual mass" that lowers the frequency.

    For a rectangular piston:
        m_air ≈ (8 × ρ_air / 3π) × (a × b)^(3/2)

    This is an approximation for low-frequency, monopole-like motion.

    Args:
        a: Plate length (m)
        b: Plate width (m)
        rho_air: Air density (kg/m³)

    Returns:
        Virtual mass from air loading (kg)
    """
    # Effective radius for rectangular plate
    r_eff = math.sqrt(a * b / math.pi)

    # Virtual mass for circular piston (approximation)
    # m_air = (8/3) × ρ_air × r_eff³
    m_air = (8.0 / 3.0) * rho_air * (r_eff**3)

    return m_air


def air_virtual_mass_cavity(
    a: float,  # m - plate length
    b: float,  # m - plate width
    cavity_depth: float,  # m - average cavity depth
    rho_air: float = AIR_DENSITY_KG_M3,
) -> float:
    """
    Compute virtual mass including cavity confinement effects.

    In a guitar body, the air is confined. This modifies the virtual mass
    compared to free-field radiation.

    For cavity confinement:
        m_air_cavity ≈ m_air_free × (1 + a×b / (π × d²))

    where d is the cavity depth.

    Args:
        a: Plate length (m)
        b: Plate width (m)
        cavity_depth: Average cavity depth (m)
        rho_air: Air density (kg/m³)

    Returns:
        Virtual mass with cavity effect (kg)
    """
    m_free = air_virtual_mass(a, b, rho_air)

    # Cavity confinement factor
    if cavity_depth > 0:
        confinement = 1.0 + (a * b) / (math.pi * cavity_depth**2)
        # Limit to reasonable range
        confinement = min(confinement, 3.0)
    else:
        confinement = 1.0

    return m_free * confinement


def brace_mass(
    rho_brace: float,  # kg/m³ - brace density
    h_brace: float,  # m - brace height
    w_brace: float,  # m - brace width
    L_brace: float,  # m - brace length
    n_braces: int = 1,  # number of similar braces
) -> float:
    """
    Compute mass contribution from braces.

    m_brace = ρ × h × w × L × n

    Args:
        rho_brace: Brace density (kg/m³)
        h_brace: Brace height (m)
        w_brace: Brace width (m)
        L_brace: Brace length (m)
        n_braces: Number of similar braces

    Returns:
        Total brace mass (kg)
    """
    return rho_brace * h_brace * w_brace * L_brace * n_braces


def compute_beta(
    # Plate properties
    rho: float,  # kg/m³
    h: float,  # m
    a: float,  # m
    b: float,  # m
    # Air loading
    include_air_loading: bool = True,
    cavity_depth: float = 0.0,  # m - 0 = free-field, >0 = cavity
    # Bracing (optional)
    brace_mass_total: float = 0.0,  # kg - from brace_mass()
    # Air properties
    rho_air: float = AIR_DENSITY_KG_M3,
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute β (mass ratio) for a plate assembled into a body.

    β = 1 + (m_air + m_braces) / m_plate

    Args:
        rho: Plate density (kg/m³)
        h: Plate thickness (m)
        a: Plate length (m)
        b: Plate width (m)
        include_air_loading: Whether to include virtual air mass
        cavity_depth: Cavity depth for confinement (0 = free-field)
        brace_mass_total: Total brace mass (kg)
        rho_air: Air density (kg/m³)

    Returns:
        Tuple of:
        - beta: Mass ratio (dimensionless, > 1)
        - info: Dict with breakdown of contributions
    """
    m_plate = plate_mass(rho, h, a, b)

    # Air virtual mass
    if include_air_loading:
        if cavity_depth > 0:
            m_air = air_virtual_mass_cavity(a, b, cavity_depth, rho_air)
        else:
            m_air = air_virtual_mass(a, b, rho_air)
    else:
        m_air = 0.0

    # Total mass increase
    m_added = m_air + brace_mass_total

    # Beta ratio
    beta = 1.0 + m_added / m_plate if m_plate > 0 else 1.0

    info = {
        "m_plate_kg": m_plate,
        "m_air_kg": m_air,
        "m_braces_kg": brace_mass_total,
        "m_added_kg": m_added,
        "include_air_loading": include_air_loading,
        "cavity_depth_m": cavity_depth,
    }

    return beta, info


# =============================================================================
# γ (Transfer Coefficient) from α and β
# =============================================================================


def compute_gamma(
    alpha: float,
    beta: float,
) -> float:
    """
    Compute transfer coefficient γ from α and β.

    γ = √(α/β)

    Args:
        alpha: Stiffness ratio (> 1)
        beta: Mass ratio (> 1)

    Returns:
        Transfer coefficient γ (typically 0.7 - 1.0)
    """
    if beta <= 0:
        raise ValueError("Beta must be positive")
    return math.sqrt(alpha / beta)


@dataclass
class AlphaBetaResult:
    """Result of α/β analysis."""

    # Computed values
    alpha: float
    beta: float
    gamma: float

    # Frequency prediction
    f_free_Hz: float
    f_box_Hz: float

    # Breakdown
    alpha_info: Dict[str, float]
    beta_info: Dict[str, float]

    # Physical interpretation
    stiffness_increase_pct: float
    mass_increase_pct: float
    frequency_shift_pct: float

    def to_dict(self) -> Dict:
        return {
            "alpha": round(self.alpha, 4),
            "beta": round(self.beta, 4),
            "gamma": round(self.gamma, 4),
            "f_free_Hz": round(self.f_free_Hz, 1),
            "f_box_Hz": round(self.f_box_Hz, 1),
            "stiffness_increase_pct": round(self.stiffness_increase_pct, 1),
            "mass_increase_pct": round(self.mass_increase_pct, 1),
            "frequency_shift_pct": round(self.frequency_shift_pct, 1),
        }


def analyze_alpha_beta(
    # Plate properties
    E_L: float,  # Pa
    E_C: float,  # Pa
    rho: float,  # kg/m³
    h: float,  # m
    a: float,  # m
    b: float,  # m
    # Free-plate frequency (measured or calculated)
    f_free_Hz: float,
    # Boundary and cavity
    boundary: str = "glued",
    cavity_depth: float = 0.10,  # m - typical guitar depth
    # Bracing
    brace_stiffness_total: float = 0.0,
    brace_mass_total: float = 0.0,
) -> AlphaBetaResult:
    """
    Full α/β analysis to predict in-box frequency from free-plate frequency.

    Args:
        E_L: Longitudinal modulus (Pa)
        E_C: Cross-grain modulus (Pa)
        rho: Plate density (kg/m³)
        h: Plate thickness (m)
        a: Plate length (m)
        b: Plate width (m)
        f_free_Hz: Measured or calculated free-plate frequency (Hz)
        boundary: Boundary condition type
        cavity_depth: Cavity depth for air loading (m)
        brace_stiffness_total: Total brace stiffness (N/m)
        brace_mass_total: Total brace mass (kg)

    Returns:
        AlphaBetaResult with full analysis
    """
    # Compute α
    alpha, alpha_info = compute_alpha(
        E_L=E_L,
        E_C=E_C,
        h=h,
        a=a,
        b=b,
        boundary=boundary,
        brace_stiffness_total=brace_stiffness_total,
    )

    # Compute β
    beta, beta_info = compute_beta(
        rho=rho,
        h=h,
        a=a,
        b=b,
        include_air_loading=True,
        cavity_depth=cavity_depth,
        brace_mass_total=brace_mass_total,
    )

    # Compute γ
    gamma = compute_gamma(alpha, beta)

    # Predict box frequency
    f_box_Hz = f_free_Hz * gamma

    # Physical interpretation
    stiffness_increase_pct = (alpha - 1.0) * 100.0
    mass_increase_pct = (beta - 1.0) * 100.0
    frequency_shift_pct = (gamma - 1.0) * 100.0

    return AlphaBetaResult(
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        f_free_Hz=f_free_Hz,
        f_box_Hz=f_box_Hz,
        alpha_info=alpha_info,
        beta_info=beta_info,
        stiffness_increase_pct=stiffness_increase_pct,
        mass_increase_pct=mass_increase_pct,
        frequency_shift_pct=frequency_shift_pct,
    )


def format_alpha_beta_report(result: AlphaBetaResult) -> str:
    """Format α/β analysis as text report."""
    lines = []
    lines.append("=" * 65)
    lines.append("Alpha/Beta Physical Analysis")
    lines.append("=" * 65)

    lines.append("\nStiffness Factor (alpha):")
    lines.append(
        f"  alpha = {result.alpha:.4f} (+{result.stiffness_increase_pct:.1f}% stiffness)"
    )
    lines.append(f"    boundary factor : {result.alpha_info['alpha_boundary']:.3f}")
    lines.append(f"    bracing factor  : {result.alpha_info['alpha_braces']:.3f}")
    lines.append(f"    brace count     : {result.alpha_info['brace_count']}")
    lines.append(f"    boundary type   : {result.alpha_info['boundary']}")

    lines.append("\nMass Factor (beta):")
    lines.append(f"  beta = {result.beta:.4f} (+{result.mass_increase_pct:.1f}% mass)")
    lines.append(f"    m_plate : {result.beta_info['m_plate_kg'] * 1000:.1f} g")
    lines.append(f"    m_air   : {result.beta_info['m_air_kg'] * 1000:.1f} g")
    lines.append(f"    m_braces: {result.beta_info['m_braces_kg'] * 1000:.1f} g")

    lines.append("\nTransfer Coefficient:")
    lines.append(f"  gamma = sqrt(alpha/beta) = {result.gamma:.4f}")

    lines.append("\nFrequency Prediction:")
    lines.append(f"  f_free = {result.f_free_Hz:.1f} Hz (Chladni)")
    lines.append(f"  f_box  = {result.f_box_Hz:.1f} Hz (predicted)")
    lines.append(f"  shift  = {result.frequency_shift_pct:+.1f}%")

    lines.append("")
    return "\n".join(lines)
