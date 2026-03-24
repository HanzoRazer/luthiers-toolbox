"""
Multi-View Shape Reconstructor

Visual hull reconstruction from 2-4 calibrated photos.
Runs existing extractor per view, aligns to common coordinate system,
intersects silhouettes to tighten the top-view profile.

Two-pass extraction:
  Pass 1: RETR_EXTERNAL for body outline (strict filtering)
  Pass 2: RETR_TREE for internal features (children of body, min 200px²)

Internal feature classification by bounding box:
  92×40mm ±15% → PICKUP
  76×56mm ±15% → NECK_POCKET
  <500px² → HARDWARE_HOLE
  else → CAVITY

No instrument identification - pure geometry output.
Works on any object: guitar bodies, templates, blanks.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
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


# =============================================================================
# Feature Classification
# =============================================================================

class FeatureLayer(Enum):
    """DXF layer names for classified features."""
    BODY_OUTLINE = "BODY_OUTLINE"
    PICKUP = "PICKUP"
    NECK_POCKET = "NECK_POCKET"
    CAVITY = "CAVITY"
    HARDWARE_HOLE = "HARDWARE_HOLE"


# Feature size specifications (mm) with ±15% tolerance
FEATURE_SPECS = {
    FeatureLayer.PICKUP: {
        "width": 92.0,
        "height": 40.0,
        "tolerance": 0.15,
    },
    FeatureLayer.NECK_POCKET: {
        "width": 76.0,
        "height": 56.0,
        "tolerance": 0.15,
    },
}

# Minimum area thresholds
MIN_INTERNAL_AREA_PX = 200  # Pass 2 minimum area filter
HARDWARE_HOLE_MAX_AREA_PX = 500  # Below this → HARDWARE_HOLE


@dataclass
class InternalFeature:
    """Classified internal feature from Pass 2."""
    contour_px: np.ndarray
    contour_mm: Optional[np.ndarray] = None
    layer: FeatureLayer = FeatureLayer.CAVITY
    area_px: float = 0.0
    area_mm2: float = 0.0
    bbox_mm: Tuple[float, float] = (0.0, 0.0)  # (width, height)
    confidence: float = 0.5


@dataclass
class ViewResult:
    """Result from processing a single view."""
    view_name: str
    contour_mm: Optional[np.ndarray] = None
    contour_px: Optional[np.ndarray] = None
    internal_features: List[InternalFeature] = field(default_factory=list)
    scale_factor: float = 1.0
    mm_per_px: float = 1.0
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
    internal_features: List[InternalFeature] = field(default_factory=list)
    features_by_layer: Dict[str, List[np.ndarray]] = field(default_factory=dict)
    view_results: Dict[str, ViewResult] = field(default_factory=dict)
    overall_confidence: float = 0.0
    output_dxf: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "contour_points": self.contour_points,
            "internal_feature_count": len(self.internal_features),
            "layers": list(self.features_by_layer.keys()),
            "view_confidences": {
                k: v.confidence for k, v in self.view_results.items()
            },
            "overall_confidence": self.overall_confidence,
            "output_dxf": self.output_dxf,
            "warnings": self.warnings,
            "success": self.success,
        }


def classify_feature_by_bbox(
    width_mm: float,
    height_mm: float,
    area_px: float,
) -> FeatureLayer:
    """
    Classify internal feature by bounding box dimensions.

    Priority:
      1. PICKUP: 92×40mm ±15%
      2. NECK_POCKET: 76×56mm ±15%
      3. HARDWARE_HOLE: area < 500px²
      4. CAVITY: everything else
    """
    # Check for pickup (92×40mm ±15%)
    pickup_spec = FEATURE_SPECS[FeatureLayer.PICKUP]
    pw, ph = pickup_spec["width"], pickup_spec["height"]
    tol = pickup_spec["tolerance"]

    if (_within_tolerance(width_mm, pw, tol) and
        _within_tolerance(height_mm, ph, tol)):
        return FeatureLayer.PICKUP

    # Also check rotated (40×92mm)
    if (_within_tolerance(width_mm, ph, tol) and
        _within_tolerance(height_mm, pw, tol)):
        return FeatureLayer.PICKUP

    # Check for neck pocket (76×56mm ±15%)
    neck_spec = FEATURE_SPECS[FeatureLayer.NECK_POCKET]
    nw, nh = neck_spec["width"], neck_spec["height"]
    tol = neck_spec["tolerance"]

    if (_within_tolerance(width_mm, nw, tol) and
        _within_tolerance(height_mm, nh, tol)):
        return FeatureLayer.NECK_POCKET

    # Also check rotated
    if (_within_tolerance(width_mm, nh, tol) and
        _within_tolerance(height_mm, nw, tol)):
        return FeatureLayer.NECK_POCKET

    # Check for hardware hole (small area)
    if area_px < HARDWARE_HOLE_MAX_AREA_PX:
        return FeatureLayer.HARDWARE_HOLE

    # Default to cavity
    return FeatureLayer.CAVITY


def _within_tolerance(value: float, target: float, tolerance: float) -> bool:
    """Check if value is within ±tolerance of target."""
    return abs(value - target) <= target * tolerance


# =============================================================================
# Main Reconstructor
# =============================================================================

class MultiViewReconstructor:
    """
    Reconstructs object geometry from multiple calibrated photos.

    Two-pass extraction:
      Pass 1: RETR_EXTERNAL for body outline via PhotoVectorizerV2
      Pass 2: RETR_TREE for internal features (children of body)

    Uses visual hull intersection: the top view defines the X-Y plane,
    front/side views constrain the profile by clipping points outside
    their projected ranges.

    Parameters
    ----------
    simplify_tolerance_mm : float
        Contour simplification tolerance in mm (default: 0.5)
    min_confidence : float
        Minimum confidence threshold for view acceptance (default: 0.3)
    extract_internal_features : bool
        Whether to run Pass 2 for internal features (default: True)
    """

    def __init__(
        self,
        simplify_tolerance_mm: float = 0.5,
        min_confidence: float = 0.3,
        extract_internal_features: bool = True,
    ):
        self.simplify_tolerance_mm = simplify_tolerance_mm
        self.min_confidence = min_confidence
        self.extract_internal_features = extract_internal_features
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
            Contains reconstructed contour, internal features, and warnings.
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
                    f"confidence={vr.confidence:.2f}, "
                    f"internal_features={len(vr.internal_features)}"
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

            # Collect internal features from top view
            result.internal_features = top_result.internal_features

            # Organize features by layer
            result.features_by_layer = self._organize_by_layer(
                reconstructed, top_result.internal_features
            )

            # Compute overall confidence
            confidences = [
                vr.confidence for vr in view_results.values() if vr.success
            ]
            result.overall_confidence = (
                float(np.mean(confidences)) if confidences else 0.0
            )

            # Export DXF if requested
            if output_path:
                dxf_path = self._export_dxf_with_layers(
                    result.features_by_layer, output_path
                )
                if dxf_path:
                    result.output_dxf = str(dxf_path)

        return result

    def _process_view(
        self,
        view_name: str,
        image_path: Union[str, Path],
        calibration_mm: float,
    ) -> ViewResult:
        """
        Process a single view with two-pass extraction.

        Pass 1: RETR_EXTERNAL for body outline (via PhotoVectorizerV2)
        Pass 2: RETR_TREE for internal features (children of body)
        """
        vr = ViewResult(view_name=view_name)

        image_path = Path(image_path)
        if not image_path.exists():
            vr.error = f"File not found: {image_path}"
            return vr

        try:
            # ─────────────────────────────────────────────────────────────────
            # Pass 1: Body outline via PhotoVectorizerV2 (RETR_EXTERNAL)
            # ─────────────────────────────────────────────────────────────────
            vectorizer = self._get_vectorizer()

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

            contour_mm = np.asarray(body.points_mm, dtype=np.float64)
            if contour_mm.ndim == 3:
                contour_mm = contour_mm.reshape(-1, 2)

            contour_px = np.asarray(body.points_px, dtype=np.float64)
            if contour_px.ndim == 3:
                contour_px = contour_px.reshape(-1, 2)

            if len(contour_mm) < 3:
                vr.error = "Contour has fewer than 3 points"
                return vr

            # Compute scale factor (mm per pixel)
            scale_factor = getattr(extraction, "scale_factor", 1.0)
            calibration = getattr(extraction, "calibration", None)
            if calibration and hasattr(calibration, "mm_per_pixel"):
                mm_per_px = calibration.mm_per_pixel
            else:
                # Estimate from body dimensions
                px_w = contour_px[:, 0].max() - contour_px[:, 0].min()
                mm_w = contour_mm[:, 0].max() - contour_mm[:, 0].min()
                mm_per_px = mm_w / px_w if px_w > 0 else 1.0

            # Normalize to centered coordinates
            contour_mm = self._center_contour(contour_mm)

            # Compute dimensions
            x_min, y_min = contour_mm.min(axis=0)
            x_max, y_max = contour_mm.max(axis=0)
            width = x_max - x_min
            height = y_max - y_min

            vr.contour_mm = contour_mm
            vr.contour_px = contour_px
            vr.scale_factor = scale_factor
            vr.mm_per_px = mm_per_px
            vr.confidence = getattr(body, "confidence", 0.5)
            vr.width_mm = float(width)
            vr.height_mm = float(height)
            vr.success = True

            # ─────────────────────────────────────────────────────────────────
            # Pass 2: Internal features via RETR_TREE (top view only)
            # ─────────────────────────────────────────────────────────────────
            if self.extract_internal_features and view_name == "top":
                vr.internal_features = self._extract_internal_features(
                    image_path, contour_px, mm_per_px
                )
                logger.info(
                    f"Pass 2: extracted {len(vr.internal_features)} internal features"
                )

        except Exception as e:
            vr.error = str(e)
            logger.exception(f"Error processing view '{view_name}'")

        return vr

    def _extract_internal_features(
        self,
        image_path: Path,
        body_contour_px: np.ndarray,
        mm_per_px: float,
    ) -> List[InternalFeature]:
        """
        Pass 2: Extract internal features using RETR_TREE.

        Finds children of body contour, filters by minimum area,
        classifies by bounding box size.
        """
        features: List[InternalFeature] = []

        try:
            # Load and preprocess image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.warning(f"Could not load image for Pass 2: {image_path}")
                return features

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply adaptive threshold for cavity detection
            thresh = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                blockSize=51,
                C=10,
            )

            # Find contours with hierarchy (RETR_TREE)
            contours, hierarchy = cv2.findContours(
                thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )

            if hierarchy is None or len(contours) == 0:
                return features

            hierarchy = hierarchy[0]  # Shape: (N, 4)

            # Find the body contour index by matching
            body_idx = self._find_body_contour_index(
                contours, body_contour_px
            )

            if body_idx < 0:
                logger.warning("Could not match body contour in hierarchy")
                # Fall back: use all contours inside body
                body_idx = None

            # Collect children of body contour (or all internal)
            body_centroid = body_contour_px.mean(axis=0)

            for i, cnt in enumerate(contours):
                # Check if this is a child of body
                if body_idx is not None:
                    parent = hierarchy[i][3]
                    if parent != body_idx:
                        continue
                else:
                    # Fallback: check if centroid is inside body
                    cnt_flat = cnt.reshape(-1, 2)
                    cnt_centroid = cnt_flat.mean(axis=0)
                    if not self._point_in_contour(cnt_centroid, body_contour_px):
                        continue

                # Filter by minimum area
                area_px = cv2.contourArea(cnt)
                if area_px < MIN_INTERNAL_AREA_PX:
                    continue

                # Get bounding box
                x, y, w, h = cv2.boundingRect(cnt)
                width_mm = w * mm_per_px
                height_mm = h * mm_per_px
                area_mm2 = area_px * (mm_per_px ** 2)

                # Classify feature
                layer = classify_feature_by_bbox(width_mm, height_mm, area_px)

                # Convert contour to mm
                cnt_flat = cnt.reshape(-1, 2).astype(np.float64)
                cnt_mm = cnt_flat * mm_per_px

                # Center relative to body centroid
                body_center_mm = body_contour_px.mean(axis=0) * mm_per_px
                cnt_mm = cnt_mm - body_center_mm

                features.append(InternalFeature(
                    contour_px=cnt,
                    contour_mm=cnt_mm,
                    layer=layer,
                    area_px=area_px,
                    area_mm2=area_mm2,
                    bbox_mm=(width_mm, height_mm),
                    confidence=0.7,
                ))

                logger.debug(
                    f"Internal feature: {layer.value} "
                    f"({width_mm:.1f}×{height_mm:.1f}mm, {area_px:.0f}px²)"
                )

        except Exception as e:
            logger.exception(f"Pass 2 failed: {e}")

        return features

    def _find_body_contour_index(
        self,
        contours: List[np.ndarray],
        body_contour_px: np.ndarray,
    ) -> int:
        """Find index of contour that best matches body outline."""
        body_area = cv2.contourArea(body_contour_px.astype(np.float32))
        best_idx = -1
        best_iou = 0.0

        for i, cnt in enumerate(contours):
            cnt_area = cv2.contourArea(cnt)
            # Quick filter: area should be similar (within 50%)
            if abs(cnt_area - body_area) > body_area * 0.5:
                continue

            # Compute IoU approximation via bounding box
            x1, y1, w1, h1 = cv2.boundingRect(cnt)
            x2, y2, w2, h2 = cv2.boundingRect(body_contour_px.astype(np.int32))

            # Intersection
            ix = max(0, min(x1+w1, x2+w2) - max(x1, x2))
            iy = max(0, min(y1+h1, y2+h2) - max(y1, y2))
            intersection = ix * iy

            # Union
            union = w1*h1 + w2*h2 - intersection
            iou = intersection / union if union > 0 else 0

            if iou > best_iou:
                best_iou = iou
                best_idx = i

        return best_idx if best_iou > 0.7 else -1

    def _point_in_contour(
        self,
        point: np.ndarray,
        contour: np.ndarray,
    ) -> bool:
        """Check if point is inside contour."""
        cnt = contour.astype(np.float32)
        if cnt.ndim == 2:
            cnt = cnt.reshape(-1, 1, 2)
        result = cv2.pointPolygonTest(cnt, (float(point[0]), float(point[1])), False)
        return result >= 0

    def _organize_by_layer(
        self,
        body_contour: np.ndarray,
        internal_features: List[InternalFeature],
    ) -> Dict[str, List[np.ndarray]]:
        """Organize all features by layer name."""
        layers: Dict[str, List[np.ndarray]] = {
            FeatureLayer.BODY_OUTLINE.value: [body_contour],
        }

        for feat in internal_features:
            layer_name = feat.layer.value
            if layer_name not in layers:
                layers[layer_name] = []
            if feat.contour_mm is not None:
                layers[layer_name].append(feat.contour_mm)

        return layers

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

        front_y_min = float(front_contour[:, 1].min())
        front_y_max = float(front_contour[:, 1].max())

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

        side_x_min = float(side_contour[:, 0].min())
        side_x_max = float(side_contour[:, 0].max())

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
        """Clip contour points to stay within axis bounds."""
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
                poly = poly.buffer(0)

            x_min, y_min = contour.min(axis=0)
            x_max, y_max = contour.max(axis=0)

            if axis == 0:
                clipped = clip_by_rect(poly, min_val, y_min - 1, max_val, y_max + 1)
            else:
                clipped = clip_by_rect(poly, x_min - 1, min_val, x_max + 1, max_val)

            if clipped.is_empty:
                return contour

            if hasattr(clipped, "exterior"):
                coords = np.array(clipped.exterior.coords)
            else:
                largest = max(clipped.geoms, key=lambda g: g.area)
                coords = np.array(largest.exterior.coords)

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
        """Simple point clamping."""
        result = contour.copy()
        result[:, axis] = np.clip(result[:, axis], min_val, max_val)
        return result

    def _export_dxf_with_layers(
        self,
        features_by_layer: Dict[str, List[np.ndarray]],
        output_path: Union[str, Path],
    ) -> Optional[Path]:
        """Export all features to DXF with layer separation."""
        if not EZDXF_AVAILABLE:
            logger.error("ezdxf not installed - pip install ezdxf")
            return None

        try:
            output_path = Path(output_path)

            # Create DXF document (R2010 format)
            doc = ezdxf.new("R2010")
            msp = doc.modelspace()

            # Layer colors (ACI color codes)
            LAYER_COLORS = {
                "BODY_OUTLINE": 7,      # White
                "PICKUP": 1,            # Red
                "NECK_POCKET": 5,       # Blue
                "CAVITY": 3,            # Green
                "HARDWARE_HOLE": 6,     # Magenta
            }

            # Add layers and features
            for layer_name, contours in features_by_layer.items():
                # Create layer
                color = LAYER_COLORS.get(layer_name, 7)
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name, color=color)

                # Add contours
                for contour in contours:
                    if contour is None or len(contour) < 3:
                        continue

                    points = contour.tolist()
                    if not np.allclose(contour[0], contour[-1]):
                        points.append(points[0])

                    msp.add_lwpolyline(
                        points,
                        dxfattribs={"layer": layer_name},
                        close=True,
                    )

            # Save
            doc.saveas(str(output_path))
            logger.info(f"DXF written: {output_path} ({len(features_by_layer)} layers)")
            return output_path

        except Exception as e:
            logger.exception(f"DXF export failed: {e}")
            return None

    # Legacy method for backward compatibility
    def _export_dxf(
        self,
        contour: np.ndarray,
        output_path: Union[str, Path],
    ) -> Optional[Path]:
        """Export single contour to DXF (backward compatible)."""
        return self._export_dxf_with_layers(
            {FeatureLayer.BODY_OUTLINE.value: [contour]},
            output_path,
        )


def parse_calibration(cal_str: str) -> float:
    """Parse calibration string like 'ruler_mm=300' or just '300'."""
    if "=" in cal_str:
        _, value = cal_str.split("=", 1)
        return float(value)
    return float(cal_str)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-view shape reconstructor with internal feature extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Top view only (body + internal features)
  python multi_view_reconstructor.py --top top.jpg --output body.dxf

  # All views with calibration
  python multi_view_reconstructor.py \\
    --top top.jpg \\
    --front front.jpg \\
    --side side.jpg \\
    --output body.dxf \\
    --calibration ruler_mm=300

Output DXF layers:
  BODY_OUTLINE   - External body contour
  PICKUP         - 92×40mm ±15% features
  NECK_POCKET    - 76×56mm ±15% features
  CAVITY         - Other internal cavities
  HARDWARE_HOLE  - Small holes (<500px²)
        """,
    )

    parser.add_argument("--top", required=True, help="Top view image (required)")
    parser.add_argument("--front", default=None, help="Front view image (optional)")
    parser.add_argument("--side", default=None, help="Side view image (optional)")
    parser.add_argument("--back", default=None, help="Back view image (optional)")
    parser.add_argument("--output", "-o", required=True, help="Output DXF path")
    parser.add_argument(
        "--calibration", "-c",
        default="ruler_mm=300",
        help="Calibration reference (e.g., ruler_mm=300)",
    )
    parser.add_argument(
        "--no-internal",
        action="store_true",
        help="Skip internal feature extraction (Pass 2)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    views: ViewDict = {"top": args.top}
    if args.front:
        views["front"] = args.front
    if args.side:
        views["side"] = args.side
    if args.back:
        views["back"] = args.back

    calibration_mm = parse_calibration(args.calibration)
    logger.info(f"Calibration: {calibration_mm}mm")

    reconstructor = MultiViewReconstructor(
        extract_internal_features=not args.no_internal,
    )
    result = reconstructor.reconstruct(
        views=views,
        output_path=args.output,
        calibration_mm=calibration_mm,
    )

    if result.success:
        print("Reconstruction successful!")
        print(f"  Body points: {len(result.contour_points)}")
        print(f"  Internal features: {len(result.internal_features)}")
        print(f"  Layers: {list(result.features_by_layer.keys())}")
        print(f"  Confidence: {result.overall_confidence:.2f}")
        print(f"  DXF: {result.output_dxf}")

        # Feature breakdown
        for layer, contours in result.features_by_layer.items():
            print(f"    {layer}: {len(contours)} contour(s)")

        sys.exit(0)
    else:
        print("Reconstruction failed!")
        for warning in result.warnings:
            print(f"  WARNING: {warning}")
        sys.exit(1)


if __name__ == "__main__":
    main()
