"""
Saw Lab 2.0 - Blade Dynamics Calculator

Calculates blade vibration and critical speed for CNC saw blades
rotating on the C-axis.

Physics model:
    A circular saw blade is a thin disk clamped at the arbor (inner radius)
    and free at the rim (outer radius). Its natural frequencies depend on:
    - Blade diameter and thickness (geometry)
    - Young's modulus and density (material)
    - Arbor clamping diameter (boundary condition)

    The blade rotates on the C-axis. Critical speed occurs when the
    C-axis RPM excites a natural frequency of the blade disk.

    Natural frequency of mode (0,n) for a clamped-free annular plate:
        fn = (lambda_n^2 / (2*pi)) * sqrt(D / (rho*h*R^4))
    where:
        D = E*h^3 / (12*(1 - nu^2))  (flexural rigidity)
        lambda_n: mode shape eigenvalue
        h: blade thickness
        R: outer radius
        rho: blade material density
        nu: Poisson's ratio (~0.3 for steel)
"""
from __future__ import annotations

from math import pi, sqrt

from ..models import SawContext, SawDesign, SawCalculatorResult


# Steel blade properties
_BLADE_DENSITY_KG_M3 = 7850.0  # Carbon steel
_POISSONS_RATIO = 0.3

# Mode eigenvalues for clamped-free annular plate (0,n) modes
# These depend on the inner/outer radius ratio (beta = Ri/Ro)
# For typical saw blades beta ~ 0.1, approximate eigenvalues:
_MODE_EIGENVALUES = {
    1: 2.00,   # First nodal diameter mode (lowest frequency)
    2: 5.31,   # Second nodal diameter
    3: 8.54,   # Third nodal diameter
}

# Safety margin: how far RPM should be from critical speeds
_CRITICAL_MARGIN_WARN = 0.15   # 15% margin -> YELLOW
_CRITICAL_MARGIN_DANGER = 0.05  # 5% margin -> RED


class SawBladeDynamicsCalculator:
    """
    Calculates blade natural frequencies and critical speeds on the C-axis.

    Checks whether the operating RPM is near a blade resonance.
    Blade vibration causes:
        - Poor cut quality (waviness)
        - Accelerated tooth wear
        - Noise and operator fatigue
        - In extreme cases, blade fracture

    Score criteria:
        - Distance from nearest critical speed
        - Multiple mode consideration (first 3 modes)
    """

    def calculate(
        self,
        design: SawDesign,
        ctx: SawContext,
    ) -> SawCalculatorResult:
        """
        Calculate blade dynamics feasibility.

        Args:
            design: Cut design parameters
            ctx: Saw context (C-axis RPM, blade geometry)

        Returns:
            SawCalculatorResult with dynamics metadata
        """
        try:
            # --- Blade Geometry ---
            outer_radius_m = ctx.blade_diameter_mm / 2000.0  # mm -> m
            thickness_m = ctx.blade_thickness_mm / 1000.0     # mm -> m
            arbor_radius_m = ctx.arbor_size_mm / 2000.0       # mm -> m

            # --- Material ---
            e_pa = ctx.blade_youngs_modulus_gpa * 1e9  # GPa -> Pa
            rho = _BLADE_DENSITY_KG_M3
            nu = _POISSONS_RATIO

            # --- Flexural Rigidity ---
            d_rigidity = (e_pa * thickness_m**3) / (12.0 * (1.0 - nu**2))

            # --- Natural Frequencies ---
            # fn = (lambda^2 / (2*pi*R^2)) * sqrt(D / (rho*h))
            natural_freqs_hz: dict[int, float] = {}
            critical_rpms: dict[int, float] = {}

            for mode, eigenvalue in _MODE_EIGENVALUES.items():
                fn = (eigenvalue**2 / (2.0 * pi * outer_radius_m**2)) * sqrt(
                    d_rigidity / (rho * thickness_m)
                )
                natural_freqs_hz[mode] = fn
                critical_rpms[mode] = fn * 60.0  # Hz -> RPM

            # --- Proximity Check ---
            # Find nearest critical speed to operating RPM
            operating_rpm = float(ctx.max_rpm)
            min_margin = float("inf")
            nearest_mode = 1
            nearest_critical_rpm = 0.0

            for mode, crit_rpm in critical_rpms.items():
                if crit_rpm > 0:
                    margin = abs(operating_rpm - crit_rpm) / crit_rpm
                    if margin < min_margin:
                        min_margin = margin
                        nearest_mode = mode
                        nearest_critical_rpm = crit_rpm

            # --- Scoring ---
            if min_margin < _CRITICAL_MARGIN_DANGER:
                score = 15.0
                warning = (
                    f"CRITICAL: Operating RPM {operating_rpm:.0f} is within "
                    f"{min_margin:.1%} of mode-{nearest_mode} critical speed "
                    f"({nearest_critical_rpm:.0f} RPM). Blade resonance risk."
                )
            elif min_margin < _CRITICAL_MARGIN_WARN:
                score = 45.0
                warning = (
                    f"Operating RPM {operating_rpm:.0f} is {min_margin:.1%} from "
                    f"mode-{nearest_mode} critical speed ({nearest_critical_rpm:.0f} RPM). "
                    f"Consider adjusting RPM."
                )
            elif min_margin < 0.25:
                score = 75.0
                warning = (
                    f"RPM margin to nearest critical speed: {min_margin:.0%} "
                    f"(mode-{nearest_mode} at {nearest_critical_rpm:.0f} RPM)"
                )
            else:
                score = 100.0
                warning = None

            # Build metadata
            modes_meta = {}
            for mode in _MODE_EIGENVALUES:
                modes_meta[f"mode_{mode}_freq_hz"] = round(natural_freqs_hz[mode], 1)
                modes_meta[f"mode_{mode}_critical_rpm"] = round(critical_rpms[mode], 0)

            return SawCalculatorResult(
                calculator_name="blade_dynamics",
                score=round(score, 1),
                warning=warning,
                metadata={
                    "operating_rpm": operating_rpm,
                    "nearest_critical_rpm": round(nearest_critical_rpm, 0),
                    "nearest_mode": nearest_mode,
                    "margin_to_critical": round(min_margin, 4),
                    "flexural_rigidity_nm": round(d_rigidity, 4),
                    **modes_meta,
                },
            )

        except (ZeroDivisionError, ValueError, TypeError, ArithmeticError, OverflowError) as e:  # WP-1: narrowed from except Exception
            return SawCalculatorResult(
                calculator_name="blade_dynamics",
                score=50.0,
                warning=f"Blade dynamics calculation error: {str(e)}",
            )
