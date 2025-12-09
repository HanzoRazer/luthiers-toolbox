"""
Saw Lab 2.0 - Deflection Calculator

Calculates blade deflection risk for saw operations.
"""
from __future__ import annotations

from ..models import SawContext, SawDesign, SawCalculatorResult


class SawDeflectionCalculator:
    """
    Calculates blade deflection feasibility.
    
    Factors:
        - Blade diameter to kerf ratio
        - Cut depth relative to blade diameter
        - Feed pressure (from feed rate)
    """
    
    def calculate(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawCalculatorResult:
        """
        Calculate blade deflection score.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            SawCalculatorResult with score and deflection estimate
        """
        try:
            # Blade stiffness factor (diameter to kerf ratio)
            # Thicker blade (lower ratio) = less deflection
            diameter_kerf_ratio = ctx.blade_diameter_mm / ctx.blade_kerf_mm
            
            # Optimal ratio: 60-100
            if diameter_kerf_ratio < 50:
                stiffness_factor = 0.7  # Blade relatively thick, less flexible
            elif diameter_kerf_ratio > 120:
                stiffness_factor = 0.75  # Blade thin, may deflect
            else:
                stiffness_factor = 1.0
            
            # Cut depth factor
            # Deeper cuts = more deflection potential
            blade_radius = ctx.blade_diameter_mm / 2.0
            cut_depth = ctx.stock_thickness_mm
            depth_ratio = cut_depth / blade_radius
            
            if depth_ratio > 0.8:
                depth_factor = 0.6  # Very deep cut
            elif depth_ratio > 0.5:
                depth_factor = 0.8  # Moderate cut
            else:
                depth_factor = 1.0  # Shallow cut
            
            # Feed pressure factor
            # Higher feed = more lateral pressure on blade
            feed_per_tooth = ctx.feed_rate_mm_per_min / (ctx.max_rpm * ctx.tooth_count)
            if feed_per_tooth > 0.15:
                feed_factor = 0.8
            elif feed_per_tooth > 0.1:
                feed_factor = 0.9
            else:
                feed_factor = 1.0
            
            # Calculate deflection index
            deflection_index = 100 * stiffness_factor * depth_factor * feed_factor
            
            # Estimate deflection in mm (simplified)
            estimated_deflection_mm = (1.0 - deflection_index / 100) * 2.0
            
            # Score and warning
            if deflection_index >= 80:
                score = 100.0
                warning = None
            elif deflection_index >= 60:
                score = 75.0
                warning = f"Minor blade deflection expected ({estimated_deflection_mm:.2f} mm)"
            elif deflection_index >= 40:
                score = 50.0
                warning = f"Significant deflection risk ({estimated_deflection_mm:.2f} mm); reduce feed rate"
            else:
                score = 25.0
                warning = f"High deflection risk ({estimated_deflection_mm:.2f} mm); use stiffer blade"
            
            return SawCalculatorResult(
                calculator_name="deflection",
                score=score,
                warning=warning,
                metadata={
                    "diameter_kerf_ratio": round(diameter_kerf_ratio, 1),
                    "cut_depth_ratio": round(depth_ratio, 2),
                    "deflection_index": round(deflection_index, 2),
                    "estimated_deflection_mm": round(estimated_deflection_mm, 3)
                }
            )
            
        except Exception as e:
            return SawCalculatorResult(
                calculator_name="deflection",
                score=50.0,
                warning=f"Deflection calculation error: {str(e)}"
            )
