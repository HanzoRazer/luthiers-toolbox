#!/usr/bin/env python3
"""
Gibson Explorer 1958 — Full CNC Build G-code Generator
=======================================================

Generates the COMPLETE machining program for the 1958 Gibson Explorer
from the authoritative spec (gibson_explorer.json) and body outline DXF.

The Explorer is a flat-top solidbody with all cavities routed from the rear.
Single-phase build (rear face up, flip for perimeter cut with front face up).

Operations produced:
  Phase 1 — Rear Face Routing (body face-down, rear face up, mm, G21)
    OP10: Fixture / registration holes (T3 3mm)
    OP20: Neck pocket rough (T1 10mm)
    OP21: Neck pickup cavity rough (T1 10mm)
    OP22: Bridge pickup cavity rough (T1 10mm)
    OP23: Control cavity rough (T1 10mm)
    OP25: Neck pocket finish (T2 6mm)
    OP26: Neck pickup cavity finish (T2 6mm)
    OP27: Bridge pickup cavity finish (T2 6mm)
    OP28: Control cavity finish (T2 6mm)
    OP35: Cover plate recess (T2 6mm)
    OP40: Wiring channels — 3 routes (T3 3mm)
    OP60: Pot shaft holes 3x (T3 3mm)
    OP61: Bridge post holes 2x (T3 3mm)
    OP62: Tailpiece stud holes 2x (T3 3mm)
    OP63: Toggle switch hole (T3 3mm)
    OP64: Output jack bore (T3 3mm)
    OP65: Cover screw pilot holes 4x (T3 3mm)

  Phase 2 — Perimeter Profile (flip body, front face up)
    OP50: Body perimeter contour with 8 tabs (T2 6mm)

Units: mm (G21) throughout.
Machine: Configurable (default GRBL_3018_Default).
Stock: Korina (African Limba), 490 x 475 x 44.45mm

Usage:
    python scripts/generate_explorer_full_build.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Import shared G-code verification utility (EX-GAP-12)
from scripts.utils.gcode_verify import verify_gcode


# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
API_DIR = REPO_ROOT / "services" / "api"

SPEC_PATH = API_DIR / "app" / "instrument_geometry" / "specs" / "gibson_explorer.json"
DXF_PATH = API_DIR / "app" / "instrument_geometry" / "body" / "dxf" / "electric" / "gibson_explorer_body.dxf"
OUTPUT_DIR = REPO_ROOT / "exports" / "explorer_1958"


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
    """Load body outline points from Explorer DXF (mm)."""
    try:
        import ezdxf
    except ImportError:
        print("WARNING: ezdxf not available, using fallback outline")
        return _fallback_body_points()

    try:
        doc = ezdxf.readfile(str(DXF_PATH))
    except FileNotFoundError:
        print(f"WARNING: DXF not found at {DXF_PATH}, using fallback outline")
        return _fallback_body_points()

    msp = doc.modelspace()

    # Find the body outline — look for LWPOLYLINE on BODY_OUTLINE layer first
    for entity in msp:
        if entity.dxftype() == "LWPOLYLINE":
            layer = entity.dxf.get("layer", "")
            if "BODY" in layer.upper() or "OUTLINE" in layer.upper():
                pts = list(entity.get_points(format="xy"))
                if pts and pts[0] != pts[-1]:
                    pts.append(pts[0])
                return pts

    # Fallback: largest closed polyline
    best_pts: List[Tuple[float, float]] = []
    best_len = 0
    for entity in msp:
        if entity.dxftype() == "LWPOLYLINE":
            pts = list(entity.get_points(format="xy"))
            if len(pts) > best_len:
                best_pts = pts
                best_len = len(pts)

    if not best_pts:
        print("WARNING: No LWPOLYLINE found in DXF, using fallback outline")
        return _fallback_body_points()

    if best_pts[0] != best_pts[-1]:
        best_pts.append(best_pts[0])
    return best_pts


def _fallback_body_points() -> List[Tuple[float, float]]:
    """
    Fallback Explorer body outline (mm).
    24-point approximation of the angular Explorer shape.
    Origin at lower-left of bounding box.
    """
    # Explorer angular shape — key vertices (mm)
    # Body width ~475mm (horn tip to horn tip), length ~460mm
    W = 475.0
    L = 460.0
    points = [
        # Start at neck pocket center top
        (W / 2 - 27.5, L),        # neck pocket left edge
        (W / 2 + 27.5, L),        # neck pocket right edge
        # Treble horn (upper right, extends further)
        (W / 2 + 60, L - 20),
        (W - 40, L - 60),
        (W, L - 120),             # treble horn tip
        (W - 30, L - 180),
        # Waist (treble side)
        (W / 2 + 80, L / 2 + 20),
        (W / 2 + 70, L / 2 - 30),
        # Lower body (treble side)
        (W / 2 + 90, 100),
        (W / 2 + 60, 40),
        # Bottom point
        (W / 2 + 10, 10),
        (W / 2, 0),               # bottom center
        (W / 2 - 10, 10),
        # Lower body (bass side)
        (W / 2 - 60, 40),
        (W / 2 - 90, 100),
        # Waist (bass side)
        (W / 2 - 70, L / 2 - 30),
        (W / 2 - 80, L / 2 + 20),
        # Bass horn (upper left, shorter)
        (0 + 30, L - 180),
        (0, L - 140),             # bass horn tip
        (0 + 40, L - 80),
        (W / 2 - 60, L - 30),
        # Close back to start
        (W / 2 - 27.5, L),
    ]
    return points


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
        self.emit(f"; Generator: The Production Shop - Explorer 1958 Full Build")
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
# Tool Library (mm, for Korina / African Limba)
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
# G-code:    origin at stock lower-left corner
#            X across body width, Y along body length
#            Y=0 at bottom (tail end), Y=max at top (neck end)

def spec_to_gcode(x_center: float, y_from_top: float,
                  body_w: float, body_h: float) -> Tuple[float, float]:
    """Convert spec coordinates to G-code coordinates (origin at stock lower-left)."""
    gx = body_w / 2 + x_center
    gy = body_h - y_from_top
    return gx, gy


# ---------------------------------------------------------------------------
# Phase 1: Rear Face Routing
# ---------------------------------------------------------------------------

def generate_phase1_rear(spec: Dict[str, Any]) -> str:
    """Generate rear-face CNC operations (all cavity routing) in mm."""

    g = GCodeBuilder()
    g.header(
        "Explorer_1958_Phase1_RearRouting",
        "GRBL_3018_Default",
        "Korina (African Limba) 490 x 475 x 44.45mm",
        "Phase 1: Rear Face Routing"
    )

    body = spec["body"]
    body_w = body["width_mm"]        # 475.0 (X axis in G-code)
    body_h = body["length_mm"]       # 460.0 (Y axis in G-code)
    stock_t = body["thickness_mm"]   # 44.45

    g.comment("OPERATOR: Body face-down on spoilboard. Rear face up.")
    g.comment("Z=0 at rear surface. All cavities routed from rear.")
    g.comment("")

    # -----------------------------------------------------------------------
    # OP10: Fixture / Registration Holes
    # -----------------------------------------------------------------------
    g.tool_change(3, "3mm Flat/Drill", T3_RPM, "OP10: Fixture pin holes for workholding")
    g.section("OP10: FIXTURE / REGISTRATION HOLES")
    g.comment(f"Stock: {body_w:.1f} x {body_h:.1f} x {stock_t:.2f} mm")
    g.comment("4 fixture holes in waste material outside body perimeter")

    fixture_offset = 15.0
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
    np_spec = spec["neck_pocket"]
    np_w = np_spec["tenon_width_mm"]     # 55.0
    np_l = np_spec["tenon_length_mm"]    # 95.0
    np_d = np_spec["tenon_depth_mm"]     # 16.0
    np_bp = np_spec["body_position_mm"]
    # Neck pocket starts at top of body; center is at y_from_top + length/2
    np_cx, np_cy = spec_to_gcode(np_bp["x_center"], np_bp["y_from_top"] + np_l / 2, body_w, body_h)

    g.tool_change(1, "10mm Flat End Mill", T1_RPM, "OP20: Neck pocket roughing")
    mill_rectangular_pocket(
        g, "Neck Pocket", np_cx, np_cy,
        np_l, np_w, np_d,
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP20"
    )

    # -----------------------------------------------------------------------
    # OP21: Neck Pickup Cavity Rough
    # -----------------------------------------------------------------------
    npu = spec["pickups"]["neck"]
    npu_bp = npu["body_position_mm"]
    npu_cx, npu_cy = spec_to_gcode(npu_bp["x_center"], npu_bp["y_from_top"], body_w, body_h)

    mill_rectangular_pocket(
        g, "Neck Pickup Cavity", npu_cx, npu_cy,
        npu["route_length_mm"], npu["route_width_mm"], npu["route_depth_mm"],
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP21"
    )

    # -----------------------------------------------------------------------
    # OP22: Bridge Pickup Cavity Rough
    # -----------------------------------------------------------------------
    bpu = spec["pickups"]["bridge"]
    bpu_bp = bpu["body_position_mm"]
    bpu_cx, bpu_cy = spec_to_gcode(bpu_bp["x_center"], bpu_bp["y_from_top"], body_w, body_h)

    mill_rectangular_pocket(
        g, "Bridge Pickup Cavity", bpu_cx, bpu_cy,
        bpu["route_length_mm"], bpu["route_width_mm"], bpu["route_depth_mm"],
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP22"
    )

    # -----------------------------------------------------------------------
    # OP23: Control Cavity Rough
    # -----------------------------------------------------------------------
    cc = spec["control_cavity"]
    cc_bp = cc["body_position_mm"]
    cc_cx, cc_cy = spec_to_gcode(cc_bp["x_center"], cc_bp["y_from_top"], body_w, body_h)

    mill_rectangular_pocket(
        g, "Control Cavity", cc_cx, cc_cy,
        cc["length_mm"], cc["width_mm"], cc["depth_mm"],
        T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE, "OP23"
    )

    # -----------------------------------------------------------------------
    # OP25-28: Finish Passes
    # -----------------------------------------------------------------------
    g.tool_change(2, "6mm Flat End Mill", T2_RPM, "OP25-28: Finish passes")

    mill_rectangular_pocket(
        g, "Neck Pocket Finish", np_cx, np_cy,
        np_l, np_w, np_d,
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP25"
    )

    mill_rectangular_pocket(
        g, "Neck Pickup Finish", npu_cx, npu_cy,
        npu["route_length_mm"], npu["route_width_mm"], npu["route_depth_mm"],
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP26"
    )

    mill_rectangular_pocket(
        g, "Bridge Pickup Finish", bpu_cx, bpu_cy,
        bpu["route_length_mm"], bpu["route_width_mm"], bpu["route_depth_mm"],
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP27"
    )

    mill_rectangular_pocket(
        g, "Control Cavity Finish", cc_cx, cc_cy,
        cc["length_mm"], cc["width_mm"], cc["depth_mm"],
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP28"
    )

    # -----------------------------------------------------------------------
    # OP35: Cover Plate Recess
    # -----------------------------------------------------------------------
    cover_lip = spec["cover_recess"]["depth_mm"]  # 3.175mm
    cover_margin = 5.0  # mm wider than cavity on each side

    mill_rectangular_pocket(
        g, "Control Cavity Cover Recess", cc_cx, cc_cy,
        cc["length_mm"] + 2 * cover_margin, cc["width_mm"] + 2 * cover_margin,
        cover_lip,
        T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE, "OP35"
    )

    # -----------------------------------------------------------------------
    # OP40: Wiring Channels
    # -----------------------------------------------------------------------
    g.tool_change(3, "3mm Flat/Drill", T3_RPM, "OP40: Wiring channels")
    g.section("OP40: WIRING CHANNELS")

    ch_width = spec["wiring_channels"]["main_channel"]["width_mm"]   # 7.62
    ch_depth = spec["wiring_channels"]["main_channel"]["depth_mm"]   # 12.7
    num_ch_passes = max(1, math.ceil(ch_depth / T3_DOC))

    g.comment(f"Channel: {ch_width}mm wide x {ch_depth}mm deep")
    g.comment("3 routes: toggleSwitch-to-control, pickups-to-control, control-to-jack")

    # Route 1: Toggle switch (upper horn) to control cavity
    toggle = cc["toggle_switch"]["body_position_mm"]
    # On rear face, X is mirrored for toggle switch
    ts_cx, ts_cy = spec_to_gcode(-toggle["x_center"], toggle["y_from_top"], body_w, body_h)
    g.comment(f"Route 1: Toggle switch ({ts_cx:.1f}, {ts_cy:.1f}) to control cavity ({cc_cx:.1f}, {cc_cy:.1f})")
    for wp in range(num_ch_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -ch_depth:
            wz = -ch_depth
        g.rapid(x=ts_cx, y=ts_cy)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=cc_cx, y=cc_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    # Route 2: Pickup cavities to control cavity (via midpoint)
    g.comment(f"Route 2: Pickups to control cavity")
    # Neck pickup to bridge pickup to control cavity
    for wp in range(num_ch_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -ch_depth:
            wz = -ch_depth
        # On rear face, pickup X center is mirrored (0.0 stays 0.0)
        npu_rx, npu_ry = spec_to_gcode(-npu_bp["x_center"], npu_bp["y_from_top"], body_w, body_h)
        g.rapid(x=npu_rx, y=npu_ry)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        bpu_rx, bpu_ry = spec_to_gcode(-bpu_bp["x_center"], bpu_bp["y_from_top"], body_w, body_h)
        g.linear(x=bpu_rx, y=bpu_ry, f=T3_FEED)
        g.linear(x=cc_cx, y=cc_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    # Route 3: Control cavity to output jack
    oj = spec["output_jack"]
    oj_bp = oj["body_position_mm"]
    oj_cx, oj_cy = spec_to_gcode(-oj_bp["x_center"], oj_bp["y_from_top"], body_w, body_h)
    g.comment(f"Route 3: Control cavity to output jack ({oj_cx:.1f}, {oj_cy:.1f})")
    for wp in range(num_ch_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -ch_depth:
            wz = -ch_depth
        g.rapid(x=cc_cx, y=cc_cy)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=oj_cx, y=oj_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    # -----------------------------------------------------------------------
    # OP60: Pot Shaft Holes (3x, 9.53mm through body)
    # -----------------------------------------------------------------------
    g.section("OP60: POT SHAFT HOLES (3x 9.53mm through)")
    pot_holes = cc["pot_shaft_holes"]
    pot_dia = pot_holes["diameter_mm"]    # 9.53
    pot_count = pot_holes["count"]        # 3

    g.comment(f"{pot_count} pot holes at {pot_dia}mm diameter through {stock_t}mm body")
    g.comment("Layout: 2 volume + 1 tone, arranged around control cavity")

    # Explorer 3-knob layout: spaced along the lower body
    pot_spacing = 30.0  # mm between pot centers
    pot_positions = [
        (cc_cx - pot_spacing, cc_cy),      # Volume (neck)
        (cc_cx, cc_cy + pot_spacing / 2),  # Volume (bridge)
        (cc_cx + pot_spacing, cc_cy),      # Tone (master)
    ]
    for i, (px, py) in enumerate(pot_positions):
        names = ["Volume Neck", "Volume Bridge", "Master Tone"]
        helical_bore(g, names[i], px, py, pot_dia, stock_t,
                     T3_DIA, T3_DOC, T3_PLUNGE, T3_FEED, "OP60")

    # -----------------------------------------------------------------------
    # OP61: Bridge Post Holes (2x, 11.1mm)
    # -----------------------------------------------------------------------
    g.section("OP61: BRIDGE POST HOLES (2x 11.1mm)")
    br = spec["bridge"]
    br_bp = br["body_position_mm"]
    br_cx, br_cy = spec_to_gcode(-br_bp["x_center"], br_bp["y_from_top"], body_w, body_h)
    br_stud_spacing = br["stud_spacing_mm"]  # 74.0
    br_stud_dia = br["stud_diameter_mm"]     # 11.1
    br_stud_depth = br["stud_depth_mm"]      # 19.05

    g.comment(f"Bridge center: ({br_cx:.1f}, {br_cy:.1f}), stud spacing: {br_stud_spacing}mm")
    bridge_holes = [
        (br_cx - br_stud_spacing / 2, br_cy),
        (br_cx + br_stud_spacing / 2, br_cy),
    ]
    for i, (bx, by) in enumerate(bridge_holes):
        helical_bore(g, f"Bridge Post {i + 1}", bx, by, br_stud_dia, br_stud_depth,
                     T3_DIA, T3_DOC, T3_PLUNGE, T3_FEED, "OP61")

    # -----------------------------------------------------------------------
    # OP62: Tailpiece Stud Holes (2x, 7.14mm)
    # -----------------------------------------------------------------------
    g.section("OP62: TAILPIECE STUD HOLES (2x 7.14mm)")
    tp = spec["tailpiece"]
    tp_bp = tp["body_position_mm"]
    tp_cx, tp_cy = spec_to_gcode(-tp_bp["x_center"], tp_bp["y_from_top"], body_w, body_h)
    tp_stud_spacing = tp["stud_spacing_mm"]  # 82.5
    tp_stud_dia = tp["stud_diameter_mm"]     # 7.14
    tp_stud_depth = tp["stud_depth_mm"]      # 15.88

    g.comment(f"Tailpiece center: ({tp_cx:.1f}, {tp_cy:.1f}), stud spacing: {tp_stud_spacing}mm")
    tailpiece_holes = [
        (tp_cx - tp_stud_spacing / 2, tp_cy),
        (tp_cx + tp_stud_spacing / 2, tp_cy),
    ]
    for i, (tx, ty) in enumerate(tailpiece_holes):
        helical_bore(g, f"Tailpiece Stud {i + 1}", tx, ty, tp_stud_dia, tp_stud_depth,
                     T3_DIA, T3_DOC, T3_PLUNGE, T3_FEED, "OP62")

    # -----------------------------------------------------------------------
    # OP63: Toggle Switch Hole (12.7mm through)
    # -----------------------------------------------------------------------
    g.section("OP63: TOGGLE SWITCH HOLE (12.7mm through)")
    toggle_dia = cc["toggle_switch"]["hole_diameter_mm"]  # 12.7
    g.comment(f"Toggle at ({ts_cx:.1f}, {ts_cy:.1f}), {toggle_dia}mm through body")
    helical_bore(g, "Toggle Switch", ts_cx, ts_cy, toggle_dia, stock_t,
                 T3_DIA, T3_DOC, T3_PLUNGE, T3_FEED, "OP63")

    # -----------------------------------------------------------------------
    # OP64: Output Jack Bore (12.7mm)
    # -----------------------------------------------------------------------
    g.section("OP64: OUTPUT JACK BORE (12.7mm)")
    oj_dia = oj["bore_diameter_mm"]    # 12.7
    oj_depth = oj["bore_depth_mm"]     # 25.0
    g.comment(f"Output jack at ({oj_cx:.1f}, {oj_cy:.1f}), {oj_dia}mm x {oj_depth}mm deep")
    g.comment("NOTE: Jack is on lower body edge — may require angled fixture for edge-mount.")
    helical_bore(g, "Output Jack", oj_cx, oj_cy, oj_dia, oj_depth,
                 T3_DIA, T3_DOC, T3_PLUNGE, T3_FEED, "OP64")

    # -----------------------------------------------------------------------
    # OP65: Cover Screw Pilot Holes (4x)
    # -----------------------------------------------------------------------
    g.section("OP65: COVER SCREW PILOT HOLES (4x)")
    cover_screw_count = spec["cover_recess"]["screw_count"]  # 4
    screw_margin = 4.0  # mm from cover edge to screw center
    cs_hw = (cc["length_mm"] + 2 * cover_margin) / 2 - screw_margin
    cs_hh = (cc["width_mm"] + 2 * cover_margin) / 2 - screw_margin

    screw_holes = [
        (cc_cx - cs_hw, cc_cy - cs_hh),
        (cc_cx + cs_hw, cc_cy - cs_hh),
        (cc_cx + cs_hw, cc_cy + cs_hh),
        (cc_cx - cs_hw, cc_cy + cs_hh),
    ]
    for i, (sx, sy) in enumerate(screw_holes):
        g.comment(f"Cover screw {i + 1}: ({sx:.1f}, {sy:.1f})")
        g.peck_drill(sx, sy, -12.7, RETRACT_Z, 3.0, T3_PLUNGE)
    g.cancel_canned()

    g.footer()
    return g.text()


# ---------------------------------------------------------------------------
# Phase 2: Body Perimeter Profile
# ---------------------------------------------------------------------------

def generate_phase2_perimeter(spec: Dict[str, Any],
                              outline_mm: List[Tuple[float, float]]) -> str:
    """Generate perimeter profile cut (body flipped, front face up)."""

    g = GCodeBuilder()
    g.header(
        "Explorer_1958_Phase2_Perimeter",
        "GRBL_3018_Default",
        "Korina (African Limba) — FLIPPED, front face up",
        "Phase 2: Perimeter Profile"
    )

    body = spec["body"]
    body_w = body["width_mm"]        # 475.0
    body_h = body["length_mm"]       # 460.0
    stock_t = body["thickness_mm"]   # 44.45

    g.comment("OPERATOR: Flip body to front face up. Re-zero Z to front surface.")
    g.comment("Use registration pins from OP10 for alignment.")
    g.comment("")

    g.tool_change(2, "6mm Flat End Mill", T2_RPM, "OP50: Body perimeter profile")
    g.section("OP50: BODY PERIMETER CONTOUR")

    # Transform outline to G-code coordinates
    xs = [p[0] for p in outline_mm[:-1]]
    ys = [p[1] for p in outline_mm[:-1]]
    dxf_w = max(xs) - min(xs)
    dxf_h = max(ys) - min(ys)

    # Scale DXF outline to match body dimensions
    scale_x = body_w / dxf_w if dxf_w > 0 else 1.0
    scale_y = body_h / dxf_h if dxf_h > 0 else 1.0
    outline_gcode = []
    for px, py in outline_mm:
        gx = (px - min(xs)) * scale_x
        gy = (py - min(ys)) * scale_y
        outline_gcode.append((gx, gy))

    # Offset outline outward by half tool diameter + finish allowance
    tool_offset = T2_DIA / 2 + 0.25
    perimeter_pts = offset_polygon(outline_gcode, -tool_offset)
    perim_len = path_length(perimeter_pts)
    tab_count = 8
    tab_width = 12.0
    tab_height = 3.0

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
# Build summary JSON
# ---------------------------------------------------------------------------

def generate_build_summary(spec: Dict[str, Any], phase1_lines: int,
                           phase2_lines: int) -> str:
    """Generate build summary JSON."""

    summary = {
        "model": "1958 Gibson Explorer",
        "spec_file": "instrument_geometry/specs/gibson_explorer.json",
        "generated": datetime.now().isoformat(),
        "generator": "The Production Shop - Explorer 1958 Full Build Generator",
        "design": {
            "body_style": "angular_explorer_asymmetric",
            "neck": "set_neck_long_tenon",
            "scale_length_mm": 628.65,
            "frets": 22,
            "material": "Korina (African Limba)",
            "material_alternative": "Mahogany",
        },
        "phases": {
            "phase1_rear_routing": {
                "file": "Explorer_1958_Phase1_RearRouting.nc",
                "units": "mm (G21)",
                "operations": [
                    "OP10: Fixture holes 4x (T3 3mm)",
                    "OP20: Neck pocket rough (T1 10mm)",
                    "OP21: Neck pickup cavity rough (T1 10mm)",
                    "OP22: Bridge pickup cavity rough (T1 10mm)",
                    "OP23: Control cavity rough (T1 10mm)",
                    "OP25: Neck pocket finish (T2 6mm)",
                    "OP26: Neck pickup cavity finish (T2 6mm)",
                    "OP27: Bridge pickup cavity finish (T2 6mm)",
                    "OP28: Control cavity finish (T2 6mm)",
                    "OP35: Cover plate recess (T2 6mm)",
                    "OP40: Wiring channels 3 routes (T3 3mm)",
                    "OP60: Pot shaft holes 3x 9.53mm (T3 3mm)",
                    "OP61: Bridge post holes 2x 11.1mm (T3 3mm)",
                    "OP62: Tailpiece stud holes 2x 7.14mm (T3 3mm)",
                    "OP63: Toggle switch hole 12.7mm (T3 3mm)",
                    "OP64: Output jack bore 12.7mm (T3 3mm)",
                    "OP65: Cover screw pilot holes 4x (T3 3mm)",
                ],
                "gcode_lines": phase1_lines,
            },
            "phase2_perimeter": {
                "file": "Explorer_1958_Phase2_Perimeter.nc",
                "units": "mm (G21)",
                "operations": [
                    "OP50: Body perimeter contour with 8 tabs (T2 6mm)",
                ],
                "gcode_lines": phase2_lines,
            },
        },
        "tool_library": {
            "T1": {"name": "10mm Flat End Mill", "diameter_mm": 10.0, "rpm": 18000},
            "T2": {"name": "6mm Flat End Mill", "diameter_mm": 6.0, "rpm": 18000},
            "T3": {"name": "3mm Flat/Drill", "diameter_mm": 3.0, "rpm": 20000},
        },
        "totals": {
            "phases": 2,
            "operations": 18,
            "tools": 3,
            "total_gcode_lines": phase1_lines + phase2_lines,
        },
    }
    return json.dumps(summary, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("  Gibson Explorer 1958 — Full CNC Build Generator")
    print("  The Production Shop")
    print("=" * 70)
    print()

    # Load spec
    print(f"Loading spec: {SPEC_PATH}")
    spec = load_spec()
    print(f"  Model: {spec['display_name']}")
    print(f"  Body: {spec['body']['width_mm']} x {spec['body']['length_mm']} x {spec['body']['thickness_mm']} mm")
    print(f"  Material: {spec['body']['material']}")
    print(f"  Scale: {spec['variants']['original_1958']['scale_length_mm']}mm (24.75\")")
    print()

    # Load outline
    print(f"Loading body outline: {DXF_PATH}")
    outline_mm = load_body_outline_from_dxf()
    xs = [p[0] for p in outline_mm]
    ys = [p[1] for p in outline_mm]
    print(f"  Points: {len(outline_mm)}")
    print(f"  DXF extents: {max(xs) - min(xs):.1f} x {max(ys) - min(ys):.1f} mm")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1: Rear Face Routing
    print("Generating Phase 1: Rear Face Routing...")
    phase1_gcode = generate_phase1_rear(spec)
    phase1_lines = len(phase1_gcode.split("\n"))
    phase1_path = OUTPUT_DIR / "Explorer_1958_Phase1_RearRouting.nc"
    phase1_path.write_text(phase1_gcode, encoding="utf-8")
    print(f"  Written: {phase1_path.name} ({phase1_lines:,} lines)")

    # Verify Phase 1 G-code (EX-GAP-12)
    v1 = verify_gcode(
        gcode=phase1_gcode,
        stock_thickness_mm=44.45,  # 1.75" Korina
        phase_name="Phase 1: Rear Face Routing",
        units="mm",
    )

    # Phase 2: Perimeter Profile
    print("Generating Phase 2: Perimeter Profile...")
    phase2_gcode = generate_phase2_perimeter(spec, outline_mm)
    phase2_lines = len(phase2_gcode.split("\n"))
    phase2_path = OUTPUT_DIR / "Explorer_1958_Phase2_Perimeter.nc"
    phase2_path.write_text(phase2_gcode, encoding="utf-8")
    print(f"  Written: {phase2_path.name} ({phase2_lines:,} lines)")

    # Verify Phase 2 G-code (EX-GAP-12)
    v2 = verify_gcode(
        gcode=phase2_gcode,
        stock_thickness_mm=44.45,  # 1.75" Korina
        phase_name="Phase 2: Perimeter Profile",
        units="mm",
    )

    # Build summary
    print("Generating build summary...")
    summary_json = generate_build_summary(spec, phase1_lines, phase2_lines)
    summary_path = OUTPUT_DIR / "Explorer_1958_BuildSummary.json"
    summary_path.write_text(summary_json, encoding="utf-8")
    print(f"  Written: {summary_path.name}")

    # Totals
    total_lines = phase1_lines + phase2_lines
    print()
    print("=" * 70)
    print(f"  BUILD COMPLETE")
    print(f"  Total G-code: {total_lines:,} lines across 2 phases")
    print(f"  Phase 1 (Rear Routing): {phase1_lines:,} lines")
    print(f"  Phase 2 (Perimeter):    {phase2_lines:,} lines")
    print(f"  Output: {OUTPUT_DIR}")

    # Verification summary (EX-GAP-12)
    all_ok = v1["ok"] and v2["ok"]
    if all_ok:
        print(f"\n  ✓ G-CODE VERIFICATION: ALL PHASES PASSED")
    else:
        print(f"\n  ✗ G-CODE VERIFICATION FAILED - review errors before machining")
        if not v1["ok"]:
            print(f"    Phase 1 errors: {v1['errors']}")
        if not v2["ok"]:
            print(f"    Phase 2 errors: {v2['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
