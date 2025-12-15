"""Pipeline registry placeholder."""
from __future__ import annotations

from typing import Dict, Any


class PipelineRegistry:
    """Registry for CAM pipeline nodes (placeholder)."""

    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[str, Any]] = {}

    def register(self, node_id: str, meta: Dict[str, Any]) -> None:
        self._nodes[node_id] = meta

    def describe(self, node_id: str) -> Dict[str, Any] | None:
        return self._nodes.get(node_id)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._nodes)
