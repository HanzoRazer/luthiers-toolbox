"""
RMOS Advisories v1 (Phase 3, interpretive) - Schema + index-safe summaries.

This module defines:
- RunAdvisoryLinkV1: append-only per-run link file pointer
- AdvisoryAttachmentRefV1: safe attachment ref (no shard path disclosure)
- IndexRunAdvisorySummaryV1: run-local rollup entry used inside _index.json meta
- IndexAdvisoryLookupV1: global advisory lookup entries stored in _advisory_lookup.json

Compatibility notes:
- Matches runs_v2/schemas.py conventions: sha256 strings, created_at_utc ISO strings, size_bytes naming.
- Avoids leaking filesystem paths; storage remains content-addressed (sha-sharded) in attachments store.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, validator


_SHA256_LEN = 64

def _normalize_tags_list(v):
    """
    Normalize tags list: dedupe, strip, remove empties.

    Shared validator logic for all advisory schemas.
    """
    if v is None:
        return None
    if not isinstance(v, list):
        raise ValueError("tags must be a list[str]")
    out = []
    seen = set()
    for t in v:
        if t is None:
            continue
        tt = str(t).strip()
        if not tt:
            continue
        if tt in seen:
            continue
        seen.add(tt)
        out.append(tt)
    return out or None


def _is_lower_hex(s: str) -> bool:
    try:
        int(s, 16)
        return True
    except (ValueError, TypeError):  # WP-1: narrowed from except Exception
        return False


class AdvisoryAttachmentRefV1(BaseModel):
    """
    Safe pointer to an advisory JSON blob in the attachments store.

    Intended usage:
      - RunArtifact.meta.acoustics.advisories[] (optional convenience)
      - API responses (resolved bytes/mime ok; NO shard paths)
    """

    schema_version: Literal["advisory_attachment_ref.v1"] = "advisory_attachment_ref.v1"

    advisory_id: str = Field(..., min_length=2, description="Stable advisory id (UUID recommended).")
    sha256: str = Field(
        ..., min_length=_SHA256_LEN, max_length=_SHA256_LEN, description="Content hash of advisory JSON blob."
    )
    kind: str = Field("advisory.v1.json", min_length=2, description="Attachment kind for advisory JSON.")
    mime: str = Field("application/json", min_length=3, description="MIME type.")
    size_bytes: Optional[int] = Field(None, ge=0, description="Byte size if known.")
    created_at_utc: Optional[str] = Field(None, description="ISO UTC timestamp if known.")
    tags: Optional[List[str]] = Field(None, description="Optional tags for query/index.")
    confidence_max: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional quick summary metric.")

    @validator("sha256")
    def _validate_sha256(cls, v: str) -> str:
        vv = v.strip().lower()
        if len(vv) != _SHA256_LEN or not _is_lower_hex(vv):
            raise ValueError("sha256 must be 64 lowercase hex chars")
        return vv

    @validator("tags", pre=True)
    def _normalize_tags(cls, v):
        return _normalize_tags_list(v)

    class Config:
        extra = "forbid"
        frozen = True


class RunAdvisoryLinkV1(BaseModel):
    """
    Append-only link record stored alongside run artifacts:

      {YYYY-MM-DD}/run_<run_id>_advisory_<advisory_id>.json

    Purpose:
      - list advisories per run without parsing advisory blobs
      - map advisory_id -> sha256 for retrieval/streaming
      - support append-only advisory addition while preserving immutability
    """

    schema_version: Literal["run_advisory_link.v1"] = "run_advisory_link.v1"

    run_id: str = Field(..., min_length=4, description="RMOS run id.")
    advisory_id: str = Field(..., min_length=2, description="Stable advisory id (UUID recommended).")
    created_at_utc: str = Field(..., description="ISO UTC timestamp of link creation (e.g. 2025-12-26T22:10:00Z).")

    advisory_sha256: str = Field(
        ..., min_length=_SHA256_LEN, max_length=_SHA256_LEN, description="Content hash of advisory JSON blob."
    )
    kind: str = Field("advisory.v1.json", min_length=2, description="Attachment kind.")
    mime: str = Field("application/json", min_length=3, description="MIME type.")
    size_bytes: Optional[int] = Field(None, ge=0, description="Byte size if known.")

    status: Literal["ACTIVE", "SUPERSEDED", "RETRACTED"] = Field(
        "ACTIVE", description="Lifecycle status for the advisory link."
    )

    # Optional indexing hints (safe summaries)
    tags: Optional[List[str]] = Field(None)
    confidence_max: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Optional evidence pointers (helpful for search)
    bundle_sha256: Optional[str] = Field(None, min_length=_SHA256_LEN, max_length=_SHA256_LEN)
    manifest_sha256: Optional[str] = Field(None, min_length=_SHA256_LEN, max_length=_SHA256_LEN)

    @validator("advisory_sha256", "bundle_sha256", "manifest_sha256", pre=True)
    def _validate_optional_sha256(cls, v):
        if v is None:
            return None
        vv = str(v).strip().lower()
        if len(vv) != _SHA256_LEN or not _is_lower_hex(vv):
            raise ValueError("sha256 must be 64 lowercase hex chars")
        return vv

    @validator("tags", pre=True)
    def _normalize_tags(cls, v):
        return _normalize_tags_list(v)

    class Config:
        extra = "forbid"
        frozen = True


class IndexRunAdvisorySummaryV1(BaseModel):
    """
    Run-local advisory summary stored inside _index.json under each run's meta dict.

    This keeps existing index structure intact (Dict[run_id -> meta]).
    """

    schema_version: Literal["index_run_advisory_summary.v1"] = "index_run_advisory_summary.v1"

    advisory_id: str = Field(..., min_length=2)
    sha256: str = Field(..., min_length=_SHA256_LEN, max_length=_SHA256_LEN)
    kind: str = Field("advisory.v1.json", min_length=2)
    mime: str = Field("application/json", min_length=3)
    size_bytes: Optional[int] = Field(None, ge=0)
    created_at_utc: Optional[str] = Field(None)

    status: Literal["ACTIVE", "SUPERSEDED", "RETRACTED"] = "ACTIVE"
    tags: Optional[List[str]] = None
    confidence_max: Optional[float] = Field(None, ge=0.0, le=1.0)

    @validator("sha256")
    def _validate_sha256(cls, v: str) -> str:
        vv = v.strip().lower()
        if len(vv) != _SHA256_LEN or not _is_lower_hex(vv):
            raise ValueError("sha256 must be 64 lowercase hex chars")
        return vv

    @validator("tags", pre=True)
    def _normalize_tags(cls, v):
        return _normalize_tags_list(v)

    class Config:
        extra = "forbid"
        frozen = True


class IndexAdvisoryLookupV1(BaseModel):
    """
    Global advisory lookup stored in a separate file:
      _advisory_lookup.json

    Reason: your _index.json is Dict[run_id -> meta], not a top-level object.
    """

    schema_version: Literal["index_advisory_lookup.v1"] = "index_advisory_lookup.v1"

    advisory_id: str = Field(..., min_length=2)
    run_id: str = Field(..., min_length=4)

    sha256: str = Field(..., min_length=_SHA256_LEN, max_length=_SHA256_LEN)
    kind: str = Field("advisory.v1.json", min_length=2)
    mime: str = Field("application/json", min_length=3)
    size_bytes: Optional[int] = Field(None, ge=0)

    created_at_utc: Optional[str] = None
    status: Literal["ACTIVE", "SUPERSEDED", "RETRACTED"] = "ACTIVE"
    tags: Optional[List[str]] = None
    confidence_max: Optional[float] = Field(None, ge=0.0, le=1.0)

    bundle_sha256: Optional[str] = Field(None, min_length=_SHA256_LEN, max_length=_SHA256_LEN)
    manifest_sha256: Optional[str] = Field(None, min_length=_SHA256_LEN, max_length=_SHA256_LEN)

    @validator("sha256", "bundle_sha256", "manifest_sha256", pre=True)
    def _validate_optional_sha(cls, v):
        if v is None:
            return None
        vv = str(v).strip().lower()
        if len(vv) != _SHA256_LEN or not _is_lower_hex(vv):
            raise ValueError("sha256 must be 64 lowercase hex chars")
        return vv

    @validator("tags", pre=True)
    def _normalize_tags(cls, v):
        return _normalize_tags_list(v)

    class Config:
        extra = "forbid"
        frozen = True


def advisory_ref_from_link(link: RunAdvisoryLinkV1) -> AdvisoryAttachmentRefV1:
    """Create a safe attachment ref from a link record (no shard paths)."""
    return AdvisoryAttachmentRefV1(
        advisory_id=link.advisory_id,
        sha256=link.advisory_sha256,
        kind=link.kind,
        mime=link.mime,
        size_bytes=link.size_bytes,
        created_at_utc=link.created_at_utc,
        tags=link.tags,
        confidence_max=link.confidence_max,
    )
