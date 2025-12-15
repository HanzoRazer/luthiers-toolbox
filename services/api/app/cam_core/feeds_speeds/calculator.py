"""Placeholder feeds and speeds calculator."""
from __future__ import annotations

from typing import Dict, Any


def calculate_feed_plan(tool: Dict[str, Any], material: str, strategy: str) -> Dict[str, Any]:
    """Return a placeholder feed plan structure."""
    return {
        "tool_id": tool.get("id"),
        "material": material,
        "strategy": strategy,
        "feed_xy": 0.0,
        "feed_z": 0.0,
        "rpm": 0.0,
        "notes": "Feeds & speeds calculator not implemented.",
    }
