"""RMOS Run Artifact Schemas v2 - Governance Compliant"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# =============================================================================
# Type Aliases
# =============================================================================

RunStatus = Literal["OK", "BLOCKED", "ERROR"]
ExplanationStatus = Literal["NONE", "PENDING", "READY", "ERROR"]
RiskLevel = Literal["GREEN", "YELLOW", "RED", "UNKNOWN", "ERROR"]

# Advisory review state (ledger-authoritative)
VariantStatus = Literal["NEW", "REVIEWED", "PROMOTED", "REJECTED"]
RejectReasonCode = Literal[
    "GEOMETRY_UNSAFE",
    "TEXT_REQUIRES_OUTLINE",
    "AESTHETIC",
    "DUPLICATE",
    "OTHER",
]


# =============================================================================
# Supporting Models
# =============================================================================

class Hashes(BaseModel):
    """SHA256 hashes for audit verification."""
    feasibility_sha256: str = Field(
        ...,  # REQUIRED per governance contract
        description="SHA256 of server-computed feasibility (REQUIRED)",
        min_length=64,
        max_length=64,
    )
    toolpaths_sha256: Optional[str] = Field(
        None,
        description="SHA256 of toolpaths payload (present if status=OK)",
    )
    gcode_sha256: Optional[str] = Field(
        None,
        description="SHA256 of G-code output (present if generated)",
    )
    opplan_sha256: Optional[str] = Field(
        None,
        description="SHA256 of operation plan (present if generated)",
    )
    snapshot_sha256: Optional[str] = Field(
        None,
        description="SHA256 of session snapshot (present for snapshot events)",
    )


class RunDecision(BaseModel):
    """Safety decision extracted from feasibility evaluation."""
    risk_level: str = Field(
        ...,  # REQUIRED per governance contract
        description="Risk classification: GREEN, YELLOW, RED, UNKNOWN, ERROR",
    )
    score: Optional[float] = Field(
        None,
        description="Numeric feasibility score (0-100)",
        ge=0,
        le=100,
    )
    block_reason: Optional[str] = Field(
        None,
        description="Why the run was blocked (if status=BLOCKED)",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warning messages from feasibility evaluation",
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional decision context",
    )

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk_level is non-empty."""
        if not v or not v.strip():
            raise ValueError("risk_level cannot be empty")
        return v.upper()


class RunOutputs(BaseModel):
    """Generated outputs from toolpath generation."""
    # Embedded outputs (for small payloads)
    gcode_text: Optional[str] = Field(
        None,
        description="Inline G-code if <= 200KB",
    )
    opplan_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Inline operation plan",
    )

    # File references (for large outputs)
    gcode_path: Optional[str] = Field(
        None,
        description="Path to G-code file",
    )
    opplan_path: Optional[str] = Field(
        None,
        description="Path to operation plan file",
    )
    preview_svg_path: Optional[str] = Field(
        None,
        description="Path to preview SVG",
    )


class RunLineage(BaseModel):
    """Lineage tracking for Plan → Execute relationships."""
    parent_plan_run_id: Optional[str] = Field(
        None,
        description="Run ID of the parent plan artifact (for lineage tracking)",
    )


class RunAttachment(BaseModel):
    """Metadata for content-addressed attachment."""
    sha256: str = Field(
        ...,
        description="Content hash (primary key)",
        min_length=64,
        max_length=64,
    )
    kind: str = Field(
        ...,
        description="Attachment type: geometry, toolpaths, gcode, debug",
    )
    mime: str = Field(
        ...,
        description="MIME type: application/json, text/plain, etc.",
    )
    filename: str = Field(
        ...,
        description="Display filename",
    )
    size_bytes: int = Field(
        ...,
        description="File size in bytes",
        ge=0,
    )
    created_at_utc: str = Field(
        ...,
        description="ISO timestamp of attachment creation",
    )


class AdvisoryInputRef(BaseModel):
    """Reference to an attached advisory/explanation asset."""
    advisory_id: str = Field(
        ...,
        description="Unique identifier of the advisory asset",
    )
    kind: Literal["explanation", "advisory", "note", "unknown"] = Field(
        "unknown",
        description="Type of advisory content",
    )
    created_at_utc: datetime = Field(
        default_factory=utc_now,
        description="When the advisory was attached",
    )
    request_id: Optional[str] = Field(
        None,
        description="Correlation ID for audit trail",
    )
    engine_id: Optional[str] = Field(
        None,
        description="AI engine that generated the advisory",
    )
    engine_version: Optional[str] = Field(
        None,
        description="Version of the generating engine",
    )

    # -------------------------------------------------------------------------
    # Review fields (RMOS ledger-authoritative)
    # These persist governance state for each advisory_id attached to the run.
    # Defaults preserve backward compatibility with existing runs.
    # -------------------------------------------------------------------------
    status: VariantStatus = Field(
        "NEW",
        description="NEW|REVIEWED|PROMOTED|REJECTED",
    )
    rejected: bool = Field(
        False,
        description="True if operator rejected this variant",
    )
    risk_level: Optional[RiskLevel] = Field(
        None,
        description="Quick triage risk level",
    )
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="1-5 star rating",
    )
    notes: Optional[str] = Field(
        None,
        description="Operator notes",
    )

    # Rejection details
    rejection_reason_code: Optional[RejectReasonCode] = None
    rejection_reason_detail: Optional[str] = None
    rejection_operator_note: Optional[str] = None
    rejected_at_utc: Optional[str] = None
    updated_at_utc: Optional[str] = None

    # Promotion state
    promoted: bool = Field(
        False,
        description="True if promoted to manufacturing",
    )
    promoted_candidate_id: Optional[str] = Field(
        None,
        description="Candidate id if created",
    )

    @field_validator("status", mode="before")
    @classmethod
    def _norm_status(cls, v: str) -> str:
        return (v or "NEW").upper()

    @field_validator("risk_level", mode="before")
    @classmethod
    def _norm_risk(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if isinstance(v, str) else v

    @field_validator("rejection_reason_code", mode="before")
    @classmethod
    def _norm_reason(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if isinstance(v, str) else v


# =============================================================================
# Core Run Artifact Model
# =============================================================================

class RunArtifact(BaseModel):
    """Complete record of a toolpath generation attempt."""
    # Identity (REQUIRED)
    run_id: str = Field(
        ...,
        description="Unique identifier (UUID hex)",
    )
    created_at_utc: datetime = Field(
        default_factory=utc_now,
        description="UTC timestamp of creation",
    )

    # Provenance (OPTIONAL but recommended for audit trail)
    request_id: Optional[str] = Field(
        None,
        description="Request correlation ID from middleware (for audit/tracing)",
    )

    # Context (REQUIRED)
    mode: str = Field(
        ...,
        description="Operation mode: saw, router, cam, etc.",
    )
    tool_id: str = Field(
        ...,
        description="Tool identifier",
    )

    # Outcome (REQUIRED)
    status: RunStatus = Field(
        ...,
        description="Run outcome: OK, BLOCKED, ERROR",
    )

    # Inputs (REQUIRED)
    request_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized request summary (no client feasibility)",
    )

    # Authoritative Data (REQUIRED)
    feasibility: Dict[str, Any] = Field(
        default_factory=dict,
        description="Server-computed feasibility evaluation",
    )
    decision: RunDecision = Field(
        ...,
        description="Safety decision from feasibility",
    )

    # Verification (REQUIRED)
    hashes: Hashes = Field(
        ...,
        description="SHA256 hashes for integrity verification",
    )

    # Outputs
    outputs: RunOutputs = Field(
        default_factory=RunOutputs,
        description="Generated artifacts",
    )

    # Lineage (Bundle 09: Plan → Execute tracking)
    lineage: Optional[RunLineage] = Field(
        None,
        description="Lineage envelope for parent_plan_run_id tracking",
    )

    # Advisory/explanation (append-only references)
    advisory_inputs: List[AdvisoryInputRef] = Field(
        default_factory=list,
        description="Attached advisory references (append-only)",
    )

    # Explanation status
    explanation_status: ExplanationStatus = Field(
        "NONE",
        description="Explanation generation state",
    )
    explanation_summary: Optional[str] = Field(
        None,
        description="Brief explanation text",
    )

    # Variant Review (Product Bundle: Review, Rating, Promotion)
    advisory_reviews: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Reviews per advisory_id: {advisory_id: {rating, notes, reviewed_at, reviewed_by}}",
    )
    manufacturing_candidates: Optional[List[Any]] = Field(
        None,
        description="Promoted advisory variants intended for manufacturing review/approval",
    )
    source_advisory_id: Optional[str] = Field(
        None,
        description="Last promoted advisory_id source for this run (convenience for product UI)",
    )

    # Legacy compatibility - content-addressed attachments
    attachments: Optional[List[RunAttachment]] = Field(
        None,
        description="Content-addressed file attachments",
    )

    # Metadata (OPTIONAL per contract)
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form metadata: versions, correlation IDs, etc.",
    )

    # =================================================================
    # Legacy Fields (for backward compatibility during migration)
    # =================================================================
    workflow_session_id: Optional[str] = Field(
        None,
        description="[LEGACY] Parent workflow session",
    )
    material_id: Optional[str] = Field(
        None,
        description="[LEGACY] Material identifier",
    )
    machine_id: Optional[str] = Field(
        None,
        description="[LEGACY] Machine identifier",
    )
    workflow_mode: Optional[str] = Field(
        None,
        description="[LEGACY] Workflow mode (use 'mode' instead)",
    )
    toolchain_id: Optional[str] = Field(
        None,
        description="[LEGACY] Toolchain identifier",
    )
    post_processor_id: Optional[str] = Field(
        None,
        description="[LEGACY] Post-processor identifier",
    )
    geometry_ref: Optional[str] = Field(
        None,
        description="[LEGACY] Geometry reference",
    )
    geometry_hash: Optional[str] = Field(
        None,
        description="[LEGACY] Geometry content hash",
    )
    event_type: str = Field(
        "unknown",
        description="[LEGACY] Event type: approval, toolpaths, etc.",
    )
    parent_run_id: Optional[str] = Field(
        None,
        description="[LEGACY] Parent run for forks",
    )
    drift_detected: Optional[bool] = Field(
        None,
        description="[LEGACY] Drift detection flag",
    )
    drift_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="[LEGACY] Drift details",
    )
    gate_policy_id: Optional[str] = Field(
        None,
        description="[LEGACY] Gate policy identifier",
    )
    gate_decision: Optional[str] = Field(
        None,
        description="[LEGACY] Gate decision",
    )
    engine_version: Optional[str] = Field(
        None,
        description="[LEGACY] Engine version",
    )
    toolchain_version: Optional[str] = Field(
        None,
        description="[LEGACY] Toolchain version",
    )
    config_fingerprint: Optional[str] = Field(
        None,
        description="[LEGACY] Config fingerprint",
    )
    notes: Optional[str] = Field(
        None,
        description="[LEGACY] Operator notes",
    )
    errors: Optional[List[str]] = Field(
        None,
        description="[LEGACY] Error messages",
    )

    class Config:
        """Pydantic configuration."""
        # Immutability: prevent modification after creation
        frozen = False  # Set to True after migration is complete
        # Allow population by field name
        populate_by_name = True
        # Validate on assignment
        validate_assignment = True


# =============================================================================
# WP-3: Attachment schemas extracted to schemas_attachments.py — re-export
# =============================================================================

# NOTE: Cannot use relative import here because this file may be loaded via
# importlib (see schemas/__init__.py). Use absolute import instead.
from app.rmos.runs_v2.schemas_attachments import (  # noqa: E402
    BindArtStudioCandidateRequest as BindArtStudioCandidateRequest,
    BindArtStudioCandidateResponse as BindArtStudioCandidateResponse,
    RunAttachmentCreateRequest as RunAttachmentCreateRequest,
    RunAttachmentCreateResponse as RunAttachmentCreateResponse,
    RunAttachmentRowV1 as RunAttachmentRowV1,
    RunAttachmentsListResponseV1 as RunAttachmentsListResponseV1,
    normalize_attachment_path as normalize_attachment_path,
)


# =============================================================================
# Model Rebuild for Forward Reference Resolution (Pydantic V2)
# =============================================================================
# When using `from __future__ import annotations`, all type hints become
# forward references (strings). Pydantic V2 needs model_rebuild() to resolve
# these references after all types are defined.

Hashes.model_rebuild()
RunDecision.model_rebuild()
RunOutputs.model_rebuild()
RunLineage.model_rebuild()
RunAttachment.model_rebuild()
AdvisoryInputRef.model_rebuild()
RunArtifact.model_rebuild()
