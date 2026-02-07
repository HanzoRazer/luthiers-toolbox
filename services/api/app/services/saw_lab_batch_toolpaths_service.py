"""
Saw Lab Batch Toolpaths Service

Generates toolpaths from a batch decision artifact.
Enforces governance invariants:
  - Server-side feasibility recompute before generating any toolpaths
  - Artifacts written even on failures
  - Parent execution artifact references all child artifacts + summary stats
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.services.saw_lab_learning_apply_service import (
    is_apply_accepted_overrides_enabled,
    tune_context_from_accepted_learning,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(x: Any) -> Any:
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return x


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


def _read_artifact(artifact_id: str) -> Dict[str, Any]:
    from app.rmos.run_artifacts.store import read_run_artifact

    art = read_run_artifact(artifact_id)
    if isinstance(art, dict):
        return art
    return {
        "artifact_id": getattr(art, "artifact_id", None) or getattr(art, "id", None),
        "kind": getattr(art, "kind", None),
        "status": getattr(art, "status", None),
        "index_meta": getattr(art, "index_meta", None),
        "payload": getattr(art, "payload", None),
        "created_utc": getattr(art, "created_utc", None),
    }


def _risk_and_score(feas_d: Dict[str, Any]) -> Tuple[str, float, List[str]]:
    risk = str(feas_d.get("risk_bucket") or feas_d.get("risk") or "UNKNOWN").upper()
    score = float(feas_d.get("score") or feas_d.get("feasibility_score") or 0.0)
    warnings = feas_d.get("warnings") or []
    if not isinstance(warnings, list):
        warnings = [str(warnings)]
    return risk, score, [str(w) for w in warnings]


def generate_batch_toolpaths_from_decision(*, batch_decision_artifact_id: str) -> Dict[str, Any]:
    """
    Reads saw_batch_decision -> saw_batch_plan -> executes chosen setup/op order.

    For each op:
      - server-side feasibility recompute (mandatory)
      - if RED/BLOCKED => write child artifact status=BLOCKED, no toolpaths
      - else generate toolpaths => write child artifact status=OK

    Writes a parent saw_batch_execution artifact referencing all children.
    Always persists artifacts even on errors.
    """
    from app.saw_lab import SawLabService

    svc = SawLabService()

    # Default outputs
    ok_count = blocked_count = error_count = 0
    child_results: List[Dict[str, Any]] = []
    child_ids: List[str] = []

    try:
        decision = _read_artifact(batch_decision_artifact_id)
        d_kind = str(decision.get("kind") or "")
        d_payload = decision.get("payload") or {}
        d_meta = decision.get("index_meta") or {}
        if not isinstance(d_payload, dict):
            d_payload = {}
        if not isinstance(d_meta, dict):
            d_meta = {}

        batch_label = d_meta.get("batch_label") or d_payload.get("batch_label")
        session_id = d_meta.get("session_id") or d_payload.get("session_id")

        plan_id = d_payload.get("batch_plan_artifact_id")
        spec_id = d_payload.get("batch_spec_artifact_id")

        if d_kind != "saw_batch_decision" or not plan_id:
            parent_id = _write_artifact(
                kind="saw_batch_execution",
                status="ERROR",
                index_meta={
                    "tool_kind": "saw_lab",
                    "kind_group": "batch",
                    "batch_label": batch_label,
                    "session_id": session_id,
                    "parent_batch_decision_artifact_id": batch_decision_artifact_id,
                },
                payload={
                    "created_utc": _utc_now_iso(),
                    "error": {
                        "type": "InvalidDecisionArtifact",
                        "message": f"Expected kind='saw_batch_decision' with batch_plan_artifact_id; got kind='{d_kind}'",
                    },
                    "batch_decision_artifact_id": batch_decision_artifact_id,
                },
            )
            return {
                "batch_execution_artifact_id": parent_id,
                "batch_decision_artifact_id": batch_decision_artifact_id,
                "batch_plan_artifact_id": plan_id,
                "batch_spec_artifact_id": spec_id,
                "batch_label": batch_label,
                "session_id": session_id,
                "status": "ERROR",
                "op_count": 0,
                "ok_count": 0,
                "blocked_count": 0,
                "error_count": 1,
                "results": [],
            }

        plan = _read_artifact(plan_id)
        p_kind = str(plan.get("kind") or "")
        p_payload = plan.get("payload") or {}
        p_meta = plan.get("index_meta") or {}
        if not isinstance(p_payload, dict):
            p_payload = {}
        if not isinstance(p_meta, dict):
            p_meta = {}

        # Pull chosen order from decision
        chosen = d_payload.get("chosen_order") or {}
        if not isinstance(chosen, dict):
            chosen = {}

        setup_order = chosen.get("setup_order") or []
        op_order = chosen.get("op_order") or []
        if not isinstance(setup_order, list) or not isinstance(op_order, list):
            setup_order, op_order = [], []

        # Build op lookup from plan payload
        setups = p_payload.get("setups") or []
        if not isinstance(setups, list):
            setups = []

        setup_by_key: Dict[str, Dict[str, Any]] = {}
        op_by_id: Dict[str, Dict[str, Any]] = {}

        for s in setups:
            if not isinstance(s, dict):
                continue
            skey = str(s.get("setup_key") or "")
            if not skey:
                continue
            setup_by_key[skey] = s
            ops = s.get("ops") or []
            if isinstance(ops, list):
                for op in ops:
                    if isinstance(op, dict) and op.get("op_id"):
                        op_by_id[str(op["op_id"])] = op

        # Optional: apply ACCEPTed learned multipliers (feature-flagged)
        learning_tuning_stamp = None
        learning_resolved = None
        learning_base_context: Dict[str, Any] = {}

        if is_apply_accepted_overrides_enabled():
            # Try to infer tool/material/thickness from spec payload when available
            spec_payload: Dict[str, Any] = {}
            if spec_id:
                try:
                    spec_art = _read_artifact(spec_id)
                    spec_payload = spec_art.get("payload") or {}
                    if not isinstance(spec_payload, dict):
                        spec_payload = {}
                except (OSError, ValueError, KeyError):  # WP-1: narrowed from except Exception
                    spec_payload = {}

            infer_tool_id = d_payload.get("tool_id") or spec_payload.get("tool_id")
            infer_material_id = None
            infer_thickness_mm = None
            try:
                items = spec_payload.get("items")
                if isinstance(items, list) and items:
                    infer_material_id = items[0].get("material_id")
                    infer_thickness_mm = items[0].get("thickness_mm")
            except (KeyError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
                pass

            # Build a base context with defaults to tune
            base_context = {
                "spindle_rpm": 18000,
                "feed_rate": 800,
                "doc_mm": 3.0,
            }
            tuned = tune_context_from_accepted_learning(
                context=base_context,
                tool_id=infer_tool_id,
                material_id=infer_material_id,
                thickness_mm=infer_thickness_mm,
                limit_events=200,
            )
            learning_resolved = tuned.get("resolved")
            learning_tuning_stamp = tuned.get("tuning_stamp")
            learning_base_context = tuned.get("tuned_context") or base_context

        # Execute in explicit operator order
        for op_id in op_order:
            op_id_s = str(op_id)
            op = op_by_id.get(op_id_s)
            if not op:
                # Record missing op as ERROR child artifact
                error_count += 1
                child_id = _write_artifact(
                    kind="saw_batch_op_toolpaths",
                    status="ERROR",
                    index_meta={
                        "tool_kind": "saw_lab",
                        "kind_group": "batch",
                        "batch_label": batch_label,
                        "session_id": session_id,
                        "parent_batch_decision_artifact_id": batch_decision_artifact_id,
                        "parent_batch_plan_artifact_id": plan_id,
                        "op_id": op_id_s,
                    },
                    payload={
                        "created_utc": _utc_now_iso(),
                        "batch_decision_artifact_id": batch_decision_artifact_id,
                        "batch_plan_artifact_id": plan_id,
                        "batch_spec_artifact_id": spec_id,
                        "op_id": op_id_s,
                        "error": {"type": "MissingOp", "message": "op_id not found in plan payload"},
                    },
                )
                child_ids.append(child_id)
                child_results.append(
                    {
                        "op_id": op_id_s,
                        "setup_key": "",
                        "status": "ERROR",
                        "risk_bucket": "ERROR",
                        "score": 0.0,
                        "toolpaths_artifact_id": child_id,
                        "warnings": ["op_id not found in plan payload"],
                    }
                )
                continue

            setup_key = str(op.get("setup_key") or "")
            setup = setup_by_key.get(setup_key) if setup_key else None

            # Reconstruct a minimal design/context for toolpaths generation.
            material_id = str(op.get("material_id") or (setup or {}).get("material_id") or "unknown")
            thickness_mm = float(op.get("thickness_mm") or (setup or {}).get("thickness_mm") or 0.0)
            length_mm = float(op.get("length_mm") or 0.0)

            tool_id = str((setup or {}).get("tool_id") or "saw:thin_140")
            preset_id = (setup or {}).get("preset_id")
            machine_id = (setup or {}).get("machine_id")

            qty = int(op.get("qty") or 1)

            design = {
                "cut_length_mm": length_mm,
                "cut_depth_mm": thickness_mm,
                "material": material_id,
                "qty": qty,
                "part_id": op.get("part_id"),
                "op_id": op_id_s,
            }
            context = {
                "tool_id": tool_id,
                "preset_id": preset_id,
                "machine_id": machine_id,
                "material_id": material_id,
                "stock_thickness_mm": thickness_mm,
                # Use learning-tuned defaults if available, else conservative defaults
                "spindle_rpm": learning_base_context.get("spindle_rpm", 18000),
                "feed_rate": learning_base_context.get("feed_rate", 800),
                "kerf_width": 1.0,
            }

            # Mandatory server-side feasibility recompute
            feas_d: Dict[str, Any] = {}
            try:
                feas = svc.check_feasibility(design, context)
                feas_d = _as_dict(feas)
                risk, score, warnings = _risk_and_score(feas_d)
            except (ValueError, TypeError, KeyError) as e:  # WP-1: narrowed from except Exception
                risk, score, warnings = "ERROR", 0.0, [f"{type(e).__name__}: {e}"]
                feas_d = {"risk_bucket": risk, "score": score}

            # If blocked, persist child artifact and skip toolpaths
            if risk in ("RED", "BLOCKED"):
                blocked_count += 1
                child_id = _write_artifact(
                    kind="saw_batch_op_toolpaths",
                    status="BLOCKED",
                    index_meta={
                        "tool_kind": "saw_lab",
                        "kind_group": "batch",
                        "batch_label": batch_label,
                        "session_id": session_id,
                        "parent_batch_decision_artifact_id": batch_decision_artifact_id,
                        "parent_batch_plan_artifact_id": plan_id,
                        "parent_batch_spec_artifact_id": spec_id,
                        "op_id": op_id_s,
                        "setup_key": setup_key,
                    },
                    payload={
                        "created_utc": _utc_now_iso(),
                        "batch_decision_artifact_id": batch_decision_artifact_id,
                        "batch_plan_artifact_id": plan_id,
                        "batch_spec_artifact_id": spec_id,
                        "op_id": op_id_s,
                        "setup_key": setup_key,
                        "design": design,
                        "context": context,
                        "feasibility_recomputed": feas_d,
                        "blocked_reason": "Server-side feasibility recompute indicates RED/BLOCKED",
                    },
                )
                child_ids.append(child_id)
                child_results.append(
                    {
                        "op_id": op_id_s,
                        "setup_key": setup_key,
                        "status": "BLOCKED",
                        "risk_bucket": risk,
                        "score": score,
                        "toolpaths_artifact_id": child_id,
                        "warnings": warnings,
                    }
                )
                continue

            # Generate toolpaths
            try:
                toolpaths = svc.generate_toolpaths(design, context)
                toolpaths_d = _as_dict(toolpaths)
                ok_count += 1
                child_status = "OK"
            except (ValueError, TypeError, KeyError, OSError) as e:  # WP-1: narrowed from except Exception
                toolpaths_d = None
                error_count += 1
                child_status = "ERROR"
                warnings = warnings + [f"toolpaths_error: {type(e).__name__}: {e}"]

            child_id = _write_artifact(
                kind="saw_batch_op_toolpaths",
                status=child_status,
                index_meta={
                    "tool_kind": "saw_lab",
                    "kind_group": "batch",
                    "batch_label": batch_label,
                    "session_id": session_id,
                    "parent_batch_decision_artifact_id": batch_decision_artifact_id,
                    "parent_batch_plan_artifact_id": plan_id,
                    "parent_batch_spec_artifact_id": spec_id,
                    "op_id": op_id_s,
                    "setup_key": setup_key,
                },
                payload={
                    "created_utc": _utc_now_iso(),
                    "batch_decision_artifact_id": batch_decision_artifact_id,
                    "batch_plan_artifact_id": plan_id,
                    "batch_spec_artifact_id": spec_id,
                    "op_id": op_id_s,
                    "setup_key": setup_key,
                    "design": design,
                    "context": context,
                    "feasibility_recomputed": feas_d,
                    "toolpaths": toolpaths_d,
                    "warnings": warnings,
                },
            )

            child_ids.append(child_id)
            child_results.append(
                {
                    "op_id": op_id_s,
                    "setup_key": setup_key,
                    "status": child_status,
                    "risk_bucket": risk if child_status != "ERROR" else "ERROR",
                    "score": score if child_status != "ERROR" else 0.0,
                    "toolpaths_artifact_id": child_id,
                    "warnings": warnings,
                }
            )

        # Parent execution artifact (always)
        parent_status = "OK" if error_count == 0 else "ERROR"
        parent_payload = {
            "created_utc": _utc_now_iso(),
            "batch_decision_artifact_id": batch_decision_artifact_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "summary": {
                "op_count": len(op_order),
                "ok_count": ok_count,
                "blocked_count": blocked_count,
                "error_count": error_count,
            },
            "children": [{"artifact_id": cid, "kind": "saw_batch_op_toolpaths"} for cid in child_ids],
            "results": child_results,
            "learning": {
                "apply_enabled": bool(is_apply_accepted_overrides_enabled()),
                "resolved": learning_resolved,
                "tuning_stamp": learning_tuning_stamp,
            },
        }

        # Extract source_count for index_meta (safe access)
        learning_source_count = None
        if isinstance(learning_resolved, dict):
            learning_source_count = learning_resolved.get("source_count")

        parent_id = _write_artifact(
            kind="saw_batch_execution",
            status=parent_status,
            index_meta={
                "tool_kind": "saw_lab",
                "kind_group": "batch",
                "batch_label": batch_label,
                "session_id": session_id,
                "parent_batch_decision_artifact_id": batch_decision_artifact_id,
                "parent_batch_plan_artifact_id": plan_id,
                "parent_batch_spec_artifact_id": spec_id,
                "op_count": len(op_order),
                "ok_count": ok_count,
                "blocked_count": blocked_count,
                "error_count": error_count,
                "learning_apply_enabled": bool(is_apply_accepted_overrides_enabled()),
                "learning_source_count": learning_source_count,
                "learning_applied": (learning_tuning_stamp or {}).get("applied") if isinstance(learning_tuning_stamp, dict) else False,
            },
            payload=parent_payload,
        )

        return {
            "batch_execution_artifact_id": parent_id,
            "batch_decision_artifact_id": batch_decision_artifact_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "batch_label": batch_label,
            "session_id": session_id,
            "status": parent_status,
            "op_count": len(op_order),
            "ok_count": ok_count,
            "blocked_count": blocked_count,
            "error_count": error_count,
            "results": child_results,
            "learning": {
                "apply_enabled": bool(is_apply_accepted_overrides_enabled()),
                "resolved": learning_resolved,
                "tuning_stamp": learning_tuning_stamp,
            },
        }

    except Exception as e:  # WP-1: keep broad — governance requires ERROR artifact even on unexpected failures
        # Persist parent ERROR even on unexpected failures
        parent_id = _write_artifact(
            kind="saw_batch_execution",
            status="ERROR",
            index_meta={
                "tool_kind": "saw_lab",
                "kind_group": "batch",
                "parent_batch_decision_artifact_id": batch_decision_artifact_id,
            },
            payload={
                "created_utc": _utc_now_iso(),
                "batch_decision_artifact_id": batch_decision_artifact_id,
                "error": {"type": type(e).__name__, "message": str(e)},
            },
        )
        return {
            "batch_execution_artifact_id": parent_id,
            "batch_decision_artifact_id": batch_decision_artifact_id,
            "status": "ERROR",
            "op_count": 0,
            "ok_count": 0,
            "blocked_count": 0,
            "error_count": 1,
            "results": [],
        }
