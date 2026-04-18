"""
Light Line Body Extractor

Specialized contour extraction for blueprint PDFs where body outlines
are drawn with very light gray lines that standard edge detection misses.

Technique:
1. Invert the image (dark becomes light)
2. Enhance contrast by 3x to amplify subtle gray lines
3. Use low Canny thresholds (15, 45) to catch faint edges
4. Apply morphological closing to connect broken line segments
5. Filter by expected body dimensions

Developed for Carlos Jumbo blueprint extraction, April 2026.
See BLUEPRINT_CALIBRATION_METHODOLOGY.md for full methodology.
"""
from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class BodyContour:
    """Extracted body outline with metadata."""
    points: np.ndarray
    width_mm: float
    height_mm: float
    aspect_ratio: float
    area_px: float
    centroid_x: float
    centroid_y: float
    mm_per_px: float
    source_region: str = "full"

    def to_mm_coordinates(self) -> np.ndarray:
        """Convert pixel coordinates to mm."""
        return self.points.astype(float) * self.mm_per_px

    def get_bbox_mm(self) -> Tuple[float, float, float, float]:
        """Return (x, y, width, height) in mm."""
        pts_mm = self.to_mm_coordinates()
        x_min, y_min = pts_mm.min(axis=0)
        x_max, y_max = pts_mm.max(axis=0)
        return (x_min, y_min, x_max - x_min, y_max - y_min)


def detect_image_polarity(gray: np.ndarray) -> str:
    """
    Detect if image has dark lines on light background or vice versa.

    Returns:
        "light_bg" — standard blueprint (dark lines on white/light background)
        "dark_bg" — inverted/negative (white/light lines on black/dark background)
    """
    mean_intensity = gray.mean()
    # Threshold at midpoint: >127 means mostly light pixels (light background)
    if mean_intensity > 127:
        return "light_bg"
    else:
        return "dark_bg"


@dataclass
class ExtractionConfig:
    """Configuration for light line extraction."""
    # Image preprocessing
    dpi: int = 200
    contrast_multiplier: float = 3.0
    invert: str = "auto"  # "auto", "always", "never"

    # Edge detection
    canny_low: int = 15
    canny_high: int = 45

    # Morphological operations
    morph_kernel_size: int = 5
    morph_iterations: int = 3
    dilate_iterations: int = 1

    # Region cropping (as fraction of image width/height)
    crop_left: float = 0.0
    crop_right: float = 1.0
    crop_top: float = 0.0
    crop_bottom: float = 1.0

    # Body dimension filters (mm)
    min_width_mm: float = 300.0
    max_width_mm: float = 700.0
    min_height_mm: float = 350.0
    max_height_mm: float = 750.0
    min_area_px: float = 100000.0

    # Contour simplification
    simplify_epsilon_factor: float = 0.001


@dataclass
class ExtractionResult:
    """Result of body extraction."""
    success: bool
    body: Optional[BodyContour] = None
    all_candidates: List[BodyContour] = field(default_factory=list)
    debug_images: Dict[str, np.ndarray] = field(default_factory=dict)
    error_message: str = ""
    page_size_mm: Tuple[float, float] = (0.0, 0.0)


def extract_body_from_image(
    image: np.ndarray,
    mm_per_px: float,
    config: Optional[ExtractionConfig] = None,
    save_debug: bool = False,
) -> ExtractionResult:
    """
    Extract guitar body outline from an image using light line detection.

    Args:
        image: BGR image array
        mm_per_px: Scale factor (millimeters per pixel)
        config: Extraction configuration (uses defaults if None)
        save_debug: If True, includes debug images in result

    Returns:
        ExtractionResult with body contour and metadata
    """
    if config is None:
        config = ExtractionConfig()

    result = ExtractionResult(success=False)
    debug_images = {}

    h, w = image.shape[:2]
    result.page_size_mm = (w * mm_per_px, h * mm_per_px)

    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Detect polarity BEFORE cropping to determine image type
    if config.invert == "auto":
        polarity = detect_image_polarity(gray)
        should_invert = (polarity == "light_bg")
        logger.info(f"Polarity detection: {polarity}, invert={should_invert}")
    elif config.invert == "always":
        polarity = "light_bg"
        should_invert = True
    else:  # "never"
        polarity = "dark_bg"
        should_invert = False

    # Crop to region of interest
    # For dark backgrounds (inverted/negative blueprints), skip left crop
    # since these are typically single-view centered images
    if polarity == "dark_bg" and config.crop_left > 0:
        logger.info(f"Dark background detected, skipping crop_left={config.crop_left}")
        x1 = 0
    else:
        x1 = int(w * config.crop_left)
    x2 = int(w * config.crop_right)
    y1 = int(h * config.crop_top)
    y2 = int(h * config.crop_bottom)

    # For dark backgrounds, relax dimension filters
    # These images often show full instruments (body + neck), not just body
    if polarity == "dark_bg":
        config.max_width_mm = max(config.max_width_mm, 900.0)
        config.max_height_mm = max(config.max_height_mm, 1200.0)
        config.min_area_px = min(config.min_area_px, 50000.0)
        logger.info(f"Dark background: relaxed filters to max_w={config.max_width_mm}, max_h={config.max_height_mm}")

    cropped = gray[y1:y2, x1:x2]
    crop_h, crop_w = cropped.shape

    if save_debug:
        debug_images['01_cropped'] = cropped.copy()

    # Invert image (light lines become dark)
    if should_invert:
        inverted = 255 - cropped
    else:
        inverted = cropped

    if save_debug:
        debug_images['02_inverted'] = inverted.copy()

    # For dark backgrounds, use thresholding instead of edge detection
    # This avoids the double-edge problem from Canny on white lines
    if polarity == "dark_bg":
        # Threshold to extract white/bright lines directly
        _, binary = cv2.threshold(inverted, 100, 255, cv2.THRESH_BINARY)
        edges = binary
        logger.info("Dark background: using threshold instead of Canny")
        if save_debug:
            debug_images['03_threshold'] = binary.copy()
    else:
        # Standard light background: enhance contrast then Canny
        enhanced = np.clip(
            inverted.astype(float) * config.contrast_multiplier,
            0, 255
        ).astype(np.uint8)

        if save_debug:
            debug_images['03_enhanced'] = enhanced.copy()

        edges = cv2.Canny(enhanced, config.canny_low, config.canny_high)

    if save_debug:
        debug_images['04_edges'] = edges.copy()

    # Morphological closing to connect broken lines
    kernel = np.ones(
        (config.morph_kernel_size, config.morph_kernel_size),
        np.uint8
    )
    closed = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=config.morph_iterations
    )

    if save_debug:
        debug_images['05_closed'] = closed.copy()

    # Dilate to thicken lines
    if config.dilate_iterations > 0:
        dilated = cv2.dilate(closed, kernel, iterations=config.dilate_iterations)
    else:
        dilated = closed

    if save_debug:
        debug_images['06_dilated'] = dilated.copy()

    # Find contours
    contours, hierarchy = cv2.findContours(
        dilated,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        result.error_message = "No contours found"
        result.debug_images = debug_images if save_debug else {}
        return result

    # Filter for body-sized contours
    candidates = []
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < config.min_area_px:
            continue

        x, y, cw, ch = cv2.boundingRect(cnt)
        width_mm = cw * mm_per_px
        height_mm = ch * mm_per_px

        if not (config.min_width_mm < width_mm < config.max_width_mm):
            continue
        if not (config.min_height_mm < height_mm < config.max_height_mm):
            continue

        # Calculate centroid
        M = cv2.moments(cnt)
        if M['m00'] > 0:
            cx = M['m10'] / M['m00'] + x1  # Adjust for crop offset
            cy = M['m01'] / M['m00'] + y1
        else:
            cx = x + cw/2 + x1
            cy = y + ch/2 + y1

        # Simplify contour
        epsilon = config.simplify_epsilon_factor * cv2.arcLength(cnt, True)
        simplified = cv2.approxPolyDP(cnt, epsilon, True)

        # Adjust coordinates for crop offset
        adjusted_points = simplified.reshape(-1, 2).copy()
        adjusted_points[:, 0] += x1
        adjusted_points[:, 1] += y1

        body = BodyContour(
            points=adjusted_points,
            width_mm=width_mm,
            height_mm=height_mm,
            aspect_ratio=width_mm / height_mm if height_mm > 0 else 0,
            area_px=area,
            centroid_x=cx,
            centroid_y=cy,
            mm_per_px=mm_per_px,
            source_region=f"crop_{config.crop_left:.2f}-{config.crop_right:.2f}",
        )
        candidates.append(body)

    if not candidates:
        result.error_message = "No body-sized contours found"
        result.debug_images = debug_images if save_debug else {}
        return result

    # Select best candidate (largest area)
    candidates.sort(key=lambda x: x.area_px, reverse=True)
    best = candidates[0]

    result.success = True
    result.body = best
    result.all_candidates = candidates

    if save_debug:
        # Create visualization
        vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # Draw all candidates in blue
        for cand in candidates[1:]:
            pts = cand.points.reshape(-1, 1, 2).astype(np.int32)
            cv2.drawContours(vis, [pts], -1, (255, 128, 0), 1)

        # Draw best in green
        pts = best.points.reshape(-1, 1, 2).astype(np.int32)
        cv2.drawContours(vis, [pts], -1, (0, 255, 0), 2)

        # Draw bounding box in red
        x, y, bw, bh = cv2.boundingRect(pts)
        cv2.rectangle(vis, (x, y), (x + bw, y + bh), (0, 0, 255), 2)

        # Add dimension labels
        cv2.putText(
            vis,
            f"{best.width_mm:.1f} x {best.height_mm:.1f} mm",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        debug_images['07_result'] = vis
        result.debug_images = debug_images

    return result


def extract_body_from_pdf(
    pdf_path: Path,
    page_number: int = 0,
    page_size_mm: Tuple[float, float] = (841.0, 1189.0),  # A0 default
    config: Optional[ExtractionConfig] = None,
    save_debug: bool = False,
) -> ExtractionResult:
    """
    Extract guitar body outline from a PDF page.

    Args:
        pdf_path: Path to PDF file
        page_number: 0-indexed page number
        page_size_mm: Expected page size in mm (width, height)
        config: Extraction configuration
        save_debug: If True, includes debug images in result

    Returns:
        ExtractionResult with body contour and metadata
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return ExtractionResult(
            success=False,
            error_message="PyMuPDF (fitz) not installed"
        )

    if config is None:
        config = ExtractionConfig()

    try:
        doc = fitz.open(str(pdf_path))
        if page_number >= len(doc):
            doc.close()
            return ExtractionResult(
                success=False,
                error_message=f"Page {page_number} not found (PDF has {len(doc)} pages)"
            )

        page = doc[page_number]

        # Render at configured DPI
        mat = fitz.Matrix(config.dpi / 72, config.dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        # Convert to numpy array
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )

        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        doc.close()

        # Calculate scale from page size
        h, w = img.shape[:2]
        mm_per_px = page_size_mm[1] / h  # Use height for scale (A0 is 1189mm tall)

        return extract_body_from_image(
            img,
            mm_per_px,
            config=config,
            save_debug=save_debug
        )

    except Exception as e:
        return ExtractionResult(
            success=False,
            error_message=f"PDF extraction failed: {str(e)}"
        )


def create_acoustic_body_config(gap_closing_level: str = "normal") -> ExtractionConfig:
    """
    Create optimized config for acoustic guitar body extraction.

    Tuned for blueprints where:
    - Body outline is drawn with light gray lines
    - Full front view is on the right side of a multi-view page
    - Expected jumbo body: 420-480mm wide, 510-550mm tall

    Args:
        gap_closing_level: "normal" (default), "aggressive", or "extreme"
            - normal: 5x5 kernel, 3 iterations (~2mm gap bridging at 200 DPI)
            - aggressive: 9x9 kernel, 5 iterations (~6mm gap bridging)
            - extreme: 15x15 kernel, 7 iterations (~12mm gap bridging)
    """
    # Base configuration
    config = ExtractionConfig(
        dpi=200,
        contrast_multiplier=3.0,
        invert="auto",  # Auto-detect polarity (light bg vs dark bg)
        canny_low=15,
        canny_high=45,
        morph_kernel_size=5,
        morph_iterations=3,
        dilate_iterations=1,
        # Crop to right portion (body view) avoiding side profiles
        crop_left=0.35,
        crop_right=1.0,
        crop_top=0.0,
        crop_bottom=1.0,
        # Jumbo body dimensions
        min_width_mm=300.0,
        max_width_mm=700.0,
        min_height_mm=350.0,
        max_height_mm=750.0,
        min_area_px=100000.0,
        simplify_epsilon_factor=0.001,
    )

    # Override morphological parameters based on gap closing level
    if gap_closing_level == "aggressive":
        # For documents with medium gaps (~3-6mm)
        config.morph_kernel_size = 9
        config.morph_iterations = 5
        config.dilate_iterations = 2
        config.canny_low = 10  # Lower threshold to catch more edges
        config.canny_high = 40
        config.contrast_multiplier = 4.0  # Higher contrast
    elif gap_closing_level == "extreme":
        # For heavily fragmented documents (~6-12mm gaps)
        config.morph_kernel_size = 15
        config.morph_iterations = 7
        config.dilate_iterations = 3
        config.canny_low = 8
        config.canny_high = 35
        config.contrast_multiplier = 5.0
        config.min_area_px = 50000.0  # Lower threshold due to potential fragmentation

    return config


def save_contour_to_dxf(
    body: BodyContour,
    output_path: Path,
    scale_to_dimensions: Optional[Tuple[float, float]] = None,
    layer_name: str = "BODY_OUTLINE",
) -> None:
    """
    Save extracted body contour to DXF file.

    Args:
        body: Extracted body contour
        output_path: Path for output DXF file
        scale_to_dimensions: If provided, scale to (width_mm, height_mm)
        layer_name: DXF layer name
    """
    try:
        import ezdxf
    except ImportError:
        raise ImportError("ezdxf not installed")

    # Convert to mm coordinates
    pts_mm = body.to_mm_coordinates()

    # Optionally scale to target dimensions
    if scale_to_dimensions:
        target_w, target_h = scale_to_dimensions
        current_w = pts_mm[:, 0].max() - pts_mm[:, 0].min()
        current_h = pts_mm[:, 1].max() - pts_mm[:, 1].min()

        scale_x = target_w / current_w if current_w > 0 else 1.0
        scale_y = target_h / current_h if current_h > 0 else 1.0

        # Center and scale
        cx = pts_mm[:, 0].mean()
        cy = pts_mm[:, 1].mean()
        pts_mm[:, 0] = (pts_mm[:, 0] - cx) * scale_x
        pts_mm[:, 1] = (pts_mm[:, 1] - cy) * scale_y

    # Create DXF
    doc = ezdxf.new('R12')
    doc.units = ezdxf.units.MM

    msp = doc.modelspace()

    # Add layer
    doc.layers.add(layer_name, color=7)

    # Create closed polyline
    points_3d = [(p[0], p[1], 0.0) for p in pts_mm]
    points_3d.append(points_3d[0])  # Close the loop

    msp.add_lwpolyline(
        points_3d,
        dxfattribs={'layer': layer_name}
    )

    doc.saveas(str(output_path))
    logger.info(f"Saved body contour to {output_path}")


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract guitar body outline from blueprint PDF"
    )
    parser.add_argument("pdf_path", type=Path, help="Input PDF file")
    parser.add_argument("--page", type=int, default=0, help="Page number (0-indexed)")
    parser.add_argument("--output", type=Path, help="Output DXF file")
    parser.add_argument("--debug", action="store_true", help="Save debug images")
    parser.add_argument(
        "--page-size",
        type=str,
        default="A0",
        help="Page size: A0, A1, A2, or WxH in mm"
    )
    parser.add_argument(
        "--target-width",
        type=float,
        help="Scale output to this width (mm)"
    )
    parser.add_argument(
        "--target-height",
        type=float,
        help="Scale output to this height (mm)"
    )

    args = parser.parse_args()

    # Parse page size
    PAGE_SIZES = {
        'A0': (841.0, 1189.0),
        'A1': (594.0, 841.0),
        'A2': (420.0, 594.0),
        'A3': (297.0, 420.0),
    }

    if args.page_size.upper() in PAGE_SIZES:
        page_size_mm = PAGE_SIZES[args.page_size.upper()]
    else:
        try:
            w, h = args.page_size.split('x')
            page_size_mm = (float(w), float(h))
        except:
            print(f"Invalid page size: {args.page_size}")
            exit(1)

    # Extract
    config = create_acoustic_body_config()
    result = extract_body_from_pdf(
        args.pdf_path,
        page_number=args.page,
        page_size_mm=page_size_mm,
        config=config,
        save_debug=args.debug,
    )

    if not result.success:
        print(f"Extraction failed: {result.error_message}")
        exit(1)

    body = result.body
    print(f"Extracted body outline:")
    print(f"  Dimensions: {body.width_mm:.1f} x {body.height_mm:.1f} mm")
    print(f"  Aspect ratio: {body.aspect_ratio:.3f}")
    print(f"  Points: {len(body.points)}")

    # Save debug images
    if args.debug and result.debug_images:
        debug_dir = args.pdf_path.parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        for name, img in result.debug_images.items():
            cv2.imwrite(str(debug_dir / f"{name}.png"), img)
        print(f"Debug images saved to {debug_dir}")

    # Save DXF
    if args.output:
        scale_dims = None
        if args.target_width and args.target_height:
            scale_dims = (args.target_width, args.target_height)

        save_contour_to_dxf(body, args.output, scale_to_dimensions=scale_dims)
        print(f"Saved DXF to {args.output}")
