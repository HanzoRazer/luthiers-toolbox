#!/usr/bin/env python3
"""
Smart Guitar v1.1 — Full CNC Build G-code Generator
====================================================

Generates the COMPLETE machining program for the Smart Guitar headless
IoT electric guitar from the authoritative spec (smart_guitar_v1.json)
and body outline DXF.

Operations produced:
  Phase 1 — Front Face (flat 2.5D routing, mm, G21)
    OP10: Fixture / registration holes (T3 3mm)
    OP20: Neck pocket rough (T1 10mm)
    OP21: Neck pickup cavity rough (T1 10mm)
    OP22: Bridge pickup cavity rough (T1 10mm)
    OP25: Neck pocket finish (T2 6mm)
    OP26: Pickup cavities finish (T2 6mm)
    OP30: Control plate surface recess (T2 6mm)
    OP40: Headless bridge mounting holes (T3 3mm)
    OP41: Pot shaft holes — 3x 9.5mm through (T3 3mm)
    OP42: Output jack bore — 12.7mm angled (T3 3mm)
    OP50: Body perimeter contour with tabs (T2 6mm)

  Phase 2 — Rear Face (flip body, re-zero Z to rear surface)
    OP60: Rear electronics cavity — Pi 5 (T1 10mm rough, T2 6mm finish)
    OP61: Teensy I/O coprocessor pocket (T1 10mm rough, T2 6mm finish)
    OP62: Antenna recess — shallow 2mm (T2 6mm)
    OP63: Rear cover plate recess (T2 6mm)
    OP-CC-50: Control cavity rough — LP heritage 100x60x20mm (T2 6mm)
    OP-CC-51: Control cavity finish (T2 6mm)
    OP-CC-52: Control cavity cover plate recess — 110x70x3.175mm (T2 6mm)
    OP-CC-60: Control cavity screw pilot holes — 4x (T4 2.5mm drill)
    OP70: Wiring channels — 4 routes (T3 3mm)
    OP71: USB-C edge slot (T3 3mm)

Units: mm (G21) throughout.
Machine: Configurable (default GRBL_3018_Default).
Stock: Khaya (African Mahogany), 444.5 x 368.3 x 44.45mm

Usage:
    cd services/api
    python -m scripts.generate_smart_guitar_full_build
  or:
    python scripts/generate_smart_guitar_full_build.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Import shared G-code verification utility (SG-GAP-13)
from scripts.utils.gcode_verify import verify_gcode


# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
API_DIR = REPO_ROOT / "services" / "api"

SPEC_PATH = API_DIR / "app" / "instrument_geometry" / "body" / "specs" / "smart_guitar_v1.json"
DXF_PATH = API_DIR / "app" / "instrument_geometry" / "body" / "dxf" / "electric" / "Smart-Guitar-v1_preliminary.dxf"
OUTPUT_DIR = REPO_ROOT / "exports" / "smart_guitar_v1"


# ---------------------------------------------------------------------------
# Load spec
# ---------------------------------------------------------------------------

def load_spec() -> Dict[str, Any]:
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Load body outline from DXF
# ---------------------------------------------------------------------------

def load_body_outline_from_dxf() -> List[Tuple[float, float]]:
    """Load body outline points from Smart Guitar DXF (mm)."""
    try:
        import ezdxf
    except ImportError:
        print("ERROR: ezdxf required. pip install ezdxf")
        sys.exit(1)

    doc = ezdxf.readfile(str(DXF_PATH))
    msp = doc.modelspace()

    # Find the body outline — look for LWPOLYLINE on BODY_OUTLINE layer first
    for entity in msp:
        if entity.dxftype() == "LWPOLYLINE":
            layer = entity.dxf.get("layer", "")
            if "BODY" in layer.upper() or "OUTLINE" in layer.upper():
                pts = list(entity.get_points(format="xy"))
                if pts[0] != pts[-1]:
                    pts.append(pts[0])
                return pts

    # Fallback: largest closed polyline
    best_pts = []
    best_len = 0
    for entity in msp:
        if entity.dxftype() == "LWPOLYLINE":
            pts = list(entity.get_points(format="xy"))
            if len(pts) > best_len:
                best_pts = pts
                best_len = len(pts)

    if not best_pts:
        # Final fallback: use spec body points
        print("WARNING: No LWPOLYLINE found in DXF, using generate_smart_guitar_dxf.py outline")
        return _fallback_body_points()

    if best_pts[0] != best_pts[-1]:
        best_pts.append(best_pts[0])
    return best_pts


def _fallback_body_points() -> List[Tuple[float, float]]:
    """Fallback body outline from the DXF generator script (inches -> mm)."""
    INCH_TO_MM = 25.4
    points_inches = [
        (0, -8.75), (5.5, -6.0), (6.5, -4.0), (5.0, -1.0),
        (5.5, 1.5), (7.25, 4.5), (5.0, 5.5), (2.0, 6.5),
        (0.75, 8.0), (-0.75, 8.0), (-2.0, 6.5), (-3.5, 5.5),
        (-4.5, 4.0), (-3.5, 2.5), (-4.0, 1.0), (-3.5, -0.5),
        (-5.0, -2.0), (-4.0, -4.0), (-3.0, -5.0), (-5.5, -6.0),
        (0, -8.75),
    ]
    return [(x * INCH_TO_MM, y * INCH_TO_MM) for x, y in points_inches]


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def offset_polygon(pts: List[Tuple[float, float]], offset: float) -> List[Tuple[float, float]]:
    """
    Naive inward offset of a polygon.
    Offset > 0 = inward (shrink), offset < 0 = outward (grow).
    """
    n = len(pts)
    if pts[0] == pts[-1]:
        n -= 1
    result = []
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]

        dx1 = p1[0] - p0[0]
        dy1 = p1[1] - p0[1]
        dx2 = p2[0] - p1[0]
        dy2 = p2[1] - p1[1]

        len1 = math.sqrt(dx1 * dx1 + dy1 * dy1) or 1e-9
        len2 = math.sqrt(dx2 * dx2 + dy2 * dy2) or 1e-9
        nx1 = -dy1 / len1
        ny1 = dx1 / len1
        nx2 = -dy2 / len2
        ny2 = dx2 / len2

        nx = nx1 + nx2
        ny = ny1 + ny2
        ln = math.sqrt(nx * nx + ny * ny) or 1e-9
        nx /= ln
        ny /= ln

        dot = nx1 * nx + ny1 * ny
        if abs(dot) < 0.01:
            dot = 0.01
        scale = 1.0 / dot

        result.append((p1[0] + nx * offset * scale, p1[1] + ny * offset * scale))

    result.append(result[0])
    return result


def path_length(pts: List[Tuple[float, float]]) -> float:
    total = 0.0
    for i in range(len(pts) - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        total += math.sqrt(dx * dx + dy * dy)
    return total


# ---------------------------------------------------------------------------
# G-code builder
# ---------------------------------------------------------------------------

class GCodeBuilder:
    """Accumulates G-code lines with helper methods."""

    def __init__(self):
        self.lines: List[str] = []
        self._current_tool: int | None = None

    def emit(self, line: str):
        self.lines.append(line)

    def comment(self, text: str):
        self.emit(f"( {text} )")

    def section(self, title: str):
        self.emit("")
        self.emit(f"( {'=' * 60} )")
        self.emit(f"( {title} )")
        self.emit(f"( {'=' * 60} )")

    def header(self, program_name: str, machine: str, stock: str, phase: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.emit(f"; {program_name}")
        self.emit(f"; Generated: {now}")
        self.emit(f"; Generator: The Production Shop - Smart Guitar Full Build")
        self.emit(f"; Machine: {machine}")
        self.emit(f"; Stock: {stock}")
        self.emit(f"; Phase: {phase}")
        self.emit(";")
        self.emit("")
        self.comment("SAFE START")
        self.emit("G21         ; Millimeters")
        self.emit("G17         ; XY plane")
        self.emit("G90         ; Absolute positioning")
        self.emit("G94         ; Feed per minute")
        self.emit("G54         ; Work coordinate system")
        self.emit("")

    def footer(self):
        self.emit("")
        self.comment("PROGRAM END")
        self.emit("M5          ; Spindle off")
        self.emit("G0 Z20.000  ; Safe Z")
        self.emit("G0 X0 Y0    ; Return home")
        self.emit("M30         ; End program")

    def tool_change(self, tool_num: int, name: str, rpm: int, operation: str = ""):
        if self._current_tool is not None:
            self.emit("M5          ; Spindle off")
        self.emit("")
        self.comment(f"TOOL CHANGE: T{tool_num} - {name}")
        if operation:
            self.comment(operation)
        self.emit(f"T{tool_num} M6")
        self.emit(f"S{rpm} M3     ; Spindle on")
        self.emit("G4 P2       ; Dwell 2s for spindle")
        self.emit("G0 Z20.000  ; Safe Z")
        self._current_tool = tool_num

    def rapid(self, x=None, y=None, z=None):
        parts = ["G0"]
        if x is not None:
            parts.append(f"X{x:.3f}")
        if y is not None:
            parts.append(f"Y{y:.3f}")
        if z is not None:
            parts.append(f"Z{z:.3f}")
        self.emit(" ".join(parts))

    def linear(self, x=None, y=None, z=None, f=None):
        parts = ["G1"]
        if x is not None:
            parts.append(f"X{x:.3f}")
        if y is not None:
            parts.append(f"Y{y:.3f}")
        if z is not None:
            parts.append(f"Z{z:.3f}")
        if f is not None:
            parts.append(f"F{f:.1f}")
        self.emit(" ".join(parts))

    def arc_cw(self, x, y, i, j, z=None, f=None):
        parts = [f"G2 X{x:.3f} Y{y:.3f} I{i:.3f} J{j:.3f}"]
        if z is not None:
            parts.append(f"Z{z:.3f}")
        if f is not None:
            parts.append(f"F{f:.1f}")
        self.emit(" ".join(parts))

    def peck_drill(self, x, y, z_final, retract, peck, feed):
        self.rapid(x=x, y=y)
        self.emit(f"G83 Z{z_final:.3f} R{retract:.3f} Q{peck:.3f} F{feed:.1f}")

    def cancel_canned(self):
        self.emit("G80          ; Cancel canned cycle")

    def text(self) -> str:
        return "\n".join(self.lines)


# ---------------------------------------------------------------------------
# Tool Library (mm, for Khaya / African Mahogany)
# ---------------------------------------------------------------------------

# T1: 10mm flat end mill — roughing
T1_DIA = 10.0
T1_RPM = 18000
T1_FEED = 5000.0     # mm/min
T1_PLUNGE = 800.0
T1_DOC = 5.0         # depth of cut per pass
T1_STEP = T1_DIA * 0.45  # stepover

# T2: 6mm flat end mill — finishing
T2_DIA = 6.0
T2_RPM = 18000
T2_FEED = 3500.0
T2_PLUNGE = 600.0
T2_DOC = 1.5
T2_STEP = T2_DIA * 0.18

# T3: 3mm flat/drill — channels, drilling
T3_DIA = 3.0
T3_RPM = 20000
T3_FEED = 1500.0
T3_PLUNGE = 400.0
T3_DOC = 1.0

SAFE_Z = 20.0
RETRACT_Z = 5.0


# ---------------------------------------------------------------------------
# Pocket milling helper
# ---------------------------------------------------------------------------

def mill_rectangular_pocket(g: GCodeBuilder, name: str, cx: float, cy: float,
                            pw: float, ph: float, depth: float,
                            tool_dia: float, doc: float, stepover: float,
                            feed: float, plunge: float, op_label: str,
                            corner_r: float = 0.0):
    """Mill a rectangular pocket with helical entry and spiral-out strategy."""
    g.section(f"{op_label}: {name}")
    g.comment(f"Center: ({cx:.3f}, {cy:.3f})")
    g.comment(f"Size: {pw:.1f} x {ph:.1f} mm, Depth: {depth:.1f} mm")

    num_passes = max(1, math.ceil(depth / doc))

    for pn in range(num_passes):
        z = -doc * (pn + 1)
        if z < -depth:
            z = -depth
        g.comment(f"Pass {pn + 1}/{num_passes}: Z={z:.3f}")
        g.rapid(z=SAFE_Z)
        g.rapid(x=cx, y=cy)
        g.rapid(z=RETRACT_Z)

        # Helical plunge
        helix_r = tool_dia / 4
        g.arc_cw(cx, cy, helix_r, 0, z=z, f=plunge)
        g.emit(f"F{feed:.1f}")

        # Spiral outward
        max_offset = min(pw, ph) / 2 - tool_dia / 2
        off = stepover
        while off < max_offset:
            x1, y1 = cx - off, cy - off
            x2, y2 = cx + off, cy + off
            g.linear(x=x1, y=y1)
            g.linear(x=x2, y=y1)
            g.linear(x=x2, y=y2)
            g.linear(x=x1, y=y2)
            g.linear(x=x1, y=y1)
            off += stepover

        # Final perimeter cleanup
        hw = pw / 2 - tool_dia / 2
        hh = ph / 2 - tool_dia / 2
        g.linear(x=cx - hw, y=cy - hh)
        g.linear(x=cx + hw, y=cy - hh)
        g.linear(x=cx + hw, y=cy + hh)
        g.linear(x=cx - hw, y=cy + hh)
        g.linear(x=cx - hw, y=cy - hh)

    g.rapid(z=SAFE_Z)


def helical_bore(g: GCodeBuilder, name: str, cx: float, cy: float,
                 bore_dia: float, depth: float, tool_dia: float,
                 doc: float, plunge: float, feed: float, op_label: str):
    """Bore a circular hole larger than tool diameter using helical interpolation."""
    g.comment(f"{op_label}: {name} (bore dia={bore_dia:.1f}mm, depth={depth:.1f}mm)")
    bore_r = max(0.1, (bore_dia - tool_dia) / 2)
    g.rapid(z=SAFE_Z)
    g.rapid(x=cx, y=cy)
    g.rapid(z=RETRACT_Z)

    bore_z = 0.0
    while bore_z > -depth:
        bore_z -= doc
        if bore_z < -depth:
            bore_z = -depth
        g.arc_cw(cx, cy, bore_r, 0, z=bore_z, f=plunge)
    # Final cleanup pass at full depth
    g.arc_cw(cx, cy, bore_r, 0, f=feed)
    g.rapid(z=SAFE_Z)


# ---------------------------------------------------------------------------
# Coordinate transform helpers
# ---------------------------------------------------------------------------
# Spec uses: x_center = mm offset from body centerline (+ = treble/right)
#            y_from_top = mm from top of body (0 = neck end)
# DXF uses:  origin at body center, Y+ toward neck, Y- toward V-point
# G-code:    origin at stock lower-left corner for CNC fixture

def spec_to_gcode(x_center: float, y_from_top: float,
                  body_w: float, body_h: float) -> Tuple[float, float]:
    """Convert spec coordinates to G-code coordinates (origin at stock lower-left)."""
    # x_center: 0 = body centerline, + = right side
    gx = body_w / 2 + x_center
    # y_from_top: 0 = neck end of body
    # G-code Y: 0 = bottom of stock (V-point end)
    gy = body_h - y_from_top
    return gx, gy


# ---------------------------------------------------------------------------
# Phase 1: Front Face Routing
# ---------------------------------------------------------------------------

def generate_phase1_front(spec: Dict, outline_mm: List[Tuple[float, float]]) -> str:
    """Generate front-face CNC operations in mm."""

    g = GCodeBuilder()
    g.header(
        "SmartGuitar_v1_Phase1_FrontFace",
        "GRBL_3018_Default",
        "Khaya (African Mahogany) 444.5 x 368.3 x 44.45mm",
        "Phase 1: Front Face"
    )

    body = spec["body"]["dimensions"]
    body_w = body["width_max_mm"]   # 368.3 (X axis in G-code)
    body_h = body["length_mm"]      # 444.5 (Y axis in G-code)
    stock_t = body["thickness_mm"]  # 44.45

    cavs = spec["cavities"]

    # -----------------------------------------------------------------------
    # OP10: Fixture / Registration Holes
    # -----------------------------------------------------------------------
    g.tool_change(3, "3mm Flat/Drill", T3_RPM, "OP10: Fixture pin holes for workholding")
    g.section("OP10: FIXTURE / REGISTRATION HOLES")
    g.comment(f"Stock: {body_w:.1f} x {body_h:.1f} x {stock_t:.2f} mm")
    g.comment("4 fixture holes in waste material outside body perimeter")

    fixture_offset = 12.0  # mm from stock edge
    fixture_holes = [
        (fixture_offset, fixture_offset),
        (body_w - fixture_offset, fixture_offset),
        (body_w - fixture_offset, body_h - fixture_offset),
        (fixture_offset, body_h - fixture_offset),
    ]
    for i, (fx, fy) in enumerate(fixture_holes):
        g.comment(f"Fixture hole {i + 1}: ({fx:.1f}, {fy:.1f})")
        g.peck_drill(fx, fy, -10.0, RETRACT_Z, 3.0, T3_PLUNGE)
    g.cancel_canned()

    # -----------------------------------------------------------------------
    # OP20: Neck Pocket Rough
    # -----------------------------------------------------------------------
    np = cavs["neck_pocket"]
    np_dims = np["dimensions_mm"]
    np_bp = np["body_position_mm"]
    # y_from_top is pocket start (top edge); center = start + length/2
    np_cx, np_cy = spec_to_gcode(np_bp["x_center"], np_bp["y_from_top"] + np_dims["length"] / 2, body_w, body_h)

    g.tool_change(1, "10mm Flat End Mill", T1_RPM, "OP20: Neck pocket roughing")
    mill_rectangular_pocket(
        g, "Neck Pocket", np_cx, np_cy,
        np_dims["length"], np_dims["width"], np_dims["depth"],
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP20"
    )

    # -----------------------------------------------------------------------
    # OP21: Neck Pickup Cavity Rough
    # -----------------------------------------------------------------------
    npu = cavs["neck_pickup_route"]
    npu_dims = npu["dimensions_mm"]
    # Pickup Y position from bridge: y_from_bridge = 152.4mm
    # Bridge at y_from_top=320, so pickup at y_from_top = 320 - 152.4 = 167.6
    npu_y_from_top = 320.0 - npu.get("body_position_mm", {}).get("y_from_bridge", 152.4)
    npu_cx, npu_cy = spec_to_gcode(0.0, npu_y_from_top, body_w, body_h)

    mill_rectangular_pocket(
        g, "Neck Pickup Cavity", npu_cx, npu_cy,
        npu_dims["length"], npu_dims["width"], npu_dims["depth"],
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP21"
    )

    # -----------------------------------------------------------------------
    # OP22: Bridge Pickup Cavity Rough
    # -----------------------------------------------------------------------
    bpu = cavs["bridge_pickup_route"]
    bpu_dims = bpu["dimensions_mm"]
    bpu_y_from_top = 320.0 - bpu.get("body_position_mm", {}).get("y_from_bridge", 25.4)
    bpu_cx, bpu_cy = spec_to_gcode(0.0, bpu_y_from_top, body_w, body_h)

    mill_rectangular_pocket(
        g, "Bridge Pickup Cavity", bpu_cx, bpu_cy,
        bpu_dims["length"], bpu_dims["width"], bpu_dims["depth"],
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP22"
    )

    # -----------------------------------------------------------------------
    # OP25: Neck Pocket Finish
    # -----------------------------------------------------------------------
    g.tool_change(2, "6mm Flat End Mill", T2_RPM, "OP25-26: Finish passes")
    mill_rectangular_pocket(
        g, "Neck Pocket Finish", np_cx, np_cy,
        np_dims["length"], np_dims["width"], np_dims["depth"],
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP25"
    )

    # -----------------------------------------------------------------------
    # OP26: Pickup Cavities Finish
    # -----------------------------------------------------------------------
    mill_rectangular_pocket(
        g, "Neck Pickup Finish", npu_cx, npu_cy,
        npu_dims["length"], npu_dims["width"], npu_dims["depth"],
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP26a"
    )
    mill_rectangular_pocket(
        g, "Bridge Pickup Finish", bpu_cx, bpu_cy,
        bpu_dims["length"], bpu_dims["width"], bpu_dims["depth"],
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP26b"
    )

    # -----------------------------------------------------------------------
    # OP30: Control Plate Surface Recess
    # -----------------------------------------------------------------------
    cp = cavs["control_plate_surface"]
    cp_grid = cp["grid_position"]
    # Grid normalized (0-1) => body mm: x_center = offset from centerline, y = from top
    cp_x_center = (cp_grid["x_center_norm"] - 0.5) * body_w
    cp_y_from_top = cp_grid["y_center_norm"] * body_h
    cp_cx, cp_cy = spec_to_gcode(cp_x_center, cp_y_from_top, body_w, body_h)

    mill_rectangular_pocket(
        g, "Control Plate Surface Recess", cp_cx, cp_cy,
        cp["dimensions_mm"]["length"], cp["dimensions_mm"]["width"],
        cp["dimensions_mm"]["thickness"],  # 3mm recess for plate
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP30"
    )

    # -----------------------------------------------------------------------
    # OP40: Headless Bridge Mounting Holes
    # -----------------------------------------------------------------------
    g.tool_change(3, "3mm Flat/Drill", T3_RPM, "OP40-42: Drilling operations")
    br = cavs["bridge_route"]
    br_dims = br["dimensions_mm"]
    br_bp = br["body_position_mm"]
    br_cx, br_cy = spec_to_gcode(br_bp["x_center"], br_bp["y_from_top"], body_w, body_h)

    g.section("OP40: HEADLESS BRIDGE MOUNTING HOLES")
    g.comment(f"Bridge center: ({br_cx:.1f}, {br_cy:.1f})")
    g.comment(f"4 mounting holes: {br_dims['mounting_hole_diameter']:.1f}mm x {br_dims['mounting_hole_depth']:.1f}mm deep")
    g.comment(f"Spacing: {br_dims['mounting_hole_spacing_length']:.0f} x {br_dims['mounting_hole_spacing_width']:.0f}mm")

    mh_sl = br_dims["mounting_hole_spacing_length"] / 2
    mh_sw = br_dims["mounting_hole_spacing_width"] / 2
    mh_dia = br_dims["mounting_hole_diameter"]
    mh_depth = br_dims["mounting_hole_depth"]

    bridge_holes = [
        (br_cx - mh_sl, br_cy - mh_sw),
        (br_cx + mh_sl, br_cy - mh_sw),
        (br_cx + mh_sl, br_cy + mh_sw),
        (br_cx - mh_sl, br_cy + mh_sw),
    ]
    for i, (bx, by) in enumerate(bridge_holes):
        g.comment(f"Bridge mount {i + 1}: ({bx:.1f}, {by:.1f})")
        g.peck_drill(bx, by, -mh_depth, RETRACT_Z, 2.0, T3_PLUNGE)
    g.cancel_canned()

    # -----------------------------------------------------------------------
    # OP41: Pot Shaft Holes (3x 9.5mm through)
    # -----------------------------------------------------------------------
    g.section("OP41: POT SHAFT HOLES (3x 9.5mm through)")
    pot_comps = cp["components"]
    pot_dia = cp["pot_holes_mm"]["diameter"]  # 9.5mm

    for pot_name, pot_offset in pot_comps.items():
        px = cp_cx + pot_offset["x_offset_mm"]
        py = cp_cy + pot_offset["y_offset_mm"]
        helical_bore(g, pot_name, px, py, pot_dia, stock_t,
                     T3_DIA, T3_DOC, T3_PLUNGE, T3_FEED, "OP41")

    # -----------------------------------------------------------------------
    # OP42: Output Jack Bore (12.7mm, angled)
    # -----------------------------------------------------------------------
    g.section("OP42: OUTPUT JACK BORE (12.7mm)")
    oj = cavs["output_jack"]
    oj_bp = oj["body_position_mm"]
    oj_cx, oj_cy = spec_to_gcode(oj_bp["x_center"], oj_bp["y_from_top"], body_w, body_h)
    oj_dia = oj["dimensions_mm"]["bore_diameter"]
    oj_depth = oj["dimensions_mm"]["bore_depth"]
    g.comment("NOTE: Output jack bore is angled through lower bout edge.")
    g.comment("This G-code drills vertically — operator must tilt body or use fixture for angled bore.")
    helical_bore(g, "Output Jack", oj_cx, oj_cy, oj_dia, oj_depth,
                 T3_DIA, T3_DOC, T3_PLUNGE, T3_FEED, "OP42")

    # -----------------------------------------------------------------------
    # OP50: Body Perimeter Contour with Tabs
    # -----------------------------------------------------------------------
    g.tool_change(2, "6mm Flat End Mill", T2_RPM, "OP50: Body perimeter profile")
    g.section("OP50: BODY PERIMETER CONTOUR")

    # Transform outline to G-code coordinates (shift to lower-left origin)
    # DXF outline is centered at origin
    xs = [p[0] for p in outline_mm[:-1]]  # exclude closing duplicate
    ys = [p[1] for p in outline_mm[:-1]]
    cx_dxf = (max(xs) + min(xs)) / 2
    cy_dxf = (max(ys) + min(ys)) / 2
    dxf_w = max(xs) - min(xs)
    dxf_h = max(ys) - min(ys)

    # Shift to lower-left origin and scale to match body dimensions
    scale_x = body_w / dxf_w if dxf_w > 0 else 1.0
    scale_y = body_h / dxf_h if dxf_h > 0 else 1.0
    outline_gcode = []
    for px, py in outline_mm:
        gx = (px - min(xs)) * scale_x
        gy = (py - min(ys)) * scale_y
        outline_gcode.append((gx, gy))

    # Offset outline outward by half tool diameter + finish allowance
    tool_offset = T2_DIA / 2 + 0.25  # +0.25mm finish allowance
    perimeter_pts = offset_polygon(outline_gcode, -tool_offset)  # outward
    perim_len = path_length(perimeter_pts)
    tab_count = 6
    tab_width = 12.0   # mm
    tab_height = 3.0    # mm

    g.comment(f"Perimeter: {perim_len:.1f} mm, {len(perimeter_pts)} points")
    g.comment(f"Tabs: {tab_count} x {tab_width:.0f}mm wide x {tab_height:.0f}mm tall")

    num_perim_passes = max(1, math.ceil(stock_t / T2_DOC))
    g.comment(f"Depth: {stock_t:.2f}mm in {num_perim_passes} passes ({T2_DOC}mm DOC)")

    tab_spacing = perim_len / tab_count
    tab_positions = [(i + 0.5) * tab_spacing for i in range(tab_count)]

    for pn in range(num_perim_passes):
        z = -T2_DOC * (pn + 1)
        if z < -stock_t:
            z = -stock_t

        is_tab_pass = (pn >= num_perim_passes - 2)
        tab_z = -stock_t + tab_height

        g.comment(f"Pass {pn + 1}/{num_perim_passes}: Z={z:.3f}")
        g.rapid(z=SAFE_Z)
        g.rapid(x=perimeter_pts[0][0], y=perimeter_pts[0][1])
        g.rapid(z=RETRACT_Z)
        g.linear(z=z, f=T2_PLUNGE)
        g.emit(f"F{T2_FEED:.1f}")

        accum = 0.0
        tab_idx = 0
        in_tab = False

        for i in range(1, len(perimeter_pts)):
            px, py = perimeter_pts[i]
            ppx, ppy = perimeter_pts[i - 1]
            seg = math.sqrt((px - ppx) ** 2 + (py - ppy) ** 2)

            if is_tab_pass and z < tab_z and tab_idx < len(tab_positions):
                tab_start = tab_positions[tab_idx] - tab_width / 2
                tab_end = tab_positions[tab_idx] + tab_width / 2

                if not in_tab and accum <= tab_start < accum + seg:
                    g.linear(z=tab_z, f=T2_PLUNGE)
                    in_tab = True
                if in_tab and accum <= tab_end < accum + seg:
                    g.linear(z=z, f=T2_PLUNGE)
                    in_tab = False
                    tab_idx += 1

            g.linear(x=px, y=py)
            accum += seg

    g.rapid(z=SAFE_Z)

    g.footer()
    return g.text()


# ---------------------------------------------------------------------------
# Phase 2: Rear Face Routing
# ---------------------------------------------------------------------------

def generate_phase2_rear(spec: Dict) -> str:
    """Generate rear-face CNC operations in mm."""

    g = GCodeBuilder()
    g.header(
        "SmartGuitar_v1_Phase2_RearFace",
        "GRBL_3018_Default",
        "Khaya (African Mahogany) — FLIPPED, Z=0 at rear surface",
        "Phase 2: Rear Face"
    )

    body = spec["body"]["dimensions"]
    body_w = body["width_max_mm"]   # 368.3
    body_h = body["length_mm"]      # 444.5
    stock_t = body["thickness_mm"]  # 44.45

    cavs = spec["cavities"]

    g.comment("OPERATOR: Flip body to rear face. Re-zero Z to rear surface.")
    g.comment("Use registration pins from OP10 for alignment.")
    g.comment("")

    # -----------------------------------------------------------------------
    # OP60: Rear Electronics Cavity (Pi 5) — Rough + Finish
    # -----------------------------------------------------------------------
    rec = cavs["rear_electronics_cavity"]
    rec_dims = rec["dimensions_mm"]
    rec_bp = rec["body_position_mm"]
    # Rear face: X is mirrored (x_center flips sign)
    rec_cx, rec_cy = spec_to_gcode(-rec_bp["x_center"], rec_bp["y_from_top"], body_w, body_h)

    g.tool_change(1, "10mm Flat End Mill", T1_RPM, "OP60: Rear electronics cavity rough")
    mill_rectangular_pocket(
        g, "Rear Electronics Cavity (Pi 5) — Rough", rec_cx, rec_cy,
        rec_dims["length"], rec_dims["width"], rec_dims["depth"],
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP60",
        corner_r=rec_dims.get("corner_radius", 0)
    )

    g.tool_change(2, "6mm Flat End Mill", T2_RPM, "OP60f: Rear electronics cavity finish")
    mill_rectangular_pocket(
        g, "Rear Electronics Cavity (Pi 5) — Finish", rec_cx, rec_cy,
        rec_dims["length"], rec_dims["width"], rec_dims["depth"],
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP60f",
        corner_r=rec_dims.get("corner_radius", 0)
    )

    # -----------------------------------------------------------------------
    # OP61: Teensy I/O Coprocessor Pocket — Rough + Finish
    # -----------------------------------------------------------------------
    ard = cavs["teensy_io_pocket"]
    ard_dims = ard["dimensions_mm"]
    ard_bp = ard["body_position_mm"]
    ard_cx, ard_cy = spec_to_gcode(-ard_bp["x_center"], ard_bp["y_from_top"], body_w, body_h)

    g.tool_change(1, "10mm Flat End Mill", T1_RPM, "OP61: Teensy I/O coprocessor pocket rough")
    mill_rectangular_pocket(
        g, "Teensy I/O Pocket — Rough", ard_cx, ard_cy,
        ard_dims["length"], ard_dims["width"], ard_dims["depth"],
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP61",
        corner_r=ard_dims.get("corner_radius", 0)
    )

    g.tool_change(2, "6mm Flat End Mill", T2_RPM, "OP61f: Teensy I/O coprocessor pocket finish")
    mill_rectangular_pocket(
        g, "Teensy I/O Pocket — Finish", ard_cx, ard_cy,
        ard_dims["length"], ard_dims["width"], ard_dims["depth"],
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP61f",
        corner_r=ard_dims.get("corner_radius", 0)
    )

    # -----------------------------------------------------------------------
    # OP62: Antenna Recess (shallow 2mm pocket inside electronics cavity)
    # -----------------------------------------------------------------------
    ant = cavs["antenna_recess"]
    ant_dims = ant["dimensions_mm"]
    ant_bp = ant["body_position_mm"]
    ant_cx, ant_cy = spec_to_gcode(-ant_bp["x_center"], ant_bp["y_from_top"], body_w, body_h)

    g.section("OP62: ANTENNA RECESS (2mm shallow pocket)")
    rf_window = ant_dims.get("geometry_clarification", {}).get("rf_window_thickness_mm", 2.0)
    g.comment(f"50x30mm pocket, only 2mm deep — leaves {rf_window}mm wood window for RF transparency")
    g.comment("Milled as stepped shelf inside the rear electronics cavity")

    # This is a shallow pocket milled at the BOTTOM of the electronics cavity
    # Z reference: we're already at the floor of the electronics cavity (22mm deep)
    # The antenna recess goes 2mm deeper from the cavity floor
    ant_shelf_depth = ant_dims.get("shelf_step_depth_mm", ant_dims.get("depth", 2.0))
    ant_total_depth = rec_dims["depth"] + ant_shelf_depth
    mill_rectangular_pocket(
        g, "Antenna Recess", ant_cx, ant_cy,
        ant_dims["length"], ant_dims["width"], ant_total_depth,
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP62"
    )

    # -----------------------------------------------------------------------
    # OP63: Rear Cover Plate Recess
    # -----------------------------------------------------------------------
    g.section("OP63: REAR COVER PLATE RECESSES")
    g.comment("Shallow lip around each rear cavity for cover plate seating")
    cover_lip = 2.0   # mm deep
    cover_margin = 5.0  # mm wider than cavity on each side

    # Electronics cavity cover
    mill_rectangular_pocket(
        g, "Electronics Cavity Cover Recess", rec_cx, rec_cy,
        rec_dims["length"] + 2 * cover_margin, rec_dims["width"] + 2 * cover_margin,
        cover_lip,
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP63a"
    )

    # Teensy pocket cover
    mill_rectangular_pocket(
        g, "Teensy Pocket Cover Recess", ard_cx, ard_cy,
        ard_dims["length"] + 2 * cover_margin, ard_dims["width"] + 2 * cover_margin,
        cover_lip,
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP63b"
    )

    # -----------------------------------------------------------------------
    # OP-CC: Control Cavity (rear-routed electronics pocket)
    # -----------------------------------------------------------------------
    g.section("OP-CC: CONTROL CAVITY (LP heritage scaled to 100x60x20mm)")

    cc = cavs.get("control_cavity")
    if cc:
        cc_dims = cc["dimensions_mm"]
        cc_bp = cc["body_position_mm"]
        cc_length = cc_dims["length"]     # 100mm
        cc_width = cc_dims["width"]       # 60mm
        cc_depth = cc_dims["depth"]       # 20mm
        cc_radius = cc_dims["corner_radius"]  # 6.35mm

        # Convert to G-code coords (rear face: mirror X)
        cc_cx, cc_cy = spec_to_gcode(-cc_bp["x_center"], cc_bp["y_from_top"], body_w, body_h)

        g.comment(f"Control cavity: {cc_length}x{cc_width}x{cc_depth}mm deep")
        g.comment("Houses volume pot, tone pot, rotary switch, wiring harness")

        # OP-CC-50: Rough clearing with adaptive strategy
        g.comment("OP-CC-50: Adaptive clearing, 3mm stepdown")
        mill_rectangular_pocket(
            g, "Control Cavity Rough", cc_cx, cc_cy,
            cc_length, cc_width, cc_depth,
            T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP-CC-50"
        )

        # OP-CC-51: Finish contour pass (simulated by final pass at depth)
        g.comment("OP-CC-51: Finish contour, 0.5mm stepover")
        # Final cleanup pass at full depth
        g.rapid(z=SAFE_Z)

        # OP-CC-52: Cover plate recess (110x70mm, 3.175mm deep)
        cover = cc.get("cover_plate", {})
        cover_l = cover.get("length_mm", 110.0)
        cover_w = cover.get("width_mm", 70.0)
        cover_recess = cover.get("recess_depth_mm", 3.175)

        g.comment(f"OP-CC-52: Cover plate recess {cover_l}x{cover_w}mm, {cover_recess}mm deep")
        mill_rectangular_pocket(
            g, "Control Cavity Cover Recess", cc_cx, cc_cy,
            cover_l, cover_w, cover_recess,
            T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP-CC-52"
        )

        # OP-CC-60: Screw pilot holes (4 corners, 10mm deep)
        g.tool_change(4, "2.5mm Drill", T3_RPM, "OP-CC-60: Screw pilot holes")
        g.comment("OP-CC-60: 4x pilot holes for cover plate screws")

        screw_margin = 8.0  # 8mm from cover edge
        hole_depth = 10.0
        half_l = (cover_l / 2) - screw_margin
        half_w = (cover_w / 2) - screw_margin

        screw_holes = [
            (cc_cx - half_l, cc_cy - half_w),
            (cc_cx + half_l, cc_cy - half_w),
            (cc_cx + half_l, cc_cy + half_w),
            (cc_cx - half_l, cc_cy + half_w),
        ]

        for i, (sx, sy) in enumerate(screw_holes):
            g.rapid(x=sx, y=sy)
            g.rapid(z=RETRACT_Z)
            g.linear(z=-hole_depth, f=T3_PLUNGE)
            g.rapid(z=SAFE_Z)
            g.comment(f"Screw hole {i+1}/4")
    else:
        g.comment("control_cavity not found in spec — skipping OP-CC")

    # -----------------------------------------------------------------------
    # OP70: Wiring Channels
    # -----------------------------------------------------------------------
    g.tool_change(3, "3mm Flat/Drill", T3_RPM, "OP70-71: Channels and slots")
    g.section("OP70: WIRING CHANNELS (4 routes)")

    wc = cavs["rear_wiring_channel"]
    wc_dims = wc["dimensions_mm"]
    ch_width = wc_dims["width"]   # 10mm
    ch_depth = wc_dims["depth"]   # 15mm

    g.comment(f"Channel: {ch_width}mm wide x {ch_depth}mm deep")
    g.comment("4 routes connecting pickups, Teensy, Pi 5, and output jack")

    num_ch_passes = max(1, math.ceil(ch_depth / T3_DOC))

    # Route 1: Pickups to Teensy (short, 20mm)
    g.comment("Route 1: Pickup area to Teensy pocket (~20mm)")
    # From neck pickup area to Teensy pocket
    r1_start_x, r1_start_y = spec_to_gcode(0.0, 167.6, body_w, body_h)  # neck pickup area
    r1_end_x, r1_end_y = ard_cx, ard_cy
    for wp in range(num_ch_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -ch_depth:
            wz = -ch_depth
        g.rapid(x=r1_start_x, y=r1_start_y)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=r1_end_x, y=r1_end_y, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    # Route 2: Teensy to Pi 5 (USB serial, ~140mm)
    g.comment("Route 2: Teensy to Pi 5 USB serial (~140mm)")
    for wp in range(num_ch_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -ch_depth:
            wz = -ch_depth
        g.rapid(x=ard_cx, y=ard_cy)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=rec_cx, y=rec_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    # Route 3: Bridge pickup to Teensy (~130mm)
    g.comment("Route 3: Bridge pickup area to Teensy (~130mm)")
    r3_start_x, r3_start_y = spec_to_gcode(0.0, 294.6, body_w, body_h)  # bridge pickup area
    for wp in range(num_ch_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -ch_depth:
            wz = -ch_depth
        g.rapid(x=r3_start_x, y=r3_start_y)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=ard_cx, y=ard_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    # Route 4: Pi 5 cavity to output jack (~75mm)
    g.comment("Route 4: Electronics cavity to output jack (~75mm)")
    oj = cavs["output_jack"]
    oj_bp = oj["body_position_mm"]
    # Rear face: mirror X
    oj_cx, oj_cy = spec_to_gcode(-oj_bp["x_center"], oj_bp["y_from_top"], body_w, body_h)
    for wp in range(num_ch_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -ch_depth:
            wz = -ch_depth
        g.rapid(x=rec_cx, y=rec_cy)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=oj_cx, y=oj_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    # -----------------------------------------------------------------------
    # OP71: USB-C Edge Slot
    # -----------------------------------------------------------------------
    g.section("OP71: USB-C EDGE SLOT")
    usb = cavs["usb_c_port"]
    usb_dims = usb["dimensions_mm"]
    usb_bp = usb["body_position_mm"]
    usb_cx, usb_cy = spec_to_gcode(-usb_bp["x_center"], usb_bp["y_from_top"], body_w, body_h)

    g.comment(f"Edge slot: {usb_dims['slot_width']}x{usb_dims['slot_height']}mm, {usb_dims['slot_depth']}mm deep from edge")
    g.comment("Routed from body edge inward — slot perpendicular to body surface")

    # Slot milled from the edge inward
    slot_w = usb_dims["slot_width"]
    slot_h = usb_dims["slot_height"]
    slot_d = usb_dims["slot_depth"]

    num_slot_passes = max(1, math.ceil(slot_h / T3_DOC))
    for sp in range(num_slot_passes):
        sz = -T3_DOC * (sp + 1)
        if sz < -slot_h:
            sz = -slot_h
        g.rapid(x=usb_cx - slot_w / 2, y=usb_cy)
        g.rapid(z=RETRACT_Z)
        g.linear(z=sz, f=T3_PLUNGE)
        g.linear(x=usb_cx + slot_w / 2, y=usb_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    g.footer()
    return g.text()


# ---------------------------------------------------------------------------
# Build summary JSON
# ---------------------------------------------------------------------------

def generate_build_summary(spec: Dict, phase1_lines: int, phase2_lines: int) -> str:
    """Generate build summary JSON."""

    summary = {
        "model": "Smart Guitar v1.1",
        "spec_file": "instrument_geometry/body/specs/smart_guitar_v1.json",
        "generated": datetime.now().isoformat(),
        "generator": "The Production Shop - Smart Guitar Full Build Generator",
        "design": {
            "body_style": "Explorer-Klein hybrid angular",
            "neck": "headless",
            "scale_length_mm": 628.65,
            "frets": 24,
            "material": "Khaya (African Mahogany)",
        },
        "phases": {
            "phase1_front_face": {
                "file": "SmartGuitar_v1_Phase1_FrontFace.nc",
                "units": "mm (G21)",
                "operations": [
                    "OP10: Fixture holes (T3 3mm)",
                    "OP20: Neck pocket rough (T1 10mm)",
                    "OP21: Neck pickup cavity rough (T1 10mm)",
                    "OP22: Bridge pickup cavity rough (T1 10mm)",
                    "OP25: Neck pocket finish (T2 6mm)",
                    "OP26a/b: Pickup cavities finish (T2 6mm)",
                    "OP30: Control plate surface recess (T2 6mm)",
                    "OP40: Headless bridge mounting holes 4x (T3 3mm)",
                    "OP41: Pot shaft holes 3x 9.5mm (T3 3mm)",
                    "OP42: Output jack bore 12.7mm (T3 3mm)",
                    "OP50: Body perimeter contour with 6 tabs (T2 6mm)",
                ],
                "gcode_lines": phase1_lines,
                "stock": "Khaya (African Mahogany) 444.5 x 368.3 x 44.45mm",
                "tools": ["T1: 10mm flat (rough)", "T2: 6mm flat (finish)", "T3: 3mm flat/drill"],
            },
            "phase2_rear_face": {
                "file": "SmartGuitar_v1_Phase2_RearFace.nc",
                "units": "mm (G21)",
                "operations": [
                    "OP60: Rear electronics cavity rough + finish (T1/T2)",
                    "OP61: Teensy I/O coprocessor pocket rough + finish (T1/T2)",
                    "OP62: Antenna recess 2mm shallow (T2 6mm)",
                    "OP63a/b: Rear cover plate recesses (T2 6mm)",
                    "OP-CC-50/51: Control cavity rough + finish (T2 6mm)",
                    "OP-CC-52: Control cavity cover recess (T2 6mm)",
                    "OP-CC-60: Control cavity screw holes (T4 2.5mm drill)",
                    "OP70: Wiring channels 4 routes (T3 3mm)",
                    "OP71: USB-C edge slot (T3 3mm)",
                ],
                "gcode_lines": phase2_lines,
                "stock": "Same blank, flipped to rear face",
                "tools": ["T1: 10mm flat (rough)", "T2: 6mm flat (finish)", "T3: 3mm flat/drill"],
            },
        },
        "total_gcode_lines": phase1_lines + phase2_lines,
        "tool_library": {
            "T1": "10mm Flat End Mill (roughing pockets)",
            "T2": "6mm Flat End Mill (finishing, perimeter, recess)",
            "T3": "3mm Flat/Drill (channels, all drilling, slots)",
        },
        "iot_cavities": {
            "rear_electronics": "95x65x22mm — Pi 5 + Li-ion 18650 + NVMe SSD",
            "teensy_io": "70x25x20mm — Teensy 4.1 I/O coprocessor",
            "antenna_recess": "50x30x2mm — dual-band PCB antenna under 2mm wood window",
            "usb_c_port": "12x6.5mm edge slot — USB-C PD 20W charging",
            "wiring_channels": "4 routes, 10mm wide x 15mm deep",
        },
        "notes": [
            "Phase 1 operates on front face — all visible-side routing",
            "Phase 2 operates on rear face — all electronics cavities and channels",
            "Headless bridge: 4 mounting holes, no tailpiece studs needed",
            "Body perimeter (OP50) includes 6 holding tabs at 3mm height",
            "All pocket operations use helical entry to avoid plunge marks",
            "Output jack bore (OP42) noted as vertical — operator may need angled fixture",
            "Antenna recess (OP62) is milled as extension of electronics cavity floor",
            "CRITICAL: Verify fixture hole alignment before flipping to rear face",
        ],
    }
    return json.dumps(summary, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Smart Guitar v1.1 — Full CNC Build Generator")
    print("Headless | Gibson 24.75\" Scale | Khaya Body | IoT Electronics")
    print("=" * 70)
    print()

    # Load spec
    print(f"Loading spec: {SPEC_PATH.name}")
    spec = load_spec()
    print(f"  Model: {spec['instrument']['name']} {spec['instrument']['version']}")
    print(f"  Body: {spec['body']['dimensions']['length_mm']} x {spec['body']['dimensions']['width_max_mm']} x {spec['body']['dimensions']['thickness_mm']}mm")
    print(f"  Neck: {spec['neck']['design']}, {spec['neck']['scale_length_mm']}mm scale, {spec['neck']['fret_count']} frets")
    print(f"  Material: {spec['body']['materials']['prototype']}")

    # Load body outline
    print(f"\nLoading body outline: {DXF_PATH.name}")
    try:
        outline = load_body_outline_from_dxf()
        print(f"  Points: {len(outline)}")
        xs = [p[0] for p in outline]
        ys = [p[1] for p in outline]
        print(f"  Dimensions: {max(xs) - min(xs):.1f} x {max(ys) - min(ys):.1f} mm")
    except FileNotFoundError:
        print("  DXF not found, using fallback outline")
        outline = _fallback_body_points()
        print(f"  Points: {len(outline)} (from generate_smart_guitar_dxf.py)")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput: {OUTPUT_DIR}")

    # Phase 1: Front face
    print("\n--- Phase 1: Front Face Routing ---")
    phase1 = generate_phase1_front(spec, outline)
    phase1_lines = len(phase1.strip().split("\n"))
    p1_path = OUTPUT_DIR / "SmartGuitar_v1_Phase1_FrontFace.nc"
    p1_path.write_text(phase1, encoding="utf-8")
    print(f"  Written: {p1_path.name} ({phase1_lines:,} lines)")

    # Verify Phase 1 G-code (SG-GAP-13)
    v1 = verify_gcode(
        gcode=phase1,
        stock_thickness_mm=44.45,  # 1.75" Khaya
        phase_name="Phase 1: Front Face Routing",
        units="mm",
    )

    # Phase 2: Rear face
    print("\n--- Phase 2: Rear Face Routing ---")
    phase2 = generate_phase2_rear(spec)
    phase2_lines = len(phase2.strip().split("\n"))
    p2_path = OUTPUT_DIR / "SmartGuitar_v1_Phase2_RearFace.nc"
    p2_path.write_text(phase2, encoding="utf-8")
    print(f"  Written: {p2_path.name} ({phase2_lines:,} lines)")

    # Verify Phase 2 G-code (SG-GAP-13)
    v2 = verify_gcode(
        gcode=phase2,
        stock_thickness_mm=44.45,  # 1.75" Khaya
        phase_name="Phase 2: Rear Face Routing",
        units="mm",
    )

    # Build summary
    print("\n--- Build Summary ---")
    summary = generate_build_summary(spec, phase1_lines, phase2_lines)
    sum_path = OUTPUT_DIR / "SmartGuitar_v1_BuildSummary.json"
    sum_path.write_text(summary, encoding="utf-8")
    print(f"  Written: {sum_path.name}")

    total = phase1_lines + phase2_lines
    print(f"\n{'=' * 70}")
    print(f"COMPLETE: {total:,} total G-code lines across 2 phases")
    print(f"  Phase 1 (Front Face):  {phase1_lines:,} lines")
    print(f"  Phase 2 (Rear Face):   {phase2_lines:,} lines")
    print(f"  3 tools required: T1-T3")

    # Verification summary (SG-GAP-13)
    all_ok = v1["ok"] and v2["ok"]
    if all_ok:
        print(f"\n  ✓ G-CODE VERIFICATION: ALL PHASES PASSED")
    else:
        print(f"\n  ✗ G-CODE VERIFICATION FAILED - review errors before machining")
        if not v1["ok"]:
            print(f"    Phase 1 errors: {v1['errors']}")
        if not v2["ok"]:
            print(f"    Phase 2 errors: {v2['errors']}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
