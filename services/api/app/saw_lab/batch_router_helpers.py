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


def _safe_param(source: Dict[str, Any], keys: List[str], default: float) -> float:
    """Extract a float from *source* trying *keys* in order, falling back to *default*."""
    for k in keys:
        val = source.get(k)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                continue
    return default


def _extract_params_from_dict(
    d: Dict[str, Any], rpm: float, feed: float, doc: float
) -> tuple[float, float, float]:
    """Pull spindle_rpm / feed_rate_mmpm / doc_mm from *d* with alias fallbacks."""
    rpm = _safe_param(d, ["spindle_rpm", "max_rpm"], rpm)
    feed = _safe_param(d, ["feed_rate_mmpm", "feed_rate_mm_per_min"], feed)
    doc = _safe_param(d, ["doc_mm", "depth_of_cut_mm"], doc)
    return rpm, feed, doc


def _extract_from_spec(
    spec: Dict[str, Any], rpm: float, feed: float, doc: float
) -> tuple[float, float, float]:
    """Unwrap a spec payload and extract machining params from items or context."""
    spec_payload = spec.get("payload") or spec.get("data") or {}
    if not isinstance(spec_payload, dict):
        return rpm, feed, doc

    items = spec_payload.get("items") or spec_payload.get("operations") or []
    if isinstance(items, list) and items and isinstance(items[0], dict):
        rpm, feed, doc = _extract_params_from_dict(items[0], rpm, feed, doc)

    ctx = spec_payload.get("context")
    if isinstance(ctx, dict):
        rpm, feed, doc = _extract_params_from_dict(ctx, rpm, feed, doc)

    return rpm, feed, doc


def _extract_from_plan_artifact(
    plan_artifact_id: str, rpm: float, feed: float, doc: float
) -> tuple[float, float, float]:
    """Fetch a plan artifact and extract machining params from its context."""
    try:
        from app.rmos.runs_v2.store import get_run
        plan = get_run(plan_artifact_id)
        if not plan or not isinstance(plan, dict):
            return rpm, feed, doc
        plan_payload = plan.get("payload") or plan.get("data") or {}
        if not isinstance(plan_payload, dict):
            return rpm, feed, doc
        plan_ctx = plan_payload.get("context") or plan_payload.get("saw_context") or {}
        if isinstance(plan_ctx, dict):
            rpm, feed, doc = _extract_params_from_dict(plan_ctx, rpm, feed, doc)
    except (ImportError, KeyError, ValueError, TypeError, AttributeError):
        pass
    return rpm, feed, doc


def extract_base_context(
    spec: Optional[Dict[str, Any]],
    plan_artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract base machining context from spec/plan artifacts."""
    rpm, feed, doc = 3000.0, 600.0, 3.0

    if spec and isinstance(spec, dict):
        rpm, feed, doc = _extract_from_spec(spec, rpm, feed, doc)

    if plan_artifact_id:
        rpm, feed, doc = _extract_from_plan_artifact(plan_artifact_id, rpm, feed, doc)

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
