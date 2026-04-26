"""
Edge-to-DXF High-Fidelity Exporter
==================================

Converts image edges directly to DXF LINE entities for maximum detail preservation.
This produces large files (10-50MB) with 50,000-300,000+ LINE entities, but captures
every edge pixel from the source image.

Use cases:
- High-fidelity archival of guitar body outlines
- When contour-based extraction loses detail
- Creating reference DXFs from photos for manual tracing

Output characteristics:
- DXF R12 format for maximum compatibility
- Individual LINE entities (not LWPOLYLINE)
- Adjacent edge pixels connected as line segments
- Configurable scale (default: body height = 500mm)

Usage:
    from edge_to_dxf import EdgeToDXF

    converter = EdgeToDXF()
    result = converter.convert(
        "Benedetto Front.jpg",
        output_path="benedetto_edges.dxf",
        target_height_mm=500.0
    )
    print(f"Created {result.line_count} LINE entities")

CLI:
    python edge_to_dxf.py "Benedetto Front.jpg" -o output.dxf --height 500

Author: The Production Shop
Date: 2026-04-01
"""

from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

logger = logging.getLogger(__name__)

# Debug overlay (optional, triggered by DEBUG_CONTOURS=1)
try:
    from contour_debug_overlay import (
        is_debug_enabled,
        ContourDebugNode,
        DebugContourScore,
        score_body_candidates_for_debug,
        to_debug_summary,
        write_debug_bundle,
    )
    DEBUG_OVERLAY_AVAILABLE = True
except ImportError:
    DEBUG_OVERLAY_AVAILABLE = False


# ─── Hierarchy Isolation Helpers ────────────────────────────────────────────


def _touches_border(
    contour: np.ndarray,
    image_width: int,
    image_height: int,
    margin_px: int = 3,
) -> Tuple[bool, int]:
    """Check if contour touches image border. Returns (touches, edge_count 0-4)."""
    if contour is None or len(contour) < 3:
        return False, 0

    x, y, w, h = cv2.boundingRect(contour)
    edges = 0
    if x <= margin_px:
        edges += 1
    if y <= margin_px:
        edges += 1
    if x + w >= image_width - margin_px:
        edges += 1
    if y + h >= image_height - margin_px:
        edges += 1

    return edges > 0, edges


def _is_page_border(edge_count: int, area_ratio: float) -> bool:
    """Detect page border: 3+ edges OR (2+ edges AND area > 70%)."""
    if edge_count >= 3:
        return True
    if edge_count >= 2 and area_ratio > 0.70:
        return True
    return False


def _centrality_score(
    contour: np.ndarray,
    image_width: int,
    image_height: int,
) -> float:
    """Score how centered the contour is (0.0 = edge, 1.0 = center)."""
    if contour is None or len(contour) < 3:
        return 0.0

    x, y, w, h = cv2.boundingRect(contour)
    cx, cy = x + w / 2, y + h / 2
    img_cx, img_cy = image_width / 2, image_height / 2

    dx = abs(cx - img_cx) / (image_width / 2)
    dy = abs(cy - img_cy) / (image_height / 2)
    offset = (dx + dy) / 2

    return float(max(0.0, 1.0 - offset))


def _build_debug_nodes_from_hierarchy(
    contours: list,
    hierarchy: np.ndarray,
    image_width: int,
    image_height: int,
) -> list:
    """
    Build ContourDebugNode list from raw OpenCV hierarchy.

    Used for debug visualization only - does not affect production path.
    """
    if not DEBUG_OVERLAY_AVAILABLE:
        return []

    if hierarchy is None or len(contours) == 0:
        return []

    # Normalize hierarchy shape
    if len(hierarchy.shape) == 3:
        hierarchy = hierarchy[0]

    image_area = float(image_width * image_height)
    nodes = []

    for idx, contour in enumerate(contours):
        if contour is None or len(contour) < 3:
            continue

        # Hierarchy: [next, prev, first_child, parent]
        parent_idx = int(hierarchy[idx][3]) if hierarchy[idx][3] >= 0 else None

        area = float(cv2.contourArea(contour))
        area_ratio = area / image_area
        bbox = cv2.boundingRect(contour)

        _, edge_count = _touches_border(contour, image_width, image_height)
        page_border = _is_page_border(edge_count, area_ratio)

        # Classify
        is_outer_candidate = False
        is_child_feature = False
        reject_reason = ""

        if page_border:
            reject_reason = "page_border"
        elif area_ratio < 0.005:
            reject_reason = "too_small"
        elif area_ratio > 0.95:
            reject_reason = "too_large"
        elif parent_idx is not None:
            is_child_feature = True
        else:
            is_outer_candidate = True

        node = ContourDebugNode(
            idx=idx,
            contour=contour,
            parent_idx=parent_idx,
            depth=0 if parent_idx is None else 1,
            area=area,
            bbox=bbox,
            touches_border_edges=edge_count,
            is_page_border=page_border,
            is_outer_candidate=is_outer_candidate,
            is_child_feature=is_child_feature,
            reject_reason=reject_reason,
        )
        nodes.append(node)

    return nodes


def _isolate_body_contours(
    contours: list,
    hierarchy: np.ndarray,
    image_width: int,
    image_height: int,
    min_area_ratio: float = 0.005,
    max_area_ratio: float = 0.95,
) -> list:
    """
    Filter contours to body candidates using hierarchy.

    Returns only top-level contours that:
    - Are not page borders
    - Are not too small or too large
    - Are not children of other contours

    DEPRECATED: Use _isolate_with_grouping() for new code.
    This function is preserved for fallback compatibility.
    """
    if hierarchy is None or len(contours) == 0:
        return contours

    # Normalize hierarchy shape
    if len(hierarchy.shape) == 3:
        hierarchy = hierarchy[0]

    image_area = float(image_width * image_height)
    candidates = []

    for idx, contour in enumerate(contours):
        if contour is None or len(contour) < 3:
            continue

        # Check parent (hierarchy[idx][3]): -1 means top-level
        parent_idx = int(hierarchy[idx][3])
        if parent_idx >= 0:
            # Has parent = child contour, skip
            continue

        area = float(cv2.contourArea(contour))
        area_ratio = area / image_area

        # Size filters
        if area_ratio < min_area_ratio:
            continue
        if area_ratio > max_area_ratio:
            continue

        # Page border filter
        _, edge_count = _touches_border(contour, image_width, image_height)
        if _is_page_border(edge_count, area_ratio):
            continue

        candidates.append(contour)

    logger.info(
        f"Hierarchy isolation: {len(contours)} contours -> {len(candidates)} body candidates"
    )
    return candidates


# ─── Surgical Border Removal ────────────────────────────────────────────────
#
# This section removes page borders from the contour pool BEFORE hierarchy
# building and grouping. This prevents borders from dominating the candidate
# set when the body contour is fragmented or weak.
#
# Key insight: Border rejection at scoring time is too late. If the border
# is the only closed contour, fallback selects it. By removing borders
# before hierarchy construction, they never enter the contest.
#
# Author: Production Shop
# Date: 2026-04-13


def _remove_page_borders_early(
    contours: list,
    hierarchy: np.ndarray,
    image_width: int,
    image_height: int,
    area_threshold: float = 0.70,
    edge_threshold: int = 3,
) -> Tuple[list, int]:
    """
    Remove page border contours from the pool BEFORE grouping.

    This is surgical pre-filtering that prevents page borders from
    entering the hierarchy/grouping contest. Unlike scoring-time
    rejection, this ensures borders never become fallback winners.

    Detection criteria (same as _is_page_border):
    - Touches 3+ image edges, OR
    - Touches 2+ edges AND area > 70% of image

    Implementation:
    - Nullifies border contours (replaces with empty array)
    - Preserves indices so hierarchy relationships remain valid
    - Degenerate (empty) contours are filtered by downstream logic

    Args:
        contours: Raw contours from cv2.findContours
        hierarchy: Hierarchy array (shape: (1, N, 4) or (N, 4))
        image_width, image_height: Image dimensions
        area_threshold: Area ratio above which 2-edge contour is border
        edge_threshold: Number of edges to touch for definite border

    Returns:
        (modified_contours, removed_count)
        Contours are modified in-place; border contours become empty arrays.
    """
    if hierarchy is None or len(contours) == 0:
        return contours, 0

    # Normalize hierarchy shape
    if len(hierarchy.shape) == 3:
        hierarchy = hierarchy[0]

    image_area = float(image_width * image_height)
    removed_count = 0
    border_indices = []

    for idx, contour in enumerate(contours):
        if contour is None or len(contour) < 3:
            continue

        # Only check top-level contours (no parent)
        parent_idx = int(hierarchy[idx][3]) if hierarchy[idx][3] >= 0 else -1
        if parent_idx >= 0:
            # Has parent = child contour, not a page border
            continue

        area = float(cv2.contourArea(contour))
        area_ratio = area / image_area

        _, edge_count = _touches_border(contour, image_width, image_height)

        # Page border detection (same logic as _is_page_border)
        is_border = False
        if edge_count >= edge_threshold:
            is_border = True
        elif edge_count >= 2 and area_ratio > area_threshold:
            is_border = True

        if is_border:
            border_indices.append(idx)
            removed_count += 1

    # Nullify border contours (replace with empty array to preserve indices)
    # This is cleaner than list removal because hierarchy indices stay valid
    for idx in border_indices:
        contours[idx] = np.array([], dtype=np.int32).reshape(0, 1, 2)

    if removed_count > 0:
        logger.info(
            f"BORDER_REMOVAL | Removed {removed_count} page border contour(s) "
            f"before grouping (indices: {border_indices[:5]}{'...' if len(border_indices) > 5 else ''})"
        )

    return contours, removed_count


# ─── Primary Object Grouping ────────────────────────────────────────────────
#
# This section implements contour grouping to solve the multi-view blueprint
# problem. Instead of scoring all top-level contours globally (which causes
# page borders and construction lines to compete with the body), we:
#
# 1. Build hierarchy nodes from raw contours
# 2. Identify eligible root candidates (top-level, non-border, right size)
# 3. Group each root with its descendants
# 4. Score groups as units
# 5. Select the winning group
# 6. Export only the winning group's contours
#
# TODO: Consolidate with services/api/app/services/contour_hierarchy.py
# These functions duplicate logic that exists in the API service. A future
# refactor should establish a shared hierarchy module.
#
# Author: Production Shop
# Date: 2026-04-12


# ─── Text Region Masking ────────────────────────────────────────────────────
#
# Text-masking preprocessing for blueprint vectorization.
# Problem: Morphological gap closing (7×7 kernel) bridges text glyph strokes,
# producing solid blobs that pollute geometry contours.
# Solution: Detect text regions with OCR, mask them before edge detection,
# then apply gap closing only to geometry.
#
# Author: Production Shop
# Date: 2026-04-26
# Sprint: Sprint 3 — Text-masking preprocessing pass
# ─────────────────────────────────────────────────────────────────────────────

# Lazy import for EasyOCR (heavy dependency)
_EASYOCR_READER = None
_EASYOCR_AVAILABLE = None


def _get_easyocr_reader():
    """Lazy-load EasyOCR reader (singleton pattern)."""
    global _EASYOCR_READER, _EASYOCR_AVAILABLE

    if _EASYOCR_AVAILABLE is None:
        try:
            import easyocr
            _EASYOCR_AVAILABLE = True
            logger.info("EasyOCR available for text masking")
        except ImportError:
            _EASYOCR_AVAILABLE = False
            logger.warning("EasyOCR not available — text masking disabled")

    if not _EASYOCR_AVAILABLE:
        return None

    if _EASYOCR_READER is None:
        import easyocr
        logger.info("Initializing EasyOCR reader (first use)...")
        _EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
        logger.info("EasyOCR reader initialized")

    return _EASYOCR_READER


def detect_text_regions(
    image: np.ndarray,
    min_confidence: float = 0.3,
    padding_px: int = 5,
) -> list:
    """
    Detect text regions in an image using EasyOCR.

    Args:
        image: BGR or grayscale image
        min_confidence: Minimum OCR confidence threshold
        padding_px: Pixels to expand each bounding box (text has proximity effects)

    Returns:
        List of (x, y, w, h) bounding boxes for detected text regions.
        Returns empty list if EasyOCR unavailable or no text found.
    """
    reader = _get_easyocr_reader()
    if reader is None:
        return []

    try:
        # EasyOCR expects BGR or grayscale
        results = reader.readtext(image)
        logger.info(f"OCR detected {len(results)} text regions")

        regions = []
        for bbox, text, confidence in results:
            if confidence < min_confidence:
                continue

            # Convert polygon bbox to (x, y, w, h)
            pts = np.array(bbox)
            x_min, y_min = pts.min(axis=0).astype(int)
            x_max, y_max = pts.max(axis=0).astype(int)

            # Add padding to account for text proximity effects
            x_min = max(0, x_min - padding_px)
            y_min = max(0, y_min - padding_px)
            x_max = x_max + padding_px
            y_max = y_max + padding_px

            w = x_max - x_min
            h = y_max - y_min

            if w > 0 and h > 0:
                regions.append((x_min, y_min, w, h))
                logger.debug(f"Text region: '{text[:20]}...' conf={confidence:.2f} bbox=({x_min},{y_min},{w},{h})")

        logger.info(f"Detected {len(regions)} text regions above confidence {min_confidence}")
        return regions

    except Exception as e:
        logger.warning(f"Text detection failed: {e}")
        return []


def create_text_mask(
    image_shape: Tuple[int, int],
    text_regions: list,
) -> np.ndarray:
    """
    Create a binary mask with text regions filled.

    Args:
        image_shape: (height, width) of the image
        text_regions: List of (x, y, w, h) bounding boxes

    Returns:
        Binary mask where text regions are 255, background is 0.
        Use bitwise NOT to get geometry-only mask.
    """
    h, w = image_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    for (x, y, rw, rh) in text_regions:
        # Clip to image bounds
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w, x + rw)
        y2 = min(h, y + rh)

        if x2 > x1 and y2 > y1:
            mask[y1:y2, x1:x2] = 255

    return mask


def apply_text_mask_to_edges(
    edges: np.ndarray,
    text_mask: np.ndarray,
) -> Tuple[np.ndarray, int]:
    """
    Remove text region edges from edge image.

    Args:
        edges: Binary edge image from Canny
        text_mask: Binary mask where text regions are 255

    Returns:
        (masked_edges, removed_pixel_count)
    """
    if text_mask is None or text_mask.size == 0:
        return edges, 0

    # Count edges that will be removed
    text_edges = cv2.bitwise_and(edges, text_mask)
    removed_count = cv2.countNonZero(text_edges)

    # Remove text edges: edges AND (NOT text_mask)
    geometry_mask = cv2.bitwise_not(text_mask)
    masked_edges = cv2.bitwise_and(edges, geometry_mask)

    return masked_edges, removed_count


# ─── Reusable Extraction Helpers ────────────────────────────────────────────
#
# These functions separate extraction from DXF writing for composability.
# Phase 1: Added for dual-pass extraction support.
# DO NOT change recovered behavior. These are additive, not replacement.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExtractedEntities:
    """Container for extracted contour entities."""
    contours: list  # List of numpy contour arrays
    edge_count: int  # Total edge pixels detected
    image_size: Tuple[int, int]  # (width, height)
    mm_per_px: float  # Scale factor
    method: str  # "canny" or "simple"
    debug: Dict[str, Any] = field(default_factory=dict)


def extract_entities_canny(
    image: np.ndarray,
    target_height_mm: float = 500.0,
    canny_low: int = 50,
    canny_high: int = 150,
    blur_kernel: int = 3,
    isolate_body: bool = False,
) -> ExtractedEntities:
    """
    Extract contour entities using Canny edge detection.

    This is the extraction portion of EdgeToDXF.convert, separated
    for composability. Does NOT write DXF.

    Args:
        image: BGR image (numpy array)
        target_height_mm: Target height for scaling
        canny_low: Canny low threshold
        canny_high: Canny high threshold
        blur_kernel: Gaussian blur kernel size (0 to disable)
        isolate_body: Use hierarchy filtering (True) or all contours (False)

    Returns:
        ExtractedEntities with contours ready for DXF writing
    """
    h, w = image.shape[:2]
    mm_per_px = target_height_mm / h

    # Grayscale + blur
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if blur_kernel > 0:
        gray = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)

    # Canny edge detection
    edges = cv2.Canny(gray, canny_low, canny_high)

    # Get edge count
    edge_points = np.column_stack(np.where(edges > 0))
    edge_count = len(edge_points)

    # Contour tracing
    if isolate_body:
        # Hierarchy-aware path (RETR_TREE)
        contours, hierarchy = cv2.findContours(
            edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
        )
        # Apply border removal and grouping
        contours, _ = _remove_page_borders_early(contours, hierarchy, w, h)
        valid_contours, _ = _isolate_with_grouping(
            contours, hierarchy, w, h,
            min_area_ratio=0.005,
            max_area_ratio=0.95,
        )
    else:
        # Recovered baseline path (RETR_LIST, all contours)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        valid_contours = [c for c in contours if len(c) >= 3]

    return ExtractedEntities(
        contours=valid_contours,
        edge_count=edge_count,
        image_size=(w, h),
        mm_per_px=mm_per_px,
        method="canny",
        debug={
            "canny_low": canny_low,
            "canny_high": canny_high,
            "isolate_body": isolate_body,
            "raw_contour_count": len(contours),
            "valid_contour_count": len(valid_contours),
        },
    )


def extract_entities_simple(
    image: np.ndarray,
    target_height_mm: float = 500.0,
    block_size: int = 21,
    c_constant: int = 10,
    min_area_px: int = 50,
    approx_epsilon_factor: float = 0.001,
) -> ExtractedEntities:
    """
    Extract contour entities using adaptive threshold (SIMPLE style).

    Based on March 6, 2026 SIMPLE extraction mode.
    Uses adaptive threshold instead of Canny for document-style blueprints.

    Args:
        image: BGR image (numpy array)
        target_height_mm: Target height for scaling
        block_size: Adaptive threshold block size
        c_constant: Adaptive threshold C constant
        min_area_px: Minimum contour area in pixels
        approx_epsilon_factor: approxPolyDP epsilon factor

    Returns:
        ExtractedEntities with contours ready for DXF writing
    """
    h, w = image.shape[:2]
    mm_per_px = target_height_mm / h
    image_area = h * w
    max_area_px = image_area * 0.95

    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Handle inverted images
    if np.mean(gray) < 127:
        gray = 255 - gray

    # Adaptive threshold (SIMPLE style)
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size, c_constant,
    )

    # Find contours (RETR_LIST, CHAIN_APPROX_SIMPLE)
    contours, _ = cv2.findContours(
        binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )

    # Filter and simplify
    valid_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area_px or area > max_area_px:
            continue

        # Simplify with approxPolyDP
        perimeter = cv2.arcLength(contour, True)
        epsilon = approx_epsilon_factor * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) >= 3:
            valid_contours.append(approx)

    return ExtractedEntities(
        contours=valid_contours,
        edge_count=0,  # Not applicable for threshold method
        image_size=(w, h),
        mm_per_px=mm_per_px,
        method="simple",
        debug={
            "block_size": block_size,
            "c_constant": c_constant,
            "min_area_px": min_area_px,
            "approx_epsilon": approx_epsilon_factor,
            "raw_contour_count": len(contours),
            "valid_contour_count": len(valid_contours),
        },
    )


def vectorize_entities_to_dxf(
    entities: ExtractedEntities,
    output_path: str,
    dxf_version: str = "R12",
    layer_name: str = "EDGES",
) -> Tuple[int, int]:
    """
    Write extracted entities to DXF file.

    This is the DXF writing portion of EdgeToDXF.convert, separated
    for composability.

    Args:
        entities: ExtractedEntities from extract_entities_* functions
        output_path: Path for output DXF file
        dxf_version: DXF version string
        layer_name: DXF layer name

    Returns:
        Tuple of (line_count, file_size_bytes)
    """
    if not EZDXF_AVAILABLE:
        raise ImportError("ezdxf is required: pip install ezdxf")

    w, h = entities.image_size
    mm_per_px = entities.mm_per_px

    # Create DXF document
    doc = ezdxf.new(dxf_version)
    msp = doc.modelspace()

    if layer_name not in doc.layers:
        doc.layers.add(layer_name)

    # Convert contours to LINE entities
    line_count = 0
    for contour in entities.contours:
        points = contour.reshape(-1, 2)

        # Create LINE entities along contour path
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            # Convert to mm coordinates (flip Y for CAD)
            mx1 = x1 * mm_per_px
            my1 = (h - y1) * mm_per_px
            mx2 = x2 * mm_per_px
            my2 = (h - y2) * mm_per_px

            msp.add_line((mx1, my1), (mx2, my2), dxfattribs={'layer': layer_name})
            line_count += 1

        # Close contour
        if len(points) >= 3:
            x1, y1 = points[-1]
            x2, y2 = points[0]
            mx1 = x1 * mm_per_px
            my1 = (h - y1) * mm_per_px
            mx2 = x2 * mm_per_px
            my2 = (h - y2) * mm_per_px
            msp.add_line((mx1, my1), (mx2, my2), dxfattribs={'layer': layer_name})
            line_count += 1

    # Save
    doc.saveas(output_path)
    file_size = Path(output_path).stat().st_size

    return line_count, file_size


# ─── Hierarchy Node and Grouping Classes ────────────────────────────────────


@dataclass
class HierarchyNode:
    """
    A contour with hierarchy context for production grouping.

    Unlike ContourDebugNode (which requires DEBUG_OVERLAY_AVAILABLE),
    this is always available for the production grouping path.
    """
    idx: int
    contour: np.ndarray
    parent_idx: Optional[int]
    child_indices: list  # Populated in second pass
    depth: int
    area: float
    area_ratio: float
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    edge_count: int
    is_page_border: bool
    is_eligible_root: bool  # Top-level, non-border, right size
    reject_reason: str


@dataclass
class ContourGroup:
    """
    A group of spatially-related contours (root + descendants).

    In the conservative first pass, each eligible root forms exactly
    one group with its descendants. No sibling merging yet.
    """
    group_id: int
    root_idx: int
    root_node: HierarchyNode
    member_indices: list  # All indices including root and descendants
    member_contours: list  # Actual contour arrays
    bbox: Tuple[int, int, int, int]  # Combined bounding box
    total_area: float
    center: Tuple[float, float]
    max_edge_count: int  # Max edge contacts in group


@dataclass
class GroupSelectionResult:
    """Result of group scoring and selection."""
    group_count: int
    selected_group_index: int
    selected_group_id: int
    selected_group_bbox: Tuple[int, int, int, int]
    selected_group_score: float
    runner_up_score: float
    winner_margin: float
    fallback_used: bool
    fallback_reason: str


def _build_hierarchy_nodes(
    contours: list,
    hierarchy: np.ndarray,
    image_width: int,
    image_height: int,
    min_area_ratio: float = 0.005,
    max_area_ratio: float = 0.95,
) -> list:
    """
    Build HierarchyNode list from raw OpenCV findContours output.

    This is the production version that doesn't depend on DEBUG_OVERLAY_AVAILABLE.

    Args:
        contours: List of contours from cv2.findContours
        hierarchy: Hierarchy array (shape: (1, N, 4) or (N, 4))
        image_width, image_height: Image dimensions
        min_area_ratio, max_area_ratio: Size filters for eligibility

    Returns:
        List of HierarchyNode with parent/child relationships resolved
    """
    if hierarchy is None or len(contours) == 0:
        return []

    # Normalize hierarchy shape
    if len(hierarchy.shape) == 3:
        hierarchy = hierarchy[0]

    image_area = float(image_width * image_height)
    nodes: list = []
    idx_to_node: Dict[int, HierarchyNode] = {}

    # First pass: create nodes with basic properties
    for idx, contour in enumerate(contours):
        if contour is None or len(contour) < 3:
            continue

        # Hierarchy: [next, prev, first_child, parent]
        parent_idx = int(hierarchy[idx][3]) if hierarchy[idx][3] >= 0 else None

        area = float(cv2.contourArea(contour))
        area_ratio = area / image_area
        bbox = cv2.boundingRect(contour)

        _, edge_count = _touches_border(contour, image_width, image_height)
        page_border = _is_page_border(edge_count, area_ratio)

        # Determine eligibility and rejection reason
        is_eligible = False
        reject_reason = ""

        if page_border:
            reject_reason = "page_border"
        elif area_ratio < min_area_ratio:
            reject_reason = "too_small"
        elif area_ratio > max_area_ratio:
            reject_reason = "too_large"
        elif parent_idx is not None:
            reject_reason = "child_contour"
        else:
            is_eligible = True

        node = HierarchyNode(
            idx=idx,
            contour=contour,
            parent_idx=parent_idx,
            child_indices=[],
            depth=0 if parent_idx is None else 1,
            area=area,
            area_ratio=area_ratio,
            bbox=bbox,
            edge_count=edge_count,
            is_page_border=page_border,
            is_eligible_root=is_eligible,
            reject_reason=reject_reason,
        )
        nodes.append(node)
        idx_to_node[idx] = node

    # Second pass: populate child_indices
    for node in nodes:
        if node.parent_idx is not None and node.parent_idx in idx_to_node:
            parent = idx_to_node[node.parent_idx]
            parent.child_indices.append(node.idx)
            # Update depth based on parent
            node.depth = parent.depth + 1

    return nodes


def _collect_descendants(
    root_idx: int,
    idx_to_node: Dict[int, HierarchyNode],
) -> list:
    """
    Recursively collect all descendant indices of a root node.

    Returns list of indices (not including root itself).
    """
    descendants = []

    if root_idx not in idx_to_node:
        return descendants

    root = idx_to_node[root_idx]
    for child_idx in root.child_indices:
        descendants.append(child_idx)
        # Recurse for grandchildren
        descendants.extend(_collect_descendants(child_idx, idx_to_node))

    return descendants


def _group_from_roots(
    nodes: list,
    image_width: int,
    image_height: int,
) -> list:
    """
    Create one ContourGroup per eligible root + its descendants.

    This is the conservative first pass: no sibling merging.
    Each top-level eligible contour becomes exactly one group.

    Args:
        nodes: List of HierarchyNode from _build_hierarchy_nodes()
        image_width, image_height: For computing combined bbox

    Returns:
        List of ContourGroup
    """
    idx_to_node = {n.idx: n for n in nodes}
    eligible_roots = [n for n in nodes if n.is_eligible_root]

    groups = []

    for group_id, root in enumerate(eligible_roots):
        # Collect descendants
        descendant_indices = _collect_descendants(root.idx, idx_to_node)
        all_indices = [root.idx] + descendant_indices

        # Gather contours
        member_contours = []
        for idx in all_indices:
            if idx in idx_to_node:
                member_contours.append(idx_to_node[idx].contour)

        if not member_contours:
            continue

        # Compute combined bounding box
        all_points = np.vstack([c.reshape(-1, 2) for c in member_contours])
        x_min, y_min = all_points.min(axis=0)
        x_max, y_max = all_points.max(axis=0)
        combined_bbox = (int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min))

        # Compute total area and center
        total_area = sum(idx_to_node[idx].area for idx in all_indices if idx in idx_to_node)
        cx = x_min + (x_max - x_min) / 2
        cy = y_min + (y_max - y_min) / 2

        # Max edge contacts in group
        max_edge = max(
            (idx_to_node[idx].edge_count for idx in all_indices if idx in idx_to_node),
            default=0
        )

        group = ContourGroup(
            group_id=group_id,
            root_idx=root.idx,
            root_node=root,
            member_indices=all_indices,
            member_contours=member_contours,
            bbox=combined_bbox,
            total_area=total_area,
            center=(cx, cy),
            max_edge_count=max_edge,
        )
        groups.append(group)

    logger.info(f"Created {len(groups)} contour groups from {len(eligible_roots)} eligible roots")
    return groups


def _score_contour_group(
    group: ContourGroup,
    image_width: int,
    image_height: int,
) -> float:
    """
    Score a single contour group.

    Scoring signals:
    - Area ratio (prefer groups covering meaningful portion of image)
    - Centrality (prefer centered groups)
    - Edge contact penalty (avoid border-hugging groups)
    - Aspect ratio penalty (penalize thin strips like construction lines)

    Returns score in range [0.0, 1.0]
    """
    image_area = float(image_width * image_height)

    # Area ratio score (target ~20-50% of image)
    area_ratio = group.total_area / image_area
    # Normalize: 0.2 area_ratio = 1.0 score, scales down outside [0.05, 0.60]
    if area_ratio < 0.05:
        area_score = area_ratio / 0.05
    elif area_ratio > 0.60:
        area_score = max(0.0, 1.0 - (area_ratio - 0.60) / 0.35)
    else:
        area_score = 1.0

    # Centrality score
    cx, cy = group.center
    img_cx, img_cy = image_width / 2, image_height / 2
    dx = abs(cx - img_cx) / (image_width / 2)
    dy = abs(cy - img_cy) / (image_height / 2)
    centrality = max(0.0, 1.0 - (dx + dy) / 2)

    # Edge contact penalty
    edge_penalty = min(1.0, group.max_edge_count * 0.25)
    edge_score = 1.0 - edge_penalty

    # Aspect ratio penalty (penalize thin strips)
    x, y, w, h = group.bbox
    if h > 0 and w > 0:
        aspect = max(w / h, h / w)
        if aspect > 5.0:
            # Very elongated = likely construction line or side view edge
            aspect_score = max(0.0, 1.0 - (aspect - 5.0) / 10.0)
        else:
            aspect_score = 1.0
    else:
        aspect_score = 0.0

    # Weighted combination
    score = (
        0.35 * area_score +
        0.30 * centrality +
        0.20 * edge_score +
        0.15 * aspect_score
    )

    return float(score)


def _select_winning_group(
    groups: list,
    image_width: int,
    image_height: int,
) -> Tuple[Optional[ContourGroup], GroupSelectionResult]:
    """
    Score all groups and select the winner.

    Args:
        groups: List of ContourGroup from _group_from_roots()
        image_width, image_height: Image dimensions

    Returns:
        (winning_group, GroupSelectionResult)
        winning_group may be None if no groups exist
    """
    if not groups:
        return None, GroupSelectionResult(
            group_count=0,
            selected_group_index=-1,
            selected_group_id=-1,
            selected_group_bbox=(0, 0, 0, 0),
            selected_group_score=0.0,
            runner_up_score=0.0,
            winner_margin=0.0,
            fallback_used=True,
            fallback_reason="no_groups",
        )

    # Score all groups
    scored = []
    for i, group in enumerate(groups):
        score = _score_contour_group(group, image_width, image_height)
        scored.append((i, group, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[2], reverse=True)

    best_idx, best_group, best_score = scored[0]

    # Runner-up and margin
    if len(scored) > 1:
        runner_up_score = scored[1][2]
    else:
        runner_up_score = 0.0

    winner_margin = best_score - runner_up_score

    logger.info(
        f"Group selection: {len(groups)} groups, "
        f"winner=group_{best_group.group_id} score={best_score:.3f} "
        f"margin={winner_margin:.3f}"
    )

    return best_group, GroupSelectionResult(
        group_count=len(groups),
        selected_group_index=best_idx,
        selected_group_id=best_group.group_id,
        selected_group_bbox=best_group.bbox,
        selected_group_score=best_score,
        runner_up_score=runner_up_score,
        winner_margin=winner_margin,
        fallback_used=False,
        fallback_reason="",
    )


def _isolate_with_grouping(
    contours: list,
    hierarchy: np.ndarray,
    image_width: int,
    image_height: int,
    min_area_ratio: float = 0.005,
    max_area_ratio: float = 0.95,
) -> Tuple[list, Optional[GroupSelectionResult]]:
    """
    Primary object grouping: isolate contours via hierarchy-aware grouping.

    This is the new production path that:
    1. Builds hierarchy nodes from raw contours
    2. Identifies eligible roots (top-level, non-border, right size)
    3. Groups each root with its descendants
    4. Scores groups as units
    5. Returns only the winning group's contours

    Args:
        contours: Raw contours from cv2.findContours
        hierarchy: Hierarchy array from cv2.findContours (RETR_TREE)
        image_width, image_height: Image dimensions
        min_area_ratio, max_area_ratio: Size eligibility thresholds

    Returns:
        (selected_contours, group_result)
        Falls back to legacy behavior if grouping fails.
    """
    try:
        # Step 1: Build hierarchy nodes
        nodes = _build_hierarchy_nodes(
            contours, hierarchy, image_width, image_height,
            min_area_ratio, max_area_ratio
        )

        if not nodes:
            logger.warning("No hierarchy nodes built, falling back to legacy isolation")
            return _isolate_body_contours(
                contours, hierarchy, image_width, image_height,
                min_area_ratio, max_area_ratio
            ), None

        # Step 2: Group from eligible roots
        groups = _group_from_roots(nodes, image_width, image_height)

        if not groups:
            logger.warning("No contour groups formed, falling back to legacy isolation")
            return _isolate_body_contours(
                contours, hierarchy, image_width, image_height,
                min_area_ratio, max_area_ratio
            ), GroupSelectionResult(
                group_count=0,
                selected_group_index=-1,
                selected_group_id=-1,
                selected_group_bbox=(0, 0, 0, 0),
                selected_group_score=0.0,
                runner_up_score=0.0,
                winner_margin=0.0,
                fallback_used=True,
                fallback_reason="no_groups_formed",
            )

        # Step 3: Score and select winning group
        winning_group, group_result = _select_winning_group(
            groups, image_width, image_height
        )

        if winning_group is None:
            logger.warning("Group selection failed, falling back to legacy isolation")
            fallback = _isolate_body_contours(
                contours, hierarchy, image_width, image_height,
                min_area_ratio, max_area_ratio
            )
            group_result.fallback_used = True
            group_result.fallback_reason = "selection_failed"
            return fallback, group_result

        # Step 4: Return winning group's contours
        # Only include the root contour for body selection, not descendants
        # (descendants are internal features like soundholes, not body outline)
        selected_contours = [winning_group.root_node.contour]

        logger.info(
            f"Grouping complete: selected group_{winning_group.group_id} "
            f"with {len(winning_group.member_indices)} members, "
            f"returning root contour for body selection"
        )

        return selected_contours, group_result

    except Exception as e:
        logger.exception(f"Grouping failed with error: {e}, falling back to legacy")
        return _isolate_body_contours(
            contours, hierarchy, image_width, image_height,
            min_area_ratio, max_area_ratio
        ), GroupSelectionResult(
            group_count=0,
            selected_group_index=-1,
            selected_group_id=-1,
            selected_group_bbox=(0, 0, 0, 0),
            selected_group_score=0.0,
            runner_up_score=0.0,
            winner_margin=0.0,
            fallback_used=True,
            fallback_reason=f"exception: {str(e)[:50]}",
        )


@dataclass
class EdgeToDXFResult:
    """Result of edge-to-DXF conversion."""
    source_path: str
    output_path: str
    line_count: int
    edge_pixel_count: int
    image_size_px: Tuple[int, int]  # (width, height)
    output_size_mm: Tuple[float, float]  # (width, height)
    mm_per_px: float
    processing_time_ms: float
    file_size_bytes: int
    contour_count: int = 0  # Number of contours traced
    stage_timings: Dict[str, float] = field(default_factory=dict)  # Per-stage timing
    # Grouping metadata (debug-only, internal)
    grouping: Optional[Dict[str, Any]] = None

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"Edge-to-DXF Conversion Complete\n"
            f"  Source: {self.source_path}\n"
            f"  Output: {self.output_path}\n"
            f"  Image: {self.image_size_px[0]} x {self.image_size_px[1]} px\n"
            f"  Scale: {self.mm_per_px:.4f} mm/px\n"
            f"  Output: {self.output_size_mm[0]:.1f} x {self.output_size_mm[1]:.1f} mm\n"
            f"  Edge pixels: {self.edge_pixel_count:,}\n"
            f"  Contours: {self.contour_count:,}\n"
            f"  LINE entities: {self.line_count:,}\n"
            f"  File size: {self.file_size_bytes / 1024 / 1024:.2f} MB\n"
            f"  Time: {self.processing_time_ms:.0f} ms"
        )


class EdgeToDXF:
    """
    High-fidelity edge-to-DXF converter.

    Converts image edges to individual LINE entities in DXF format.
    Produces large, detailed files suitable for archival or manual tracing.
    """

    def __init__(
        self,
        canny_low: int = 50,
        canny_high: int = 150,
        adjacency_threshold: float = 3.0,
        dxf_version: str = "R12",
        layer_name: str = "EDGES",
    ):
        """
        Initialize the converter.

        Args:
            canny_low: Canny edge detection low threshold
            canny_high: Canny edge detection high threshold
            adjacency_threshold: Max pixel distance to connect as LINE
            dxf_version: DXF version (R12 for maximum compatibility)
            layer_name: DXF layer name for LINE entities
        """
        if not EZDXF_AVAILABLE:
            raise ImportError("ezdxf is required: pip install ezdxf")

        self.canny_low = canny_low
        self.canny_high = canny_high
        self.adjacency_threshold = adjacency_threshold
        self.dxf_version = dxf_version
        self.layer_name = layer_name

    def convert(
        self,
        source_path: str,
        output_path: Optional[str] = None,
        target_height_mm: float = 500.0,
        blur_kernel: int = 3,
        morph_close_kernel: int = 0,
        isolate_body: bool = False,
    ) -> EdgeToDXFResult:
        """
        Convert image edges to DXF LINE entities.

        Args:
            source_path: Path to source image (JPG, PNG, etc.)
            output_path: Output DXF path (default: {source}_edges.dxf)
            target_height_mm: Target height in mm for scaling
            blur_kernel: Gaussian blur kernel size (0 to disable)
            morph_close_kernel: Morphological close kernel (0 to disable)
            isolate_body: If True, use hierarchy to filter to body candidates only.
                Removes page borders, child contours, and noise before DXF creation.

        Returns:
            EdgeToDXFResult with conversion statistics
        """
        start_time = time.time()
        stage_timings: Dict[str, float] = {}

        # Validate input
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        # Default output path
        if output_path is None:
            output_path = str(source.with_name(f"{source.stem}_edges.dxf"))

        # Stage: Image load
        t0 = time.time()
        logger.info(f"Loading: {source_path}")
        img = cv2.imread(str(source_path))
        if img is None:
            raise ValueError(f"Failed to load image: {source_path}")
        stage_timings["image_load_ms"] = round((time.time() - t0) * 1000, 1)

        h, w = img.shape[:2]
        logger.info(f"Image size: {w} x {h} px")

        # Stage: Edge detection (includes grayscale, blur, canny)
        t0 = time.time()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if blur_kernel > 0:
            gray = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)

        logger.info(f"Running Canny edge detection (thresholds: {self.canny_low}/{self.canny_high})")
        edges = cv2.Canny(gray, self.canny_low, self.canny_high)

        if morph_close_kernel > 0:
            kernel = np.ones((morph_close_kernel, morph_close_kernel), np.uint8)
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        stage_timings["edge_detect_ms"] = round((time.time() - t0) * 1000, 1)

        # Get edge pixel coordinates
        edge_points = np.column_stack(np.where(edges > 0))
        edge_count = len(edge_points)
        logger.info(f"Found {edge_count:,} edge pixels")

        if edge_count == 0:
            raise ValueError("No edges detected in image")

        # Calculate scale
        mm_per_px = target_height_mm / h
        output_w = w * mm_per_px
        output_h = h * mm_per_px
        logger.info(f"Scale: {mm_per_px:.4f} mm/px -> {output_w:.1f} x {output_h:.1f} mm")

        # Stage: Contour tracing
        t0 = time.time()
        logger.info("Tracing contours from edge image...")

        # Track grouping result for debug metadata
        group_result: Optional[GroupSelectionResult] = None

        if isolate_body:
            # Use RETR_TREE to get hierarchy for body isolation
            logger.info("Using hierarchy-aware isolation mode with PRIMARY OBJECT GROUPING")
            contours, hierarchy = cv2.findContours(
                edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
            )

            # SURGICAL BORDER REMOVAL (Phase 1 of Melody Maker fix):
            # Remove page borders from the contour pool BEFORE grouping.
            # This prevents borders from entering the candidate contest
            # and becoming fallback winners when body is fragmented.
            contours, borders_removed = _remove_page_borders_early(
                contours, hierarchy, w, h
            )
            if borders_removed > 0:
                logger.info(f"Proceeding with {len([c for c in contours if len(c) >= 3])} non-border contours")

            # PRIMARY OBJECT GROUPING:
            # Instead of scoring all contours globally, we:
            # 1. Build hierarchy nodes (now without page borders)
            # 2. Group each eligible root + descendants
            # 3. Score groups as units
            # 4. Select winning group
            # 5. Return only winning group's contours
            valid_contours, group_result = _isolate_with_grouping(
                contours, hierarchy, w, h,
                min_area_ratio=0.005,
                max_area_ratio=0.95,
            )

            # Log grouping outcome
            if group_result:
                if group_result.fallback_used:
                    logger.warning(
                        f"Grouping fallback used: {group_result.fallback_reason}"
                    )
                else:
                    logger.info(
                        f"Group selection: {group_result.group_count} groups, "
                        f"selected group {group_result.selected_group_id}, "
                        f"score={group_result.selected_group_score:.3f}, "
                        f"margin={group_result.winner_margin:.3f}"
                    )

            # Debug overlay (if DEBUG_CONTOURS=1)
            if DEBUG_OVERLAY_AVAILABLE and is_debug_enabled():
                try:
                    logger.info("Generating debug overlay...")
                    debug_nodes = _build_debug_nodes_from_hierarchy(
                        contours, hierarchy, w, h
                    )

                    # Score candidates for debug visualization
                    candidates = [n for n in debug_nodes if n.is_outer_candidate]
                    score_map, selected_idx, runner_up, margin = \
                        score_body_candidates_for_debug(candidates, w, h)

                    # Hydrate scores onto nodes
                    for node in debug_nodes:
                        if node.idx in score_map:
                            node.score = score_map[node.idx].score

                    # Determine recommendation for display
                    if margin >= 0.12 and score_map.get(selected_idx, DebugContourScore(0, 0)).score >= 0.70:
                        rec = "accept"
                    elif score_map.get(selected_idx, DebugContourScore(0, 0)).score >= 0.45:
                        rec = "review"
                    else:
                        rec = "reject"

                    # Include grouping info in debug notes
                    debug_notes = [
                        f"Total contours: {len(contours)}",
                        f"Body candidates: {len(valid_contours)}",
                    ]
                    if group_result and not group_result.fallback_used:
                        debug_notes.append(
                            f"Groups: {group_result.group_count}, "
                            f"selected: {group_result.selected_group_id}"
                        )

                    summary = to_debug_summary(
                        source_name=str(source),
                        candidate_count=len(candidates),
                        selected_idx=selected_idx,
                        selection_score=score_map.get(selected_idx, DebugContourScore(0, 0)).score if selected_idx else 0.0,
                        runner_up_score=runner_up,
                        winner_margin=margin,
                        recommendation=rec,
                        notes=debug_notes,
                    )

                    # Write debug bundle
                    out_dir = Path(output_path).parent if output_path else Path(".")
                    paths = write_debug_bundle(img, debug_nodes, summary, out_dir)
                    logger.info(f"Debug overlay written: {paths['overlay']}")
                    stage_timings["debug_overlay_ms"] = round((time.time() - t0) * 1000, 1)

                except Exception as e:
                    logger.warning(f"Debug overlay failed (non-fatal): {e}")

        else:
            # Original behavior: all contours
            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            # Filter degenerate contours (< 3 points)
            valid_contours = [c for c in contours if len(c) >= 3]

        logger.info(f"Found {len(contours)} contours, {len(valid_contours)} valid")
        stage_timings["contour_trace_ms"] = round((time.time() - t0) * 1000, 1)

        if not valid_contours:
            raise ValueError("No valid contours found in edge image")

        # Stage: DXF generation
        t0 = time.time()
        logger.info(f"Creating DXF ({self.dxf_version})...")
        doc = ezdxf.new(self.dxf_version)
        msp = doc.modelspace()

        # Add layer
        if self.layer_name not in doc.layers:
            doc.layers.add(self.layer_name)

        # Convert contours to LINE entities (preserving topology)
        line_count = 0
        contour_count = 0

        logger.info("Converting contours to LINE entities...")
        for contour in valid_contours:
            contour_count += 1
            points = contour.reshape(-1, 2)  # Shape: (N, 2) with (x, y)

            # Create LINE entities along the contour path
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]

                # Convert to mm coordinates (flip Y for CAD convention)
                mx1 = x1 * mm_per_px
                my1 = (h - y1) * mm_per_px
                mx2 = x2 * mm_per_px
                my2 = (h - y2) * mm_per_px

                msp.add_line(
                    (mx1, my1),
                    (mx2, my2),
                    dxfattribs={'layer': self.layer_name}
                )
                line_count += 1

            # Close the contour (connect last point to first)
            if len(points) >= 3:
                x1, y1 = points[-1]
                x2, y2 = points[0]
                mx1 = x1 * mm_per_px
                my1 = (h - y1) * mm_per_px
                mx2 = x2 * mm_per_px
                my2 = (h - y2) * mm_per_px
                msp.add_line(
                    (mx1, my1),
                    (mx2, my2),
                    dxfattribs={'layer': self.layer_name}
                )
                line_count += 1

        logger.info(f"Created {line_count:,} LINE entities from {contour_count} contours")
        stage_timings["dxf_generate_ms"] = round((time.time() - t0) * 1000, 1)

        # Stage: DXF save
        t0 = time.time()
        logger.info(f"Saving: {output_path}")
        doc.saveas(output_path)
        stage_timings["dxf_save_ms"] = round((time.time() - t0) * 1000, 1)

        # Get file size
        file_size = Path(output_path).stat().st_size

        processing_time = (time.time() - start_time) * 1000

        # Log stage timing summary
        timing_str = " | ".join(f"{k}={v}" for k, v in stage_timings.items())
        logger.info(f"EDGE_TO_DXF_TIMING | total={processing_time:.0f}ms | {timing_str}")

        # Build grouping metadata for debug (internal only)
        grouping_metadata = None
        if group_result is not None:
            grouping_metadata = {
                "group_count": group_result.group_count,
                "selected_group_index": group_result.selected_group_index,
                "selected_group_id": group_result.selected_group_id,
                "selected_group_bbox": group_result.selected_group_bbox,
                "selected_group_score": round(group_result.selected_group_score, 3),
                "runner_up_score": round(group_result.runner_up_score, 3),
                "group_winner_margin": round(group_result.winner_margin, 3),
                "grouping_fallback_used": group_result.fallback_used,
                "fallback_reason": group_result.fallback_reason,
            }

        result = EdgeToDXFResult(
            source_path=str(source_path),
            output_path=output_path,
            line_count=line_count,
            edge_pixel_count=edge_count,
            image_size_px=(w, h),
            output_size_mm=(output_w, output_h),
            mm_per_px=mm_per_px,
            processing_time_ms=processing_time,
            file_size_bytes=file_size,
            contour_count=contour_count,
            stage_timings=stage_timings,
            grouping=grouping_metadata,
        )

        logger.info(f"Complete in {processing_time:.0f}ms")
        return result

    def convert_enhanced(
        self,
        source_path: str,
        output_path: Optional[str] = None,
        target_height_mm: float = 500.0,
        gap_close_size: int = 7,
        mask_text: bool = True,
    ) -> EdgeToDXFResult:
        """
        Enhanced conversion with multi-scale edge fusion.

        Combines edges from multiple Canny threshold levels for more
        complete edge coverage. Produces more LINE entities.

        Text masking (Sprint 3): Detects text regions with OCR and removes
        them from edges before morphological closing. This prevents the 7×7
        kernel from bridging text glyph strokes into solid blobs.

        Args:
            source_path: Path to source image
            output_path: Output DXF path
            target_height_mm: Target height in mm
            gap_close_size: Morphological closing kernel size (0=disabled, 7=default)
            mask_text: If True, detect and mask text regions before gap closing

        Returns:
            EdgeToDXFResult with conversion statistics
        """
        start_time = time.time()

        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        if output_path is None:
            output_path = str(source.with_name(f"{source.stem}_enhanced.dxf"))

        # Load image
        img = cv2.imread(str(source_path))
        if img is None:
            raise ValueError(f"Failed to load image: {source_path}")

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Multi-scale edge detection
        logger.info("Running multi-scale edge detection...")
        edge_levels = [
            (30, 100),   # Fine detail
            (50, 150),   # Standard
            (80, 200),   # Strong edges
        ]

        combined_edges = np.zeros_like(gray)
        for low, high in edge_levels:
            edges = cv2.Canny(gray, low, high)
            combined_edges = cv2.bitwise_or(combined_edges, edges)

        # Text masking: remove text edges BEFORE morphological closing
        # This prevents the 7×7 kernel from bridging text glyph strokes
        text_removed_count = 0
        if mask_text:
            text_regions = detect_text_regions(img, min_confidence=0.3, padding_px=5)
            if text_regions:
                text_mask = create_text_mask((h, w), text_regions)
                combined_edges, text_removed_count = apply_text_mask_to_edges(
                    combined_edges, text_mask
                )
                logger.info(
                    f"TEXT_MASK | Removed {text_removed_count:,} edge pixels "
                    f"from {len(text_regions)} text regions"
                )

        # Bridge pixel-level gaps before contour extraction (restored from Phase 2)
        if gap_close_size > 0:
            kernel = np.ones((gap_close_size, gap_close_size), np.uint8)
            combined_edges = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)
            logger.info(f"Applied morphological closing with kernel size {gap_close_size}")

        # Get edge pixels
        edge_points = np.column_stack(np.where(combined_edges > 0))
        edge_count = len(edge_points)
        logger.info(f"Found {edge_count:,} edge pixels (multi-scale)")

        if edge_count == 0:
            raise ValueError("No edges detected")

        # Scale
        mm_per_px = target_height_mm / h
        output_w = w * mm_per_px
        output_h = h * mm_per_px

        # Create DXF
        doc = ezdxf.new(self.dxf_version)
        msp = doc.modelspace()
        doc.layers.add(self.layer_name)

        # TOPOLOGY FIX: Use cv2.findContours() for proper contour tracing
        logger.info("Tracing contours from combined edge image...")
        contours, _ = cv2.findContours(combined_edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        valid_contours = [c for c in contours if len(c) >= 3]
        logger.info(f"Found {len(contours)} contours, {len(valid_contours)} valid")

        if not valid_contours:
            raise ValueError("No valid contours found")

        line_count = 0
        for contour in valid_contours:
            points = contour.reshape(-1, 2)
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                mx1 = x1 * mm_per_px
                my1 = (h - y1) * mm_per_px
                mx2 = x2 * mm_per_px
                my2 = (h - y2) * mm_per_px
                msp.add_line((mx1, my1), (mx2, my2), dxfattribs={'layer': self.layer_name})
                line_count += 1

            # Close contour
            if len(points) >= 3:
                x1, y1 = points[-1]
                x2, y2 = points[0]
                mx1 = x1 * mm_per_px
                my1 = (h - y1) * mm_per_px
                mx2 = x2 * mm_per_px
                my2 = (h - y2) * mm_per_px
                msp.add_line((mx1, my1), (mx2, my2), dxfattribs={'layer': self.layer_name})
                line_count += 1

        logger.info(f"Created {line_count:,} LINE entities from {len(valid_contours)} contours")
        doc.saveas(output_path)
        file_size = Path(output_path).stat().st_size
        processing_time = (time.time() - start_time) * 1000

        return EdgeToDXFResult(
            source_path=str(source_path),
            output_path=output_path,
            line_count=line_count,
            edge_pixel_count=edge_count,
            image_size_px=(w, h),
            output_size_mm=(output_w, output_h),
            mm_per_px=mm_per_px,
            processing_time_ms=processing_time,
            file_size_bytes=file_size,
        )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Edge-to-DXF: Convert image edges to high-fidelity LINE DXF"
    )
    parser.add_argument("source", help="Source image path (JPG, PNG, etc.)")
    parser.add_argument("-o", "--output", help="Output DXF path")
    parser.add_argument("--height", type=float, default=500.0,
                        help="Target height in mm (default: 500)")
    parser.add_argument("--enhanced", action="store_true",
                        help="Use multi-scale edge fusion for more detail")
    parser.add_argument("--canny-low", type=int, default=50,
                        help="Canny low threshold (default: 50)")
    parser.add_argument("--canny-high", type=int, default=150,
                        help="Canny high threshold (default: 150)")
    parser.add_argument("--adjacency", type=float, default=3.0,
                        help="Max pixel distance to connect (default: 3.0)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    converter = EdgeToDXF(
        canny_low=args.canny_low,
        canny_high=args.canny_high,
        adjacency_threshold=args.adjacency,
    )

    if args.enhanced:
        result = converter.convert_enhanced(
            args.source,
            output_path=args.output,
            target_height_mm=args.height,
        )
    else:
        result = converter.convert(
            args.source,
            output_path=args.output,
            target_height_mm=args.height,
        )

    print(result.summary())


if __name__ == "__main__":
    main()
