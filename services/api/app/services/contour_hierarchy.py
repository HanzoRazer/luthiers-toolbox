"""
Contour Hierarchy Module
========================

Separates isolation from ranking for blueprint contour selection.

Architecture:
    extraction (RETR_TREE) -> build_hierarchy() -> isolate_body_candidates() -> scoring

This module interprets OpenCV hierarchy structure to:
- Identify parent/child relationships
- Reject page borders before scoring
- Mark top-level body candidates
- Preserve child contours as features (not competitors)

Author: Production Shop
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import cv2
import numpy as np


# ─── Data Structures ────────────────────────────────────────────────────────


@dataclass
class ContourNode:
    """
    A contour with hierarchy context.

    OpenCV hierarchy format: [next, prev, first_child, parent]
    We convert this to a more usable structure.
    """
    idx: int
    contour: np.ndarray
    parent_idx: Optional[int]  # None if top-level
    child_indices: List[int] = field(default_factory=list)
    depth: int = 0  # 0 = top-level, 1 = child, 2 = grandchild, etc.

    # Geometric properties
    area: float = 0.0
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h
    perimeter: float = 0.0

    # Border detection
    touches_border_edges: int = 0  # 0-4
    is_page_border: bool = False

    # Classification
    is_outer_candidate: bool = False  # Eligible for body selection
    is_child_feature: bool = False  # Interior feature (hole, cavity)
    reject_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "idx": self.idx,
            "parent_idx": self.parent_idx,
            "child_count": len(self.child_indices),
            "depth": self.depth,
            "area": round(self.area, 1),
            "bbox": self.bbox,
            "touches_border_edges": self.touches_border_edges,
            "is_page_border": self.is_page_border,
            "is_outer_candidate": self.is_outer_candidate,
            "is_child_feature": self.is_child_feature,
            "reject_reason": self.reject_reason,
        }


@dataclass
class BodyCandidate:
    """
    A top-level contour eligible for body selection, with its children.

    This is what gets passed to the scorer.
    """
    node: ContourNode
    child_nodes: List[ContourNode] = field(default_factory=list)

    # Child-aware metrics
    child_area_sum: float = 0.0
    child_area_ratio: float = 0.0  # child_area_sum / outer_area
    has_internal_structure: bool = False

    # Scoring (filled by scorer)
    score: float = 0.0
    reasons: List[str] = field(default_factory=list)

    @property
    def contour(self) -> np.ndarray:
        return self.node.contour

    @property
    def area(self) -> float:
        return self.node.area

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return self.node.bbox

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_idx": self.node.idx,
            "child_count": len(self.child_nodes),
            "child_area_sum": round(self.child_area_sum, 1),
            "child_area_ratio": round(self.child_area_ratio, 4),
            "has_internal_structure": self.has_internal_structure,
            "score": round(self.score, 3),
            "reasons": self.reasons,
        }


# ─── Border Detection ───────────────────────────────────────────────────────


def _touches_border(
    contour: np.ndarray,
    image_width: int,
    image_height: int,
    margin_px: int = 3,
) -> Tuple[bool, int]:
    """
    Check if contour touches image border.

    Returns:
        (touches_any_edge, edge_count) where edge_count is 0-4
    """
    if contour is None or len(contour) < 3:
        return False, 0

    x, y, w, h = cv2.boundingRect(contour)

    edges_touched = 0
    if x <= margin_px:
        edges_touched += 1  # left
    if y <= margin_px:
        edges_touched += 1  # top
    if x + w >= image_width - margin_px:
        edges_touched += 1  # right
    if y + h >= image_height - margin_px:
        edges_touched += 1  # bottom

    return edges_touched > 0, edges_touched


def _is_page_border(
    edge_count: int,
    area_ratio: float,
) -> bool:
    """
    Detect if contour is likely a page border.

    Page borders:
    - Touch 3+ edges
    - OR touch 2+ edges AND area > 70% of image
    """
    if edge_count >= 3:
        return True
    if edge_count >= 2 and area_ratio > 0.70:
        return True
    return False


def _is_title_block_shape(
    bbox: Tuple[int, int, int, int],
    image_width: int,
    image_height: int,
) -> bool:
    """
    Detect title-block-like rectangles.

    Title blocks are typically:
    - Wide and short (aspect > 4:1)
    - At bottom or top edge
    - Width > 50% of image
    """
    x, y, w, h = bbox
    if h <= 0:
        return False

    aspect = w / h
    width_ratio = w / image_width
    is_at_edge = y <= 10 or (y + h) >= image_height - 10

    return aspect > 4.0 and width_ratio > 0.5 and is_at_edge


# ─── Hierarchy Building ─────────────────────────────────────────────────────


def build_hierarchy(
    contours: List[np.ndarray],
    hierarchy: np.ndarray,
    image_shape: Tuple[int, int],
) -> List[ContourNode]:
    """
    Build ContourNode list from OpenCV findContours output.

    Args:
        contours: List of contours from cv2.findContours
        hierarchy: Hierarchy array from cv2.findContours (shape: (1, N, 4) or (N, 4))
        image_shape: (height, width) of source image

    Returns:
        List of ContourNode with parent/child relationships resolved
    """
    if not contours or hierarchy is None:
        return []

    # Normalize hierarchy shape
    if len(hierarchy.shape) == 3:
        hierarchy = hierarchy[0]  # (1, N, 4) -> (N, 4)

    image_height, image_width = image_shape
    image_area = float(image_width * image_height)

    nodes: List[ContourNode] = []

    # First pass: create nodes with basic properties
    for idx, contour in enumerate(contours):
        if contour is None or len(contour) < 3:
            continue

        # Get hierarchy info: [next, prev, first_child, parent]
        hier = hierarchy[idx]
        parent_idx = int(hier[3]) if hier[3] >= 0 else None

        # Compute geometric properties
        area = float(cv2.contourArea(contour))
        bbox = cv2.boundingRect(contour)
        perimeter = float(cv2.arcLength(contour, closed=True))

        # Border detection
        touches, edge_count = _touches_border(contour, image_width, image_height)
        area_ratio = area / image_area if image_area > 0 else 0.0
        page_border = _is_page_border(edge_count, area_ratio)

        node = ContourNode(
            idx=idx,
            contour=contour,
            parent_idx=parent_idx,
            area=area,
            bbox=bbox,
            perimeter=perimeter,
            touches_border_edges=edge_count,
            is_page_border=page_border,
        )
        nodes.append(node)

    # Build index lookup
    idx_to_node = {node.idx: node for node in nodes}

    # Second pass: resolve child relationships and depth
    for node in nodes:
        if node.parent_idx is not None and node.parent_idx in idx_to_node:
            parent = idx_to_node[node.parent_idx]
            parent.child_indices.append(node.idx)
            node.depth = parent.depth + 1
        else:
            node.depth = 0  # Top-level

    # Third pass: classify nodes
    for node in nodes:
        _classify_node(node, idx_to_node, image_width, image_height, image_area)

    return nodes


def _classify_node(
    node: ContourNode,
    idx_to_node: dict,
    image_width: int,
    image_height: int,
    image_area: float,
) -> None:
    """
    Classify a node as outer candidate, child feature, or rejected.
    """
    area_ratio = node.area / image_area if image_area > 0 else 0.0

    # Page border → reject
    if node.is_page_border:
        node.reject_reason = "page_border"
        return

    # Title block shape → reject
    if _is_title_block_shape(node.bbox, image_width, image_height):
        node.reject_reason = "title_block"
        return

    # Too small (< 0.5% of image) → reject as noise
    if area_ratio < 0.005:
        node.reject_reason = "too_small"
        return

    # Too large (> 95% of image) → reject
    if area_ratio > 0.95:
        node.reject_reason = "too_large"
        return

    # Child contour (has parent) → mark as child feature
    if node.parent_idx is not None:
        node.is_child_feature = True
        return

    # Top-level, passes filters → outer candidate
    node.is_outer_candidate = True


# ─── Candidate Isolation ────────────────────────────────────────────────────


def isolate_body_candidates(
    nodes: List[ContourNode],
    min_child_area_ratio: float = 0.01,
    max_child_area_ratio: float = 0.25,
) -> List[BodyCandidate]:
    """
    Extract body candidates from hierarchy nodes.

    Only top-level non-rejected contours become candidates.
    Their children are attached as potential internal features.

    Args:
        nodes: List of ContourNode from build_hierarchy()
        min_child_area_ratio: Minimum child/outer ratio to count as structure
        max_child_area_ratio: Maximum child/outer ratio for bonus eligibility

    Returns:
        List of BodyCandidate ready for scoring
    """
    idx_to_node = {node.idx: node for node in nodes}
    candidates: List[BodyCandidate] = []

    for node in nodes:
        if not node.is_outer_candidate:
            continue

        # Collect child nodes
        child_nodes = []
        child_area_sum = 0.0

        for child_idx in node.child_indices:
            if child_idx in idx_to_node:
                child = idx_to_node[child_idx]
                child_nodes.append(child)
                child_area_sum += child.area

        # Compute child metrics
        child_area_ratio = child_area_sum / node.area if node.area > 0 else 0.0

        # Determine if has plausible internal structure
        has_internal_structure = (
            len(child_nodes) >= 1
            and min_child_area_ratio <= child_area_ratio <= max_child_area_ratio
        )

        candidate = BodyCandidate(
            node=node,
            child_nodes=child_nodes,
            child_area_sum=child_area_sum,
            child_area_ratio=child_area_ratio,
            has_internal_structure=has_internal_structure,
        )
        candidates.append(candidate)

    return candidates


# ─── Utility Functions ──────────────────────────────────────────────────────


def get_top_level_nodes(nodes: List[ContourNode]) -> List[ContourNode]:
    """Get all top-level (depth=0) nodes."""
    return [n for n in nodes if n.depth == 0]


def get_child_nodes(
    parent: ContourNode,
    nodes: List[ContourNode],
) -> List[ContourNode]:
    """Get direct children of a node."""
    idx_to_node = {node.idx: node for node in nodes}
    return [idx_to_node[idx] for idx in parent.child_indices if idx in idx_to_node]


def get_rejected_nodes(nodes: List[ContourNode]) -> List[ContourNode]:
    """Get all rejected nodes with their reasons."""
    return [n for n in nodes if n.reject_reason]


def hierarchy_summary(nodes: List[ContourNode]) -> dict[str, Any]:
    """
    Generate summary statistics for debugging.
    """
    top_level = [n for n in nodes if n.depth == 0]
    candidates = [n for n in nodes if n.is_outer_candidate]
    children = [n for n in nodes if n.is_child_feature]
    rejected = [n for n in nodes if n.reject_reason]

    reject_reasons = {}
    for n in rejected:
        reason = n.reject_reason
        reject_reasons[reason] = reject_reasons.get(reason, 0) + 1

    return {
        "total_contours": len(nodes),
        "top_level_count": len(top_level),
        "candidate_count": len(candidates),
        "child_count": len(children),
        "rejected_count": len(rejected),
        "reject_reasons": reject_reasons,
    }
