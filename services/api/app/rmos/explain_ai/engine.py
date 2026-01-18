"""
Phase 5 — Assistant Explanation Engine

Generates advisory-only explanations for run artifacts.

This implementation is intentionally deterministic (no network dependency).
If/when you add an LLM provider, do it behind a feature flag and keep this as fallback.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.rmos.feasibility.rule_registry import FEASIBILITY_RULES
from app.rmos.runs_v2.schemas import RunArtifact
from .schemas import AssistantExplanation, AssistantExplanationBasedOn


def _get_rule_summaries(rule_ids: List[str]) -> List[str]:
    """Look up summaries for each rule ID from the authoritative registry."""
    out: List[str] = []
    for rid in rule_ids:
        meta = FEASIBILITY_RULES.get(rid)
        if meta is None:
            out.append(f"{rid}: Unknown feasibility rule")
        else:
            out.append(f"{rid}: {meta['summary']}")
    return out


def _extract_grounding_facts(run: RunArtifact) -> Dict[str, Any]:
    """
    Pull only safe, already-present facts from the run artifact.
    This keeps explanations grounded and deterministic.
    """
    rs = run.request_summary or {}
    feas = run.feasibility or {}

    # Get decision safely
    decision: Dict[str, Any] = {}
    if hasattr(run.decision, "model_dump"):
        decision = run.decision.model_dump()
    elif isinstance(run.decision, dict):
        decision = run.decision
    elif run.decision is not None:
        decision = {"risk_level": getattr(run.decision, "risk_level", None)}

    # Common CAM fields (best-effort; do not assume existence)
    facts: Dict[str, Any] = {
        "tool_d": rs.get("tool_d"),
        "stepover": rs.get("stepover"),
        "stepdown": rs.get("stepdown"),
        "z_rough": rs.get("z_rough"),
        "safe_z": rs.get("safe_z"),
        "feed_xy": rs.get("feed_xy"),
        "feed_z": rs.get("feed_z"),
        "rapid": rs.get("rapid"),
        "strategy": rs.get("strategy"),
        "layer_name": rs.get("layer_name"),
        # feasibility-side facts if present
        "loop_count": feas.get("loop_count") or feas.get("loops") or feas.get("loop_count_estimate"),
        "smallest_feature_mm": feas.get("smallest_feature_mm"),
        "bbox_mm": feas.get("bbox_mm") or feas.get("bounding_box_mm"),
        "risk_level": decision.get("risk_level"),
    }
    return {k: v for k, v in facts.items() if v is not None}


def generate_assistant_explanation(
    run: RunArtifact,
    *,
    inputs_hash: Optional[str] = None,
    model_name: str = "deterministic.v1",
) -> AssistantExplanation:
    """
    On-demand explanation generator.

    NOTE: This implementation is intentionally deterministic (no network dependency).
    If/when you add an LLM provider, do it behind a feature flag and keep this as fallback.
    """
    # Extract rules_triggered safely
    rule_ids: List[str] = []
    try:
        raw_rules = (run.feasibility or {}).get("rules_triggered", [])
        rule_ids = [str(x).strip().upper() for x in raw_rules if x]
    except Exception:
        rule_ids = []

    # Get risk level safely
    risk = "UNKNOWN"
    if hasattr(run.decision, "risk_level") and run.decision.risk_level:
        risk = run.decision.risk_level
    elif isinstance(run.decision, dict) and run.decision.get("risk_level"):
        risk = run.decision["risk_level"]

    facts = _extract_grounding_facts(run)
    rule_summaries = _get_rule_summaries(rule_ids)

    # Build summary
    n = len(rule_ids)
    if n == 0:
        summary = "No feasibility rules were recorded for this run."
    else:
        summary = f"{n} feasibility rule(s) triggered → {risk}."

    # Build operator notes
    operator_notes: List[str] = []
    if rule_summaries:
        operator_notes.extend(rule_summaries)

    # Add a small amount of grounded, numeric-friendly context when available.
    # (Do NOT invent measurements.)
    if "tool_d" in facts and "smallest_feature_mm" in facts:
        operator_notes.append(
            f"Tool diameter vs smallest feature: tool_d={facts['tool_d']}mm, smallest≈{facts['smallest_feature_mm']}mm."
        )
    if "feed_z" in facts and "feed_xy" in facts:
        try:
            if float(facts["feed_z"]) > float(facts["feed_xy"]):
                operator_notes.append(
                    f"Plunge feed exceeds XY feed: feed_z={facts['feed_z']} > feed_xy={facts['feed_xy']}."
                )
        except Exception:
            pass

    # Build suggested actions tied to known rule IDs
    suggested_actions: List[str] = []
    if "F010" in rule_ids:
        suggested_actions.append("Consider a smaller tool diameter or increase feature sizes/clearances.")
    if "F011" in rule_ids:
        suggested_actions.append("Reduce feed_z to be <= feed_xy, or reduce stepdown.")
    if "F012" in rule_ids:
        suggested_actions.append("Reduce stepdown or increase pass count for safer cutting.")
    if "F013" in rule_ids:
        suggested_actions.append("Simplify geometry or reduce loop count (clean DXF, merge contours).")
    if any(rid in rule_ids for rid in ["F006", "F007"]):
        suggested_actions.append("Ensure DXF contains closed LWPOLYLINE loops on the selected layer.")

    based_on = AssistantExplanationBasedOn(
        run_id=run.run_id,
        risk_level=risk,
        rules_triggered=rule_ids,
        inputs_hash=inputs_hash,
    )

    return AssistantExplanation(
        based_on=based_on,
        summary=summary,
        operator_notes=operator_notes,
        suggested_actions=suggested_actions,
        meta={"generator": model_name, "grounded_facts": facts},
    )
