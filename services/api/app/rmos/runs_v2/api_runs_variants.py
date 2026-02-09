"""
RMOS Runs v2 — Variant review, rejection, bulk-promote, and manufacturing candidates.

Endpoints:
- GET  /{run_id}/advisory/variants
- POST /{run_id}/advisory/{advisory_id}/reject
- POST /{run_id}/advisory/{advisory_id}/unreject
- POST /{run_id}/advisory/bulk-promote
- GET  /{run_id}/manufacturing/candidates
- POST /{run_id}/manufacturing/candidates/{candidate_id}/decision
- GET  /{run_id}/manufacturing/candidates/{candidate_id}/download-zip
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import Principal, require_roles

from .schemas_variant_review import (
    AdvisoryVariantListResponse,
    AdvisoryVariantReviewRequest,
    AdvisoryVariantReviewRecord,
    PromoteVariantRequest,
    PromoteVariantResponse,
    RejectVariantRequest,
    RejectVariantResponse,
    UnrejectVariantResponse,
    BulkPromoteRequest,
    BulkPromoteResponse,
)
from .variant_review_service import (
    list_variants,
    reject_variant,
    unreject_variant,
    bulk_promote_variants,
)
from .schemas_manufacturing_ops import (
    CandidateListResponse,
    CandidateDecisionRequest,
    CandidateDecisionResponse,
)
from .manufacturing_candidate_service import (
    list_candidates,
    decide_candidate,
    download_candidate_zip,
)

router = APIRouter()


# ── Variant Review ───────────────────────────────────────────────────────────


@router.get("/{run_id}/advisory/variants", response_model=AdvisoryVariantListResponse)
def get_advisory_variants(run_id: str):
    """
    List all advisory variants attached to a run with review status.

    Returns variant info including advisory_id, mime type, filename,
    size_bytes, preview_blocked status, rating, notes, and promoted status.
    """
    return list_variants(run_id)


@router.post(
    "/{run_id}/advisory/{advisory_id}/reject", response_model=RejectVariantResponse
)
def post_reject_advisory_variant(
    run_id: str,
    advisory_id: str,
    payload: RejectVariantRequest,
    principal: Principal = Depends(require_roles("admin", "operator")),
):
    """
    Reject an advisory variant.

    Requires authenticated user with role: admin or operator.
    Rejection stores metadata on the run (does not delete the advisory blob).
    Use unreject to clear rejection status.
    """
    return reject_variant(run_id, advisory_id, payload, principal)


@router.post(
    "/{run_id}/advisory/{advisory_id}/unreject", response_model=UnrejectVariantResponse
)
def post_unreject_advisory_variant(
    run_id: str,
    advisory_id: str,
    principal: Principal = Depends(require_roles("admin", "operator")),
):
    """
    Clear rejection status for an advisory variant.

    Requires authenticated user with role: admin or operator.
    Returns cleared=true if rejection was removed, false if not rejected.
    """
    return unreject_variant(run_id, advisory_id, principal)


# ── Bulk Promote ─────────────────────────────────────────────────────────────


@router.post("/{run_id}/advisory/bulk-promote", response_model=BulkPromoteResponse)
def post_bulk_promote_advisory_variants(
    run_id: str,
    payload: BulkPromoteRequest,
    principal: Principal = Depends(require_roles("admin", "operator", "engineer")),
):
    """
    Bulk-promote multiple advisory variants to manufacturing candidates.

    Requires authenticated user with role: admin, operator, or engineer.
    Processing continues on individual failures to maximize throughput.
    """
    return bulk_promote_variants(run_id, payload, principal)


# ── Manufacturing Candidates ─────────────────────────────────────────────────


@router.get("/{run_id}/manufacturing/candidates", response_model=CandidateListResponse)
def get_manufacturing_candidates(run_id: str):
    """
    List all manufacturing candidates for a run.

    Returns candidates with their status (PROPOSED, ACCEPTED, REJECTED),
    sorted newest-first by updated_at_utc.
    """
    return list_candidates(run_id)


@router.post(
    "/{run_id}/manufacturing/candidates/{candidate_id}/decision",
    response_model=CandidateDecisionResponse,
)
def post_candidate_decision(
    run_id: str,
    candidate_id: str,
    payload: CandidateDecisionRequest,
    principal: Principal = Depends(require_roles("admin", "operator")),
):
    """
    Approve or reject a manufacturing candidate.

    Requires authenticated user with role: admin or operator.
    """
    return decide_candidate(run_id, candidate_id, payload, principal)


@router.get("/{run_id}/manufacturing/candidates/{candidate_id}/download-zip")
def get_candidate_zip(
    run_id: str,
    candidate_id: str,
    principal: Principal = Depends(
        require_roles("admin", "operator", "engineer", "viewer")
    ),
):
    """
    Download a ZIP containing the candidate's advisory blob and manifest.

    Requires any authenticated role (admin/operator/engineer/viewer).
    """
    return download_candidate_zip(run_id, candidate_id)
