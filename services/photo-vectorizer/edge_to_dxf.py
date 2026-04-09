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
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

logger = logging.getLogger(__name__)


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
    ) -> EdgeToDXFResult:
        """
        Convert image edges to DXF LINE entities.

        Args:
            source_path: Path to source image (JPG, PNG, etc.)
            output_path: Output DXF path (default: {source}_edges.dxf)
            target_height_mm: Target height in mm for scaling
            blur_kernel: Gaussian blur kernel size (0 to disable)
            morph_close_kernel: Morphological close kernel (0 to disable)

        Returns:
            EdgeToDXFResult with conversion statistics
        """
        start_time = time.time()

        # Validate input
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        # Default output path
        if output_path is None:
            output_path = str(source.with_name(f"{source.stem}_edges.dxf"))

        # Load image
        logger.info(f"Loading: {source_path}")
        img = cv2.imread(str(source_path))
        if img is None:
            raise ValueError(f"Failed to load image: {source_path}")

        h, w = img.shape[:2]
        logger.info(f"Image size: {w} x {h} px")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Optional blur
        if blur_kernel > 0:
            gray = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)

        # Edge detection
        logger.info(f"Running Canny edge detection (thresholds: {self.canny_low}/{self.canny_high})")
        edges = cv2.Canny(gray, self.canny_low, self.canny_high)

        # Optional morphological close to connect nearby edges
        if morph_close_kernel > 0:
            kernel = np.ones((morph_close_kernel, morph_close_kernel), np.uint8)
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

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

        # Create DXF
        logger.info(f"Creating DXF ({self.dxf_version})...")
        doc = ezdxf.new(self.dxf_version)
        msp = doc.modelspace()

        # Add layer
        if self.layer_name not in doc.layers:
            doc.layers.add(self.layer_name)

        # TOPOLOGY FIX: Use cv2.findContours() for proper contour tracing
        # instead of row-major pixel sorting which creates disconnected LINE segments
        logger.info("Tracing contours from edge image...")
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        # Filter degenerate contours (< 3 points)
        valid_contours = [c for c in contours if len(c) >= 3]
        logger.info(f"Found {len(contours)} contours, {len(valid_contours)} valid (>= 3 points)")

        if not valid_contours:
            raise ValueError("No valid contours found in edge image")

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

        # Save DXF
        logger.info(f"Saving: {output_path}")
        doc.saveas(output_path)

        # Get file size
        file_size = Path(output_path).stat().st_size

        processing_time = (time.time() - start_time) * 1000

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
        )

        logger.info(f"Complete in {processing_time:.0f}ms")
        return result

    def convert_enhanced(
        self,
        source_path: str,
        output_path: Optional[str] = None,
        target_height_mm: float = 500.0,
    ) -> EdgeToDXFResult:
        """
        Enhanced conversion with multi-scale edge fusion.

        Combines edges from multiple Canny threshold levels for more
        complete edge coverage. Produces more LINE entities.

        Args:
            source_path: Path to source image
            output_path: Output DXF path
            target_height_mm: Target height in mm

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
