"""
RMOS AI Advisory Schemas

Pydantic models for the AI advisory workflow.
These mirror the JSON schemas from ai-integrator for validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# AIContextPacket v1 (input to ai-integrator)
# -----------------------------------------------------------------------------


class AIContextPacketRequest(BaseModel):
    """Request section of AIContextPacket."""

    kind: Literal["explanation", "comparison", "asset_generation", "cam_assist"]
    template_id: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    notes: Optional[str] = None


class AIContextPacketSelected(BaseModel):
    """Selected item from viewer pack."""

    pointId: str
    freqHz: float
    activeRelpath: str


class AIContextPacketRef(BaseModel):
    """Evidence reference."""

    kind: str
    relpath: str


class AIContextPacketEvidence(BaseModel):
    """Evidence section of AIContextPacket."""

    bundle_sha256: str = Field(min_length=16)
    schema_id: str = Field(min_length=1)
    selected: AIContextPacketSelected
    refs: List[AIContextPacketRef] = Field(default_factory=list)


class AIContextPacketV1(BaseModel):
    """
    AIContextPacket v1 — Input to ai-integrator CLI.

    This is what ToolBox sends to RMOS to request an advisory.
    """

    schema_id: Literal["ai_context_packet_v1"] = "ai_context_packet_v1"
    created_at_utc: str  # RFC3339 timestamp
    request: AIContextPacketRequest
    evidence: AIContextPacketEvidence
    excerpts: Optional[Dict[str, Any]] = None

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# AdvisoryDraft v1 (output from ai-integrator)
# -----------------------------------------------------------------------------


class AdvisoryDraftModel(BaseModel):
    """Model info from draft."""

    id: str = Field(min_length=1)
    version: Optional[str] = None
    runtime: Literal["local"] = "local"


class AdvisoryDraftTemplate(BaseModel):
    """Template info from draft."""

    id: str = Field(min_length=1)
    version: str = Field(min_length=1)


class AdvisoryDraftClaim(BaseModel):
    """A single claim with evidence refs."""

    text: str = Field(min_length=1)
    evidence_refs: List[str] = Field(default_factory=list)


class AdvisoryDraftV1(BaseModel):
    """
    AdvisoryDraft v1 — Output from ai-integrator CLI.

    Contains the AI-generated advisory content.
    """

    schema_id: Literal["advisory_draft_v1"] = "advisory_draft_v1"
    kind: Literal["explanation", "comparison", "asset_generation", "cam_assist"]
    model: AdvisoryDraftModel
    template: AdvisoryDraftTemplate
    claims: List[AdvisoryDraftClaim] = Field(min_length=1)
    caveats: Optional[List[str]] = None

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# RMOS Advisory Artifact v1 (persisted by RMOS)
# -----------------------------------------------------------------------------


class AdvisoryArtifactInput(BaseModel):
    """Input provenance for artifact."""

    context_packet_sha256: str = Field(min_length=16)
    evidence_bundle_sha256: str = Field(min_length=16)


class AdvisoryArtifactEngine(BaseModel):
    """Engine provenance for artifact."""

    model_id: str = Field(min_length=1)
    template_id: str = Field(min_length=1)
    template_version: str = Field(min_length=1)


class AdvisoryArtifactGovernance(BaseModel):
    """Governance status for artifact."""

    status: Literal["draft", "published", "rejected"] = "draft"
    published_by: Optional[str] = None
    notes: Optional[str] = None


class AdvisoryArtifactV1(BaseModel):
    """
    RMOS Advisory Artifact v1 — Persisted by RMOS.

    Wraps the AdvisoryDraft with RMOS governance and provenance.
    """

    schema_id: Literal["rmos_advisory_artifact_v1"] = "rmos_advisory_artifact_v1"
    advisory_id: str = Field(min_length=1)
    created_at_utc: str  # RFC3339 timestamp
    input: AdvisoryArtifactInput
    engine: AdvisoryArtifactEngine
    draft: AdvisoryDraftV1
    governance: AdvisoryArtifactGovernance = Field(
        default_factory=lambda: AdvisoryArtifactGovernance(status="draft")
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# API Response Models
# -----------------------------------------------------------------------------


class AdvisoryRequestResponse(BaseModel):
    """Response from POST /api/rmos/advisories/request."""

    ok: bool = True
    advisory_id: str
    status: Literal["draft", "published", "rejected"] = "draft"
    message: Optional[str] = None


class AdvisoryGetResponse(BaseModel):
    """Response from GET /api/rmos/advisories/{advisory_id}."""

    ok: bool = True
    artifact: AdvisoryArtifactV1
