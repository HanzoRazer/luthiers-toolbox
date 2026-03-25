from __future__ import annotations

from typing import Any, Dict, List, Union

from app.art_studio.schemas.rosette_feasibility import RosetteFeasibilitySummary
from app.art_studio.schemas.rosette_params import RosetteParamSpec


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute or dict key."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def build_intent_explain(
    design: Union[RosetteParamSpec, Dict[str, Any]],
    feasibility: Union[RosetteFeasibilitySummary, Dict[str, Any]],
) -> Dict[str, List[str]]:
    """
    Build a compact, human-readable explanation for a promotion intent.

    This is designed for:
      - logs
      - inspectors
      - debugging
      - review UIs

    Handles both pydantic models and dicts for flexibility.
    """

    bullets: List[str] = []
    warnings: List[str] = []
    top_risks: List[str] = []

    ring_params = _get(design, "ring_params") or []
    ring_count = len(ring_params)
    bullets.append(f"Rosette with {ring_count} rings")

    outer_d = _get(design, "outer_diameter_mm")
    if outer_d:
        bullets.append(f"Outer {chr(216)} {outer_d:.2f} mm")

    if ring_params:
        total_width = sum(_get(r, "width_mm", 0) or 0 for r in ring_params)
        bullets.append(f"Total width {total_width:.2f} mm")

    overall_score = _get(feasibility, "overall_score")
    if overall_score is not None:
        bullets.append(f"Feasibility score: {overall_score:.1f}")

    risk_bucket = _get(feasibility, "risk_bucket")
    if risk_bucket:
        bullets.append(f"Risk bucket: {risk_bucket}")

    feas_warnings = _get(feasibility, "warnings") or []
    if feas_warnings:
        warnings.extend(feas_warnings)
        top_risks.extend(feas_warnings[:3])

    return {
        "bullets": bullets,
        "warnings": warnings,
        "top_risks": top_risks,
    }
