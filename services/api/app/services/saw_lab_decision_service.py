"""
Saw Lab Decision Capture Service

Creates decision artifacts that record operator approval of a specific
candidate from a compare batch. Never mutates the batch artifact.

Governance rules:
- Immutable run history: batch artifact stays unchanged
- Decision is explicit: separate artifact is diffable/auditable
- Forensics preserved: even validation failures create ERROR decision artifacts
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    """
    Read artifact for validation.
    Returns dict with artifact fields or None if not found.
    """
    from app.rmos.runs_v2.store import get_run

    art = get_run(artifact_id)
    if art is None:
        return None

    return {
        "artifact_id": art.run_id,
        "kind": getattr(art, "event_type", None),
        "status": art.status,
        "meta": art.meta,
        "payload": getattr(art, "feasibility", None),  # For child artifacts
    }


def _write_decision_artifact(
    *,
    status: str,
    index_meta: Dict[str, Any],
    payload: Dict[str, Any],
) -> str:
    """
    Create a decision artifact using the runs_v2 store.
    Returns the artifact_id (run_id).
    """
    from app.rmos.runs_v2.store import persist_run, create_run_id
    from app.rmos.runs_v2.schemas import RunArtifact, Hashes, RunDecision
    import hashlib
    import json

    run_id = create_run_id()

    # Compute hash from payload
    payload_str = json.dumps(payload, sort_keys=True)
    payload_sha256 = hashlib.sha256(payload_str.encode()).hexdigest()

    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=datetime.now(timezone.utc),
        event_type="saw_compare_decision",
        status=status,
        tool_id=index_meta.get("tool_id", "saw:decision"),
        mode="saw_compare",
        material_id=index_meta.get("material_id", "unknown"),
        machine_id=index_meta.get("machine_id", "unknown"),
        workflow_session_id=index_meta.get("session_id"),
        request_summary=payload,
        feasibility=payload,
        decision=RunDecision(
            risk_level="GREEN" if status == "OK" else "RED",
            score=1.0 if status == "OK" else 0.0,
            warnings=[],
            details={},
        ),
        hashes=Hashes(feasibility_sha256=payload_sha256),
        advisory_inputs=[],
        explanation_status="NONE",
        meta={
            "batch_label": index_meta.get("batch_label"),
            "session_id": index_meta.get("session_id"),
            "parent_batch_artifact_id": index_meta.get("parent_batch_artifact_id"),
            "selected_child_artifact_id": index_meta.get("selected_child_artifact_id"),
            "approved_by": index_meta.get("approved_by"),
        },
    )

    persist_run(artifact)
    return run_id


def create_saw_compare_decision(
    *,
    parent_batch_artifact_id: str,
    selected_child_artifact_id: str,
    approved_by: str,
    reason: str,
    ticket_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a decision artifact that references an existing saw compare batch + chosen child.
    Does NOT mutate the batch artifact.
    Always writes an artifact, even if validation fails (ERROR artifact).
    """
    try:
        parent = _read_artifact(parent_batch_artifact_id)
        child = _read_artifact(selected_child_artifact_id)

        # Handle missing artifacts
        if parent is None:
            raise ValueError(f"Parent batch artifact not found: {parent_batch_artifact_id}")
        if child is None:
            raise ValueError(f"Child artifact not found: {selected_child_artifact_id}")

        parent_kind = str(parent.get("kind") or "")
        child_kind = str(child.get("kind") or "")

        # Validate kinds (soft-fail into ERROR artifact if mismatch)
        ok_parent = parent_kind == "saw_compare_batch"
        ok_child = child_kind == "saw_compare_feasibility"

        parent_meta = parent.get("meta") or {}
        if not isinstance(parent_meta, dict):
            parent_meta = {}

        session_id = parent_meta.get("session_id")
        batch_label = parent_meta.get("batch_label")

        decision_payload = {
            "approved_by": approved_by,
            "reason": reason,
            "ticket_id": ticket_id,
            "approved_utc": _utc_now_iso(),
            "parent": {
                "artifact_id": parent_batch_artifact_id,
                "kind": parent_kind,
                "status": parent.get("status"),
                "batch_label": batch_label,
                "session_id": session_id,
            },
            "selected": {
                "artifact_id": selected_child_artifact_id,
                "kind": child_kind,
                "status": child.get("status"),
            },
            "validation": {
                "parent_kind_ok": ok_parent,
                "child_kind_ok": ok_child,
            },
        }

        status = "OK" if ok_parent and ok_child else "ERROR"

        decision_index_meta = {
            "session_id": session_id,
            "batch_label": batch_label,
            "tool_kind": "saw_lab",
            "parent_batch_artifact_id": parent_batch_artifact_id,
            "selected_child_artifact_id": selected_child_artifact_id,
            "approved_by": approved_by,
        }

        decision_id = _write_decision_artifact(
            status=status,
            index_meta=decision_index_meta,
            payload=decision_payload,
        )

        return {
            "decision_artifact_id": decision_id,
            "parent_batch_artifact_id": parent_batch_artifact_id,
            "selected_child_artifact_id": selected_child_artifact_id,
            "approved_by": approved_by,
            "reason": reason,
            "ticket_id": ticket_id,
        }

    except Exception as e:  # WP-1: keep broad — governance requires ERROR artifact even on unexpected failures
        # Governance rule: even failures must persist an ERROR artifact
        decision_id = _write_decision_artifact(
            status="ERROR",
            index_meta={
                "tool_kind": "saw_lab",
                "parent_batch_artifact_id": parent_batch_artifact_id,
                "selected_child_artifact_id": selected_child_artifact_id,
                "approved_by": approved_by,
            },
            payload={
                "approved_by": approved_by,
                "reason": reason,
                "ticket_id": ticket_id,
                "approved_utc": _utc_now_iso(),
                "error": {"type": type(e).__name__, "message": str(e)},
            },
        )
        return {
            "decision_artifact_id": decision_id,
            "parent_batch_artifact_id": parent_batch_artifact_id,
            "selected_child_artifact_id": selected_child_artifact_id,
            "approved_by": approved_by,
            "reason": reason,
            "ticket_id": ticket_id,
        }
