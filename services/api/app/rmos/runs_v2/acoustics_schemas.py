"""
RMOS Acoustics Response Schemas - Stable Public Shapes.

These Pydantic models define the API contract for acoustics attachment endpoints.
Using typed response models prevents "shape drift" between endpoints and provides
automatic OpenAPI documentation.

Contract: H7.2.2.1 features (signed URLs, attachment meta index, no-path disclosure)
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Attachment Meta Schemas
# =============================================================================


class AttachmentMetaPublic(BaseModel):
    """
    Public attachment metadata (no path disclosure).

    This is the shape returned for individual attachment lookups.
    """
    sha256: str = Field(..., description="Content hash (primary key)")
    kind: Optional[str] = Field(None, description="Attachment type: manifest, analysis, advisory, etc.")
    mime: Optional[str] = Field(None, description="MIME type")
    filename: Optional[str] = Field(None, description="Display filename")
    size_bytes: Optional[int] = Field(None, description="File size in bytes", ge=0)
    created_at_utc: Optional[str] = Field(None, description="ISO timestamp of creation")

    # Optional fields when include_urls=True
    download_url: Optional[str] = Field(None, description="Relative URL for streaming/download")
    signed_url: Optional[str] = Field(None, description="Signed URL (when requested)")

    # Inline data for small attachments
    data_b64: Optional[str] = Field(None, description="Base64-encoded content (when include_bytes=True)")
    omitted_reason: Optional[str] = Field(None, description="Why data was omitted (too_large, missing, etc.)")


class AttachmentMetaIndexEntry(BaseModel):
    """
    Entry from _attachment_meta.json global index.

    Includes tracking fields not exposed in public API.
    """
    sha256: str
    kind: Optional[str] = None
    mime: Optional[str] = None
    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at_utc: Optional[str] = None
    first_seen_run_id: Optional[str] = None
    last_seen_run_id: Optional[str] = None
    first_seen_at_utc: Optional[str] = None
    last_seen_at_utc: Optional[str] = None
    ref_count: Optional[int] = None


# =============================================================================
# Endpoint Response Schemas
# =============================================================================


class RunAttachmentsListOut(BaseModel):
    """
    Response for /runs/{run_id}/attachments endpoint.

    Lists all attachments for a run with optional inline bytes.
    """
    run_id: str = Field(..., description="Run identifier")
    count: int = Field(..., description="Number of attachments returned")
    include_bytes: bool = Field(False, description="Whether inline bytes were requested")
    max_inline_bytes: int = Field(2_000_000, description="Max size for inline base64 data")
    attachments: List[AttachmentMetaPublic] = Field(
        default_factory=list,
        description="List of attachment metadata"
    )


class AttachmentHeadOut(BaseModel):
    """
    Response shape for HEAD /attachments/{sha256} (returned via headers).

    Note: HEAD requests return headers, not a body. This schema documents
    the header fields set by the endpoint.
    """
    sha256: str = Field(..., description="Content hash (X-RMOS-Attachment-SHA256)")
    size_bytes: int = Field(..., description="File size (Content-Length)")
    mime: str = Field("application/octet-stream", description="MIME type (Content-Type)")
    kind: Optional[str] = Field(None, description="Attachment type (X-RMOS-Attachment-Kind)")
    filename: Optional[str] = Field(None, description="Display name (X-RMOS-Attachment-Filename)")
    created_at_utc: Optional[str] = Field(None, description="Creation time (X-RMOS-Attachment-Created-At)")


class AttachmentExistsOut(BaseModel):
    """
    Response for /index/attachment_meta/{sha256}/exists endpoint.

    Reports both index presence and blob presence for integrity checks.
    """
    sha256: str = Field(..., description="Content hash (normalized to lowercase)")
    in_index: bool = Field(..., description="True if sha256 exists in _attachment_meta.json")
    in_store: bool = Field(..., description="True if blob exists in content-addressed store")
    size_bytes: Optional[int] = Field(None, description="File size if in_store is True")

    # Extended fields when in_index=True
    index_kind: Optional[str] = Field(None, description="Kind from index (if in_index=True)")
    index_mime: Optional[str] = Field(None, description="MIME from index (if in_index=True)")
    index_filename: Optional[str] = Field(None, description="Filename from index (if in_index=True)")
    index_size_bytes: Optional[int] = Field(None, description="Size from index (if in_index=True)")


class SignedUrlMintOut(BaseModel):
    """
    Response for POST /attachments/{sha256}/signed_url endpoint.

    Returns a temporary signed URL for the frontend to use.
    """
    sha256: str = Field(..., description="Content hash")
    method: str = Field(..., description="HTTP method the URL is signed for (GET or HEAD)")
    scope: Literal["download", "head"] = Field("download", description="Token scope")
    expires: int = Field(..., description="Unix timestamp when URL expires")
    signed_url: str = Field(..., description="Signed relative URL")


class AdvisorySummary(BaseModel):
    """
    Summary of an advisory from run index.
    """
    advisory_id: str = Field(..., description="Unique advisory identifier")
    kind: Optional[str] = Field(None, description="Advisory type")
    created_at_utc: Optional[str] = Field(None, description="Creation timestamp")


class RunAdvisoriesListOut(BaseModel):
    """
    Response for /runs/{run_id}/advisories endpoint.
    """
    run_id: str = Field(..., description="Run identifier")
    count: int = Field(..., description="Number of advisories")
    advisories: List[AdvisorySummary] = Field(
        default_factory=list,
        description="List of advisory summaries"
    )


class AdvisoryResolveOut(BaseModel):
    """
    Response for /advisories/{advisory_id} endpoint.

    Returns the full advisory lookup entry.
    """
    advisory_id: str = Field(..., description="Advisory identifier")
    run_id: Optional[str] = Field(None, description="Associated run ID")
    sha256: Optional[str] = Field(None, description="Content hash of advisory blob")
    kind: Optional[str] = Field(None, description="Advisory type")
    created_at_utc: Optional[str] = Field(None, description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class IndexRebuildOut(BaseModel):
    """
    Response for POST /index/rebuild_attachment_meta endpoint.
    """
    ok: bool = Field(..., description="Whether rebuild succeeded")
    runs_scanned: int = Field(0, description="Number of run artifacts scanned")
    attachments_indexed: int = Field(0, description="Total attachment references processed")
    unique_sha256: int = Field(0, description="Number of unique SHA256 entries in index")
