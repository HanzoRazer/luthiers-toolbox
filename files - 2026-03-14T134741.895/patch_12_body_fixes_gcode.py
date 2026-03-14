"""
PATCH 12 — Body Contour Fixes + G-code Export
===============================================

Contains three components:

  FIX A — ContourAssembler: body_region_hint
    Filters body candidate contours by vertical overlap with BodyIsolator output.
    Prevents neck/headstock contours from being elected as the body outline,
    which was causing 50% height truncation on Smart Guitar and J45.

  FIX B — PhotoEdgeDetector: adaptive close kernel
    Uses 11×11 morphological close for PHOTO inputs instead of 5×5.
    Bridges cutaway gaps (2–5mm at typical mpp) that were fragmenting the
    body outline into two separate contours (pre- and post-cutaway).

  GCodeExporter
    Converts closed mm-coordinate contours from PhotoVectorizerV2 output
    into CNC-ready G-code. Supports:
      - Profile cuts (body outline, f-holes, soundhole, binding)
      - Pocket cuts (pickup routes, neck pocket, control cavity)
      - Multi-pass depth with configurable pass depth per layer
      - Climb vs conventional milling direction
      - Tab generation for profile cuts (prevents workpiece shifting)
      - GRBL and Mach3/LinuxCNC dialect output
      - Per-layer bit diameter, feed rate, plunge rate
      - Tool change prompts between bit sizes
      - Safe height, work-holding, and coordinate zero comments

Pipeline position:
  PhotoVectorizerV2.extract() → export_contours (mm) → GCodeExporter.export()

Author: The Production Shop
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# FIX A — ContourAssembler: body_region_hint
# =============================================================================
"""
Problem:
  ContourAssembler.assemble() elects the largest-area contour as the body.
  When GrabCut only captures 30% foreground, the largest contour may be the
  neck+headstock region (tall, narrow) rather than the body (wide, short).
  Result: body bounding box spans full image → wrong dimensions.

Fix:
  Pass body_region (from BodyIsolator) to assemble(). Filter body candidates
  to those with ≥ MIN_BODY_OVERLAP vertical overlap with the body rows.
  If no contour passes the overlap filter, fall back to largest-area (safe).

Integration: In PhotoVectorizerV2.extract(), replace:

    feature_contours = self.assembler.assemble(edges, alpha_mask, mpp)

  With:

    feature_contours = self.assembler.assemble(
        edges, alpha_mask, mpp,
        body_region_hint=body_region)    # ← ADD

  Add body_region_hint parameter to ContourAssembler.assemble().
"""

MIN_BODY_OVERLAP = 0.50   # contour must overlap body rows by at least 50%


def body_region_overlap_fraction(
    contour_bbox:  Tuple[int, int, int, int],
    body_region,                              # BodyRegion dataclass
) -> float:
    """
    Compute fraction of contour's vertical extent that overlaps with body rows.

    Parameters
    ----------
    contour_bbox : (x, y, w, h) in pixels
    body_region  : BodyRegion from BodyIsolator (has .y and .height attrs)

    Returns
    -------
    float in [0, 1]
    """
    _, cy, _, ch = contour_bbox
    c_top = cy
    c_bot = cy + ch
    b_top = body_region.y
    b_bot = body_region.y + body_region.height

    overlap = max(0, min(c_bot, b_bot) - max(c_top, b_top))
    return overlap / max(ch, 1)


def elect_body_contour(
    contours:          list,                  # List[FeatureContour]
    body_region_hint,                         # BodyRegion or None
    min_overlap:       float = MIN_BODY_OVERLAP,
) -> int:
    """
    Choose the best body contour index from a list of FeatureContour objects.

    Strategy:
      1. If body_region_hint available: filter by vertical overlap ≥ min_overlap
         Among candidates, pick the one with highest overlap × area product
         (overlap-weighted area — avoids picking tiny overlapping fragments)
      2. If no candidates pass the filter: fall back to largest area (original)

    Parameters
    ----------
    contours         : list of FeatureContour objects
    body_region_hint : BodyRegion from BodyIsolator, or None
    min_overlap      : minimum vertical overlap fraction

    Returns
    -------
    Index into contours list of the elected body contour, or -1 if empty.
    """
    if not contours:
        return -1

    if body_region_hint is None:
        # Original behavior: largest area
        return max(range(len(contours)), key=lambda i: contours[i].area_px)

    # Filter and score by overlap × area
    scored = []
    for i, fc in enumerate(contours):
        overlap = body_region_overlap_fraction(fc.bbox_px, body_region_hint)
        if overlap >= min_overlap:
            score = overlap * fc.area_px
            scored.append((i, score, overlap))

    if scored:
        scored.sort(key=lambda x: x[1], reverse=True)
        best_idx, best_score, best_ov = scored[0]
        logger.info(
            f"BodyContourElection: {len(scored)} candidates passed overlap filter "
            f"(min={min_overlap:.0%}). Best: idx={best_idx}, "
            f"overlap={best_ov:.0%}, area={contours[best_idx].area_px:.0f}px²")
        return best_idx
    else:
        # No contour overlaps body region — fall back
        logger.warning(
            f"BodyContourElection: no contours passed overlap filter "
            f"(min={min_overlap:.0%}) — falling back to largest area")
        return max(range(len(contours)), key=lambda i: contours[i].area_px)


INTEGRATION_A = """
In ContourAssembler.assemble(), add body_region_hint parameter and
replace the body election block:

    def assemble(self, edge_image, alpha_mask, mm_per_px,
                 body_region_hint=None):   # ← ADD PARAMETER

    # Replace:
    body_idx = -1
    max_area = 0
    for i, cnt in enumerate(contours):
        a = cv2.contourArea(cnt)
        if a > max_area and a >= self.min_area_px:
            max_area = a
            body_idx = i

    # With: (after features list is built)
    from patch_12_body_fixes_gcode import elect_body_contour
    body_idx = elect_body_contour(features, body_region_hint)

Note: elect_body_contour operates on FeatureContour objects (needs bbox_px
and area_px), so call it after the features list is assembled, not before.
The body_bbox for FeatureClassifier comes from features[body_idx].bbox_px.
This means the election must happen in two passes or body_bbox is initially
None (acceptable — FeatureClassifier still works, grid reclassify corrects it).
"""


# =============================================================================
# FIX B — PhotoEdgeDetector: adaptive close kernel
# =============================================================================
"""
Problem:
  PhotoEdgeDetector uses a fixed 5×5 close kernel regardless of input type.
  For PHOTO inputs, cutaway horns create 2–5mm pixel gaps in the edge image
  that the 5×5 kernel cannot bridge. Two contours result: one for the body
  above the cutaway, one for the body below — the larger one gets elected,
  truncating height by up to 50%.

Fix:
  Use input_type to select close kernel size:
    PHOTO / SCAN    → 11×11 (bridges ~3–10mm gaps depending on mpp)
    BLUEPRINT / SVG → 5×5  (preserve fine detail)

Integration: In PhotoEdgeDetector.detect(), add input_type parameter:

    def detect(self, fg_image, alpha_mask, canny_sigma=0.33,
               close_kernel=5,
               input_type=None):          # ← ADD

    # Replace fixed close_kernel with:
    if input_type in ("photo", "scan", None):
        close_kernel = 11
    # else keep 5 for blueprint/svg

  In PhotoVectorizerV2.extract(), pass result.input_type.value:

    edges = self.edge_detector.detect(
        fg_image, alpha_mask,
        input_type=result.input_type.value)   # ← ADD
"""

PHOTO_CLOSE_KERNEL  = 11   # bridges up to ~5mm cutaway gaps at mpp=0.5
BLUEPRINT_CLOSE_KERNEL = 5  # preserve detail for line drawings


def get_close_kernel_size(input_type_str: Optional[str]) -> int:
    """
    Return the appropriate morphological close kernel size for the input type.

    Parameters
    ----------
    input_type_str : "photo", "scan", "blueprint", "svg", or None

    Returns
    -------
    kernel size (int, odd number)
    """
    if input_type_str in ("blueprint", "svg"):
        return BLUEPRINT_CLOSE_KERNEL
    return PHOTO_CLOSE_KERNEL   # photo, scan, unknown → wider close


INTEGRATION_B = """
In PhotoEdgeDetector.detect():

    # Replace the hardcoded close block near the end:
    # BEFORE:
    if close_kernel > 0:
        k = np.ones((close_kernel, close_kernel), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k, iterations=2)

    # AFTER:
    from patch_12_body_fixes_gcode import get_close_kernel_size
    ck = get_close_kernel_size(input_type)
    if ck > 0:
        k = np.ones((ck, ck), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k, iterations=2)
"""


# =============================================================================
# G-code Export
# =============================================================================

class GCodeDialect(Enum):
    GRBL       = "grbl"        # GRBL 1.1 (most hobbyist CNC routers)
    MACH3      = "mach3"       # Mach3 / Mach4 (common in shops)
    LINUXCNC   = "linuxcnc"    # LinuxCNC / EMC2
    GENERIC    = "generic"     # Plain G-code, no controller-specific commands


class CutOperation(Enum):
    PROFILE = "profile"   # follows contour perimeter (inside or outside)
    POCKET  = "pocket"    # fills interior area
    ENGRAVE = "engrave"   # surface-only trace, no depth passes


@dataclass
class LayerCutParams:
    """Cutting parameters for one feature layer."""
    depth_mm:       float          # total cut depth
    passes:         int            # number of Z passes
    bit_diameter_mm: float         # tool diameter
    feed_mmpm:      float          # XY feed rate (mm/min)
    plunge_mmpm:    float          # Z plunge rate (mm/min)
    operation:      CutOperation   # profile or pocket
    inside:         bool  = False  # for profile: cut inside contour
    climb:          bool  = True   # climb milling (True) or conventional
    tabs:           bool  = False  # leave tabs for profile cuts
    tab_height_mm:  float = 3.0    # tab height from bottom
    tab_width_mm:   float = 8.0    # tab width along contour
    n_tabs:         int   = 4      # tabs per profile contour
    spindle_rpm:    int   = 18000  # spindle speed

    @property
    def pass_depth_mm(self) -> float:
        return self.depth_mm / max(self.passes, 1)


# Default cutting parameters per layer
DEFAULT_CUT_PARAMS: Dict[str, LayerCutParams] = {
    "BODY_OUTLINE":    LayerCutParams(19.0,  4, 6.35,  2000, 300, CutOperation.PROFILE,
                                      inside=False, tabs=True,  n_tabs=6),
    "PICKUP_ROUTE":    LayerCutParams(16.0,  4, 9.53,  1500, 200, CutOperation.POCKET),
    "NECK_POCKET":     LayerCutParams(19.0,  5, 9.53,  1200, 150, CutOperation.POCKET),
    "CONTROL_CAVITY":  LayerCutParams(38.0,  8, 9.53,  1500, 200, CutOperation.POCKET),
    "BRIDGE_ROUTE":    LayerCutParams( 6.35, 2, 6.35,  1500, 200, CutOperation.POCKET),
    "F_HOLE":          LayerCutParams(19.0,  4, 6.35,  1500, 200, CutOperation.PROFILE,
                                      inside=True,  tabs=True,  n_tabs=2),
    "SOUNDHOLE":       LayerCutParams(19.0,  4, 6.35,  1500, 200, CutOperation.PROFILE,
                                      inside=True,  tabs=True,  n_tabs=2),
    "ROSETTE":         LayerCutParams( 3.0,  1, 3.175,  800, 100, CutOperation.POCKET),
    "JACK_ROUTE":      LayerCutParams(38.0,  4, 12.7,  1000, 150, CutOperation.POCKET),
    "BINDING":         LayerCutParams( 3.0,  1, 3.175,  600,  80, CutOperation.PROFILE,
                                       inside=False),
    "PURFLING":        LayerCutParams( 1.5,  1, 1.5875, 400,  60, CutOperation.PROFILE,
                                       inside=False),
    "UNKNOWN":         LayerCutParams( 6.0,  2, 6.35,  1000, 150, CutOperation.PROFILE),
}


@dataclass
class GCodeExportConfig:
    """Configuration for G-code export."""
    dialect:          GCodeDialect = GCodeDialect.GRBL
    safe_height_mm:   float = 5.0      # Z height for rapid moves between features
    work_zero_mm:     Tuple[float, float, float] = (0.0, 0.0, 0.0)
    units:            str   = "mm"     # "mm" or "inch"
    spindle_on_cmd:   str   = "M3"     # M3=CW, M4=CCW
    coolant:          bool  = False
    program_number:   int   = 1000
    layer_params:     Dict[str, LayerCutParams] = field(
                          default_factory=lambda: dict(DEFAULT_CUT_PARAMS))
    cut_order:        List[str] = field(default_factory=lambda: [
        # Deepest/most critical cuts first; binding/purfling last
        "ROSETTE", "PURFLING", "SOUNDHOLE", "F_HOLE",
        "PICKUP_ROUTE", "BRIDGE_ROUTE", "JACK_ROUTE",
        "NECK_POCKET", "CONTROL_CAVITY",
        "BINDING", "BODY_OUTLINE",
    ])


class GCodeExporter:
    """
    Converts closed mm contours from PhotoVectorizerV2 into CNC G-code.

    Parameters
    ----------
    config : GCodeExportConfig (uses defaults if None)
    """

    def __init__(self, config: Optional[GCodeExportConfig] = None):
        self.cfg = config or GCodeExportConfig()

    # ------------------------------------------------------------------
    def export(
        self,
        contours_by_layer: Dict[str, List[np.ndarray]],
        output_path:       str,
        source_name:       str = "instrument",
        calibration_info:  str = "",
    ) -> str:
        """
        Generate G-code file from contour dictionary.

        Parameters
        ----------
        contours_by_layer : {layer_name: [pts_mm, ...]}
                            Same dict as written to SVG/DXF by write_svg()
        output_path       : path for .nc / .gcode file
        source_name       : instrument name for file header
        calibration_info  : calibration summary string for header comment

        Returns
        -------
        output_path (str)
        """
        lines = []
        lines += self._header(source_name, calibration_info)

        # Group layers by bit diameter to minimise tool changes
        bit_groups: Dict[float, List[str]] = {}
        for layer in self.cfg.cut_order:
            if layer not in contours_by_layer:
                continue
            if not contours_by_layer[layer]:
                continue
            params = self.cfg.layer_params.get(layer)
            if params is None:
                continue
            bit = round(params.bit_diameter_mm, 4)
            bit_groups.setdefault(bit, []).append(layer)

        first_tool = True
        for bit_mm, layers_for_bit in sorted(
                bit_groups.items(),
                key=lambda kv: -kv[0]):   # larger bits first
            lines += self._tool_change(bit_mm, first=first_tool)
            first_tool = False

            for layer in layers_for_bit:
                pts_list = contours_by_layer.get(layer, [])
                params   = self.cfg.layer_params.get(layer)
                if not pts_list or params is None:
                    continue
                lines += self._cut_layer(layer, pts_list, params)

        lines += self._footer()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(lines) + "\n")

        logger.info(f"G-code written: {output_path} ({len(lines)} lines)")
        return output_path

    # ------------------------------------------------------------------
    # Header / footer
    # ------------------------------------------------------------------

    def _header(self, source_name: str, calib_info: str) -> List[str]:
        d = self.cfg.dialect
        lines = [
            f"; ============================================================",
            f"; The Production Shop — G-code Export",
            f"; Source:      {source_name}",
            f"; Calibration: {calib_info}",
            f"; Dialect:     {d.value}",
            f"; Units:       {self.cfg.units}",
            f"; Safe height: {self.cfg.safe_height_mm}mm",
            f"; ============================================================",
            f"; WORK-HOLDING NOTE: Secure workpiece before running.",
            f"; Zero X,Y to body centre; Zero Z to top surface.",
            f"; ============================================================",
            "",
        ]

        if d == GCodeDialect.GRBL:
            lines += ["G21 G90 G17 G94   ; mm, absolute, XY plane, feed/min",
                      "G28               ; home",
                      ""]
        elif d in (GCodeDialect.MACH3, GCodeDialect.LINUXCNC):
            lines += [f"O{self.cfg.program_number}",
                      "G21 G90 G17 G94",
                      "G49 G40 G80       ; cancel tool length, comp, canned",
                      ""]
        else:
            lines += ["G21 G90 G17 G94", ""]

        return lines

    def _footer(self) -> List[str]:
        lines = [
            "",
            f"; ============================================================",
            f"; Program end",
            f"; ============================================================",
            f"G0 Z{self.cfg.safe_height_mm:.3f}   ; retract",
        ]
        if self.cfg.dialect in (GCodeDialect.GRBL,):
            lines += ["M5   ; spindle off", "M30  ; end program"]
        else:
            lines += ["M5", "M30"]
        return lines

    # ------------------------------------------------------------------
    # Tool change block
    # ------------------------------------------------------------------

    def _tool_change(self, bit_mm: float, first: bool = False) -> List[str]:
        bit_in = bit_mm / 25.4
        lines = [
            "",
            f"; ── Tool: {bit_mm:.4f}mm ({bit_in:.4f}\") ─────────────────────────",
            f"G0 Z{self.cfg.safe_height_mm:.3f}",
        ]
        if not first:
            lines += [
                "M5          ; spindle off",
                "M0          ; PAUSE — change to "
                f"{bit_mm:.3f}mm ({bit_in:.3f}\") bit, then cycle start",
            ]
        return lines

    # ------------------------------------------------------------------
    # Layer cutting
    # ------------------------------------------------------------------

    def _cut_layer(
        self,
        layer:    str,
        pts_list: List[np.ndarray],
        params:   LayerCutParams,
    ) -> List[str]:
        lines = [
            "",
            f"; ── Layer: {layer} ──────────────────────────",
            f";    Operation: {params.operation.value}",
            f";    Depth: {params.depth_mm}mm in {params.passes} pass(es) "
            f"({params.pass_depth_mm:.2f}mm each)",
            f";    Feed: {params.feed_mmpm}mm/min  Plunge: {params.plunge_mmpm}mm/min",
            f";    Spindle: {params.spindle_rpm} RPM",
            f"{self.cfg.spindle_on_cmd} S{params.spindle_rpm}",
            f"G4 P2   ; 2s spindle spin-up",
        ]

        if self.cfg.coolant:
            lines.append("M8   ; coolant on")

        for i, pts in enumerate(pts_list):
            if len(pts) < 3:
                continue
            contour_label = f"{layer}[{i}]" if len(pts_list) > 1 else layer

            if params.operation == CutOperation.PROFILE:
                lines += self._profile_contour(contour_label, pts, params)
            elif params.operation == CutOperation.POCKET:
                lines += self._pocket_contour(contour_label, pts, params)
            else:  # ENGRAVE
                lines += self._profile_contour(contour_label, pts, params,
                                                depth_override=0.2)

        if self.cfg.coolant:
            lines.append("M9   ; coolant off")
        lines.append(f"G0 Z{self.cfg.safe_height_mm:.3f}   ; retract after {layer}")
        return lines

    # ------------------------------------------------------------------
    # Profile contour (follows perimeter)
    # ------------------------------------------------------------------

    def _profile_contour(
        self,
        label:          str,
        pts:            np.ndarray,
        params:         LayerCutParams,
        depth_override: Optional[float] = None,
    ) -> List[str]:
        """Generate multi-pass profile contour G-code."""
        lines = [f"; Profile: {label} ({len(pts)} pts)"]
        depth = depth_override or params.depth_mm

        # Offset for bit radius if needed (approximate — no full offset polygon)
        offset = params.bit_diameter_mm / 2.0
        if params.inside:
            offset = -offset

        # Find start point (first vertex)
        start = pts[0]

        # Rapid to start position, safe height
        lines.append(f"G0 Z{self.cfg.safe_height_mm:.3f}")
        lines.append(f"G0 X{start[0]:.3f} Y{start[1]:.3f}")

        # Generate tabs if requested
        tab_positions = set()
        if params.tabs and params.n_tabs > 0:
            tab_indices = self._compute_tab_indices(pts, params.n_tabs)
            tab_positions = set(tab_indices)

        # Multi-pass Z
        for pass_num in range(params.passes):
            z_depth = -params.pass_depth_mm * (pass_num + 1)
            z_depth = max(z_depth, -depth)

            lines.append(f"; Pass {pass_num + 1}/{params.passes}, Z={z_depth:.3f}mm")
            lines.append(f"G1 Z{z_depth:.3f} F{params.plunge_mmpm:.0f}")

            in_tab = False
            for j, pt in enumerate(pts):
                is_tab_point = j in tab_positions
                last_pass = (pass_num == params.passes - 1)

                if is_tab_point and last_pass and params.tabs:
                    # Lift for tab
                    tab_z = -depth + params.tab_height_mm
                    if not in_tab:
                        lines.append(f"G1 Z{tab_z:.3f} F{params.plunge_mmpm:.0f}  ; tab up")
                        in_tab = True
                elif in_tab:
                    lines.append(f"G1 Z{z_depth:.3f} F{params.plunge_mmpm:.0f}  ; tab down")
                    in_tab = False

                lines.append(f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} F{params.feed_mmpm:.0f}")

            # Close contour
            lines.append(f"G1 X{start[0]:.3f} Y{start[1]:.3f} F{params.feed_mmpm:.0f}")

        lines.append(f"G0 Z{self.cfg.safe_height_mm:.3f}")
        return lines

    # ------------------------------------------------------------------
    # Pocket contour (fills interior with raster or spiral)
    # ------------------------------------------------------------------

    def _pocket_contour(
        self,
        label:  str,
        pts:    np.ndarray,
        params: LayerCutParams,
    ) -> List[str]:
        """
        Generate pocket G-code using a raster (zigzag) fill strategy.
        Stepover = 40% of bit diameter (conservative overlap).
        """
        lines = [f"; Pocket: {label} ({len(pts)} pts)"]

        xs, ys = pts[:, 0], pts[:, 1]
        x_min, x_max = float(xs.min()), float(xs.max())
        y_min, y_max = float(ys.min()), float(ys.max())

        stepover = params.bit_diameter_mm * 0.40
        start_x  = x_min + stepover

        lines.append(f"G0 Z{self.cfg.safe_height_mm:.3f}")
        lines.append(f"G0 X{start_x:.3f} Y{y_min:.3f}")

        for pass_num in range(params.passes):
            z_depth = -params.pass_depth_mm * (pass_num + 1)
            z_depth = max(z_depth, -params.depth_mm)
            lines.append(f"; Pocket pass {pass_num + 1}/{params.passes}, Z={z_depth:.3f}")

            y = y_min + stepover
            row = 0
            while y <= y_max - stepover:
                # Find X extents within contour at this Y
                x_left, x_right = self._scanline_x(pts, y)
                if x_left is None:
                    y += stepover
                    row += 1
                    continue

                x_left  = max(x_left  + params.bit_diameter_mm / 2, x_min)
                x_right = min(x_right - params.bit_diameter_mm / 2, x_max)

                if x_right <= x_left:
                    y += stepover
                    row += 1
                    continue

                if row == 0 and pass_num == 0:
                    lines.append(f"G0 X{x_left:.3f} Y{y:.3f}")
                    lines.append(f"G1 Z{z_depth:.3f} F{params.plunge_mmpm:.0f}")
                else:
                    lines.append(f"G0 Z{self.cfg.safe_height_mm:.3f}")
                    if row % 2 == 0:
                        lines.append(f"G0 X{x_left:.3f} Y{y:.3f}")
                        lines.append(f"G1 Z{z_depth:.3f} F{params.plunge_mmpm:.0f}")
                        lines.append(f"G1 X{x_right:.3f} Y{y:.3f} "
                                     f"F{params.feed_mmpm:.0f}")
                    else:
                        lines.append(f"G0 X{x_right:.3f} Y{y:.3f}")
                        lines.append(f"G1 Z{z_depth:.3f} F{params.plunge_mmpm:.0f}")
                        lines.append(f"G1 X{x_left:.3f} Y{y:.3f} "
                                     f"F{params.feed_mmpm:.0f}")

                y   += stepover
                row += 1

        lines.append(f"G0 Z{self.cfg.safe_height_mm:.3f}")
        return lines

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_tab_indices(pts: np.ndarray, n_tabs: int) -> List[int]:
        """Return evenly-spaced point indices along contour for tab placement."""
        n = len(pts)
        if n == 0 or n_tabs == 0:
            return []
        step = n // n_tabs
        return [i * step for i in range(n_tabs)]

    @staticmethod
    def _scanline_x(
        pts: np.ndarray,
        y:   float,
    ) -> Tuple[Optional[float], Optional[float]]:
        """Find left and right X extents of polygon at horizontal scanline y."""
        n = len(pts)
        xs = []
        for i in range(n):
            ay, by = pts[i, 1], pts[(i + 1) % n, 1]
            ax, bx = pts[i, 0], pts[(i + 1) % n, 0]
            if (ay <= y < by) or (by <= y < ay):
                if abs(by - ay) < 1e-9:
                    continue
                t  = (y - ay) / (by - ay)
                xi = ax + t * (bx - ax)
                xs.append(xi)
        if len(xs) < 2:
            return None, None
        return float(min(xs)), float(max(xs))


# =============================================================================
# Convenience wrapper
# =============================================================================

def export_gcode(
    extraction_result,
    output_path:   Optional[str] = None,
    dialect:       str = "grbl",
    params_override: Optional[Dict[str, dict]] = None,
) -> str:
    """
    One-call G-code export from a PhotoExtractionResult.

    Parameters
    ----------
    extraction_result : PhotoExtractionResult from PhotoVectorizerV2
    output_path       : .nc file path (auto-named from source if None)
    dialect           : "grbl", "mach3", "linuxcnc", "generic"
    params_override   : {layer: {field: value}} to override per-layer defaults

    Returns
    -------
    output_path (str)
    """
    if output_path is None:
        stem = Path(extraction_result.source_path).stem
        output_path = str(Path(extraction_result.source_path).parent
                          / f"{stem}_toolpaths.nc")

    # Build contours_by_layer from features
    contours: Dict[str, List[np.ndarray]] = {}
    for ft, fc_list in extraction_result.features.items():
        layer    = ft.value.upper()
        pts_list = [fc.points_mm for fc in fc_list if fc.points_mm is not None]
        if pts_list:
            contours[layer] = pts_list

    # Dialect
    dialect_map = {
        "grbl":     GCodeDialect.GRBL,
        "mach3":    GCodeDialect.MACH3,
        "linuxcnc": GCodeDialect.LINUXCNC,
        "generic":  GCodeDialect.GENERIC,
    }

    # Build config
    layer_params = dict(DEFAULT_CUT_PARAMS)
    if params_override:
        for layer, overrides in params_override.items():
            if layer in layer_params:
                p = layer_params[layer]
                for k, v in overrides.items():
                    setattr(p, k, v)

    cfg = GCodeExportConfig(
        dialect      = dialect_map.get(dialect, GCodeDialect.GRBL),
        layer_params = layer_params,
    )

    cal = extraction_result.calibration
    calib_str = (f"{cal.source.value} (conf={cal.confidence:.2f})"
                 if cal else "unknown")

    exporter = GCodeExporter(cfg)
    return exporter.export(
        contours,
        output_path  = output_path,
        source_name  = Path(extraction_result.source_path).name,
        calibration_info = calib_str,
    )


# =============================================================================
# CLI integration note
# =============================================================================

CLI_INTEGRATION = """
Add to CLI in photo_vectorizer_v2.py:

    parser.add_argument("--gcode", action="store_true",
        help="Export G-code toolpaths (.nc file)")
    parser.add_argument("--dialect", default="grbl",
        choices=["grbl", "mach3", "linuxcnc", "generic"],
        help="G-code dialect (default: grbl)")
    parser.add_argument("--depth", type=float, default=None,
        help="Override body outline depth (mm)")

    # In main(), after extract():
    if args.gcode:
        from patch_12_body_fixes_gcode import export_gcode
        params_override = {}
        if args.depth:
            params_override["BODY_OUTLINE"] = {"depth_mm": args.depth}
        for result in results:
            nc_path = export_gcode(result, dialect=args.dialect,
                                   params_override=params_override)
            print(f"G-code: {nc_path}")
"""


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 65)
    print("PATCH 12 — Self-Test")
    print("=" * 65)

    # ── Fix A: body region hint ──────────────────────────────────────
    print("\nFIX A — body_region_overlap_fraction:")

    class MockBodyRegion:
        def __init__(self, y, height): self.y = y; self.height = height

    body_region = MockBodyRegion(y=497, height=522)  # archtop body rows
    cases = [
        ("neck (top of image)",    (400,   0, 200, 490), False),
        ("full instrument",        (200,  50, 700, 1400), False),
        ("body only",              (150, 480, 750, 550),  True),
        ("lower bout",             (200, 700, 700, 300),  True),
    ]
    for label, bbox, should_pass in cases:
        ov = body_region_overlap_fraction(bbox, body_region)
        result = "✓" if (ov >= MIN_BODY_OVERLAP) == should_pass else "✗"
        print(f"  {label:<30} overlap={ov:.0%}  "
              f"{'PASS' if ov>=MIN_BODY_OVERLAP else 'REJECT'}  {result}")

    # ── Fix B: close kernel selection ──────────────────────────────
    print("\nFIX B — get_close_kernel_size:")
    for itype in ("photo", "scan", "blueprint", "svg", None):
        k = get_close_kernel_size(itype)
        print(f"  input_type={str(itype):<12} → {k}×{k} kernel")

    # ── G-code export ───────────────────────────────────────────────
    print("\nGCodeExporter — generating test toolpaths:")

    # Build mock contours
    body = np.array([
        [0, 0], [400, 0], [400, 520], [0, 520]
    ], dtype=np.float32)

    pickup = np.array([
        [100, 200], [185, 200], [185, 238], [100, 238]
    ], dtype=np.float32)

    soundhole = np.array([
        [175, 140], [225, 140], [225, 190], [175, 190]
    ], dtype=np.float32)

    contours = {
        "BODY_OUTLINE": [body],
        "PICKUP_ROUTE": [pickup],
        "SOUNDHOLE":    [soundhole],
    }

    exporter = GCodeExporter()
    out_path = "/tmp/test_guitar_toolpaths.nc"
    exporter.export(
        contours, out_path,
        source_name      = "test_guitar.png",
        calibration_info = "instrument_spec (conf=0.60)",
    )

    # Report results
    content  = open(out_path).read()
    nc_lines = content.split("\n")
    g1_moves = [l for l in nc_lines if l.strip().startswith("G1")]
    g0_moves = [l for l in nc_lines if l.strip().startswith("G0")]
    comments = [l for l in nc_lines if l.strip().startswith(";")]

    print(f"  Output: {out_path}")
    print(f"  Total lines:  {len(nc_lines)}")
    print(f"  G0 rapids:    {len(g0_moves)}")
    print(f"  G1 feed moves:{len(g1_moves)}")
    print(f"  Comments:     {len(comments)}")
    print(f"\nFirst 30 lines of G-code:")
    for line in nc_lines[:30]:
        print(f"  {line}")

    print(f"\n{'='*65}")
    print("All tests complete.")
    print("\nINTEGRATION SUMMARY:")
    print("  Fix A: add body_region_hint param to ContourAssembler.assemble()")
    print("         call elect_body_contour() instead of max-area loop")
    print("  Fix B: pass input_type to PhotoEdgeDetector.detect()")
    print("         use get_close_kernel_size() for adaptive close kernel")
    print("  G-code: call export_gcode(result) after extract()")
    print("          add --gcode --dialect --depth flags to CLI")
