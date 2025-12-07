"""
Saw Lab 2.0 - Kickback Risk Calculator

Calculates kickback risk for saw operations.
"""
from __future__ import annotations

from ..models import SawContext, SawDesign, SawCalculatorResult


class SawKickbackCalculator:
    """
    Calculates kickback risk for saw operations.
    
    Kickback occurs when the blade binds in the cut and
    throws the workpiece back at the operator.
    
    Risk factors:
        - Cut type (rip cuts higher risk)
        - Blade exposure above stock
        - Feed rate (too fast = stall, too slow = binding)
        - Bevel/miter angles (reduce stability)
        - Stock thickness and stability
    """
    
    def calculate(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawCalculatorResult:
        """
        Calculate kickback risk score.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            SawCalculatorResult with score and risk factors
        """
        try:
            risk_factors = []
            risk_score = 0.0
            
            # Cut type risk
            cut_type_risks = {
                "rip": 25.0,
                "crosscut": 10.0,
                "miter": 20.0,
                "bevel": 20.0,
                "dado": 15.0,
                "rabbet": 15.0,
            }
            cut_risk = cut_type_risks.get(design.cut_type.lower(), 15.0)
            risk_score += cut_risk
            if cut_risk >= 20:
                risk_factors.append(f"Cut type '{design.cut_type}' has elevated kickback risk")
            
            # Blade exposure risk
            blade_radius = ctx.blade_diameter_mm / 2.0
            exposure_mm = blade_radius - ctx.stock_thickness_mm
            if exposure_mm > 40:
                risk_score += 25.0
                risk_factors.append(f"High blade exposure ({exposure_mm:.0f}mm above stock)")
            elif exposure_mm > 20:
                risk_score += 10.0
                risk_factors.append(f"Moderate blade exposure ({exposure_mm:.0f}mm)")
            
            # Feed rate risk
            feed_per_tooth = ctx.feed_rate_mm_per_min / (ctx.max_rpm * ctx.tooth_count)
            if feed_per_tooth > 0.2:
                risk_score += 15.0
                risk_factors.append("Feed rate too aggressive; may cause stalling")
            elif feed_per_tooth < 0.02:
                risk_score += 10.0
                risk_factors.append("Feed rate too slow; blade may bind")
            
            # Angle risks
            if abs(design.bevel_angle_deg) > 30:
                risk_score += 15.0
                risk_factors.append(f"Steep bevel angle ({design.bevel_angle_deg}°) reduces stability")
            elif abs(design.bevel_angle_deg) > 15:
                risk_score += 8.0
            
            if abs(design.miter_angle_deg) > 30:
                risk_score += 10.0
                risk_factors.append(f"High miter angle ({design.miter_angle_deg}°)")
            elif abs(design.miter_angle_deg) > 15:
                risk_score += 5.0
            
            # Stock thickness risk
            if ctx.stock_thickness_mm > 75:
                risk_score += 15.0
                risk_factors.append("Very thick stock increases binding risk")
            elif ctx.stock_thickness_mm > 50:
                risk_score += 8.0
            
            # Combined angle risk (bevel + miter)
            if abs(design.bevel_angle_deg) > 0 and abs(design.miter_angle_deg) > 0:
                risk_score += 10.0
                risk_factors.append("Compound angle cuts require extra caution")
            
            # Calculate final score (inverted - lower risk = higher score)
            final_score = max(0, 100 - risk_score)
            
            # Determine warning level
            if final_score >= 80:
                warning = None
            elif final_score >= 60:
                warning = f"Moderate kickback risk ({len(risk_factors)} factors)"
            elif final_score >= 40:
                warning = f"Elevated kickback risk; use push sticks and featherboards"
            else:
                warning = f"HIGH kickback risk; verify all safety equipment"
            
            return SawCalculatorResult(
                calculator_name="kickback",
                score=final_score,
                warning=warning,
                metadata={
                    "risk_score": round(risk_score, 1),
                    "risk_factors": risk_factors,
                    "blade_exposure_mm": round(exposure_mm, 1),
                    "feed_per_tooth_mm": round(feed_per_tooth, 4),
                    "cut_type": design.cut_type,
                    "bevel_angle_deg": design.bevel_angle_deg,
                    "miter_angle_deg": design.miter_angle_deg
                }
            )
            
        except Exception as e:
            return SawCalculatorResult(
                calculator_name="kickback",
                score=50.0,
                warning=f"Kickback calculation error: {str(e)}"
            )
