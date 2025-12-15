"""Saw Lab operation planners."""
from __future__ import annotations

from typing import Dict, Any


def plan_cut_operation(job: Dict[str, Any]) -> Dict[str, Any]:
    """Return placeholder plan results."""
    return {
        "job": job,
        "gcode": "",
        "warnings": ["Saw Lab operation planner not implemented."],
    }
