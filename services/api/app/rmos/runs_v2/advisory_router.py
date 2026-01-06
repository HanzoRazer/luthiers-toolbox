# services/api/app/rmos/runs_v2/advisory_router.py
"""
RMOS Advisory Ledger Plane - Canonical Endpoints

This router provides the ledger plane for the hybrid architecture:
- Attach: Links Vision-generated sha256 to runs
- Review: Unified reject/undo/rate/notes surface
- Bulk-review: Batch operations
- Promote: Elevate to manufacturing candidate

The Producer Plane (Vision) generates assets and writes to CAS.
This Ledger Plane governs state transitions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request

from .attachments import verify_attachment
from .store import get_run, attach_advisory, update_run
from .schemas import AdvisoryInputRef
from .schemas.advisory_schemas import (
    AdvisoryAttachRequest,
    AdvisoryAttachResponse,
    AdvisoryVariantReviewRecord,
    AdvisoryVariantReviewRequest,
    BulkReviewAdvisoryVariantsRequest,
    BulkReviewAdvisoryVariantsResponse,
    PromoteVariantResponse,
)

router = APIRouter(prefix="/runs", tags=["RMOS", "Advisory"])


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _req_id(req: Request) -> str:
    return req.headers.get("x-request-id") or ""


def _find_advisory(run: Any, advisory_id: str) -> Optional[Dict[str, Any]]:
    """Find advisory in run's advisory_inputs by advisory_id."""
    refs = getattr(run, "advisory_inputs", None) or []
    for ref in refs:
        ref_id = getattr(ref, "advisory_id", None)
        if ref_id == advisory_id:
            # Convert to dict for mutation
            if hasattr(ref, "model_dump"):
                return ref.model_dump()
            return dict(ref) if hasattr(ref, "__dict__") else None
    return None


def _find_advisory_index(run: Any, advisory_id: str) -> int:
    """Find index of advisory in run's advisory_inputs."""
    refs = getattr(run, "advisory_inputs", None) or []
    for i, ref in enumerate(refs):
        ref_id = getattr(ref, "advisory_id", None)
        if ref_id == advisory_id:
            return i
    return -1


@router.post("/{run_id}/advisory/attach", response_model=AdvisoryAttachResponse)
def attach_advisory_to_run(
    run_id: str, payload: AdvisoryAttachRequest, request: Request
) -> AdvisoryAttachResponse:
    """
    Attach a Vision-generated advisory (by sha256) to an RMOS run.

    This is the canonical attach endpoint for the hybrid architecture.
    The advisory_id must exist in CAS (high-signal integrity gate).
    """
    # Ensure advisory_id points to an actual CAS blob
    result = verify_attachment(payload.advisory_id)
    if not result.get("ok", False):
        raise HTTPException(
            status_code=409, detail=f"CAS_MISSING_BLOB: {payload.advisory_id}"
        )

    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="RUN_NOT_FOUND")

    # Check for duplicates
    existing_refs = getattr(run, "advisory_inputs", None) or []
    for ref in existing_refs:
        if getattr(ref, "advisory_id", None) == payload.advisory_id:
            return AdvisoryAttachResponse(
                run_id=run_id,
                advisory_id=payload.advisory_id,
                attached=False,
                message="Already attached",
            )

    # Use canonical attach_advisory function
    ref = attach_advisory(
        run_id=run_id,
        advisory_id=payload.advisory_id,
        kind=payload.kind,
        request_id=_req_id(request),
    )

    if ref is None:
        raise HTTPException(status_code=500, detail="ATTACH_FAILED")

    return AdvisoryAttachResponse(
        run_id=run_id,
        advisory_id=payload.advisory_id,
        attached=True,
        message="Attached",
    )


@router.post(
    "/{run_id}/advisory/{advisory_id}/review",
    response_model=AdvisoryVariantReviewRecord,
)
def review_advisory_variant(
    req: Request, run_id: str, advisory_id: str, payload: AdvisoryVariantReviewRequest
) -> AdvisoryVariantReviewRecord:
    """
    Unified review endpoint for advisory variants.

    Supports: reject, undo-reject, rate, add notes, set risk level.
    Status is server-normalized based on rejection state.
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="RUN_NOT_FOUND")

    idx = _find_advisory_index(run, advisory_id)
    if idx < 0:
        raise HTTPException(status_code=404, detail="ADVISORY_NOT_FOUND_ON_RUN")

    # Get current advisory ref and update it
    refs = list(run.advisory_inputs) if run.advisory_inputs else []
    current_ref = refs[idx]

    now = _now_utc_iso()

    # Build updated ref dict
    updated = current_ref.model_dump() if hasattr(current_ref, "model_dump") else dict(current_ref)

    # Normalize rejection state
    rejected = bool(payload.rejected) if payload.rejected is not None else updated.get("rejected", False)
    status = payload.status or updated.get("status") or "NEW"

    if payload.rejected is True:
        status = "REJECTED"
        updated["rejected_at_utc"] = now
    elif payload.rejected is False and status == "REJECTED":
        status = "REVIEWED"
        updated["rejected_at_utc"] = None

    updated["status"] = status
    updated["rejected"] = rejected
    updated["updated_at_utc"] = now

    # Apply optional review fields
    if payload.risk_level is not None:
        updated["risk_level"] = payload.risk_level
    if payload.rating is not None:
        updated["rating"] = payload.rating
    if payload.notes is not None:
        updated["notes"] = payload.notes
    if payload.rejection_reason_code is not None:
        updated["rejection_reason_code"] = payload.rejection_reason_code
    if payload.rejection_reason_detail is not None:
        updated["rejection_reason_detail"] = payload.rejection_reason_detail
    if payload.rejection_operator_note is not None:
        updated["rejection_operator_note"] = payload.rejection_operator_note

    # Replace ref in list
    refs[idx] = AdvisoryInputRef(**{k: v for k, v in updated.items() if k in AdvisoryInputRef.model_fields})

    # Update run with new advisory_inputs
    run_copy = run.model_copy(update={"advisory_inputs": refs})
    update_run(run_copy)

    return AdvisoryVariantReviewRecord(
        run_id=run_id,
        advisory_id=advisory_id,
        status=updated.get("status", "NEW"),
        rejected=bool(updated.get("rejected", False)),
        rating=updated.get("rating"),
        notes=updated.get("notes"),
        risk_level=updated.get("risk_level"),
        rejection_reason_code=updated.get("rejection_reason_code"),
        rejection_reason_detail=updated.get("rejection_reason_detail"),
        rejection_operator_note=updated.get("rejection_operator_note"),
        rejected_at_utc=updated.get("rejected_at_utc"),
        updated_at_utc=updated.get("updated_at_utc"),
    )


@router.post(
    "/{run_id}/advisory/bulk-review",
    response_model=BulkReviewAdvisoryVariantsResponse,
)
def bulk_review(
    req: Request, run_id: str, payload: BulkReviewAdvisoryVariantsRequest
) -> BulkReviewAdvisoryVariantsResponse:
    """
    Bulk review multiple advisory variants at once.

    Applies the same review state to all specified advisory_ids.
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="RUN_NOT_FOUND")

    refs = list(run.advisory_inputs) if run.advisory_inputs else []
    updated_ids: List[str] = []
    now = _now_utc_iso()

    for i, ref in enumerate(refs):
        ref_id = getattr(ref, "advisory_id", None)
        if ref_id not in payload.advisory_ids:
            continue

        ref_dict = ref.model_dump() if hasattr(ref, "model_dump") else dict(ref)

        # Apply bulk review fields
        if payload.rejected is not None:
            ref_dict["rejected"] = bool(payload.rejected)
            if payload.rejected:
                ref_dict["status"] = "REJECTED"
                ref_dict["rejected_at_utc"] = now
            else:
                if ref_dict.get("status") == "REJECTED":
                    ref_dict["status"] = "REVIEWED"
                ref_dict["rejected_at_utc"] = None

        if payload.status is not None:
            ref_dict["status"] = payload.status
        if payload.rating is not None:
            ref_dict["rating"] = payload.rating
        if payload.notes is not None:
            ref_dict["notes"] = payload.notes
        if payload.risk_level is not None:
            ref_dict["risk_level"] = payload.risk_level
        if payload.rejection_reason_code is not None:
            ref_dict["rejection_reason_code"] = payload.rejection_reason_code
        if payload.rejection_reason_detail is not None:
            ref_dict["rejection_reason_detail"] = payload.rejection_reason_detail
        if payload.rejection_operator_note is not None:
            ref_dict["rejection_operator_note"] = payload.rejection_operator_note

        ref_dict["updated_at_utc"] = now
        refs[i] = AdvisoryInputRef(**{k: v for k, v in ref_dict.items() if k in AdvisoryInputRef.model_fields})
        updated_ids.append(ref_id)

    run_copy = run.model_copy(update={"advisory_inputs": refs})
    update_run(run_copy)

    return BulkReviewAdvisoryVariantsResponse(
        updated_count=len(updated_ids),
        advisory_ids=updated_ids,
    )


@router.post(
    "/{run_id}/advisory/{advisory_id}/promote",
    response_model=PromoteVariantResponse,
)
def promote(run_id: str, advisory_id: str) -> PromoteVariantResponse:
    """
    Promote an advisory variant to manufacturing candidate.

    Requirements:
    - Must not be rejected
    - Must be reviewed (not NEW)
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="RUN_NOT_FOUND")

    idx = _find_advisory_index(run, advisory_id)
    if idx < 0:
        raise HTTPException(status_code=404, detail="ADVISORY_NOT_FOUND_ON_RUN")

    refs = list(run.advisory_inputs) if run.advisory_inputs else []
    ref = refs[idx]
    ref_dict = ref.model_dump() if hasattr(ref, "model_dump") else dict(ref)

    # Check promotion gates
    if bool(ref_dict.get("rejected", False)):
        raise HTTPException(status_code=409, detail="PROMOTE_BLOCKED: rejected")

    status = ref_dict.get("status") or "NEW"
    if status == "NEW":
        raise HTTPException(status_code=409, detail="PROMOTE_BLOCKED: must review first")

    # Mark as promoted
    ref_dict["status"] = "PROMOTED"
    ref_dict["promoted"] = True
    ref_dict["rejected"] = False  # Defensive: ensure rejected is strictly boolean False
    ref_dict["updated_at_utc"] = _now_utc_iso()

    refs[idx] = AdvisoryInputRef(**{k: v for k, v in ref_dict.items() if k in AdvisoryInputRef.model_fields})
    run_copy = run.model_copy(update={"advisory_inputs": refs})
    update_run(run_copy)

    return PromoteVariantResponse(
        run_id=run_id,
        advisory_id=advisory_id,
        promoted=True,
        promoted_candidate_id=ref_dict.get("promoted_candidate_id"),
    )
