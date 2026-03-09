"""
DXF Post-Processor for CAM-Ready Output
========================================

Addresses three commercial viability blockers:
  1. Version upgrade: R2000 default for native LWPOLYLINE support
  2. Arc fitting: detect circular arcs in polyline sequences
  3. Scale application: multiply all output coordinates by scale_factor

Usage:
    # During export (integrated into pipeline)
    from dxf_postprocessor import ArcFitter, export_cam_ready_dxf

    # Standalone post-processing of an existing DXF
    from dxf_postprocessor import postprocess_dxf
    postprocess_dxf("input.dxf", "output.dxf", version='R2000', fit_arcs=True)

Author: The Production Shop
Version: 1.0.0
"""
import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import ezdxf
    from ezdxf.document import Drawing
    from ezdxf.layouts import Modelspace
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

from dxf_compat import (
    create_document, add_polyline, supports_lwpolyline,
    validate_version, DxfVersion
)

logger = logging.getLogger(__name__)


# =============================================================================
# Arc Detection Data Structures
# =============================================================================

@dataclass
class ArcSegment:
    """A detected circular arc in a point sequence."""
    center: Tuple[float, float]
    radius: float
    start_angle: float  # degrees
    end_angle: float    # degrees
    start_idx: int
    end_idx: int
    fit_error: float    # RMS residual in mm


@dataclass
class PolySegment:
    """A straight/non-arc portion of a point sequence."""
    points: List[Tuple[float, float]]
    start_idx: int
    end_idx: int


# =============================================================================
# Arc Fitting Algorithm
# =============================================================================

class ArcFitter:
    """
    Detects true circular arcs in polyline point sequences.

    Uses a sliding-window approach:
      1. Start with a window of min_points consecutive points
      2. Fit a circle using algebraic least-squares
      3. If fit error < tolerance, extend the window
      4. When the window can't extend further, record the arc
      5. Non-arc sections become polyline segments

    Only outputs arcs when:
      - At least min_points points participate
      - Arc span > min_arc_degrees
      - Fit error < tolerance (mm)
    """

    def __init__(
        self,
        tolerance: float = 0.3,
        min_points: int = 5,
        min_arc_degrees: float = 15.0,
        max_radius: float = 5000.0
    ):
        self.tolerance = tolerance
        self.min_points = min_points
        self.min_arc_degrees = min_arc_degrees
        self.max_radius = max_radius

    def detect_arcs(self, points: List[Tuple[float, float]]) -> List:
        """
        Detect circular arcs in a sequence of points.

        Args:
            points: List of (x, y) tuples in mm

        Returns:
            List of ArcSegment and PolySegment in sequence order
        """
        n = len(points)
        if n < self.min_points:
            return [PolySegment(points=points, start_idx=0, end_idx=n - 1)]

        pts = np.array(points, dtype=np.float64)
        segments = []
        i = 0

        while i < n:
            # Try to start an arc at position i
            best_arc = None

            if i + self.min_points <= n:
                # Start with minimum window
                j = i + self.min_points
                while j <= n:
                    window = pts[i:j]
                    arc = self._fit_circle(window, i, j - 1)

                    if arc and arc.fit_error <= self.tolerance:
                        best_arc = arc
                        j += 1  # Try to extend
                    else:
                        break

            if best_arc and self._arc_span_degrees(best_arc) >= self.min_arc_degrees:
                # Flush any preceding polyline points
                if segments and isinstance(segments[-1], PolySegment):
                    pass  # Already flushed
                segments.append(best_arc)
                i = best_arc.end_idx + 1
            else:
                # No arc found here — add point to polyline segment
                if segments and isinstance(segments[-1], PolySegment):
                    segments[-1].points.append(tuple(pts[i]))
                    segments[-1].end_idx = i
                else:
                    segments.append(PolySegment(
                        points=[tuple(pts[i])],
                        start_idx=i, end_idx=i
                    ))
                i += 1

        return segments

    def _fit_circle(
        self, points: np.ndarray, start_idx: int, end_idx: int
    ) -> Optional[ArcSegment]:
        """
        Algebraic circle fit using Kasa's method.

        Given points (x_i, y_i), solves:
            (x - cx)^2 + (y - cy)^2 = r^2

        Returns ArcSegment or None if fit is degenerate.
        """
        n = len(points)
        if n < 3:
            return None

        x = points[:, 0]
        y = points[:, 1]

        # Kasa's method: solve A @ [cx, cy, c] = b
        # where x^2 + y^2 = 2*cx*x + 2*cy*y + c
        A = np.column_stack([x, y, np.ones(n)])
        b = x ** 2 + y ** 2

        try:
            result, residuals, rank, sv = np.linalg.lstsq(A, b, rcond=None)
        except np.linalg.LinAlgError:
            return None

        cx = result[0] / 2
        cy = result[1] / 2
        r_sq = result[2] + cx ** 2 + cy ** 2

        if r_sq <= 0:
            return None

        r = math.sqrt(r_sq)
        if r > self.max_radius or r < 0.1:
            return None

        # Compute fit error (RMS distance from circle)
        distances = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        residuals = distances - r
        rms_error = float(np.sqrt(np.mean(residuals ** 2)))

        # Compute start and end angles
        start_angle = math.degrees(math.atan2(y[0] - cy, x[0] - cx))
        end_angle = math.degrees(math.atan2(y[-1] - cy, x[-1] - cx))

        return ArcSegment(
            center=(float(cx), float(cy)),
            radius=float(r),
            start_angle=start_angle,
            end_angle=end_angle,
            start_idx=start_idx,
            end_idx=end_idx,
            fit_error=rms_error
        )

    @staticmethod
    def _arc_span_degrees(arc: ArcSegment) -> float:
        """Compute the angular span of an arc."""
        span = abs(arc.end_angle - arc.start_angle)
        if span > 180:
            span = 360 - span
        return span


# =============================================================================
# CAM-Ready DXF Export
# =============================================================================

def export_cam_ready_dxf(
    classified: dict,
    output_path: str,
    image_height: int,
    mm_per_px: float,
    scale_factor: float = 1.0,
    simplify_tolerance: float = 0.2,
    dxf_version: DxfVersion = 'R2000',
    fit_arcs: bool = True,
    arc_tolerance: float = 0.3,
    excluded_categories: Optional[list] = None,
    max_per_category: Optional[dict] = None,
    center_on_body: bool = True
) -> Tuple[float, float]:
    """
    Export classified contours to a CAM-ready DXF file.

    Differences from standard export_to_dxf:
      - Default version R2000 (LWPOLYLINE, native ARC/CIRCLE)
      - Applies scale_factor to all coordinates
      - Optionally fits arcs for smoother toolpaths
      - Uses native CIRCLE/ARC entities where possible (R13+)

    Args:
        classified: Dict of category -> contour list
        output_path: Output DXF path
        image_height: Source image height in pixels
        mm_per_px: Pixels to mm conversion
        scale_factor: Scale multiplier from calibration
        simplify_tolerance: Douglas-Peucker tolerance in mm
        dxf_version: DXF version (default R2000 for LWPOLYLINE)
        fit_arcs: Enable arc fitting for smoother output
        arc_tolerance: Arc fit tolerance in mm
        excluded_categories: Categories to skip
        max_per_category: Max contours per category
        center_on_body: If True, center geometry on body outline

    Returns:
        Tuple of (body_width_mm, body_height_mm)
    """
    import cv2

    try:
        from vectorizer_phase3 import ContourCategory
        if excluded_categories is None:
            excluded_categories = [
                ContourCategory.TEXT,
                ContourCategory.PAGE_BORDER,
                ContourCategory.UNKNOWN
            ]
    except ImportError:
        if excluded_categories is None:
            excluded_categories = []

    if max_per_category is None:
        max_per_category = {}

    # Find body center for alignment
    center_x, center_y = 0.0, 0.0
    body_width, body_height = 0.0, 0.0

    body_key = None
    for cat in classified:
        cat_val = cat.value if hasattr(cat, 'value') else str(cat)
        if cat_val == 'body_outline':
            body_key = cat
            break

    if center_on_body and body_key and classified[body_key]:
        body = classified[body_key][0]
        pts = body.contour.reshape(-1, 2)
        xs = [p[0] * mm_per_px * scale_factor for p in pts]
        ys = [(image_height - p[1]) * mm_per_px * scale_factor for p in pts]
        center_x = (min(xs) + max(xs)) / 2
        center_y = (min(ys) + max(ys)) / 2
        body_width = max(xs) - min(xs)
        body_height = max(ys) - min(ys)

    # Create DXF document (R2000+ by default for LWPOLYLINE)
    version = validate_version(dxf_version)
    doc = create_document(version=version, setup=True if version != 'R12' else False)
    msp = doc.modelspace()

    # Layer colors
    layer_colors = {
        'BODY_OUTLINE': 1, 'PICKGUARD': 2, 'NECK_POCKET': 3,
        'PICKUP_ROUTE': 4, 'CONTROL_CAVITY': 5, 'BRIDGE_ROUTE': 6,
        'JACK_ROUTE': 7, 'RHYTHM_CIRCUIT': 8, 'SOUNDHOLE': 1,
        'D_HOLE': 1, 'F_HOLE': 1, 'ROSETTE': 2, 'BRACING': 3,
        'SMALL_FEATURE': 7,
    }

    use_native_arcs = supports_lwpolyline(version) and fit_arcs
    arc_fitter = ArcFitter(tolerance=arc_tolerance) if use_native_arcs else None

    exported_count = 0
    arc_count = 0

    for category, contours in classified.items():
        if category in excluded_categories:
            continue

        cat_val = category.value if hasattr(category, 'value') else str(category)
        layer_name = cat_val.upper()
        max_count = max_per_category.get(category, 10)

        # Ensure layer exists with color
        if layer_name not in doc.layers:
            color = layer_colors.get(layer_name, 7)
            doc.layers.new(name=layer_name, dxfattribs={'color': color})

        for i, info in enumerate(contours[:max_count]):
            # Convert to scaled mm, flip Y, center
            pts = info.contour.reshape(-1, 2)
            mm_pts = []
            for px, py in pts:
                x_mm = px * mm_per_px * scale_factor - center_x
                y_mm = (image_height - py) * mm_per_px * scale_factor - center_y
                mm_pts.append([x_mm, y_mm])

            # Simplify
            pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
            simplified = cv2.approxPolyDP(pts_array, simplify_tolerance, closed=True)
            simplified = simplified.reshape(-1, 2)

            if len(simplified) < 3:
                continue

            point_tuples = [(float(x), float(y)) for x, y in simplified]

            if arc_fitter:
                # Detect arcs and export mixed entities
                segments = arc_fitter.detect_arcs(point_tuples)
                for seg in segments:
                    try:
                        if isinstance(seg, ArcSegment):
                            msp.add_arc(
                                center=seg.center, radius=seg.radius,
                                start_angle=seg.start_angle,
                                end_angle=seg.end_angle,
                                dxfattribs={'layer': layer_name}
                            )
                            arc_count += 1
                        elif isinstance(seg, PolySegment) and len(seg.points) >= 2:
                            add_polyline(
                                msp, seg.points,
                                layer=layer_name, closed=False, version=version
                            )
                    except Exception as e:
                        logger.warning(f"Failed to add segment to {layer_name}: {e}")
                exported_count += 1
            else:
                # Standard polyline export
                try:
                    add_polyline(msp, point_tuples, layer=layer_name, closed=True, version=version)
                    exported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to add contour to {layer_name}: {e}")

    doc.saveas(output_path)

    if arc_count > 0:
        logger.info(
            f"CAM-ready export: {exported_count} contours, {arc_count} native arcs "
            f"({version} LWPOLYLINE) -> {output_path}"
        )
    else:
        logger.info(f"Exported {exported_count} contours ({version}) -> {output_path}")

    return body_width, body_height


# =============================================================================
# Standalone Post-Processing
# =============================================================================

def postprocess_dxf(
    input_path: str,
    output_path: str,
    version: DxfVersion = 'R2000',
    fit_arcs: bool = False,
    arc_tolerance: float = 0.3,
    scale_multiplier: float = 1.0
) -> Dict[str, int]:
    """
    Post-process an existing DXF file for CAM readiness.

    Reads the input DXF, optionally upgrades version, applies scale,
    and rewrites to output path.

    Args:
        input_path: Source DXF file
        output_path: Target DXF file
        version: Target DXF version (default R2000)
        fit_arcs: Enable arc detection in polylines
        arc_tolerance: Arc fit tolerance in mm
        scale_multiplier: Scale to apply to all coordinates

    Returns:
        Dict with stats: {'entities_processed', 'arcs_fitted', 'version'}
    """
    if not EZDXF_AVAILABLE:
        raise ImportError("ezdxf is required for DXF post-processing")

    src = ezdxf.readfile(input_path)
    target_version = validate_version(version)

    # Create new document at target version
    doc = create_document(version=target_version)
    msp = doc.modelspace()

    # Copy layers from source
    for layer in src.layers:
        if layer.dxf.name not in doc.layers:
            doc.layers.new(
                name=layer.dxf.name,
                dxfattribs={'color': layer.dxf.color}
            )

    stats = {'entities_processed': 0, 'arcs_fitted': 0, 'version': target_version}
    arc_fitter = ArcFitter(tolerance=arc_tolerance) if fit_arcs else None

    for entity in src.modelspace():
        layer = entity.dxf.layer
        stats['entities_processed'] += 1

        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            s = (start.x * scale_multiplier, start.y * scale_multiplier)
            e = (end.x * scale_multiplier, end.y * scale_multiplier)
            msp.add_line(s, e, dxfattribs={'layer': layer})

        elif entity.dxftype() == 'LWPOLYLINE':
            points = [(p[0] * scale_multiplier, p[1] * scale_multiplier)
                       for p in entity.get_points(format='xy')]
            is_closed = entity.closed

            if arc_fitter and len(points) >= arc_fitter.min_points:
                segments = arc_fitter.detect_arcs(points)
                for seg in segments:
                    if isinstance(seg, ArcSegment):
                        msp.add_arc(
                            center=seg.center, radius=seg.radius,
                            start_angle=seg.start_angle,
                            end_angle=seg.end_angle,
                            dxfattribs={'layer': layer}
                        )
                        stats['arcs_fitted'] += 1
                    elif isinstance(seg, PolySegment) and len(seg.points) >= 2:
                        add_polyline(msp, seg.points, layer=layer,
                                     closed=False, version=target_version)
            else:
                add_polyline(msp, points, layer=layer,
                             closed=is_closed, version=target_version)

        elif entity.dxftype() == 'CIRCLE':
            c = entity.dxf.center
            r = entity.dxf.radius * scale_multiplier
            cx = c.x * scale_multiplier
            cy = c.y * scale_multiplier
            if supports_lwpolyline(target_version):
                msp.add_circle((cx, cy), r, dxfattribs={'layer': layer})
            else:
                # R12 fallback: polyline approximation
                n = max(32, int(r * 2))
                pts = [
                    (cx + r * math.cos(2 * math.pi * i / n),
                     cy + r * math.sin(2 * math.pi * i / n))
                    for i in range(n)
                ]
                add_polyline(msp, pts, layer=layer, closed=True, version=target_version)

        elif entity.dxftype() == 'ARC':
            c = entity.dxf.center
            r = entity.dxf.radius * scale_multiplier
            cx = c.x * scale_multiplier
            cy = c.y * scale_multiplier
            if supports_lwpolyline(target_version):
                msp.add_arc(
                    (cx, cy), r,
                    entity.dxf.start_angle, entity.dxf.end_angle,
                    dxfattribs={'layer': layer}
                )
            else:
                # R12 fallback: polyline approximation
                start = math.radians(entity.dxf.start_angle)
                end = math.radians(entity.dxf.end_angle)
                if end < start:
                    end += 2 * math.pi
                span = end - start
                n = max(16, int(math.degrees(span) / 5))
                pts = [
                    (cx + r * math.cos(start + span * i / n),
                     cy + r * math.sin(start + span * i / n))
                    for i in range(n + 1)
                ]
                add_polyline(msp, pts, layer=layer, closed=False, version=target_version)

    doc.saveas(output_path)
    logger.info(
        f"Post-processed DXF: {stats['entities_processed']} entities, "
        f"{stats['arcs_fitted']} arcs fitted -> {output_path} ({target_version})"
    )
    return stats
