#!/usr/bin/env python3
"""
Generate Smart Guitar CAM-ready DXF with corrected geometry.

Fixes:
1. Centers body on X=0 (fixes -21.94mm offset from preliminary DXF)
2. Uses 60-point traced outline (instead of 21-point preliminary)
3. Includes 3 Klein-style voids (upper_bass, upper_treble, lower_bass)
4. Multi-layer CAM structure (like LesPaul_CAM_Closed.dxf)

Layers:
- BODY_OUTLINE: Main 60-point body perimeter
- VOIDS: 3 Klein-style ergonomic voids (front-routed)
- NECK_POCKET: 76.2 x 55.9 mm bolt-on pocket
- PICKUP_CAVITIES: Neck and bridge humbucker routes (92 x 40 mm)
- BRIDGE_ROUTE: Headless bridge mounting (95 x 42 mm)
- ELECTRONICS_CAVITY: Rear Pi 5 cavity (95 x 65 mm) [reference only]
- TEENSY_IO_POCKET: Rear Teensy I/O coprocessor cavity (70 x 25 mm) [reference only]
- CENTERLINE: Vertical centerline for alignment

Origin: Body center (0, 0), Y+ toward neck, Y- toward tail.

Author: Claude Code
Date: 2026-03-25
"""

import sys
from pathlib import Path

# Add app to path for imports
APP_ROOT = Path(__file__).parent.parent / "services" / "api"
sys.path.insert(0, str(APP_ROOT))

try:
    import ezdxf
except ImportError:
    print("ERROR: ezdxf not installed. Run: pip install ezdxf")
    sys.exit(1)


# ============================================================================
# BODY OUTLINE - 60 points from traced_outline.py
# Origin: body center (0, 0), Y+ toward neck
# ============================================================================
BODY_PTS = [
    (40.80, 35.35), (48.63, 40.05), (58.02, 43.70), (67.42, 47.36),
    (76.81, 45.79), (74.20, 33.79), (72.11, 22.31), (70.03, 9.79),
    (65.33, -0.65), (62.20, -12.13), (63.24, -22.57), (73.68, -36.66),
    (84.64, -54.40), (103.42, -79.44), (109.16, -100.32), (114.90, -118.58),
    (112.81, -127.45), (99.25, -135.28), (83.07, -143.11), (76.81, -149.89),
    (55.94, -161.37), (41.85, -169.20), (27.24, -174.94), (7.93, -185.89),
    (0.63, -193.72), (-13.99, -183.81), (-18.68, -180.15), (-40.08, -186.42),
    (-56.77, -192.68), (-82.86, -199.98), (-104.78, -210.42), (-116.26, -213.03),
    (-130.35, -218.25), (-132.96, -204.68), (-126.70, -175.98), (-123.04, -153.54),
    (-120.96, -140.50), (-113.13, -120.67), (-106.87, -99.79), (-102.17, -87.27),
    (-94.87, -76.84), (-86.52, -61.18), (-77.65, -49.70), (-75.04, -38.22),
    (-70.34, -30.92), (-67.73, -19.96), (-73.47, -3.26), (-69.82, -12.65),
    (-75.04, 7.18), (-79.21, 32.22), (-77.12, 47.88), (-74.51, 55.71),
    (-61.99, 65.10), (-49.99, 71.88), (-43.21, 73.45), (-32.25, 75.53),
    (-22.33, 76.06), (18.89, 34.31), (27.76, 34.31), (35.06, 32.22),
]

# ============================================================================
# VOIDS - Klein-style ergonomic negative spaces
# ============================================================================
VOID_UPPER_BASS = [
    (-33.00, 44.00), (-48.42, 54.14), (-58.86, 43.70), (-61.99, 30.14),
    (-60.95, 15.00), (-55.00, 0.00), (-44.00, -22.00), (-33.00, -22.00),
    (-33.00, -11.00), (-33.00, 11.00), (-33.00, 33.00),
]

VOID_UPPER_TREBLE = [
    (44.00, 22.00), (55.00, 22.00), (55.00, 0.00), (55.00, -22.00),
    (49.50, -22.00), (44.00, -22.00), (38.50, -16.50), (33.00, -11.00),
    (33.00, 0.00), (33.00, 11.00), (38.50, 22.00), (44.00, 22.00),
]

VOID_LOWER_BASS = [
    (-64.08, -48.14), (-62.51, -48.66), (-70.86, -66.40), (-78.69, -82.58),
    (-89.13, -100.32), (-98.52, -120.67), (-100.61, -132.15), (-102.69, -144.15),
    (-102.17, -154.59), (-90.69, -149.37), (-79.21, -148.32), (-65.12, -142.58),
    (-49.47, -134.76), (-40.08, -127.97), (-36.94, -99.27), (-40.08, -75.79),
    (-40.08, -58.57), (-39.03, -50.74), (-37.99, -45.53), (-40.08, -39.79),
    (-51.56, -35.09),
]

# ============================================================================
# CAVITY DEFINITIONS (from smart_guitar_v1.json)
# All positions in mm, origin at body center (0, 0)
# y_from_top values converted: body_y = body_half_length - y_from_top
# Body length = 444.5mm, so body_half = 222.25mm
# ============================================================================
BODY_HALF_LENGTH = 222.25  # mm (444.5 / 2)

def y_from_top_to_body_y(y_from_top: float) -> float:
    """Convert y_from_top (spec) to body-centered Y coordinate."""
    return BODY_HALF_LENGTH - y_from_top


# Neck pocket: 76.2 x 55.9 mm, y_from_top=53.3
NECK_POCKET = {
    "x_center": 0.0,
    "y_center": y_from_top_to_body_y(53.3),  # 168.95
    "length": 76.2,
    "width": 55.9,
    "corner_radius": 6.35,
}

# Neck pickup: 92 x 40 mm, y_from_top=167.6
NECK_PICKUP = {
    "x_center": 0.0,
    "y_center": y_from_top_to_body_y(167.6),  # 54.65
    "length": 92.0,
    "width": 40.0,
    "corner_radius": 3.0,
}

# Bridge pickup: 92 x 40 mm, y_from_top=294.6
BRIDGE_PICKUP = {
    "x_center": 0.0,
    "y_center": y_from_top_to_body_y(294.6),  # -72.35
    "length": 92.0,
    "width": 40.0,
    "corner_radius": 3.0,
}

# Bridge route: 95 x 42 mm, y_from_top=320
BRIDGE_ROUTE = {
    "x_center": 0.0,
    "y_center": y_from_top_to_body_y(320.0),  # -97.75
    "length": 95.0,
    "width": 42.0,
    "corner_radius": 3.175,
}

# Rear electronics (Pi 5): 95 x 65 mm, y_from_top=275.7, x_center=36.8
ELECTRONICS_CAVITY = {
    "x_center": 36.8,
    "y_center": y_from_top_to_body_y(275.7),  # -53.45
    "length": 95.0,
    "width": 65.0,
    "corner_radius": 6.0,
}

# Teensy I/O pocket: 70 x 25 mm, y_from_top=133.5, x_center=36.8
TEENSY_IO_POCKET = {
    "x_center": 36.8,
    "y_center": y_from_top_to_body_y(133.5),  # 88.75
    "length": 70.0,
    "width": 25.0,
    "corner_radius": 3.0,
}


def recenter_points(pts):
    """Recenter a list of (x, y) points so the centroid is at (0, 0)."""
    x_coords = [p[0] for p in pts]
    y_coords = [p[1] for p in pts]
    x_offset = (max(x_coords) + min(x_coords)) / 2
    y_offset = (max(y_coords) + min(y_coords)) / 2
    return [(p[0] - x_offset, p[1] - y_offset) for p in pts]


def create_rounded_rect_points(x_center, y_center, length, width, corner_radius, segments=8):
    """Generate points for a rounded rectangle cavity."""
    import math

    half_l = length / 2
    half_w = width / 2
    r = min(corner_radius, half_l, half_w)

    pts = []

    # Four corners with arcs
    corners = [
        (x_center + half_l - r, y_center + half_w - r, 0),      # top-right
        (x_center - half_l + r, y_center + half_w - r, 90),     # top-left
        (x_center - half_l + r, y_center - half_w + r, 180),    # bottom-left
        (x_center + half_l - r, y_center - half_w + r, 270),    # bottom-right
    ]

    for cx, cy, start_angle in corners:
        for i in range(segments + 1):
            angle = math.radians(start_angle + (90 * i / segments))
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            pts.append((px, py))

    return pts


def add_cavity_polyline(msp, cavity, layer, color=None):
    """Add a rounded rectangle cavity to the DXF."""
    pts = create_rounded_rect_points(
        cavity["x_center"],
        cavity["y_center"],
        cavity["length"],
        cavity["width"],
        cavity["corner_radius"],
    )
    attribs = {"layer": layer}
    if color:
        attribs["color"] = color
    msp.add_lwpolyline(pts, close=True, dxfattribs=attribs)


def main():
    """Generate the Smart Guitar CAM-ready DXF."""

    # Recenter the body outline on (0, 0)
    body_pts_centered = recenter_points(BODY_PTS)

    # Calculate the offset applied so we can shift voids too
    x_coords = [p[0] for p in BODY_PTS]
    y_coords = [p[1] for p in BODY_PTS]
    x_offset = (max(x_coords) + min(x_coords)) / 2
    y_offset = (max(y_coords) + min(y_coords)) / 2
    print(f"Recentering: X offset = {x_offset:.2f} mm, Y offset = {y_offset:.2f} mm")

    # Apply same offset to voids
    void_upper_bass_centered = [(p[0] - x_offset, p[1] - y_offset) for p in VOID_UPPER_BASS]
    void_upper_treble_centered = [(p[0] - x_offset, p[1] - y_offset) for p in VOID_UPPER_TREBLE]
    void_lower_bass_centered = [(p[0] - x_offset, p[1] - y_offset) for p in VOID_LOWER_BASS]

    # Create new DXF document (AutoCAD 2010 format)
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create layers with colors
    layers = [
        ("BODY_OUTLINE", 7),       # White
        ("VOIDS", 1),              # Red
        ("NECK_POCKET", 3),        # Green
        ("PICKUP_CAVITIES", 5),    # Blue
        ("BRIDGE_ROUTE", 4),       # Cyan
        ("ELECTRONICS_CAVITY", 6), # Magenta (rear reference)
        ("ARDUINO_POCKET", 30),    # Orange (rear reference)
        ("CENTERLINE", 8),         # Gray
        ("ANNOTATIONS", 7),        # White
    ]

    for name, color in layers:
        doc.layers.add(name, color=color)

    # 1. BODY_OUTLINE - 60-point perimeter (closed, centered)
    msp.add_lwpolyline(body_pts_centered, close=True, dxfattribs={"layer": "BODY_OUTLINE"})

    # 2. VOIDS - 3 Klein-style cutouts (centered)
    msp.add_lwpolyline(void_upper_bass_centered, close=True, dxfattribs={"layer": "VOIDS"})
    msp.add_lwpolyline(void_upper_treble_centered, close=True, dxfattribs={"layer": "VOIDS"})
    msp.add_lwpolyline(void_lower_bass_centered, close=True, dxfattribs={"layer": "VOIDS"})

    # Adjust cavity positions for the recentering offset
    def adjust_cavity(cav, x_off, y_off):
        return {
            **cav,
            "x_center": cav["x_center"] - x_off,
            "y_center": cav["y_center"] - y_off,
        }

    # 3. NECK_POCKET - bolt-on pocket
    add_cavity_polyline(msp, adjust_cavity(NECK_POCKET, x_offset, y_offset), "NECK_POCKET")

    # 4. PICKUP_CAVITIES - neck and bridge humbuckers
    add_cavity_polyline(msp, adjust_cavity(NECK_PICKUP, x_offset, y_offset), "PICKUP_CAVITIES")
    add_cavity_polyline(msp, adjust_cavity(BRIDGE_PICKUP, x_offset, y_offset), "PICKUP_CAVITIES")

    # 5. BRIDGE_ROUTE - headless bridge mounting
    add_cavity_polyline(msp, adjust_cavity(BRIDGE_ROUTE, x_offset, y_offset), "BRIDGE_ROUTE")

    # 6. ELECTRONICS_CAVITY - rear Pi 5 cavity (reference)
    add_cavity_polyline(msp, adjust_cavity(ELECTRONICS_CAVITY, x_offset, y_offset), "ELECTRONICS_CAVITY")

    # 7. TEENSY_IO_POCKET - rear Teensy I/O coprocessor cavity (reference)
    add_cavity_polyline(msp, adjust_cavity(TEENSY_IO_POCKET, x_offset, y_offset), "TEENSY_IO_POCKET")

    # Get actual body bounds after centering
    body_y_max = max(p[1] for p in body_pts_centered)
    body_y_min = min(p[1] for p in body_pts_centered)

    # 8. CENTERLINE - vertical alignment reference
    msp.add_line(
        (0, body_y_max + 20),
        (0, body_y_min - 20),
        dxfattribs={"layer": "CENTERLINE", "linetype": "CENTER"}
    )

    # 9. ANNOTATIONS - model info
    msp.add_text(
        "Smart Guitar v1.1 CAM",
        dxfattribs={"layer": "ANNOTATIONS", "height": 5}
    ).set_placement((0, body_y_max + 30))

    msp.add_text(
        "60-pt body, 3 voids, 6 cavities",
        dxfattribs={"layer": "ANNOTATIONS", "height": 3}
    ).set_placement((0, body_y_max + 22))

    msp.add_text(
        "Origin: body center (0, 0)",
        dxfattribs={"layer": "ANNOTATIONS", "height": 3}
    ).set_placement((0, body_y_min - 25))

    # Output path
    output_dir = Path(__file__).parent.parent / "services" / "api" / "app" / "instrument_geometry" / "body" / "dxf" / "electric"
    output_path = output_dir / "Smart-Guitar-v1_CAM.dxf"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save DXF
    doc.saveas(str(output_path))

    print(f"Generated: {output_path}")
    print(f"  Body points: {len(BODY_PTS)}")
    print(f"  Voids: 3 (upper_bass: {len(VOID_UPPER_BASS)} pts, upper_treble: {len(VOID_UPPER_TREBLE)} pts, lower_bass: {len(VOID_LOWER_BASS)} pts)")
    print(f"  Layers: {len(layers)}")
    print(f"  Cavities: neck_pocket, neck_pickup, bridge_pickup, bridge_route, electronics (rear), teensy_io (rear)")

    # Run audit
    auditor = doc.audit()
    if auditor.errors:
        print(f"  Audit: {len(auditor.errors)} errors")
        for error in auditor.errors[:5]:
            print(f"    - {error}")
    else:
        print("  Audit: CLEAN")

    # Calculate bounding box (using centered points)
    x_coords_c = [p[0] for p in body_pts_centered]
    y_coords_c = [p[1] for p in body_pts_centered]
    width = max(x_coords_c) - min(x_coords_c)
    height = max(y_coords_c) - min(y_coords_c)
    x_center_final = (max(x_coords_c) + min(x_coords_c)) / 2

    print(f"  Bounding box: {width:.1f} x {height:.1f} mm")
    print(f"  X centerline offset: {x_center_final:.2f} mm (should be 0.00)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
