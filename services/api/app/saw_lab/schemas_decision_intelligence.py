from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TuningDelta(BaseModel):
    """
    Conservative, human-reviewable tuning deltas.
    Multipliers are applied to the *planned* values (rpm/feed/doc).
    """

    rpm_mul: float = Field(1.0, ge=0.70, le=1.20)
    feed_mul: float = Field(1.0, ge=0.70, le=1.20)
    doc_mul: float = Field(1.0, ge=0.70, le=1.20)


class DecisionIntelSuggestion(BaseModel):
    """
    A single proposed tuning change for an execution.
    """

    suggestion_id: str
    batch_execution_artifact_id: str
    material_id: Optional[str] = None
    tool_id: Optional[str] = None
    signals: List[str] = Field(default_factory=list)  # ["burn", "tearout", ...]
    rationale: List[str] = Field(default_factory=list)
    delta: TuningDelta
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    bounds_note: str = "Conservative clamp applied (±20%)."


class CreateSuggestionResponse(BaseModel):
    artifact_id: str
    suggestion: DecisionIntelSuggestion


class ApproveSuggestionRequest(BaseModel):
    suggestion_artifact_id: str
    approved: bool
    approved_by: str = "operator"
    note: Optional[str] = None

    # Optional override (operator can tweak within bounds)
    chosen_delta: Optional[TuningDelta] = None


class ApproveSuggestionResponse(BaseModel):
    decision_artifact_id: str
    approved: bool
    effective_delta: Optional[TuningDelta] = None
    wrote_overrides_jsonl: bool = False
