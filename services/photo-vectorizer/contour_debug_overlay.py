"""
Contour Debug Overlay
=====================

Visual debug tool for hierarchy-based contour selection.
Makes it obvious, per file, why a body candidate was accepted/reviewed/rejected.

Called after contour extraction + hierarchy isolation in edge_to_dxf.py.
Triggered by DEBUG_CONTOURS=1 environment variable.

Output:
- {stem}_overlay.png: Full image with color-coded contours
- {stem}_candidates.png: Grid of candidate crops

Color semantics:
- Blue: Selected contour
- Green: Top-level candidate
- Orange: Child contour
- Red: Page border
- Gray: Rejected

Author: Production Shop
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np


# ─── Debug Data Structures ──────────────────────────────────────────────────


Color = Tuple[int, int, int]  # BGR for OpenCV


@dataclass
class ContourDebugNode:
    """Contour with all debug-relevant fields merged."""
    idx: int
    contour: np.ndarray
    parent_idx: Optional[int]
    child_indices: List[int] = field(default_factory=list)
    depth: int = 0
    area: float = 0.0
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
    touches_border_edges: int = 0
    is_page_border: bool = False
    is_outer_candidate: bool = False
    is_child_feature: bool = False
    reject_reason: str = ""
    score: float = 0.0
    child_area_ratio: float = 0.0


@dataclass
class DebugSelectionSummary:
    """Summary of selection result for debug panel."""
    source_name: str
    candidate_count: int
    selected_idx: Optional[int]
    selection_score: float
    runner_up_score: float
    winner_margin: float
    recommendation: str
    notes: List[str] = field(default_factory=list)


# ─── Color Palette ──────────────────────────────────────────────────────────


COLORS: Dict[str, Color] = {
    "selected": (255, 0, 0),        # blue
    "outer_candidate": (0, 180, 0), # green
    "child": (0, 165, 255),         # orange
    "page_border": (0, 0, 255),     # red
    "rejected": (150, 150, 150),    # gray
    "label_bg": (245, 245, 245),
    "label_fg": (20, 20, 20),
}


# ─── Conversion Functions ───────────────────────────────────────────────────


@dataclass
class DebugContourScore:
    """Lightweight score for debug visualization only."""
    index: int
    score: float
    rejected: bool = False
    reject_reason: str = ""


def to_debug_nodes(
    nodes: List[Any],  # List[ContourNode] from hierarchy
    score_map: Dict[int, DebugContourScore],
    selected_index: Optional[int] = None,
) -> List[ContourDebugNode]:
    """
    Convert ContourNode list + score map to debug-ready nodes.

    Args:
        nodes: List of ContourNode from build_hierarchy()
        score_map: Dict mapping node.idx to DebugContourScore
        selected_index: Index of selected contour (for highlighting)

    Returns:
        List of ContourDebugNode ready for rendering
    """
    debug_nodes = []

    for node in nodes:
        score_info = score_map.get(node.idx)

        debug_node = ContourDebugNode(
            idx=node.idx,
            contour=node.contour,
            parent_idx=node.parent_idx,
            child_indices=list(node.child_indices),
            depth=node.depth,
            area=node.area,
            bbox=node.bbox,
            touches_border_edges=node.touches_border_edges,
            is_page_border=node.is_page_border,
            is_outer_candidate=node.is_outer_candidate,
            is_child_feature=node.is_child_feature,
            reject_reason=node.reject_reason or (score_info.reject_reason if score_info else ""),
            score=score_info.score if score_info else 0.0,
            child_area_ratio=0.0,  # Can be enriched from BodyCandidate if needed
        )
        debug_nodes.append(debug_node)

    return debug_nodes


def to_debug_summary(
    source_name: str,
    candidate_count: int,
    selected_idx: Optional[int],
    selection_score: float,
    runner_up_score: float,
    winner_margin: float,
    recommendation: str,
    notes: Optional[List[str]] = None,
) -> DebugSelectionSummary:
    """Build debug summary from selection results."""
    return DebugSelectionSummary(
        source_name=source_name,
        candidate_count=candidate_count,
        selected_idx=selected_idx,
        selection_score=selection_score,
        runner_up_score=runner_up_score,
        winner_margin=winner_margin,
        recommendation=recommendation,
        notes=notes or [],
    )


# ─── Debug-Only Scoring ─────────────────────────────────────────────────────


def score_body_candidates_for_debug(
    candidates: List[Any],  # List of contours or BodyCandidate-like objects
    image_width: int,
    image_height: int,
) -> Tuple[Dict[int, DebugContourScore], Optional[int], float, float]:
    """
    Lightweight scoring for debug visualization only.

    This is NOT the production scorer. It provides approximate scores
    so debug overlays can show relative quality before DXF creation.

    Args:
        candidates: List of contour arrays or objects with .contour attribute
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        (score_map, selected_idx, runner_up_score, winner_margin)
    """
    image_area = float(max(image_width * image_height, 1))
    score_map: Dict[int, DebugContourScore] = {}
    scores: List[Tuple[int, float]] = []

    for i, cand in enumerate(candidates):
        # Handle both raw contours and BodyCandidate objects
        if hasattr(cand, 'contour'):
            contour = cand.contour
            idx = cand.node.idx if hasattr(cand, 'node') else i
        else:
            contour = cand
            idx = i

        if contour is None or len(contour) < 3:
            score_map[idx] = DebugContourScore(
                index=idx, score=0.0, rejected=True, reject_reason="degenerate"
            )
            continue

        # Simple geometric scoring (mirrors production logic loosely)
        area = float(cv2.contourArea(contour))
        area_ratio = area / image_area

        # Closure score
        perimeter = float(cv2.arcLength(contour, closed=False))
        if len(contour) >= 2:
            start = contour[0][0].astype(np.float32)
            end = contour[-1][0].astype(np.float32)
            gap = float(np.linalg.norm(start - end))
            closure = max(0.0, 1.0 - min((gap / max(perimeter, 1.0)) * 20.0, 1.0))
        else:
            closure = 0.0

        # Solidity
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0.0

        # Centrality
        x, y, w, h = cv2.boundingRect(contour)
        cx, cy = x + w / 2, y + h / 2
        dx = abs(cx - image_width / 2) / (image_width / 2)
        dy = abs(cy - image_height / 2) / (image_height / 2)
        centrality = max(0.0, 1.0 - (dx + dy) / 2)

        # Rejection filters
        rejected = False
        reject_reason = ""

        if area_ratio < 0.005:
            rejected = True
            reject_reason = "too_small"
        elif area_ratio > 0.95:
            rejected = True
            reject_reason = "too_large"

        # Weighted score (simplified)
        score = (
            0.30 * min(area_ratio / 0.35, 1.0) +
            0.25 * closure +
            0.15 * solidity +
            0.15 * centrality +
            0.15  # baseline
        )

        if rejected:
            score *= 0.1

        score_map[idx] = DebugContourScore(
            index=idx,
            score=round(score, 3),
            rejected=rejected,
            reject_reason=reject_reason,
        )
        scores.append((idx, score))

    # Find selected and runner-up
    if not scores:
        return score_map, None, 0.0, 0.0

    scores.sort(key=lambda x: x[1], reverse=True)
    selected_idx = scores[0][0]
    best_score = scores[0][1]
    runner_up = scores[1][1] if len(scores) > 1 else 0.0
    margin = best_score - runner_up

    return score_map, selected_idx, runner_up, margin


# ─── Rendering Functions ────────────────────────────────────────────────────


def _ensure_color(image: np.ndarray) -> np.ndarray:
    """Ensure image is BGR color."""
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image.copy()


def _draw_contour_with_label(
    canvas: np.ndarray,
    node: ContourDebugNode,
    color: Color,
    label: str,
    thickness: int = 2,
) -> None:
    """Draw contour with label box."""
    cv2.drawContours(canvas, [node.contour], -1, color, thickness)

    x, y, w, h = node.bbox
    text = f"#{node.idx} {label}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.45
    t = 1
    (tw, th), baseline = cv2.getTextSize(text, font, scale, t)
    box_y = max(y - th - baseline - 6, 0)
    cv2.rectangle(
        canvas,
        (x, box_y),
        (x + tw + 6, box_y + th + baseline + 6),
        COLORS["label_bg"],
        -1,
    )
    cv2.putText(
        canvas,
        text,
        (x + 3, box_y + th + 2),
        font,
        scale,
        COLORS["label_fg"],
        t,
        cv2.LINE_AA,
    )


def _draw_summary_panel(canvas: np.ndarray, summary: DebugSelectionSummary) -> None:
    """Draw summary panel in top-left corner."""
    lines = [
        f"file: {summary.source_name}",
        f"candidates: {summary.candidate_count}",
        f"selected: {summary.selected_idx}",
        f"score: {summary.selection_score:.3f}",
        f"runner-up: {summary.runner_up_score:.3f}",
        f"margin: {summary.winner_margin:.3f}",
        f"recommendation: {summary.recommendation}",
    ]
    lines.extend(summary.notes[:5])

    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    pad = 8
    line_h = 22
    width = 420
    height = pad * 2 + line_h * len(lines)

    x1, y1 = 10, 10
    x2, y2 = x1 + width, y1 + height
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 255, 255), -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 0), 1)

    y = y1 + pad + 14
    for line in lines:
        cv2.putText(canvas, line, (x1 + pad, y), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)
        y += line_h


def render_contour_hierarchy_overlay(
    image: np.ndarray,
    nodes: Iterable[ContourDebugNode],
    summary: DebugSelectionSummary,
    *,
    show_bboxes: bool = True,
) -> np.ndarray:
    """
    Render annotated overlay with color-coded contours.

    Color semantics:
    - Blue: Selected contour
    - Green: Top-level candidate
    - Orange: Child feature
    - Red: Page border
    - Gray: Rejected
    """
    canvas = _ensure_color(image)
    nodes = list(nodes)

    # Draw order: rejected first, selected last (so it's on top)
    draw_order = sorted(
        nodes,
        key=lambda n: (
            0 if n.is_page_border else
            1 if n.reject_reason else
            2 if n.is_child_feature else
            3 if n.is_outer_candidate else
            4,
            n.depth,
        ),
    )

    for node in draw_order:
        if summary.selected_idx is not None and node.idx == summary.selected_idx:
            color = COLORS["selected"]
            label = f"SELECTED s={node.score:.2f}"
            thickness = 3
        elif node.is_page_border:
            color = COLORS["page_border"]
            label = "PAGE BORDER"
            thickness = 2
        elif node.is_child_feature:
            color = COLORS["child"]
            label = f"CHILD d={node.depth}"
            thickness = 2
        elif node.is_outer_candidate:
            color = COLORS["outer_candidate"]
            label = f"CAND s={node.score:.2f}"
            thickness = 2
        else:
            color = COLORS["rejected"]
            reason = node.reject_reason or "REJECTED"
            label = reason[:28]
            thickness = 1

        _draw_contour_with_label(canvas, node, color, label, thickness=thickness)

        if show_bboxes:
            x, y, w, h = node.bbox
            cv2.rectangle(canvas, (x, y), (x + w, y + h), color, 1)

    _draw_summary_panel(canvas, summary)
    return canvas


def render_candidate_grid(
    image: np.ndarray,
    nodes: Iterable[ContourDebugNode],
    *,
    crop_size: int = 220,
    columns: int = 3,
) -> np.ndarray:
    """Render per-candidate crops for quick visual comparison."""
    base = _ensure_color(image)
    candidates = list(nodes)
    if not candidates:
        blank = np.full((200, 400, 3), 255, dtype=np.uint8)
        cv2.putText(blank, "No candidates", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
        return blank

    tiles: List[np.ndarray] = []
    for node in candidates:
        x, y, w, h = node.bbox
        cx, cy = x + w // 2, y + h // 2
        half = crop_size // 2
        x1 = max(cx - half, 0)
        y1 = max(cy - half, 0)
        x2 = min(cx + half, base.shape[1])
        y2 = min(cy + half, base.shape[0])

        tile = base[y1:y2, x1:x2].copy()

        # Shift contour to tile coordinates
        shifted = node.contour.copy()
        shifted[:, 0, 0] -= x1
        shifted[:, 0, 1] -= y1
        cv2.drawContours(tile, [shifted], -1, (255, 0, 0), 2)

        # Labels
        text = f"#{node.idx} s={node.score:.2f} a={node.area:.0f}"
        cv2.putText(tile, text, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
        if node.reject_reason:
            cv2.putText(tile, node.reject_reason[:28], (8, 42),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 200), 1, cv2.LINE_AA)
        tiles.append(tile)

    # Assemble grid
    rows = (len(tiles) + columns - 1) // columns
    tile_h = max(tile.shape[0] for tile in tiles)
    tile_w = max(tile.shape[1] for tile in tiles)
    grid = np.full((rows * tile_h, columns * tile_w, 3), 245, dtype=np.uint8)

    for i, tile in enumerate(tiles):
        r, c = divmod(i, columns)
        y = r * tile_h
        x = c * tile_w
        grid[y:y + tile.shape[0], x:x + tile.shape[1]] = tile

    return grid


# ─── Bundle Writer ──────────────────────────────────────────────────────────


def write_debug_bundle(
    image: np.ndarray,
    nodes: Iterable[ContourDebugNode],
    summary: DebugSelectionSummary,
    out_dir: str | Path,
) -> Dict[str, str]:
    """
    Write overlay + candidate grid for one source file.

    Returns:
        Dict with paths to generated files
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    nodes_list = list(nodes)

    overlay = render_contour_hierarchy_overlay(image, nodes_list, summary)
    grid = render_candidate_grid(
        image,
        [n for n in nodes_list if n.is_outer_candidate or n.reject_reason],
        columns=3,
    )

    stem = Path(summary.source_name).stem
    overlay_path = out_path / f"{stem}_overlay.png"
    grid_path = out_path / f"{stem}_candidates.png"

    cv2.imwrite(str(overlay_path), overlay)
    cv2.imwrite(str(grid_path), grid)

    return {
        "overlay": str(overlay_path),
        "candidates": str(grid_path),
    }


# ─── Convenience Helper ─────────────────────────────────────────────────────


def is_debug_enabled() -> bool:
    """Check if DEBUG_CONTOURS environment variable is set."""
    return os.getenv("DEBUG_CONTOURS", "").lower() in ("1", "true", "yes")
