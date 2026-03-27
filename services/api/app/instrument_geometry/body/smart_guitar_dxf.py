# services/api/app/instrument_geometry/body/smart_guitar_dxf.py

"""
Smart Guitar DXF Layer Generator
=================================

Generates CAM-ready DXF files from Smart Guitar v1 cavity specifications.
Each cavity type maps to a named layer with depth annotation for CAM.

Layers:
    NECK_POCKET         - 15.9mm depth, 6.35mm corner rad
    PICKUP_NECK         - 19mm depth, humbucker route
    PICKUP_BRIDGE       - 19mm depth, humbucker route
    REAR_ELECTRONICS    - 22mm depth, Pi 5 + battery chamber
    ARDUINO_POCKET      - 20mm depth, preamp module
    ANTENNA_RECESS      - 2mm shelf step (milled from rear cavity floor)
    WIRING_CHANNEL      - 15mm depth, rear-routed
    BRIDGE_MOUNTING     - surface mount, 4x M3.5 holes
    CONTROL_PLATE       - surface mount, 3x pot holes
    USB_PORT            - 7mm edge slot (requires 3+1 or 4th axis)
    OUTPUT_JACK         - 25mm angled bore

Usage:
    from app.instrument_geometry.body.smart_guitar_dxf import generate_smart_guitar_dxf

    dxf_path = generate_smart_guitar_dxf(
        output_path="smart_guitar_cavities.dxf",
        include_body_outline=True,
    )
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import ezdxf
    from ezdxf import units
    from ezdxf.math import Vec2
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

# Traced outline coordinates (60 body points, 3 voids)
TRACED_OUTLINE_AVAILABLE = False
try:
    from app.instrument_geometry.body.traced_outlines.smart_guitar_traced_outline import (
        body_pts as TRACED_BODY_PTS,
        void_upper_bass_pts,
        void_upper_treble_pts,
        void_lower_bass_pts,
        ALL_VOIDS,
    )
    TRACED_OUTLINE_AVAILABLE = True
except ImportError:
    TRACED_BODY_PTS = None
    void_upper_bass_pts = []
    void_upper_treble_pts = []
    void_lower_bass_pts = []
    ALL_VOIDS = []

# Body outline origin correction
# The traced outline has body top at Y=114.87mm (not Y=0).
# All y_from_top cavity positions must be offset by this value.
# Derived from: max(body_pts_y) after 1.510312x scale correction.
BODY_TOP_Y = 114.87  # mm — traced outline body top in world coordinates


# ─── Layer Definitions ───────────────────────────────────────────────────────

@dataclass
class LayerSpec:
    """DXF layer specification with CAM metadata."""
    name: str
    color: int  # AutoCAD color index (1-255)
    depth_mm: float
    description: str
    linetype: str = "CONTINUOUS"


CAVITY_LAYERS: Dict[str, LayerSpec] = {
    "NECK_POCKET": LayerSpec(
        name="NECK_POCKET",
        color=1,  # Red
        depth_mm=15.9,
        description="Neck pocket mortise - 76.2x55.9mm, 6.35mm corner rad",
    ),
    "PICKUP_NECK": LayerSpec(
        name="PICKUP_NECK",
        color=3,  # Green
        depth_mm=19.0,
        description="Neck humbucker route - 92x40mm",
    ),
    "PICKUP_BRIDGE": LayerSpec(
        name="PICKUP_BRIDGE",
        color=3,  # Green
        depth_mm=19.0,
        description="Bridge humbucker route - 92x40mm",
    ),
    "REAR_ELECTRONICS": LayerSpec(
        name="REAR_ELECTRONICS",
        color=5,  # Blue
        depth_mm=22.0,
        description="Pi 5 + battery cavity - 95x65mm, rear access",
    ),
    "ARDUINO_POCKET": LayerSpec(
        name="ARDUINO_POCKET",
        color=4,  # Cyan
        depth_mm=20.0,
        description="Arduino preamp pocket - 80x60mm",
    ),
    "ANTENNA_RECESS": LayerSpec(
        name="ANTENNA_RECESS",
        color=6,  # Magenta
        depth_mm=2.0,
        description="RF antenna shelf - 50x30mm, milled from rear cavity floor",
    ),
    "WIRING_CHANNEL": LayerSpec(
        name="WIRING_CHANNEL",
        color=8,  # Gray
        depth_mm=15.0,
        description="Rear wiring channels - 10mm wide",
    ),
    "BRIDGE_MOUNTING": LayerSpec(
        name="BRIDGE_MOUNTING",
        color=2,  # Yellow
        depth_mm=0.0,  # Surface mount
        description="Headless bridge mount - 4x M3.5 holes",
    ),
    "CONTROL_PLATE": LayerSpec(
        name="CONTROL_PLATE",
        color=2,  # Yellow
        depth_mm=0.0,  # Surface mount
        description="Control plate - 3x 9.5mm pot holes",
    ),
    "USB_PORT": LayerSpec(
        name="USB_PORT",
        color=30,  # Orange
        depth_mm=7.0,
        description="USB-C edge slot - 12x6.5mm, requires edge access",
    ),
    "OUTPUT_JACK": LayerSpec(
        name="OUTPUT_JACK",
        color=30,  # Orange
        depth_mm=25.0,
        description="1/4\" barrel jack bore - 12.7mm dia, 15° angle",
    ),
    "BODY_OUTLINE": LayerSpec(
        name="BODY_OUTLINE",
        color=7,  # White
        depth_mm=0.0,
        description="Body perimeter reference",
    ),
    "CENTERLINE": LayerSpec(
        name="CENTERLINE",
        color=9,  # Light gray
        depth_mm=0.0,
        description="Body centerline reference",
        linetype="CONTINUOUS",  # Changed from CENTER - undefined linetypes cause viewer hangs
    ),
    # Void cutaway layers
    "VOID_UPPER_BASS": LayerSpec(
        name="VOID_UPPER_BASS",
        color=40,  # Light cyan
        depth_mm=0.0,
        description="Upper bass cutaway void (11 points)",
    ),
    "VOID_UPPER_TREBLE": LayerSpec(
        name="VOID_UPPER_TREBLE",
        color=50,  # Light yellow
        depth_mm=0.0,
        description="Upper treble cutaway void (12 points)",
    ),
    "VOID_LOWER_BASS": LayerSpec(
        name="VOID_LOWER_BASS",
        color=60,  # Light magenta
        depth_mm=0.0,
        description="Lower bass cutaway void (21 points)",
    ),
}


# ─── Geometry Helpers ────────────────────────────────────────────────────────

def rounded_rect_points(
    cx: float,
    cy: float,
    length: float,
    width: float,
    corner_radius: float,
    segments_per_corner: int = 8,
) -> List[Tuple[float, float]]:
    """
    Generate points for a rounded rectangle (closed LWPOLYLINE).

    Args:
        cx, cy: Center position
        length: Total length (X dimension)
        width: Total width (Y dimension)
        corner_radius: Fillet radius for corners
        segments_per_corner: Arc segments per 90° corner

    Returns:
        List of (x, y) tuples forming closed polyline
    """
    r = min(corner_radius, length / 2, width / 2)
    half_l = length / 2
    half_w = width / 2

    points = []

    # Start at bottom-left, go clockwise
    corners = [
        (cx - half_l + r, cy - half_w + r, 180, 270),  # Bottom-left
        (cx + half_l - r, cy - half_w + r, 270, 360),  # Bottom-right
        (cx + half_l - r, cy + half_w - r, 0, 90),     # Top-right
        (cx - half_l + r, cy + half_w - r, 90, 180),   # Top-left
    ]

    for corner_cx, corner_cy, start_deg, end_deg in corners:
        for i in range(segments_per_corner + 1):
            angle = math.radians(start_deg + (end_deg - start_deg) * i / segments_per_corner)
            x = corner_cx + r * math.cos(angle)
            y = corner_cy + r * math.sin(angle)
            points.append((x, y))

    # Close the shape
    if points:
        points.append(points[0])

    return points


def circle_points(
    cx: float,
    cy: float,
    radius: float,
    segments: int = 32,
) -> List[Tuple[float, float]]:
    """Generate points for a circle."""
    points = []
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    return points


# ─── Main Generator ──────────────────────────────────────────────────────────

def generate_smart_guitar_dxf(
    output_path: str | Path,
    spec_path: Optional[str | Path] = None,
    include_body_outline: bool = True,
    include_centerline: bool = True,
    include_wiring_channels: bool = True,
    include_voids: bool = True,
    use_traced_outline: bool = True,
    body_width_mm: float = 330.0,
    body_height_mm: float = 445.0,
) -> Path:
    """
    Generate DXF file with Smart Guitar cavity layers.

    Args:
        output_path: Output DXF file path
        spec_path: Path to smart_guitar_v1.json (auto-detected if None)
        include_body_outline: Add body perimeter reference layer
        include_centerline: Add vertical centerline reference
        include_wiring_channels: Include rear wiring channel paths
        body_width_mm: Body width for outline (if no spec)
        body_height_mm: Body height for outline (if no spec)

    Returns:
        Path to generated DXF file
    """
    if not EZDXF_AVAILABLE:
        raise ImportError("ezdxf required: pip install ezdxf")

    output_path = Path(output_path)

    # Load spec
    if spec_path is None:
        spec_path = Path(__file__).parent / "specs" / "smart_guitar_v1.json"

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    cavities = spec.get("cavities", {})

    # Create DXF document
    doc = ezdxf.new("R2000")
    doc.units = units.MM
    msp = doc.modelspace()

    # Create layers
    for layer_spec in CAVITY_LAYERS.values():
        doc.layers.add(
            name=layer_spec.name,
            color=layer_spec.color,
            linetype=layer_spec.linetype,
        )

    # ─── Body Outline ────────────────────────────────────────────────────────
    if include_body_outline:
        if use_traced_outline and TRACED_OUTLINE_AVAILABLE and TRACED_BODY_PTS:
            # Use 60-point traced outline from smart_guitar_outline_editor_v6
            msp.add_lwpolyline(
                TRACED_BODY_PTS,
                dxfattribs={"layer": "BODY_OUTLINE"},
                close=True,
            )
        else:
            # Fallback: simplified parametric body outline
            body_points = rounded_rect_points(
                cx=0, cy=-body_height_mm / 2,
                length=body_width_mm,
                width=body_height_mm,
                corner_radius=50.0,
                segments_per_corner=16,
            )
            msp.add_lwpolyline(
                body_points,
                dxfattribs={"layer": "BODY_OUTLINE"},
                close=True,
            )

    # ─── Void Cutaways ───────────────────────────────────────────────────────
    if include_voids and TRACED_OUTLINE_AVAILABLE:
        # Upper bass void (11 points)
        if void_upper_bass_pts:
            msp.add_lwpolyline(
                void_upper_bass_pts,
                dxfattribs={"layer": "VOID_UPPER_BASS"},
                close=True,
            )

        # Upper treble void (12 points)
        if void_upper_treble_pts:
            msp.add_lwpolyline(
                void_upper_treble_pts,
                dxfattribs={"layer": "VOID_UPPER_TREBLE"},
                close=True,
            )

        # Lower bass void (21 points)
        if void_lower_bass_pts:
            msp.add_lwpolyline(
                void_lower_bass_pts,
                dxfattribs={"layer": "VOID_LOWER_BASS"},
                close=True,
            )

    # ─── Centerline ──────────────────────────────────────────────────────────
    if include_centerline:
        msp.add_line(
            (0, BODY_TOP_Y), (0, BODY_TOP_Y - body_height_mm),
            dxfattribs={"layer": "CENTERLINE"},
        )

    # ─── Neck Pocket ─────────────────────────────────────────────────────────
    np = cavities.get("neck_pocket", {})
    np_dims = np.get("dimensions_mm", {})
    np_pos = np.get("body_position_mm", {})

    if np_dims:
        y_from_top = np_pos.get("y_from_top", 53.3)
        points = rounded_rect_points(
            cx=0,
            cy=BODY_TOP_Y - y_from_top - np_dims.get("length", 76.2) / 2,
            length=np_dims.get("length", 76.2),
            width=np_dims.get("width", 55.9),
            corner_radius=np_dims.get("corner_radius", 6.35),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "NECK_POCKET"}, close=True)

    # ─── Neck Pickup ─────────────────────────────────────────────────────────
    nu = cavities.get("neck_pickup_route", {})
    nu_dims = nu.get("dimensions_mm", {})
    nu_pos = nu.get("body_position_mm", {})

    if nu_dims:
        y_from_top = nu_pos.get("y_from_top", 167.6)
        points = rounded_rect_points(
            cx=0,
            cy=BODY_TOP_Y - y_from_top,
            length=nu_dims.get("length", 92.0),
            width=nu_dims.get("width", 40.0),
            corner_radius=nu_dims.get("corner_radius", 3.175),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "PICKUP_NECK"}, close=True)

    # ─── Bridge Pickup ───────────────────────────────────────────────────────
    bu = cavities.get("bridge_pickup_route", {})
    bu_dims = bu.get("dimensions_mm", {})
    bu_pos = bu.get("body_position_mm", {})

    if bu_dims:
        y_from_top = bu_pos.get("y_from_top", 294.6)
        points = rounded_rect_points(
            cx=0,
            cy=BODY_TOP_Y - y_from_top,
            length=bu_dims.get("length", 92.0),
            width=bu_dims.get("width", 40.0),
            corner_radius=bu_dims.get("corner_radius", 3.175),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "PICKUP_BRIDGE"}, close=True)

    # ─── Rear Electronics Cavity ─────────────────────────────────────────────
    re = cavities.get("rear_electronics_cavity", {})
    re_dims = re.get("dimensions_mm", {})
    re_pos = re.get("body_position_mm", {})

    if re_dims:
        x_center = re_pos.get("x_center", 36.8)
        y_from_top = re_pos.get("y_from_top", 275.7)
        points = rounded_rect_points(
            cx=x_center,
            cy=BODY_TOP_Y - y_from_top,
            length=re_dims.get("length", 95.0),
            width=re_dims.get("width", 65.0),
            corner_radius=re_dims.get("corner_radius", 6.0),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "REAR_ELECTRONICS"}, close=True)

        # Cover plate screw holes
        screws = re.get("cover_plate_screws", {})
        screw_positions = screws.get("positions_from_center_mm", [])
        pilot_dia = screws.get("pilot_hole_mm", 2.8)
        for pos in screw_positions:
            screw_x = x_center + pos.get("x", 0)
            screw_y = BODY_TOP_Y - y_from_top + pos.get("y", 0)
            msp.add_circle(
                (screw_x, screw_y),
                radius=pilot_dia / 2,
                dxfattribs={"layer": "REAR_ELECTRONICS"},
            )

    # ─── Arduino Preamp Pocket ───────────────────────────────────────────────
    ap = cavities.get("arduino_preamp_pocket", {})
    ap_dims = ap.get("dimensions_mm", {})
    ap_pos = ap.get("body_position_mm", {})

    if ap_dims:
        x_center = ap_pos.get("x_center", 36.8)
        y_from_top = ap_pos.get("y_from_top", 133.5)
        points = rounded_rect_points(
            cx=x_center,
            cy=BODY_TOP_Y - y_from_top,
            length=ap_dims.get("length", 80.0),
            width=ap_dims.get("width", 60.0),
            corner_radius=ap_dims.get("corner_radius", 4.0),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "ARDUINO_POCKET"}, close=True)

    # ─── Antenna Recess ──────────────────────────────────────────────────────
    ar = cavities.get("antenna_recess", {})
    ar_dims = ar.get("dimensions_mm", {})
    ar_pos = ar.get("body_position_mm", {})

    if ar_dims:
        x_center = ar_pos.get("x_center", 22.2)
        y_from_top = ar_pos.get("y_from_top", 202.6)
        points = rounded_rect_points(
            cx=x_center,
            cy=BODY_TOP_Y - y_from_top,
            length=ar_dims.get("length", 50.0),
            width=ar_dims.get("width", 30.0),
            corner_radius=ar_dims.get("corner_radius", 3.0),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "ANTENNA_RECESS"}, close=True)

    # ─── Bridge Mounting ─────────────────────────────────────────────────────
    br = cavities.get("bridge_route", {})
    br_dims = br.get("dimensions_mm", {})
    br_pos = br.get("body_position_mm", {})

    if br_dims:
        y_from_top = br_pos.get("y_from_top", 320.0)
        hole_spacing_l = br_dims.get("mounting_hole_spacing_length", 80.0)
        hole_spacing_w = br_dims.get("mounting_hole_spacing_width", 35.0)
        hole_dia = br_dims.get("mounting_hole_diameter", 3.5)

        # 4 mounting holes in rectangle pattern
        for dx in [-hole_spacing_l/2, hole_spacing_l/2]:
            for dy in [-hole_spacing_w/2, hole_spacing_w/2]:
                msp.add_circle(
                    (dx, BODY_TOP_Y - y_from_top + dy),
                    radius=hole_dia / 2,
                    dxfattribs={"layer": "BRIDGE_MOUNTING"},
                )

        # Bridge outline (reference only)
        points = rounded_rect_points(
            cx=0,
            cy=BODY_TOP_Y - y_from_top,
            length=br_dims.get("bridge_length", 95.0),
            width=br_dims.get("bridge_width", 42.0),
            corner_radius=br_dims.get("corner_radius", 3.175),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "BRIDGE_MOUNTING"}, close=True)

    # ─── Control Plate ───────────────────────────────────────────────────────
    cp = cavities.get("control_plate_surface", {})
    cp_dims = cp.get("dimensions_mm", {})
    cp_pos = cp.get("body_position_mm", {})

    if cp_dims and cp_pos:
        x_center = cp_pos.get("x_center", 55.2)
        y_from_top = cp_pos.get("y_from_top", 346.7)

        # Plate outline
        points = rounded_rect_points(
            cx=x_center,
            cy=BODY_TOP_Y - y_from_top,
            length=cp_dims.get("length", 100.0),
            width=cp_dims.get("width", 50.0),
            corner_radius=cp_dims.get("corner_radius", 6.35),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "CONTROL_PLATE"}, close=True)

        # Pot holes
        components = cp.get("components", {})
        pot_dia = cp.get("pot_holes_mm", {}).get("diameter", 9.5)

        for comp_name, comp in components.items():
            hole_x = x_center + comp.get("x_offset_mm", 0)
            hole_y = BODY_TOP_Y - y_from_top + comp.get("y_offset_mm", 0)
            msp.add_circle(
                (hole_x, hole_y),
                radius=pot_dia / 2,
                dxfattribs={"layer": "CONTROL_PLATE"},
            )

    # ─── USB-C Port ──────────────────────────────────────────────────────────
    usb = cavities.get("usb_c_port", {})
    usb_dims = usb.get("dimensions_mm", {})
    usb_pos = usb.get("body_position_mm", {})

    if usb_dims:
        # Edge slot - positioned at body edge
        x_center = usb_pos.get("x_center", 216.0)  # Near body edge
        y_from_top = usb_pos.get("y_from_top", 239.4)

        points = rounded_rect_points(
            cx=x_center,
            cy=BODY_TOP_Y - y_from_top,
            length=usb_dims.get("slot_depth", 7.0),  # Into body
            width=usb_dims.get("slot_width", 12.0),
            corner_radius=usb_dims.get("corner_radius", 1.5),
        )
        msp.add_lwpolyline(points, dxfattribs={"layer": "USB_PORT"}, close=True)

    # ─── Output Jack ─────────────────────────────────────────────────────────
    oj = cavities.get("output_jack", {})
    oj_dims = oj.get("dimensions_mm", {})
    oj_pos = oj.get("body_position_mm", {})

    if oj_dims:
        x_center = oj_pos.get("x_center", 110.4)
        y_from_top = oj_pos.get("y_from_top", 391.2)
        bore_dia = oj_dims.get("bore_diameter", 12.7)

        msp.add_circle(
            (x_center, BODY_TOP_Y - y_from_top),
            radius=bore_dia / 2,
            dxfattribs={"layer": "OUTPUT_JACK"},
        )

    # ─── Wiring Channels ─────────────────────────────────────────────────────
    if include_wiring_channels:
        wc = cavities.get("rear_wiring_channel", {})
        paths = wc.get("paths", [])
        channel_width = wc.get("dimensions_mm", {}).get("width", 10.0)

        for path in paths:
            start = path.get("start_mm", {})
            end = path.get("end_mm", {})

            if start and end:
                # Draw channel centerline
                msp.add_line(
                    (start.get("x", 0), BODY_TOP_Y - start.get("y", 0)),
                    (end.get("x", 0), BODY_TOP_Y - end.get("y", 0)),
                    dxfattribs={"layer": "WIRING_CHANNEL"},
                )

    # Save DXF
    doc.saveas(output_path)

    return output_path


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    output = sys.argv[1] if len(sys.argv) > 1 else "smart_guitar_cavities.dxf"
    path = generate_smart_guitar_dxf(output)
    print(f"Generated: {path}")

    # Print layer summary
    print("\nLayers:")
    for name, spec in CAVITY_LAYERS.items():
        print(f"  {name:20s} depth={spec.depth_mm:5.1f}mm  color={spec.color:2d}  {spec.description}")
