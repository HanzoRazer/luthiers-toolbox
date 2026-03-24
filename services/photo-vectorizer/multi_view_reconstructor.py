"""
Multi-View Shape Reconstructor

Visual hull reconstruction from 2-4 calibrated photos.
Runs existing extractor per view, aligns to common coordinate system,
intersects silhouettes to tighten the top-view profile.

No instrument identification - pure geometry output.
Works on any object: guitar bodies, templates, blanks.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

try:
    from shapely.geometry import Polygon
    from shapely.ops import clip_by_rect
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

logger = logging.getLogger(__name__)

# Type aliases
ViewDict = Dict[str, Union[str, Path]]
PointList = List[Tuple[float, float]]


@dataclass
class ViewResult:
    """Result from processing a single view."""
    view_name: str
    contour_mm: Optional[np.ndarray] = None
    scale_factor: float = 1.0
    confidence: float = 0.0
    width_mm: float = 0.0
    height_mm: float = 0.0
    success: bool = False
    error: Optional[str] = None


@dataclass
class ReconstructionResult:
    """Result from multi-view reconstruction."""
    contour_mm: Optional[np.ndarray] = None
    contour_points: Optional[PointList] = None
    view_results: Dict[str, ViewResult] = field(default_factory=dict)
    overall_confidence: float = 0.0
    output_dxf: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "contour_points": self.contour_points,
            "view_confidences": {
                k: v.confidence for k, v in self.view_results.items()
            },
            "overall_confidence": self.overall_confidence,
            "output_dxf": self.output_dxf,
            "warnings": self.warnings,
            "success": self.success,
        }


class MultiViewReconstructor:
    """
    Reconstructs object geometry from multiple calibrated photos.

    Uses visual hull intersection: the top view defines the X-Y plane,
    front/side views constrain the profile by clipping points outside
    their projected ranges.

    Parameters
    ----------
    simplify_tolerance_mm : float
        Contour simplification tolerance in mm (default: 0.5)
    min_confidence : float
        Minimum confidence threshold for view acceptance (default: 0.3)
    """

    def __init__(
        self,
        simplify_tolerance_mm: float = 0.5,
        min_confidence: float = 0.3,
    ):
        self.simplify_tolerance_mm = simplify_tolerance_mm
        self.min_confidence = min_confidence
        self._vectorizer = None

    def _get_vectorizer(self):
        """Lazy-load PhotoVectorizerV2 to avoid import overhead."""
        if self._vectorizer is None:
            from photo_vectorizer_v2 import PhotoVectorizerV2
            self._vectorizer = PhotoVectorizerV2(
                simplify_tolerance_mm=self.simplify_tolerance_mm,
                dxf_version="R2010",
            )
        return self._vectorizer

    def reconstruct(
        self,
        views: ViewDict,
        output_path: Optional[Union[str, Path]] = None,
        calibration_mm: float = 300.0,
    ) -> ReconstructionResult:
        """
        Reconstruct shape from multiple views.

        Parameters
        ----------
        views : dict
            Image paths keyed by view name. "top" is required.
            Optional: "front", "side", "back".
            Example: {"top": "top.jpg", "front": "front.jpg"}

        output_path : str or Path, optional
            Output DXF path. If None, DXF is not exported.

        calibration_mm : float
            Known reference dimension in mm (e.g., ruler length).
            Default: 300mm (12 inch ruler).

        Returns
        -------
        ReconstructionResult
            Contains reconstructed contour, per-view confidences, and warnings.
        """
        result = ReconstructionResult()

        # Validate required top view
        if "top" not in views:
            result.warnings.append("Missing required 'top' view")
            return result

        # Process each view
        view_results: Dict[str, ViewResult] = {}
        for view_name, image_path in views.items():
            if view_name not in ("top", "front", "side", "back"):
                result.warnings.append(f"Unknown view '{view_name}' ignored")
                continue

            vr = self._process_view(view_name, image_path, calibration_mm)
            view_results[view_name] = vr

            if vr.success:
                logger.info(
                    f"View '{view_name}': {vr.width_mm:.1f}x{vr.height_mm:.1f}mm, "
                    f"confidence={vr.confidence:.2f}"
                )
            else:
                result.warnings.append(
                    f"View '{view_name}' failed: {vr.error or 'unknown'}"
                )

        result.view_results = view_results

        # Top view is required and must succeed
        top_result = view_results.get("top")
        if not top_result or not top_result.success:
            result.warnings.append("Top view extraction failed")
            return result

        # Start with top view contour
        reconstructed = top_result.contour_mm.copy()

        # Apply silhouette intersection from other views
        front_result = view_results.get("front")
        side_result = view_results.get("side")

        if front_result and front_result.success:
            reconstructed = self._clip_by_front_view(
                reconstructed, front_result.contour_mm
            )
            logger.info("Applied front view clipping")

        if side_result and side_result.success:
            reconstructed = self._clip_by_side_view(
                reconstructed, side_result.contour_mm
            )
            logger.info("Applied side view clipping")

        # Finalize result
        if reconstructed is not None and len(reconstructed) >= 3:
            result.contour_mm = reconstructed
            result.contour_points = [
                (float(p[0]), float(p[1])) for p in reconstructed
            ]
            result.success = True

            # Compute overall confidence
            confidences = [
                vr.confidence for vr in view_results.values() if vr.success
            ]
            result.overall_confidence = float(np.mean(confidences)) if confidences else 0.0

            # Export DXF if requested
            if output_path:
                dxf_path = self._export_dxf(reconstructed, output_path)
                if dxf_path:
                    result.output_dxf = str(dxf_path)

        return result

    def _process_view(
        self,
        view_name: str,
        image_path: Union[str, Path],
        calibration_mm: float,
    ) -> ViewResult:
        """Extract body contour from a single view image."""
        vr = ViewResult(view_name=view_name)

        image_path = Path(image_path)
        if not image_path.exists():
            vr.error = f"File not found: {image_path}"
            return vr

        try:
            vectorizer = self._get_vectorizer()

            # Extract with photo pipeline and calibration
            extraction = vectorizer.extract(
                str(image_path),
                output_dir=str(image_path.parent),
                known_dimension_mm=calibration_mm,
                source_type="photo",
                export_dxf=False,
                export_svg=False,
                export_json=False,
                debug_images=False,
            )

            # Handle potential list result (multi-instrument)
            if isinstance(extraction, list):
                extraction = extraction[0] if extraction else None

            if extraction is None:
                vr.error = "Extraction returned None"
                return vr

            # Get body contour
            body = getattr(extraction, "body_contour", None)
            if body is None or body.points_mm is None:
                vr.error = "No body contour extracted"
                return vr

            contour = np.asarray(body.points_mm, dtype=np.float64)
            if contour.ndim == 3:
                contour = contour.reshape(-1, 2)

            if len(contour) < 3:
                vr.error = "Contour has fewer than 3 points"
                return vr

            # Normalize to centered coordinates
            contour = self._center_contour(contour)

            # Compute dimensions
            x_min, y_min = contour.min(axis=0)
            x_max, y_max = contour.max(axis=0)
            width = x_max - x_min
            height = y_max - y_min

            vr.contour_mm = contour
            vr.scale_factor = getattr(extraction, "scale_factor", 1.0)
            vr.confidence = getattr(body, "confidence", 0.5)
            vr.width_mm = float(width)
            vr.height_mm = float(height)
            vr.success = True

        except Exception as e:
            vr.error = str(e)
            logger.exception(f"Error processing view '{view_name}'")

        return vr

    def _center_contour(self, contour: np.ndarray) -> np.ndarray:
        """Center contour around its centroid."""
        centroid = contour.mean(axis=0)
        return contour - centroid

    def _clip_by_front_view(
        self,
        top_contour: np.ndarray,
        front_contour: np.ndarray,
    ) -> np.ndarray:
        """
        Clip top contour using front view projection.

        Front view projects height profile onto Y axis.
        Points in top contour outside front's Y range are clipped.
        """
        if front_contour is None or len(front_contour) < 3:
            return top_contour

        # Front view: Y axis represents depth (corresponds to top view Y)
        # Get Y range from front view
        front_y_min = float(front_contour[:, 1].min())
        front_y_max = float(front_contour[:, 1].max())

        # Clip top contour points
        return self._clip_contour_by_axis(
            top_contour, axis=1, min_val=front_y_min, max_val=front_y_max
        )

    def _clip_by_side_view(
        self,
        top_contour: np.ndarray,
        side_contour: np.ndarray,
    ) -> np.ndarray:
        """
        Clip top contour using side view projection.

        Side view projects width profile onto X axis.
        Points in top contour outside side's X range are clipped.
        """
        if side_contour is None or len(side_contour) < 3:
            return top_contour

        # Side view: X axis represents width (corresponds to top view X)
        # Get X range from side view
        side_x_min = float(side_contour[:, 0].min())
        side_x_max = float(side_contour[:, 0].max())

        # Clip top contour points
        return self._clip_contour_by_axis(
            top_contour, axis=0, min_val=side_x_min, max_val=side_x_max
        )

    def _clip_contour_by_axis(
        self,
        contour: np.ndarray,
        axis: int,
        min_val: float,
        max_val: float,
    ) -> np.ndarray:
        """
        Clip contour points to stay within axis bounds.

        Uses Shapely for proper polygon clipping if available,
        otherwise falls back to simple point filtering.
        """
        if SHAPELY_AVAILABLE:
            return self._clip_with_shapely(contour, axis, min_val, max_val)
        else:
            return self._clip_simple(contour, axis, min_val, max_val)

    def _clip_with_shapely(
        self,
        contour: np.ndarray,
        axis: int,
        min_val: float,
        max_val: float,
    ) -> np.ndarray:
        """Clip using Shapely's polygon clipping."""
        try:
            poly = Polygon(contour)
            if not poly.is_valid:
                poly = poly.buffer(0)  # Fix invalid geometry

            # Get bounding box of contour
            x_min, y_min = contour.min(axis=0)
            x_max, y_max = contour.max(axis=0)

            # Create clip rectangle based on axis
            if axis == 0:  # X axis
                clipped = clip_by_rect(poly, min_val, y_min - 1, max_val, y_max + 1)
            else:  # Y axis
                clipped = clip_by_rect(poly, x_min - 1, min_val, x_max + 1, max_val)

            if clipped.is_empty:
                return contour

            # Extract exterior coordinates
            if hasattr(clipped, "exterior"):
                coords = np.array(clipped.exterior.coords)
            else:
                # May be MultiPolygon - take largest
                largest = max(clipped.geoms, key=lambda g: g.area)
                coords = np.array(largest.exterior.coords)

            # Remove closing point if present
            if len(coords) > 1 and np.allclose(coords[0], coords[-1]):
                coords = coords[:-1]

            return coords

        except Exception as e:
            logger.warning(f"Shapely clipping failed: {e}, using simple clip")
            return self._clip_simple(contour, axis, min_val, max_val)

    def _clip_simple(
        self,
        contour: np.ndarray,
        axis: int,
        min_val: float,
        max_val: float,
    ) -> np.ndarray:
        """Simple point filtering (less accurate but no dependencies)."""
        # Clamp points to bounds rather than removing
        result = contour.copy()
        result[:, axis] = np.clip(result[:, axis], min_val, max_val)
        return result

    def _export_dxf(
        self,
        contour: np.ndarray,
        output_path: Union[str, Path],
    ) -> Optional[Path]:
        """Export reconstructed contour to DXF."""
        if not EZDXF_AVAILABLE:
            logger.error("ezdxf not installed - pip install ezdxf")
            return None

        try:
            output_path = Path(output_path)

            # Create DXF document (R2010 format)
            doc = ezdxf.new("R2010")
            msp = doc.modelspace()

            # Create BODY_OUTLINE layer
            if "BODY_OUTLINE" not in doc.layers:
                doc.layers.add("BODY_OUTLINE", color=7)  # White

            # Close the contour if not already closed
            points = contour.tolist()
            if not np.allclose(contour[0], contour[-1]):
                points.append(points[0])

            # Add polyline
            msp.add_lwpolyline(
                points,
                dxfattribs={"layer": "BODY_OUTLINE"},
                close=True,
            )

            # Save
            doc.saveas(str(output_path))
            logger.info(f"DXF written: {output_path}")
            return output_path

        except Exception as e:
            logger.exception(f"DXF export failed: {e}")
            return None


def parse_calibration(cal_str: str) -> float:
    """Parse calibration string like 'ruler_mm=300' or just '300'."""
    if "=" in cal_str:
        _, value = cal_str.split("=", 1)
        return float(value)
    return float(cal_str)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-view shape reconstructor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Top view only
  python multi_view_reconstructor.py --top top.jpg --output body.dxf

  # All views with calibration
  python multi_view_reconstructor.py \\
    --top top.jpg \\
    --front front.jpg \\
    --side side.jpg \\
    --output body.dxf \\
    --calibration ruler_mm=300
        """,
    )

    parser.add_argument(
        "--top",
        required=True,
        help="Top view image (required)",
    )
    parser.add_argument(
        "--front",
        default=None,
        help="Front view image (optional refiner)",
    )
    parser.add_argument(
        "--side",
        default=None,
        help="Side view image (optional refiner)",
    )
    parser.add_argument(
        "--back",
        default=None,
        help="Back view image (optional refiner)",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output DXF path",
    )
    parser.add_argument(
        "--calibration", "-c",
        default="ruler_mm=300",
        help="Calibration reference (e.g., ruler_mm=300)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Build views dict
    views: ViewDict = {"top": args.top}
    if args.front:
        views["front"] = args.front
    if args.side:
        views["side"] = args.side
    if args.back:
        views["back"] = args.back

    # Parse calibration
    calibration_mm = parse_calibration(args.calibration)
    logger.info(f"Calibration: {calibration_mm}mm")

    # Run reconstruction
    reconstructor = MultiViewReconstructor()
    result = reconstructor.reconstruct(
        views=views,
        output_path=args.output,
        calibration_mm=calibration_mm,
    )

    # Report results
    if result.success:
        print(f"Reconstruction successful!")
        print(f"  Points: {len(result.contour_points)}")
        print(f"  Confidence: {result.overall_confidence:.2f}")
        print(f"  DXF: {result.output_dxf}")

        for view_name, vr in result.view_results.items():
            status = "OK" if vr.success else f"FAILED: {vr.error}"
            print(f"  View '{view_name}': {status}")
            if vr.success:
                print(f"    Dimensions: {vr.width_mm:.1f}x{vr.height_mm:.1f}mm")
                print(f"    Confidence: {vr.confidence:.2f}")

        sys.exit(0)
    else:
        print("Reconstruction failed!")
        for warning in result.warnings:
            print(f"  WARNING: {warning}")
        sys.exit(1)


if __name__ == "__main__":
    main()
