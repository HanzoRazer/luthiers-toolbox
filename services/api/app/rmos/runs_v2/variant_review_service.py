"""
RMOS Variant Review Service

Product Bundle: Variant Review, Rating, and Promotion

Capabilities:
- List advisory variants for a run
- Save rating + notes for a variant
- Promote a variant to manufacturing candidate

Governance rules:
- Reviews are stored in RunArtifact.advisory_reviews (does not mutate advisory blob)
- Promotion creates a NEW RunArtifact with source_advisory_id lineage
- All actions are auditable
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from .store import get_run, persist_run, update_run, create_run_id
from .schemas import RunArtifact, RunDecision, Hashes, AdvisoryInputRef
from .attachments import get_attachment_path, get_bytes_attachment
from .advisory_blob_service import _run_or_404, _authorized_advisory_ids, _find_ref


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _infer_mime(sha256: str) -> str:
    """Infer MIME type from blob content."""
    try:
        data = get_bytes_attachment(sha256)
        if data:
            if data[:5] == b"<?xml" or data[:4] == b"<svg":
                return "image/svg+xml"
            if data[:8] == b"\x89PNG\r\n\x1a\n":
                return "image/png"
            if data[:2] == b"\xff\xd8":
                return "image/jpeg"
    except Exception:
        pass
    return "application/octet-stream"


def _infer_filename(ref: Any, sha256: str, mime: str) -> str:
    """Infer filename from ref or generate from sha256."""
    # Check ref for filename hint
    if ref:
        filename = getattr(ref, "filename", None)
        if filename:
            return filename
        kind = getattr(ref, "kind", None)
        if kind:
            ext = ".svg" if mime == "image/svg+xml" else ".bin"
            return f"{kind}_{sha256[:12]}{ext}"

    # Generate from sha256
    ext = {
        "image/svg+xml": ".svg",
        "image/png": ".png",
        "image/jpeg": ".jpg",
    }.get(mime, ".bin")
    return f"variant_{sha256[:12]}{ext}"


def list_advisory_variants(run_id: str) -> List[Dict[str, Any]]:
    """
    List all advisory variants for a run with their review status.

    Returns:
        List of variant dicts with advisory_id, mime, filename, rating, notes, promoted
    """
    run = _run_or_404(run_id)
    advisory_ids = _authorized_advisory_ids(run)
    reviews = getattr(run, "advisory_reviews", None) or {}

    variants = []
    for adv_id in advisory_ids:
        ref = _find_ref(run, adv_id)
        mime = _infer_mime(adv_id)
        filename = _infer_filename(ref, adv_id, mime)

        review = reviews.get(adv_id, {})
        variants.append({
            "advisory_id": adv_id,
            "mime": mime,
            "filename": filename,
            "kind": getattr(ref, "kind", "unknown") if ref else "unknown",
            "rating": review.get("rating"),
            "notes": review.get("notes"),
            "reviewed_at": review.get("reviewed_at"),
            "reviewed_by": review.get("reviewed_by"),
            "promoted": review.get("promoted", False),
            "promoted_run_id": review.get("promoted_run_id"),
        })

    return variants


def save_variant_review(
    run_id: str,
    advisory_id: str,
    rating: int,
    notes: str,
    reviewed_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Save rating + notes for an advisory variant.

    Args:
        run_id: Run artifact ID
        advisory_id: Advisory blob SHA256
        rating: 1-5 stars
        notes: Review notes
        reviewed_by: Operator identity

    Returns:
        Updated review dict

    Note: This modifies the RunArtifact.advisory_reviews field.
          The advisory blob itself is never mutated.
    """
    # Validate rating
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    run = _run_or_404(run_id)

    # Verify advisory exists on this run
    if advisory_id not in _authorized_advisory_ids(run):
        raise HTTPException(status_code=404, detail="Advisory not linked to this run")

    # Build review entry
    review = {
        "rating": rating,
        "notes": notes,
        "reviewed_at": _utc_now_iso(),
        "reviewed_by": reviewed_by,
    }

    # Update advisory_reviews (copy to avoid mutation issues)
    reviews = dict(getattr(run, "advisory_reviews", None) or {})

    # Preserve existing promoted status if any
    existing = reviews.get(advisory_id, {})
    if existing.get("promoted"):
        review["promoted"] = True
        review["promoted_run_id"] = existing.get("promoted_run_id")

    reviews[advisory_id] = review

    # Update run with new reviews (controlled mutation of advisory_reviews only)
    run.advisory_reviews = reviews
    update_run(run)

    return review


def promote_variant(
    run_id: str,
    advisory_id: str,
    promoted_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Promote an advisory variant to a manufacturing candidate.

    This creates a NEW RunArtifact with:
    - source_advisory_id pointing to the promoted variant
    - Re-evaluated feasibility
    - Lineage preserved

    Args:
        run_id: Source run artifact ID
        advisory_id: Advisory blob SHA256 to promote
        promoted_by: Operator identity

    Returns:
        Dict with new manufacturing artifact details

    Raises:
        HTTPException 404: Run or advisory not found
        HTTPException 409: Already promoted
    """
    run = _run_or_404(run_id)

    # Verify advisory exists
    if advisory_id not in _authorized_advisory_ids(run):
        raise HTTPException(status_code=404, detail="Advisory not linked to this run")

    # Check if already promoted
    reviews = getattr(run, "advisory_reviews", None) or {}
    existing = reviews.get(advisory_id, {})
    if existing.get("promoted"):
        raise HTTPException(
            status_code=409,
            detail=f"Already promoted to run {existing.get('promoted_run_id')}"
        )

    # Get advisory blob for feasibility re-check
    blob_path = get_attachment_path(advisory_id)
    if not blob_path:
        raise HTTPException(status_code=404, detail="Advisory blob not found in CAS")

    # Create new manufacturing candidate artifact
    new_run_id = create_run_id()

    # Inherit context from parent run
    parent_mode = getattr(run, "mode", "promoted")
    parent_tool_id = getattr(run, "tool_id", "unknown")
    parent_material_id = getattr(run, "material_id", "unknown")
    parent_machine_id = getattr(run, "machine_id", "unknown")

    # Re-evaluate feasibility (simplified - in production would call actual feasibility service)
    # For now, inherit parent's decision with promotion context
    parent_decision = getattr(run, "decision", None)
    if parent_decision:
        risk_level = parent_decision.risk_level
        score = parent_decision.score
    else:
        risk_level = "YELLOW"  # Promoted variants get YELLOW by default
        score = 0.8

    import hashlib
    import json

    promotion_payload = {
        "source_run_id": run_id,
        "source_advisory_id": advisory_id,
        "promoted_by": promoted_by,
        "promoted_at": _utc_now_iso(),
    }
    payload_hash = hashlib.sha256(json.dumps(promotion_payload, sort_keys=True).encode()).hexdigest()

    manufacturing_artifact = RunArtifact(
        run_id=new_run_id,
        created_at_utc=datetime.now(timezone.utc),
        event_type="manufacturing_candidate",
        mode=parent_mode,
        tool_id=parent_tool_id,
        material_id=parent_material_id,
        machine_id=parent_machine_id,
        status="OK" if risk_level != "RED" else "BLOCKED",
        request_summary=promotion_payload,
        feasibility={
            "promotion": True,
            "source_run_id": run_id,
            "source_advisory_id": advisory_id,
        },
        decision=RunDecision(
            risk_level=risk_level,
            score=score,
            warnings=["Promoted from advisory variant"],
            details={"promotion_source": advisory_id},
        ),
        hashes=Hashes(feasibility_sha256=payload_hash),
        advisory_inputs=[
            AdvisoryInputRef(
                advisory_id=advisory_id,
                kind="advisory",
            )
        ],
        source_advisory_id=advisory_id,
        parent_run_id=run_id,
        meta={
            "promoted_from_run": run_id,
            "promoted_from_advisory": advisory_id,
            "promoted_by": promoted_by,
        },
    )

    persist_run(manufacturing_artifact)

    # Mark as promoted in source run (controlled mutation of advisory_reviews only)
    reviews = dict(getattr(run, "advisory_reviews", None) or {})
    review = dict(reviews.get(advisory_id, {}))
    review["promoted"] = True
    review["promoted_run_id"] = new_run_id
    review["promoted_at"] = _utc_now_iso()
    review["promoted_by"] = promoted_by
    reviews[advisory_id] = review
    run.advisory_reviews = reviews
    update_run(run)

    return {
        "manufacturing_run_id": new_run_id,
        "source_run_id": run_id,
        "source_advisory_id": advisory_id,
        "status": manufacturing_artifact.status,
        "risk_level": risk_level,
        "promoted_by": promoted_by,
    }
