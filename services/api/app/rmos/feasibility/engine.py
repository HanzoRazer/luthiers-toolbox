from __future__ import annotations

from typing import Dict, List

from .schemas import FeasibilityInput, FeasibilityResult, RiskLevel
from .rules import all_rules


def compute_feasibility(fi: FeasibilityInput) -> FeasibilityResult:
    hits = all_rules(fi)

    blocking_reasons: List[str] = []
    warnings: List[str] = []
    constraints: List[str] = []

    has_red = False
    for h in hits:
        if h.level == "RED":
            has_red = True
            blocking_reasons.append(h.message)
        elif h.level == "YELLOW":
            warnings.append(h.message)
        if h.constraint:
            constraints.append(h.constraint)

    risk = RiskLevel.RED if has_red else (RiskLevel.YELLOW if warnings else RiskLevel.GREEN)

    details: Dict[str, object] = {
        "pipeline_id": fi.pipeline_id,
        "post_id": fi.post_id,
        "units": fi.units,
        "layer_name": fi.layer_name,
        "bbox": fi.bbox,
        "entity_count": fi.entity_count,
        "loop_count_hint": fi.loop_count_hint,
        "has_closed_paths": fi.has_closed_paths,
    }

    return FeasibilityResult(
        risk_level=risk,
        blocking=has_red,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
        constraints=constraints,
        engine_version="feasibility_engine_v1",
        details=details,
    )
