"""
Translator Governance Review Ledger Router

CAM Dev Order 7K: REST endpoints for immutable governance review ledger.

Endpoints:
  POST /api/cam/translators/governance-review-ledger/build   - Build ledger entry
  GET  /api/cam/translators/governance-review-ledger         - List entries
  GET  /api/cam/translators/governance-review-ledger/{id}    - Get entry
  GET  /api/cam/translators/governance-review-ledger/by-translator/{id} - By translator
  GET  /api/cam/translators/governance-review-ledger/{id}/lineage - Get lineage

7K invariants:
  - All responses have immutable=true
  - All responses have execution_authorized=false
  - All responses have machine_output_allowed=false
  - No mutation endpoints
  - No approval endpoints

Guardrail:
  7K records governance review trace ancestry. It must not mutate
  prior entries, approval state, or execution authority.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.cam.translator_governance_review_ledger import (
    TranslatorGovernanceReviewLedgerEntry,
    GovernanceReviewLedgerSummary,
    build_governance_review_ledger_entry_by_matrix_id,
    get_review_ledger_entry,
    list_review_ledger_entries,
    list_review_ledger_entries_for_translator,
    get_lineage_chain,
    to_summary,
    LedgerBuildError,
    DuplicateLedgerEntryError,
)


router = APIRouter(tags=["Translator Governance Review Ledger"])


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------

class LedgerBuildRequest(BaseModel):
    """Request model for building a governance review ledger entry."""

    review_matrix_id: str = Field(..., description="Review matrix ID to build from")
    parent_ledger_hashes: Optional[List[str]] = Field(
        default=None,
        description="Explicit parent hashes (auto-detect if None)"
    )
    persist_to_rmos: bool = Field(
        default=False,
        description="Whether to persist to RMOS"
    )


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class LedgerPolicyInfo(BaseModel):
    """Information about ledger policy configuration."""

    append_only: bool = True
    mutation_allowed: bool = False
    deletion_allowed: bool = False
    duplicate_ids_allowed: bool = False

    # 7K invariants
    immutable: bool = True
    execution_authorized: bool = False
    machine_output_allowed: bool = False


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/translators/governance-review-ledger/build",
    response_model=TranslatorGovernanceReviewLedgerEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Build governance review ledger entry",
    description="Build an immutable governance review ledger entry from a review matrix.",
)
async def build_ledger_entry(
    request: LedgerBuildRequest,
) -> TranslatorGovernanceReviewLedgerEntry:
    """
    Build immutable governance review ledger entry.

    Creates a new append-only ledger entry with deterministic review trace hash.

    Guardrail:
      7K records governance review trace ancestry. It must not mutate
      prior entries, approval state, or execution authority.
    """
    try:
        entry = build_governance_review_ledger_entry_by_matrix_id(
            review_matrix_id=request.review_matrix_id,
            parent_ledger_hashes=request.parent_ledger_hashes,
            persist_to_rmos=request.persist_to_rmos,
        )
        return entry
    except DuplicateLedgerEntryError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except LedgerBuildError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/translators/governance-review-ledger",
    response_model=List[GovernanceReviewLedgerSummary],
    summary="List governance review ledger entries",
    description="List all governance review ledger entries.",
)
async def list_ledger_entries(
    translator_id: Optional[str] = None,
) -> List[GovernanceReviewLedgerSummary]:
    """List ledger entries, optionally filtered by translator."""
    if translator_id:
        entries = list_review_ledger_entries_for_translator(translator_id)
    else:
        entries = list_review_ledger_entries()
    return [to_summary(e) for e in entries]


@router.get(
    "/translators/governance-review-ledger/policy",
    response_model=LedgerPolicyInfo,
    summary="Get ledger policy",
    description="Get the current ledger policy configuration.",
)
async def get_ledger_policy() -> LedgerPolicyInfo:
    """Get ledger policy information."""
    return LedgerPolicyInfo()


@router.get(
    "/translators/governance-review-ledger/by-translator/{translator_id}",
    response_model=List[TranslatorGovernanceReviewLedgerEntry],
    summary="Get ledger entries by translator",
    description="Get all governance review ledger entries for a specific translator.",
)
async def get_ledger_entries_by_translator(
    translator_id: str,
) -> List[TranslatorGovernanceReviewLedgerEntry]:
    """Get all ledger entries for a translator."""
    return list_review_ledger_entries_for_translator(translator_id)


@router.get(
    "/translators/governance-review-ledger/{ledger_entry_id}/lineage",
    response_model=List[GovernanceReviewLedgerSummary],
    summary="Get ledger entry lineage",
    description="Get the ancestry chain for a ledger entry.",
)
async def get_entry_lineage(
    ledger_entry_id: str,
    max_depth: int = 10,
) -> List[GovernanceReviewLedgerSummary]:
    """
    Get lineage chain for a ledger entry.

    Walks parent_ledger_hashes to build ancestry chain.
    """
    chain = get_lineage_chain(ledger_entry_id, max_depth=max_depth)
    if not chain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ledger entry not found: {ledger_entry_id}",
        )
    return [to_summary(e) for e in chain]


@router.get(
    "/translators/governance-review-ledger/{ledger_entry_id}",
    response_model=TranslatorGovernanceReviewLedgerEntry,
    summary="Get governance review ledger entry",
    description="Get a specific governance review ledger entry by ID.",
)
async def get_ledger_entry(
    ledger_entry_id: str,
) -> TranslatorGovernanceReviewLedgerEntry:
    """Get ledger entry by ID."""
    entry = get_review_ledger_entry(ledger_entry_id)

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Governance review ledger entry not found: {ledger_entry_id}",
        )

    return entry
