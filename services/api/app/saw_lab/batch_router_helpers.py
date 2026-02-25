"""Batch router service helpers — toolpath generation, rollup computation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


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
