"""
march_pipeline_restore.py — Restore March 2026 Benchmark Pipeline
==================================================================

Restores the working pipeline that produced:
  Jumbo Tiger Maple Archtop Guitar with a Florentine Cutaway_00_original_photo_v2.dxf

Key components:
1. _studio() — Corner/edge patch background model for studio gray backgrounds
2. Grid re-classification — FeatureClassifier + PhotoGridClassifier merge
3. Raw contour export — No potrace simplification, preserve OpenCV points
4. Layer assignment — BODY_OUTLINE, CONTROL_CAVITY, F_HOLE, UNKNOWN

Usage:
    from march_pipeline_restore import (
        studio_background_remove,
        classify_and_assign_layers,
        export_raw_contours_dxf,      # POLYLINE output (non-Fusion)
        export_layered_lines_dxf,     # LINE output (Fusion-compatible, Sprint 5)
        run_march_pipeline,
        NoContoursError,  # Raised when BG removal fails / no valid contours
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

from grid_classify import PhotoGridClassifier, merge_classifications

logger = logging.getLogger(__name__)


# =============================================================================
# Feature Types (matching March benchmark)
# =============================================================================

class FeatureType(Enum):
    BODY_OUTLINE = "body_outline"
    PICKUP_ROUTE = "pickup_route"
    NECK_POCKET = "neck_pocket"
    CONTROL_CAVITY = "control_cavity"
    BRIDGE_ROUTE = "bridge_route"
    F_HOLE = "f_hole"
    SOUNDHOLE = "soundhole"
    ROSETTE = "rosette"
    JACK_ROUTE = "jack_route"
    BINDING = "binding"
    PURFLING = "purfling"
    UNKNOWN = "unknown"


@dataclass
class FeatureContour:
    """Contour with classification metadata."""
    points_px: np.ndarray
    points_mm: Optional[np.ndarray] = None
    feature_type: FeatureType = FeatureType.UNKNOWN
    confidence: float = 0.0
    area_px: float = 0.0
    perimeter_px: float = 0.0
    bbox_px: Tuple[int, int, int, int] = (0, 0, 0, 0)
    grid_zone: Optional[str] = None
    grid_confidence: float = 0.0
    grid_notes: List[str] = field(default_factory=list)


# =============================================================================
# 1. Studio Background Removal (Corner/Edge Patch Model)
# =============================================================================

def studio_background_remove(
    image: np.ndarray,
    patch_size: int = 30,
    distance_threshold: float = 2.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Remove background using statistical model from corner/edge patches.

    Works well on studio gray backgrounds (uniform or smoothly graduated).

    Algorithm:
    1. Sample 8 patches: 4 corners + 4 edge midpoints
    2. Compute mean and std of those pixels in BGR space
    3. For every pixel, compute normalized distance from background mean:
       distance = sqrt(sum(((pixel - mu) / std)^2))
    4. Pixels with distance > threshold = foreground

    This is simplified Mahalanobis distance using per-channel std instead
    of full covariance matrix. Fast and effective for studio backgrounds.

    Args:
        image: BGR image
        patch_size: Size of sampling patches (default 30px)
        distance_threshold: Normalized distance threshold (default 2.0)

    Returns:
        (foreground_image, alpha_mask)
    """
    h, w = image.shape[:2]
    ps = min(patch_size, h // 6, w // 6)

    # Sample 8 patches: 4 corners + 4 edge midpoints
    patches = []

    # Corners
    patches.append(image[0:ps, 0:ps])                    # top-left
    patches.append(image[0:ps, w-ps:w])                  # top-right
    patches.append(image[h-ps:h, 0:ps])                  # bottom-left
    patches.append(image[h-ps:h, w-ps:w])                # bottom-right

    # Edge midpoints
    mid_h, mid_w = h // 2, w // 2
    patches.append(image[0:ps, mid_w-ps//2:mid_w+ps//2])           # top-center
    patches.append(image[h-ps:h, mid_w-ps//2:mid_w+ps//2])         # bottom-center
    patches.append(image[mid_h-ps//2:mid_h+ps//2, 0:ps])           # left-center
    patches.append(image[mid_h-ps//2:mid_h+ps//2, w-ps:w])         # right-center

    # Concatenate all patch pixels
    all_bg_pixels = np.vstack([p.reshape(-1, 3) for p in patches]).astype(np.float32)

    # Compute mean and std per channel
    mu = np.mean(all_bg_pixels, axis=0)  # shape (3,)
    std = np.std(all_bg_pixels, axis=0)  # shape (3,)
    std = np.maximum(std, 1.0)  # Avoid division by zero

    logger.info(f"Studio BG model: mu={mu.astype(int)}, std={std.astype(int)}")

    # Compute normalized distance for every pixel
    img_float = image.astype(np.float32)
    diff = (img_float - mu) / std  # Broadcasting: (H, W, 3)
    distance = np.sqrt(np.sum(diff ** 2, axis=2))  # (H, W)

    # Threshold to get foreground mask
    fg_mask = (distance > distance_threshold).astype(np.uint8) * 255

    # Clean up with morphology
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Apply mask
    fg = cv2.bitwise_and(image, image, mask=fg_mask)

    return fg, fg_mask


# =============================================================================
# 2. Feature Classifier (Dimension-based)
# =============================================================================

class FeatureClassifier:
    """
    Classify contours by dimension in mm.

    Matches March 2026 benchmark classification thresholds.
    """

    def classify(
        self,
        contour: np.ndarray,
        mm_per_px: float,
        bbox: Tuple[int, int, int, int],
    ) -> Tuple[FeatureType, float]:
        """
        Classify a contour by its dimensions.

        Args:
            contour: OpenCV contour
            mm_per_px: Scale factor
            bbox: (x, y, w, h) bounding box in pixels

        Returns:
            (FeatureType, confidence)
        """
        x, y, w, h = bbox
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        max_dim = max(w_mm, h_mm)
        min_dim = min(w_mm, h_mm)

        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0

        # Body outline — large contour
        if max_dim > 300 and min_dim > 200:
            return FeatureType.BODY_OUTLINE, 0.9

        # F-hole — elongated, medium size
        if 120 < max_dim < 200 and 30 < min_dim < 60:
            return FeatureType.F_HOLE, 0.8

        # Soundhole — circular, medium size
        if 80 < max_dim < 130 and 80 < min_dim < 130 and circularity > 0.7:
            return FeatureType.SOUNDHOLE, 0.85

        # Pickup route
        if 60 < max_dim < 100 and 30 < min_dim < 50:
            return FeatureType.PICKUP_ROUTE, 0.75

        # Neck pocket
        if 50 < max_dim < 90 and 40 < min_dim < 70:
            return FeatureType.NECK_POCKET, 0.8

        # Bridge route
        if 50 < max_dim < 150 and 20 < min_dim < 50:
            return FeatureType.BRIDGE_ROUTE, 0.7

        # Control cavity
        if 70 < max_dim < 150 and 40 < min_dim < 90:
            return FeatureType.CONTROL_CAVITY, 0.65

        # Jack route — small
        if 15 < max_dim < 40 and 15 < min_dim < 40:
            return FeatureType.JACK_ROUTE, 0.6

        return FeatureType.UNKNOWN, 0.3


# =============================================================================
# 3. Grid Re-Classification (Stage 8.5 from March)
# =============================================================================

class NoContoursError(Exception):
    """Raised when no valid contours are found after filtering."""
    pass


def classify_and_assign_layers(
    contours: List[np.ndarray],
    mm_per_px: float,
    min_area_px: int = 2000,  # Validated floor: filters fret markers, string shadows, hardware reflections
) -> Dict[str, List[FeatureContour]]:
    """
    Classify contours and assign to layers using dimension + grid zone logic.

    This is the March 2026 Stage 8.5 pipeline:
    1. Find body contour (largest)
    2. Classify each contour by dimension (FeatureClassifier)
    3. Re-classify by grid zone position (PhotoGridClassifier)
    4. Merge classifications (agreement boost, disagreement penalty)
    5. Return contours organized by layer name

    Args:
        contours: List of OpenCV contours
        mm_per_px: Scale factor for dimension classification
        min_area_px: Minimum contour area to include

    Returns:
        Dict mapping layer names (BODY_OUTLINE, CONTROL_CAVITY, etc.) to contours

    Raises:
        NoContoursError: If no contours pass the area threshold (BG removal likely failed)
    """
    if not contours:
        raise NoContoursError("No contours provided - background removal may have failed")

    classifier = FeatureClassifier()
    grid_clf = PhotoGridClassifier()

    # Build FeatureContour list
    feature_contours: List[FeatureContour] = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area_px:
            continue

        bbox = cv2.boundingRect(cnt)
        perimeter = cv2.arcLength(cnt, True)

        # Dimension-based classification
        feat_type, confidence = classifier.classify(cnt, mm_per_px, bbox)

        fc = FeatureContour(
            points_px=cnt,
            feature_type=feat_type,
            confidence=confidence,
            area_px=area,
            perimeter_px=perimeter,
            bbox_px=bbox,
        )
        feature_contours.append(fc)

    if not feature_contours:
        raise NoContoursError(
            f"No contours above min_area_px={min_area_px} - "
            f"background removal may have failed or image contains no valid features"
        )

    # Find body contour (largest)
    body_fc = max(feature_contours, key=lambda fc: fc.area_px)
    body_fc.feature_type = FeatureType.BODY_OUTLINE
    body_fc.confidence = 0.95
    body_fc.grid_zone = "BODY_OUTLINE"
    body_fc.grid_confidence = 1.0

    body_bbox_px = body_fc.bbox_px

    # Grid re-classification for non-body contours
    reclassified = 0
    for fc in feature_contours:
        if fc is body_fc:
            continue

        # Get grid classification
        gc = grid_clf.classify_contour_px(fc.bbox_px, body_bbox_px)
        fc.grid_zone = gc.zone
        fc.grid_notes = gc.notes

        # Merge dimension + grid classifications
        final_feat, final_conf, reason = merge_classifications(
            fc.feature_type.value, fc.confidence, gc
        )

        try:
            new_type = FeatureType(final_feat)
        except ValueError:
            new_type = fc.feature_type

        if new_type != fc.feature_type:
            logger.debug(f"Grid reclassify: {fc.feature_type.value} -> {new_type.value} ({reason})")
            fc.feature_type = new_type
            reclassified += 1

        fc.confidence = final_conf
        fc.grid_confidence = gc.grid_confidence

    logger.info(f"Grid re-classification: {reclassified}/{len(feature_contours)} changed")

    # Organize by layer
    layers: Dict[str, List[FeatureContour]] = {}
    for fc in feature_contours:
        layer_name = fc.feature_type.value.upper()
        if layer_name not in layers:
            layers[layer_name] = []
        layers[layer_name].append(fc)

    return layers


# =============================================================================
# 4. Raw Contour DXF Export (No Simplification)
# =============================================================================

def export_raw_contours_dxf(
    layers: Dict[str, List[FeatureContour]],
    output_path: Path,
    mm_per_px: float,
    image_height: int,
    dxf_version: str = "R12",
) -> bool:
    """
    Export contours to DXF preserving raw OpenCV points (no simplification).

    This matches the March 2026 benchmark which had 1020-1152 vertices per
    polyline entity instead of 38-50 simplified points.

    Args:
        layers: Dict mapping layer names to FeatureContour lists
        output_path: Output DXF file path
        mm_per_px: Scale factor for conversion to mm
        image_height: Image height for Y-flip
        dxf_version: DXF version (default R12)

    Returns:
        True if successful

    Raises:
        NoContoursError: If layers dict is empty (refuses to write empty DXF)
    """
    if not EZDXF_AVAILABLE:
        logger.error("ezdxf not available")
        return False

    if not layers:
        raise NoContoursError("Cannot export empty DXF - no layers/contours provided")

    doc = ezdxf.new(dxf_version)
    msp = doc.modelspace()

    # Layer colors
    layer_colors = {
        "BODY_OUTLINE": 7,      # White
        "CONTROL_CAVITY": 3,    # Green
        "F_HOLE": 5,            # Blue
        "PICKUP_ROUTE": 1,      # Red
        "NECK_POCKET": 4,       # Cyan
        "BRIDGE_ROUTE": 6,      # Magenta
        "SOUNDHOLE": 2,         # Yellow
        "UNKNOWN": 8,           # Gray
    }

    # Create layers
    for layer_name in layers.keys():
        color = layer_colors.get(layer_name, 7)
        doc.layers.add(layer_name, color=color)

    total_entities = 0

    for layer_name, contour_list in layers.items():
        for fc in contour_list:
            # Get raw points (no simplification)
            pts = fc.points_px
            if pts.ndim == 3:
                pts = pts.squeeze(axis=1)  # (N, 1, 2) -> (N, 2)

            if len(pts) < 3:
                continue

            # Convert to mm and flip Y
            pts_mm = pts.astype(float) * mm_per_px
            pts_mm[:, 1] = (image_height * mm_per_px) - pts_mm[:, 1]

            # Center on origin (use body center if available)
            center = np.mean(pts_mm, axis=0)
            pts_mm -= center

            # Add as POLYLINE (R12) or LWPOLYLINE (R2010+)
            if dxf_version == "R12":
                # R12: Use 2D POLYLINE
                points_3d = [(float(p[0]), float(p[1]), 0.0) for p in pts_mm]
                msp.add_polyline2d(
                    points_3d,
                    close=True,
                    dxfattribs={'layer': layer_name}
                )
            else:
                # R2010+: Use LWPOLYLINE
                points_2d = [(float(p[0]), float(p[1])) for p in pts_mm]
                msp.add_lwpolyline(
                    points_2d,
                    close=True,
                    dxfattribs={'layer': layer_name}
                )

            total_entities += 1
            logger.debug(f"Layer {layer_name}: {len(pts)} vertices")

    doc.saveas(str(output_path))
    logger.info(f"DXF saved: {output_path} ({total_entities} entities)")

    return True


def export_layered_lines_dxf(
    layers: Dict[str, List[FeatureContour]],
    output_path: Path,
    mm_per_px: float,
    image_height: int,
) -> Dict[str, int]:
    """
    Export contours to R12 DXF using LINE entities (Fusion 360 compatible).

    This is the production-standard export matching CLAUDE.md:
    - Format: R12 (AC1009)
    - Entities: LINE only (no POLYLINE, no LWPOLYLINE)
    - Named layers: BODY_OUTLINE, CAVITY, etc.

    Args:
        layers: Dict mapping layer names to FeatureContour lists
        output_path: Output DXF file path
        mm_per_px: Scale factor for conversion to mm
        image_height: Image height for Y-flip

    Returns:
        Dict with LINE counts per layer

    Raises:
        NoContoursError: If layers dict is empty
    """
    if not EZDXF_AVAILABLE:
        raise ImportError("ezdxf not available")

    if not layers:
        raise NoContoursError("Cannot export empty DXF - no layers/contours provided")

    doc = ezdxf.new("R12")
    msp = doc.modelspace()

    # Layer colors (ACI)
    layer_colors = {
        "BODY_OUTLINE": 7,      # White
        "CAVITY": 3,            # Green
        "CONTROL_CAVITY": 3,    # Green
        "F_HOLE": 5,            # Blue
        "PICKUP_ROUTE": 1,      # Red
        "NECK_POCKET": 4,       # Cyan
        "BRIDGE_ROUTE": 6,      # Magenta
        "SOUNDHOLE": 2,         # Yellow
        "UNKNOWN": 8,           # Gray
    }

    # Create layers
    for layer_name in layers.keys():
        color = layer_colors.get(layer_name, 7)
        doc.layers.add(layer_name, color=color)

    counts: Dict[str, int] = {}
    image_height_mm = image_height * mm_per_px

    for layer_name, contour_list in layers.items():
        layer_line_count = 0

        for fc in contour_list:
            pts = fc.points_px
            if pts.ndim == 3:
                pts = pts.squeeze(axis=1)

            if len(pts) < 2:
                continue

            # Convert to mm and flip Y
            pts_mm = pts.astype(float) * mm_per_px
            pts_mm[:, 1] = image_height_mm - pts_mm[:, 1]

            # Write as LINE entities (consecutive point pairs)
            for i in range(len(pts_mm) - 1):
                p1 = pts_mm[i]
                p2 = pts_mm[i + 1]
                msp.add_line(
                    (float(p1[0]), float(p1[1]), 0.0),
                    (float(p2[0]), float(p2[1]), 0.0),
                    dxfattribs={'layer': layer_name}
                )
                layer_line_count += 1

            # Close the contour
            if len(pts_mm) > 2:
                p1 = pts_mm[-1]
                p2 = pts_mm[0]
                msp.add_line(
                    (float(p1[0]), float(p1[1]), 0.0),
                    (float(p2[0]), float(p2[1]), 0.0),
                    dxfattribs={'layer': layer_name}
                )
                layer_line_count += 1

        counts[layer_name] = layer_line_count

    doc.saveas(str(output_path))

    total = sum(counts.values())
    logger.info(f"Layered LINE DXF saved: {output_path} ({total} LINEs)")
    for layer_name, count in counts.items():
        logger.info(f"  {layer_name}: {count}")

    return counts


# =============================================================================
# 5. Full Pipeline (Matching March Benchmark)
# =============================================================================

def run_march_pipeline(
    image_path: str,
    output_dir: str,
    mm_per_px: float = 0.5,  # Default scale, override with known dimension
    bg_method: str = "studio",  # "studio", "rembg", "threshold"
    min_area_px: int = 1000,
    debug_images: bool = True,
) -> Dict:
    """
    Run the full March 2026 benchmark pipeline.

    Stages:
    1. Load image
    2. Background removal (studio model or rembg)
    3. Edge detection (Canny)
    4. Contour extraction
    5. Feature classification + grid re-classification
    6. Raw contour DXF export

    Args:
        image_path: Input image path
        output_dir: Output directory
        mm_per_px: Scale factor (mm per pixel)
        bg_method: Background removal method
        min_area_px: Minimum contour area
        debug_images: Save debug images

    Returns:
        Dict with results and file paths
    """
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load: {image_path}")

    h, w = image.shape[:2]
    logger.info(f"Image: {w}x{h}")

    # Stage 1: Background removal
    if bg_method == "studio":
        fg, alpha_mask = studio_background_remove(image)
        bg_used = "studio"
    elif bg_method == "rembg":
        try:
            from rembg import remove as rembg_remove
            from PIL import Image as PILImage
            import io
            pil_img = PILImage.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            buf = io.BytesIO()
            pil_img.save(buf, format='PNG')
            buf.seek(0)
            result_bytes = rembg_remove(buf.read())
            result_pil = PILImage.open(io.BytesIO(result_bytes)).convert('RGBA')
            result_np = np.array(result_pil)
            alpha_mask = (result_np[:, :, 3] > 128).astype(np.uint8) * 255
            fg = cv2.bitwise_and(image, image, mask=alpha_mask)
            bg_used = "rembg"
        except ImportError:
            logger.warning("rembg not available, falling back to studio")
            fg, alpha_mask = studio_background_remove(image)
            bg_used = "studio_fallback"
    else:
        # Threshold
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, alpha_mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        fg = cv2.bitwise_and(image, image, mask=alpha_mask)
        bg_used = "threshold"

    if debug_images:
        cv2.imwrite(str(output_dir / f"{image_path.stem}_01_foreground.jpg"), fg)
        cv2.imwrite(str(output_dir / f"{image_path.stem}_02_alpha.png"), alpha_mask)

    # Stage 2: Edge detection
    gray_fg = cv2.cvtColor(fg, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_fg, 50, 150)

    # Dilate edges slightly to connect gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=1)

    if debug_images:
        cv2.imwrite(str(output_dir / f"{image_path.stem}_03_edges.png"), edges)

    # Stage 3: Contour extraction
    contours, hierarchy = cv2.findContours(
        alpha_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE  # APPROX_NONE = keep all points
    )

    logger.info(f"Found {len(contours)} contours")

    # Stage 4: Classification + grid re-classification
    layers = classify_and_assign_layers(contours, mm_per_px, min_area_px)

    # Count entities per layer
    layer_counts = {name: len(fcs) for name, fcs in layers.items()}
    logger.info(f"Layers: {layer_counts}")

    # Debug: Grid overlay
    if debug_images and layers:
        debug_img = image.copy()
        grid_clf = PhotoGridClassifier()

        # Find body bbox
        body_contours = layers.get("BODY_OUTLINE", [])
        if body_contours:
            body_fc = body_contours[0]
            bx, by, bw, bh = body_fc.bbox_px

            # Draw body bbox
            cv2.rectangle(debug_img, (bx, by), (bx+bw, by+bh), (0, 255, 0), 2)

            # Draw grid
            for i in range(1, 3):
                gx = int(bx + bw * i / 3)
                gy = int(by + bh * i / 3)
                cv2.line(debug_img, (gx, by), (gx, by+bh), (0, 255, 0), 1)
                cv2.line(debug_img, (bx, gy), (bx+bw, gy), (0, 255, 0), 1)

            # Draw all contours with layer colors
            colors = {
                "BODY_OUTLINE": (255, 255, 255),
                "CONTROL_CAVITY": (0, 255, 0),
                "F_HOLE": (255, 0, 0),
                "UNKNOWN": (128, 128, 128),
            }
            for layer_name, fcs in layers.items():
                color = colors.get(layer_name, (200, 200, 200))
                for fc in fcs:
                    cv2.drawContours(debug_img, [fc.points_px], -1, color, 2)

        cv2.imwrite(str(output_dir / f"{image_path.stem}_04_grid_overlay.jpg"), debug_img)

    # Stage 5: Export DXF
    dxf_path = output_dir / f"{image_path.stem}_march_v2.dxf"
    export_raw_contours_dxf(layers, dxf_path, mm_per_px, h, dxf_version="R12")

    # Calculate body dimensions
    body_dims_mm = (0.0, 0.0)
    if "BODY_OUTLINE" in layers and layers["BODY_OUTLINE"]:
        body_fc = layers["BODY_OUTLINE"][0]
        bx, by, bw, bh = body_fc.bbox_px
        body_dims_mm = (bw * mm_per_px, bh * mm_per_px)

    result = {
        "source": str(image_path),
        "dxf_path": str(dxf_path),
        "bg_method": bg_used,
        "layer_counts": layer_counts,
        "body_dimensions_mm": body_dims_mm,
        "mm_per_px": mm_per_px,
        "total_contours": sum(layer_counts.values()),
    }

    return result


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python march_pipeline_restore.py <image> [output_dir] [mm_per_px]")
        print("\nExample:")
        print("  python march_pipeline_restore.py guitar.jpg ./output 0.5")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./march_output"
    mm_per_px = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5

    result = run_march_pipeline(
        image_path=image_path,
        output_dir=output_dir,
        mm_per_px=mm_per_px,
        bg_method="studio",
        debug_images=True,
    )

    print("\nResult:")
    for k, v in result.items():
        print(f"  {k}: {v}")
