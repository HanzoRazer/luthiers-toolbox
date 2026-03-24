"""
Smart Guitar DXF Generator Router
=================================

Generates complete routing DXF from the Smart Guitar database spec.
No file upload required - reads smart_guitar_v1.json from instrument
registry at request time.

Endpoint: GET /api/instruments/smart-guitar/dxf

Returns R2010 DXF with 12 routing layers:
- BODY_OUTLINE: Explorer-Klein hybrid silhouette
- NECK_POCKET: bolt-on pocket 76.2x55.9x15.9mm
- NECK_PICKUP / BRIDGE_PICKUP: humbucker routes
- BRIDGE_ROUTE: headless bridge mounting
- REAR_ELECTRONICS: Raspberry Pi 5 cavity
- ARDUINO_POCKET: preamp/battery bay
- ANTENNA_RECESS: RF window shelf
- CONTROL_PLATE: surface recess
- OUTPUT_JACK: angled bore
- USB_PORT: edge-routed slot
- BOLT_HOLES: 4x neck bolts
"""

from fastapi import APIRouter
from fastapi.responses import Response
import ezdxf
import json
import tempfile
import os
from pathlib import Path

router = APIRouter(
    prefix="/api/instruments/smart-guitar",
    tags=["instruments", "smart-guitar", "dxf"],
)

SPEC_PATH = (
    Path(__file__).parent.parent.parent.parent  # go up to app/
    / "instrument_geometry"
    / "body"
    / "specs"
    / "smart_guitar_v1.json"
)


@router.get(
    "/dxf",
    summary="Generate Smart Guitar DXF from spec",
    response_class=Response,
    responses={
        200: {
            "content": {"application/dxf": {}},
            "description": "Smart Guitar routing DXF",
        }
    },
)
def generate_smart_guitar_dxf(
    version: str = "v3",
    include_cavities: bool = True,
    include_body_outline: bool = True,
):
    """
    Generate a complete Smart Guitar DXF from the database spec.
    No file uploads required.

    Returns a downloadable DXF with layers:
    - BODY_OUTLINE: Explorer-Klein hybrid silhouette
    - NECK_POCKET: bolt-on pocket 76.2x55.9x15.9mm
    - NECK_PICKUP / BRIDGE_PICKUP: humbucker routes
    - REAR_ELECTRONICS / ARDUINO_POCKET: electronics bays
    - ANTENNA_RECESS / CONTROL_PLATE / OUTPUT_JACK / USB_PORT
    - BOLT_HOLES: 4x neck bolts
    """
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    # Add layers with distinct colors (ACI)
    layer_colors = {
        "BODY_OUTLINE": 7,  # White
        "NECK_POCKET": 5,  # Magenta
        "NECK_PICKUP": 1,  # Red
        "BRIDGE_PICKUP": 1,  # Red
        "BRIDGE_ROUTE": 3,  # Green
        "REAR_ELECTRONICS": 4,  # Cyan
        "ARDUINO_POCKET": 4,  # Cyan
        "ANTENNA_RECESS": 6,  # Magenta
        "CONTROL_PLATE": 2,  # Yellow
        "OUTPUT_JACK": 30,  # Orange
        "USB_PORT": 30,  # Orange
        "BOLT_HOLES": 8,  # Gray
    }

    for name, color in layer_colors.items():
        doc.layers.add(name, color=color)

    # Body dimensions
    body = spec["body"]["dimensions"]
    BL = body["length_mm"]  # 444.5
    BW = body["width_max_mm"]  # 368.3
    hl = BL / 2  # half length
    hw = BW / 2  # half width

    # Bout widths
    lbh = spec["body"]["lower_bout"]["width_mm"] / 2  # 152.4 (304.8/2)
    ubh = spec["body"]["upper_section"]["width_mm"] / 2  # 127 (254/2)

    def add_rect(layer: str, cx: float, cy: float, length: float, width: float, r: float = 3.0):
        """Add a rectangle (polyline) centered at (cx, cy)."""
        x0, y0 = cx - width / 2, cy - length / 2
        x1, y1 = cx + width / 2, cy + length / 2
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        msp.add_lwpolyline(pts, dxfattribs={"layer": layer}, close=True)

    if include_body_outline:
        # Explorer-Klein hybrid body outline
        # Origin at body center (0, 0), Y+ toward neck
        pts = [
            # Upper horn (treble side) - start at neck
            (ubh * 0.15, hl),
            (ubh * 0.85, hl * 0.82),
            (hw * 0.90, hl * 0.62),
            (hw, hl * 0.35),
            (hw, hl * 0.10),
            # Right side curve down
            (hw * 0.98, -hl * 0.08),
            (hw * 0.92, -hl * 0.28),
            (hw * 0.88, -hl * 0.50),
            (hw * 0.78, -hl * 0.68),
            # Lower bout V-point
            (lbh * 0.90, -hl * 0.82),
            (lbh * 0.40, -hl * 0.96),
            (0, -hl),  # V-point
            (-lbh * 0.40, -hl * 0.96),
            (-lbh * 0.90, -hl * 0.82),
            # Left side curve up
            (-hw * 0.78, -hl * 0.68),
            (-hw * 0.88, -hl * 0.50),
            (-hw * 0.92, -hl * 0.28),
            (-hw * 0.98, -hl * 0.08),
            (-hw, hl * 0.10),
            (-hw, hl * 0.35),
            # Upper cutaway (bass side) - Klein ergonomic relief
            (-hw * 0.95, hl * 0.50),
            (-hw * 0.80, hl * 0.62),
            (-ubh * 0.95, hl * 0.70),
            (-ubh * 0.75, hl * 0.78),
            (-ubh * 0.50, hl * 0.85),
            (-ubh * 0.25, hl * 0.90),
            (-ubh * 0.10, hl * 0.94),
            # Back to start
            (ubh * 0.15, hl),
        ]
        msp.add_lwpolyline(pts, dxfattribs={"layer": "BODY_OUTLINE"}, close=True)

    if include_cavities:
        cavs = spec["cavities"]

        # Neck pocket
        d = cavs["neck_pocket"]["dimensions_mm"]
        p = cavs["neck_pocket"]["body_position_mm"]
        cy = hl - p["y_from_top"] - d["length"] / 2
        add_rect("NECK_POCKET", 0, cy, d["length"], d["width"])

        # Bolt holes (4x pattern)
        if "bolt_pattern" in cavs["neck_pocket"]:
            for bolt in cavs["neck_pocket"]["bolt_pattern"].get(
                "positions_from_pocket_center_mm", []
            ):
                msp.add_circle(
                    center=(bolt["x"], cy + bolt["y"]),
                    radius=2.0,
                    dxfattribs={"layer": "BOLT_HOLES"},
                )
        else:
            # Default 4-bolt pattern if not specified
            bolt_offsets = [
                (-20, -25),
                (20, -25),
                (-20, 25),
                (20, 25),
            ]
            for bx, by in bolt_offsets:
                msp.add_circle(
                    center=(bx, cy + by),
                    radius=2.0,
                    dxfattribs={"layer": "BOLT_HOLES"},
                )

        # Pickups
        pickup_routes = [
            ("NECK_PICKUP", "neck_pickup_route"),
            ("BRIDGE_PICKUP", "bridge_pickup_route"),
        ]
        for layer, key in pickup_routes:
            if key in cavs:
                d = cavs[key]["dimensions_mm"]
                p = cavs[key]["body_position_mm"]
                cy = hl - p["y_from_top"]
                add_rect(layer, 0, cy, d["length"], d["width"])

        # Bridge route
        if "bridge_route" in cavs:
            d = cavs["bridge_route"]["dimensions_mm"]
            p = cavs["bridge_route"]["body_position_mm"]
            cy = hl - p["y_from_top"]
            add_rect(
                "BRIDGE_ROUTE",
                0,
                cy,
                d.get("bridge_length", 95.0),
                d.get("bridge_width", 42.0),
            )

        # Rear electronics cavity (Pi 5)
        if "rear_electronics_cavity" in cavs:
            d = cavs["rear_electronics_cavity"]["dimensions_mm"]
            p = cavs["rear_electronics_cavity"]["body_position_mm"]
            cx = p.get("x_center", 36.8)
            cy = hl - p.get("y_from_top", 275.7)
            add_rect("REAR_ELECTRONICS", cx, cy, d["length"], d["width"])

        # Arduino/preamp pocket
        if "arduino_preamp_pocket" in cavs:
            d = cavs["arduino_preamp_pocket"]["dimensions_mm"]
            p = cavs["arduino_preamp_pocket"]["body_position_mm"]
            cx = p.get("x_center", 36.8)
            cy = hl - p.get("y_from_top", 133.5)
            add_rect("ARDUINO_POCKET", cx, cy, d["length"], d["width"])

        # Antenna recess (shelf in Pi cavity)
        if "antenna_recess" in cavs:
            d = cavs["antenna_recess"]["dimensions_mm"]
            p = cavs["antenna_recess"]["body_position_mm"]
            cx = p.get("x_center", 22.2)
            cy = hl - p.get("y_from_top", 202.6)
            add_rect("ANTENNA_RECESS", cx, cy, d["length"], d["width"])

        # Control plate surface
        if "control_plate_surface" in cavs:
            d = cavs["control_plate_surface"]["dimensions_mm"]
            p = cavs["control_plate_surface"]["body_position_mm"]
            cx = p.get("x_center", 55.2)
            cy = hl - p.get("y_from_top", 346.7)
            add_rect("CONTROL_PLATE", cx, cy, d["length"], d["width"])

        # Output jack (angled bore)
        if "output_jack" in cavs:
            p = cavs["output_jack"]["body_position_mm"]
            d = cavs["output_jack"]["dimensions_mm"]
            cx = p.get("x_center", 110.4)
            cy = hl - p.get("y_from_top", 391.2)
            radius = d.get("bore_diameter", 12.7) / 2
            msp.add_circle(
                center=(cx, cy),
                radius=radius,
                dxfattribs={"layer": "OUTPUT_JACK"},
            )

        # USB-C port (edge slot)
        if "usb_c_port" in cavs:
            d = cavs["usb_c_port"]["dimensions_mm"]
            p = cavs["usb_c_port"]["body_position_mm"]
            # USB port is at body edge
            cx = hw - d.get("slot_depth", 7.0) / 2
            cy = hl - p.get("y_from_top", 239.4)
            add_rect(
                "USB_PORT",
                cx,
                cy,
                d.get("slot_height", 6.5),
                d.get("slot_width", 12.0),
            )

    # Serialize to bytes via tempfile (ezdxf requires file path)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dxf", delete=False) as f:
        temp_path = f.name
    try:
        doc.saveas(temp_path)
        with open(temp_path, "rb") as f:
            dxf_bytes = f.read()
    finally:
        os.unlink(temp_path)

    filename = f"smart_guitar_{version}.dxf"
    return Response(
        content=dxf_bytes,
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
