from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .decision_apply_service import apply_decision_to_context


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _extract_created_utc(art: Dict[str, Any]) -> str:
    p = _as_dict(art.get("payload") or art.get("data"))
    if isinstance(p.get("created_utc"), str):
        return p["created_utc"]
    if isinstance(art.get("created_utc"), str):
        return art["created_utc"]
    return ""


def _required_str(d: Dict[str, Any], key: str) -> str:
    v = d.get(key)
    if v is None:
        return ""
    return str(v)


def _load_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    """
    Centralized loader. Uses RMOS runs_v2 store as authoritative artifact store.
    """
    from app.rmos.runs_v2 import store as runs_store

    return runs_store.get_run(artifact_id)


def _persist_artifact(*, kind: str, payload: Dict[str, Any], parent_id: str, session_id: str) -> str:
    from app.rmos.runs_v2 import store as runs_store

    # Store expects governance invariants: OK/BLOCKED/ERROR all get artifacts.
    return runs_store.store_artifact(kind=kind, payload=payload, parent_id=parent_id, session_id=session_id)


def _build_base_context_from_spec_and_plan(
    spec_payload: Dict[str, Any],
    plan_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic base context for saw toolpaths.
    Precedence:
      plan.payload.context (if present) overrides spec.payload.context
      then flat spec/plan fields for common keys
    """
    ctx: Dict[str, Any] = {}

    spec_ctx = _as_dict(spec_payload.get("context"))
    plan_ctx = _as_dict(plan_payload.get("context"))
    ctx.update(spec_ctx)
    ctx.update(plan_ctx)

    # Common fields that are often stored flat in payload
    for k in (
        "tool_id",
        "material_id",
        "machine_id",
        "kerf_width",
        "stock_thickness",
        "feed_rate",
        "spindle_rpm",
        "safe_z_mm",
        "doc_mm",
        "depth_of_cut_mm",
    ):
        if k in spec_payload and k not in ctx:
            ctx[k] = spec_payload.get(k)
        if k in plan_payload and k not in ctx:
            ctx[k] = plan_payload.get(k)

    return ctx


def generate_toolpaths_from_decision(
    *,
    batch_decision_artifact_id: str,
    include_gcode: bool = True,
) -> Dict[str, Any]:
    """
    Canonical saw-lab generation:
      decision -> (plan + spec) -> base_context
      apply_decision_to_context(applied_patch, applied_multipliers)
      generate toolpaths (best-effort)
      persist saw_batch_toolpaths artifact parented to the decision
      return artifact id + preview
    """
    dec = _load_artifact(batch_decision_artifact_id)
    if not dec:
        return {
            "status": "ERROR",
            "error": "Decision artifact not found",
            "batch_toolpaths_artifact_id": None,
        }

    dec_payload = _as_dict(dec.get("payload") or dec.get("data"))
    session_id = _required_str(dec_payload, "session_id")
    batch_label = _required_str(dec_payload, "batch_label")
    plan_id = _required_str(dec_payload, "batch_plan_artifact_id")
    spec_id = _required_str(dec_payload, "batch_spec_artifact_id")

    plan = _load_artifact(plan_id) if plan_id else None
    spec = _load_artifact(spec_id) if spec_id else None

    if not plan or not spec:
        # Still persist an ERROR artifact for traceability.
        err_payload = {
            "status": "ERROR",
            "error": "Missing plan/spec for decision",
            "batch_decision_artifact_id": batch_decision_artifact_id,
            "batch_plan_artifact_id": plan_id or None,
            "batch_spec_artifact_id": spec_id or None,
            "session_id": session_id,
            "batch_label": batch_label,
            "parent_batch_decision_artifact_id": batch_decision_artifact_id,
            "parent_batch_plan_artifact_id": plan_id or None,
            "parent_batch_spec_artifact_id": spec_id or None,
        }
        toolpaths_id = _persist_artifact(
            kind="saw_batch_toolpaths",
            payload=err_payload,
            parent_id=batch_decision_artifact_id,
            session_id=session_id,
        )
        return {
            "status": "ERROR",
            "error": err_payload["error"],
            "batch_toolpaths_artifact_id": toolpaths_id,
        }

    plan_payload = _as_dict(plan.get("payload") or plan.get("data"))
    spec_payload = _as_dict(spec.get("payload") or spec.get("data"))

    base_context = _build_base_context_from_spec_and_plan(spec_payload, plan_payload)

    applied_patch = _as_dict(dec_payload.get("applied_context_patch"))
    applied_mult = _as_dict(dec_payload.get("applied_multipliers"))
    tuned_context, apply_stamp = apply_decision_to_context(
        base_context=base_context,
        applied_context_patch=applied_patch if applied_patch else None,
        applied_multipliers=applied_mult if applied_mult else None,
    )

    # The plan encodes the approved setup/op order
    selected_setup_key = _required_str(dec_payload, "selected_setup_key")
    selected_op_ids = dec_payload.get("selected_op_ids") or []

    # Generate toolpaths (best-effort; always persist artifact)
    try:
        # This module is the *only* place that calls saw toolpath generation.
        # Keep RMOS from importing saw_lab by containing the coupling here.
        from app.saw_lab_run_service import plan_saw_toolpaths_for_design

        result = plan_saw_toolpaths_for_design(
            spec_payload=spec_payload,
            plan_payload=plan_payload,
            selected_setup_key=selected_setup_key,
            selected_op_ids=selected_op_ids,
            context=tuned_context,
            include_gcode=include_gcode,
        )

        ok_payload = {
            "status": "OK",
            "batch_decision_artifact_id": batch_decision_artifact_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "session_id": session_id,
            "batch_label": batch_label,
            "selected_setup_key": selected_setup_key,
            "selected_op_ids": selected_op_ids,
            "tuned_context": tuned_context,
            "decision_apply_stamp": apply_stamp,
            "toolpaths": _as_dict(result),
            # Linkage invariants (used by tree resolver / audit export / UI)
            "parent_batch_decision_artifact_id": batch_decision_artifact_id,
            "parent_batch_plan_artifact_id": plan_id,
            "parent_batch_spec_artifact_id": spec_id,
        }

        toolpaths_id = _persist_artifact(
            kind="saw_batch_toolpaths",
            payload=ok_payload,
            parent_id=batch_decision_artifact_id,
            session_id=session_id,
        )
        return {
            "status": "OK",
            "batch_toolpaths_artifact_id": toolpaths_id,
            "decision_apply_stamp": apply_stamp,
            "preview": {
                "gcode_preview": (_as_dict(result).get("gcode_text") or "")[:500] if include_gcode else None,
                "statistics": _as_dict(result).get("statistics"),
            },
        }
    except Exception as e:  # WP-1: keep broad — saw lab toolpath generation must persist error artifacts
        err_payload = {
            "status": "ERROR",
            "error": f"{type(e).__name__}: {e}",
            "batch_decision_artifact_id": batch_decision_artifact_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "session_id": session_id,
            "batch_label": batch_label,
            "selected_setup_key": selected_setup_key,
            "selected_op_ids": selected_op_ids,
            "tuned_context": tuned_context,
            "decision_apply_stamp": apply_stamp,
            # Linkage invariants
            "parent_batch_decision_artifact_id": batch_decision_artifact_id,
            "parent_batch_plan_artifact_id": plan_id,
            "parent_batch_spec_artifact_id": spec_id,
        }
        toolpaths_id = _persist_artifact(
            kind="saw_batch_toolpaths",
            payload=err_payload,
            parent_id=batch_decision_artifact_id,
            session_id=session_id,
        )
        return {
            "status": "ERROR",
            "error": err_payload["error"],
            "batch_toolpaths_artifact_id": toolpaths_id,
        }
