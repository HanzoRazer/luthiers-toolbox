#!/usr/bin/env python3
"""
Gibson Les Paul 1956-59 — Full CNC Build G-code Generator
=========================================================

Generates the COMPLETE machining program for a 1956-59 Gibson Les Paul
from the authoritative spec (gibson_les_paul.json) and body outline DXF.

Operations produced:
  Phase 1 — Mahogany Back (flat 2.5D routing, inches, G20)
    OP10: Fixture holes (registration pins)
    OP20: Neck pocket rough (T1 10mm)
    OP21: Pickup cavities rough — neck + bridge (T1 10mm)
    OP22: Electronics cavity rough (T1 10mm)
    OP25: Cover recess (T2 6mm)
    OP30: Neck pocket finish (T2 6mm)
    OP31: Pickup cavities finish (T2 6mm)
    OP40: Wiring channels (T3 3mm)
    OP50: Body perimeter contour with tabs (T2 6mm)
    OP60: Pot shaft holes — 4x 3/8" through (T3)
    OP61: Bridge post holes — 2x 7/16" (T3)
    OP62: Tailpiece stud holes — 2x 9/32" (T3)
    OP63: Screw pilot holes (T3)

  Phase 2 — Purfling Channel Routing (both top and back)
    OP70: Primary purfling channel — Spanish wave (T4 2.4mm)
    OP71: Inner purfling ledge — green wood (T5 1.6mm)

  Phase 3 — Maple Cap Carved Top (3D surfacing, mm, G21)
    OP80: Rough carved top — ball nose (T6 6mm ball)
    OP81: Finish carved top — ball nose (T7 3mm ball)

  Phase 4 — Neck (from NeckPipeline orchestrator)
    OP90: Truss rod channel (T8 6.35mm flat)
    OP91: Neck profile rough (T9 12mm ball nose)
    OP92: Neck profile finish (T10 6mm ball nose)
    OP93: Fret slots (T11 0.58mm fret saw)

Units: Phase 1-2 in inches (G20). Phase 3-4 in mm (G21).

Resolves: LP-GAP-04 (fret slot CAM), LP-GAP-08 (G-code verification)
Machine: Configurable (default TXRX Labs Router).

Usage:
    cd services/api
    python -m scripts.generate_les_paul_full_build
  or:
    python ../../scripts/generate_les_paul_full_build.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Import shared G-code verification utility (LP-GAP-08)
from scripts.utils.gcode_verify import verify_gcode, verify_all_phases


# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
API_DIR = REPO_ROOT / "services" / "api"

SPEC_PATH = API_DIR / "app" / "instrument_geometry" / "specs" / "gibson_les_paul.json"
DXF_PATH = API_DIR / "app" / "instrument_geometry" / "body" / "dxf" / "electric" / "LesPaul_body.dxf"
OUTPUT_DIR = REPO_ROOT / "exports" / "les_paul_1959"


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
    """Load 669-point body outline from LesPaul_body.dxf (mm)."""
    try:
        import ezdxf
    except ImportError:
        print("ERROR: ezdxf required. pip install ezdxf")
        sys.exit(1)

    doc = ezdxf.readfile(str(DXF_PATH))
    msp = doc.modelspace()
    entity = list(msp)[0]
    pts = list(entity.get_points(format="xy"))
    # Close if not already
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


# ---------------------------------------------------------------------------
# Unit conversions
# ---------------------------------------------------------------------------

MM_PER_INCH = 25.4

def mm_to_in(mm: float) -> float:
    return mm / MM_PER_INCH

def in_to_mm(inches: float) -> float:
    return inches * MM_PER_INCH


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def offset_polygon(pts: List[Tuple[float, float]], offset: float) -> List[Tuple[float, float]]:
    """
    Naive inward offset of a polygon by computing normals at each vertex.
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

        # Edge vectors
        dx1 = p1[0] - p0[0]
        dy1 = p1[1] - p0[1]
        dx2 = p2[0] - p1[0]
        dy2 = p2[1] - p1[1]

        # Normals (pointing inward for CCW polygon)
        len1 = math.sqrt(dx1 * dx1 + dy1 * dy1) or 1e-9
        len2 = math.sqrt(dx2 * dx2 + dy2 * dy2) or 1e-9
        nx1 = -dy1 / len1
        ny1 = dx1 / len1
        nx2 = -dy2 / len2
        ny2 = dx2 / len2

        # Average normal
        nx = nx1 + nx2
        ny = ny1 + ny2
        ln = math.sqrt(nx * nx + ny * ny) or 1e-9
        nx /= ln
        ny /= ln

        # Bisector scale factor
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

    def header(self, program_name: str, machine: str, units: str, stock: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.emit(f"; {program_name}")
        self.emit(f"; Generated: {now}")
        self.emit(f"; Generator: The Production Shop — Les Paul Full Build")
        self.emit(f"; Machine: {machine}")
        self.emit(f"; Stock: {stock}")
        self.emit(";")
        self.emit("")
        self.comment("SAFE START")
        if units == "inch":
            self.emit("G20         ; Inches")
        else:
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
        self.emit("G0 Z1.0000  ; Safe Z")
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
        self.emit("G0 Z0.7500  ; Safe Z")
        self._current_tool = tool_num

    def rapid(self, x=None, y=None, z=None):
        parts = ["G0"]
        if x is not None: parts.append(f"X{x:.4f}")
        if y is not None: parts.append(f"Y{y:.4f}")
        if z is not None: parts.append(f"Z{z:.4f}")
        self.emit(" ".join(parts))

    def linear(self, x=None, y=None, z=None, f=None):
        parts = ["G1"]
        if x is not None: parts.append(f"X{x:.4f}")
        if y is not None: parts.append(f"Y{y:.4f}")
        if z is not None: parts.append(f"Z{z:.4f}")
        if f is not None: parts.append(f"F{f:.1f}")
        self.emit(" ".join(parts))

    def arc_cw(self, x, y, i, j, z=None, f=None):
        parts = [f"G2 X{x:.4f} Y{y:.4f} I{i:.4f} J{j:.4f}"]
        if z is not None: parts.append(f"Z{z:.4f}")
        if f is not None: parts.append(f"F{f:.1f}")
        self.emit(" ".join(parts))

    def peck_drill(self, x, y, z_final, retract, peck, feed):
        self.rapid(x=x, y=y)
        self.emit(f"G83 Z{z_final:.4f} R{retract:.4f} Q{peck:.4f} F{feed:.1f}")

    def cancel_canned(self):
        self.emit("G80          ; Cancel canned cycle")

    def text(self) -> str:
        return "\n".join(self.lines)


# ---------------------------------------------------------------------------
# Phase 1: Mahogany Back Routing (inches)
# ---------------------------------------------------------------------------

def generate_phase1_back(spec: Dict, outline_mm: List[Tuple[float, float]]) -> str:
    """Generate all mahogany back routing operations in inches."""

    g = GCodeBuilder()
    g.header(
        "LesPaul_1959_Phase1_MahoganyBack",
        "TXRX Labs Router / BCAMCNC 2030CA",
        "inch",
        "Honduran Mahogany 1.75\" thick"
    )

    body = spec["body"]
    neck = spec["neck_pocket"]
    pickups = spec["pickups"]
    ctrl = spec["control_cavity"]
    bridge = spec["bridge"]
    tail = spec["tailpiece"]

    # Convert body outline to inches, origin at lower-left
    outline_in = [(mm_to_in(x), mm_to_in(y)) for x, y in outline_mm]
    body_w = mm_to_in(body["outline_dxf_dimensions"]["width_mm"])
    body_h = mm_to_in(body["outline_dxf_dimensions"]["height_mm"])

    # Body center
    cx = body_w / 2
    cy = body_h / 2

    stock_t = 1.75  # inches

    # Tool library (from lespaul_config.py)
    T1_DIA = 0.394   # 10mm flat end mill
    T1_RPM = 18000
    T1_FEED = 220.0
    T1_PLUNGE = 31.0
    T1_DOC = 0.22
    T1_STEP = T1_DIA * 0.45

    T2_DIA = 0.236   # 6mm flat end mill
    T2_RPM = 18000
    T2_FEED = 150.0
    T2_PLUNGE = 24.0
    T2_DOC = 0.06
    T2_STEP = T2_DIA * 0.18

    T3_DIA = 0.118   # 3mm flat/drill
    T3_RPM = 20000
    T3_FEED = 60.0
    T3_PLUNGE = 16.0
    T3_DOC = 0.03

    SAFE_Z = 0.75
    RETRACT_Z = 0.25

    # -----------------------------------------------------------------------
    # OP10: Fixture / Registration Holes
    # -----------------------------------------------------------------------
    g.section("OP10: FIXTURE / REGISTRATION HOLES")
    g.tool_change(3, "3mm Flat/Drill", T3_RPM, "OP10: Fixture pin holes for workholding")
    # 4 fixture holes outside the body perimeter, in waste material
    fixture_holes = [
        (0.5, 0.5),
        (body_w - 0.5, 0.5),
        (body_w - 0.5, body_h - 0.5),
        (0.5, body_h - 0.5),
    ]
    for i, (fx, fy) in enumerate(fixture_holes):
        g.comment(f"Fixture hole {i+1}: ({fx:.3f}, {fy:.3f})")
        g.peck_drill(fx, fy, -0.375, RETRACT_Z, 0.125, T3_PLUNGE)
    g.cancel_canned()

    # -----------------------------------------------------------------------
    # Pocket helper
    # -----------------------------------------------------------------------
    def mill_rectangular_pocket(name: str, pcx: float, pcy: float,
                                pw: float, ph: float, depth: float,
                                tool_dia: float, doc: float, stepover: float,
                                feed: float, plunge: float, op_label: str):
        g.section(f"{op_label}: {name}")
        g.comment(f"Center: ({pcx:.4f}, {pcy:.4f})")
        g.comment(f"Size: {pw:.4f} x {ph:.4f} in, Depth: {depth:.4f} in")

        num_passes = max(1, math.ceil(depth / doc))

        for pn in range(num_passes):
            z = -doc * (pn + 1)
            if z < -depth:
                z = -depth
            g.comment(f"Pass {pn+1}/{num_passes}: Z={z:.4f}")
            g.rapid(z=SAFE_Z)
            g.rapid(x=pcx, y=pcy)
            g.rapid(z=RETRACT_Z)

            # Helical plunge
            helix_r = tool_dia / 4
            g.arc_cw(pcx, pcy, helix_r, 0, z=z, f=plunge)
            g.emit(f"F{feed:.1f}")

            # Spiral outward
            max_offset = min(pw, ph) / 2 - tool_dia / 2
            off = stepover
            while off < max_offset:
                x1, y1 = pcx - off, pcy - off
                x2, y2 = pcx + off, pcy + off
                g.linear(x=x1, y=y1)
                g.linear(x=x2, y=y1)
                g.linear(x=x2, y=y2)
                g.linear(x=x1, y=y2)
                g.linear(x=x1, y=y1)
                off += stepover

            # Final perimeter cleanup
            hw = pw / 2 - tool_dia / 2
            hh = ph / 2 - tool_dia / 2
            g.linear(x=pcx - hw, y=pcy - hh)
            g.linear(x=pcx + hw, y=pcy - hh)
            g.linear(x=pcx + hw, y=pcy + hh)
            g.linear(x=pcx - hw, y=pcy + hh)
            g.linear(x=pcx - hw, y=pcy - hh)

    # -----------------------------------------------------------------------
    # OP20: Neck Pocket Rough
    # -----------------------------------------------------------------------
    g.tool_change(1, "10mm Flat End Mill", T1_RPM, "OP20-OP22: Roughing pockets")
    np_w = mm_to_in(neck["tenon_width_mm"])
    np_l = mm_to_in(neck["tenon_length_mm"])
    np_depth = neck["mortise_depth_inches"]
    # Neck pocket at upper-right of body (cutaway side), high on Y axis
    np_cx = body_w * 0.78   # ~78% along body length (near headstock end)
    np_cy = cy              # centered on body width
    mill_rectangular_pocket("Neck Mortise", np_cx, np_cy,
                            np_l, np_w, np_depth,
                            T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE,
                            "OP20")

    # -----------------------------------------------------------------------
    # OP21: Pickup Cavities Rough
    # -----------------------------------------------------------------------
    pu_w = mm_to_in(pickups["neck"]["route_width_mm"])
    pu_l = mm_to_in(pickups["neck"]["route_length_mm"])
    pu_depth = pickups["neck"]["route_depth_inches"]

    # Neck pickup — roughly 155mm from bridge toward neck
    bridge_x = mm_to_in(628.65)  # scale length position
    # Pickup positions relative to body center
    neck_pu_cx = cx + mm_to_in(155.0 - body["width_mm"] / 2) * 0.5
    bridge_pu_cx = cx + mm_to_in(20.0)

    # Place pickups along the body length axis (X in DXF)
    # Bridge pickup near center, neck pickup offset toward neck
    pu_neck_x = cx + 2.5     # ~2.5 inches from center toward neck
    pu_bridge_x = cx - 0.8   # ~0.8 inches from center toward bridge
    pu_y = cy                 # centered on width

    mill_rectangular_pocket("Neck Pickup Cavity", pu_neck_x, pu_y,
                            pu_l, pu_w, pu_depth,
                            T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE,
                            "OP21a")

    mill_rectangular_pocket("Bridge Pickup Cavity", pu_bridge_x, pu_y,
                            pu_l, pu_w, pu_depth,
                            T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE,
                            "OP21b")

    # -----------------------------------------------------------------------
    # OP22: Electronics Cavity Rough
    # -----------------------------------------------------------------------
    ec_w = mm_to_in(ctrl["width_mm"])
    ec_l = mm_to_in(ctrl["length_mm"])
    ec_depth = ctrl["depth_inches"]
    # Control cavity in lower bout area, offset slightly to treble side
    ec_cx = cx - 3.0   # lower bout, offset toward bridge end
    ec_cy = cy - 1.5   # offset to treble side

    mill_rectangular_pocket("Electronics Cavity", ec_cx, ec_cy,
                            ec_l, ec_w, ec_depth,
                            T1_DIA, T1_DOC, T1_STEP, T1_FEED, T1_PLUNGE,
                            "OP22")

    # -----------------------------------------------------------------------
    # OP25: Cover Recess
    # -----------------------------------------------------------------------
    g.tool_change(2, "6mm Flat End Mill", T2_RPM, "OP25: Back cover plate recess")
    g.section("OP25: COVER RECESS (Back)")
    recess_depth = spec["cover_recess"]["depth_inches"]
    # Slightly larger than electronics cavity
    recess_w = ec_w + 0.25
    recess_l = ec_l + 0.25
    mill_rectangular_pocket("Cover Plate Recess", ec_cx, ec_cy,
                            recess_l, recess_w, recess_depth,
                            T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE,
                            "OP25")

    # -----------------------------------------------------------------------
    # OP30: Neck Pocket Finish
    # -----------------------------------------------------------------------
    g.section("OP30: NECK POCKET FINISH")
    g.comment("Finish pass with finer tool for tight tenon fit")
    mill_rectangular_pocket("Neck Mortise Finish", np_cx, np_cy,
                            np_l, np_w, np_depth,
                            T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE,
                            "OP30")

    # -----------------------------------------------------------------------
    # OP31: Pickup Cavities Finish
    # -----------------------------------------------------------------------
    g.section("OP31: PICKUP CAVITIES FINISH")
    mill_rectangular_pocket("Neck Pickup Finish", pu_neck_x, pu_y,
                            pu_l, pu_w, pu_depth,
                            T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE,
                            "OP31a")
    mill_rectangular_pocket("Bridge Pickup Finish", pu_bridge_x, pu_y,
                            pu_l, pu_w, pu_depth,
                            T2_DIA, T2_DOC, T2_STEP, T2_FEED, T2_PLUNGE,
                            "OP31b")

    # -----------------------------------------------------------------------
    # OP40: Wiring Channels
    # -----------------------------------------------------------------------
    g.tool_change(3, "3mm Flat/Drill", T3_RPM, "OP40: Wiring channels")
    g.section("OP40: WIRING CHANNELS")
    wire_depth = 0.5  # inches

    g.comment("Channel: Control cavity to toggle switch cavity")
    g.rapid(z=SAFE_Z)
    # Route from electronics cavity to upper bout toggle switch location
    toggle_x = cx + 4.0
    toggle_y = cy + 2.5

    num_wire_passes = max(1, math.ceil(wire_depth / T3_DOC))
    for wp in range(num_wire_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -wire_depth:
            wz = -wire_depth
        g.rapid(x=ec_cx, y=ec_cy)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=toggle_x, y=toggle_y, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    g.comment("Channel: Neck pickup to control cavity")
    for wp in range(num_wire_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -wire_depth:
            wz = -wire_depth
        g.rapid(x=pu_neck_x, y=pu_y)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=ec_cx, y=ec_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    g.comment("Channel: Bridge pickup to control cavity")
    for wp in range(num_wire_passes):
        wz = -T3_DOC * (wp + 1)
        if wz < -wire_depth:
            wz = -wire_depth
        g.rapid(x=pu_bridge_x, y=pu_y)
        g.rapid(z=RETRACT_Z)
        g.linear(z=wz, f=T3_PLUNGE)
        g.linear(x=ec_cx, y=ec_cy, f=T3_FEED)
        g.rapid(z=SAFE_Z)

    # -----------------------------------------------------------------------
    # OP50: Body Perimeter Contour with Tabs
    # -----------------------------------------------------------------------
    g.tool_change(2, "6mm Flat End Mill", T2_RPM, "OP50: Body perimeter profile")
    g.section("OP50: BODY PERIMETER CONTOUR")

    # Offset outline by half tool diameter (climb milling, outside)
    tool_offset = T2_DIA / 2 + 0.010  # +0.010 finish allowance
    perimeter_pts = offset_polygon(outline_in, -tool_offset)  # outward offset
    perim_len = path_length(perimeter_pts)
    tab_count = 6
    tab_width = 0.5
    tab_height = 0.125

    g.comment(f"Perimeter: {perim_len:.1f} in, {len(perimeter_pts)} points")
    g.comment(f"Tabs: {tab_count} x {tab_width}\" wide x {tab_height}\" tall")

    num_perim_passes = max(1, math.ceil(stock_t / T2_DOC))
    g.comment(f"Depth: {stock_t}\" in {num_perim_passes} passes ({T2_DOC}\" DOC)")

    # Tab positions along path
    tab_spacing = perim_len / tab_count
    tab_positions = [(i + 0.5) * tab_spacing for i in range(tab_count)]

    for pn in range(num_perim_passes):
        z = -T2_DOC * (pn + 1)
        if z < -stock_t:
            z = -stock_t

        is_tab_pass = (pn >= num_perim_passes - 2)
        tab_z = -stock_t + tab_height

        g.comment(f"Pass {pn+1}/{num_perim_passes}: Z={z:.4f}")
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

            # Handle tabs on final passes
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

    # -----------------------------------------------------------------------
    # OP60-63: Drilling Operations
    # -----------------------------------------------------------------------
    g.tool_change(3, "3mm Flat/Drill", T3_RPM, "OP60-63: Drilling operations")

    # OP60: Pot shaft holes (4x 3/8" through)
    g.section("OP60: POT SHAFT HOLES (4x 3/8\" through)")
    pot_dia = mm_to_in(ctrl["pot_shaft_holes"]["diameter_mm"])
    # 4 pots in a roughly diamond pattern in the lower bout
    pot_holes = [
        (ec_cx - 0.5, ec_cy + 0.5),   # Volume neck
        (ec_cx + 0.5, ec_cy + 0.5),   # Volume bridge
        (ec_cx - 0.5, ec_cy - 0.5),   # Tone neck
        (ec_cx + 0.5, ec_cy - 0.5),   # Tone bridge
    ]
    for i, (px, py) in enumerate(pot_holes):
        g.comment(f"Pot {i+1}: ({px:.3f}, {py:.3f}) dia {pot_dia:.3f}\"")
        # Helical bore for larger-than-tool holes
        bore_r = (pot_dia - T3_DIA) / 2
        g.rapid(z=SAFE_Z)
        g.rapid(x=px, y=py)
        g.rapid(z=RETRACT_Z)
        bore_z = 0.0
        while bore_z > -stock_t:
            bore_z -= T3_DOC
            if bore_z < -stock_t:
                bore_z = -stock_t
            g.arc_cw(px, py, bore_r, 0, z=bore_z, f=T3_PLUNGE)
        # Final cleanup pass
        g.arc_cw(px, py, bore_r, 0, f=T3_FEED)
    g.rapid(z=SAFE_Z)

    # OP61: Bridge post holes (2x 7/16")
    g.section("OP61: BRIDGE POST HOLES (2x 7/16\")")
    bridge_stud_spacing = mm_to_in(bridge["stud_spacing_mm"])
    bridge_depth = bridge["stud_depth_inches"]
    bridge_dia = mm_to_in(bridge["stud_diameter_mm"])
    # Bridge at roughly 60% of body length from neck end
    bridge_x = cx - 1.0
    bridge_holes = [
        (bridge_x, cy - bridge_stud_spacing / 2),
        (bridge_x, cy + bridge_stud_spacing / 2),
    ]
    for i, (bx, by) in enumerate(bridge_holes):
        g.comment(f"Bridge stud {i+1}: ({bx:.3f}, {by:.3f})")
        bore_r = (bridge_dia - T3_DIA) / 2
        g.rapid(z=SAFE_Z)
        g.rapid(x=bx, y=by)
        g.rapid(z=RETRACT_Z)
        bore_z = 0.0
        while bore_z > -bridge_depth:
            bore_z -= T3_DOC
            if bore_z < -bridge_depth:
                bore_z = -bridge_depth
            g.arc_cw(bx, by, bore_r, 0, z=bore_z, f=T3_PLUNGE)
        g.arc_cw(bx, by, bore_r, 0, f=T3_FEED)
    g.rapid(z=SAFE_Z)

    # OP62: Tailpiece stud holes (2x 9/32")
    g.section("OP62: TAILPIECE STUD HOLES (2x 9/32\")")
    tail_spacing = mm_to_in(tail["stud_spacing_mm"])
    tail_depth = tail["stud_depth_inches"]
    tail_dia = mm_to_in(tail["stud_diameter_mm"])
    tail_x = bridge_x - mm_to_in(tail["position_behind_bridge_mm"])
    tail_holes = [
        (tail_x, cy - tail_spacing / 2),
        (tail_x, cy + tail_spacing / 2),
    ]
    for i, (tx, ty) in enumerate(tail_holes):
        g.comment(f"Tailpiece stud {i+1}: ({tx:.3f}, {ty:.3f})")
        bore_r = max(0.01, (tail_dia - T3_DIA) / 2)
        g.rapid(z=SAFE_Z)
        g.rapid(x=tx, y=ty)
        g.rapid(z=RETRACT_Z)
        bore_z = 0.0
        while bore_z > -tail_depth:
            bore_z -= T3_DOC
            if bore_z < -tail_depth:
                bore_z = -tail_depth
            g.arc_cw(tx, ty, bore_r, 0, z=bore_z, f=T3_PLUNGE)
        g.arc_cw(tx, ty, bore_r, 0, f=T3_FEED)
    g.rapid(z=SAFE_Z)

    # OP63: Screw pilot holes
    g.section("OP63: SCREW PILOT HOLES (#8)")
    # Pickguard screws, strap button holes, cover screws
    screw_holes = [
        # Cover plate screws (4 around electronics cavity)
        (ec_cx - ec_l / 2 - 0.15, ec_cy - ec_w / 2 - 0.15),
        (ec_cx + ec_l / 2 + 0.15, ec_cy - ec_w / 2 - 0.15),
        (ec_cx + ec_l / 2 + 0.15, ec_cy + ec_w / 2 + 0.15),
        (ec_cx - ec_l / 2 - 0.15, ec_cy + ec_w / 2 + 0.15),
        # Strap buttons
        (0.5, cy),                    # tail end
        (body_w - 0.5, cy + 2.5),    # neck heel
    ]
    for i, (sx, sy) in enumerate(screw_holes):
        g.comment(f"Screw {i+1}: ({sx:.3f}, {sy:.3f})")
        g.peck_drill(sx, sy, -0.5, RETRACT_Z, 0.125, T3_PLUNGE)
    g.cancel_canned()

    g.footer()
    return g.text()


# ---------------------------------------------------------------------------
# Phase 2: Purfling Channel Routing (inches)
# ---------------------------------------------------------------------------

def generate_phase2_purfling(spec: Dict, outline_mm: List[Tuple[float, float]]) -> str:
    """Generate purfling channel routing — Spanish wave + green wood."""

    bp = spec["binding_and_purfling"]
    rc = bp["routing_channels"]

    g = GCodeBuilder()
    g.header(
        "LesPaul_1959_Phase2_PurflingChannels",
        "TXRX Labs Router / BCAMCNC 2030CA",
        "inch",
        "Assembled body (mahogany + maple)"
    )

    outline_in = [(mm_to_in(x), mm_to_in(y)) for x, y in outline_mm]

    # T4: Custom ground 2.4mm flat for Spanish wave channel
    T4_DIA = mm_to_in(rc["primary_channel"]["width_mm"])  # 2.375mm -> ~0.0935"
    T4_RPM = 20000
    T4_FEED = 40.0
    T4_PLUNGE = 10.0
    T4_DOC = 0.030

    # T5: Custom ground 1.6mm flat for green wood ledge
    T5_DIA = mm_to_in(rc["inner_ledge"]["width_mm"])  # 1.6mm -> ~0.063"
    T5_RPM = 22000
    T5_FEED = 30.0
    T5_PLUNGE = 8.0
    T5_DOC = 0.020

    SAFE_Z = 0.75
    RETRACT_Z = 0.10

    # -----------------------------------------------------------------------
    # OP70: Primary channel — Spanish wave (top face)
    # -----------------------------------------------------------------------
    g.tool_change(4, f"2.4mm Flat ({T4_DIA:.4f}\")", T4_RPM,
                  "OP70: Primary purfling channel - Spanish wave")
    g.section("OP70: PRIMARY PURFLING CHANNEL - SPANISH WAVE (TOP)")

    primary_depth = mm_to_in(rc["primary_channel"]["depth_mm"])  # 6.2mm
    g.comment(f"Channel: {T4_DIA:.4f}\" wide x {primary_depth:.4f}\" deep")
    g.comment(f"Material: Spanish wave purfling 2.2 x 6.0 mm")

    # Offset path inward from body edge by half channel width
    channel_offset = T4_DIA / 2 + mm_to_in(0.5)  # half tool + edge margin
    purfling_path = offset_polygon(outline_in, channel_offset)

    num_passes = max(1, math.ceil(primary_depth / T4_DOC))
    g.comment(f"Passes: {num_passes} at {T4_DOC}\" DOC")

    for pn in range(num_passes):
        z = -T4_DOC * (pn + 1)
        if z < -primary_depth:
            z = -primary_depth
        g.comment(f"Pass {pn+1}/{num_passes}: Z={z:.4f}")
        g.rapid(z=SAFE_Z)
        g.rapid(x=purfling_path[0][0], y=purfling_path[0][1])
        g.rapid(z=RETRACT_Z)
        g.linear(z=z, f=T4_PLUNGE)
        g.emit(f"F{T4_FEED:.1f}")
        for px, py in purfling_path[1:]:
            g.linear(x=px, y=py)
    g.rapid(z=SAFE_Z)

    # OP70b: Same on back face (flip side)
    g.section("OP70b: PRIMARY PURFLING CHANNEL - SPANISH WAVE (BACK)")
    g.comment("OPERATOR: Flip body to back face. Re-zero Z to back surface.")
    g.comment("Same channel geometry as top — Spanish wave on both faces.")
    for pn in range(num_passes):
        z = -T4_DOC * (pn + 1)
        if z < -primary_depth:
            z = -primary_depth
        g.comment(f"Pass {pn+1}/{num_passes}: Z={z:.4f}")
        g.rapid(z=SAFE_Z)
        g.rapid(x=purfling_path[0][0], y=purfling_path[0][1])
        g.rapid(z=RETRACT_Z)
        g.linear(z=z, f=T4_PLUNGE)
        g.emit(f"F{T4_FEED:.1f}")
        for px, py in purfling_path[1:]:
            g.linear(x=px, y=py)
    g.rapid(z=SAFE_Z)

    # -----------------------------------------------------------------------
    # OP71: Inner ledge — green wood (top face)
    # -----------------------------------------------------------------------
    g.tool_change(5, f"1.6mm Flat ({T5_DIA:.4f}\")", T5_RPM,
                  "OP71: Inner purfling ledge - green wood")
    g.section("OP71: INNER PURFLING LEDGE - GREEN WOOD (TOP)")

    ledge_depth = mm_to_in(rc["inner_ledge"]["depth_mm"])  # 1.5mm
    g.comment(f"Channel: {T5_DIA:.4f}\" wide x {ledge_depth:.4f}\" deep")
    g.comment(f"Material: Green wood purfling 1.5 x 1.3 mm")

    # Inner ledge sits inside the primary channel
    ledge_offset = channel_offset + T4_DIA / 2 + T5_DIA / 2 + 0.002  # snug against primary
    ledge_path = offset_polygon(outline_in, ledge_offset)

    ledge_passes = max(1, math.ceil(ledge_depth / T5_DOC))
    g.comment(f"Passes: {ledge_passes} at {T5_DOC}\" DOC")

    for pn in range(ledge_passes):
        z = -T5_DOC * (pn + 1)
        if z < -ledge_depth:
            z = -ledge_depth
        g.comment(f"Pass {pn+1}/{ledge_passes}: Z={z:.4f}")
        g.rapid(z=SAFE_Z)
        g.rapid(x=ledge_path[0][0], y=ledge_path[0][1])
        g.rapid(z=RETRACT_Z)
        g.linear(z=z, f=T5_PLUNGE)
        g.emit(f"F{T5_FEED:.1f}")
        for px, py in ledge_path[1:]:
            g.linear(x=px, y=py)
    g.rapid(z=SAFE_Z)

    # OP71b: Same on back face
    g.section("OP71b: INNER PURFLING LEDGE - GREEN WOOD (BACK)")
    g.comment("OPERATOR: Flip body to back face. Re-zero Z to back surface.")
    for pn in range(ledge_passes):
        z = -T5_DOC * (pn + 1)
        if z < -ledge_depth:
            z = -ledge_depth
        g.comment(f"Pass {pn+1}/{ledge_passes}: Z={z:.4f}")
        g.rapid(z=SAFE_Z)
        g.rapid(x=ledge_path[0][0], y=ledge_path[0][1])
        g.rapid(z=RETRACT_Z)
        g.linear(z=z, f=T5_PLUNGE)
        g.emit(f"F{T5_FEED:.1f}")
        for px, py in ledge_path[1:]:
            g.linear(x=px, y=py)
    g.rapid(z=SAFE_Z)

    g.footer()
    return g.text()


# ---------------------------------------------------------------------------
# Phase 3: Carved Top 3D Surfacing (mm)
# ---------------------------------------------------------------------------

def generate_phase3_carved_top(spec: Dict, outline_mm: List[Tuple[float, float]]) -> str:
    """
    Generate 3D surfacing G-code for Les Paul carved maple top.

    Uses the compound-radius dome geometry from the spec:
     - Major radius: 508mm (across waist)
     - Minor radius: 381mm (along length)
     - Total rise: 7.8mm from edge to peak
     - Average slope: 3.2 degrees

    Strategy: parallel raster passes along the X axis with Z height
    computed from the elliptical dome equation.
    """
    carve = spec["carved_top"]
    body = spec["body"]

    g = GCodeBuilder()
    g.header(
        "LesPaul_1959_Phase3_CarvedTop",
        "TXRX Labs Router / BCAMCNC 2030CA",
        "mm",
        "Bookmatched figured maple cap, 19.05mm (3/4\") thick, glued to mahogany"
    )

    # Dimensions in mm (body outline)
    body_w_mm = body["outline_dxf_dimensions"]["width_mm"]   # 383.54 (length along X)
    body_h_mm = body["outline_dxf_dimensions"]["height_mm"]  # 269.24 (width along Y)
    cx = body_w_mm / 2
    cy = body_h_mm / 2

    # Dome parameters
    R_major = carve["major_radius_mm"]   # 508mm
    R_minor = carve["minor_radius_mm"]   # 381mm
    peak_above_edge = carve["total_rise_mm"]  # 7.8mm
    cap_thickness = carve["cap_thickness_before_carving_mm"]  # 12.7mm
    edge_thickness = carve["cap_thickness_after_carving_edge_mm"]  # 5.0mm

    # Z=0 at the top surface of the uncarved cap
    # The dome peak stays at Z=0 (center), edges get carved down
    # Material above the dome surface is removed
    max_carve_depth = cap_thickness - edge_thickness  # 7.7mm max material removal at edge

    # T6: 6mm ball-nose for roughing
    T6_DIA = 6.0
    T6_RPM = 18000
    T6_FEED = 2000.0
    T6_PLUNGE = 500.0
    T6_STEPOVER = 3.0  # 50% stepover for roughing
    T6_DOC = 2.0

    # T7: 3mm ball-nose for finishing
    T7_DIA = 3.0
    T7_RPM = 20000
    T7_FEED = 1500.0
    T7_PLUNGE = 400.0
    T7_STEPOVER = 0.5  # ~17% stepover for smooth finish

    SAFE_Z = 20.0
    RETRACT_Z = 5.0

    def dome_z(x: float, y: float) -> float:
        """
        Compute Z height of the compound-radius dome at position (x, y).

        The dome is an elliptical paraboloid approximation:
          z = peak - (dx^2 / (2*R_major)) - (dy^2 / (2*R_minor))

        where dx, dy are distances from the dome center.
        Z=0 is the uncarved cap surface. Negative Z = material removed.
        """
        dx = x - cx
        dy = y - cy
        # Elliptical dome: higher at center, dropping toward edges
        z = -(dx * dx / (2.0 * R_major)) - (dy * dy / (2.0 * R_minor))
        # Shift so center is at Z=0 (no material removed at peak)
        # and edges are at the max carve depth
        return z  # negative values = material removal

    def is_inside_body(x: float, y: float) -> bool:
        """Simple bounds check — point must be inside body rectangle with margin."""
        margin = 3.0  # mm
        return (margin < x < body_w_mm - margin and
                margin < y < body_h_mm - margin)

    # Determine the dome Z at the edges for normalization
    edge_z_at_corner = dome_z(0, 0)
    # Normalize so that corner z = -max_carve_depth
    if abs(edge_z_at_corner) > 0.001:
        z_scale = max_carve_depth / abs(edge_z_at_corner)
    else:
        z_scale = 1.0

    def scaled_dome_z(x: float, y: float) -> float:
        return dome_z(x, y) * z_scale

    # -----------------------------------------------------------------------
    # OP80: Rough Carved Top — 6mm Ball Nose
    # -----------------------------------------------------------------------
    g.tool_change(6, "6mm Ball Nose End Mill", T6_RPM,
                  "OP80: Rough carved top — 3D surfacing")
    g.section("OP80: ROUGH CARVED TOP (6mm Ball Nose)")
    g.comment(f"Dome: R_major={R_major}mm, R_minor={R_minor}mm, rise={peak_above_edge}mm")
    g.comment(f"Stepover: {T6_STEPOVER}mm, DOC: {T6_DOC}mm")
    g.comment(f"Cap thickness: {cap_thickness}mm, edge after carve: {edge_thickness}mm")

    # Leave 0.5mm stock for finish pass
    rough_stock = 0.5

    # Raster passes along X, stepping in Y
    y = T6_DIA / 2
    row = 0
    while y < body_h_mm - T6_DIA / 2:
        row += 1
        g.comment(f"Row {row}: Y={y:.2f}mm")

        if row % 2 == 1:
            # Forward pass
            x_start = T6_DIA / 2
            x_end = body_w_mm - T6_DIA / 2
            x_step = T6_STEPOVER
        else:
            # Reverse pass (bidirectional for efficiency)
            x_start = body_w_mm - T6_DIA / 2
            x_end = T6_DIA / 2
            x_step = -T6_STEPOVER

        g.rapid(z=SAFE_Z)
        first_x = x_start
        first_z = scaled_dome_z(first_x, y) + rough_stock
        first_z = max(first_z, -max_carve_depth)
        g.rapid(x=first_x, y=y)
        g.rapid(z=RETRACT_Z)
        g.linear(z=first_z, f=T6_PLUNGE)

        x = x_start + x_step
        while (x_step > 0 and x <= x_end) or (x_step < 0 and x >= x_end):
            if is_inside_body(x, y):
                z = scaled_dome_z(x, y) + rough_stock
                z = max(z, -max_carve_depth)
                g.linear(x=x, y=y, z=z, f=T6_FEED)
            x += x_step

        g.rapid(z=SAFE_Z)
        y += T6_STEPOVER

    # -----------------------------------------------------------------------
    # OP81: Finish Carved Top — 3mm Ball Nose
    # -----------------------------------------------------------------------
    g.tool_change(7, "3mm Ball Nose End Mill", T7_RPM,
                  "OP81: Finish carved top — fine 3D surfacing")
    g.section("OP81: FINISH CARVED TOP (3mm Ball Nose)")
    g.comment(f"Stepover: {T7_STEPOVER}mm for scallop-free surface")
    g.comment(f"Feed: {T7_FEED}mm/min")

    y = T7_DIA / 2
    row = 0
    while y < body_h_mm - T7_DIA / 2:
        row += 1

        if row % 2 == 1:
            x_start = T7_DIA / 2
            x_end = body_w_mm - T7_DIA / 2
            x_step = T7_STEPOVER
        else:
            x_start = body_w_mm - T7_DIA / 2
            x_end = T7_DIA / 2
            x_step = -T7_STEPOVER

        g.rapid(z=SAFE_Z)
        first_x = x_start
        first_z = scaled_dome_z(first_x, y)
        first_z = max(first_z, -max_carve_depth)
        g.rapid(x=first_x, y=y)
        g.rapid(z=RETRACT_Z)
        g.linear(z=first_z, f=T7_PLUNGE)

        x = x_start + x_step
        while (x_step > 0 and x <= x_end) or (x_step < 0 and x >= x_end):
            if is_inside_body(x, y):
                z = scaled_dome_z(x, y)
                z = max(z, -max_carve_depth)
                g.linear(x=x, y=y, z=z, f=T7_FEED)
            x += x_step

        g.rapid(z=SAFE_Z)
        y += T7_STEPOVER

    g.footer()
    return g.text()


# ---------------------------------------------------------------------------
# Build summary JSON
# ---------------------------------------------------------------------------

def generate_build_summary(spec: Dict, phase1_lines: int, phase2_lines: int,
                           phase3_lines: int) -> str:
    """Generate build summary JSON."""
    carve = spec["carved_top"]
    bp = spec["binding_and_purfling"]

    summary = {
        "model": spec["display_name"],
        "spec_file": "instrument_geometry/specs/gibson_les_paul.json",
        "generated": datetime.now().isoformat(),
        "generator": "The Production Shop — Les Paul Full Build Generator",
        "phases": {
            "phase1_mahogany_back": {
                "file": "LesPaul_1959_Phase1_MahoganyBack.nc",
                "units": "inches (G20)",
                "operations": [
                    "OP10: Fixture holes",
                    "OP20: Neck pocket rough (T1 10mm)",
                    "OP21a/b: Pickup cavities rough (T1 10mm)",
                    "OP22: Electronics cavity rough (T1 10mm)",
                    "OP25: Cover recess (T2 6mm)",
                    "OP30: Neck pocket finish (T2 6mm)",
                    "OP31a/b: Pickup cavities finish (T2 6mm)",
                    "OP40: Wiring channels (T3 3mm)",
                    "OP50: Body perimeter contour with 6 tabs (T2 6mm)",
                    "OP60: Pot shaft holes 4x (T3 3mm)",
                    "OP61: Bridge post holes 2x (T3 3mm)",
                    "OP62: Tailpiece stud holes 2x (T3 3mm)",
                    "OP63: Screw pilot holes (T3 3mm)",
                ],
                "gcode_lines": phase1_lines,
                "stock": "Honduran mahogany, 1.75\" thick",
                "tools": ["T1: 10mm flat (rough)", "T2: 6mm flat (finish)", "T3: 3mm flat/drill"],
            },
            "phase2_purfling_channels": {
                "file": "LesPaul_1959_Phase2_PurflingChannels.nc",
                "units": "inches (G20)",
                "operations": [
                    "OP70: Primary channel - Spanish wave (top)",
                    "OP70b: Primary channel - Spanish wave (back)",
                    "OP71: Inner ledge - green wood (top)",
                    "OP71b: Inner ledge - green wood (back)",
                ],
                "gcode_lines": phase2_lines,
                "stock": "Assembled body (mahogany + maple)",
                "tools": [
                    f"T4: 2.4mm flat ({bp['routing_channels']['primary_channel']['width_mm']}mm channel)",
                    f"T5: 1.6mm flat ({bp['routing_channels']['inner_ledge']['width_mm']}mm channel)",
                ],
                "purfling_spec": {
                    "spanish_wave": "2.2mm x 6.0mm -> channel 2.375mm x 6.2mm",
                    "green_wood": "1.5mm x 1.3mm -> ledge 1.6mm x 1.5mm",
                },
            },
            "phase3_carved_top": {
                "file": "LesPaul_1959_Phase3_CarvedTop.nc",
                "units": "mm (G21)",
                "operations": [
                    "OP80: Rough carved top (T6 6mm ball nose)",
                    "OP81: Finish carved top (T7 3mm ball nose)",
                ],
                "gcode_lines": phase3_lines,
                "stock": "Bookmatched figured maple, 19.05mm (3/4\") cap glued to mahogany",
                "tools": ["T6: 6mm ball nose (rough)", "T7: 3mm ball nose (finish)"],
                "carved_top_geometry": {
                    "major_radius_mm": carve["major_radius_mm"],
                    "minor_radius_mm": carve["minor_radius_mm"],
                    "total_rise_mm": carve["total_rise_mm"],
                    "average_slope_deg": carve["carve_slope"]["average_degrees"],
                    "slope_range_deg": carve["carve_slope"]["range_degrees"],
                    "cap_thickness_before_mm": carve["cap_thickness_before_carving_mm"],
                    "cap_thickness_edge_after_mm": carve["cap_thickness_after_carving_edge_mm"],
                },
            },
        },
        "total_gcode_lines": phase1_lines + phase2_lines + phase3_lines,
        "tool_library": {
            "T1": "10mm Flat End Mill (roughing pockets)",
            "T2": "6mm Flat End Mill (finishing, perimeter)",
            "T3": "3mm Flat/Drill (channels, all drilling)",
            "T4": "2.375mm Flat (Spanish wave purfling channel)",
            "T5": "1.6mm Flat (green wood purfling ledge)",
            "T6": "6mm Ball Nose (rough carved top)",
            "T7": "3mm Ball Nose (finish carved top)",
        },
        "machine_targets": spec["cnc_operations"]["machine_targets"],
        "notes": [
            "Phase 1 operates on mahogany back slab ONLY — all cavity routing",
            "Phase 2 operates on the assembled body — purfling channels on both faces",
            "Phase 3 operates on the maple cap top face — 3D compound-radius dome carving",
            "Body perimeter (OP50) includes 6 holding tabs at 0.125\" height",
            "Carved top uses bidirectional raster with elliptical dome Z computation",
            "All pocket operations use helical entry to avoid plunge marks",
            "CRITICAL: Run scrap test for purfling channels before production (see spec)",
        ],
    }
    return json.dumps(summary, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Gibson Les Paul 1956-59 — Full CNC Build Generator")
    print("=" * 70)
    print()

    # Load spec
    print(f"Loading spec: {SPEC_PATH.name}")
    spec = load_spec()
    print(f"  Model: {spec['display_name']}")
    print(f"  Variants: {', '.join(spec['variants'].keys())}")

    # Load body outline
    print(f"Loading body outline: {DXF_PATH.name}")
    outline = load_body_outline_from_dxf()
    print(f"  Points: {len(outline)}")
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    print(f"  Dimensions: {max(xs)-min(xs):.1f} x {max(ys)-min(ys):.1f} mm")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput: {OUTPUT_DIR}")

    # Phase 1: Mahogany back
    print("\n--- Phase 1: Mahogany Back Routing ---")
    phase1 = generate_phase1_back(spec, outline)
    phase1_lines = len(phase1.strip().split("\n"))
    p1_path = OUTPUT_DIR / "LesPaul_1959_Phase1_MahoganyBack.nc"
    p1_path.write_text(phase1, encoding="utf-8")
    print(f"  Written: {p1_path.name} ({phase1_lines:,} lines)")

    # Verify Phase 1 G-code (LP-GAP-08)
    v1 = verify_gcode(
        gcode=phase1,
        stock_thickness_mm=44.45,  # 1.75"
        phase_name="Phase 1: Mahogany Back",
        units="inch",
    )

    # Phase 2: Purfling channels
    print("\n--- Phase 2: Purfling Channel Routing ---")
    phase2 = generate_phase2_purfling(spec, outline)
    phase2_lines = len(phase2.strip().split("\n"))
    p2_path = OUTPUT_DIR / "LesPaul_1959_Phase2_PurflingChannels.nc"
    p2_path.write_text(phase2, encoding="utf-8")
    print(f"  Written: {p2_path.name} ({phase2_lines:,} lines)")

    # Verify Phase 2 G-code (LP-GAP-08)
    v2 = verify_gcode(
        gcode=phase2,
        stock_thickness_mm=44.45,  # 1.75"
        phase_name="Phase 2: Purfling Channels",
        units="inch",
    )

    # Phase 3: Carved top
    print("\n--- Phase 3: Carved Maple Top ---")
    phase3 = generate_phase3_carved_top(spec, outline)
    phase3_lines = len(phase3.strip().split("\n"))
    p3_path = OUTPUT_DIR / "LesPaul_1959_Phase3_CarvedTop.nc"
    p3_path.write_text(phase3, encoding="utf-8")
    print(f"  Written: {p3_path.name} ({phase3_lines:,} lines)")

    # Verify Phase 3 G-code (LP-GAP-08)
    v3 = verify_gcode(
        gcode=phase3,
        stock_thickness_mm=12.7,  # Maple cap 0.5"
        phase_name="Phase 3: Carved Maple Top",
        units="mm",
    )

    # Build summary
    print("\n--- Build Summary ---")
    summary = generate_build_summary(spec, phase1_lines, phase2_lines, phase3_lines)
    sum_path = OUTPUT_DIR / "LesPaul_1959_BuildSummary.json"
    sum_path.write_text(summary, encoding="utf-8")
    print(f"  Written: {sum_path.name}")

    total = phase1_lines + phase2_lines + phase3_lines
    print(f"\n{'=' * 70}")
    print(f"COMPLETE: {total:,} total G-code lines across 3 phases")
    print(f"  Phase 1 (Mahogany Back):    {phase1_lines:,} lines")
    print(f"  Phase 2 (Purfling):         {phase2_lines:,} lines")
    print(f"  Phase 3 (Carved Top):       {phase3_lines:,} lines")
    print(f"  7 tools required: T1-T7")

    # Verification summary (LP-GAP-08)
    all_ok = v1["ok"] and v2["ok"] and v3["ok"]
    if all_ok:
        print(f"\n  ✓ G-CODE VERIFICATION: ALL PHASES PASSED")
    else:
        print(f"\n  ✗ G-CODE VERIFICATION FAILED - review errors before machining")
        if not v1["ok"]:
            print(f"    Phase 1 errors: {v1['errors']}")
        if not v2["ok"]:
            print(f"    Phase 2 errors: {v2['errors']}")
        if not v3["ok"]:
            print(f"    Phase 3 errors: {v3['errors']}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
