"""WP-3: Attachment-related schemas for RMOS Runs v2.

Extracted from schemas.py to reduce god-object size.
Covers attachment CRUD, Art Studio binding, and path normalization.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Attachment Creation Schemas
# =============================================================================

class RunAttachmentCreateRequest(BaseModel):
    """Request to create a new attachment for a run."""
    kind: str = Field(
        ...,
        description="Attachment type: geometry_svg, geometry_spec_json, ai_provenance_json, gcode, etc.",
    )
    filename: str = Field(
        ...,
        description="Display filename",
    )
    content_type: str = Field(
        ...,
        description="MIME type (e.g., image/svg+xml, application/json)",
    )
    sha256: str = Field(
        ...,
        description="Expected SHA256 hash of the decoded content",
        min_length=64,
        max_length=64,
    )
    b64: str = Field(
        ...,
        description="Base64-encoded payload (dev-friendly, deterministic)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata: request_id, generator_version, variant_index, etc.",
    )


class RunAttachmentCreateResponse(BaseModel):
    """Response after creating an attachment."""
    attachment_id: str = Field(
        ...,
        description="Attachment identifier (same as sha256 for content-addressed storage)",
    )
    sha256: str = Field(
        ...,
        description="Verified SHA256 hash of the content",
    )
    kind: str = Field(
        ...,
        description="Attachment type",
    )


# =============================================================================
# Art Studio Binding Schemas
# =============================================================================

class BindArtStudioCandidateRequest(BaseModel):
    """Request to bind Art Studio candidate attachments to a run artifact."""
    attachment_ids: List[str] = Field(
        ...,
        description="List of attachment SHA256 hashes (att-... or raw sha256)",
        min_length=1,
    )
    operator_notes: Optional[str] = Field(
        None,
        description="Optional operator notes for this binding",
    )
    strict: bool = Field(
        default=True,
        description="If true, fail if any attachment is missing",
    )


class BindArtStudioCandidateResponse(BaseModel):
    """Response after binding Art Studio candidate."""
    artifact_id: str = Field(
        ...,
        description="Created run artifact ID",
    )
    decision: Literal["ALLOW", "BLOCK"] = Field(
        ...,
        description="Feasibility decision: ALLOW or BLOCK",
    )
    feasibility_score: float = Field(
        ...,
        description="Feasibility score (0.0 - 1.0)",
        ge=0.0,
        le=1.0,
    )
    risk_level: str = Field(
        ...,
        description="Risk level: GREEN, YELLOW, RED, UNKNOWN",
    )
    feasibility_sha256: str = Field(
        ...,
        description="SHA256 of the feasibility evaluation",
        min_length=64,
        max_length=64,
    )
    attachment_sha256_map: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of attachment_id -> verified sha256",
    )


# =============================================================================
# Bundle 17: Attachment Path Normalization + Contract
# =============================================================================

def normalize_attachment_path(p: str) -> str:
    """
    Normalize an attachment path to forward slashes.

    Removes leading "./" and collapses double slashes.
    """
    s = (p or "").strip().replace("\\", "/")
    while s.startswith("./"):
        s = s[2:]
    while "//" in s:
        s = s.replace("//", "/")
    return s


class RunAttachmentRowV1(BaseModel):
    """Normalized attachment row for list responses."""
    att_id: str = Field(
        ...,
        description="Attachment ID (stable identifier)",
    )
    path: str = Field(
        ...,
        description="Normalized attachment path (forward slashes)",
    )
    sha256: Optional[str] = Field(
        None,
        description="Content hash",
    )
    size_bytes: Optional[int] = Field(
        None,
        description="File size in bytes",
    )
    content_type: Optional[str] = Field(
        None,
        description="MIME type",
    )
    signed_url: Optional[str] = Field(
        None,
        description="Signed URL for direct download (only when requested)",
    )


class RunAttachmentsListResponseV1(BaseModel):
    """Normalized response for attachment list endpoint."""
    attachments: List[RunAttachmentRowV1] = Field(
        default_factory=list,
        description="List of attachment rows (normalized)",
    )


# =============================================================================
# Model Rebuild for Forward Reference Resolution (Pydantic V2)
# =============================================================================

RunAttachmentCreateRequest.model_rebuild()
RunAttachmentCreateResponse.model_rebuild()
BindArtStudioCandidateRequest.model_rebuild()
BindArtStudioCandidateResponse.model_rebuild()
RunAttachmentRowV1.model_rebuild()
RunAttachmentsListResponseV1.model_rebuild()
