"""
inverse_solver.py — Inverse solver for plate thickness design.

Given target modal frequencies, solve for optimal plate thickness and
other design parameters using the Rayleigh-Ritz forward model.

Theory:
    Forward problem: Given geometry + material → compute frequencies
    Inverse problem: Given target frequencies → find geometry/material

    The plate modal frequency scales approximately as:
        f ∝ h / (a² × b²)^(1/4) × √(E_eff / ρ)

    For thickness optimization:
        f ∝ h  (linear in thickness for fixed material/geometry)

    This makes the inverse problem well-posed for thickness.

Optimization Approaches:
    1. Single-frequency targeting: Find h for target f₁
    2. Multi-frequency targeting: Minimize weighted error across modes
    3. Constrained optimization: Respect manufacturing bounds

Usage:
    >>> from tap_tone_pi.design import (
    ...     solve_for_thickness,
    ...     InverseDesignProblem,
    ...     ThicknessConstraints,
    ... )
    >>>
    >>> # Simple: find thickness for 180 Hz fundamental
    >>> result = solve_for_thickness(
    ...     target_f1_Hz=180.0,
    ...     E_L=12e9, E_C=0.8e9, rho=420,
    ...     a=0.45, b=0.35,
    ... )
    >>> print(f"Optimal thickness: {result.thickness_mm:.2f} mm")

    >>> # Advanced: multi-mode targeting with constraints
    >>> problem = InverseDesignProblem(
    ...     E_L=12e9, E_C=0.8e9, rho=420,
    ...     a=0.45, b=0.35,
    ... )
    >>> problem.add_target(mode=(1,1), frequency_Hz=180.0, weight=1.0)
    >>> problem.add_target(mode=(2,1), frequency_Hz=290.0, weight=0.5)
    >>> result = problem.solve(
    ...     constraints=ThicknessConstraints(h_min_mm=2.0, h_max_mm=4.0)
    ... )
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from scipy import optimize

from .rayleigh_ritz import (
    OrthotropicPlate,
    BoundaryCondition,
    solve_rayleigh_ritz,
)
from .thickness_calculator import plate_modal_frequency


# =============================================================================
# Data Classes
# =============================================================================


class ForwardModel(str, Enum):
    """Choice of forward model for frequency computation."""

    SIMPLE = "simple"  # Closed-form plate formula (fast)
    RAYLEIGH_RITZ = "rayleigh_ritz"  # Variational method (accurate)


@dataclass
class ThicknessConstraints:
    """Manufacturing constraints on plate thickness.

    Attributes:
        h_min_mm: Minimum thickness (mm) - structural limit
        h_max_mm: Maximum thickness (mm) - weight/tonal limit
        h_step_mm: Thickness step for discrete optimization (optional)
        taper_max_ratio: Maximum taper ratio (center/edge) if variable thickness
    """

    h_min_mm: float = 1.5
    h_max_mm: float = 5.0
    h_step_mm: Optional[float] = None
    taper_max_ratio: float = 1.5

    def __post_init__(self):
        if self.h_min_mm <= 0:
            raise ValueError("h_min_mm must be positive")
        if self.h_max_mm <= self.h_min_mm:
            raise ValueError("h_max_mm must be greater than h_min_mm")

    def is_valid(self, h_mm: float) -> bool:
        """Check if thickness is within constraints."""
        return self.h_min_mm <= h_mm <= self.h_max_mm

    def clamp(self, h_mm: float) -> float:
        """Clamp thickness to valid range."""
        return max(self.h_min_mm, min(self.h_max_mm, h_mm))

    def discretize(self, h_mm: float) -> float:
        """Round to discrete step if specified."""
        if self.h_step_mm is None:
            return h_mm
        return round(h_mm / self.h_step_mm) * self.h_step_mm


@dataclass
class FrequencyTarget:
    """Target frequency specification for optimization.

    Attributes:
        mode: Mode indices (m, n) or mode number
        frequency_Hz: Target frequency
        weight: Relative importance (higher = more important)
        tolerance_Hz: Acceptable error (for constraint formulation)
    """

    mode: Union[Tuple[int, int], int]
    frequency_Hz: float
    weight: float = 1.0
    tolerance_Hz: float = 5.0

    @property
    def mode_index(self) -> int:
        """Convert mode to 0-based index for result lookup."""
        if isinstance(self.mode, int):
            return self.mode - 1  # Mode 1 → index 0
        else:
            # For (m,n) modes, estimate index (approximate)
            m, n = self.mode
            return (m - 1) * 3 + (n - 1)  # Assumes 3 modes per direction


@dataclass
class InverseSolverResult:
    """Result of inverse thickness optimization.

    Attributes:
        thickness_mm: Optimal thickness (mm)
        thickness_m: Optimal thickness (m)
        achieved_frequencies_Hz: Frequencies at optimal thickness
        target_frequencies_Hz: Original target frequencies
        frequency_errors_Hz: Difference from targets
        frequency_errors_pct: Percentage errors
        rms_error_Hz: RMS frequency error
        converged: Whether optimization converged
        n_iterations: Number of iterations
        forward_model: Which forward model was used
        constraints_active: Whether constraints limited the solution
    """

    thickness_mm: float
    thickness_m: float
    achieved_frequencies_Hz: List[float]
    target_frequencies_Hz: List[float]
    frequency_errors_Hz: List[float]
    frequency_errors_pct: List[float]
    rms_error_Hz: float
    converged: bool
    n_iterations: int
    forward_model: ForwardModel
    constraints_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "thickness_mm": self.thickness_mm,
            "thickness_m": self.thickness_m,
            "achieved_frequencies_Hz": self.achieved_frequencies_Hz,
            "target_frequencies_Hz": self.target_frequencies_Hz,
            "frequency_errors_Hz": self.frequency_errors_Hz,
            "frequency_errors_pct": self.frequency_errors_pct,
            "rms_error_Hz": self.rms_error_Hz,
            "converged": self.converged,
            "n_iterations": self.n_iterations,
            "forward_model": self.forward_model.value,
            "constraints_active": self.constraints_active,
        }


# =============================================================================
# Forward Models
# =============================================================================


def _forward_simple(
    h_m: float,
    E_L: float,
    E_C: float,
    rho: float,
    a: float,
    b: float,
    n_modes: int = 5,
) -> List[float]:
    """Simple closed-form forward model.

    Uses the orthotropic plate formula for first few modes.
    Fast but less accurate for higher modes.
    """
    # Fundamental mode (1,1)
    f1 = plate_modal_frequency(E_L, E_C, rho, h_m, a, b)

    # Higher modes scale approximately as mode number squared
    # This is a rough approximation
    frequencies = [f1]
    mode_factors = [1.0, 2.0, 2.5, 3.5, 4.0]  # Empirical ratios

    for i in range(1, min(n_modes, len(mode_factors))):
        frequencies.append(f1 * mode_factors[i])

    return frequencies[:n_modes]


def _forward_rayleigh_ritz(
    h_m: float,
    E_L: float,
    E_C: float,
    rho: float,
    a: float,
    b: float,
    bc_x: BoundaryCondition = BoundaryCondition.SIMPLY_SUPPORTED,
    bc_y: BoundaryCondition = BoundaryCondition.SIMPLY_SUPPORTED,
    n_modes_x: int = 4,
    n_modes_y: int = 4,
    n_return: int = 5,
) -> List[float]:
    """Rayleigh-Ritz forward model.

    More accurate but slower than simple formula.
    """
    plate = OrthotropicPlate.from_wood(
        E_L=E_L,
        E_C=E_C,
        rho=rho,
        h=h_m,
        a=a,
        b=b,
    )

    result = solve_rayleigh_ritz(
        plate,
        n_modes_x=n_modes_x,
        n_modes_y=n_modes_y,
        bc_x=bc_x,
        bc_y=bc_y,
    )

    return result.frequencies_Hz[:n_return]


# =============================================================================
# Simple Solver (Single Target)
# =============================================================================


def solve_for_thickness(
    target_f1_Hz: float,
    E_L: float,
    E_C: float,
    rho: float,
    a: float,
    b: float,
    gamma: float = 1.0,
    constraints: Optional[ThicknessConstraints] = None,
    forward_model: ForwardModel = ForwardModel.SIMPLE,
) -> InverseSolverResult:
    """Solve for plate thickness to achieve target fundamental frequency.

    This is the simplest inverse problem: single mode, single parameter.

    For the simple model, we can solve analytically since f ∝ h.
    For Rayleigh-Ritz, we use numerical optimization.

    Args:
        target_f1_Hz: Target fundamental frequency (Hz)
        E_L: Longitudinal modulus (Pa)
        E_C: Cross-grain modulus (Pa)
        rho: Density (kg/m³)
        a: Plate length (m)
        b: Plate width (m)
        gamma: Transfer coefficient for free→box mapping (default 1.0 = free plate)
        constraints: Thickness constraints (optional)
        forward_model: Which forward model to use

    Returns:
        InverseSolverResult with optimal thickness
    """
    if constraints is None:
        constraints = ThicknessConstraints()

    # Adjust target for gamma (we design to free-plate frequency)
    target_free_Hz = target_f1_Hz / gamma if gamma != 0 else target_f1_Hz

    if forward_model == ForwardModel.SIMPLE:
        # Analytical solution using scaling
        # f ∝ h, so h_new = h_ref × (f_target / f_ref)

        # Compute reference frequency at h_ref = 3mm
        h_ref = 3.0e-3
        f_ref = plate_modal_frequency(E_L, E_C, rho, h_ref, a, b)

        # Scale to target
        h_opt_m = h_ref * (target_free_Hz / f_ref)
        n_iter = 1

    else:  # Rayleigh-Ritz
        # Numerical optimization
        def objective(h_mm: float) -> float:
            h_m = h_mm * 1e-3
            freqs = _forward_rayleigh_ritz(h_m, E_L, E_C, rho, a, b, n_return=1)
            return (freqs[0] - target_free_Hz) ** 2

        # Bracket search
        result = optimize.minimize_scalar(
            objective,
            bounds=(constraints.h_min_mm, constraints.h_max_mm),
            method="bounded",
        )
        h_opt_m = result.x * 1e-3
        n_iter = result.nfev

    # Apply constraints
    h_opt_mm = h_opt_m * 1e3
    constraints_active = False

    if not constraints.is_valid(h_opt_mm):
        h_opt_mm = constraints.clamp(h_opt_mm)
        h_opt_m = h_opt_mm * 1e-3
        constraints_active = True

    h_opt_mm = constraints.discretize(h_opt_mm)
    h_opt_m = h_opt_mm * 1e-3

    # Compute achieved frequency
    if forward_model == ForwardModel.SIMPLE:
        achieved = _forward_simple(h_opt_m, E_L, E_C, rho, a, b, n_modes=1)
    else:
        achieved = _forward_rayleigh_ritz(h_opt_m, E_L, E_C, rho, a, b, n_return=1)

    # Apply gamma for box frequency
    achieved_box = [f * gamma for f in achieved]

    error_Hz = achieved_box[0] - target_f1_Hz
    error_pct = 100.0 * error_Hz / target_f1_Hz if target_f1_Hz > 0 else 0.0

    return InverseSolverResult(
        thickness_mm=h_opt_mm,
        thickness_m=h_opt_m,
        achieved_frequencies_Hz=achieved_box,
        target_frequencies_Hz=[target_f1_Hz],
        frequency_errors_Hz=[error_Hz],
        frequency_errors_pct=[error_pct],
        rms_error_Hz=abs(error_Hz),
        converged=abs(error_pct) < 1.0,
        n_iterations=n_iter,
        forward_model=forward_model,
        constraints_active=constraints_active,
    )


# =============================================================================
# Advanced Solver (Multi-Target)
# =============================================================================


class InverseDesignProblem:
    """Advanced inverse design problem with multiple targets.

    Supports:
        - Multiple frequency targets with weights
        - Constrained optimization
        - Choice of forward model
        - Material/geometry optimization (future)

    Example:
        >>> problem = InverseDesignProblem(E_L=12e9, E_C=0.8e9, rho=420, a=0.45, b=0.35)
        >>> problem.add_target(mode=1, frequency_Hz=180.0, weight=1.0)
        >>> problem.add_target(mode=2, frequency_Hz=290.0, weight=0.5)
        >>> result = problem.solve()
    """

    def __init__(
        self,
        E_L: float,
        E_C: float,
        rho: float,
        a: float,
        b: float,
        gamma: float = 1.0,
        forward_model: ForwardModel = ForwardModel.RAYLEIGH_RITZ,
        bc_x: BoundaryCondition = BoundaryCondition.SIMPLY_SUPPORTED,
        bc_y: BoundaryCondition = BoundaryCondition.SIMPLY_SUPPORTED,
    ):
        """Initialize inverse design problem.

        Args:
            E_L: Longitudinal modulus (Pa)
            E_C: Cross-grain modulus (Pa)
            rho: Density (kg/m³)
            a: Plate length (m)
            b: Plate width (m)
            gamma: Transfer coefficient (free→box)
            forward_model: Which forward model to use
            bc_x: Boundary condition in x
            bc_y: Boundary condition in y
        """
        self.E_L = E_L
        self.E_C = E_C
        self.rho = rho
        self.a = a
        self.b = b
        self.gamma = gamma
        self.forward_model = forward_model
        self.bc_x = bc_x
        self.bc_y = bc_y

        self.targets: List[FrequencyTarget] = []
        self._eval_count = 0

    def add_target(
        self,
        mode: Union[Tuple[int, int], int],
        frequency_Hz: float,
        weight: float = 1.0,
        tolerance_Hz: float = 5.0,
    ) -> None:
        """Add a frequency target.

        Args:
            mode: Mode number (1, 2, ...) or indices (m, n)
            frequency_Hz: Target frequency
            weight: Relative importance
            tolerance_Hz: Acceptable error
        """
        self.targets.append(
            FrequencyTarget(
                mode=mode,
                frequency_Hz=frequency_Hz,
                weight=weight,
                tolerance_Hz=tolerance_Hz,
            )
        )

    def clear_targets(self) -> None:
        """Clear all targets."""
        self.targets.clear()

    def _compute_frequencies(self, h_m: float) -> List[float]:
        """Compute frequencies at given thickness."""
        n_modes_needed = (
            max(t.mode_index + 1 for t in self.targets) if self.targets else 5
        )

        if self.forward_model == ForwardModel.SIMPLE:
            freqs = _forward_simple(
                h_m,
                self.E_L,
                self.E_C,
                self.rho,
                self.a,
                self.b,
                n_modes=n_modes_needed,
            )
        else:
            freqs = _forward_rayleigh_ritz(
                h_m,
                self.E_L,
                self.E_C,
                self.rho,
                self.a,
                self.b,
                bc_x=self.bc_x,
                bc_y=self.bc_y,
                n_return=n_modes_needed,
            )

        # Apply gamma for box frequencies
        return [f * self.gamma for f in freqs]

    def _objective(self, h_mm: float) -> float:
        """Weighted RMS error objective function."""
        self._eval_count += 1
        h_m = h_mm * 1e-3

        try:
            freqs = self._compute_frequencies(h_m)
        except Exception:  # audited: solver-iteration-fallback
            return 1e10  # Penalty for invalid parameters

        total_error = 0.0
        total_weight = 0.0

        for target in self.targets:
            idx = target.mode_index
            if idx < len(freqs):
                # Relative error, weighted
                rel_error = (freqs[idx] - target.frequency_Hz) / target.frequency_Hz
                total_error += target.weight * (rel_error**2)
                total_weight += target.weight

        if total_weight > 0:
            return math.sqrt(total_error / total_weight)
        else:
            return 0.0

    def solve(
        self,
        constraints: Optional[ThicknessConstraints] = None,
        _initial_guess_mm: Optional[float] = None,
        method: str = "bounded",
    ) -> InverseSolverResult:
        """Solve the inverse problem.

        Args:
            constraints: Thickness constraints
            _initial_guess_mm: Reserved for future use (currently unused)
            method: Optimization method ("bounded", "brent", "golden")

        Returns:
            InverseSolverResult
        """
        if not self.targets:
            raise ValueError("No targets added. Use add_target() first.")

        if constraints is None:
            constraints = ThicknessConstraints()

        self._eval_count = 0

        # Solve
        if method == "bounded":
            result = optimize.minimize_scalar(
                self._objective,
                bounds=(constraints.h_min_mm, constraints.h_max_mm),
                method="bounded",
                options={"xatol": 0.01},  # 0.01mm tolerance
            )
            h_opt_mm = result.x
            converged = result.success
        else:
            # Bracket-based methods
            result = optimize.minimize_scalar(
                self._objective,
                bracket=(constraints.h_min_mm, constraints.h_max_mm),
                method=method,
            )
            h_opt_mm = result.x
            converged = True

        # Apply constraints
        constraints_active = False
        if not constraints.is_valid(h_opt_mm):
            h_opt_mm = constraints.clamp(h_opt_mm)
            constraints_active = True

        h_opt_mm = constraints.discretize(h_opt_mm)
        h_opt_m = h_opt_mm * 1e-3

        # Compute achieved frequencies
        achieved = self._compute_frequencies(h_opt_m)

        # Build result
        target_freqs = [t.frequency_Hz for t in self.targets]
        achieved_freqs = []
        errors_Hz = []
        errors_pct = []

        for target in self.targets:
            idx = target.mode_index
            if idx < len(achieved):
                f_achieved = achieved[idx]
                achieved_freqs.append(f_achieved)
                err = f_achieved - target.frequency_Hz
                errors_Hz.append(err)
                errors_pct.append(100.0 * err / target.frequency_Hz)
            else:
                achieved_freqs.append(0.0)
                errors_Hz.append(float("inf"))
                errors_pct.append(float("inf"))

        rms_error = (
            math.sqrt(sum(e**2 for e in errors_Hz) / len(errors_Hz))
            if errors_Hz
            else 0.0
        )

        return InverseSolverResult(
            thickness_mm=h_opt_mm,
            thickness_m=h_opt_m,
            achieved_frequencies_Hz=achieved_freqs,
            target_frequencies_Hz=target_freqs,
            frequency_errors_Hz=errors_Hz,
            frequency_errors_pct=errors_pct,
            rms_error_Hz=rms_error,
            converged=converged,
            n_iterations=self._eval_count,
            forward_model=self.forward_model,
            constraints_active=constraints_active,
        )


# =============================================================================
# Material Selection Solver
# =============================================================================


@dataclass
class MaterialCandidate:
    """Material candidate for selection optimization."""

    name: str
    E_L: float  # Pa
    E_C: float  # Pa
    rho: float  # kg/m³
    cost_factor: float = 1.0  # Relative cost


def solve_for_material_and_thickness(
    target_f1_Hz: float,
    candidates: List[MaterialCandidate],
    a: float,
    b: float,
    gamma: float = 1.0,
    constraints: Optional[ThicknessConstraints] = None,
    prefer_thin: bool = True,
) -> Tuple[MaterialCandidate, InverseSolverResult]:
    """Find optimal material and thickness combination.

    Evaluates each material candidate and finds the thickness needed
    to achieve the target frequency, then selects the best combination.

    Args:
        target_f1_Hz: Target fundamental frequency
        candidates: List of material candidates
        a: Plate length (m)
        b: Plate width (m)
        gamma: Transfer coefficient
        constraints: Thickness constraints
        prefer_thin: If True, prefer thinner solutions (lighter)

    Returns:
        Tuple of (best_material, solver_result)
    """
    if constraints is None:
        constraints = ThicknessConstraints()

    results = []

    for material in candidates:
        result = solve_for_thickness(
            target_f1_Hz=target_f1_Hz,
            E_L=material.E_L,
            E_C=material.E_C,
            rho=material.rho,
            a=a,
            b=b,
            gamma=gamma,
            constraints=constraints,
        )

        # Score: prioritize feasibility, then thinness or cost
        if result.constraints_active:
            score = 1000.0  # Penalty for hitting constraints
        else:
            if prefer_thin:
                score = result.thickness_mm * material.cost_factor
            else:
                score = material.cost_factor

        results.append((material, result, score))

    # Sort by score (lower is better)
    results.sort(key=lambda x: x[2])

    return results[0][0], results[0][1]


# =============================================================================
# Reporting
# =============================================================================


def format_inverse_solver_report(result: InverseSolverResult) -> str:
    """Format inverse solver result as text report."""
    lines = []
    lines.append("=" * 65)
    lines.append("Inverse Thickness Solver Result")
    lines.append("=" * 65)

    lines.append("\nOptimal Thickness:")
    lines.append(
        f"  h = {result.thickness_mm:.2f} mm ({result.thickness_m * 1e6:.0f} μm)"
    )

    lines.append("\nSolver Info:")
    lines.append(f"  Forward model: {result.forward_model.value}")
    lines.append(f"  Iterations:    {result.n_iterations}")
    lines.append(f"  Converged:     {result.converged}")
    lines.append(
        f"  Constraints:   {'active' if result.constraints_active else 'inactive'}"
    )

    lines.append("\nFrequency Matching:")
    lines.append(
        f"  {'Mode':<8} {'Target':>10} {'Achieved':>10} {'Error':>10} {'Error %':>10}"
    )
    lines.append(f"  {'-' * 8} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 10}")

    for i in range(len(result.target_frequencies_Hz)):
        lines.append(
            f"  {i + 1:<8} "
            f"{result.target_frequencies_Hz[i]:>10.1f} "
            f"{result.achieved_frequencies_Hz[i]:>10.1f} "
            f"{result.frequency_errors_Hz[i]:>+10.1f} "
            f"{result.frequency_errors_pct[i]:>+10.1f}%"
        )

    lines.append(f"\n  RMS Error: {result.rms_error_Hz:.2f} Hz")

    lines.append("")
    return "\n".join(lines)
