from __future__ import annotations

from typing import Dict, List

from app.art_studio.schemas.rosette_feasibility import RosetteFeasibilitySummary
from app.art_studio.schemas.rosette_params import RosetteParamSpec


def build_intent_explain(
    design: RosetteParamSpec,
    feasibility: RosetteFeasibilitySummary,
) -> Dict[str, List[str]]:
    """
    Build a compact, human-readable explanation for a promotion intent.

    This is designed for:
      - logs
      - inspectors
      - debugging
      - review UIs
    """

    bullets: List[str] = []
    warnings: List[str] = []
    top_risks: List[str] = []

    ring_count = len(design.ring_params) if design.ring_params else 0
    bullets.append(f"Rosette with {ring_count} rings")

    if design.outer_diameter_mm:
        bullets.append(f"Outer Ø {design.outer_diameter_mm:.2f} mm")

    if design.ring_params:
        total_width = sum(getattr(r, "width_mm", 0) or 0 for r in design.ring_params)
        bullets.append(f"Total width {total_width:.2f} mm")

    if feasibility.overall_score is not None:
        bullets.append(f"Feasibility score: {feasibility.overall_score:.1f}")

    if feasibility.risk_bucket:
        bullets.append(f"Risk bucket: {feasibility.risk_bucket}")

    if feasibility.warnings:
        warnings.extend(feasibility.warnings)
        top_risks.extend(feasibility.warnings[:3])

    return {
        "bullets": bullets,
        "warnings": warnings,
        "top_risks": top_risks,
    }
