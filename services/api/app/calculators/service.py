"""
RMOS 2.0 Calculator Service
Unified facade for chipload, heat, deflection, rim speed, and BOM calculators.
"""
from typing import Dict, Any
from ..rmos.api_contracts import RmosContext, RmosBomResult

try:
    from ..art_studio.schemas import RosetteParamSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    from ..rmos.api_contracts import RosetteParamSpec


class CalculatorService:
    """
    Unified calculator facade providing manufacturing feasibility checks.
    Each calculator returns dict with 'score' (0-100) and optional 'warning' string.
    """
    
    def check_chipload_feasibility(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> Dict[str, Any]:
        """
        Check if chipload is within acceptable range for material/tool.
        
        Returns:
            {'score': 0-100, 'warning': str (optional), 'chipload_mm': float}
        """
        # Placeholder implementation
        # Real implementation would query tool/material databases
        try:
            # Assume typical spindle speed and feed rate
            spindle_rpm = 18000
            feed_rate_mm_per_min = 1200
            flute_count = 2
            
            # Chipload = feed_rate / (spindle_rpm * flute_count)
            chipload_mm = feed_rate_mm_per_min / (spindle_rpm * flute_count)
            
            # Acceptable range: 0.05-0.15 mm for wood
            if 0.05 <= chipload_mm <= 0.15:
                score = 100.0
                warning = None
            elif chipload_mm < 0.05:
                score = 60.0
                warning = f"Chipload too low ({chipload_mm:.3f} mm); may cause burning"
            else:
                score = 50.0
                warning = f"Chipload too high ({chipload_mm:.3f} mm); may cause tear-out"
            
            return {
                "score": score,
                "chipload_mm": round(chipload_mm, 4),
                "warning": warning
            }
        except Exception as e:
            return {"score": 50.0, "warning": f"Chipload calculation error: {str(e)}"}
    
    def check_heat_dissipation(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> Dict[str, Any]:
        """
        Check if heat dissipation is adequate for cut depth/feed rate.
        
        Returns:
            {'score': 0-100, 'warning': str (optional), 'heat_index': float}
        """
        # Placeholder implementation
        try:
            # Heat index based on ring count and pattern complexity
            heat_index = design.ring_count * 1.5
            
            if heat_index < 10:
                score = 100.0
                warning = None
            elif heat_index < 20:
                score = 75.0
                warning = "Moderate heat generation; consider coolant"
            else:
                score = 40.0
                warning = "High heat generation; coolant required"
            
            return {
                "score": score,
                "heat_index": round(heat_index, 2),
                "warning": warning
            }
        except Exception as e:
            return {"score": 50.0, "warning": f"Heat calculation error: {str(e)}"}
    
    def check_tool_deflection(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> Dict[str, Any]:
        """
        Check if tool deflection is acceptable for required cut depth.
        
        Returns:
            {'score': 0-100, 'warning': str (optional), 'deflection_mm': float}
        """
        # Placeholder implementation
        try:
            # Assume 6mm tool, 25mm stickout, typical cut depth
            tool_diameter_mm = 6.0
            stickout_mm = 25.0
            cut_depth_mm = 3.0
            
            # Simplified deflection: proportional to (stickout^3 / diameter^4)
            deflection_factor = (stickout_mm ** 3) / (tool_diameter_mm ** 4)
            deflection_mm = deflection_factor * cut_depth_mm / 10000
            
            if deflection_mm < 0.02:
                score = 100.0
                warning = None
            elif deflection_mm < 0.05:
                score = 70.0
                warning = f"Moderate deflection ({deflection_mm:.3f} mm); reduce cut depth"
            else:
                score = 30.0
                warning = f"Excessive deflection ({deflection_mm:.3f} mm); use larger tool or reduce stickout"
            
            return {
                "score": score,
                "deflection_mm": round(deflection_mm, 4),
                "warning": warning
            }
        except Exception as e:
            return {"score": 50.0, "warning": f"Deflection calculation error: {str(e)}"}
    
    def check_rim_speed(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> Dict[str, Any]:
        """
        Check if rim speed (surface speed at outer diameter) is safe.
        
        Returns:
            {'score': 0-100, 'warning': str (optional), 'rim_speed_m_per_min': float}
        """
        # Placeholder implementation
        try:
            # Assume typical spindle speed
            spindle_rpm = 18000
            
            # Rim speed = π * diameter * RPM / 1000 (convert mm to m)
            rim_speed_m_per_min = (3.14159 * design.outer_diameter_mm * spindle_rpm) / 1000
            
            # Safe range for wood: 30-100 m/min
            if 30 <= rim_speed_m_per_min <= 100:
                score = 100.0
                warning = None
            elif rim_speed_m_per_min < 30:
                score = 80.0
                warning = f"Low rim speed ({rim_speed_m_per_min:.1f} m/min); consider higher RPM"
            else:
                score = 60.0
                warning = f"High rim speed ({rim_speed_m_per_min:.1f} m/min); reduce RPM to prevent burning"
            
            return {
                "score": score,
                "rim_speed_m_per_min": round(rim_speed_m_per_min, 2),
                "warning": warning
            }
        except Exception as e:
            return {"score": 50.0, "warning": f"Rim speed calculation error: {str(e)}"}
    
    def check_geometry_complexity(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> Dict[str, Any]:
        """
        Check if geometry complexity is within machine capability.
        
        Returns:
            {'score': 0-100, 'warning': str (optional), 'complexity_index': float}
        """
        # Placeholder implementation
        try:
            # Complexity based on ring count and pattern type
            base_complexity = design.ring_count
            
            # Adjust for pattern type (herringbone more complex than simple)
            pattern_multiplier = {
                "herringbone": 1.5,
                "radial": 1.0,
                "spiral": 1.3,
                "hexagonal": 1.2
            }.get(design.pattern_type, 1.0)
            
            complexity_index = base_complexity * pattern_multiplier
            
            if complexity_index < 5:
                score = 100.0
                warning = None
            elif complexity_index < 10:
                score = 80.0
                warning = "Moderate complexity; verify toolpath before cutting"
            else:
                score = 60.0
                warning = "High complexity; extended machining time expected"
            
            return {
                "score": score,
                "complexity_index": round(complexity_index, 2),
                "warning": warning
            }
        except Exception as e:
            return {"score": 50.0, "warning": f"Complexity calculation error: {str(e)}"}
    
    def compute_bom(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> RmosBomResult:
        """
        Compute Bill of Materials for design.
        
        Returns:
            RmosBomResult with material area, tool IDs, waste estimate
        """
        try:
            # Calculate material area (outer circle)
            material_required_mm2 = 3.14159 * (design.outer_diameter_mm / 2) ** 2
            
            # Typical tools for rosette cutting
            tool_ids = ["end_mill_6mm", "v_bit_60deg"]
            
            # Waste estimate (inner circle + kerf)
            inner_area = 3.14159 * (design.inner_diameter_mm / 2) ** 2
            waste_percent = (inner_area / material_required_mm2) * 100
            
            notes = [
                f"Material: {material_required_mm2:.1f} mm²",
                f"Waste: {waste_percent:.1f}%",
                f"Tools required: {len(tool_ids)}"
            ]
            
            return RmosBomResult(
                material_required_mm2=round(material_required_mm2, 2),
                tool_ids=tool_ids,
                estimated_waste_percent=round(waste_percent, 2),
                notes=notes
            )
        except Exception as e:
            return RmosBomResult(
                material_required_mm2=0.0,
                tool_ids=[],
                estimated_waste_percent=0.0,
                notes=[f"BOM calculation error: {str(e)}"]
            )
