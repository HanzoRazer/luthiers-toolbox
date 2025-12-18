from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Hashes(BaseModel):
    feasibility_sha256: Optional[str] = None
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None
    opplan_sha256: Optional[str] = None


class RunDecision(BaseModel):
    risk_level: Optional[str] = None  # e.g. GREEN/YELLOW/RED/ERROR (engine contract comes later)
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class RunOutputs(BaseModel):
    gcode_text: Optional[str] = None
    opplan_json: Optional[Dict[str, Any]] = None

    gcode_path: Optional[str] = None
    opplan_path: Optional[str] = None
    preview_svg_path: Optional[str] = None


class AdvisoryInputRef(BaseModel):
    advisory_id: str
    kind: Literal["explanation", "advisory", "note", "unknown"] = "unknown"
    created_at_utc: datetime = Field(default_factory=utc_now)

    # Optional provenance (helps audits / reverse lookup later)
    request_id: Optional[str] = None
    engine_id: Optional[str] = None
    engine_version: Optional[str] = None


class RunArtifact(BaseModel):
    run_id: str
    created_at_utc: datetime = Field(default_factory=utc_now)

    # Operational metadata
    mode: str
    tool_id: str
    status: Literal["OK", "BLOCKED", "ERROR"]

    # Core payloads
    request_summary: Dict[str, Any] = Field(default_factory=dict)
    feasibility: Dict[str, Any] = Field(default_factory=dict)
    decision: RunDecision = Field(default_factory=RunDecision)
    hashes: Hashes = Field(default_factory=Hashes)
    outputs: RunOutputs = Field(default_factory=RunOutputs)

    # Advisory/explanation hooks (append-only references)
    advisory_inputs: List[AdvisoryInputRef] = Field(default_factory=list)

    # Optional inline preview (canonical explanation lives in advisory asset later)
    explanation_status: Literal["NONE", "PENDING", "READY", "ERROR"] = "NONE"
    explanation_summary: Optional[str] = None

    # Free-form extras (client version, correlation ids, etc.)
    meta: Dict[str, Any] = Field(default_factory=dict)
