from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SawBatchLinkSummary(BaseModel):
    """
    Minimal "link graph" summary for UI.
    Lets the frontend jump between spec/plan/decision/execution without chasing IDs manually.
    """

    batch_label: Optional[str] = None
    session_id: Optional[str] = None

    # Primary nodes (newest-first where applicable)
    latest_spec_artifact_id: Optional[str] = None
    latest_plan_artifact_id: Optional[str] = None
    latest_decision_artifact_id: Optional[str] = None
    latest_execution_artifact_id: Optional[str] = None

    # Optional lists (bounded)
    spec_artifact_ids: List[str] = Field(default_factory=list)
    plan_artifact_ids: List[str] = Field(default_factory=list)
    decision_artifact_ids: List[str] = Field(default_factory=list)
    execution_artifact_ids: List[str] = Field(default_factory=list)

    # Debug payload for quick triage (kept small)
    notes: Dict[str, Any] = Field(default_factory=dict)
