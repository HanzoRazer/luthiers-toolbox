from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .schemas_decision_intelligence import TuningDelta


class LatestApprovedDeltaResponse(BaseModel):
    """
    Advisory payload: what the system recommends applying on the next plan for (tool, material).
    This does NOT modify any plan automatically.
    """

    tool_id: str
    material_id: str
    decision_artifact_id: Optional[str] = None
    effective_delta: Optional[TuningDelta] = None
    note: str = "No approved tuning decision found for this tool/material."


class StampPlanIntelLinkRequest(BaseModel):
    """
    Create a governed linkage artifact so the plan can be traced to the decision intel used.
    """

    batch_plan_artifact_id: str
    tool_id: str
    material_id: str
    decision_artifact_id: str
    effective_delta: TuningDelta
    stamped_by: str = "operator"
    note: Optional[str] = None


class StampPlanIntelLinkResponse(BaseModel):
    artifact_id: str
    batch_plan_artifact_id: str
    decision_artifact_id: str
    applied_delta: TuningDelta
    wrote_overrides_jsonl: bool = False
