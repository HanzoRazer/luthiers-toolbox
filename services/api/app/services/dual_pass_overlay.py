"""
Dual-Pass Debug Overlay (Phase 4)
=================================

Visual debugging utility for layered dual-pass extraction.
Shows entities by semantic layer with distinct colors.

Layer Colors:
- BODY: Green
- AUX_VIEWS: Blue
- ANNOTATION: Orange
- TITLE_BLOCK: Purple/Magenta
- PAGE_FRAME: Red

Author: Production Shop
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from .layer_builder import Layer, LayeredEntities, LAYER_COLORS

logger = logging.getLogger(__name__)

# Legacy color definitions for backward compatibility
PASS_A_COLOR = (0, 255, 0)      # Green
PASS_B_COLOR = (0, 165, 255)    # Orange
BACKGROUND_COLOR = (30, 30, 30)  # Dark gray


def create_dual_pass_overlay(
    image: np.ndarray,
    pass_a_contours: List[np.ndarray],
    pass_b_contours: List[np.ndarray],
    alpha: float = 0.7,
    line_thickness: int = 2,
) -> np.ndarray:
    """
    Create overlay image showing Pass A and Pass B contours.

    Args:
        image: Original BGR image
        pass_a_contours: List of contours from Pass A (structural)
        pass_b_contours: List of contours from Pass B (annotation)
        alpha: Blend factor for overlay (0=original, 1=overlay only)
        line_thickness: Thickness of contour lines

    Returns:
        BGR image with colored overlay
    """
    h, w = image.shape[:2]

    # Create overlay on dark background
    overlay = np.full((h, w, 3), BACKGROUND_COLOR, dtype=np.uint8)

    # Draw Pass A contours in green
    if pass_a_contours:
        cv2.drawContours(overlay, pass_a_contours, -1, PASS_A_COLOR, line_thickness)
        logger.info(f"Overlay: Drew {len(pass_a_contours)} Pass A contours (green)")

    # Draw Pass B contours in orange
    if pass_b_contours:
        cv2.drawContours(overlay, pass_b_contours, -1, PASS_B_COLOR, line_thickness)
        logger.info(f"Overlay: Drew {len(pass_b_contours)} Pass B contours (orange)")

    # Blend with original
    result = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)

    return result


def create_side_by_side_overlay(
    image: np.ndarray,
    pass_a_contours: List[np.ndarray],
    pass_b_contours: List[np.ndarray],
    line_thickness: int = 2,
) -> np.ndarray:
    """
    Create side-by-side comparison showing Pass A and Pass B separately.

    Args:
        image: Original BGR image
        pass_a_contours: List of contours from Pass A (structural)
        pass_b_contours: List of contours from Pass B (annotation)
        line_thickness: Thickness of contour lines

    Returns:
        BGR image with side-by-side comparison
    """
    h, w = image.shape[:2]

    # Create left panel (Pass A on original)
    left = image.copy()
    if pass_a_contours:
        cv2.drawContours(left, pass_a_contours, -1, PASS_A_COLOR, line_thickness)

    # Create right panel (Pass B on original)
    right = image.copy()
    if pass_b_contours:
        cv2.drawContours(right, pass_b_contours, -1, PASS_B_COLOR, line_thickness)

    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.5, min(w, h) / 1000)
    cv2.putText(left, f"Pass A: {len(pass_a_contours)} structural",
                (10, 30), font, font_scale, PASS_A_COLOR, 2)
    cv2.putText(right, f"Pass B: {len(pass_b_contours)} annotation",
                (10, 30), font, font_scale, PASS_B_COLOR, 2)

    # Combine side by side
    result = np.hstack([left, right])

    return result


def save_dual_pass_overlay(
    source_image_path: str,
    pass_a_contours: List[np.ndarray],
    pass_b_contours: List[np.ndarray],
    output_path: Optional[str] = None,
    mode: str = "combined",
) -> str:
    """
    Load image, create overlay, and save to file.

    Args:
        source_image_path: Path to original image
        pass_a_contours: List of contours from Pass A
        pass_b_contours: List of contours from Pass B
        output_path: Output path (auto-generated if None)
        mode: "combined" for blended overlay, "sidebyside" for split view

    Returns:
        Path to saved overlay image
    """
    # Load source image
    image = cv2.imread(source_image_path)
    if image is None:
        raise ValueError(f"Failed to load image: {source_image_path}")

    # Create overlay
    if mode == "sidebyside":
        overlay = create_side_by_side_overlay(
            image, pass_a_contours, pass_b_contours
        )
    else:
        overlay = create_dual_pass_overlay(
            image, pass_a_contours, pass_b_contours
        )

    # Generate output path if not provided
    if output_path is None:
        source_path = Path(source_image_path)
        output_path = str(
            source_path.parent / f"{source_path.stem}_dual_pass_overlay.png"
        )

    # Save
    cv2.imwrite(output_path, overlay)
    logger.info(f"Saved dual-pass overlay: {output_path}")

    return output_path


def generate_benchmark_overlay(
    source_image_path: str,
    target_height_mm: float = 500.0,
    output_dir: Optional[str] = None,
) -> Tuple[str, dict]:
    """
    Generate dual-pass overlay for benchmarking.

    Runs both Pass A and Pass B extraction, then creates overlay.

    Args:
        source_image_path: Path to blueprint image
        target_height_mm: Target height for scaling
        output_dir: Output directory (defaults to source directory)

    Returns:
        (overlay_path, metadata_dict)
    """
    from .blueprint_extract import extract_structural_pass, extract_annotation_pass
    from .annotation_extract import get_annotation_contours
    from edge_to_dxf import extract_entities_simple

    # Load image
    image = cv2.imread(source_image_path)
    if image is None:
        raise ValueError(f"Failed to load image: {source_image_path}")

    # Run Pass A (get contours directly)
    pass_a_entities = extract_entities_simple(
        image=image,
        target_height_mm=target_height_mm,
    )
    pass_a_contours = pass_a_entities.contours

    # Run Pass B
    from .annotation_extract import extract_annotations
    pass_b_result = extract_annotations(
        image=image,
        target_height_mm=target_height_mm,
    )
    pass_b_contours = get_annotation_contours(pass_b_result)

    # Create overlay
    overlay = create_dual_pass_overlay(image, pass_a_contours, pass_b_contours)

    # Generate output path
    source_path = Path(source_image_path)
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = source_path.parent

    output_path = str(out_dir / f"{source_path.stem}_dual_pass_overlay.png")
    cv2.imwrite(output_path, overlay)

    # Build metadata
    metadata = {
        "source": source_image_path,
        "overlay": output_path,
        "pass_a_count": len(pass_a_contours),
        "pass_b_count": len(pass_b_contours),
        "pass_b_text_like": pass_b_result.debug.get("text_like_count", 0),
        "pass_b_categories": pass_b_result.debug.get("categories", {}),
    }

    logger.info(
        f"Generated benchmark overlay: {output_path}\n"
        f"  Pass A: {len(pass_a_contours)} structural\n"
        f"  Pass B: {len(pass_b_contours)} annotation"
    )

    return output_path, metadata


# ─── Phase 4: Layered Overlay ───────────────────────────────────────────────

def create_layered_overlay(
    image: np.ndarray,
    layered_entities: LayeredEntities,
    alpha: float = 0.7,
    line_thickness: int = 2,
) -> np.ndarray:
    """
    Create overlay showing all 5 semantic layers.

    Colors:
    - BODY: Green
    - AUX_VIEWS: Blue
    - ANNOTATION: Orange
    - TITLE_BLOCK: Purple
    - PAGE_FRAME: Red

    Args:
        image: Original BGR image
        layered_entities: LayeredEntities from build_layers()
        alpha: Blend factor
        line_thickness: Contour line thickness

    Returns:
        BGR image with layered overlay
    """
    h, w = image.shape[:2]
    overlay = np.full((h, w, 3), BACKGROUND_COLOR, dtype=np.uint8)

    # Draw each layer
    for layer in Layer:
        entities = layered_entities.get_layer(layer)
        if entities:
            contours = [e.contour for e in entities]
            color = LAYER_COLORS[layer]
            cv2.drawContours(overlay, contours, -1, color, line_thickness)
            logger.info(f"Overlay: Drew {len(contours)} {layer.value} contours")

    # Blend with original
    result = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)

    return result


def generate_layered_overlay(
    source_image_path: str,
    target_height_mm: float = 500.0,
    output_dir: Optional[str] = None,
) -> Tuple[str, Dict]:
    """
    Generate 5-layer overlay for Phase 4 debugging.

    Runs Pass A + Pass B, builds layers, and creates colored overlay.

    Args:
        source_image_path: Path to blueprint image
        target_height_mm: Target height for scaling
        output_dir: Output directory (defaults to source directory)

    Returns:
        (overlay_path, metadata_dict)
    """
    from .annotation_extract import extract_annotations, get_annotation_contours
    from .layer_builder import build_layers
    from .blueprint_extract import _ensure_edge_to_dxf_importable

    _ensure_edge_to_dxf_importable()
    from edge_to_dxf import extract_entities_simple

    # Load image
    image = cv2.imread(source_image_path)
    if image is None:
        raise ValueError(f"Failed to load image: {source_image_path}")

    h, w = image.shape[:2]
    mm_per_px = target_height_mm / h

    # Pass A: Structural
    pass_a_entities = extract_entities_simple(
        image=image,
        target_height_mm=target_height_mm,
    )
    pass_a_contours = pass_a_entities.contours

    # Pass B: Annotation
    pass_b_result = extract_annotations(
        image=image,
        target_height_mm=target_height_mm,
    )
    pass_b_contours = get_annotation_contours(pass_b_result)

    # Build layers
    layered = build_layers(
        structural_contours=pass_a_contours,
        annotation_contours=pass_b_contours,
        image_size=(w, h),
        mm_per_px=mm_per_px,
    )

    # Create overlay
    overlay = create_layered_overlay(image, layered)

    # Generate output path
    source_path = Path(source_image_path)
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = source_path.parent

    output_path = str(out_dir / f"{source_path.stem}_layered_overlay.png")
    cv2.imwrite(output_path, overlay)

    # Build metadata
    counts = layered.counts()
    metadata = {
        "source": source_image_path,
        "overlay": output_path,
        "layer_counts": counts,
        "pass_a_raw": len(pass_a_contours),
        "pass_b_raw": len(pass_b_contours),
        "annotation_categories": pass_b_result.debug.get("categories", {}),
    }

    logger.info(
        f"Generated layered overlay: {output_path}\n"
        f"  BODY: {counts['body']}\n"
        f"  AUX_VIEWS: {counts['aux_views']}\n"
        f"  ANNOTATION: {counts['annotation']}\n"
        f"  TITLE_BLOCK: {counts['title_block']}\n"
        f"  PAGE_FRAME: {counts['page_frame']}"
    )

    return output_path, metadata
