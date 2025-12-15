"""
Saw Lab 2.0 - Saw Engine (RMOS Integration)

This module provides the RMOS-facing interface for Saw Lab operations.
Activated when tool_id starts with "saw:" prefix.

Usage in RMOS:
    from toolpath.saw_engine import SawEngine
    
    if tool_id.startswith("saw:"):
        engine = SawEngine()
        result = engine.generate_toolpaths(design, ctx)
"""
from __future__ import annotations

from typing import Dict, Any, Optional

from ..rmos.api_contracts import RmosContext, RmosToolpathPlan, RmosFeasibilityResult
from ..saw_lab import (
    SawLabService,
    SawContext,
    SawDesign,
)

# Import RosetteParamSpec for design conversion
try:
    from ..art_studio.schemas import RosetteParamSpec
except ImportError:
    from ..rmos.api_contracts import RosetteParamSpec


def _is_saw_tool(tool_id: Optional[str]) -> bool:
    """Check if tool_id indicates a saw blade operation."""
    if not tool_id:
        return False
    return tool_id.lower().startswith("saw:")


def _parse_saw_tool_id(tool_id: str) -> Dict[str, Any]:
    """
    Parse saw tool ID to extract blade parameters.
    
    Format: saw:<diameter_inches>_<tooth_count>_<kerf_mm>
    Example: saw:10_24_3.0 → 10" blade, 24 teeth, 3.0mm kerf
    
    Returns:
        Dict with blade parameters
    """
    defaults = {
        "blade_diameter_mm": 254.0,  # 10"
        "tooth_count": 24,
        "blade_kerf_mm": 3.0,
    }
    
    if not tool_id or not tool_id.startswith("saw:"):
        return defaults
    
    try:
        parts = tool_id[4:].split("_")  # Remove "saw:" prefix
        
        if len(parts) >= 1:
            # First part is diameter in inches
            diameter_in = float(parts[0])
            defaults["blade_diameter_mm"] = diameter_in * 25.4
        
        if len(parts) >= 2:
            defaults["tooth_count"] = int(parts[1])
        
        if len(parts) >= 3:
            defaults["blade_kerf_mm"] = float(parts[2])
    
    except (ValueError, IndexError):
        pass  # Return defaults on parse error
    
    return defaults


def _convert_to_saw_context(
    rmos_ctx: RmosContext,
    design: RosetteParamSpec
) -> SawContext:
    """
    Convert RMOS context to Saw Lab context.
    
    Maps RMOS fields to saw-specific parameters.
    """
    # Parse tool ID for blade parameters
    blade_params = _parse_saw_tool_id(rmos_ctx.tool_id)
    
    # Stock thickness from design or default
    stock_thickness = getattr(design, "stock_thickness_mm", 25.0)
    if not stock_thickness:
        stock_thickness = 25.0
    
    return SawContext(
        blade_diameter_mm=blade_params["blade_diameter_mm"],
        blade_kerf_mm=blade_params["blade_kerf_mm"],
        tooth_count=blade_params["tooth_count"],
        max_rpm=5000,  # Default CNC saw RPM
        material_id=rmos_ctx.material_id,
        stock_thickness_mm=stock_thickness,
        feed_rate_mm_per_min=3000.0,  # Default feed
        use_dust_collection=True,
    )


def _convert_to_saw_design(design: RosetteParamSpec) -> SawDesign:
    """
    Convert rosette design to saw cut design.
    
    Maps rosette parameters to saw-specific cut parameters.
    """
    # Use outer diameter as cut length
    cut_length = getattr(design, "outer_diameter_mm", 300.0)
    if not cut_length:
        cut_length = 300.0
    
    # Ring count maps to repeat count (multiple cuts)
    repeat_count = getattr(design, "ring_count", 1)
    if not repeat_count or repeat_count < 1:
        repeat_count = 1
    
    # Pattern type can indicate cut type
    pattern = getattr(design, "pattern_type", "crosscut")
    cut_type = "crosscut" if pattern in ["radial", "simple"] else "rip"
    
    return SawDesign(
        cut_length_mm=cut_length,
        cut_type=cut_type,
        repeat_count=repeat_count,
        miter_angle_deg=0.0,
        bevel_angle_deg=0.0,
    )


class SawEngine:
    """
    RMOS-facing interface for Saw Lab operations.
    
    Provides methods that match RMOS service signatures but delegate
    to Saw Lab implementation when tool_id indicates saw mode.
    """
    
    def __init__(self):
        self._saw_service = SawLabService()
    
    def check_feasibility(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> RmosFeasibilityResult:
        """
        Check feasibility for saw operation.
        
        Converts RMOS types to Saw Lab types, runs calculators,
        then converts result back to RMOS format.
        """
        # Convert to saw-specific types
        saw_ctx = _convert_to_saw_context(ctx, design)
        saw_design = _convert_to_saw_design(design)
        
        # Get saw feasibility result
        saw_result = self._saw_service.check_feasibility(saw_design, saw_ctx)
        
        # Convert to RMOS format
        # Map SawRiskLevel to RMOS risk_bucket string
        risk_bucket = saw_result.risk_level.value
        
        # Convert calculator results to dict format
        calc_results = {}
        for name, result in saw_result.calculator_results.items():
            calc_results[name] = {
                "score": result.score,
                "warning": result.warning,
                **result.metadata
            }
        
        return RmosFeasibilityResult(
            score=saw_result.score,
            risk_bucket=risk_bucket,
            warnings=saw_result.warnings,
            efficiency=saw_result.efficiency,
            estimated_cut_time_seconds=saw_result.estimated_cut_time_seconds,
            calculator_results=calc_results
        )
    
    def generate_toolpaths(
        self,
        design: RosetteParamSpec,
        ctx: RmosContext
    ) -> RmosToolpathPlan:
        """
        Generate toolpaths for saw operation.
        
        Converts RMOS types to Saw Lab types, generates toolpaths,
        then converts result back to RMOS format.
        """
        # Convert to saw-specific types
        saw_ctx = _convert_to_saw_context(ctx, design)
        saw_design = _convert_to_saw_design(design)
        
        # Generate saw toolpaths
        saw_plan = self._saw_service.generate_toolpaths(saw_design, saw_ctx)
        
        # Convert moves to RMOS format (list of dicts)
        toolpath_moves = []
        for move in saw_plan.moves:
            move_dict = {"code": move.code}
            if move.x is not None:
                move_dict["x"] = move.x
            if move.y is not None:
                move_dict["y"] = move.y
            if move.z is not None:
                move_dict["z"] = move.z
            if move.f is not None:
                move_dict["f"] = move.f
            if move.comment:
                move_dict["comment"] = move.comment
            toolpath_moves.append(move_dict)
        
        return RmosToolpathPlan(
            toolpaths=toolpath_moves,
            total_length_mm=saw_plan.total_length_mm,
            estimated_time_seconds=saw_plan.estimated_time_seconds,
            warnings=saw_plan.warnings
        )


# Module-level helper functions for service integration
def is_saw_mode(ctx: RmosContext) -> bool:
    """Check if context indicates saw mode operation."""
    return _is_saw_tool(ctx.tool_id)


def get_saw_engine() -> SawEngine:
    """Get Saw Engine instance."""
    return SawEngine()


# =============================================================================
# NEW: Saw Toolpath Builder 2.0 Integration with Path Planner 2.1
# =============================================================================

from ..saw_lab.path_planner import (
    SawCutContext,
    SawCutPlan,
    SawBladeSpec,
    SawMaterialSpec,
    SawPlannerConfig,
    plan_saw_cuts_for_board,
)


def _build_saw_cut_context_from_rmos(
    design: RosetteParamSpec,
    ctx: RmosContext,
) -> SawCutContext:
    """
    Build SawCutContext from RMOS design and context.
    
    Maps rosette ring parameters to desired piece lengths for the saw planner.
    """
    # Parse blade info from tool_id
    blade_params = _parse_saw_tool_id(ctx.tool_id)
    
    blade = SawBladeSpec(
        kerf_mm=blade_params.get("blade_kerf_mm", 3.0),
        diameter_mm=blade_params.get("blade_diameter_mm", 254.0),
        tooth_count=blade_params.get("tooth_count", 24),
    )
    
    material = SawMaterialSpec(
        material_id=ctx.material_id,
        hardness="MEDIUM",  # Could be derived from material preset
    )
    
    # Extract desired piece lengths from ring params
    # Each ring width becomes a piece length
    desired_lengths: list[float] = []
    ring_params = getattr(design, "ring_params", []) or []
    for rp in ring_params:
        width = getattr(rp, "width_mm", None)
        if width and width > 0:
            desired_lengths.append(float(width))
    
    # If no ring params, use outer - inner diameter as single piece
    if not desired_lengths:
        outer = getattr(design, "outer_diameter_mm", 100.0) or 100.0
        inner = getattr(design, "inner_diameter_mm", 20.0) or 20.0
        desired_lengths.append(outer - inner)
    
    # Stock length: sum of pieces + generous allowance
    total_pieces = sum(desired_lengths)
    stock_length = total_pieces + (len(desired_lengths) * blade.kerf_mm) + 50.0  # 50mm extra
    
    return SawCutContext(
        blade=blade,
        material=material,
        stock_length_mm=stock_length,
        desired_piece_lengths_mm=desired_lengths,
    )


def _map_saw_cut_plan_to_rmos(
    saw_plan: SawCutPlan,
) -> RmosToolpathPlan:
    """
    Map SawCutPlan from 2.1 planner to RmosToolpathPlan.
    
    Converts cut operations to a toolpath representation.
    """
    toolpaths: list[dict] = []
    
    for op in saw_plan.operations:
        toolpaths.append({
            "op_id": op.op_id,
            "sequence": op.sequence_index,
            "type": op.cut_type,
            "start_mm": op.start_offset_mm,
            "length_mm": op.cut_length_mm,
            "kerf_mm": op.kerf_mm,
            "description": op.description,
        })
    
    # Estimate time based on cut lengths (rough approximation)
    total_cut_length = sum(op.cut_length_mm for op in saw_plan.operations)
    feed_rate = 3000.0  # mm/min default
    estimated_time = (total_cut_length / feed_rate) * 60.0  # seconds
    
    return RmosToolpathPlan(
        toolpaths=toolpaths,
        total_length_mm=total_cut_length,
        estimated_time_seconds=estimated_time,
        warnings=saw_plan.warnings,
    )


def plan_saw_toolpaths_for_design(
    design: RosetteParamSpec,
    ctx: RmosContext,
    planner_cfg: Optional[SawPlannerConfig] = None,
) -> RmosToolpathPlan:
    """
    Saw Toolpath Builder 2.0 - Main entry point.
    
    Uses the 2.1 path planner to generate cut plans for RMOS designs.
    
    Flow:
        RosetteParamSpec + RmosContext
            → SawCutContext
            → plan_saw_cuts_for_board()
            → SawCutPlan
            → RmosToolpathPlan
    
    Args:
        design: Rosette design parameters
        ctx: RMOS manufacturing context
        planner_cfg: Optional planner configuration (trim, scrap, ordering)
    
    Returns:
        RmosToolpathPlan with cut operations and statistics
    """
    # Build saw cut context from RMOS inputs
    cut_ctx = _build_saw_cut_context_from_rmos(design, ctx)
    
    # Use 2.1 planner
    saw_plan = plan_saw_cuts_for_board(
        cut_ctx=cut_ctx,
        config=None,  # Use defaults
        planner_cfg=planner_cfg,
    )
    
    # Check feasibility
    if not saw_plan.is_feasible:
        return RmosToolpathPlan(
            toolpaths=[],
            total_length_mm=0.0,
            estimated_time_seconds=0.0,
            warnings=saw_plan.warnings + ["Saw cut plan is not feasible"],
        )
    
    # Map to RMOS format
    return _map_saw_cut_plan_to_rmos(saw_plan)

