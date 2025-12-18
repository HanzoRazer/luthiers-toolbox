"""
RMOS Runs v2 Schemas

Pydantic models with REQUIRED fields per governance contract.
Per: docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md

GOVERNANCE:
- feasibility_sha256: REQUIRED (not Optional)
- risk_level: REQUIRED (not Optional)
- Pydantic enforces at creation time
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Hashes(BaseModel):
    """Content hashes for integrity verification."""
    feasibility_sha256: str  # REQUIRED per governance
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None
    opplan_sha256: Optional[str] = None

    @field_validator("feasibility_sha256")
    @classmethod
    def feasibility_sha256_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("feasibility_sha256 is REQUIRED and cannot be empty")
        return v


class RunDecision(BaseModel):
    """Feasibility decision summary."""
    risk_level: str  # REQUIRED per governance (GREEN/YELLOW/RED/UNKNOWN/ERROR)
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("risk_level")
    @classmethod
    def risk_level_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("risk_level is REQUIRED and cannot be empty")
        return v


class RunOutputs(BaseModel):
    """Generated output references."""
    gcode_text: Optional[str] = None
    opplan_json: Optional[Dict[str, Any]] = None
    gcode_path: Optional[str] = None
    opplan_path: Optional[str] = None
    preview_svg_path: Optional[str] = None


class AdvisoryInputRef(BaseModel):
    """
    Reference to an advisory asset.
    Stored as separate link file to preserve artifact immutability.
    """
    advisory_id: str
    kind: Literal["explanation", "advisory", "note", "unknown"] = "unknown"
    created_at_utc: datetime = Field(default_factory=utc_now)
    request_id: Optional[str] = None
    engine_id: Optional[str] = None
    engine_version: Optional[str] = None


class RunAttachment(BaseModel):
    """Metadata for content-addressed attachment."""
    sha256: str
    kind: str
    mime: str
    filename: str
    size_bytes: int
    created_at_utc: datetime = Field(default_factory=utc_now)


class RunArtifact(BaseModel):
    """
    Immutable run artifact for audit-grade tracking.

    GOVERNANCE (per RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md):
    - Write-once (no modifications after creation)
    - Required fields enforced by Pydantic validators
    - Advisory links stored separately to preserve immutability
    """
    # Identity (REQUIRED)
    run_id: str
    created_at_utc: datetime = Field(default_factory=utc_now)

    # Context (REQUIRED)
    mode: str
    tool_id: str

    # Outcome (REQUIRED)
    status: Literal["OK", "BLOCKED", "ERROR"]

    # Inputs (REQUIRED)
    request_summary: Dict[str, Any]

    # Authoritative Data (REQUIRED)
    feasibility: Dict[str, Any]
    decision: RunDecision  # Contains REQUIRED risk_level
    hashes: Hashes  # Contains REQUIRED feasibility_sha256

    # Outputs
    outputs: RunOutputs = Field(default_factory=RunOutputs)

    # Advisory inputs (loaded from separate link files at read time)
    advisory_inputs: List[AdvisoryInputRef] = Field(default_factory=list)

    # Explanation status (stored in separate file)
    explanation_status: Literal["NONE", "PENDING", "READY", "ERROR"] = "NONE"
    explanation_summary: Optional[str] = None

    # Legacy compatibility
    attachments: Optional[List[RunAttachment]] = None

    # Free-form extras
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("run_id")
    @classmethod
    def run_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("run_id is REQUIRED and cannot be empty")
        return v

    @field_validator("mode")
    @classmethod
    def mode_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("mode is REQUIRED and cannot be empty")
        return v

    @field_validator("tool_id")
    @classmethod
    def tool_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("tool_id is REQUIRED and cannot be empty")
        return v
