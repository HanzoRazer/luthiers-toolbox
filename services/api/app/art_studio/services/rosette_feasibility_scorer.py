"""
Rosette Feasibility Scorer - Art Studio Wrapper

Wraps the RMOS feasibility scorer to produce Art Studio compatible summaries.
"""

from typing import Optional
from ...rmos.api_contracts import RmosContext, RiskBucket
from ...rmos.feasibility_scorer import score_design_feasibility
from ..schemas.rosette_params import RosetteParamSpec
from ..schemas.rosette_feasibility import RosetteFeasibilitySummary


# Default context specs for standalone feasibility checks
class MaterialSpec:
    """Minimal material specification."""
    def __init__(
        self,
        material_id: str,
        name: str,
        material_class: str,
    ):
        self.material_id = material_id
        self.name = name
        self.material_class = material_class


class ToolSpec:
    """Minimal tool specification."""
    def __init__(
        self,
        tool_id: str,
        diameter_mm: float,
        flutes: int,
        tool_material: str,
        stickout_mm: float,
    ):
        self.tool_id = tool_id
        self.diameter_mm = diameter_mm
        self.flutes = flutes
        self.tool_material = tool_material
        self.stickout_mm = stickout_mm


def estimate_rosette_feasibility(
    *,
    spec: RosetteParamSpec,
    default_material: Optional[MaterialSpec] = None,
    default_tool: Optional[ToolSpec] = None,
) -> RosetteFeasibilitySummary:
    """
    Estimate feasibility for a rosette design.

    Returns a lightweight summary suitable for batch preview operations.
    """
    # Build context from specs
    ctx = RmosContext(
        material_id=default_material.material_id if default_material else "default-ebony",
        tool_id=default_tool.tool_id if default_tool else "default-vbit",
    )

    # Call the main feasibility scorer
    result = score_design_feasibility(spec, ctx, workflow_mode="design_first")

    # Convert to summary format
    return RosetteFeasibilitySummary(
        overall_score=result.score,
        risk_bucket=result.risk_bucket,
        material_efficiency=result.efficiency or 85.0,
        estimated_cut_time_min=(result.estimated_cut_time_seconds or 300.0) / 60.0,
        warnings=result.warnings or [],
    )
