"""
Saw Lab 2.0 - CNC Saw Blade Integration for RMOS

This module integrates saw blade operations as a first-class mode within
the RMOS orchestration system. Activated when tool_id starts with "saw:".

Key Components:
    - models.py: Pydantic models for saw operations
    - geometry.py: Geometry computation for saw paths
    - path_planner.py: Toolpath planning for saw cuts
    - toolpath_builder.py: G-code generation for saw operations
    - risk_evaluator.py: Safety risk assessment for saw operations
    - calculators/: Material-specific feasibility calculations
        - saw_heat.py: Heat buildup calculations
        - saw_deflection.py: Blade deflection analysis
        - saw_rimspeed.py: Rim speed safety checks
        - saw_bite_load.py: Tooth bite load analysis
        - saw_kickback.py: Kickback risk evaluation

Usage:
    from saw_lab import SawLabService, SawContext
    
    ctx = SawContext(
        blade_diameter_mm=254.0,
        blade_kerf_mm=3.0,
        tooth_count=24,
        max_rpm=5000
    )
    
    service = SawLabService()
    feasibility = service.check_feasibility(design, ctx)
    toolpaths = service.generate_toolpaths(design, ctx)
"""

from .models import (
    SawContext,
    SawDesign,
    SawFeasibilityResult,
    SawToolpathPlan,
    SawRiskLevel,
)
from .path_planner import (
    SawPathPlanner,
    # NEW: Saw Path Planner 2.1 exports
    SawPlannerConfig,
    SawCutOperation,
    SawCutPlan,
    SawCutContext,
    SawBladeSpec,
    SawMaterialSpec,
    SawLabConfig,
    plan_saw_cuts_for_board,
)
from .toolpath_builder import SawToolpathBuilder
from .risk_evaluator import SawRiskEvaluator
from .geometry import SawGeometryEngine

# Convenience imports for calculator bundle
from .calculators import FeasibilityCalculatorBundle


class SawLabService:
    """
    Main entry point for Saw Lab operations within RMOS.
    
    Provides:
        - Feasibility analysis for saw cuts
        - Toolpath generation for saw operations
        - Risk evaluation for safety
    """
    
    def __init__(self):
        self._path_planner = SawPathPlanner()
        self._toolpath_builder = SawToolpathBuilder()
        self._risk_evaluator = SawRiskEvaluator()
        self._geometry_engine = SawGeometryEngine()
        self._calculator_bundle = FeasibilityCalculatorBundle()
    
    def check_feasibility(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawFeasibilityResult:
        """
        Check if saw cut is feasible and safe.
        
        Args:
            design: Saw cut design parameters
            ctx: Saw blade and machine context
        
        Returns:
            SawFeasibilityResult with score, risk level, warnings
        """
        return self._calculator_bundle.evaluate(design, ctx)
    
    def generate_toolpaths(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawToolpathPlan:
        """
        Generate toolpaths for saw cut operation.
        
        Args:
            design: Saw cut design parameters
            ctx: Saw blade and machine context
        
        Returns:
            SawToolpathPlan with moves, length, time estimate
        """
        # Generate geometry
        paths = self._path_planner.plan_cuts(design, ctx)
        
        # Convert to toolpath moves
        toolpaths = self._toolpath_builder.build(paths, ctx)
        
        return toolpaths
    
    def evaluate_risk(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawRiskLevel:
        """
        Evaluate safety risk for saw operation.
        
        Args:
            design: Saw cut design parameters
            ctx: Saw blade and machine context
        
        Returns:
            SawRiskLevel enum (GREEN, YELLOW, RED)
        """
        return self._risk_evaluator.evaluate(design, ctx)


__all__ = [
    "SawLabService",
    "SawContext",
    "SawDesign",
    "SawFeasibilityResult",
    "SawToolpathPlan",
    "SawRiskLevel",
    "SawPathPlanner",
    "SawToolpathBuilder",
    "SawRiskEvaluator",
    "SawGeometryEngine",
    "FeasibilityCalculatorBundle",
    # NEW: Saw Path Planner 2.1 exports
    "SawPlannerConfig",
    "SawCutOperation",
    "SawCutPlan",
    "SawCutContext",
    "SawBladeSpec",
    "SawMaterialSpec",
    "SawLabConfig",
    "plan_saw_cuts_for_board",
]


def include_decision_intel_router(app) -> None:
    """
    Call from app.main after Saw routers are mounted.
    Kept here so Saw Lab owns its own router wiring.
    """
    from .decision_intelligence_router import router as decision_intel_router
    from .decision_intel_apply_router import router as decision_intel_apply_router

    app.include_router(decision_intel_router)
    app.include_router(decision_intel_apply_router)
