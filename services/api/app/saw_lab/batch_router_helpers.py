"""Batch router service helpers — toolpath generation, rollup computation."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from app.saw_lab.store import (
    store_artifact,
    get_artifact,
    query_job_logs_by_execution,
    query_accepted_learning_events,
)


# ---------------------------------------------------------------------------
# Plan helpers
# ---------------------------------------------------------------------------


def extract_plan_snapshot(plan_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the relevant snapshot from a plan payload for auditing."""
    return {
        "batch_label": plan_payload.get("batch_label", ""),
        "session_id": plan_payload.get("session_id", ""),
        "setups": plan_payload.get("setups", []),
    }


def find_setup_ops(
    plan_payload: Dict[str, Any], setup_key: str, op_ids: List[str]
) -> List[Dict[str, Any]]:
    """Find ops from a specific setup by their IDs."""
    for setup in plan_payload.get("setups", []):
        if setup.get("setup_key") == setup_key:
            return [op for op in setup.get("ops", []) if op.get("op_id") in op_ids]
    return []


def extract_base_context(
    spec: Optional[Dict[str, Any]],
    plan_artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract base machining context from spec/plan artifacts."""
    rpm = 3000.0
    feed = 600.0
    doc = 3.0

    if spec and isinstance(spec, dict):
        spec_payload = spec.get("payload") or spec.get("data") or {}
        if isinstance(spec_payload, dict):
            items = spec_payload.get("items") or spec_payload.get("operations") or []
            if isinstance(items, list) and items:
                first_item = items[0] if isinstance(items[0], dict) else {}
                rpm = float(first_item.get("spindle_rpm") or first_item.get("max_rpm") or rpm)
                feed = float(first_item.get("feed_rate_mmpm") or first_item.get("feed_rate_mm_per_min") or feed)
                doc = float(first_item.get("doc_mm") or first_item.get("depth_of_cut_mm") or doc)

            ctx = spec_payload.get("context") or {}
            if isinstance(ctx, dict):
                rpm = float(ctx.get("spindle_rpm") or ctx.get("max_rpm") or rpm)
                feed = float(ctx.get("feed_rate_mmpm") or ctx.get("feed_rate_mm_per_min") or feed)
                doc = float(ctx.get("doc_mm") or doc)

    if plan_artifact_id:
        try:
            from app.rmos.runs_v2.store import get_run
            plan = get_run(plan_artifact_id)
            if plan and isinstance(plan, dict):
                plan_payload = plan.get("payload") or plan.get("data") or {}
                if isinstance(plan_payload, dict):
                    plan_ctx = plan_payload.get("context") or plan_payload.get("saw_context") or {}
                    if isinstance(plan_ctx, dict):
                        rpm = float(plan_ctx.get("spindle_rpm") or plan_ctx.get("max_rpm") or rpm)
                        feed = float(plan_ctx.get("feed_rate_mmpm") or plan_ctx.get("feed_rate_mm_per_min") or feed)
                        doc = float(plan_ctx.get("doc_mm") or doc)
        except (ImportError, KeyError, ValueError, TypeError, AttributeError):
            pass

    return {
        "spindle_rpm": rpm,
        "feed_rate_mmpm": feed,
        "doc_mm": doc,
    }


def apply_patch_to_context(
    base_context: Dict[str, Any], applied_multipliers: Dict[str, float]
) -> Dict[str, Any]:
    """Apply decision multipliers to base context, returning the patched context."""
    from app.saw_lab.decision_apply_service import apply_decision_to_context

    result, _stamp = apply_decision_to_context(
        base_context=base_context,
        applied_multipliers=applied_multipliers,
    )
    return result


# ---------------------------------------------------------------------------
# Toolpath generation core
# ---------------------------------------------------------------------------

_MOCK_GCODE_MOVES = [
    {"code": "G21", "comment": "Units: mm"},
    {"code": "G90", "comment": "Absolute positioning"},
    {"code": "G0", "z": 10.0, "comment": "Rapid to safe height"},
    {"code": "G0", "x": 0.0, "y": 0.0, "comment": "Move to start"},
    {"code": "M3", "comment": "Spindle on"},
    {"code": "G1", "z": -6.0, "f": 100.0, "comment": "Plunge"},
    {"code": "G1", "x": 300.0, "f": 800.0, "comment": "Cut"},
    {"code": "G0", "z": 10.0, "comment": "Retract"},
    {"code": "M5", "comment": "Spindle off"},
]


def generate_toolpaths_for_ops(
    *,
    decision_artifact_id: str,
    plan_id: str,
    spec_id: str,
    batch_label: str,
    session_id: str,
    op_order: List[str],
    op_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[List[str], List[Dict[str, Any]], int, int]:
    """Generate toolpaths for each op in the order.

    Returns (child_ids, child_results, ok_count, total_gcode_lines).
    """
    child_ids: List[str] = []
    child_results: List[Dict[str, Any]] = []
    ok_count = 0
    total_gcode_lines = 0

    for op_id in op_order:
        op = op_by_id.get(op_id, {})
        setup_key = op.get("setup_key", "")

        op_payload = {
            "batch_decision_artifact_id": decision_artifact_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "op_id": op_id,
            "setup_key": setup_key,
            "toolpaths": {"moves": list(_MOCK_GCODE_MOVES)},
        }

        child_id = store_artifact(
            kind="saw_batch_op_toolpaths",
            payload=op_payload,
            parent_id=decision_artifact_id,
            session_id=session_id,
            status="OK",
        )
        child_ids.append(child_id)
        ok_count += 1
        total_gcode_lines += len(_MOCK_GCODE_MOVES)

        child_results.append(
            {
                "op_id": op_id,
                "setup_key": setup_key,
                "status": "OK",
                "risk_bucket": "GREEN",
                "score": 1.0,
                "toolpaths_artifact_id": child_id,
                "warnings": [],
            }
        )

    return child_ids, child_results, ok_count, total_gcode_lines


# ---------------------------------------------------------------------------
# Rollup computation
# ---------------------------------------------------------------------------


def compute_rollup_from_logs(
    batch_execution_artifact_id: str,
) -> Dict[str, Any]:
    """Aggregate metrics from all job logs for an execution."""
    all_logs = query_job_logs_by_execution(batch_execution_artifact_id)
    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in all_logs:
        log_metrics = log.get("payload", {}).get("metrics", {})
        total_cut_time += log_metrics.get("cut_time_s", 0.0)
        total_setup_time += log_metrics.get("setup_time_s", 0.0)
        parts_ok += log_metrics.get("parts_ok", 0)
        parts_scrap += log_metrics.get("parts_scrap", 0)
        if log_metrics.get("burn"):
            burn_events += 1
        if log_metrics.get("tearout"):
            tearout_events += 1
        if log_metrics.get("kickback"):
            kickback_events += 1

    return {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "metrics": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
            "total_time_s": total_cut_time + total_setup_time,
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
        },
        "counts": {"job_log_count": len(all_logs)},
        "signals": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }


def store_rollup_for_query(
    rollup_id: str, payload: Dict[str, Any], decision_id: str
) -> None:
    """Store rollup in a format that query_run_artifacts can find."""
    try:
        from app.rmos.run_artifacts.store import persist_run_artifact

        persist_run_artifact(
            kind="saw_batch_execution_metrics_rollup",
            payload=payload,
            index_meta={
                "parent_batch_decision_artifact_id": decision_id,
                "parent_batch_execution_artifact_id": payload.get(
                    "batch_execution_artifact_id"
                ),
            },
        )
    except (ImportError, OSError, RuntimeError, ValueError, TypeError):
        pass
