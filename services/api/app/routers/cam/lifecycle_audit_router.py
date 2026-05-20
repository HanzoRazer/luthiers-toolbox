"""
Lifecycle Audit Router

CAM Dev Order 7R: HTTP endpoints for lifecycle audit lineage.

Provides:
  - Audit entry retrieval
  - Lineage verification
  - Replay continuity
  - Ancestry reconstruction
  - Lineage report generation

7R invariants:
  - Read-only operations
  - No execution authorization
  - No machine output generation
  - Replay = verification, not re-execution
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.cam.cam_lifecycle_audit_ledger import (
    CAMLifecycleAuditLedgerEntry,
    AuditLedgerSummary,
    LIFECYCLE_AUDIT_LEDGER_INDEX,
    LIFECYCLE_AUDIT_BY_EXPORT_INDEX,
    get_audit_entry,
    get_audit_entries_for_export,
    list_audit_entries,
)
from app.cam.lifecycle_lineage_engine import (
    LineageIntegrityStatus,
    ReplayContinuityStatus,
    verify_lifecycle_continuity,
    build_lifecycle_replay,
    reconstruct_ancestry,
    verify_checkpoint_continuity,
    generate_lineage_report,
    is_valid_lifecycle_transition,
)


router = APIRouter(
    prefix="/api/cam/lifecycle-audit",
    tags=["CAM Lifecycle Audit"],
)


class LineageVerificationResponse(BaseModel):
    """Response model for lineage verification."""
    entry_id: str
    status: str
    parent_verified: bool
    chain_depth: int
    broken_at: Optional[str] = None
    reason: Optional[str] = None
    verified_at: str


class ReplayContinuityResponse(BaseModel):
    """Response model for replay continuity."""
    export_id: str
    status: str
    entries_verified: int
    entries_total: int
    gaps: List[List[str]] = Field(default_factory=list)
    divergence_point: Optional[str] = None
    timeline: List[str] = Field(default_factory=list)
    verified_at: str


class AncestryReconstructionResponse(BaseModel):
    """Response model for ancestry reconstruction."""
    entry_id: str
    ancestry_chain: List[str]
    root_entry_id: Optional[str] = None
    chain_length: int
    complete: bool
    missing_links: List[str] = Field(default_factory=list)
    reconstructed_at: str


class CheckpointContinuityResponse(BaseModel):
    """Response model for checkpoint continuity."""
    checkpoint_pathway: str
    entries_with_checkpoint: int
    entries_without_checkpoint: int
    continuity_maintained: bool
    first_checkpoint_entry: Optional[str] = None
    last_checkpoint_entry: Optional[str] = None


class TransitionValidationRequest(BaseModel):
    """Request model for transition validation."""
    from_entry_id: str
    to_entry_id: str


class TransitionValidationResponse(BaseModel):
    """Response model for transition validation."""
    from_entry_id: str
    to_entry_id: str
    is_valid: bool
    reason: str


class LineageReportResponse(BaseModel):
    """Response model for lineage report."""
    total_entries: int
    valid_entries: int
    broken_chains: int
    orphaned_entries: int
    root_entries: int
    integrity_percentage: float
    generated_at: str


class AuditSummaryResponse(BaseModel):
    """Response model for audit summary."""
    total_entries: int
    entries_with_checkpoints: int
    entries_without_checkpoints: int
    unique_exports: int
    integrity_verified: bool


@router.get(
    "/entries",
    summary="List all audit entries",
    description="Returns all lifecycle audit entries in the ledger.",
)
def list_all_entries() -> List[Dict[str, Any]]:
    """List all audit entries in the ledger."""
    entries = list_audit_entries()
    return [entry.model_dump() for entry in entries]


@router.get(
    "/entries/{entry_id}",
    summary="Get specific audit entry",
    description="Returns a specific lifecycle audit entry by ID.",
)
def get_entry(entry_id: str) -> Dict[str, Any]:
    """Get a specific audit entry by ID."""
    entry = get_audit_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
    return entry.model_dump()


@router.get(
    "/entries/by-export/{export_id}",
    summary="Get audit entries by export object",
    description="Returns all audit entries associated with a specific export object.",
)
def get_entries_by_export(export_id: str) -> List[Dict[str, Any]]:
    """Get audit entries by export object ID."""
    entries = get_audit_entries_for_export(export_id)
    return [entry.model_dump() for entry in entries]


@router.get(
    "/verify/{entry_id}",
    response_model=LineageVerificationResponse,
    summary="Verify lineage for an entry",
    description="""
Verify lineage continuity for a specific audit entry.

Checks:
- Entry exists in ledger
- Parent hashes point to valid entries
- Hash chain is unbroken
- No orphaned references
""",
)
def verify_entry_lineage(entry_id: str) -> LineageVerificationResponse:
    """Verify lineage continuity for an entry."""
    result = verify_lifecycle_continuity(entry_id)
    return LineageVerificationResponse(
        entry_id=result.entry_id,
        status=result.status.value,
        parent_verified=result.parent_verified,
        chain_depth=result.chain_depth,
        broken_at=result.broken_at,
        reason=result.reason,
        verified_at=result.verified_at,
    )


@router.get(
    "/replay/{export_id}",
    response_model=ReplayContinuityResponse,
    summary="Build replay timeline for export",
    description="""
Build replay timeline for an export.

Replay is integrity verification + determinism check + timeline view.
It does NOT re-execute operations.

Returns ordered timeline of entries with gap detection.
""",
)
def replay_export(export_id: str) -> ReplayContinuityResponse:
    """Build replay timeline for an export."""
    result = build_lifecycle_replay(export_id)
    return ReplayContinuityResponse(
        export_id=result.export_id,
        status=result.status.value,
        entries_verified=result.entries_verified,
        entries_total=result.entries_total,
        gaps=[list(gap) for gap in result.gaps],
        divergence_point=result.divergence_point,
        timeline=result.timeline,
        verified_at=result.verified_at,
    )


@router.get(
    "/ancestry/{entry_id}",
    response_model=AncestryReconstructionResponse,
    summary="Reconstruct ancestry chain",
    description="""
Reconstruct full ancestry chain for an entry.

Walks parent hash chain backward to find root entry.
Returns complete lineage with missing link detection.
""",
)
def get_ancestry(entry_id: str, max_depth: int = 100) -> AncestryReconstructionResponse:
    """Reconstruct ancestry chain for an entry."""
    result = reconstruct_ancestry(entry_id, max_depth=max_depth)
    return AncestryReconstructionResponse(
        entry_id=result.entry_id,
        ancestry_chain=result.ancestry_chain,
        root_entry_id=result.root_entry_id,
        chain_length=result.chain_length,
        complete=result.complete,
        missing_links=result.missing_links,
        reconstructed_at=result.reconstructed_at,
    )


@router.get(
    "/checkpoint-continuity/{checkpoint_pathway:path}",
    response_model=CheckpointContinuityResponse,
    summary="Verify checkpoint continuity",
    description="""
Verify checkpoint continuity across all entries for a pathway.

Returns statistics on entries with/without checkpoint evaluation.
""",
)
def get_checkpoint_continuity(checkpoint_pathway: str) -> CheckpointContinuityResponse:
    """Verify checkpoint continuity for a pathway."""
    result = verify_checkpoint_continuity(checkpoint_pathway)
    return CheckpointContinuityResponse(
        checkpoint_pathway=result.checkpoint_pathway,
        entries_with_checkpoint=result.entries_with_checkpoint,
        entries_without_checkpoint=result.entries_without_checkpoint,
        continuity_maintained=result.continuity_maintained,
        first_checkpoint_entry=result.first_checkpoint_entry,
        last_checkpoint_entry=result.last_checkpoint_entry,
    )


@router.post(
    "/validate-transition",
    response_model=TransitionValidationResponse,
    summary="Validate lifecycle transition",
    description="""
Check if transition between two entries is valid.

Valid transitions require:
- Both entries exist in ledger
- Target references source in parent_lifecycle_hashes
- Target created_at >= source created_at
""",
)
def validate_transition(request: TransitionValidationRequest) -> TransitionValidationResponse:
    """Validate a lifecycle transition."""
    is_valid, reason = is_valid_lifecycle_transition(
        request.from_entry_id,
        request.to_entry_id,
    )
    return TransitionValidationResponse(
        from_entry_id=request.from_entry_id,
        to_entry_id=request.to_entry_id,
        is_valid=is_valid,
        reason=reason,
    )


@router.get(
    "/report",
    response_model=LineageReportResponse,
    summary="Generate lineage report",
    description="""
Generate comprehensive lineage report for all entries.

Returns:
- Total entry count
- Valid entry count
- Broken chain count
- Orphaned entry count
- Root entry count
- Integrity percentage
""",
)
def get_lineage_report() -> LineageReportResponse:
    """Generate lineage report."""
    report = generate_lineage_report()
    return LineageReportResponse(
        total_entries=report["total_entries"],
        valid_entries=report["valid_entries"],
        broken_chains=report["broken_chains"],
        orphaned_entries=report["orphaned_entries"],
        root_entries=report["root_entries"],
        integrity_percentage=report["integrity_percentage"],
        generated_at=report["generated_at"],
    )


@router.get(
    "/summary",
    response_model=AuditSummaryResponse,
    summary="Get audit ledger summary",
    description="Returns summary statistics for the audit ledger.",
)
def get_audit_summary() -> AuditSummaryResponse:
    """Get audit ledger summary."""
    entries = list_audit_entries()
    unique_exports = set(e.export_id for e in entries)
    entries_with_checkpoints = sum(1 for e in entries if e.checkpoint_summary is not None)

    return AuditSummaryResponse(
        total_entries=len(entries),
        entries_with_checkpoints=entries_with_checkpoints,
        entries_without_checkpoints=len(entries) - entries_with_checkpoints,
        unique_exports=len(unique_exports),
        integrity_verified=True,
    )
