"""
Brace Graph Service

Interprets brace layout topology and couples with geometry
to produce CAM policy constraints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class BraceNode:
    """A node in the brace graph (intersection or endpoint)."""
    node_id: str
    position_mm: Tuple[float, float, float]
    connected_braces: List[str] = field(default_factory=list)
    is_intersection: bool = False


@dataclass
class BraceEdge:
    """An edge in the brace graph (a brace segment)."""
    brace_id: str
    from_node: str
    to_node: str
    length_mm: float
    profile_type: str  # parabolic, triangular, rectangular
    has_scallop: bool = False
    scallop_positions: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class BraceGraphResult:
    """Result of brace graph analysis."""
    model_id: str
    node_count: int
    edge_count: int
    topology_valid: bool
    nodes: List[BraceNode] = field(default_factory=list)
    edges: List[BraceEdge] = field(default_factory=list)
    scallop_zones: List[str] = field(default_factory=list)
    intersection_issues: List[Dict[str, str]] = field(default_factory=list)
    cam_policy_overrides: List[Dict[str, Any]] = field(default_factory=list)


class BraceGraphService:
    """
    Service for interpreting brace layout topology.

    This is the INTERPRETATION layer - it takes brace geometry
    and produces structural analysis and CAM constraints.
    """

    def __init__(self):
        self._cache: Dict[str, BraceGraphResult] = {}

    def ingest_bracing_layout(self, model_id: str, bracing_json: Dict[str, Any]) -> None:
        """
        Ingest bracing layout from bracing pipeline.

        Expects format from MVP_scaffold_bracing_hardware.zip:
          - braces[]: {name, material, profile, path, ...}
        """
        # Stub: Parse bracing JSON into graph
        # - Create nodes at endpoints and intersections
        # - Create edges for brace segments
        # - Detect scallop zones from taper info
        pass

    def build_graph(self, model_id: str) -> None:
        """Build the brace graph from ingested data."""
        # Stub: Construct graph topology
        # - Find intersections (geometric proximity)
        # - Validate connectivity
        # - Identify scallop zones
        pass

    def analyze(self, model_id: str, geometry: Optional[Any] = None) -> BraceGraphResult:
        """
        Analyze brace graph and produce interpretation.

        Returns:
          - Graph structure (nodes, edges)
          - Topology validation
          - Scallop zones
          - Intersection issues
          - CAM policy overrides
        """
        # Stub: Full analysis

        return BraceGraphResult(
            model_id=model_id,
            node_count=0,
            edge_count=0,
            topology_valid=True,
            nodes=[],
            edges=[],
            scallop_zones=[],
            intersection_issues=[],
            cam_policy_overrides=[],
        )

    def get_cam_constraints(self, model_id: str) -> List[Dict[str, Any]]:
        """
        Get CAM policy constraints for brace zones.

        Returns list of constraint dicts compatible with cam_policy.schema.json.
        """
        result = self._cache.get(model_id)
        if not result:
            return []

        constraints = []

        # Brace intersection zones → no-cut or careful machining
        for node in result.nodes:
            if node.is_intersection:
                constraints.append({
                    "region_id": f"brace_intersection_{node.node_id}",
                    "type": "brace_zone",
                    "constraints": {
                        "stepdown_max_mm": 0.3,
                        "min_tool_diameter_mm": 3.0,
                        "cut_direction": "climb",
                    },
                    "reason": f"Brace intersection at {node.position_mm}",
                    "source_field": "brace_graph",
                    "priority": 9,
                })

        # Scallop zones → finish-only with small stepover
        for zone_id in result.scallop_zones:
            constraints.append({
                "region_id": zone_id,
                "type": "brace_zone",
                "constraints": {
                    "stepover_max_pct": 10,
                    "feed_rate_max_mm_min": 800,
                },
                "reason": "Brace scallop zone - delicate profiling",
                "source_field": "brace_graph",
                "priority": 6,
            })

        return constraints

    def get_no_cut_zones(self, model_id: str) -> List[Dict[str, Any]]:
        """Get absolute no-cut zones from brace graph."""
        result = self._cache.get(model_id)
        if not result:
            return []

        zones = []
        for node in result.nodes:
            if node.is_intersection and len(node.connected_braces) >= 3:
                # Critical multi-brace junction
                zones.append({
                    "zone_id": f"brace_junction_{node.node_id}",
                    "reason": f"Critical brace junction ({len(node.connected_braces)} braces)",
                    "override_allowed": False,
                })

        return zones
