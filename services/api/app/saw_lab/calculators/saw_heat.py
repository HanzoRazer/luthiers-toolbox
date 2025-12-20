"""
Saw Lab 2.0 - Heat Calculator

Calculates heat buildup risk for saw blade operations.
"""
from __future__ import annotations

from math import pi

from ..models import SawContext, SawDesign, SawCalculatorResult


class SawHeatCalculator:
    """
    Calculates heat buildup feasibility for saw operations.
    
    Factors:
        - Rim speed (higher = more heat)
        - Feed rate (slower = more heat due to friction)
        - Material burn tendency
        - Dust collection (reduces heat)
    """
    
    def calculate(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawCalculatorResult:
        """
        Calculate heat buildup score.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            SawCalculatorResult with score and heat index
        """
        try:
            # Calculate rim speed (m/s)
            rim_speed_m_s = (pi * ctx.blade_diameter_mm * ctx.max_rpm) / (1000 * 60)
            
            # Heat index based on rim speed
            # Optimal: 40-60 m/s for wood
            if rim_speed_m_s < 30:
                speed_factor = 0.8  # Too slow, may cause friction heat
            elif rim_speed_m_s > 70:
                speed_factor = 0.7  # Too fast, blade heating
            else:
                speed_factor = 1.0  # Optimal range
            
            # Feed per tooth factor
            feed_per_tooth = ctx.feed_rate_mm_per_min / (ctx.max_rpm * ctx.tooth_count)
            if feed_per_tooth < 0.03:
                feed_factor = 0.7  # Too slow, burning risk
            elif feed_per_tooth > 0.2:
                feed_factor = 0.85  # Too fast, overloading
            else:
                feed_factor = 1.0
            
            # Dust collection factor
            dust_factor = 1.0 if ctx.use_dust_collection else 0.85
            
            # Calculate heat index (0-100, lower is more heat)
            heat_index = 100 * speed_factor * feed_factor * dust_factor
            
            # Determine score and warning
            if heat_index >= 80:
                score = 100.0
                warning = None
            elif heat_index >= 60:
                score = 75.0
                warning = f"Moderate heat risk (index: {heat_index:.1f})"
            elif heat_index >= 40:
                score = 50.0
                warning = f"High heat risk (index: {heat_index:.1f}); reduce speed or increase feed"
            else:
                score = 25.0
                warning = f"Critical heat risk (index: {heat_index:.1f}); cut may cause burning"
            
            return SawCalculatorResult(
                calculator_name="heat",
                score=score,
                warning=warning,
                metadata={
                    "rim_speed_m_s": round(rim_speed_m_s, 2),
                    "feed_per_tooth_mm": round(feed_per_tooth, 4),
                    "heat_index": round(heat_index, 2),
                    "dust_collection_active": ctx.use_dust_collection
                }
            )
            
        except Exception as e:
            return SawCalculatorResult(
                calculator_name="heat",
                score=50.0,
                warning=f"Heat calculation error: {str(e)}"
            )
