"""
AI Render Extractor — Standalone handler for AI-generated instrument renders.

Extracts geometry from AI renders (Midjourney, DALL-E, etc.) with:
- CUTAWAY_VOID layer for Klein ergonomic through-body voids
- Spec cavity overlay for routing geometry not visible in renders
- Dark background auto-detection
- CLI interface

This runs alongside photo_vectorizer_v2.py, not as a replacement.
Companion to multi_view_reconstructor.py.

Usage:
    python ai_render_extractor.py image.png -s smart_guitar -o output.dxf
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

DXF_LAYERS = {
    "BODY_OUTLINE": {"color": 7},      # White - main body perimeter
    "CUTAWAY_VOID": {"color": 1},      # Red - Klein ergonomic voids
    "NECK_POCKET": {"color": 3},       # Green - neck pocket from spec
    "PICKUP_CAVITY": {"color": 4},     # Cyan - pickup routes from spec
    "CONTROL_CAVITY": {"color": 5},    # Blue - control cavity from spec
    "BRIDGE_ROUTE": {"color": 6},      # Magenta - bridge routing from spec
}

SPEC_DIR = Path(__file__).parent.parent / "api" / "app" / "instrument_geometry" / "body" / "specs"

DARK_BACKGROUND_THRESHOLD = 60  # Mean brightness below this = dark background


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExtractorConfig:
    """Configuration for AI render extraction."""
    spec_name: str = "smart_guitar"
    min_contour_area: float = 1000.0
    simplify_epsilon: float = 2.0
    detect_voids: bool = True
    overlay_spec_cavities: bool = True
    output_scale_mm: float = 1.0  # Output units in mm


@dataclass
class ExtractionResult:
    """Result of AI render extraction."""
    body_contour: List[Tuple[float, float]] = field(default_factory=list)
    cutaway_voids: List[List[Tuple[float, float]]] = field(default_factory=list)
    spec_cavities: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict)
    is_dark_background: bool = False
    image_size: Tuple[int, int] = (0, 0)
    warnings: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# AIRenderExtractor Class
# ─────────────────────────────────────────────────────────────────────────────

class AIRenderExtractor:
    """
    Standalone extractor for AI-generated instrument renders.

    Extracts body outline and Klein ergonomic voids from renders,
    then overlays spec-defined cavity geometry for routing.
    """

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()
        self._spec_data: Optional[Dict[str, Any]] = None

    def load_spec(self, spec_name: str) -> bool:
        """Load instrument spec JSON for cavity overlay."""
        spec_path = SPEC_DIR / f"{spec_name}_v1.json"
        if not spec_path.exists():
            # Try without _v1 suffix
            spec_path = SPEC_DIR / f"{spec_name}.json"

        if not spec_path.exists():
            return False

        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                self._spec_data = json.load(f)
            return True
        except (json.JSONDecodeError, OSError):
            return False

    def detect_dark_background(self, image: "np.ndarray") -> bool:
        """Detect if image has dark background (AI renders often do)."""
        if not CV2_AVAILABLE:
            return False

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Check mean brightness of border pixels
        h, w = gray.shape[:2]
        border_size = max(10, min(h, w) // 20)

        top = gray[:border_size, :].mean()
        bottom = gray[-border_size:, :].mean()
        left = gray[:, :border_size].mean()
        right = gray[:, -border_size:].mean()

        mean_border = (top + bottom + left + right) / 4
        return mean_border < DARK_BACKGROUND_THRESHOLD

    def extract_body_contour(
        self,
        image: "np.ndarray",
        invert_for_dark: bool = True
    ) -> List[Tuple[float, float]]:
        """Extract main body outline from image."""
        if not CV2_AVAILABLE:
            return []

        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Invert if dark background
        if invert_for_dark and self.detect_dark_background(image):
            gray = cv2.bitwise_not(gray)

        # Threshold and find contours
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return []

        # Find largest contour (body outline)
        largest = max(contours, key=cv2.contourArea)

        if cv2.contourArea(largest) < self.config.min_contour_area:
            return []

        # Simplify contour
        epsilon = self.config.simplify_epsilon
        approx = cv2.approxPolyDP(largest, epsilon, True)

        # Convert to list of tuples
        return [(float(pt[0][0]), float(pt[0][1])) for pt in approx]

    def extract_cutaway_voids(
        self,
        image: "np.ndarray",
        body_contour: List[Tuple[float, float]]
    ) -> List[List[Tuple[float, float]]]:
        """
        Extract Klein ergonomic cutaway voids.

        These are internal voids in the body silhouette that represent
        through-body ergonomic cuts (Klein ETR style).
        """
        if not CV2_AVAILABLE or not self.config.detect_voids:
            return []

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        is_dark = self.detect_dark_background(image)
        if is_dark:
            gray = cv2.bitwise_not(gray)

        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Find internal contours (holes in the body)
        contours, hierarchy = cv2.findContours(
            binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )

        voids = []
        if hierarchy is not None:
            for i, (contour, hier) in enumerate(zip(contours, hierarchy[0])):
                # hier[3] is parent - if parent exists, this is an internal contour
                if hier[3] != -1:
                    area = cv2.contourArea(contour)
                    if area > self.config.min_contour_area * 0.1:  # Smaller threshold for voids
                        epsilon = self.config.simplify_epsilon
                        approx = cv2.approxPolyDP(contour, epsilon, True)
                        void_pts = [(float(pt[0][0]), float(pt[0][1])) for pt in approx]
                        voids.append(void_pts)

        return voids

    def get_spec_cavities(self) -> Dict[str, List[Tuple[float, float]]]:
        """Get cavity geometry from loaded spec."""
        if not self._spec_data:
            return {}

        cavities = {}

        # Extract cavity definitions from spec
        # Structure varies by spec, handle common patterns
        if "cavities" in self._spec_data:
            for cavity_name, cavity_data in self._spec_data["cavities"].items():
                if "outline" in cavity_data:
                    cavities[cavity_name] = [
                        (pt["x"], pt["y"]) for pt in cavity_data["outline"]
                    ]
                elif "rect" in cavity_data:
                    rect = cavity_data["rect"]
                    x, y, w, h = rect["x"], rect["y"], rect["width"], rect["height"]
                    cavities[cavity_name] = [
                        (x, y), (x + w, y), (x + w, y + h), (x, y + h)
                    ]

        # Also check for named cavity sections
        for section in ["neck_pocket", "pickup_neck", "pickup_bridge",
                       "control_cavity", "bridge_route", "pi_cavity"]:
            if section in self._spec_data:
                data = self._spec_data[section]
                if isinstance(data, dict):
                    if "center" in data and "width_mm" in data and "depth_mm" in data:
                        cx, cy = data["center"]["x"], data["center"]["y"]
                        w, h = data["width_mm"], data["depth_mm"]
                        cavities[section] = [
                            (cx - w/2, cy - h/2),
                            (cx + w/2, cy - h/2),
                            (cx + w/2, cy + h/2),
                            (cx - w/2, cy + h/2),
                        ]

        return cavities

    def extract(self, image_path: str) -> ExtractionResult:
        """
        Run full extraction pipeline on an image.

        Args:
            image_path: Path to AI render image

        Returns:
            ExtractionResult with all extracted geometry
        """
        result = ExtractionResult()

        if not CV2_AVAILABLE:
            result.warnings.append("OpenCV not available - extraction disabled")
            return result

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            result.warnings.append(f"Could not load image: {image_path}")
            return result

        result.image_size = (image.shape[1], image.shape[0])
        result.is_dark_background = self.detect_dark_background(image)

        # Extract body contour
        result.body_contour = self.extract_body_contour(image)
        if not result.body_contour:
            result.warnings.append("No body contour detected")

        # Extract cutaway voids
        if self.config.detect_voids:
            result.cutaway_voids = self.extract_cutaway_voids(image, result.body_contour)

        # Load and overlay spec cavities
        if self.config.overlay_spec_cavities:
            if self.load_spec(self.config.spec_name):
                result.spec_cavities = self.get_spec_cavities()
            else:
                result.warnings.append(f"Spec not found: {self.config.spec_name}")

        return result

    def export_dxf(
        self,
        result: ExtractionResult,
        output_path: str,
        center_origin: bool = True
    ) -> bool:
        """
        Export extraction result to DXF.

        Args:
            result: ExtractionResult from extract()
            output_path: Output DXF file path
            center_origin: If True, center geometry at (0, 0)

        Returns:
            True if export succeeded
        """
        if not EZDXF_AVAILABLE:
            return False

        doc = ezdxf.new("R12")
        msp = doc.modelspace()

        # Create layers
        for layer_name, props in DXF_LAYERS.items():
            doc.layers.add(layer_name, color=props["color"])

        # Calculate centering offset
        offset_x, offset_y = 0.0, 0.0
        if center_origin and result.body_contour:
            xs = [p[0] for p in result.body_contour]
            ys = [p[1] for p in result.body_contour]
            offset_x = (max(xs) + min(xs)) / 2
            offset_y = (max(ys) + min(ys)) / 2

        def transform(pts: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
            scale = self.config.output_scale_mm
            return [(
                (x - offset_x) * scale,
                (y - offset_y) * scale
            ) for x, y in pts]

        # Add body outline
        if result.body_contour:
            pts = transform(result.body_contour)
            msp.add_lwpolyline(pts, dxfattribs={"layer": "BODY_OUTLINE"}, close=True)

        # Add cutaway voids
        for void in result.cutaway_voids:
            pts = transform(void)
            msp.add_lwpolyline(pts, dxfattribs={"layer": "CUTAWAY_VOID"}, close=True)

        # Add spec cavities
        layer_map = {
            "neck_pocket": "NECK_POCKET",
            "pickup_neck": "PICKUP_CAVITY",
            "pickup_bridge": "PICKUP_CAVITY",
            "control_cavity": "CONTROL_CAVITY",
            "bridge_route": "BRIDGE_ROUTE",
        }

        for cavity_name, cavity_pts in result.spec_cavities.items():
            layer = layer_map.get(cavity_name, "CONTROL_CAVITY")
            pts = transform(cavity_pts)
            if len(pts) >= 3:
                msp.add_lwpolyline(pts, dxfattribs={"layer": layer}, close=True)

        try:
            doc.saveas(output_path)
            return True
        except (OSError, ezdxf.DXFError):
            return False


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract geometry from AI-generated instrument renders"
    )
    parser.add_argument("image", help="Input image path (PNG, JPG)")
    parser.add_argument(
        "-s", "--spec",
        default="smart_guitar",
        help="Instrument spec name (default: smart_guitar)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output DXF path (default: <image>_extracted.dxf)"
    )
    parser.add_argument(
        "--no-voids",
        action="store_true",
        help="Disable cutaway void detection"
    )
    parser.add_argument(
        "--no-overlay",
        action="store_true",
        help="Disable spec cavity overlay"
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Output scale factor (default: 1.0 = mm)"
    )

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.image):
        print(f"Error: Image not found: {args.image}")
        return 1

    # Configure extractor
    config = ExtractorConfig(
        spec_name=args.spec,
        detect_voids=not args.no_voids,
        overlay_spec_cavities=not args.no_overlay,
        output_scale_mm=args.scale,
    )

    extractor = AIRenderExtractor(config)

    # Run extraction
    print(f"Extracting from: {args.image}")
    result = extractor.extract(args.image)

    # Report results
    print(f"  Dark background: {result.is_dark_background}")
    print(f"  Body contour: {len(result.body_contour)} points")
    print(f"  Cutaway voids: {len(result.cutaway_voids)}")
    print(f"  Spec cavities: {len(result.spec_cavities)}")

    for warning in result.warnings:
        print(f"  WARNING: {warning}")

    # Export DXF
    output_path = args.output
    if not output_path:
        base = os.path.splitext(args.image)[0]
        output_path = f"{base}_extracted.dxf"

    if extractor.export_dxf(result, output_path):
        print(f"  Exported: {output_path}")
        return 0
    else:
        print("  ERROR: DXF export failed")
        return 1


if __name__ == "__main__":
    exit(main())
