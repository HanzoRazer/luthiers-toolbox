"""
Saw Lab 2.0 - Rim Speed Calculator

Calculates rim (peripheral) speed safety for saw blades.
"""
from __future__ import annotations

import math

from ..models import SawContext, SawDesign, SawCalculatorResult


class SawRimSpeedCalculator:
    """
    Calculates rim speed safety for saw operations.
    
    Rim speed = peripheral velocity of blade teeth.
    Critical safety factor - excessive rim speed can cause
    blade failure and is a primary safety concern.
    
    Safe limits (carbide-tipped):
        - Wood: 40-80 m/s
        - Aluminum: 20-40 m/s
        - Plastic: 30-60 m/s
    """
    
    # Material-specific safe rim speed ranges (m/s)
    SAFE_RANGES = {
        "hardwood": (40, 70),
        "softwood": (50, 80),
        "plywood": (45, 75),
        "mdf": (50, 80),
        "aluminum": (20, 40),
        "acrylic": (30, 60),
        "default": (40, 70)
    }
    
    def calculate(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawCalculatorResult:
        """
        Calculate rim speed safety score.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            SawCalculatorResult with score and rim speed data
        """
        try:
            # Calculate rim speed: v = π * D * RPM / 60 (in m/s)
            rim_speed_m_s = (math.pi * ctx.blade_diameter_mm * ctx.max_rpm) / (1000 * 60)
            
            # Get safe range for material
            material_key = self._get_material_key(ctx.material_id)
            min_safe, max_safe = self.SAFE_RANGES.get(material_key, self.SAFE_RANGES["default"])
            
            # Determine score based on rim speed
            if min_safe <= rim_speed_m_s <= max_safe:
                score = 100.0
                warning = None
            elif rim_speed_m_s < min_safe * 0.7:
                score = 60.0
                warning = f"Rim speed very low ({rim_speed_m_s:.1f} m/s); may cause poor cut quality"
            elif rim_speed_m_s < min_safe:
                score = 80.0
                warning = f"Rim speed below optimal ({rim_speed_m_s:.1f} m/s)"
            elif rim_speed_m_s <= max_safe * 1.1:
                score = 70.0
                warning = f"Rim speed at upper limit ({rim_speed_m_s:.1f} m/s); monitor blade temperature"
            elif rim_speed_m_s <= max_safe * 1.2:
                score = 40.0
                warning = f"Rim speed exceeds safe range ({rim_speed_m_s:.1f} m/s); reduce RPM"
            else:
                score = 10.0
                warning = f"DANGER: Rim speed critically high ({rim_speed_m_s:.1f} m/s); DO NOT operate"
            
            # Calculate recommended RPM for optimal rim speed
            optimal_speed = (min_safe + max_safe) / 2
            recommended_rpm = int((optimal_speed * 1000 * 60) / (math.pi * ctx.blade_diameter_mm))
            
            return SawCalculatorResult(
                calculator_name="rim_speed",
                score=score,
                warning=warning,
                metadata={
                    "rim_speed_m_s": round(rim_speed_m_s, 2),
                    "safe_range_m_s": [min_safe, max_safe],
                    "recommended_rpm": recommended_rpm,
                    "current_rpm": ctx.max_rpm,
                    "blade_diameter_mm": ctx.blade_diameter_mm
                }
            )
            
        except Exception as e:
            return SawCalculatorResult(
                calculator_name="rim_speed",
                score=50.0,
                warning=f"Rim speed calculation error: {str(e)}"
            )
    
    def _get_material_key(self, material_id: str | None) -> str:
        """Map material_id to safe range key."""
        if not material_id:
            return "default"
        
        material_lower = material_id.lower()
        
        if "hardwood" in material_lower or "oak" in material_lower or "maple" in material_lower:
            return "hardwood"
        elif "soft" in material_lower or "pine" in material_lower or "cedar" in material_lower:
            return "softwood"
        elif "plywood" in material_lower or "ply" in material_lower:
            return "plywood"
        elif "mdf" in material_lower:
            return "mdf"
        elif "alum" in material_lower:
            return "aluminum"
        elif "acrylic" in material_lower or "plastic" in material_lower:
            return "acrylic"
        
        return "default"
