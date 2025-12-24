from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SawCompareCandidate(BaseModel):
    """
    One candidate scenario to evaluate.
    You can treat design/context as opaque dicts; Saw Lab service will adapt them.
    """
    candidate_id: str = Field(..., description="Client-provided ID for correlation (stable across retries).")
    label: Optional[str] = Field(None, description="Human label: 'Freud 140mm @ 18k rpm', etc.")
    design: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class SawCompareRequest(BaseModel):
    """
    Compare a batch of candidates using feasibility only (no toolpaths).
    """
    candidates: List[SawCompareCandidate] = Field(..., min_length=1, max_length=50)
    # Optional grouping fields for indexing/audit
    batch_label: Optional[str] = None
    session_id: Optional[str] = None


class SawCompareItem(BaseModel):
    candidate_id: str
    label: Optional[str] = None
    artifact_id: str
    risk_bucket: str
    score: float


class SawCompareResponse(BaseModel):
    batch_label: Optional[str] = None
    session_id: Optional[str] = None
    parent_artifact_id: Optional[str] = None
    items: List[SawCompareItem]
