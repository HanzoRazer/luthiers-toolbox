"""
Saw Lab: Decision → Toolpaths Service

Governance-compliant toolpath generation from an approved decision artifact.
Recomputes feasibility server-side before generating toolpaths.
Always persists an artifact (OK/BLOCKED/ERROR) for traceability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_artifact(artifact_id: str) -> Dict[str, Any]:
    from app.rmos.runs_v2.store import get_run

    art = get_run(artifact_id)
    if art is None:
        raise ValueError(f"Run artifact {artifact_id} not found")
    if isinstance(art, dict):
        return art
    # Convert RunArtifact model to dict
    return {
        "artifact_id": art.run_id,
        "kind": art.mode,
        "status": art.status,
        "index_meta": art.meta,
        "payload": {"decision": art.decision, "outputs": art.outputs},
        "created_utc": art.created_at_utc,
    }


def _write_artifact(*, kind: str, status: str, index_meta: Dict[str, Any], payload: Dict[str, Any]) -> str:
    from app.rmos.runs_v2.store import persist_run, create_run_id
    from app.rmos.runs_v2.schemas import RunArtifact, Hashes, RunDecision
    from datetime import datetime, timezone
    import hashlib
    import json

    run_id = create_run_id()
    
    # Extract tool_id
    tool_id = str(index_meta.get("tool_id") or index_meta.get("tool_kind") or "saw:unknown")
    
    # Compute feasibility hash
    feas_str = json.dumps(payload.get("feasibility", {}), sort_keys=True)
    feasibility_sha256 = hashlib.sha256(feas_str.encode()).hexdigest()
    
    # Extract risk level for decision
    risk_level = "UNKNOWN"
    if status == "OK":
        risk_level = "GREEN"
    elif status == "BLOCKED":
        risk_level = "RED"
    elif status == "ERROR":
        risk_level = "ERROR"
    
    art = RunArtifact(
        run_id=run_id,
        created_at_utc=datetime.now(timezone.utc),
        mode="saw_compare",
        event_type=kind,  # Set event_type to enable filtering by kind
        status=status,
        tool_id=tool_id,
        workflow_session_id=index_meta.get("session_id"),
        hashes=Hashes(feasibility_sha256=feasibility_sha256),
        decision=RunDecision(risk_level=risk_level),
        meta={
            "batch_label": index_meta.get("batch_label"),
            "session_id": index_meta.get("session_id"),
            "payload": payload,
            "index_meta": index_meta,
        },
    )
    persisted = persist_run(art)
    return persisted.run_id


def _as_dict(x: Any) -> Any:
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return x


def generate_toolpaths_from_decision(*, decision_artifact_id: str) -> Dict[str, Any]:
    """
    Governance-compliant decision -> toolpaths:

    1) Read decision artifact (must be kind='saw_compare_decision')
    2) Resolve selected child feasibility artifact payload (design/context)
    3) Recompute feasibility server-side (invariant)
    4) If RED/BLOCKED -> persist BLOCKED toolpaths artifact (no toolpaths)
       Else generate toolpaths and persist OK toolpaths artifact
    5) Return toolpaths artifact id immediately
    """
    # Import in services layer is allowed (orchestration)
    from app.saw_lab import SawLabService

    # Always persist something, even if validation fails
    try:
        decision = _read_artifact(decision_artifact_id)
        d_kind = str(decision.get("kind") or "")
        d_payload = decision.get("payload") or {}
        d_meta = decision.get("index_meta") or {}
        if not isinstance(d_payload, dict):
            d_payload = {}
        if not isinstance(d_meta, dict):
            d_meta = {}

        parent_batch_artifact_id = (d_payload.get("parent") or {}).get("artifact_id")
        selected_child_artifact_id = (d_payload.get("selected") or {}).get("artifact_id")

        # Validate decision kind
        if d_kind != "saw_compare_decision" or not selected_child_artifact_id:
            toolpaths_id = _write_artifact(
                kind="saw_compare_toolpaths",
                status="ERROR",
                index_meta={
                    "tool_kind": "saw_lab",
                    "parent_decision_artifact_id": decision_artifact_id,
                    "batch_label": d_meta.get("batch_label"),
                    "session_id": d_meta.get("session_id"),
                },
                payload={
                    "created_utc": _utc_now_iso(),
                    "error": {
                        "type": "InvalidDecisionArtifact",
                        "message": f"Expected kind='saw_compare_decision' with selected child; got kind='{d_kind}'",
                    },
                    "decision_artifact_id": decision_artifact_id,
                },
            )
            return {
                "toolpaths_artifact_id": toolpaths_id,
                "decision_artifact_id": decision_artifact_id,
                "parent_batch_artifact_id": parent_batch_artifact_id,
                "selected_child_artifact_id": selected_child_artifact_id,
                "status": "ERROR",
            }

        # Load selected child feasibility artifact to recover design/context
        child = _read_artifact(selected_child_artifact_id)
        c_payload = child.get("payload") or {}
        if not isinstance(c_payload, dict):
            c_payload = {}

        design = c_payload.get("design") or {}
        context = c_payload.get("context") or {}
        prior_feas = c_payload.get("feasibility") or {}

        svc = SawLabService()

        # Server-side feasibility recompute (platform invariant)
        recomputed = svc.check_feasibility(design, context)
        recomputed_d = _as_dict(recomputed)

        # Extract risk bucket in a tolerant way
        risk = str(recomputed_d.get("risk_bucket") or recomputed_d.get("risk") or "UNKNOWN").upper()
        if risk in ("RED", "BLOCKED", "FAIL", "FAILED"):
            # Persist BLOCKED toolpaths artifact (no toolpaths) for traceability
            toolpaths_id = _write_artifact(
                kind="saw_compare_toolpaths",
                status="BLOCKED",
                index_meta={
                    "tool_kind": "saw_lab",
                    "batch_label": d_meta.get("batch_label"),
                    "session_id": d_meta.get("session_id"),
                    "parent_batch_artifact_id": parent_batch_artifact_id,
                    "parent_decision_artifact_id": decision_artifact_id,
                    "selected_child_artifact_id": selected_child_artifact_id,
                },
                payload={
                    "created_utc": _utc_now_iso(),
                    "decision_artifact_id": decision_artifact_id,
                    "parent_batch_artifact_id": parent_batch_artifact_id,
                    "selected_child_artifact_id": selected_child_artifact_id,
                    "design": design,
                    "context": context,
                    "feasibility_prior": prior_feas,
                    "feasibility_recomputed": recomputed_d,
                    "blocked_reason": "Server-side feasibility recompute indicates RED/BLOCKED",
                },
            )
            return {
                "toolpaths_artifact_id": toolpaths_id,
                "decision_artifact_id": decision_artifact_id,
                "parent_batch_artifact_id": parent_batch_artifact_id,
                "selected_child_artifact_id": selected_child_artifact_id,
                "status": "BLOCKED",
            }

        # Generate toolpaths (domain service)
        toolpaths = svc.generate_toolpaths(design, context)
        toolpaths_d = _as_dict(toolpaths)

        toolpaths_id = _write_artifact(
            kind="saw_compare_toolpaths",
            status="OK",
            index_meta={
                "tool_kind": "saw_lab",
                "batch_label": d_meta.get("batch_label"),
                "session_id": d_meta.get("session_id"),
                "parent_batch_artifact_id": parent_batch_artifact_id,
                "parent_decision_artifact_id": decision_artifact_id,
                "selected_child_artifact_id": selected_child_artifact_id,
            },
            payload={
                "created_utc": _utc_now_iso(),
                "decision_artifact_id": decision_artifact_id,
                "parent_batch_artifact_id": parent_batch_artifact_id,
                "selected_child_artifact_id": selected_child_artifact_id,
                "design": design,
                "context": context,
                "feasibility_prior": prior_feas,
                "feasibility_recomputed": recomputed_d,
                "toolpaths": toolpaths_d,
            },
        )

        return {
            "toolpaths_artifact_id": toolpaths_id,
            "decision_artifact_id": decision_artifact_id,
            "parent_batch_artifact_id": parent_batch_artifact_id,
            "selected_child_artifact_id": selected_child_artifact_id,
            "status": "OK",
        }

    except Exception as e:  # WP-1: keep broad — governance requires ERROR artifact even on unexpected failures
        toolpaths_id = _write_artifact(
            kind="saw_compare_toolpaths",
            status="ERROR",
            index_meta={
                "tool_kind": "saw_lab",
                "parent_decision_artifact_id": decision_artifact_id,
            },
            payload={
                "created_utc": _utc_now_iso(),
                "decision_artifact_id": decision_artifact_id,
                "error": {"type": type(e).__name__, "message": str(e)},
            },
        )
        return {
            "toolpaths_artifact_id": toolpaths_id,
            "decision_artifact_id": decision_artifact_id,
            "status": "ERROR",
        }
