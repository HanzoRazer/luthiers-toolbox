from __future__ import annotations

from typing import Any, Dict, List, Optional


def _as_dict(x: Any) -> Any:
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return x


def _get_meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def _write_artifact(*, kind: str, status: str, index_meta: Dict[str, Any], payload: Dict[str, Any]) -> str:
    from app.rmos.run_artifacts.store import write_run_artifact

    art = write_run_artifact(
        kind=kind,
        status=status,
        session_id=index_meta.get("session_id"),
        index_meta=index_meta,
        payload=payload,
    )
    if isinstance(art, dict):
        return str(art.get("artifact_id") or art.get("id"))
    return str(getattr(art, "artifact_id", None) or getattr(art, "id", None))


def retry_batch_execution(
    *,
    batch_execution_artifact_id: str,
    op_ids: Optional[List[str]] = None,
    reason: str = "retry",
) -> Dict[str, Any]:
    """
    Create a NEW execution by re-running a subset of ops from a prior execution.

    - Reads parent execution artifact
    - Determines which op toolpaths children were BLOCKED/ERROR (or uses explicit op_ids)
    - Re-runs those ops using the original child payload design/context
    - Writes new child artifacts + a new parent execution artifact

    This preserves immutability: no updates-in-place.
    """
    from app.rmos.run_artifacts.store import read_run_artifact
    from app.saw_lab import SawLabService

    svc = SawLabService()

    parent = read_run_artifact(batch_execution_artifact_id)
    parent_d: Dict[str, Any] = parent if isinstance(parent, dict) else {
        "artifact_id": getattr(parent, "artifact_id", None) or getattr(parent, "id", None),
        "kind": getattr(parent, "kind", None),
        "status": getattr(parent, "status", None),
        "index_meta": getattr(parent, "index_meta", None),
        "payload": getattr(parent, "payload", None),
        "created_utc": getattr(parent, "created_utc", None),
    }

    if str(parent_d.get("kind") or "") != "saw_batch_execution":
        # Persist an error retry attempt artifact (still governed)
        rid = _write_artifact(
            kind="saw_batch_execution_retry",
            status="ERROR",
            index_meta={"tool_kind": "saw_lab", "kind_group": "batch"},
            payload={
                "error": {"type": "InvalidParentKind", "message": "Expected kind=saw_batch_execution"},
                "source_execution_artifact_id": batch_execution_artifact_id,
                "reason": reason,
            },
        )
        return {"status": "ERROR", "retry_artifact_id": rid}

    meta = _get_meta(parent_d)
    payload = parent_d.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}

    batch_label = meta.get("batch_label") or payload.get("batch_label")
    session_id = meta.get("session_id") or payload.get("session_id")
    decision_id = meta.get("parent_batch_decision_artifact_id") or payload.get("batch_decision_artifact_id")
    plan_id = meta.get("parent_batch_plan_artifact_id") or payload.get("batch_plan_artifact_id")
    spec_id = meta.get("parent_batch_spec_artifact_id") or payload.get("batch_spec_artifact_id")

    children = payload.get("children") or []
    if not isinstance(children, list):
        children = []

    # Load child artifacts (small N per batch)
    child_arts: List[Dict[str, Any]] = []
    for c in children:
        if not isinstance(c, dict) or not c.get("artifact_id"):
            continue
        it = read_run_artifact(c["artifact_id"])
        if isinstance(it, dict):
            child_arts.append(it)
        else:
            child_arts.append({
                "artifact_id": getattr(it, "artifact_id", None) or getattr(it, "id", None),
                "kind": getattr(it, "kind", None),
                "status": getattr(it, "status", None),
                "index_meta": getattr(it, "index_meta", None),
                "payload": getattr(it, "payload", None),
                "created_utc": getattr(it, "created_utc", None),
            })

    # Decide which ops to retry
    retry_ops: List[Dict[str, Any]] = []
    op_ids_set = set(str(x) for x in (op_ids or []))
    for ch in child_arts:
        if str(ch.get("kind") or "") != "saw_batch_op_toolpaths":
            continue
        ch_status = str(ch.get("status") or "").upper()
        ch_payload = ch.get("payload") or {}
        if not isinstance(ch_payload, dict):
            ch_payload = {}
        op_id = str(ch_payload.get("op_id") or _get_meta(ch).get("op_id") or "")
        if not op_id:
            continue

        if op_ids_set:
            if op_id in op_ids_set:
                retry_ops.append(ch)
        else:
            if ch_status in ("BLOCKED", "ERROR"):
                retry_ops.append(ch)

    ok = blocked = err = 0
    new_child_ids: List[str] = []
    results: List[Dict[str, Any]] = []

    for ch in retry_ops:
        ch_payload = ch.get("payload") or {}
        if not isinstance(ch_payload, dict):
            ch_payload = {}

        design = ch_payload.get("design") or {}
        context = ch_payload.get("context") or {}
        if not isinstance(design, dict):
            design = {}
        if not isinstance(context, dict):
            context = {}

        op_id = str(ch_payload.get("op_id") or "")
        setup_key = str(ch_payload.get("setup_key") or "")

        # Recompute feasibility (mandatory)
        try:
            feas = svc.check_feasibility(design, context)
            feas_d = _as_dict(feas)
            risk = str(feas_d.get("risk_bucket") or feas_d.get("risk") or "UNKNOWN").upper()
            score = float(feas_d.get("score") or feas_d.get("feasibility_score") or 0.0)
            warnings = feas_d.get("warnings") or []
            if not isinstance(warnings, list):
                warnings = [str(warnings)]
        except (ValueError, TypeError, KeyError) as e:  # WP-1: narrowed from except Exception
            risk, score, warnings = "ERROR", 0.0, [f"{type(e).__name__}: {e}"]
            feas_d = {"risk_bucket": "ERROR", "score": 0.0, "warnings": warnings}

        if risk in ("RED", "BLOCKED"):
            blocked += 1
            cid = _write_artifact(
                kind="saw_batch_op_toolpaths",
                status="BLOCKED",
                index_meta={
                    "tool_kind": "saw_lab",
                    "kind_group": "batch",
                    "batch_label": batch_label,
                    "session_id": session_id,
                    "parent_batch_decision_artifact_id": decision_id,
                    "parent_batch_plan_artifact_id": plan_id,
                    "parent_batch_spec_artifact_id": spec_id,
                    "op_id": op_id,
                    "setup_key": setup_key,
                    "retry_of_execution_artifact_id": batch_execution_artifact_id,
                },
                payload={
                    "retry_reason": reason,
                    "retry_of_execution_artifact_id": batch_execution_artifact_id,
                    "op_id": op_id,
                    "setup_key": setup_key,
                    "design": design,
                    "context": context,
                    "feasibility_recomputed": feas_d,
                    "blocked_reason": "Retry recompute indicates RED/BLOCKED",
                },
            )
            new_child_ids.append(cid)
            results.append({"op_id": op_id, "setup_key": setup_key, "status": "BLOCKED", "risk_bucket": risk, "score": score, "toolpaths_artifact_id": cid})
            continue

        # Generate toolpaths
        try:
            toolpaths = svc.generate_toolpaths(design, context)
            toolpaths_d = _as_dict(toolpaths)
            ok += 1
            ch_status = "OK"
        except (ValueError, TypeError, KeyError, OSError) as e:  # WP-1: narrowed from except Exception
            toolpaths_d = None
            err += 1
            ch_status = "ERROR"
            warnings = list(warnings) + [f"toolpaths_error: {type(e).__name__}: {e}"]

        cid = _write_artifact(
            kind="saw_batch_op_toolpaths",
            status=ch_status,
            index_meta={
                "tool_kind": "saw_lab",
                "kind_group": "batch",
                "batch_label": batch_label,
                "session_id": session_id,
                "parent_batch_decision_artifact_id": decision_id,
                "parent_batch_plan_artifact_id": plan_id,
                "parent_batch_spec_artifact_id": spec_id,
                "op_id": op_id,
                "setup_key": setup_key,
                "retry_of_execution_artifact_id": batch_execution_artifact_id,
            },
            payload={
                "retry_reason": reason,
                "retry_of_execution_artifact_id": batch_execution_artifact_id,
                "op_id": op_id,
                "setup_key": setup_key,
                "design": design,
                "context": context,
                "feasibility_recomputed": feas_d,
                "toolpaths": toolpaths_d,
                "warnings": warnings,
            },
        )
        new_child_ids.append(cid)
        results.append({"op_id": op_id, "setup_key": setup_key, "status": ch_status, "risk_bucket": "ERROR" if ch_status == "ERROR" else risk, "score": 0.0 if ch_status == "ERROR" else score, "toolpaths_artifact_id": cid})

    parent_status = "OK" if err == 0 else "ERROR"

    exec_parent_id = _write_artifact(
        kind="saw_batch_execution",
        status=parent_status,
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": batch_label,
            "session_id": session_id,
            "parent_batch_decision_artifact_id": decision_id,
            "parent_batch_plan_artifact_id": plan_id,
            "parent_batch_spec_artifact_id": spec_id,
            "retry_of_execution_artifact_id": batch_execution_artifact_id,
            "op_count": len(retry_ops),
            "ok_count": ok,
            "blocked_count": blocked,
            "error_count": err,
        },
        payload={
            "retry_reason": reason,
            "retry_of_execution_artifact_id": batch_execution_artifact_id,
            "batch_decision_artifact_id": decision_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "summary": {"op_count": len(retry_ops), "ok_count": ok, "blocked_count": blocked, "error_count": err},
            "children": [{"artifact_id": cid, "kind": "saw_batch_op_toolpaths"} for cid in new_child_ids],
            "results": results,
        },
    )

    retry_id = _write_artifact(
        kind="saw_batch_execution_retry",
        status="OK" if err == 0 else "ERROR",
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": batch_label,
            "session_id": session_id,
            "parent_batch_decision_artifact_id": decision_id,
            "parent_batch_plan_artifact_id": plan_id,
            "parent_batch_spec_artifact_id": spec_id,
            "source_execution_artifact_id": batch_execution_artifact_id,
            "new_execution_artifact_id": exec_parent_id,
        },
        payload={
            "reason": reason,
            "source_execution_artifact_id": batch_execution_artifact_id,
            "new_execution_artifact_id": exec_parent_id,
            "retried_op_count": len(retry_ops),
            "results": results,
        },
    )

    return {
        "status": parent_status,
        "retry_artifact_id": retry_id,
        "new_execution_artifact_id": exec_parent_id,
        "source_execution_artifact_id": batch_execution_artifact_id,
        "retried_op_count": len(retry_ops),
        "ok_count": ok,
        "blocked_count": blocked,
        "error_count": err,
        "results": results,
    }
