"""
RMOS Advisory Blob Schemas - Bundle RMOS_ADVISORY_BLOB_BROWSER_V1

Schemas for the run-scoped advisory blob browser API.
Authority: run.advisory_inputs[*].advisory_id (sha256 CAS key)
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class AdvisoryBlobRef(BaseModel):
    """Reference to an advisory blob linked to a run."""
    advisory_id: str = Field(..., description="CAS sha256 key (authoritative)")
    kind: Optional[str] = Field(default=None, description="Optional label if present on the ref")
    title: Optional[str] = Field(default=None, description="Optional display title if present on the ref")
    mime: Optional[str] = Field(default=None, description="Optional mime if present on the ref")
    filename: Optional[str] = Field(default=None, description="Optional filename if present on the ref")


class AdvisoryBlobListResponse(BaseModel):
    """Response for listing advisory blobs linked to a run."""
    run_id: str
    count: int
    items: List[AdvisoryBlobRef]


class SvgPreviewStatusResponse(BaseModel):
    """Response for SVG preview status check (when preview is blocked)."""
    run_id: str
    advisory_id: str
    ok: bool
    mime: Optional[str] = None
    reason: Optional[str] = None
    blocked_by: Optional[str] = Field(
        default=None,
        description="e.g. script|foreignObject|image|encoding|not_svg"
    )
    action: str = Field(
        default="download",
        description="Recommended UI action when preview is blocked"
    )
