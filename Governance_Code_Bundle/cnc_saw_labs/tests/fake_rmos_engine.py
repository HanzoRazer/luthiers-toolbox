from __future__ import annotations
from typing import Any, Dict


class FakeEngine:
    def compute_feasibility_for_design(self, design: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        mat = context.get("material_id") or "unknown"
        # simple deterministic differences per material
        if mat == "ebony":
            return {"score": 92.0, "risk_bucket": "GREEN", "warnings": [], "details": {"mat": mat}}
        if mat == "maple":
            return {"score": 74.0, "risk_bucket": "YELLOW", "warnings": ["heat risk"], "details": {"mat": mat}}
        return {"score": 50.0, "risk_bucket": "YELLOW", "warnings": ["generic"], "details": {"mat": mat}}

    def generate_toolpaths_for_design(self, design: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        mat = context.get("material_id") or "unknown"
        return {
            "plan_id": f"plan_{mat}",
            "summary": {"ops": 3, "material": mat},
        }