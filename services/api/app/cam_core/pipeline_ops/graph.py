"""Pipeline graph placeholder."""
from __future__ import annotations

from typing import Dict, Any, List


def build_pipeline_graph(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "nodes": nodes,
        "edges": [],
        "status": "graph_not_implemented",
    }
