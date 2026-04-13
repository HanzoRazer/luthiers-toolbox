"""
Annotation Extraction Module (Pass B)
=====================================

Dedicated extraction for annotation/document elements:
- Titles
- Dimensions
- Labels
- Text-like drafting strokes
- Arrows / leaders

Uses lighter thresholds than Pass A (structural) to preserve
fine detail that would otherwise be filtered out.

Phase 3: Capture only, no layer assignment or OCR yet.

Author: Production Shop
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ─── Configuration ──────────────────────────────────────────────────────────

# Pass B defaults - tuned for annotation capture
ANNOTATION_BLOCK_SIZE = 21
ANNOTATION_C_CONSTANT = 10
ANNOTATION_MIN_AREA_PX = 12  # Much lower than Pass A (50)
ANNOTATION_EPSILON_FACTOR = 0.0005  # Lighter than Pass A (0.001)
ANNOTATION_MAX_AREA_RATIO = 0.3  # Exclude large shapes (body, page border)


# ─── Result Models ──────────────────────────────────────────────────────────

@dataclass
class AnnotationEntity:
    """Single annotation entity from Pass B."""
    contour: np.ndarray
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    area: float
    perimeter: float
    aspect_ratio: float
    vertex_count: int
    is_text_like: bool = False
    category: str = "unknown"  # text, dimension, arrow, label, other


@dataclass
class AnnotationExtractionResult:
    """Result from Pass B annotation extraction."""
    success: bool
    entities: List[AnnotationEntity] = field(default_factory=list)
    entity_count: int = 0
    bbox_count: int = 0
    image_size_px: Tuple[int, int] = (0, 0)
    mm_per_px: float = 0.0
    processing_time_ms: float = 0.0
    error: str = ""
    warnings: List[str] = field(default_factory=list)
    debug: Dict[str, Any] = field(default_factory=dict)


# ─── Classification Helpers ─────────────────────────────────────────────────

def _classify_annotation(
    contour: np.ndarray,
    bbox: Tuple[int, int, int, int],
    area: float,
    perimeter: float,
) -> Tuple[str, bool]:
    """
    Classify an annotation entity by shape characteristics.

    Returns:
        (category, is_text_like)
    """
    x, y, w, h = bbox
    aspect = w / max(h, 1)
    vertex_count = len(contour)

    # Text-like: small area, moderate aspect ratio, many vertices
    # Typical for character strokes
    if area < 500 and 0.2 < aspect < 5.0 and vertex_count > 4:
        return "text", True

    # Dimension line: very elongated (aspect > 8 or < 0.125)
    if aspect > 8.0 or aspect < 0.125:
        return "dimension", False

    # Arrow/leader: small, triangular (3-6 vertices)
    if area < 200 and 3 <= vertex_count <= 6:
        return "arrow", False

    # Label box: rectangular, moderate size
    if 4 <= vertex_count <= 8 and 0.5 < aspect < 2.0 and 100 < area < 5000:
        return "label", False

    return "other", False


def _is_inside_body_region(
    bbox: Tuple[int, int, int, int],
    body_bbox: Optional[Tuple[int, int, int, int]],
    margin_ratio: float = 0.1,
) -> bool:
    """Check if annotation bbox is inside the body region (with margin)."""
    if body_bbox is None:
        return False

    bx, by, bw, bh = body_bbox
    ax, ay, aw, ah = bbox

    # Expand body bbox by margin
    margin_x = int(bw * margin_ratio)
    margin_y = int(bh * margin_ratio)

    # Check if annotation center is inside expanded body region
    center_x = ax + aw // 2
    center_y = ay + ah // 2

    return (
        bx - margin_x <= center_x <= bx + bw + margin_x and
        by - margin_y <= center_y <= by + bh + margin_y
    )


# ─── Main Extraction ────────────────────────────────────────────────────────

def extract_annotations(
    image: np.ndarray,
    target_height_mm: float = 500.0,
    body_bbox: Optional[Tuple[int, int, int, int]] = None,
    block_size: int = ANNOTATION_BLOCK_SIZE,
    c_constant: int = ANNOTATION_C_CONSTANT,
    min_area_px: int = ANNOTATION_MIN_AREA_PX,
    epsilon_factor: float = ANNOTATION_EPSILON_FACTOR,
    max_area_ratio: float = ANNOTATION_MAX_AREA_RATIO,
) -> AnnotationExtractionResult:
    """
    Extract annotation entities from blueprint image.

    Uses adaptive threshold with lighter parameters than Pass A
    to preserve fine text and dimension details.

    Args:
        image: BGR image (numpy array)
        target_height_mm: Target height for scaling
        body_bbox: Optional body bounding box to filter annotations
        block_size: Adaptive threshold block size
        c_constant: Adaptive threshold C constant
        min_area_px: Minimum contour area in pixels
        epsilon_factor: approxPolyDP epsilon factor (lighter = more detail)
        max_area_ratio: Maximum area ratio to image (exclude large shapes)

    Returns:
        AnnotationExtractionResult with annotation entities
    """
    start_time = time.time()
    warnings: List[str] = []

    try:
        h, w = image.shape[:2]
        mm_per_px = target_height_mm / h
        image_area = h * w
        max_area_px = image_area * max_area_ratio

        logger.info(f"Pass B annotation extraction: {w}x{h}, max_area={max_area_px:.0f}px")

        # Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Handle inverted images
        if np.mean(gray) < 127:
            gray = 255 - gray

        # Adaptive threshold (same as Pass A but different filtering)
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

        logger.info(f"Pass B raw contours: {len(contours)}")

        # Filter and classify
        entities: List[AnnotationEntity] = []
        text_like_count = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            # Skip too small or too large
            if area < min_area_px or area > max_area_px:
                continue

            # Get bounding box
            bbox = cv2.boundingRect(contour)
            x, y, bw, bh = bbox

            # Skip if inside body region (Pass A territory)
            # This prevents annotation pass from duplicating body contours
            if _is_inside_body_region(bbox, body_bbox, margin_ratio=0.05):
                # Only skip if it's a large contour (likely body part)
                if area > 1000:
                    continue

            # Simplify with lighter epsilon
            perimeter = cv2.arcLength(contour, True)
            epsilon = epsilon_factor * perimeter
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) < 3:
                continue

            # Classify
            category, is_text_like = _classify_annotation(
                approx, bbox, area, perimeter
            )

            if is_text_like:
                text_like_count += 1

            aspect_ratio = bw / max(bh, 1)

            entities.append(AnnotationEntity(
                contour=approx,
                bbox=bbox,
                area=area,
                perimeter=perimeter,
                aspect_ratio=aspect_ratio,
                vertex_count=len(approx),
                is_text_like=is_text_like,
                category=category,
            ))

        elapsed_ms = (time.time() - start_time) * 1000

        # Count unique bounding boxes (for text grouping later)
        bbox_set = set((e.bbox for e in entities))
        bbox_count = len(bbox_set)

        logger.info(
            f"Pass B complete: {len(entities)} entities, "
            f"{text_like_count} text-like, {bbox_count} unique bboxes"
        )

        return AnnotationExtractionResult(
            success=True,
            entities=entities,
            entity_count=len(entities),
            bbox_count=bbox_count,
            image_size_px=(w, h),
            mm_per_px=mm_per_px,
            processing_time_ms=elapsed_ms,
            error="",
            warnings=warnings,
            debug={
                "raw_contours": len(contours),
                "text_like_count": text_like_count,
                "min_area_px": min_area_px,
                "max_area_px": max_area_px,
                "epsilon_factor": epsilon_factor,
                "body_bbox_provided": body_bbox is not None,
                "categories": {
                    "text": sum(1 for e in entities if e.category == "text"),
                    "dimension": sum(1 for e in entities if e.category == "dimension"),
                    "arrow": sum(1 for e in entities if e.category == "arrow"),
                    "label": sum(1 for e in entities if e.category == "label"),
                    "other": sum(1 for e in entities if e.category == "other"),
                },
            },
        )

    except Exception as e:
        logger.exception(f"Pass B extraction failed: {e}")
        return AnnotationExtractionResult(
            success=False,
            error=str(e),
            warnings=warnings,
            processing_time_ms=(time.time() - start_time) * 1000,
        )


def get_annotation_contours(result: AnnotationExtractionResult) -> List[np.ndarray]:
    """Extract raw contours from annotation result for DXF/overlay use."""
    return [e.contour for e in result.entities]
