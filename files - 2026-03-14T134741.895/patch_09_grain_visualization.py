"""
PATCH 09 — Grain Visualization + Thin-Section Safety Checker
=============================================================

Downstream of: PhotoVectorizerV2 → PhotoExtractionResult + MaterialBOM
Input:  Closed mm-coordinate contours, material assignments, grain angle
Output: SVG with grain lines overlaid, thin-section warnings

Two components:

  GrainVisualizer
    Adds wood grain direction lines inside each feature contour in the SVG.
    Grain lines are spaced to represent real wood grain at appropriate density.
    Supports per-material grain angle configuration.

  ThinSectionChecker
    Scans each feature contour for sections narrower than a minimum safe width.
    Considers the grain angle — cuts across grain are weaker.
    Returns a list of ThinSectionWarning with location, width, and severity.

Design decisions:
  - Grain lines are visual only — they do not affect toolpaths
  - Thin-section threshold defaults: 3mm minimum (binding), 6mm (body parts)
  - Cross-grain cuts at narrow sections are flagged as CRITICAL
  - Along-grain narrow sections are flagged as WARNING
  - SVG output is additive — takes existing SVG and overlays grain layer

Author: The Production Shop
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree.ElementTree import Element, SubElement, ElementTree, parse as etree_parse

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Thin-section safety
# ---------------------------------------------------------------------------

class Severity(Enum):
    INFO     = "info"
    WARNING  = "warning"
    CRITICAL = "critical"


@dataclass
class ThinSectionWarning:
    feature_type:  str
    location_mm:   Tuple[float, float]   # approximate centre of thin section
    width_mm:      float
    grain_angle:   float                  # degrees; 0 = horizontal
    cross_grain:   bool                   # True if cut direction crosses grain
    severity:      Severity
    message:       str

    def to_dict(self) -> dict:
        return {
            "feature_type": self.feature_type,
            "location_mm":  [round(self.location_mm[0], 2),
                              round(self.location_mm[1], 2)],
            "width_mm":     round(self.width_mm, 2),
            "grain_angle":  self.grain_angle,
            "cross_grain":  self.cross_grain,
            "severity":     self.severity.value,
            "message":      self.message,
        }


class ThinSectionChecker:
    """
    Scans feature contours for sections narrower than safe thresholds.

    Parameters
    ----------
    min_width_mm       : absolute minimum safe width (any material)
    binding_min_mm     : minimum for binding/purfling (thinner is OK)
    cross_grain_factor : multiply min_width by this when crossing grain
    sample_interval_mm : interval along perimeter to check width (smaller = thorough)
    """

    def __init__(
        self,
        min_width_mm:       float = 6.0,
        binding_min_mm:     float = 2.5,
        cross_grain_factor: float = 1.5,
        sample_interval_mm: float = 5.0,
    ):
        self.min_width_mm       = min_width_mm
        self.binding_min_mm     = binding_min_mm
        self.cross_grain_factor = cross_grain_factor
        self.sample_interval_mm = sample_interval_mm

    def check(
        self,
        contours_by_layer: Dict[str, List[np.ndarray]],
        grain_angles:      Optional[Dict[str, float]] = None,
    ) -> List[ThinSectionWarning]:
        """
        Check all contours for thin sections.

        Parameters
        ----------
        contours_by_layer : {layer_name: [pts_mm, ...]}
        grain_angles      : {layer_name: angle_degrees}  (0 = horizontal grain)

        Returns
        -------
        list of ThinSectionWarning, sorted by severity (CRITICAL first)
        """
        if grain_angles is None:
            grain_angles = {}

        warnings = []
        for layer, pts_list in contours_by_layer.items():
            is_binding = layer in ("BINDING", "PURFLING")
            min_w = self.binding_min_mm if is_binding else self.min_width_mm
            g_angle = grain_angles.get(layer, 0.0)

            for pts in pts_list:
                w = self._check_contour(pts, layer, min_w, g_angle)
                warnings.extend(w)

        # Sort: CRITICAL first, then WARNING, then INFO
        order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
        warnings.sort(key=lambda w: order[w.severity])
        return warnings

    def _check_contour(
        self,
        pts:         np.ndarray,
        layer:       str,
        min_w_mm:    float,
        grain_angle: float,
    ) -> List[ThinSectionWarning]:
        """
        Sample points along the contour perimeter and cast inward rays to
        measure local width at each sample point.
        """
        warnings = []
        n = len(pts)
        if n < 4:
            return warnings

        # Compute cumulative perimeter
        diff = np.diff(np.vstack([pts, pts[:1]]), axis=0)
        seg_lens = np.sqrt((diff ** 2).sum(axis=1))
        total_perim = float(seg_lens.sum())

        if total_perim < 1.0:
            return warnings

        # Sample at regular intervals
        n_samples = max(4, int(total_perim / self.sample_interval_mm))
        sample_t = np.linspace(0, total_perim, n_samples, endpoint=False)

        cumlen = np.concatenate([[0], np.cumsum(seg_lens)])

        for t in sample_t:
            # Find point on contour at arc-length t
            idx = np.searchsorted(cumlen, t, side='right') - 1
            idx = min(idx, n - 1)
            next_idx = (idx + 1) % n
            seg_t = (t - cumlen[idx]) / max(seg_lens[idx], 1e-9)
            px = pts[idx, 0] + seg_t * (pts[next_idx, 0] - pts[idx, 0])
            py = pts[idx, 1] + seg_t * (pts[next_idx, 1] - pts[idx, 1])

            # Inward normal direction
            dx = pts[next_idx, 0] - pts[idx, 0]
            dy = pts[next_idx, 1] - pts[idx, 1]
            seg_len = math.sqrt(dx * dx + dy * dy)
            if seg_len < 1e-9:
                continue
            nx = -dy / seg_len   # inward normal (perpendicular, pointing inward)
            ny =  dx / seg_len

            # Cast ray inward; find first intersection with contour
            width = self._ray_width(pts, px, py, nx, ny)
            if width is None or width <= 0:
                continue

            # Determine if this section crosses grain
            # Section direction vs grain angle
            section_angle = math.degrees(math.atan2(dy, dx)) % 180
            grain_dir = grain_angle % 180
            angle_diff = abs(section_angle - grain_dir)
            if angle_diff > 90:
                angle_diff = 180 - angle_diff
            cross_grain = angle_diff > 45   # > 45° from grain = cross-grain

            # Effective minimum (tighter threshold when crossing grain)
            eff_min = min_w_mm * (self.cross_grain_factor if cross_grain else 1.0)

            if width < eff_min:
                if width < eff_min * 0.5:
                    sev = Severity.CRITICAL
                elif width < eff_min * 0.75:
                    sev = Severity.WARNING
                else:
                    sev = Severity.INFO

                warnings.append(ThinSectionWarning(
                    feature_type = layer,
                    location_mm  = (round(px, 2), round(py, 2)),
                    width_mm     = round(width, 2),
                    grain_angle  = grain_angle,
                    cross_grain  = cross_grain,
                    severity     = sev,
                    message      = (
                        f"{layer}: {width:.1f}mm wide at ({px:.0f},{py:.0f})mm "
                        f"{'[CROSS-GRAIN]' if cross_grain else '[along-grain]'} "
                        f"— min safe: {eff_min:.1f}mm [{sev.value.upper()}]"
                    ),
                ))

        return warnings

    @staticmethod
    def _ray_width(
        pts:  np.ndarray,
        px:   float, py: float,
        nx:   float, ny: float,
        max_dist: float = 500.0,
    ) -> Optional[float]:
        """
        Cast a ray from (px, py) in direction (nx, ny) and find the first
        intersection with the polygon boundary. Returns the distance.
        """
        n = len(pts)
        min_dist = max_dist

        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            # Segment AB; ray from P in direction N
            # Solve: P + t*N = A + s*(B-A)
            denom = nx * (by - ay) - ny * (bx - ax)
            if abs(denom) < 1e-9:
                continue
            t = ((ax - px) * (by - ay) - (ay - py) * (bx - ax)) / denom
            s = ((ax - px) * ny - (ay - py) * nx) / denom
            if 0.001 < t < min_dist and 0.0 <= s <= 1.0:
                min_dist = t

        return min_dist if min_dist < max_dist else None


# ---------------------------------------------------------------------------
# Grain visualizer
# ---------------------------------------------------------------------------

# Default grain line spacing per material (mm)
GRAIN_SPACING_MM: Dict[str, float] = {
    "spruce_top":      3.0,
    "maple_back_side": 2.5,
    "mahogany":        4.0,
    "rosewood":        2.0,
    "ebony":           1.5,
    "walnut":          3.5,
    "unknown":         5.0,
}

# Default grain stroke colour per material
GRAIN_COLORS: Dict[str, str] = {
    "spruce_top":      "#C8A96E",
    "maple_back_side": "#D4B483",
    "mahogany":        "#8B4513",
    "rosewood":        "#5C2A0A",
    "ebony":           "#2A1A0A",
    "walnut":          "#6B3D1E",
    "unknown":         "#AAAAAA",
}


class GrainVisualizer:
    """
    Adds wood grain lines to an existing SVG file as a new layer.

    Parameters
    ----------
    grain_angles  : {layer_name: degrees}  (0° = horizontal, 90° = vertical)
    material_map  : {layer_name: material_name}  (from BOM or user config)
    spacing_map   : {material: mm between grain lines}
    color_map     : {material: stroke color}
    stroke_width  : SVG stroke width for grain lines (mm)
    opacity       : grain line opacity (0–1)
    """

    def __init__(
        self,
        grain_angles: Optional[Dict[str, float]] = None,
        material_map: Optional[Dict[str, str]]   = None,
        spacing_map:  Optional[Dict[str, float]]  = None,
        color_map:    Optional[Dict[str, str]]    = None,
        stroke_width: float = 0.15,
        opacity:      float = 0.45,
    ):
        self.grain_angles = grain_angles or {}
        self.material_map = material_map or {}
        self.spacing_map  = {**GRAIN_SPACING_MM,  **(spacing_map  or {})}
        self.color_map    = {**GRAIN_COLORS,       **(color_map    or {})}
        self.stroke_width = stroke_width
        self.opacity      = opacity

    # ------------------------------------------------------------------
    def add_to_svg(
        self,
        svg_path:          str,
        contours_by_layer: Dict[str, List[np.ndarray]],
        output_path:       Optional[str] = None,
        thin_warnings:     Optional[List[ThinSectionWarning]] = None,
    ) -> str:
        """
        Add grain lines and (optionally) thin-section markers to an SVG.

        Parameters
        ----------
        svg_path           : path to existing SVG from write_svg()
        contours_by_layer  : {layer: [pts_mm, ...]}  same as used for SVG export
        output_path        : output path (defaults to svg_path with _grain suffix)
        thin_warnings      : if provided, adds red markers at thin sections

        Returns
        -------
        output_path (str)
        """
        if output_path is None:
            p = Path(svg_path)
            output_path = str(p.parent / (p.stem + "_grain" + p.suffix))

        # Parse existing SVG
        try:
            tree = etree_parse(svg_path)
            root = tree.getroot()
            # Strip namespace for easier element access
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"
        except Exception as e:
            # Build minimal SVG from scratch
            root = Element("svg", xmlns="http://www.w3.org/2000/svg",
                           width="600mm", height="800mm",
                           viewBox="0 0 600 800")
            tree = ElementTree(root)
            ns = ""

        # Add grain layer group
        grain_g = SubElement(root, f"{ns}g" if ns else "g",
                              id="GRAIN_VISUALIZATION",
                              opacity=str(self.opacity))

        for layer, pts_list in contours_by_layer.items():
            if layer in ("UNKNOWN",):
                continue
            grain_angle = self.grain_angles.get(layer, 0.0)
            material    = self.material_map.get(layer, "unknown")
            spacing     = self.spacing_map.get(material, 5.0)
            color       = self.color_map.get(material, "#AAAAAA")

            for pts in pts_list:
                if len(pts) < 3:
                    continue
                lines = self._generate_grain_lines(pts, grain_angle, spacing)
                for (x1, y1, x2, y2) in lines:
                    SubElement(grain_g, "line",
                               x1=f"{x1:.3f}", y1=f"{y1:.3f}",
                               x2=f"{x2:.3f}", y2=f"{y2:.3f}",
                               stroke=color,
                               **{"stroke-width": str(self.stroke_width)})

        # Add thin-section warning markers
        if thin_warnings:
            warn_g = SubElement(root, "g", id="THIN_SECTION_WARNINGS")
            for tw in thin_warnings:
                color = {"critical": "#FF0000",
                         "warning":  "#FF8800",
                         "info":     "#FFCC00"}.get(tw.severity.value, "#FF0000")
                x, y = tw.location_mm
                # Circle marker
                SubElement(warn_g, "circle",
                           cx=str(x), cy=str(y), r="3",
                           fill=color, opacity="0.8")
                # Label
                lbl = SubElement(warn_g, "text",
                                 x=str(x + 4), y=str(y + 1),
                                 **{"font-size": "3",
                                    "fill": color,
                                    "font-family": "sans-serif"})
                lbl.text = f"{tw.width_mm:.1f}mm"

        with open(output_path, "wb") as f:
            tree.write(f, xml_declaration=True, encoding="utf-8")

        return output_path

    # ------------------------------------------------------------------
    def _generate_grain_lines(
        self,
        pts:         np.ndarray,
        grain_angle: float,
        spacing_mm:  float,
    ) -> List[Tuple[float, float, float, float]]:
        """
        Generate grain lines inside a polygon contour.

        Grain lines are parallel lines at `grain_angle` degrees, clipped
        to the interior of the polygon using scanline intersection.

        Returns list of (x1, y1, x2, y2) line segments in mm coordinates.
        """
        if len(pts) < 3:
            return []

        xs, ys = pts[:, 0], pts[:, 1]
        x_min, x_max = float(xs.min()), float(xs.max())
        y_min, y_max = float(ys.min()), float(ys.max())

        lines_out = []
        rad = math.radians(grain_angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)

        # Grain direction vector (unit)
        gx, gy = cos_a, sin_a
        # Perpendicular (spacing direction)
        px_dir, py_dir = -sin_a, cos_a

        # Project all polygon vertices onto perpendicular axis
        proj = [px_dir * x + py_dir * y for x, y in zip(xs, ys)]
        p_min, p_max = min(proj), max(proj)

        # March along perpendicular axis at spacing_mm
        p = p_min
        while p <= p_max:
            # Scanline at perpendicular offset p
            # Find all intersections of this line with polygon edges
            intersections = self._scanline_intersect(pts, p, px_dir, py_dir, gx, gy)
            if len(intersections) >= 2:
                intersections.sort()
                for i in range(0, len(intersections) - 1, 2):
                    t1, t2 = intersections[i], intersections[i + 1]
                    # Convert parametric to xy
                    base_x = px_dir * p
                    base_y = py_dir * p
                    x1 = base_x + gx * t1
                    y1 = base_y + gy * t1
                    x2 = base_x + gx * t2
                    y2 = base_y + gy * t2
                    # Only include if within bounding box
                    if (x_min <= x1 <= x_max or x_min <= x2 <= x_max):
                        lines_out.append((x1, y1, x2, y2))
            p += spacing_mm

        return lines_out

    @staticmethod
    def _scanline_intersect(
        pts:    np.ndarray,
        p:      float,
        px_dir: float, py_dir: float,
        gx:     float, gy:     float,
    ) -> List[float]:
        """
        Find intersections of the scanline (at perpendicular offset p) with polygon.
        Returns list of parametric t values along grain direction.
        """
        n = len(pts)
        ts = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            # Project endpoints onto perpendicular axis
            pa = px_dir * ax + py_dir * ay
            pb = px_dir * bx + py_dir * by
            if (pa - p) * (pb - p) > 0:
                continue   # same side — no intersection
            if abs(pb - pa) < 1e-9:
                continue
            frac = (p - pa) / (pb - pa)
            ix = ax + frac * (bx - ax)
            iy = ay + frac * (by - ay)
            # Project intersection onto grain axis
            t = gx * ix + gy * iy
            ts.append(t)
        return ts


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def visualize_grain_and_check(
    extraction_result,
    bom,
    grain_angles:       Optional[Dict[str, float]] = None,
    output_svg_path:    Optional[str]              = None,
    warn_min_width_mm:  float = 6.0,
) -> Tuple[str, List[ThinSectionWarning]]:
    """
    One-call wrapper: generate grain SVG + thin-section warnings.

    Parameters
    ----------
    extraction_result : PhotoExtractionResult
    bom               : MaterialBOM (from Patch 08) for material assignments
    grain_angles      : {layer: degrees}  override per-layer grain direction
    output_svg_path   : where to write the grain SVG (None = auto-named)
    warn_min_width_mm : minimum safe section width

    Returns
    -------
    (grain_svg_path, thin_section_warnings)
    """
    if not extraction_result.output_svg:
        raise ValueError("extraction_result has no output_svg — run extract() first")

    # Build material map from BOM
    mat_map = {}
    for ln in bom.lines:
        mat_map[ln.layer] = ln.material

    # Build contours_by_layer from extraction_result
    contours_by_layer: Dict[str, List[np.ndarray]] = {}
    for ft, fc_list in extraction_result.features.items():
        layer = ft.value.upper()
        pts_list = [fc.points_mm for fc in fc_list if fc.points_mm is not None]
        if pts_list:
            contours_by_layer[layer] = pts_list

    # Default grain angles (0° = along body length for most materials)
    default_angles = {layer: 90.0 for layer in contours_by_layer}  # 90° = vertical grain
    if grain_angles:
        default_angles.update(grain_angles)

    # Thin-section check
    checker  = ThinSectionChecker(min_width_mm=warn_min_width_mm)
    warnings = checker.check(contours_by_layer, default_angles)

    # Grain visualization
    viz = GrainVisualizer(
        grain_angles = default_angles,
        material_map = mat_map,
    )
    grain_path = viz.add_to_svg(
        extraction_result.output_svg,
        contours_by_layer,
        output_path  = output_svg_path,
        thin_warnings = warnings,
    )

    return grain_path, warnings


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Construct a simple test body outline (rough guitar shape)
    body = np.array([
        [50, 0], [350, 0], [400, 50], [400, 300],
        [380, 380], [300, 450], [200, 470], [100, 450],
        [20, 380], [0, 300], [0, 50]
    ], dtype=np.float32)

    # Narrow cutaway section (Florentine-style)
    cutaway = np.array([
        [300, 0], [350, 0], [400, 50], [380, 60], [320, 20]
    ], dtype=np.float32)

    contours_by_layer = {
        "BODY_OUTLINE": [body],
        "BINDING":      [body],
    }

    grain_angles = {"BODY_OUTLINE": 90.0, "BINDING": 90.0}

    # Thin-section check
    checker = ThinSectionChecker(min_width_mm=6.0, sample_interval_mm=10.0)
    warnings = checker.check(contours_by_layer, grain_angles)

    print(f"Thin-section warnings: {len(warnings)}")
    for w in warnings[:5]:
        print(f"  [{w.severity.value.upper()}] {w.message}")

    # Grain visualization (write to a temp SVG then add grain)
    from xml.etree.ElementTree import Element, SubElement, ElementTree

    # Create minimal base SVG
    svg = Element("svg", xmlns="http://www.w3.org/2000/svg",
                   width="500mm", height="500mm", viewBox="0 0 500 500")
    g = SubElement(svg, "g", id="BODY_OUTLINE")
    pts_2d = body.reshape(-1, 2)
    d = "M " + " L ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts_2d) + " Z"
    SubElement(g, "path", d=d, fill="none", stroke="#000000",
               **{"stroke-width": "0.5"})

    base_path = "/tmp/grain_test_base.svg"
    with open(base_path, "wb") as f:
        ElementTree(svg).write(f, xml_declaration=True, encoding="utf-8")

    viz = GrainVisualizer(
        grain_angles = grain_angles,
        material_map = {"BODY_OUTLINE": "spruce_top", "BINDING": "abs_binding"},
    )
    out_path = viz.add_to_svg(
        base_path,
        {"BODY_OUTLINE": [body]},
        output_path   = "/tmp/grain_test_output.svg",
        thin_warnings = warnings,
    )
    print(f"\nGrain SVG written: {out_path}")

    # Count grain lines generated
    from xml.etree.ElementTree import parse as etp
    t = etp(out_path)
    grain_lines = t.findall(".//{http://www.w3.org/2000/svg}line")
    print(f"Grain lines in SVG: {len(grain_lines)}")
    print(f"Warning markers: {len(warnings)}")
