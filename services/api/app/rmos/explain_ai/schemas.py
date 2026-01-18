"""
Phase 5 — Assistant Explanation Schemas

Advisory-only explanation payload. MUST NOT be treated as authoritative for gating.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AssistantExplanationBasedOn(BaseModel):
    """Context that the explanation is grounded on."""

    run_id: str
    risk_level: str
    rules_triggered: List[str] = Field(default_factory=list)
    inputs_hash: Optional[str] = None


class AssistantExplanation(BaseModel):
    """
    Advisory-only explanation payload.

    MUST NOT be treated as authoritative for gating.
    The official decision remains the rule engine output (risk_level + rules_triggered).
    """

    version: str = "phase5.v1"
    based_on: AssistantExplanationBasedOn
    summary: str
    operator_notes: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "This text is advisory only. RMOS feasibility/decision are authoritative."
    )
    meta: Dict[str, Any] = Field(default_factory=dict)
