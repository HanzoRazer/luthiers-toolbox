"""
Guitar Segmentation Service

Core service for AI-powered guitar body outline extraction.
Orchestrates: Vision AI → Polygon Processing → DXF Export

DATE: January 2026
"""
from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image
import io
import json

from app.ai.transport import get_vision_client, VisionClient, VisionClientError
from app.vision.segmentation_prompts import (
    get_segmentation_prompt,
    validate_segmentation_response,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SegmentationResult:
    """Result of guitar body segmentation."""
    # Polygon in normalized coordinates (0-1 range)
    polygon_normalized: List[Tuple[float, float]]
    # Polygon scaled to target dimensions (mm)
    polygon_mm: List[Tuple[float, float]]
    # Confidence score from AI (0-1)
    confidence: float
    # Detected guitar type
    guitar_type: str
    # Original image dimensions
    image_width: int
    image_height: int
    # Target dimensions used for scaling
    target_width_mm: float
    target_height_mm: float
    # Processing metadata
    point_count: int
    notes: str = ""
    # Token usage from API
    usage: Dict[str, int] = field(default_factory=dict)


@dataclass
class SegmentationError:
    """Error result from segmentation."""
    error: str
    confidence: float = 0.0
    details: Optional[str] = None


# ---------------------------------------------------------------------------
# Geometry Utilities
# ---------------------------------------------------------------------------

def douglas_peucker(points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
    """
    Douglas-Peucker polyline simplification.

    Reduces point count while preserving shape within epsilon tolerance.
    """
    if len(points) < 3:
        return points

    # Find point with maximum distance from line between first and last
    start, end = points[0], points[-1]
    max_dist = 0.0
    max_idx = 0

    for i in range(1, len(points) - 1):
        dist = perpendicular_distance(points[i], start, end)
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    # If max distance exceeds epsilon, recursively simplify
    if max_dist > epsilon:
        left = douglas_peucker(points[:max_idx + 1], epsilon)
        right = douglas_peucker(points[max_idx:], epsilon)
        return left[:-1] + right
    else:
        return [start, end]


def perpendicular_distance(
    point: Tuple[float, float],
    line_start: Tuple[float, float],
    line_end: Tuple[float, float]
) -> float:
    """Calculate perpendicular distance from point to line segment."""
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

    t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)))

    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return math.sqrt((x0 - proj_x) ** 2 + (y0 - proj_y) ** 2)


def compute_signed_area(points: List[Tuple[float, float]]) -> float:
    """
    Compute signed area using shoelace formula.

    Positive = counter-clockwise, Negative = clockwise
    """
    n = len(points)
    if n < 3:
        return 0.0

    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]

    return area / 2.0


def ensure_ccw(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Ensure polygon has counter-clockwise winding (for outer boundaries)."""
    if compute_signed_area(points) < 0:
        return list(reversed(points))
    return points


def ensure_closed(points: List[Tuple[float, float]], tolerance: float = 0.001) -> List[Tuple[float, float]]:
    """Ensure polygon is closed (first point == last point)."""
    if not points:
        return points

    first, last = points[0], points[-1]
    dist = math.sqrt((first[0] - last[0]) ** 2 + (first[1] - last[1]) ** 2)

    if dist > tolerance:
        return points + [first]
    return points


def normalize_polygon(
    points: List[Tuple[float, float]],
    image_width: int,
    image_height: int
) -> List[Tuple[float, float]]:
    """Normalize polygon coordinates to 0-1 range."""
    return [(x / image_width, y / image_height) for x, y in points]


def scale_polygon(
    normalized: List[Tuple[float, float]],
    target_width_mm: float,
    target_height_mm: float,
    center: bool = True
) -> List[Tuple[float, float]]:
    """
    Scale normalized polygon to target dimensions in mm.

    Args:
        normalized: Polygon with coordinates in 0-1 range
        target_width_mm: Target width in mm
        target_height_mm: Target height in mm
        center: If True, center polygon on origin

    Returns:
        Polygon with coordinates in mm
    """
    scaled = [(x * target_width_mm, y * target_height_mm) for x, y in normalized]

    if center:
        # Find bounds
        xs = [p[0] for p in scaled]
        ys = [p[1] for p in scaled]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2

        # Center on origin
        scaled = [(x - cx, y - cy) for x, y in scaled]

        # Flip Y axis (image coords to CAD coords)
        scaled = [(x, -y) for x, y in scaled]

    return scaled


# ---------------------------------------------------------------------------
# Main Segmentation Service
# ---------------------------------------------------------------------------

class GuitarSegmentationService:
    """
    Service for extracting guitar body outlines from images.

    Pipeline:
    1. Send image to Vision AI (GPT-4o)
    2. Parse polygon coordinates from response
    3. Normalize to 0-1 range
    4. Scale to target dimensions (mm)
    5. Simplify polygon (Douglas-Peucker)
    6. Ensure CCW winding and closure
    7. Export to DXF format
    """

    def __init__(self, vision_client: Optional[VisionClient] = None):
        """
        Initialize segmentation service.

        Args:
            vision_client: Vision client instance (defaults to OpenAI GPT-4o)
        """
        self.client = vision_client or get_vision_client("openai")

    def segment(
        self,
        image_bytes: bytes,
        target_width_mm: float = 400.0,
        simplify_tolerance_mm: float = 1.0,
        guitar_category: str = "auto",
    ) -> SegmentationResult | SegmentationError:
        """
        Segment guitar body from image.

        Args:
            image_bytes: Raw image bytes (PNG, JPG, WebP)
            target_width_mm: Target width for output in mm
            simplify_tolerance_mm: Simplification tolerance in mm
            guitar_category: "acoustic", "electric", or "auto"

        Returns:
            SegmentationResult on success, SegmentationError on failure
        """
        # Get image dimensions
        try:
            img = Image.open(io.BytesIO(image_bytes))
            image_width, image_height = img.size
        except (OSError, ValueError) as e:  # WP-1: narrowed from except Exception
            return SegmentationError(
                error=f"Failed to read image: {e}",
                details="Ensure image is valid PNG, JPG, or WebP"
            )

        # Calculate target height maintaining aspect ratio
        aspect_ratio = image_height / image_width
        target_height_mm = target_width_mm * aspect_ratio

        # Get appropriate prompt
        prompt = get_segmentation_prompt(guitar_category)

        # Call Vision AI
        try:
            response = self.client.analyze(
                image_bytes=image_bytes,
                prompt=prompt,
                response_format="json",
                detail="high",
            )
        except VisionClientError as e:
            return SegmentationError(
                error=f"Vision API error: {e}",
                details=str(e)
            )

        # Parse response
        try:
            data = response.as_json
            validated = validate_segmentation_response(data)
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
            return SegmentationError(
                error=f"Failed to parse response: {e}",
                details=response.raw_response[:500] if response else None
            )

        # Check for error response
        if "error" in validated:
            return SegmentationError(
                error=validated["error"],
                confidence=validated.get("confidence", 0.0)
            )

        # Extract polygon
        raw_points = validated["body_outline"]
        points = [(float(p[0]), float(p[1])) for p in raw_points]

        # Use detected image dimensions if provided
        detected_width = validated.get("image_width", image_width)
        detected_height = validated.get("image_height", image_height)

        # Normalize to 0-1 range
        normalized = normalize_polygon(points, detected_width, detected_height)

        # Scale to target mm
        scaled = scale_polygon(normalized, target_width_mm, target_height_mm, center=True)

        # Simplify
        if simplify_tolerance_mm > 0:
            scaled = douglas_peucker(scaled, simplify_tolerance_mm)

        # Ensure CCW winding (for outer boundary)
        scaled = ensure_ccw(scaled)

        # Ensure closed
        scaled = ensure_closed(scaled)

        return SegmentationResult(
            polygon_normalized=normalized,
            polygon_mm=scaled,
            confidence=validated.get("confidence", 0.0),
            guitar_type=validated.get("guitar_type", "unknown"),
            image_width=image_width,
            image_height=image_height,
            target_width_mm=target_width_mm,
            target_height_mm=target_height_mm,
            point_count=len(scaled),
            notes=validated.get("notes", ""),
            usage=response.usage,
        )

    def export_to_dxf(self, result: SegmentationResult) -> bytes:
        """
        Export segmentation result to DXF format.

        Args:
            result: Successful segmentation result

        Returns:
            DXF file bytes
        """
        # Build DXF R12 format (widely compatible)
        lines = [
            "0", "SECTION",
            "2", "HEADER",
            "9", "$ACADVER",
            "1", "AC1009",  # AutoCAD R12
            "9", "$INSUNITS",
            "70", "4",  # 4 = millimeters
            "0", "ENDSEC",
            "0", "SECTION",
            "2", "ENTITIES",
        ]

        # Add LWPOLYLINE (or use POLYLINE for R12 compat)
        points = result.polygon_mm

        if points:
            # POLYLINE entity (R12 compatible)
            lines.extend([
                "0", "POLYLINE",
                "8", "GEOMETRY",  # Layer name
                "66", "1",  # Vertices follow
                "70", "1",  # Closed polyline
            ])

            for x, y in points:
                lines.extend([
                    "0", "VERTEX",
                    "8", "GEOMETRY",
                    "10", f"{x:.6f}",
                    "20", f"{y:.6f}",
                    "30", "0.0",
                ])

            lines.extend(["0", "SEQEND", "8", "GEOMETRY"])

        lines.extend([
            "0", "ENDSEC",
            "0", "EOF",
        ])

        return "\n".join(lines).encode("utf-8")

    def export_to_svg(
        self,
        result: SegmentationResult,
        stroke_width: float = 0.5
    ) -> str:
        """
        Export segmentation result to SVG format.

        Args:
            result: Successful segmentation result
            stroke_width: Stroke width in mm

        Returns:
            SVG string
        """
        points = result.polygon_mm
        if not points:
            return '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

        # Calculate bounds
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        padding = 10
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding

        # Build path
        points_str = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="{min_x - padding} {min_y - padding} {width} {height}"
     width="{width}mm" height="{height}mm">
  <title>Guitar Body - {result.guitar_type}</title>
  <desc>AI-segmented guitar body outline. Confidence: {result.confidence:.2f}</desc>
  <g fill="none" stroke="black" stroke-width="{stroke_width}">
    <polygon points="{points_str}" />
  </g>
</svg>'''

        return svg
