# services/api/app/rmos/runs_v2/manufacturing_candidate_service.py
"""
Manufacturing Candidate Service.

Bundle C: Manufacturing Readiness & Decision Control

Provides:
- List candidates for a run (with decision state)
- Decide: set decision (GREEN/YELLOW/RED/null) with append-only history
- ZIP export for manufacturing (GREEN-only gated)

Decision Protocol (spine-locked):
- decision: null = NEEDS_DECISION (not ready)
- decision: GREEN = OK to manufacture
- decision: YELLOW = caution/hold
- decision: RED = do not manufacture
- All decisions append to decision_history (audit trail)
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.auth.principal import Principal
from .store import get_run, update_run
from .attachments import get_attachment_path, get_bytes_attachment
from .schemas_manufacturing_ops import (
    CandidateListResponse,
    CandidateListItem,
    CandidateDecisionRequest,
    CandidateDecisionResponse,
    DecisionHistoryItem,
    RiskLevel,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_candidates(run: Any) -> list[Any]:
    """Get manufacturing candidates list from run."""
    return list(getattr(run, "manufacturing_candidates", None) or [])


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from object or dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _set_attr(obj: Any, key: str, value: Any) -> None:
    """Set attribute on object or dict."""
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def list_candidates(run_id: str) -> CandidateListResponse:
    """List all manufacturing candidates for a run (Bundle C enhanced)."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    candidates = _get_candidates(run)

    items: list[CandidateListItem] = []
    for c in candidates:
        # Extract decision_history if present
        raw_history = _get_attr(c, "decision_history", None)
        history: Optional[List[DecisionHistoryItem]] = None
        if raw_history and isinstance(raw_history, list):
            history = [
                DecisionHistoryItem(
                    decision=(
                        h.get("decision")
                        if isinstance(h, dict)
                        else getattr(h, "decision", "GREEN")
                    ),
                    note=(
                        h.get("note")
                        if isinstance(h, dict)
                        else getattr(h, "note", None)
                    ),
                    decided_at_utc=(
                        h.get("decided_at_utc")
                        if isinstance(h, dict)
                        else getattr(h, "decided_at_utc", "")
                    ),
                    decided_by=(
                        h.get("decided_by")
                        if isinstance(h, dict)
                        else getattr(h, "decided_by", None)
                    ),
                )
                for h in raw_history
            ]

        # Derive status from decision for legacy compat
        decision = _get_attr(c, "decision", None)
        if decision == "GREEN":
            status = "ACCEPTED"
        elif decision == "RED":
            status = "REJECTED"
        elif decision == "YELLOW":
            status = "PROPOSED"  # YELLOW maps to PROPOSED (caution state)
        else:
            status = _get_attr(c, "status", "PROPOSED")

        items.append(
            CandidateListItem(
                candidate_id=_get_attr(c, "candidate_id", ""),
                advisory_id=_get_attr(c, "advisory_id", ""),
                decision=decision,
                decision_note=_get_attr(c, "decision_note"),
                decided_at_utc=_get_attr(c, "decided_at_utc"),
                decided_by=_get_attr(c, "decided_by"),
                decision_history=history,
                status=status,
                label=_get_attr(c, "label"),
                note=_get_attr(c, "note"),
                score=_get_attr(c, "score"),
                risk_level=_get_attr(c, "risk_level"),
                created_at_utc=_get_attr(c, "created_at_utc", ""),
                created_by=_get_attr(c, "created_by"),
                updated_at_utc=_get_attr(c, "updated_at_utc", ""),
                updated_by=_get_attr(c, "updated_by"),
            )
        )

    # Stable ordering: newest first by updated_at_utc, then by candidate_id
    items.sort(key=lambda x: (x.updated_at_utc or "", x.candidate_id), reverse=True)
    return CandidateListResponse(run_id=run_id, count=len(items), items=items)


def _find_candidate_or_404(run: Any, candidate_id: str) -> Any:
    """Find candidate by ID or raise 404."""
    for c in _get_candidates(run):
        if _get_attr(c, "candidate_id") == candidate_id:
            return c
    raise HTTPException(status_code=404, detail="Candidate not found")


def decide_candidate(
    run_id: str,
    candidate_id: str,
    payload: CandidateDecisionRequest,
    principal: Principal,
) -> CandidateDecisionResponse:
    """Set decision on a manufacturing candidate (Bundle C).

    Decision Protocol:
    - decision: null = clear decision (NEEDS_DECISION)
    - decision: GREEN/YELLOW/RED = set explicit decision
    - All non-null decisions append to decision_history (audit trail)
    - Export is gated: only GREEN candidates can be exported
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    cand = _find_candidate_or_404(run, candidate_id)

    now = _utc_now()
    decision = payload.decision  # RiskLevel | None
    note = payload.note
    decided_by = payload.decided_by or principal.user_id

    # Get or create decision_history (append-only audit trail)
    raw_history = _get_attr(cand, "decision_history", None)
    history: list = list(raw_history) if raw_history else []

    # If setting a non-null decision, append to history
    if decision is not None:
        history.append(
            {
                "decision": decision,
                "note": note,
                "decided_at_utc": now,
                "decided_by": decided_by,
            }
        )

    # Update candidate fields
    _set_attr(cand, "decision", decision)
    _set_attr(cand, "decision_note", note)
    _set_attr(cand, "decided_at_utc", now if decision else None)
    _set_attr(cand, "decided_by", decided_by if decision else None)
    _set_attr(cand, "decision_history", history)

    # Derive status from decision for legacy compat
    if decision == "GREEN":
        status = "ACCEPTED"
    elif decision == "RED":
        status = "REJECTED"
    else:  # null or YELLOW
        status = "PROPOSED"
    _set_attr(cand, "status", status)

    _set_attr(cand, "updated_at_utc", now)
    _set_attr(cand, "updated_by", decided_by)

    # Persist the updated candidates list
    run.manufacturing_candidates = _get_candidates(run)
    update_run(run)

    # Build history items for response
    history_items: Optional[List[DecisionHistoryItem]] = None
    if history:
        history_items = [
            DecisionHistoryItem(
                decision=h["decision"],
                note=h.get("note"),
                decided_at_utc=h["decided_at_utc"],
                decided_by=h.get("decided_by"),
            )
            for h in history
        ]

    return CandidateDecisionResponse(
        run_id=run_id,
        candidate_id=candidate_id,
        advisory_id=_get_attr(cand, "advisory_id", ""),
        decision=decision,
        decision_note=note,
        decided_at_utc=now if decision else None,
        decided_by=decided_by if decision else None,
        decision_history=history_items,
        status=status,
        updated_at_utc=now,
        updated_by=decided_by,
    )


def _infer_file_info(blob_bytes: bytes) -> tuple[str, str]:
    """Infer filename extension and MIME type from blob content."""
    head = blob_bytes[:4096]
    if head.startswith(b"<svg") or b"<svg" in head:
        return ".svg", "image/svg+xml"
    if head.startswith(b"{") or head.startswith(b"["):
        return ".json", "application/json"
    if head.startswith(b"%PDF"):
        return ".pdf", "application/pdf"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png", "image/png"
    if head[:3] == b"\xff\xd8\xff":
        return ".jpg", "image/jpeg"
    return ".bin", "application/octet-stream"


def download_candidate_zip(run_id: str, candidate_id: str) -> StreamingResponse:
    """
    Create a ZIP containing the advisory blob and manifest.

    Bundle C Export Gating:
    - Only GREEN candidates can be exported
    - YELLOW, RED, or null decision = blocked

    Product-facing export for operators/manufacturing.
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    cand = _find_candidate_or_404(run, candidate_id)

    # Bundle C: Export gating - only GREEN can be exported
    decision = _get_attr(cand, "decision", None)
    if decision != "GREEN":
        if decision is None:
            raise HTTPException(
                status_code=403,
                detail="Export blocked: candidate NEEDS DECISION. Set decision to GREEN to export.",
            )
        else:
            raise HTTPException(
                status_code=403,
                detail=f"Export blocked: candidate decision is {decision}. Only GREEN candidates can be exported.",
            )

    advisory_id = _get_attr(cand, "advisory_id", "")
    if not advisory_id:
        raise HTTPException(status_code=400, detail="Candidate missing advisory_id")

    blob_path = get_attachment_path(advisory_id)
    if not blob_path:
        raise HTTPException(status_code=404, detail="Advisory blob not found in CAS")

    blob_bytes = get_bytes_attachment(advisory_id)
    if blob_bytes is None:
        blob_bytes = Path(blob_path).read_bytes()

    ext, mime = _infer_file_info(blob_bytes)
    fname = f"{advisory_id}{ext}"

    manifest = {
        "run_id": run_id,
        "candidate_id": candidate_id,
        "advisory_id": advisory_id,
        # Bundle C decision fields
        "decision": _get_attr(cand, "decision"),
        "decision_note": _get_attr(cand, "decision_note"),
        "decided_at_utc": _get_attr(cand, "decided_at_utc"),
        "decided_by": _get_attr(cand, "decided_by"),
        # Legacy compat
        "status": _get_attr(cand, "status", "PROPOSED"),
        # Metadata
        "label": _get_attr(cand, "label"),
        "note": _get_attr(cand, "note"),
        "mime": mime,
        "created_at_utc": _get_attr(cand, "created_at_utc"),
        "created_by": _get_attr(cand, "created_by"),
        "updated_at_utc": _get_attr(cand, "updated_at_utc"),
        "updated_by": _get_attr(cand, "updated_by"),
        # Audit: include decision history in exported manifest
        "decision_history": _get_attr(cand, "decision_history", []),
    }

    def _stream():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr(f"blob/{fname}", blob_bytes)
        buf.seek(0)
        yield from buf

    out_name = f"candidate_{candidate_id}_{advisory_id[:12]}.zip"
    return StreamingResponse(
        _stream(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
