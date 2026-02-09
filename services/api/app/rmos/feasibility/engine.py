from __future__ import annotations

from typing import Dict, List

from .schemas import FeasibilityInput, FeasibilityResult, RiskLevel
from .rules import all_rules
from app.core.safety import safety_critical


@safety_critical
def compute_feasibility(fi: FeasibilityInput) -> FeasibilityResult:
    """
    Compute feasibility with Phase 3 explainability.
    
    Returns a FeasibilityResult with:
    - rules_triggered: List of rule IDs for registry lookup
    - warnings/blocking_reasons: Human-readable messages (backward compat)
    """
    hits = all_rules(fi)

    blocking_reasons: List[str] = []
    warnings: List[str] = []
    constraints: List[str] = []
    rules_triggered: List[str] = []  # Phase 3: collect rule IDs

    has_red = False
    for h in hits:
        rules_triggered.append(h.rule_id)  # Phase 3: every hit has a rule_id
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
        rules_triggered=rules_triggered,  # Phase 3
        constraints=constraints,
        engine_version="feasibility_engine_v1",
        details=details,
    )
