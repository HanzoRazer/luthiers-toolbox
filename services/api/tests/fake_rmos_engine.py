"""
Fake RMOS Engine for Testing

Provides deterministic feasibility and toolpath generation for tests.
"""
from __future__ import annotations
from typing import Any, Dict


class FakeEngine:
    """
    Fake RMOS engine that returns deterministic results for testing.

    Returns different scores and risk buckets based on material_id:
    - ebony: GREEN (92.0)
    - maple: YELLOW (74.0)
    - other: YELLOW (50.0)
    """

    def compute_feasibility_for_design(
        self,
        design: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute deterministic feasibility based on material."""
        mat = context.get("material_id") or "unknown"

        if mat == "ebony":
            return {
                "score": 92.0,
                "risk_bucket": "GREEN",
                "warnings": [],
                "details": {"mat": mat},
            }
        if mat == "maple":
            return {
                "score": 74.0,
                "risk_bucket": "YELLOW",
                "warnings": ["heat risk"],
                "details": {"mat": mat},
            }
        return {
            "score": 50.0,
            "risk_bucket": "YELLOW",
            "warnings": ["generic"],
            "details": {"mat": mat},
        }

    def generate_toolpaths_for_design(
        self,
        design: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate deterministic toolpaths based on material."""
        mat = context.get("material_id") or "unknown"
        return {
            "plan_id": f"plan_{mat}",
            "summary": {"ops": 3, "material": mat},
        }


# Module-level singleton for easy import
engine = FakeEngine()
