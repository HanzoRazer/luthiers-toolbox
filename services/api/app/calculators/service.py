"""
RMOS 2.0 Calculator Service
Unified facade for chipload, heat, deflection, rim speed, BOM, and bracing calculators.

Supports two modes:
    - Router mode (default): For rosette/router operations
    - Saw mode: Activated when tool_id starts with "saw:" prefix
"""
from typing import Dict, Any, Optional
from math import pi
from ..rmos.api_contracts import RmosContext, RmosBomResult, RmosFeasibilityResult
from ..data_registry import Registry, Edition

try:
    from ..art_studio.schemas import RosetteParamSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    from ..rmos.api_contracts import RosetteParamSpec

# Bracing calculator facade
from . import bracing_calc


def _is_saw_tool(tool_id: Optional[str]) -> bool:
    """Check if tool_id indicates a saw blade operation."""
    if not tool_id:
        return False
    return tool_id.lower().startswith("saw:")


class CalculatorService:
    """
    Unified calculator facade providing manufacturing feasibility checks.
    Each calculator returns dict with 'score' (0-100) and optional 'warning' string.
    
    Supports saw mode when tool_id starts with "saw:" prefix.
    """
    
    def __init__(self, edition: str = "pro"):
        """
        Initialize calculator service with data registry.
        
        Args:
            edition: Product edition (express, pro, enterprise)
        """
        self.edition = edition
        self.registry = Registry(edition=edition)
    
    def evaluate_feasibility(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> RmosFeasibilityResult:
        """
        Evaluate overall feasibility, branching on saw vs router mode.
        
        Args:
            design: Design parameters
            ctx: Manufacturing context
        
        Returns:
            RmosFeasibilityResult with score, risk, warnings
        """
        if _is_saw_tool(ctx.tool_id):
            return self._evaluate_saw_feasibility(design, ctx)
        return self._evaluate_router_feasibility(design, ctx)
    
    def _evaluate_saw_feasibility(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> RmosFeasibilityResult:
        """Evaluate feasibility using Saw Lab calculators."""
        try:
            from ..toolpath.saw_engine import get_saw_engine
            engine = get_saw_engine()
            return engine.check_feasibility(design, ctx)
        except ImportError as e:
            return RmosFeasibilityResult(
                score=50.0,
                risk_bucket="YELLOW",
                warnings=[f"Saw Lab module not available: {str(e)}"],
                efficiency=0.0,
                estimated_cut_time_seconds=0.0,
                calculator_results={}
            )
    
    def _evaluate_router_feasibility(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> RmosFeasibilityResult:
        """Evaluate feasibility using router calculators."""
        # Run all router calculators
        results = {
            "chipload": self.check_chipload_feasibility(design, ctx),
            "heat": self.check_heat_dissipation(design, ctx),
            "deflection": self.check_tool_deflection(design, ctx),
            "rim_speed": self.check_rim_speed(design, ctx),
            "geometry": self.check_geometry_complexity(design, ctx),
        }
        
        # Weighted aggregation
        weights = {
            "chipload": 0.30,
            "heat": 0.25,
            "deflection": 0.20,
            "rim_speed": 0.15,
            "geometry": 0.10,
        }
        
        weighted_sum = sum(
            results[k]["score"] * weights.get(k, 0.1)
            for k in results
        )
        
        # Collect warnings
        warnings = [
            r["warning"] for r in results.values()
            if r.get("warning")
        ]
        
        # Determine risk bucket
        min_score = min(r["score"] for r in results.values())
        if min_score < 30:
            risk_bucket = "RED"
        elif weighted_sum >= 80:
            risk_bucket = "GREEN"
        elif weighted_sum >= 50:
            risk_bucket = "YELLOW"
        else:
            risk_bucket = "RED"
        
        # Estimate efficiency
        efficiency = min(100.0, weighted_sum * 1.1)
        
        return RmosFeasibilityResult(
            score=round(weighted_sum, 1),
            risk_bucket=risk_bucket,
            warnings=warnings,
            efficiency=round(efficiency, 1),
            estimated_cut_time_seconds=0.0,  # Calculated elsewhere
            calculator_results=results
        )
    
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
        # Get empirical limits from registry (Pro edition only)
        try:
            # Default values for Express edition (no empirical data)
            spindle_rpm = 18000
            feed_rate_mm_per_min = 1200
            flute_count = 2
            
            # If Pro/Enterprise, get empirical limits for material
            if self.edition in ["pro", "enterprise"] and ctx.material_id:
                material_id = ctx.material_id or "mahogany_honduran"
                try:
                    limits_data = self.registry.get_empirical_limits()
                    if limits_data and "limits" in limits_data:
                        limit = limits_data["limits"].get(material_id, {})
                        if limit:
                            # Use empirical roughing max feed as baseline
                            feed_rate_mm_per_min = limit.get("feed_clamp", {}).get("roughing_max_mm_min", 1200) * 0.5
                            # Use optimal RPM from speed clamp
                            speed_clamp = limit.get("speed_clamp", {})
                            min_rpm = speed_clamp.get("min_rpm", 12000)
                            max_rpm = speed_clamp.get("max_rpm", 24000)
                            spindle_rpm = (min_rpm + max_rpm) // 2  # Use midpoint
                except AttributeError:
                    # Registry method not available - use defaults
                    pass
                except Exception as e:
                    # Log unexpected errors but continue with defaults
                    print(f"Warning: Failed to get empirical limits: {type(e).__name__}: {e}")
                    pass
            
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
            import traceback
            print(f"ERROR in check_chipload_feasibility: {type(e).__name__}: {e}")
            traceback.print_exc()
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
        # Get optimal spindle speed from registry (Pro edition only)
        try:
            spindle_rpm = 18000  # Default for Express
            
            # If Pro/Enterprise, get from empirical limits
            if self.edition in ["pro", "enterprise"] and ctx.material_id:
                material_id = ctx.material_id or "mahogany_honduran"
                try:
                    limits_data = self.registry.get_empirical_limits()
                    if limits_data and "limits" in limits_data:
                        limit = limits_data["limits"].get(material_id, {})
                        if limit:
                            speed_clamp = limit.get("speed_clamp", {})
                            min_rpm = speed_clamp.get("min_rpm", 12000)
                            max_rpm = speed_clamp.get("max_rpm", 24000)
                            spindle_rpm = (min_rpm + max_rpm) // 2
                except Exception:
                    pass  # Fall back to default
            
            # Rim speed = π * diameter * RPM / 1000 (convert mm to m)
            rim_speed_m_per_min = (pi * design.outer_diameter_mm * spindle_rpm) / 1000
            
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
            material_required_mm2 = pi * (design.outer_diameter_mm / 2) ** 2
            
            # Typical tools for rosette cutting
            tool_ids = ["end_mill_6mm", "v_bit_60deg"]
            
            # Waste estimate (inner circle + kerf)
            inner_area = pi * (design.inner_diameter_mm / 2) ** 2
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


# --- Bracing calculators (Art Studio integration) ---


def calculate_bracing_section(
    data: bracing_calc.BracingCalcInput,
) -> bracing_calc.BraceSectionResult:
    """
    Public façade for bracing section calculations.

    This is the function RMOS, Art Studio, or any other subsystem
    should call when they need bracing properties.

    It delegates to calculators.bracing_calc and ultimately to the
    legacy pipelines.bracing.bracing_calc implementation.
    """
    return bracing_calc.calculate_brace_section(data)


def estimate_bracing_mass_grams(
    data: bracing_calc.BracingCalcInput,
) -> float:
    """
    Public façade for bracing mass estimation.

    Returns the estimated brace mass in grams, as computed by the
    underlying bracing physics module.
    """
    return bracing_calc.estimate_mass_grams(data)


# ---------------------------------------------------------------------------
# Public API Wrappers (Wave 17→18 Integration)
# ---------------------------------------------------------------------------
# These thin wrappers provide top-level functions for RMOS feasibility API
# while delegating to the CalculatorService class for actual logic.
# ---------------------------------------------------------------------------

def compute_chipload_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate chipload risk for given design and context.
    
    Args:
        request: {
            "design": RosetteParamSpec or dict,
            "context": RmosContext or dict,
        }
    
    Returns:
        {
            "score": float (0-100),
            "risk": str ("GREEN"|"YELLOW"|"RED"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    return service.check_chipload_feasibility(design, ctx)


def compute_heat_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate heat dissipation risk for given design and context.
    
    Args:
        request: Same as compute_chipload_risk
    
    Returns:
        {
            "score": float (0-100),
            "risk": str ("GREEN"|"YELLOW"|"RED"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    return service.check_heat_dissipation(design, ctx)


def compute_deflection_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate tool deflection risk for given design and context.
    
    Args:
        request: Same as compute_chipload_risk
    
    Returns:
        {
            "score": float (0-100),
            "risk": str ("GREEN"|"YELLOW"|"RED"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    return service.check_tool_deflection(design, ctx)


def compute_rimspeed_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate rim speed safety for given design and context.
    
    Args:
        request: Same as compute_chipload_risk
    
    Returns:
        {
            "score": float (0-100),
            "risk": str ("GREEN"|"YELLOW"|"RED"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    return service.check_rim_speed(design, ctx)


def compute_bom_efficiency(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate bill-of-materials efficiency for given design and context.
    
    Note: BOM calculator is still under development.
    Returns conservative score until fully implemented.
    
    Args:
        request: Same as compute_chipload_risk
    
    Returns:
        {
            "score": float (0-100, currently 75.0 default),
            "risk": str ("YELLOW"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    
    # TODO: Implement full BOM calculator
    # For now, return conservative score
    return {
        "score": 75.0,
        "risk": "YELLOW",
        "warnings": ["BOM calculator not fully implemented - using conservative score"],
        "details": {
            "design_type": getattr(design, "design_type", "unknown"),
            "model_id": ctx.model_id if ctx else "unknown"
        }
    }
