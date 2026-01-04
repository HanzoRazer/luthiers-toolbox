"""
RMOS Variant Review Service

Product Bundle: Variant Review, Rating, and Promotion

Capabilities:
- List advisory variants for a run
- Save rating + notes for a variant
- Promote a variant to manufacturing candidate

Governance rules:
- Reviews are stored in RunArtifact.advisory_reviews (does not mutate advisory blob)
- Promotion adds to manufacturing_candidates list (in-place on run)
- RBAC: promotion requires admin/operator/engineer role
- All actions are auditable
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import HTTPException, Request

from app.auth import Principal
from .store import get_run, update_run
from .attachments import get_attachment_path, get_bytes_attachment
from .schemas_variant_review import (
    AdvisoryVariantListResponse,
    AdvisoryVariantSummary,
    AdvisoryVariantReviewRequest,
    AdvisoryVariantReviewRecord,
    PromoteVariantRequest,
    PromoteVariantResponse,
    RejectVariantRequest,
    RejectVariantResponse,
    UnrejectVariantResponse,
)
from .schemas_manufacturing import ManufacturingCandidate
from .advisory_variant_state import read_rejection, write_rejection, clear_rejection


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authorized_advisory_ids(run: Any) -> List[str]:
    """Get list of advisory IDs linked to a run."""
    refs = getattr(run, "advisory_inputs", None) or []
    out: List[str] = []
    for r in refs:
        adv = getattr(r, "advisory_id", None)
        if isinstance(adv, str) and adv:
            out.append(adv)
    return out


def _mime_from_bytes(data: bytes) -> str:
    """High-signal MIME sniffing from first bytes."""
    if data.startswith(b"<svg") or b"<svg" in data[:4096]:
        return "image/svg+xml"
    if data.startswith(b"{") or data.startswith(b"["):
        return "application/json"
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return "application/octet-stream"


def _infer_filename(advisory_id: str, mime: str) -> str:
    """Generate filename from advisory ID and MIME type."""
    ext = {
        "image/svg+xml": ".svg",
        "application/json": ".json",
        "text/plain": ".txt",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "application/pdf": ".pdf",
        "application/octet-stream": ".bin",
    }.get(mime, ".bin")
    return f"{advisory_id[:16]}{ext}"


def _preview_safety(svg_text: str) -> Tuple[bool, Optional[str]]:
    """Check if SVG is safe for inline preview."""
    lower = (svg_text or "").lower()
    if "<script" in lower:
        return False, "script"
    if "foreignobject" in lower:
        return False, "foreignObject"
    if "<image" in lower:
        return False, "image"
    if "<text" in lower:
        # Product choice: block preview only, allow download + bind
        return False, "text"
    return True, None


def _risk_from_svg_for_binding(svg_text: str) -> Tuple[str, str, float, str]:
    """
    Bind-time policy for SVG promotion:
      - BLOCK: script, foreignObject, image
      - ALLOW: path, geometry
      - WARN: text => ALLOW + YELLOW
    """
    lower = (svg_text or "").lower()
    if "<script" in lower:
        return ("BLOCK", "RED", 0.0, "svg_script")
    if "foreignobject" in lower:
        return ("BLOCK", "RED", 0.0, "svg_foreignobject")
    if "<image" in lower:
        return ("BLOCK", "RED", 0.10, "svg_image_embed")
    if "<text" in lower:
        return ("ALLOW", "YELLOW", 0.75, "svg_text_requires_outline")
    return ("ALLOW", "GREEN", 1.0, "ok")


def _get_user_id(req: Request) -> Optional[str]:
    """Extract user ID from request headers (legacy, for save_review)."""
    uid = (req.headers.get("x-user-id") or "").strip()
    return uid or None


def list_variants(run_id: str) -> AdvisoryVariantListResponse:
    """List all advisory variants for a run with their review status."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    allowed = set(_authorized_advisory_ids(run))

    # Review records stored on run (dict keyed by advisory_id)
    review_map: Dict[str, Any] = getattr(run, "advisory_reviews", None) or {}

    # Rejection records: prefer file-based state, fallback to legacy run.advisory_rejections
    legacy_rejection_map: Dict[str, Any] = getattr(run, "advisory_rejections", None) or {}

    # Manufacturing candidates (list) - may be dicts or objects depending on storage
    candidates: list[Any] = list(getattr(run, "manufacturing_candidates", []) or [])
    promoted_ids: set[str] = set()
    for c in candidates:
        if isinstance(c, dict):
            adv = c.get("advisory_id")
        else:
            adv = getattr(c, "advisory_id", None)
        if adv:
            promoted_ids.add(adv)

    # Advisory timestamps (if available)
    advisory_meta: Dict[str, Any] = getattr(run, "advisory_meta", None) or {}

    items: list[AdvisoryVariantSummary] = []
    for adv_id in allowed:
        p = get_attachment_path(adv_id)
        if not p:
            # Still list, but mark missing
            items.append(
                AdvisoryVariantSummary(
                    advisory_id=adv_id,
                    mime="application/octet-stream",
                    filename=_infer_filename(adv_id, "application/octet-stream"),
                    size_bytes=0,
                    preview_blocked=True,
                    preview_block_reason="missing",
                    rating=None,
                    notes=None,
                    promoted=adv_id in promoted_ids,
                    status="NEW",
                    risk_level="RED",
                    created_at_utc=None,
                    updated_at_utc=None,
                    rejected=False,
                    rejection_reason=None,
                )
            )
            continue

        size = Path(p).stat().st_size
        data = get_bytes_attachment(adv_id) or b""
        mime = _mime_from_bytes(data[:4096] if data else b"")
        filename = _infer_filename(adv_id, mime)

        preview_blocked = False
        preview_reason = None
        risk_level = "GREEN"
        if mime == "image/svg+xml":
            try:
                svg_text = data.decode("utf-8", errors="ignore")
                ok, reason = _preview_safety(svg_text)
                preview_blocked = not ok
                preview_reason = reason
                # Compute risk based on SVG content
                _, risk_level, _, _ = _risk_from_svg_for_binding(svg_text)
            except Exception:
                preview_blocked = True
                preview_reason = "decode"
                risk_level = "YELLOW"
        else:
            # Non-SVG files get YELLOW risk
            risk_level = "YELLOW"

        rec = review_map.get(adv_id) or {}
        rating = rec.get("rating")
        notes = rec.get("notes")
        updated_at_utc = rec.get("updated_at_utc")

        # Rejection state: prefer file-based, fallback to legacy
        file_rej = read_rejection(run_id, adv_id)
        legacy_rej = legacy_rejection_map.get(adv_id) or {}
        is_rejected = file_rej is not None or bool(legacy_rej.get("rejected", False))
        rejection_reason = file_rej.reason_code if file_rej else legacy_rej.get("reason")
        rejection_reason_code = file_rej.reason_code if file_rej else None
        rejection_reason_detail = file_rej.reason_detail if file_rej else None
        rejection_operator_note = file_rej.operator_note if file_rej else None
        rejected_at_utc = file_rej.rejected_at_utc if file_rej else None

        # Metadata timestamps
        meta = advisory_meta.get(adv_id) or {}
        created_at_utc = meta.get("created_at_utc")

        # Compute status: PROMOTED > REJECTED > REVIEWED > NEW
        is_promoted = adv_id in promoted_ids
        has_review = rating is not None or (notes and notes.strip())

        if is_promoted:
            status = "PROMOTED"
        elif is_rejected:
            status = "REJECTED"
        elif has_review:
            status = "REVIEWED"
        else:
            status = "NEW"

        items.append(
            AdvisoryVariantSummary(
                advisory_id=adv_id,
                mime=mime,
                filename=filename,
                size_bytes=size,
                preview_blocked=preview_blocked,
                preview_block_reason=preview_reason,
                rating=rating,
                notes=notes,
                promoted=is_promoted,
                status=status,  # type: ignore
                risk_level=risk_level,  # type: ignore
                created_at_utc=created_at_utc,
                updated_at_utc=updated_at_utc,
                rejected=is_rejected,
                rejection_reason=rejection_reason,
                rejection_reason_code=rejection_reason_code,
                rejection_reason_detail=rejection_reason_detail,
                rejection_operator_note=rejection_operator_note,
                rejected_at_utc=rejected_at_utc,
            )
        )

    # Stable ordering by advisory_id for determinism
    items.sort(key=lambda x: x.advisory_id)
    return AdvisoryVariantListResponse(run_id=run_id, count=len(items), items=items)


def save_review(
    run_id: str,
    advisory_id: str,
    payload: AdvisoryVariantReviewRequest,
    req: Request,
) -> AdvisoryVariantReviewRecord:
    """Save rating + notes for an advisory variant."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    allowed = set(_authorized_advisory_ids(run))
    if advisory_id not in allowed:
        raise HTTPException(status_code=404, detail="Advisory blob not linked to this run")

    review_map: Dict[str, Any] = dict(getattr(run, "advisory_reviews", None) or {})
    now = _utc_now()
    user_id = _get_user_id(req)

    review_map[advisory_id] = {
        "rating": payload.rating,
        "notes": payload.notes,
        "updated_at_utc": now,
        "updated_by": user_id,
    }
    run.advisory_reviews = review_map
    update_run(run)

    return AdvisoryVariantReviewRecord(
        advisory_id=advisory_id,
        rating=payload.rating,
        notes=payload.notes,
        updated_at_utc=now,
        updated_by=user_id,
    )


def promote_variant(
    run_id: str,
    advisory_id: str,
    payload: PromoteVariantRequest,
    principal: Principal,
) -> PromoteVariantResponse:
    """Promote an advisory variant to manufacturing candidate.

    RBAC is enforced at the API layer via Depends(require_roles(...)).
    Principal is already validated to have admin/operator/engineer role.
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    allowed = set(_authorized_advisory_ids(run))
    if advisory_id not in allowed:
        raise HTTPException(status_code=404, detail="Advisory blob not linked to this run")

    # Prevent double-promotion (handle both dict and object forms)
    candidates: list[Any] = list(getattr(run, "manufacturing_candidates", []) or [])
    for c in candidates:
        c_adv_id = c.get("advisory_id") if isinstance(c, dict) else getattr(c, "advisory_id", None)
        if c_adv_id == advisory_id:
            raise HTTPException(status_code=409, detail="Variant already promoted")

    # Resolve blob
    path = get_attachment_path(advisory_id)
    if not path:
        raise HTTPException(status_code=404, detail="Advisory blob not found (CAS missing)")

    data = Path(path).read_bytes()
    mime = _mime_from_bytes(data[:4096])

    decision = "ALLOW"
    risk = "GREEN"
    score = 1.0
    reason = "ok"

    if mime == "image/svg+xml":
        svg_text = data.decode("utf-8", errors="ignore")
        decision, risk, score, reason = _risk_from_svg_for_binding(svg_text)
    else:
        # Non-SVG candidates can exist but are not ideal for manufacturing
        decision, risk, score, reason = ("ALLOW", "YELLOW", 0.60, f"non_svg:{mime}")

    if decision == "BLOCK":
        # Do NOT persist a candidate
        return PromoteVariantResponse(
            run_id=run_id,
            advisory_id=advisory_id,
            decision="BLOCK",
            risk_level="RED",
            score=score,
            reason=reason,
            manufactured_candidate_id=None,
            message="Promotion blocked by bind-time policy",
        )

    user_id = principal.user_id
    now = _utc_now()
    cand = ManufacturingCandidate(
        candidate_id=f"mc_{uuid4().hex[:12]}",
        advisory_id=advisory_id,
        status="PROPOSED",
        label=payload.label,
        note=payload.note,
        created_at_utc=now,
        created_by=user_id,
        updated_at_utc=now,
        updated_by=user_id,
    )
    candidates.append(cand)
    run.manufacturing_candidates = candidates

    # Stamp minimal provenance for product UI
    run.source_advisory_id = advisory_id

    update_run(run)

    return PromoteVariantResponse(
        run_id=run_id,
        advisory_id=advisory_id,
        decision="ALLOW",
        risk_level=risk,  # type: ignore
        score=score,
        reason=reason,
        manufactured_candidate_id=cand.candidate_id,
        message=None,
    )


# =============================================================================
# Bulk Promote (Product Bundle)
# =============================================================================

from .schemas_variant_review import (
    BulkPromoteRequest,
    BulkPromoteItemResult,
    BulkPromoteResponse,
)


def bulk_promote_variants(
    run_id: str,
    payload: BulkPromoteRequest,
    principal: Principal,
) -> BulkPromoteResponse:
    """Bulk-promote multiple advisory variants to manufacturing candidates.

    Processes each variant individually, collecting results.
    Continues on individual failures to maximize throughput.

    Returns aggregate statistics and per-item results.
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    allowed = set(_authorized_advisory_ids(run))

    # Get current candidates to detect duplicates
    candidates: list[Any] = list(getattr(run, "manufacturing_candidates", []) or [])
    already_promoted: set[str] = set()
    for c in candidates:
        c_adv_id = c.get("advisory_id") if isinstance(c, dict) else getattr(c, "advisory_id", None)
        if c_adv_id:
            already_promoted.add(c_adv_id)

    user_id = principal.user_id
    now = _utc_now()

    results: List[BulkPromoteItemResult] = []
    succeeded = 0
    failed = 0
    blocked = 0

    for advisory_id in payload.advisory_ids:
        # Check if advisory is linked to run
        if advisory_id not in allowed:
            results.append(BulkPromoteItemResult(
                advisory_id=advisory_id,
                success=False,
                error="Advisory blob not linked to this run",
            ))
            failed += 1
            continue

        # Check if already promoted
        if advisory_id in already_promoted:
            results.append(BulkPromoteItemResult(
                advisory_id=advisory_id,
                success=False,
                error="Variant already promoted",
            ))
            failed += 1
            continue

        # Resolve blob
        path = get_attachment_path(advisory_id)
        if not path:
            results.append(BulkPromoteItemResult(
                advisory_id=advisory_id,
                success=False,
                error="Advisory blob not found (CAS missing)",
            ))
            failed += 1
            continue

        try:
            data = Path(path).read_bytes()
            mime = _mime_from_bytes(data[:4096])

            decision = "ALLOW"
            risk = "GREEN"
            score = 1.0
            reason = "ok"

            if mime == "image/svg+xml":
                svg_text = data.decode("utf-8", errors="ignore")
                decision, risk, score, reason = _risk_from_svg_for_binding(svg_text)
            else:
                decision, risk, score, reason = ("ALLOW", "YELLOW", 0.60, f"non_svg:{mime}")

            if decision == "BLOCK":
                results.append(BulkPromoteItemResult(
                    advisory_id=advisory_id,
                    success=False,
                    decision="BLOCK",
                    risk_level="RED",
                    score=score,
                    reason=reason,
                    error="Promotion blocked by bind-time policy",
                ))
                blocked += 1
                continue

            # Create manufacturing candidate
            cand = ManufacturingCandidate(
                candidate_id=f"mc_{uuid4().hex[:12]}",
                advisory_id=advisory_id,
                status="PROPOSED",
                label=payload.label,
                note=payload.note,
                created_at_utc=now,
                created_by=user_id,
                updated_at_utc=now,
                updated_by=user_id,
            )
            candidates.append(cand)
            already_promoted.add(advisory_id)  # Track to prevent duplicates in same batch

            results.append(BulkPromoteItemResult(
                advisory_id=advisory_id,
                success=True,
                decision="ALLOW",
                risk_level=risk,  # type: ignore
                score=score,
                reason=reason,
                manufactured_candidate_id=cand.candidate_id,
            ))
            succeeded += 1

        except Exception as e:
            results.append(BulkPromoteItemResult(
                advisory_id=advisory_id,
                success=False,
                error=str(e),
            ))
            failed += 1

    # Persist all changes at once
    run.manufacturing_candidates = candidates
    update_run(run)

    return BulkPromoteResponse(
        run_id=run_id,
        total=len(payload.advisory_ids),
        succeeded=succeeded,
        failed=failed,
        blocked=blocked,
        results=results,
    )


def reject_variant(
    run_id: str,
    advisory_id: str,
    payload: RejectVariantRequest,
    principal: Principal,
) -> RejectVariantResponse:
    """Reject an advisory variant.

    RBAC is enforced at the API layer via Depends(require_roles(...)).
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    allowed = set(_authorized_advisory_ids(run))
    if advisory_id not in allowed:
        raise HTTPException(status_code=404, detail="Advisory blob not linked to this run")

    now = _utc_now()
    write_rejection(
        run_id=run_id,
        advisory_id=advisory_id,
        reason_code=payload.reason_code,
        reason_detail=payload.reason_detail,
        operator_note=payload.operator_note,
    )

    return RejectVariantResponse(
        run_id=run_id,
        advisory_id=advisory_id,
        rejected=True,
        reason_code=payload.reason_code,
        reason_detail=payload.reason_detail,
        rejected_at_utc=now,
    )


def unreject_variant(
    run_id: str,
    advisory_id: str,
    principal: Principal,
) -> UnrejectVariantResponse:
    """Clear rejection status for an advisory variant.

    RBAC is enforced at the API layer via Depends(require_roles(...)).
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    allowed = set(_authorized_advisory_ids(run))
    if advisory_id not in allowed:
        raise HTTPException(status_code=404, detail="Advisory blob not linked to this run")

    now = _utc_now()
    clear_rejection(run_id=run_id, advisory_id=advisory_id)

    return UnrejectVariantResponse(
        run_id=run_id,
        advisory_id=advisory_id,
        rejected=False,
        cleared_at_utc=now,
    )
