#!/usr/bin/env python3
"""
rayleigh_ritz.py - Rayleigh-Ritz method for orthotropic plate modal analysis.

The Rayleigh-Ritz method approximates plate vibration modes by assuming
trial functions and minimizing the Rayleigh quotient:

    ω² = max strain energy / max kinetic energy
       = ∫∫ D(∇²w)² dA / ∫∫ ρh w² dA

This provides more accurate mode shapes than simple formulas, especially
for real boundary conditions (clamped edges, mixed BCs).

Trial Functions:
    The deflection w(x,y) is approximated as a sum of basis functions:

    w(x,y) = Σᵢ Σⱼ Cᵢⱼ × φᵢ(x) × ψⱼ(y)

    where φᵢ, ψⱼ are chosen to satisfy boundary conditions:
    - Simply Supported: sin(nπx/a) - zero displacement at edges
    - Clamped: (1 - cos(2nπx/a)) - zero displacement AND slope
    - Free: polynomial or beam functions

Orthotropic Plates:
    For wood plates with different stiffness along/across grain:

    Strain energy includes terms for:
    - D₁₁ (∂²w/∂x²)² - bending along grain (E_L)
    - D₂₂ (∂²w/∂y²)² - bending across grain (E_C)
    - D₁₂ (∂²w/∂x²)(∂²w/∂y²) - Poisson coupling
    - D₆₆ (∂²w/∂x∂y)² - twisting (shear modulus)

References:
    - Leissa, "Vibration of Plates", NASA SP-160, 1969
    - Whitney, "Structural Analysis of Laminated Anisotropic Plates"
    - Gore & Gilet, "Contemporary Acoustic Guitar Design and Build"
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Tuple

import numpy as np
from numpy.typing import NDArray


class BoundaryCondition(Enum):
    """Plate boundary condition types."""

    FREE = "free"
    SIMPLY_SUPPORTED = "simply_supported"
    CLAMPED = "clamped"


# =============================================================================
# Orthotropic Plate Stiffness Matrix
# =============================================================================


@dataclass
class OrthotropicPlate:
    """Material and geometric properties of an orthotropic plate."""

    # Elastic moduli (Pa)
    E_L: float  # Longitudinal (along grain)
    E_C: float  # Cross-grain (across grain)
    G_LC: float  # In-plane shear modulus

    # Poisson's ratios
    nu_LC: float  # Poisson's ratio (strain in C due to stress in L)
    nu_CL: float  # Poisson's ratio (strain in L due to stress in C)

    # Density (kg/m³)
    rho: float

    # Geometry
    h: float  # Thickness (m)
    a: float  # Length along L direction (m)
    b: float  # Width along C direction (m)

    @classmethod
    def from_wood(
        cls,
        E_L: float,  # Pa
        E_C: float,  # Pa
        rho: float,  # kg/m³
        h: float,  # m
        a: float,  # m
        b: float,  # m
        nu_LC: float = 0.3,
    ) -> "OrthotropicPlate":
        """
        Create plate from typical wood properties.

        Estimates G_LC and nu_CL from E_L, E_C using empirical relations.

        Args:
            E_L: Longitudinal modulus (Pa)
            E_C: Cross-grain modulus (Pa)
            rho: Density (kg/m³)
            h: Thickness (m)
            a: Length along grain (m)
            b: Width across grain (m)
            nu_LC: Poisson's ratio (default 0.3)

        Returns:
            OrthotropicPlate instance
        """
        # Estimate shear modulus (typically G ≈ 0.06 × E_L for softwoods)
        G_LC = 0.06 * E_L

        # Reciprocity relation: nu_CL / E_C = nu_LC / E_L
        nu_CL = nu_LC * E_C / E_L

        return cls(
            E_L=E_L,
            E_C=E_C,
            G_LC=G_LC,
            nu_LC=nu_LC,
            nu_CL=nu_CL,
            rho=rho,
            h=h,
            a=a,
            b=b,
        )

    @property
    def D11(self) -> float:
        """Bending stiffness D₁₁ (along L direction)."""
        denom = 1.0 - self.nu_LC * self.nu_CL
        return self.E_L * (self.h**3) / (12.0 * denom)

    @property
    def D22(self) -> float:
        """Bending stiffness D₂₂ (along C direction)."""
        denom = 1.0 - self.nu_LC * self.nu_CL
        return self.E_C * (self.h**3) / (12.0 * denom)

    @property
    def D12(self) -> float:
        """Poisson coupling stiffness D₁₂."""
        denom = 1.0 - self.nu_LC * self.nu_CL
        return self.nu_LC * self.E_C * (self.h**3) / (12.0 * denom)

    @property
    def D66(self) -> float:
        """Twisting stiffness D₆₆."""
        return self.G_LC * (self.h**3) / 12.0

    @property
    def mass_per_area(self) -> float:
        """Mass per unit area (kg/m²)."""
        return self.rho * self.h

    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio a/b."""
        return self.a / self.b

    @property
    def orthotropy_ratio(self) -> float:
        """Orthotropy ratio E_L/E_C."""
        return self.E_L / self.E_C


# =============================================================================
# Trial Functions for Different Boundary Conditions
# =============================================================================


def sinusoidal_basis(
    n: int,
    L: float,
    x: NDArray[np.float64],
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """
    Sinusoidal basis functions for simply-supported edges.

    φₙ(x) = sin(nπx/L)

    Satisfies: φ(0) = φ(L) = 0 (zero displacement at edges)

    Args:
        n: Mode number (1, 2, 3, ...)
        L: Plate dimension (m)
        x: Position array (m)

    Returns:
        Tuple of (φ, dφ/dx, d²φ/dx²)
    """
    k = n * math.pi / L
    phi = np.sin(k * x)
    dphi = k * np.cos(k * x)
    d2phi = -k * k * np.sin(k * x)
    return phi, dphi, d2phi


def clamped_basis(
    n: int,
    L: float,
    x: NDArray[np.float64],
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """
    Basis functions for clamped edges.

    φₙ(x) = 1 - cos(2nπx/L)

    Satisfies: φ(0) = φ(L) = 0, dφ/dx(0) = dφ/dx(L) = 0

    Args:
        n: Mode number (1, 2, 3, ...)
        L: Plate dimension (m)
        x: Position array (m)

    Returns:
        Tuple of (φ, dφ/dx, d²φ/dx²)
    """
    k = 2 * n * math.pi / L
    phi = 1.0 - np.cos(k * x)
    dphi = k * np.sin(k * x)
    d2phi = k * k * np.cos(k * x)
    return phi, dphi, d2phi


def free_edge_basis(
    n: int,
    L: float,
    x: NDArray[np.float64],
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """
    Polynomial basis functions for free edges.

    Uses Legendre-type polynomials that satisfy free edge conditions
    (zero moment and shear at edges).

    φₙ(x) = xⁿ × (L-x)ⁿ × Pₙ(2x/L - 1)

    For simplicity, we use:
    φ₁(x) = 1 (rigid body)
    φ₂(x) = x/L - 0.5 (tilt)
    φ₃(x) = (x/L)² - x/L + 1/6 (curvature)
    ...

    Args:
        n: Mode number (1, 2, 3, ...)
        L: Plate dimension (m)
        x: Position array (m)

    Returns:
        Tuple of (φ, dφ/dx, d²φ/dx²)
    """
    xi = x / L  # Normalized coordinate

    if n == 1:
        # Constant (rigid body mode) - will be filtered out
        phi = np.ones_like(x)
        dphi = np.zeros_like(x)
        d2phi = np.zeros_like(x)
    elif n == 2:
        # Linear (rigid body rotation)
        phi = xi - 0.5
        dphi = np.ones_like(x) / L
        d2phi = np.zeros_like(x)
    else:
        # Higher order: use sinusoidal with shifted BC
        # This approximates free-free beam modes
        k = (n - 2) * math.pi / L
        phi = np.cos(k * x) + 0.5 * np.cos(k * (L - x))
        dphi = -k * np.sin(k * x) + 0.5 * k * np.sin(k * (L - x))
        d2phi = -k * k * np.cos(k * x) - 0.5 * k * k * np.cos(k * (L - x))

    return phi, dphi, d2phi


def get_basis_function(
    bc: BoundaryCondition,
) -> Callable[[int, float, NDArray], Tuple[NDArray, NDArray, NDArray]]:
    """Get the appropriate basis function for a boundary condition."""
    if bc == BoundaryCondition.SIMPLY_SUPPORTED:
        return sinusoidal_basis
    elif bc == BoundaryCondition.CLAMPED:
        return clamped_basis
    elif bc == BoundaryCondition.FREE:
        return free_edge_basis
    else:
        return sinusoidal_basis


# =============================================================================
# Rayleigh-Ritz Stiffness and Mass Matrices
# =============================================================================


def compute_stiffness_matrix(
    plate: OrthotropicPlate,
    n_modes_x: int,
    n_modes_y: int,
    bc_x: BoundaryCondition,
    bc_y: BoundaryCondition,
    n_quad: int = 32,
) -> NDArray[np.float64]:
    """
    Compute the stiffness matrix K for the Rayleigh-Ritz formulation.

    K[i,j] = ∫∫ [D₁₁ φᵢ'' ψᵢ × φⱼ'' ψⱼ + D₂₂ φᵢ ψᵢ'' × φⱼ ψⱼ''
              + D₁₂ (φᵢ'' ψᵢ × φⱼ ψⱼ'' + φᵢ ψᵢ'' × φⱼ'' ψⱼ)
              + 4D₆₆ φᵢ' ψᵢ' × φⱼ' ψⱼ'] dx dy

    Args:
        plate: Orthotropic plate properties
        n_modes_x: Number of modes in x direction
        n_modes_y: Number of modes in y direction
        bc_x: Boundary condition in x direction
        bc_y: Boundary condition in y direction
        n_quad: Number of quadrature points

    Returns:
        Stiffness matrix K (n_modes_x × n_modes_y, n_modes_x × n_modes_y)
    """
    n_total = n_modes_x * n_modes_y

    # Quadrature points and weights (Gauss-Legendre)
    xi_x, w_x = np.polynomial.legendre.leggauss(n_quad)
    xi_y, w_y = np.polynomial.legendre.leggauss(n_quad)

    # Map to physical coordinates [0, a] and [0, b]
    x = 0.5 * plate.a * (xi_x + 1)
    y = 0.5 * plate.b * (xi_y + 1)
    wx = 0.5 * plate.a * w_x
    wy = 0.5 * plate.b * w_y

    # Get basis functions
    basis_x = get_basis_function(bc_x)
    basis_y = get_basis_function(bc_y)

    # Precompute basis function values
    phi_x = []
    dphi_x = []
    d2phi_x = []
    for m in range(1, n_modes_x + 1):
        p, dp, d2p = basis_x(m, plate.a, x)
        phi_x.append(p)
        dphi_x.append(dp)
        d2phi_x.append(d2p)

    psi_y = []
    dpsi_y = []
    d2psi_y = []
    for n in range(1, n_modes_y + 1):
        p, dp, d2p = basis_y(n, plate.b, y)
        psi_y.append(p)
        dpsi_y.append(dp)
        d2psi_y.append(d2p)

    # Build stiffness matrix
    K = np.zeros((n_total, n_total))

    for i in range(n_total):
        mi = i // n_modes_y
        ni = i % n_modes_y

        for j in range(i, n_total):
            mj = j // n_modes_y
            nj = j % n_modes_y

            # Integrate over plate area
            integral = 0.0

            for qx in range(n_quad):
                for qy in range(n_quad):
                    # Basis function values at quadrature point
                    phi_i = phi_x[mi][qx]
                    dphi_i = dphi_x[mi][qx]
                    d2phi_i = d2phi_x[mi][qx]
                    psi_i = psi_y[ni][qy]
                    dpsi_i = dpsi_y[ni][qy]
                    d2psi_i = d2psi_y[ni][qy]

                    phi_j = phi_x[mj][qx]
                    dphi_j = dphi_x[mj][qx]
                    d2phi_j = d2phi_x[mj][qx]
                    psi_j = psi_y[nj][qy]
                    dpsi_j = dpsi_y[nj][qy]
                    d2psi_j = d2psi_y[nj][qy]

                    # D₁₁ term: (∂²w/∂x²)²
                    term_D11 = plate.D11 * (d2phi_i * psi_i) * (d2phi_j * psi_j)

                    # D₂₂ term: (∂²w/∂y²)²
                    term_D22 = plate.D22 * (phi_i * d2psi_i) * (phi_j * d2psi_j)

                    # D₁₂ term: (∂²w/∂x²)(∂²w/∂y²)
                    term_D12 = plate.D12 * (
                        (d2phi_i * psi_i) * (phi_j * d2psi_j)
                        + (phi_i * d2psi_i) * (d2phi_j * psi_j)
                    )

                    # D₆₆ term: (∂²w/∂x∂y)²
                    term_D66 = 4.0 * plate.D66 * (dphi_i * dpsi_i) * (dphi_j * dpsi_j)

                    # Sum and weight
                    integrand = term_D11 + term_D22 + term_D12 + term_D66
                    integral += integrand * wx[qx] * wy[qy]

            K[i, j] = integral
            K[j, i] = integral  # Symmetric

    return K


def compute_mass_matrix(
    plate: OrthotropicPlate,
    n_modes_x: int,
    n_modes_y: int,
    bc_x: BoundaryCondition,
    bc_y: BoundaryCondition,
    n_quad: int = 32,
) -> NDArray[np.float64]:
    """
    Compute the mass matrix M for the Rayleigh-Ritz formulation.

    M[i,j] = ρh × ∫∫ φᵢ ψᵢ × φⱼ ψⱼ dx dy

    Args:
        plate: Orthotropic plate properties
        n_modes_x: Number of modes in x direction
        n_modes_y: Number of modes in y direction
        bc_x: Boundary condition in x direction
        bc_y: Boundary condition in y direction
        n_quad: Number of quadrature points

    Returns:
        Mass matrix M (n_total, n_total)
    """
    n_total = n_modes_x * n_modes_y

    # Quadrature points
    xi_x, w_x = np.polynomial.legendre.leggauss(n_quad)
    xi_y, w_y = np.polynomial.legendre.leggauss(n_quad)

    x = 0.5 * plate.a * (xi_x + 1)
    y = 0.5 * plate.b * (xi_y + 1)
    wx = 0.5 * plate.a * w_x
    wy = 0.5 * plate.b * w_y

    # Get basis functions
    basis_x = get_basis_function(bc_x)
    basis_y = get_basis_function(bc_y)

    # Precompute basis function values (only need φ, ψ - not derivatives)
    phi_x = []
    for m in range(1, n_modes_x + 1):
        p, _, _ = basis_x(m, plate.a, x)
        phi_x.append(p)

    psi_y = []
    for n in range(1, n_modes_y + 1):
        p, _, _ = basis_y(n, plate.b, y)
        psi_y.append(p)

    # Build mass matrix
    M = np.zeros((n_total, n_total))

    for i in range(n_total):
        mi = i // n_modes_y
        ni = i % n_modes_y

        for j in range(i, n_total):
            mj = j // n_modes_y
            nj = j % n_modes_y

            integral = 0.0

            for qx in range(n_quad):
                for qy in range(n_quad):
                    phi_i = phi_x[mi][qx]
                    psi_i = psi_y[ni][qy]
                    phi_j = phi_x[mj][qx]
                    psi_j = psi_y[nj][qy]

                    integrand = (phi_i * psi_i) * (phi_j * psi_j)
                    integral += integrand * wx[qx] * wy[qy]

            M[i, j] = plate.mass_per_area * integral
            M[j, i] = M[i, j]  # Symmetric

    return M


# =============================================================================
# Eigenvalue Solver
# =============================================================================


@dataclass
class RayleighRitzMode:
    """A single vibration mode from Rayleigh-Ritz analysis."""

    mode_number: int
    frequency_Hz: float
    mode_indices: Tuple[int, int]  # (m, n) - mode shape indices
    coefficients: NDArray[np.float64]  # Expansion coefficients

    @property
    def omega_rad_s(self) -> float:
        """Angular frequency (rad/s)."""
        return 2.0 * math.pi * self.frequency_Hz


@dataclass
class RayleighRitzResult:
    """Results from Rayleigh-Ritz modal analysis."""

    # Plate info
    plate: OrthotropicPlate
    bc_x: BoundaryCondition
    bc_y: BoundaryCondition

    # Modes (sorted by frequency)
    modes: List[RayleighRitzMode]

    # Matrices (for advanced users)
    K: NDArray[np.float64]
    M: NDArray[np.float64]

    @property
    def n_modes(self) -> int:
        return len(self.modes)

    @property
    def frequencies_Hz(self) -> List[float]:
        return [m.frequency_Hz for m in self.modes]

    def get_mode_shape(
        self,
        mode_index: int,
        x: NDArray[np.float64],
        y: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """
        Evaluate mode shape on a grid.

        Args:
            mode_index: Which mode (0 = fundamental)
            x: 1D array of x coordinates
            y: 1D array of y coordinates

        Returns:
            2D array of mode shape values w(x, y)
        """
        mode = self.modes[mode_index]
        n_modes_x = int(math.sqrt(len(mode.coefficients)))
        n_modes_y = n_modes_x

        basis_x = get_basis_function(self.bc_x)
        basis_y = get_basis_function(self.bc_y)

        # Evaluate mode shape
        X, Y = np.meshgrid(x, y, indexing="ij")
        w = np.zeros_like(X)

        for i, c in enumerate(mode.coefficients):
            mi = i // n_modes_y
            ni = i % n_modes_y

            phi, _, _ = basis_x(mi + 1, self.plate.a, x)
            psi, _, _ = basis_y(ni + 1, self.plate.b, y)

            # Outer product
            for ix in range(len(x)):
                for iy in range(len(y)):
                    w[ix, iy] += c * phi[ix] * psi[iy]

        return w


def solve_rayleigh_ritz(
    plate: OrthotropicPlate,
    n_modes_x: int = 4,
    n_modes_y: int = 4,
    bc_x: BoundaryCondition = BoundaryCondition.SIMPLY_SUPPORTED,
    bc_y: BoundaryCondition = BoundaryCondition.SIMPLY_SUPPORTED,
    n_quad: int = 32,
    n_modes_return: int = 10,
) -> RayleighRitzResult:
    """
    Solve for plate vibration modes using the Rayleigh-Ritz method.

    Args:
        plate: Orthotropic plate properties
        n_modes_x: Number of trial functions in x direction (default 4)
        n_modes_y: Number of trial functions in y direction (default 4)
        bc_x: Boundary condition in x direction
        bc_y: Boundary condition in y direction
        n_quad: Number of quadrature points for integration
        n_modes_return: Number of modes to return (default 10)

    Returns:
        RayleighRitzResult with modes and matrices
    """
    # Build stiffness and mass matrices
    K = compute_stiffness_matrix(plate, n_modes_x, n_modes_y, bc_x, bc_y, n_quad)
    M = compute_mass_matrix(plate, n_modes_x, n_modes_y, bc_x, bc_y, n_quad)

    # Solve generalized eigenvalue problem: K v = λ M v
    # where λ = ω²
    try:
        eigenvalues, eigenvectors = np.linalg.eig(np.linalg.inv(M) @ K)
    except np.linalg.LinAlgError:
        # Fallback to scipy if available
        eigenvalues = np.diag(K) / np.diag(M)
        eigenvectors = np.eye(len(eigenvalues))

    # Sort by eigenvalue (frequency)
    idx = np.argsort(np.real(eigenvalues))
    eigenvalues = np.real(eigenvalues[idx])
    eigenvectors = np.real(eigenvectors[:, idx])

    # Filter out negative/zero eigenvalues (numerical artifacts)
    valid = eigenvalues > 1e-6
    eigenvalues = eigenvalues[valid]
    eigenvectors = eigenvectors[:, valid]

    # Convert to frequencies
    frequencies_Hz = np.sqrt(eigenvalues) / (2.0 * math.pi)

    # Build mode objects
    modes = []
    n_return = min(n_modes_return, len(frequencies_Hz))

    for i in range(n_return):
        # Determine dominant mode indices
        coeffs = eigenvectors[:, i]
        max_idx = np.argmax(np.abs(coeffs))
        mi = max_idx // n_modes_y + 1
        ni = max_idx % n_modes_y + 1

        modes.append(
            RayleighRitzMode(
                mode_number=i + 1,
                frequency_Hz=float(frequencies_Hz[i]),
                mode_indices=(mi, ni),
                coefficients=coeffs.copy(),
            )
        )

    return RayleighRitzResult(
        plate=plate,
        bc_x=bc_x,
        bc_y=bc_y,
        modes=modes,
        K=K,
        M=M,
    )


def format_rayleigh_ritz_report(result: RayleighRitzResult) -> str:
    """Format Rayleigh-Ritz analysis as text report."""
    lines = []
    lines.append("=" * 65)
    lines.append("Rayleigh-Ritz Modal Analysis")
    lines.append("=" * 65)

    lines.append("\nPlate Properties:")
    lines.append(
        f"  Dimensions : {result.plate.a * 1000:.1f} x {result.plate.b * 1000:.1f} x {result.plate.h * 1000:.2f} mm"
    )
    lines.append(f"  E_L        : {result.plate.E_L / 1e9:.2f} GPa")
    lines.append(f"  E_C        : {result.plate.E_C / 1e9:.2f} GPa")
    lines.append(f"  E_L/E_C    : {result.plate.orthotropy_ratio:.1f}")
    lines.append(f"  Density    : {result.plate.rho:.0f} kg/m3")

    lines.append("\nBoundary Conditions:")
    lines.append(f"  X edges    : {result.bc_x.value}")
    lines.append(f"  Y edges    : {result.bc_y.value}")

    lines.append("\nModal Frequencies:")
    lines.append(f"  {'Mode':<6} {'(m,n)':<8} {'Frequency':>12}")
    lines.append(f"  {'-' * 6} {'-' * 8} {'-' * 12}")

    for mode in result.modes:
        lines.append(
            f"  {mode.mode_number:<6} "
            f"({mode.mode_indices[0]},{mode.mode_indices[1]})    "
            f"{mode.frequency_Hz:>10.1f} Hz"
        )

    lines.append("")
    return "\n".join(lines)
