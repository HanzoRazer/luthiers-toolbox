"""
Blueprint View Segmenter
========================

Detects and segments multiple views within a single blueprint image.

Problem: Traditional blueprints pack multiple views (front, side, back,
cross-sections) onto a single page. Edge detection finds 600+ fragmented
contours that cross view boundaries, making body extraction fail.

Solution: Segment the image into rectangular view regions BEFORE running
contour extraction. Each view is processed independently, then results
are merged with view-aware coordinate transforms.

View Detection Methods:
1. Thick line detection (view dividers)
2. Whitespace gap analysis (empty columns/rows)
3. Label detection (text like "FRONT", "SIDE", "TOP")
4. Contour clustering (group nearby contours into regions)

Usage:
    from blueprint_view_segmenter import BlueprintViewSegmenter

    segmenter = BlueprintViewSegmenter()
    views = segmenter.segment("multi_view_blueprint.png")

    for view in views:
        print(f"{view.label}: {view.bbox}")
        # Process view.image independently

Author: The Production Shop
Date: 2026-04-01
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ViewType(Enum):
    """Blueprint view types."""
    FRONT = "front"
    BACK = "back"
    SIDE = "side"
    TOP = "top"
    CROSS_SECTION = "cross_section"
    DETAIL = "detail"
    UNKNOWN = "unknown"


@dataclass
class DetectedView:
    """A detected view region within a blueprint."""
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    image: Optional[np.ndarray] = None
    label: str = "unknown"
    view_type: ViewType = ViewType.UNKNOWN
    confidence: float = 0.5
    contour_count: int = 0
    area_ratio: float = 0.0  # Ratio of view area to full image area

    @property
    def x(self) -> int:
        return self.bbox[0]

    @property
    def y(self) -> int:
        return self.bbox[1]

    @property
    def width(self) -> int:
        return self.bbox[2]

    @property
    def height(self) -> int:
        return self.bbox[3]

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


@dataclass
class SegmentationResult:
    """Result of blueprint view segmentation."""
    views: List[DetectedView] = field(default_factory=list)
    original_size: Tuple[int, int] = (0, 0)  # (width, height)
    is_multi_view: bool = False
    divider_lines: List[Tuple[int, int, int, int]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def view_count(self) -> int:
        return len(self.views)

    def get_largest_view(self) -> Optional[DetectedView]:
        """Return the view with the largest area."""
        if not self.views:
            return None
        return max(self.views, key=lambda v: v.width * v.height)


# =============================================================================
# Page Border Detection
# =============================================================================

def is_page_border_contour(
    contour: np.ndarray,
    image_shape: Tuple[int, int],
    margin: int = 10,
    edge_contact_threshold: float = 0.15,
) -> bool:
    """
    Detect if a contour is likely a page border rather than a body outline.

    Page borders exhibit these characteristics:
    - Touch multiple image edges
    - Cover a large fraction of the image
    - Have points clustered near edges

    Args:
        contour: Contour points as numpy array
        image_shape: (height, width) of the image
        margin: Pixel margin from edge to consider "touching"
        edge_contact_threshold: Fraction of points touching edge to trigger

    Returns:
        True if contour appears to be a page border
    """
    h, w = image_shape[:2]
    pts = contour.reshape(-1, 2)

    if len(pts) < 4:
        return False

    x, y = pts[:, 0], pts[:, 1]

    # Count points near each edge
    near_left = np.sum(x <= margin)
    near_right = np.sum(x >= w - margin)
    near_top = np.sum(y <= margin)
    near_bottom = np.sum(y >= h - margin)

    total_pts = len(pts)
    edge_contact_ratio = (near_left + near_right + near_top + near_bottom) / (4 * total_pts)

    # Check how many edges are touched
    edges_touched = sum([
        near_left > margin,
        near_right > margin,
        near_top > margin,
        near_bottom > margin,
    ])

    # Check bounding box coverage
    cx, cy, cw, ch = cv2.boundingRect(contour)
    area_ratio = (cw * ch) / (w * h)

    # Page border indicators:
    # 1. Touches 3+ edges
    # 2. OR covers >70% of image area
    # 3. OR high edge contact ratio
    if edges_touched >= 3:
        logger.debug(f"Border detected: touches {edges_touched} edges")
        return True

    if area_ratio > 0.70:
        logger.debug(f"Border detected: area ratio {area_ratio:.2%}")
        return True

    if edge_contact_ratio > edge_contact_threshold:
        logger.debug(f"Border detected: edge contact {edge_contact_ratio:.2%}")
        return True

    return False


def edge_contact_penalty(
    contour: np.ndarray,
    image_shape: Tuple[int, int],
    margin: int = 5,
) -> float:
    """
    Calculate penalty score for contours touching image edges.

    Returns:
        Penalty in range [0, 1], where 1 = maximum penalty (page border)
    """
    h, w = image_shape[:2]
    pts = contour.reshape(-1, 2)

    if len(pts) < 4:
        return 0.0

    x, y = pts[:, 0], pts[:, 1]

    # Fraction of points near each edge
    frac_left = np.mean(x <= margin)
    frac_right = np.mean(x >= w - margin)
    frac_top = np.mean(y <= margin)
    frac_bottom = np.mean(y >= h - margin)

    # Total edge contact
    total_edge_contact = frac_left + frac_right + frac_top + frac_bottom

    # Penalty increases with edge contact
    # Max theoretical contact = 4 (touches all edges completely)
    penalty = min(1.0, total_edge_contact / 2.0)

    return penalty


# =============================================================================
# Contour Quality Filters
# =============================================================================

def filter_border_contours(
    contours: List[np.ndarray],
    image_shape: Tuple[int, int],
    margin: int = 10,
) -> List[np.ndarray]:
    """
    Filter out contours that are likely page borders.

    Args:
        contours: List of contours
        image_shape: (height, width) of source image
        margin: Pixel margin for border detection

    Returns:
        Filtered list of contours (page borders removed)
    """
    filtered = []
    removed_count = 0

    for cnt in contours:
        if is_page_border_contour(cnt, image_shape, margin=margin):
            removed_count += 1
            continue
        filtered.append(cnt)

    if removed_count > 0:
        logger.info(f"Removed {removed_count} page border contours")

    return filtered


def reject_oversized_contours(
    contours: List[np.ndarray],
    image_shape: Tuple[int, int],
    max_area_ratio: float = 0.70,
) -> List[np.ndarray]:
    """
    Reject contours that cover too much of the image area.

    Real body contours typically cover 15-50% of a well-framed image.
    Contours covering >70% are usually borders or background.
    """
    h, w = image_shape[:2]
    image_area = w * h

    filtered = []
    for cnt in contours:
        cnt_area = cv2.contourArea(cnt)
        area_ratio = cnt_area / image_area

        if area_ratio > max_area_ratio:
            logger.debug(f"Rejected oversized contour: {area_ratio:.1%} of image")
            continue

        filtered.append(cnt)

    return filtered


# =============================================================================
# View Segmentation
# =============================================================================

class BlueprintViewSegmenter:
    """
    Segments a multi-view blueprint into individual view regions.

    Uses multiple detection strategies:
    1. Thick horizontal/vertical lines as dividers
    2. Large whitespace gaps
    3. Text label detection (optional, requires OCR)
    4. Contour clustering by spatial proximity
    """

    def __init__(
        self,
        min_view_area_ratio: float = 0.05,
        max_views: int = 8,
        line_thickness_threshold: int = 3,
        whitespace_threshold: float = 0.90,
    ):
        """
        Initialize segmenter.

        Args:
            min_view_area_ratio: Minimum view area as fraction of image
            max_views: Maximum number of views to detect
            line_thickness_threshold: Minimum line thickness for dividers
            whitespace_threshold: Fraction of white pixels to detect gap
        """
        self.min_view_area_ratio = min_view_area_ratio
        self.max_views = max_views
        self.line_thickness_threshold = line_thickness_threshold
        self.whitespace_threshold = whitespace_threshold

    def segment(
        self,
        image_path: Union[str, Path],
        method: str = "auto",
    ) -> SegmentationResult:
        """
        Segment blueprint into individual views.

        Args:
            image_path: Path to blueprint image
            method: Detection method ("lines", "whitespace", "contours", "auto")

        Returns:
            SegmentationResult with detected views
        """
        result = SegmentationResult()

        # Load image
        image_path = Path(image_path)
        if not image_path.exists():
            result.warnings.append(f"File not found: {image_path}")
            return result

        image = cv2.imread(str(image_path))
        if image is None:
            result.warnings.append(f"Failed to load image: {image_path}")
            return result

        h, w = image.shape[:2]
        result.original_size = (w, h)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Choose detection method
        if method == "auto":
            views = self._auto_detect(image, gray)
        elif method == "lines":
            views = self._detect_by_lines(image, gray)
        elif method == "whitespace":
            views = self._detect_by_whitespace(image, gray)
        elif method == "contours":
            views = self._detect_by_contours(image, gray)
        else:
            result.warnings.append(f"Unknown method: {method}")
            views = []

        # Filter small views
        min_area = w * h * self.min_view_area_ratio
        views = [v for v in views if v.width * v.height >= min_area]

        # Limit view count
        if len(views) > self.max_views:
            views = sorted(views, key=lambda v: v.width * v.height, reverse=True)
            views = views[:self.max_views]
            result.warnings.append(f"Truncated to {self.max_views} largest views")

        # Extract view images
        for view in views:
            x, y, vw, vh = view.bbox
            view.image = image[y:y+vh, x:x+vw].copy()
            view.area_ratio = (vw * vh) / (w * h)

        result.views = views
        result.is_multi_view = len(views) > 1

        logger.info(f"Detected {len(views)} views (multi-view: {result.is_multi_view})")

        return result

    def _auto_detect(
        self,
        image: np.ndarray,
        gray: np.ndarray,
    ) -> List[DetectedView]:
        """
        Auto-detect views using multiple strategies.

        Priority:
        1. Try line detection (most reliable for technical drawings)
        2. Fall back to whitespace detection
        3. Fall back to contour clustering
        """
        # Try line detection first
        views = self._detect_by_lines(image, gray)
        if len(views) > 1:
            logger.info("Auto-detect: using line-based segmentation")
            return views

        # Try whitespace detection
        views = self._detect_by_whitespace(image, gray)
        if len(views) > 1:
            logger.info("Auto-detect: using whitespace-based segmentation")
            return views

        # Fall back to contour clustering
        views = self._detect_by_contours(image, gray)
        if len(views) > 1:
            logger.info("Auto-detect: using contour-based segmentation")
            return views

        # Single view - return full image
        logger.info("Auto-detect: single view detected")
        h, w = image.shape[:2]
        return [DetectedView(
            bbox=(0, 0, w, h),
            label="full_image",
            view_type=ViewType.UNKNOWN,
            confidence=1.0,
        )]

    def _detect_by_lines(
        self,
        image: np.ndarray,
        gray: np.ndarray,
    ) -> List[DetectedView]:
        """
        Detect views by finding thick dividing lines.

        Technical drawings often use thick lines to separate views.
        """
        h, w = image.shape[:2]
        views = []

        # Detect edges
        edges = cv2.Canny(gray, 50, 150)

        # Use Hough transform to find lines
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=min(w, h) * 0.3,
            maxLineGap=20,
        )

        if lines is None:
            return views

        # Separate horizontal and vertical lines
        h_lines = []
        v_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)

            # Check if horizontal (angle near 0 or 180)
            if abs(y2 - y1) < length * 0.1:
                h_lines.append((y1 + y2) // 2)
            # Check if vertical (angle near 90)
            elif abs(x2 - x1) < length * 0.1:
                v_lines.append((x1 + x2) // 2)

        # Cluster nearby lines
        h_dividers = self._cluster_positions(h_lines, threshold=50)
        v_dividers = self._cluster_positions(v_lines, threshold=50)

        # Create view regions from dividers
        h_boundaries = [0] + sorted(h_dividers) + [h]
        v_boundaries = [0] + sorted(v_dividers) + [w]

        # Generate grid of views
        for i in range(len(h_boundaries) - 1):
            for j in range(len(v_boundaries) - 1):
                y1, y2 = h_boundaries[i], h_boundaries[i+1]
                x1, x2 = v_boundaries[j], v_boundaries[j+1]

                if y2 - y1 < h * 0.1 or x2 - x1 < w * 0.1:
                    continue

                views.append(DetectedView(
                    bbox=(x1, y1, x2 - x1, y2 - y1),
                    label=f"view_{len(views)+1}",
                    confidence=0.7,
                ))

        return views

    def _detect_by_whitespace(
        self,
        image: np.ndarray,
        gray: np.ndarray,
    ) -> List[DetectedView]:
        """
        Detect views by finding large whitespace gaps.

        Views are often separated by empty space (no ink).
        """
        h, w = image.shape[:2]

        # Threshold to binary
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

        # Find horizontal projection (sum along rows)
        h_proj = np.mean(binary, axis=1) / 255.0

        # Find vertical projection (sum along columns)
        v_proj = np.mean(binary, axis=0) / 255.0

        # Find gaps (high whitespace)
        h_gaps = np.where(h_proj > self.whitespace_threshold)[0]
        v_gaps = np.where(v_proj > self.whitespace_threshold)[0]

        # Cluster gaps into dividers
        h_dividers = self._find_gap_centers(h_gaps, min_gap=30)
        v_dividers = self._find_gap_centers(v_gaps, min_gap=30)

        # Create views from boundaries
        h_boundaries = [0] + h_dividers + [h]
        v_boundaries = [0] + v_dividers + [w]

        views = []
        for i in range(len(h_boundaries) - 1):
            for j in range(len(v_boundaries) - 1):
                y1, y2 = h_boundaries[i], h_boundaries[i+1]
                x1, x2 = v_boundaries[j], v_boundaries[j+1]

                if y2 - y1 < h * 0.1 or x2 - x1 < w * 0.1:
                    continue

                views.append(DetectedView(
                    bbox=(x1, y1, x2 - x1, y2 - y1),
                    label=f"view_{len(views)+1}",
                    confidence=0.6,
                ))

        return views

    def _detect_by_contours(
        self,
        image: np.ndarray,
        gray: np.ndarray,
    ) -> List[DetectedView]:
        """
        Detect views by clustering contours spatially.

        Groups of nearby contours likely belong to the same view.
        """
        h, w = image.shape[:2]

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) < 2:
            return []

        # Get bounding boxes
        bboxes = [cv2.boundingRect(cnt) for cnt in contours]

        # Filter tiny contours
        bboxes = [(x, y, bw, bh) for x, y, bw, bh in bboxes
                  if bw * bh > w * h * 0.001]

        if len(bboxes) < 2:
            return []

        # Cluster by centroid proximity
        centers = np.array([(x + bw/2, y + bh/2) for x, y, bw, bh in bboxes])

        # Simple clustering: divide image into quadrants if contours are spread
        x_spread = centers[:, 0].std() / w
        y_spread = centers[:, 1].std() / h

        views = []

        if x_spread > 0.2 and y_spread > 0.2:
            # 4 quadrants
            for qx in range(2):
                for qy in range(2):
                    vx = qx * w // 2
                    vy = qy * h // 2
                    views.append(DetectedView(
                        bbox=(vx, vy, w // 2, h // 2),
                        label=f"quadrant_{qx}_{qy}",
                        confidence=0.5,
                    ))
        elif x_spread > 0.2:
            # Split horizontally (left/right)
            views.append(DetectedView(bbox=(0, 0, w // 2, h), label="left", confidence=0.5))
            views.append(DetectedView(bbox=(w // 2, 0, w // 2, h), label="right", confidence=0.5))
        elif y_spread > 0.2:
            # Split vertically (top/bottom)
            views.append(DetectedView(bbox=(0, 0, w, h // 2), label="top", confidence=0.5))
            views.append(DetectedView(bbox=(0, h // 2, w, h // 2), label="bottom", confidence=0.5))

        return views

    def _cluster_positions(
        self,
        positions: List[int],
        threshold: int = 50,
    ) -> List[int]:
        """Cluster nearby positions and return cluster centers."""
        if not positions:
            return []

        positions = sorted(positions)
        clusters = [[positions[0]]]

        for pos in positions[1:]:
            if pos - clusters[-1][-1] < threshold:
                clusters[-1].append(pos)
            else:
                clusters.append([pos])

        return [int(np.mean(c)) for c in clusters]

    def _find_gap_centers(
        self,
        gap_indices: np.ndarray,
        min_gap: int = 30,
    ) -> List[int]:
        """Find centers of contiguous gap regions."""
        if len(gap_indices) < min_gap:
            return []

        # Find contiguous regions
        regions = []
        start = gap_indices[0]
        prev = gap_indices[0]

        for idx in gap_indices[1:]:
            if idx - prev > 1:
                if prev - start >= min_gap:
                    regions.append((start, prev))
                start = idx
            prev = idx

        if prev - start >= min_gap:
            regions.append((start, prev))

        # Return centers
        return [(s + e) // 2 for s, e in regions]


# =============================================================================
# Integration with Existing Pipeline
# =============================================================================

def preprocess_blueprint(
    image_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
) -> List[Path]:
    """
    Preprocess a multi-view blueprint into individual view images.

    Args:
        image_path: Path to multi-view blueprint
        output_dir: Directory for output images (default: same as input)

    Returns:
        List of paths to individual view images
    """
    image_path = Path(image_path)
    if output_dir is None:
        output_dir = image_path.parent
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Segment views
    segmenter = BlueprintViewSegmenter()
    result = segmenter.segment(image_path)

    if not result.is_multi_view:
        logger.info("Single view detected, no preprocessing needed")
        return [image_path]

    # Save individual views
    output_paths = []
    stem = image_path.stem

    for i, view in enumerate(result.views):
        if view.image is None:
            continue

        view_path = output_dir / f"{stem}_view{i+1}_{view.label}.png"
        cv2.imwrite(str(view_path), view.image)
        output_paths.append(view_path)
        logger.info(f"Saved view: {view_path} ({view.width}x{view.height})")

    return output_paths


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Segment multi-view blueprints into individual views"
    )
    parser.add_argument("image", help="Input blueprint image")
    parser.add_argument("-o", "--output-dir", help="Output directory for view images")
    parser.add_argument(
        "-m", "--method",
        choices=["auto", "lines", "whitespace", "contours"],
        default="auto",
        help="Detection method",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    segmenter = BlueprintViewSegmenter()
    result = segmenter.segment(args.image, method=args.method)

    print(f"\nSegmentation Result:")
    print(f"  Original size: {result.original_size[0]} x {result.original_size[1]}")
    print(f"  Multi-view: {result.is_multi_view}")
    print(f"  Views found: {result.view_count}")

    for i, view in enumerate(result.views):
        print(f"\n  View {i+1}: {view.label}")
        print(f"    Bbox: x={view.x}, y={view.y}, {view.width}x{view.height}")
        print(f"    Area ratio: {view.area_ratio:.1%}")
        print(f"    Confidence: {view.confidence:.2f}")

    if result.warnings:
        print(f"\nWarnings:")
        for warn in result.warnings:
            print(f"  - {warn}")

    # Optionally save views
    if args.output_dir:
        paths = preprocess_blueprint(args.image, args.output_dir)
        print(f"\nSaved {len(paths)} view images to {args.output_dir}")


if __name__ == "__main__":
    main()
