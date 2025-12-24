"""
Rosette Feasibility Routes - Bundle 31.0.27

API endpoints for rosette feasibility preview with RMOS run artifact persistence.
"""

from typing import List, Optional
from fastapi import APIRouter

from ..schemas.rosette_params import RosetteParamSpec
from ..schemas.rosette_feasibility import (
    RosetteFeasibilitySummary,
    RosetteFeasibilityBatchRequest,
    RosetteFeasibilityBatchResponse,
)
from ..services.rosette_feasibility_scorer import (
    estimate_rosette_feasibility,
    MaterialSpec,
    ToolSpec,
)
from ...services.art_studio_run_service import create_art_studio_feasibility_run


router = APIRouter(prefix="/rosette/feasibility", tags=["art-studio", "feasibility"])


# Default material/tool for standalone feasibility checks
default_material = MaterialSpec(
    material_id="default-ebony",
    name="Ebony",
    material_class="hardwood",
)
default_tool = ToolSpec(
    tool_id="default-vbit",
    diameter_mm=6.0,
    flutes=2,
    tool_material="carbide",
    stickout_mm=25.0,
)


@router.post("/batch", response_model=RosetteFeasibilityBatchResponse)
async def batch_feasibility(req: RosetteFeasibilityBatchRequest):
    """
    Evaluate feasibility for a batch of rosette specs.

    Each spec is evaluated and persisted as a RunArtifact for audit trail.
    Returns lightweight summaries with run_id references.
    """
    summaries: List[RosetteFeasibilitySummary] = []

    for idx, spec in enumerate(req.specs):
        # Get suggestion_id if provided
        suggestion_id = None
        if req.suggestion_ids and idx < len(req.suggestion_ids):
            suggestion_id = req.suggestion_ids[idx]

        # Estimate feasibility
        summary = estimate_rosette_feasibility(
            spec=spec,
            default_material=default_material,
            default_tool=default_tool,
        )

        # Persist as RunArtifact
        run_artifact = create_art_studio_feasibility_run(
            request_summary={
                "suggestion_id": suggestion_id,
                "outer_diameter_mm": spec.outer_diameter_mm,
                "inner_diameter_mm": spec.inner_diameter_mm,
                "ring_count": len(spec.ring_params),
            },
            feasibility={
                "overall_score": summary.overall_score,
                "risk_bucket": summary.risk_bucket.value,
                "material_efficiency": summary.material_efficiency,
                "estimated_cut_time_min": summary.estimated_cut_time_min,
                "warnings": summary.warnings,
            },
            tool_id=default_tool.tool_id,
        )

        # Attach run_id and suggestion_id to summary
        summary.run_id = run_artifact.run_id
        summary.suggestion_id = suggestion_id

        summaries.append(summary)

    return RosetteFeasibilityBatchResponse(summaries=summaries)


@router.post("/single", response_model=RosetteFeasibilitySummary)
async def single_feasibility(spec: RosetteParamSpec, suggestion_id: Optional[str] = None):
    """
    Evaluate feasibility for a single rosette spec.

    Persists as a RunArtifact and returns summary with run_id.
    """
    summary = estimate_rosette_feasibility(
        spec=spec,
        default_material=default_material,
        default_tool=default_tool,
    )

    run_artifact = create_art_studio_feasibility_run(
        request_summary={
            "suggestion_id": suggestion_id,
            "outer_diameter_mm": spec.outer_diameter_mm,
            "inner_diameter_mm": spec.inner_diameter_mm,
            "ring_count": len(spec.ring_params),
        },
        feasibility={
            "overall_score": summary.overall_score,
            "risk_bucket": summary.risk_bucket.value,
            "material_efficiency": summary.material_efficiency,
            "estimated_cut_time_min": summary.estimated_cut_time_min,
            "warnings": summary.warnings,
        },
        tool_id=default_tool.tool_id,
    )

    summary.run_id = run_artifact.run_id
    summary.suggestion_id = suggestion_id

    return summary
