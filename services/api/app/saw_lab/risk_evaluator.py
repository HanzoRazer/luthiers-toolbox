"""
Saw Lab 2.0 - Risk Evaluator

Evaluates safety risks for saw blade operations.
"""
from __future__ import annotations

from typing import List, Dict, Any
from math import pi

from .models import SawContext, SawDesign, SawRiskLevel


class SawRiskEvaluator:
    """
    Evaluates safety risks for saw operations.
    
    Checks:
        - Kickback risk based on cut type and material
        - Blade exposure risk
        - Feed rate safety
        - RPM safety for blade diameter
    """
    
    def evaluate(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawRiskLevel:
        """
        Evaluate overall safety risk for operation.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            SawRiskLevel (GREEN, YELLOW, RED)
        """
        risks = []
        
        # Check kickback risk
        risks.append(self._check_kickback_risk(design, ctx))
        
        # Check blade exposure
        risks.append(self._check_blade_exposure(design, ctx))
        
        # Check RPM safety
        risks.append(self._check_rpm_safety(ctx))
        
        # Check feed rate safety
        risks.append(self._check_feed_safety(design, ctx))
        
        # Return worst case
        if SawRiskLevel.RED in risks:
            return SawRiskLevel.RED
        elif SawRiskLevel.YELLOW in risks:
            return SawRiskLevel.YELLOW
        return SawRiskLevel.GREEN
    
    def get_risk_details(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> Dict[str, Any]:
        """
        Get detailed risk assessment breakdown.
        
        Returns:
            Dict with risk details for each category
        """
        return {
            "kickback": {
                "level": self._check_kickback_risk(design, ctx).value,
                "factors": self._get_kickback_factors(design, ctx)
            },
            "blade_exposure": {
                "level": self._check_blade_exposure(design, ctx).value,
                "factors": self._get_exposure_factors(design, ctx)
            },
            "rpm": {
                "level": self._check_rpm_safety(ctx).value,
                "factors": self._get_rpm_factors(ctx)
            },
            "feed": {
                "level": self._check_feed_safety(design, ctx).value,
                "factors": self._get_feed_factors(design, ctx)
            }
        }
    
    def _check_kickback_risk(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawRiskLevel:
        """Check risk of kickback."""
        # Higher risk for rip cuts and thick stock
        risk_score = 0.0
        
        # Cut type factor
        if design.cut_type == "rip":
            risk_score += 30.0
        elif design.cut_type == "crosscut":
            risk_score += 10.0
        else:
            risk_score += 20.0
        
        # Stock thickness factor
        if ctx.stock_thickness_mm > 50:
            risk_score += 25.0
        elif ctx.stock_thickness_mm > 25:
            risk_score += 15.0
        
        # Bevel cuts increase risk
        if abs(design.bevel_angle_deg) > 30:
            risk_score += 20.0
        elif abs(design.bevel_angle_deg) > 15:
            risk_score += 10.0
        
        # Feed rate factor (too fast = higher kickback risk)
        if ctx.feed_rate_mm_per_min > 10000:
            risk_score += 15.0
        elif ctx.feed_rate_mm_per_min > 5000:
            risk_score += 5.0
        
        if risk_score >= 60:
            return SawRiskLevel.RED
        elif risk_score >= 35:
            return SawRiskLevel.YELLOW
        return SawRiskLevel.GREEN
    
    def _check_blade_exposure(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawRiskLevel:
        """Check blade exposure risk."""
        # Blade exposure above stock
        blade_radius = ctx.blade_diameter_mm / 2.0
        exposure_above_stock = blade_radius - ctx.stock_thickness_mm
        
        # More than 25mm exposure is high risk
        if exposure_above_stock > 50:
            return SawRiskLevel.RED
        elif exposure_above_stock > 25:
            return SawRiskLevel.YELLOW
        return SawRiskLevel.GREEN
    
    def _check_rpm_safety(self, ctx: SawContext) -> SawRiskLevel:
        """Check if RPM is safe for blade diameter."""
        # Maximum safe rim speed ~80 m/s for carbide blades
        max_rim_speed_m_s = 80.0
        
        # Rim speed = π * D * RPM / (1000 * 60) in m/s
        rim_speed = (pi * ctx.blade_diameter_mm * ctx.max_rpm) / (1000 * 60)
        
        if rim_speed > max_rim_speed_m_s:
            return SawRiskLevel.RED
        elif rim_speed > max_rim_speed_m_s * 0.9:
            return SawRiskLevel.YELLOW
        return SawRiskLevel.GREEN
    
    def _check_feed_safety(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawRiskLevel:
        """Check if feed rate is safe for cut type."""
        # Feed per tooth threshold
        feed_per_tooth = ctx.feed_rate_mm_per_min / (ctx.max_rpm * ctx.tooth_count)
        
        # Safe range: 0.05-0.15 mm/tooth for wood
        if feed_per_tooth > 0.25:
            return SawRiskLevel.RED
        elif feed_per_tooth > 0.15 or feed_per_tooth < 0.02:
            return SawRiskLevel.YELLOW
        return SawRiskLevel.GREEN
    
    def _get_kickback_factors(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> List[str]:
        """Get factors contributing to kickback risk."""
        factors = []
        if design.cut_type == "rip":
            factors.append("Rip cuts have higher kickback potential")
        if ctx.stock_thickness_mm > 50:
            factors.append("Thick stock increases binding risk")
        if abs(design.bevel_angle_deg) > 30:
            factors.append("Steep bevel angle increases instability")
        return factors
    
    def _get_exposure_factors(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> List[str]:
        """Get factors for blade exposure risk."""
        factors = []
        blade_radius = ctx.blade_diameter_mm / 2.0
        exposure = blade_radius - ctx.stock_thickness_mm
        if exposure > 25:
            factors.append(f"Blade exposure {exposure:.0f}mm above stock")
        return factors
    
    def _get_rpm_factors(self, ctx: SawContext) -> List[str]:
        """Get factors for RPM risk."""
        factors = []
        rim_speed = (pi * ctx.blade_diameter_mm * ctx.max_rpm) / (1000 * 60)
        factors.append(f"Rim speed: {rim_speed:.1f} m/s")
        if rim_speed > 72:
            factors.append("Approaching maximum safe rim speed")
        return factors
    
    def _get_feed_factors(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> List[str]:
        """Get factors for feed rate risk."""
        factors = []
        feed_per_tooth = ctx.feed_rate_mm_per_min / (ctx.max_rpm * ctx.tooth_count)
        factors.append(f"Feed per tooth: {feed_per_tooth:.3f} mm")
        if feed_per_tooth > 0.15:
            factors.append("High feed per tooth may cause tearout")
        elif feed_per_tooth < 0.02:
            factors.append("Low feed per tooth may cause burning")
        return factors
