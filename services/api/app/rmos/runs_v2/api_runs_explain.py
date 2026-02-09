"""
RMOS Runs v2 — On-demand AI-assisted explanation (advisory-only).

Endpoints:
- POST /{run_id}/explain
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from .store import get_run, update_run
from .attachments import put_json_attachment
from .hashing import sha256_of_obj
from app.rmos.explain_ai import generate_assistant_explanation

router = APIRouter()


@router.post("/{run_id}/explain")
def explain_run_on_demand(
    run_id: str,
    force: bool = Query(
        False,
        description="Regenerate and attach a new assistant explanation even if one exists.",
    ),
) -> Dict[str, Any]:
    """
    Phase 5: On-demand AI-assisted explanation generation (advisory-only).

    This endpoint NEVER changes feasibility/decision authority.
    It stores an attachment: kind='assistant_explanation' (content-addressed).

    - Returns existing explanation if present (idempotent)
    - Use ?force=true to regenerate
    """
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    attachments = list(run.attachments or [])
    existing = None
    for a in attachments:
        kind = getattr(a, "kind", None) if not isinstance(a, dict) else a.get("kind")
        if kind == "assistant_explanation":
            existing = a if isinstance(a, dict) else a.model_dump()
            break

    if existing is not None and not force:
        return {
            "ok": True,
            "run_id": run.run_id,
            "explanation_status": "READY",
            "attachment": existing,
            "note": "assistant_explanation already present (use ?force=true to regenerate)",
        }

    # Inputs hash ties advisory text to current run facts deterministically
    grounded_hash: Optional[str] = None
    try:
        grounded_hash = sha256_of_obj(
            {
                "run_id": run.run_id,
                "risk_level": (
                    getattr(run.decision, "risk_level", None)
                    if run.decision
                    else None
                ),
                "rules_triggered": (run.feasibility or {}).get(
                    "rules_triggered", []
                ),
                "request_summary": run.request_summary or {},
                "feasibility": run.feasibility or {},
            }
        )
    except (ValueError, TypeError, KeyError, AttributeError):
        grounded_hash = None

    explanation = generate_assistant_explanation(
        run,
        inputs_hash=grounded_hash,
        model_name="deterministic.v1",
    )
    explanation_dict = explanation.model_dump()

    att, _path, _sha = put_json_attachment(
        explanation_dict,
        kind="assistant_explanation",
        filename="assistant_explanation",
        ext=".json",
    )
    att_dict = att if isinstance(att, dict) else att.model_dump()

    # Replace existing assistant_explanation attachment if force, otherwise append
    new_attachments = []
    for a in attachments:
        kind = getattr(a, "kind", None) if not isinstance(a, dict) else a.get("kind")
        if kind == "assistant_explanation":
            continue
        new_attachments.append(a)
    new_attachments.append(att)

    run.attachments = new_attachments
    run.explanation_status = "READY"

    try:
        run.meta = dict(run.meta or {})
        run.meta["assistant_explanation_model"] = "deterministic.v1"
        run.meta["assistant_explanation_inputs_sha256"] = grounded_hash
    except (ValueError, TypeError, KeyError, AttributeError):
        pass

    update_run(run)

    return {
        "ok": True,
        "run_id": run.run_id,
        "explanation_status": "READY",
        "attachment": att_dict,
        "explanation": explanation_dict,
    }
