"""
Saw Lab 2.0 - Deflection Calculator (Beam Theory)

Calculates blade deflection using Euler-Bernoulli beam theory
applied to the unsupported blade span.

Physics model:
    The blade extends from the arbor clamp to the cutting zone.
    The unsupported portion acts as a cantilever beam loaded by
    the radial force Fr (perpendicular to blade face).

    Fr is the radial component of the cutting force, directed
    perpendicular to the C-axis rotation plane. It pushes the
    blade sideways and causes lateral deflection.

    Deflection: delta = Fr * L^3 / (3 * E * I)
    where:
        Fr: radial cutting force (N)
        L: unsupported blade length = blade_radius - arbor_clamp_radius (m)
        E: Young modulus of blade steel (Pa)
        I: second moment of area of blade cross-section (m^4)
           I = (1/12) * arc_contact_width * blade_thickness^3

    Acceptable deflection for woodworking: < 0.1 mm (precision)
    Marginal: 0.1-0.25 mm
    Unacceptable: > 0.25 mm
"""
from __future__ import annotations

from math import pi

from ..models import SawContext, SawDesign, SawCalculatorResult, MaterialProperties


# Deflection thresholds (mm)
_DEFLECTION_EXCELLENT = 0.05   # < 0.05 mm: excellent cut quality
_DEFLECTION_GOOD = 0.10       # < 0.10 mm: good cut quality
_DEFLECTION_MARGINAL = 0.25   # < 0.25 mm: marginal, visible marks
# > 0.25 mm: unacceptable, blade wander

# Default radial force ratio (Fr/Ft) for wood sawing
_RADIAL_RATIO = 0.4


class SawDeflectionCalculator:
    """
    Calculates blade deflection using beam theory.

    Uses the radial force component (perpendicular to the blade face,
    i.e. perpendicular to the C-axis rotation plane) to compute lateral
    blade deflection via cantilever beam model.

    Inputs:
        - Blade geometry (diameter, thickness, arbor size)
        - Blade material (Young modulus)
        - Cutting conditions (RPM, feed rate, tooth count)
        - Material being cut (specific cutting energy)

    Output:
        - Estimated deflection in mm
        - Score based on deflection thresholds
    """

    def calculate(
        self,
        design: SawDesign,
        ctx: SawContext,
        material: MaterialProperties | None = None,
    ) -> SawCalculatorResult:
        """
        Calculate blade deflection score using beam theory.

        Args:
            design: Cut design parameters
            ctx: Saw context (blade geometry, C-axis RPM)
            material: Optional material properties

        Returns:
            SawCalculatorResult with deflection estimate
        """
        try:
            # --- Specific cutting energy ---
            kc = 30.0  # J/mm^3 default (medium hardwood)
            if material is not None:
                kc = material.specific_cutting_energy_j_per_mm3

            # --- Estimate radial force Fr ---
            # First compute tangential force from cutting power / rim speed
            if design.dado_width_mm > 0:
                cut_width = design.dado_width_mm
                cut_depth = design.dado_depth_mm
            else:
                cut_width = ctx.blade_kerf_mm
                cut_depth = ctx.stock_thickness_mm

            feed_rate_mm_per_s = ctx.feed_rate_mm_per_min / 60.0
            mrr = cut_width * cut_depth * feed_rate_mm_per_s  # mm^3/s
            cutting_power_w = kc * mrr

            rim_speed = (pi * ctx.blade_diameter_mm * ctx.max_rpm) / (1000.0 * 60.0)  # m/s

            if rim_speed > 0:
                ft_n = cutting_power_w / rim_speed  # Tangential force (N)
            else:
                ft_n = 0.0

            fr_n = ft_n * _RADIAL_RATIO  # Radial force (N) -- causes deflection

            # --- Beam deflection model ---
            # Unsupported length: blade radius minus arbor clamp radius
            blade_radius_m = ctx.blade_diameter_mm / 2000.0
            arbor_clamp_radius_m = ctx.arbor_size_mm / 2000.0
            unsupported_length_m = blade_radius_m - arbor_clamp_radius_m

            # Second moment of area for blade cross-section
            # Treat as rectangular beam: I = (1/12) * b * h^3
            # b = effective contact width (approximate as arc of teeth in cut)
            # For simplicity, use the stock thickness as effective beam width
            blade_thickness_m = ctx.blade_thickness_mm / 1000.0
            effective_width_m = min(ctx.stock_thickness_mm, ctx.blade_diameter_mm / 4.0) / 1000.0

            i_moment = (1.0 / 12.0) * effective_width_m * blade_thickness_m**3

            # Young modulus
            e_pa = ctx.blade_youngs_modulus_gpa * 1e9  # GPa -> Pa

            # Cantilever deflection: delta = F * L^3 / (3 * E * I)
            if e_pa > 0 and i_moment > 0:
                deflection_m = fr_n * unsupported_length_m**3 / (3.0 * e_pa * i_moment)
                deflection_mm = abs(deflection_m) * 1000.0
            else:
                deflection_mm = 0.0

            # --- Scoring ---
            if deflection_mm <= _DEFLECTION_EXCELLENT:
                score = 100.0
                warning = None
            elif deflection_mm <= _DEFLECTION_GOOD:
                score = 85.0
                warning = f"Minor deflection {deflection_mm:.3f} mm (acceptable)"
            elif deflection_mm <= _DEFLECTION_MARGINAL:
                score = 55.0
                warning = (
                    f"Significant deflection {deflection_mm:.3f} mm; "
                    f"reduce feed rate or use thicker blade"
                )
            else:
                score = 20.0
                warning = (
                    f"Excessive deflection {deflection_mm:.3f} mm; "
                    f"blade wander will occur. Use stiffer blade or reduce cut depth."
                )

            return SawCalculatorResult(
                calculator_name="deflection",
                score=round(score, 1),
                warning=warning,
                metadata={
                    "deflection_mm": round(deflection_mm, 4),
                    "radial_force_n": round(fr_n, 2),
                    "tangential_force_n": round(ft_n, 2),
                    "unsupported_length_mm": round(unsupported_length_m * 1000, 1),
                    "blade_thickness_mm": ctx.blade_thickness_mm,
                    "moment_of_inertia_m4": i_moment,
                    "youngs_modulus_gpa": ctx.blade_youngs_modulus_gpa,
                    "mrr_mm3_per_s": round(mrr, 2),
                },
            )

        except (ZeroDivisionError, ValueError, TypeError, ArithmeticError, OverflowError) as e:  # WP-1: narrowed from except Exception
            return SawCalculatorResult(
                calculator_name="deflection",
                score=50.0,
                warning=f"Deflection calculation error: {str(e)}",
            )
