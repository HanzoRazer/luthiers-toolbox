"""Queue-driven diff placeholder for CP-S21."""
from __future__ import annotations

from typing import Dict, Any


def compute_pipeline_diff(seed_a: Dict[str, Any], seed_b: Dict[str, Any]) -> Dict[str, Any]:
    """Return placeholder diff structure."""
    return {
        "seed_a": seed_a,
        "seed_b": seed_b,
        "changes": [],
        "status": "diff_not_implemented",
    }
