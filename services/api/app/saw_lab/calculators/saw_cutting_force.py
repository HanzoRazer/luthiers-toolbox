"""
Saw Lab 2.0 - Cutting Force Calculator

Calculates cutting forces for CNC saw blade operations using
specific cutting energy and C-axis force decomposition.

Coordinate model:
    - X, Y, Z: Linear machine axes (feed, cross-feed, vertical)
    - C-axis: Blade rotational axis (the saw blade spins on C)
    - Forces decompose relative to C-axis rotation plane:
        Ft (tangential) - in the C-axis rotation plane
        Fr (radial) - perpendicular to blade face, causes deflection
        Ff (feed) - along the linear feed axis
"""
from __future__ import annotations

from math import pi

from ..models import SawContext, SawDesign, SawCalculatorResult, MaterialProperties


# Default material force ratios for wood cutting
# Fr/Ft ratio: radial force is typically 30-50% of tangential in wood
_DEFAULT_RADIAL_RATIO = 0.4
# Ff/Ft ratio: feed force is typically 50-70% of tangential in wood
_DEFAULT_FEED_RATIO = 0.6
# Cutting efficiency: fraction of motor power available at blade
_MOTOR_EFFICIENCY = 0.85


class SawCuttingForceCalculator:
    """
    Calculates cutting forces and power consumption for saw operations.

    Physics:
        MRR = kerf_mm * stock_thickness_mm * feed_rate_mm_per_min / 60  [mm^3/s]
        Pc = Kc * MRR  [W]  (cutting power = specific energy * removal rate)
        Vc = pi * D * RPM / (1000 * 60)  [m/s]  (rim speed)
        Ft = Pc / Vc  [N]  (tangential force from power / velocity)
        Fr = Ft * radial_ratio  [N]  (radial force, causes deflection)
        Ff = Ft * feed_ratio  [N]  (feed force, resists workpiece motion)

    Score criteria:
        - Power ratio (required vs available): must stay under 80%
        - Force magnitude: excessive forces reduce score
        - MRR within productive but safe range
    """

    def calculate(
        self,
        design: SawDesign,
        ctx: SawContext,
        material: MaterialProperties | None = None,
    ) -> SawCalculatorResult:
        """
        Calculate cutting force feasibility.

        Args:
            design: Cut design parameters
            ctx: Saw context (includes C-axis RPM, feed rate)
            material: Optional material properties (uses defaults if None)

        Returns:
            SawCalculatorResult with force data in metadata
        """
        try:
            # Material properties (defaults for generic hardwood)
            kc = 30.0  # J/mm^3 default
            if material is not None:
                kc = material.specific_cutting_energy_j_per_mm3

            # --- Material Removal Rate ---
            # For through-cuts: MRR = kerf * depth * feed_rate
            # For dados: MRR = dado_width * dado_depth * feed_rate
            if design.dado_width_mm > 0:
                cut_width = design.dado_width_mm
                cut_depth = design.dado_depth_mm
            else:
                cut_width = ctx.blade_kerf_mm
                cut_depth = ctx.stock_thickness_mm

            # MRR in mm^3/s
            feed_rate_mm_per_s = ctx.feed_rate_mm_per_min / 60.0
            mrr_mm3_per_s = cut_width * cut_depth * feed_rate_mm_per_s

            # --- Cutting Power ---
            # Pc = Kc * MRR  (Kc in J/mm^3 = N/mm^2, MRR in mm^3/s -> W)
            cutting_power_w = kc * mrr_mm3_per_s

            # --- Rim Speed (C-axis tangential velocity) ---
            rim_speed_m_per_s = (pi * ctx.blade_diameter_mm * ctx.max_rpm) / (1000.0 * 60.0)

            # --- Force Decomposition (relative to C-axis) ---
            if rim_speed_m_per_s > 0:
                # Ft = Pc / Vc (tangential force in C-axis rotation plane)
                ft_n = cutting_power_w / rim_speed_m_per_s
            else:
                ft_n = 0.0

            # Fr (radial, perpendicular to blade face -> deflection)
            fr_n = ft_n * _DEFAULT_RADIAL_RATIO
            # Ff (feed force, along linear feed axis)
            ff_n = ft_n * _DEFAULT_FEED_RATIO

            # Resultant force
            resultant_n = (ft_n**2 + fr_n**2 + ff_n**2) ** 0.5

            # --- Power Feasibility ---
            available_power_w = ctx.machine_power_kw * 1000.0 * _MOTOR_EFFICIENCY
            power_ratio = cutting_power_w / available_power_w if available_power_w > 0 else 1.0

            # --- Scoring ---
            # Power ratio is primary concern
            if power_ratio > 1.0:
                score = 10.0
                warning = (
                    f"OVERLOAD: cutting needs {cutting_power_w:.0f} W but "
                    f"machine provides {available_power_w:.0f} W ({power_ratio:.0%})"
                )
            elif power_ratio > 0.9:
                score = 30.0
                warning = (
                    f"Near machine power limit ({power_ratio:.0%}); "
                    f"reduce feed rate or depth of cut"
                )
            elif power_ratio > 0.8:
                score = 55.0
                warning = (
                    f"High power usage ({power_ratio:.0%}); "
                    f"Ft={ft_n:.1f} N, Fr={fr_n:.1f} N"
                )
            elif power_ratio > 0.6:
                score = 80.0
                warning = None
            else:
                score = 100.0
                warning = None

            # Secondary penalty: excessive tangential force
            if ft_n > 500 and score > 50:
                score = max(50.0, score - 15.0)
                warning = (
                    warning or ""
                ) + f" High tangential force: {ft_n:.0f} N on C-axis"

            return SawCalculatorResult(
                calculator_name="cutting_force",
                score=round(score, 1),
                warning=warning if warning else None,
                metadata={
                    "mrr_mm3_per_s": round(mrr_mm3_per_s, 2),
                    "cutting_power_w": round(cutting_power_w, 1),
                    "available_power_w": round(available_power_w, 1),
                    "power_ratio": round(power_ratio, 3),
                    "rim_speed_m_per_s": round(rim_speed_m_per_s, 2),
                    "ft_tangential_n": round(ft_n, 2),
                    "fr_radial_n": round(fr_n, 2),
                    "ff_feed_n": round(ff_n, 2),
                    "resultant_force_n": round(resultant_n, 2),
                    "specific_cutting_energy_j_per_mm3": kc,
                },
            )

        except (ZeroDivisionError, ValueError, TypeError, ArithmeticError, OverflowError) as e:  # WP-1: narrowed from except Exception
            return SawCalculatorResult(
                calculator_name="cutting_force",
                score=50.0,
                warning=f"Cutting force calculation error: {str(e)}",
            )
