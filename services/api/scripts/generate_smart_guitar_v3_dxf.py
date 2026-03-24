#!/usr/bin/env python3
"""
Generate Smart Guitar DXF from spec JSON.

Usage:
    python scripts/generate_smart_guitar_v3_dxf.py \
        --spec app/instrument_geometry/body/specs/smart_guitar_v1.json \
        --output data/smart_guitar_v4_body_fixed.dxf
"""

import argparse
import json
from pathlib import Path

import ezdxf


def load_spec(spec_path: Path) -> dict:
    """Load smart guitar spec JSON."""
    with open(spec_path, encoding="utf-8") as f:
        return json.load(f)


def generate_explorer_klein_body_outline(length_mm: float, width_mm: float) -> list:
    """
    Generate Explorer-Klein hybrid body outline points.

    Parametric outline based on:
    - Explorer: Angular V-shaped lower bout, pointed horns
    - Klein: Ergonomic negative-space cutaways

    Centered at (0, 0) for CAM compatibility.
    """
    # Half dimensions for centering
    half_w = width_mm / 2
    half_l = length_mm / 2

    # Explorer-Klein parametric outline (12 points)
    # Clockwise from bottom V-point
    points = [
        # Bottom V-point (Explorer heritage)
        (0, -half_l),

        # Lower right bout
        (half_w * 0.65, -half_l * 0.7),

        # Right waist (Klein ergonomic curve)
        (half_w * 0.85, -half_l * 0.3),

        # Right upper bout
        (half_w, half_l * 0.1),

        # Right horn tip (Explorer angular)
        (half_w * 0.7, half_l * 0.5),

        # Neck pocket right
        (half_w * 0.35, half_l * 0.7),

        # Top center (neck heel)
        (0, half_l),

        # Neck pocket left
        (-half_w * 0.35, half_l * 0.7),

        # Left horn tip (Explorer angular)
        (-half_w * 0.7, half_l * 0.5),

        # Left upper bout
        (-half_w, half_l * 0.1),

        # Left waist (Klein ergonomic curve)
        (-half_w * 0.85, -half_l * 0.3),

        # Lower left bout
        (-half_w * 0.65, -half_l * 0.7),
    ]

    return points


def create_dxf(spec: dict, output_path: Path):
    """Create DXF with all routing layers from spec."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Get body dimensions from spec
    body = spec.get("body", {})
    dims = body.get("dimensions", {})
    length_mm = dims.get("length_mm", 444.5)
    width_mm = dims.get("width_max_mm", 368.3)

    # Create layers
    layers = [
        "BODY_OUTLINE",
        "NECK_POCKET",
        "NECK_PICKUP",
        "BRIDGE_PICKUP",
        "BRIDGE_ROUTE",
        "PI_CAVITY",
        "ARDUINO_POCKET",
        "OUTPUT_JACK",
        "USB_PORT",
        "ANTENNA",
        "CONTROL_PLATE",
        "BOLT_HOLES",
    ]

    for layer in layers:
        doc.layers.add(layer)

    # Generate body outline
    body_points = generate_explorer_klein_body_outline(length_mm, width_mm)
    msp.add_lwpolyline(body_points, close=True, dxfattribs={"layer": "BODY_OUTLINE"})

    # Add routing features from spec cavities
    cavities = spec.get("cavities", {})

    # Neck pocket
    np = cavities.get("neck_pocket", {}).get("dimensions_mm", {})
    if np:
        np_l = np.get("length", 76.2)
        np_w = np.get("width", 55.9)
        np_y = length_mm / 2 - np_l / 2 - 10  # 10mm from top
        msp.add_lwpolyline([
            (-np_w/2, np_y),
            (np_w/2, np_y),
            (np_w/2, np_y + np_l),
            (-np_w/2, np_y + np_l),
        ], close=True, dxfattribs={"layer": "NECK_POCKET"})

    # Neck pickup (humbucker)
    pickup_dims = cavities.get("neck_pickup_route", {}).get("dimensions_mm", {})
    if pickup_dims:
        pu_l = pickup_dims.get("length", 92)
        pu_w = pickup_dims.get("width", 40)
        pu_y = length_mm * 0.15  # 15% from center toward neck
        msp.add_lwpolyline([
            (-pu_l/2, pu_y - pu_w/2),
            (pu_l/2, pu_y - pu_w/2),
            (pu_l/2, pu_y + pu_w/2),
            (-pu_l/2, pu_y + pu_w/2),
        ], close=True, dxfattribs={"layer": "NECK_PICKUP"})

    # Bridge pickup (humbucker)
    bridge_pu = cavities.get("bridge_pickup_route", {}).get("dimensions_mm", {})
    if bridge_pu:
        bp_l = bridge_pu.get("length", 92)
        bp_w = bridge_pu.get("width", 40)
        bp_y = -length_mm * 0.12  # 12% from center toward bridge
        msp.add_lwpolyline([
            (-bp_l/2, bp_y - bp_w/2),
            (bp_l/2, bp_y - bp_w/2),
            (bp_l/2, bp_y + bp_w/2),
            (-bp_l/2, bp_y + bp_w/2),
        ], close=True, dxfattribs={"layer": "BRIDGE_PICKUP"})

    # Bridge route (Tune-o-Matic)
    bridge = cavities.get("bridge_route", {}).get("dimensions_mm", {})
    if bridge:
        br_l = bridge.get("length", 105)
        br_w = bridge.get("width", 20)
        br_y = -length_mm * 0.22
        msp.add_lwpolyline([
            (-br_l/2, br_y - br_w/2),
            (br_l/2, br_y - br_w/2),
            (br_l/2, br_y + br_w/2),
            (-br_l/2, br_y + br_w/2),
        ], close=True, dxfattribs={"layer": "BRIDGE_ROUTE"})

    # Pi cavity (rear electronics)
    pi = cavities.get("rear_electronics_cavity", {}).get("dimensions_mm", {})
    if pi:
        pi_l = pi.get("length", 100)
        pi_w = pi.get("width", 70)
        pi_y = -length_mm * 0.05
        msp.add_lwpolyline([
            (-pi_l/2, pi_y - pi_w/2),
            (pi_l/2, pi_y - pi_w/2),
            (pi_l/2, pi_y + pi_w/2),
            (-pi_l/2, pi_y + pi_w/2),
        ], close=True, dxfattribs={"layer": "PI_CAVITY"})

    # Arduino pocket
    arduino = cavities.get("arduino_preamp_pocket", {}).get("dimensions_mm", {})
    if arduino:
        ar_l = arduino.get("length", 70)
        ar_w = arduino.get("width", 55)
        ar_x = width_mm * 0.25
        ar_y = -length_mm * 0.1
        msp.add_lwpolyline([
            (ar_x - ar_l/2, ar_y - ar_w/2),
            (ar_x + ar_l/2, ar_y - ar_w/2),
            (ar_x + ar_l/2, ar_y + ar_w/2),
            (ar_x - ar_l/2, ar_y + ar_w/2),
        ], close=True, dxfattribs={"layer": "ARDUINO_POCKET"})

    # Output jack
    jack = cavities.get("output_jack", {}).get("dimensions_mm", {})
    if jack:
        jack_d = jack.get("diameter", 12.7)
        jack_x = width_mm * 0.35
        jack_y = -length_mm * 0.35
        msp.add_circle((jack_x, jack_y), jack_d/2, dxfattribs={"layer": "OUTPUT_JACK"})

    # USB port
    usb = cavities.get("usb_c_port", {}).get("dimensions_mm", {})
    if usb:
        usb_w = usb.get("width", 15)
        usb_h = usb.get("height", 8)
        usb_x = -width_mm * 0.35
        usb_y = length_mm * 0.2
        msp.add_lwpolyline([
            (usb_x - usb_w/2, usb_y - usb_h/2),
            (usb_x + usb_w/2, usb_y - usb_h/2),
            (usb_x + usb_w/2, usb_y + usb_h/2),
            (usb_x - usb_w/2, usb_y + usb_h/2),
        ], close=True, dxfattribs={"layer": "USB_PORT"})

    # Antenna pocket
    antenna = cavities.get("antenna_recess", {}).get("dimensions_mm", {})
    if antenna:
        ant_l = antenna.get("length", 50)
        ant_w = antenna.get("width", 10)
        ant_x = -width_mm * 0.3
        ant_y = 0
        msp.add_lwpolyline([
            (ant_x - ant_l/2, ant_y - ant_w/2),
            (ant_x + ant_l/2, ant_y - ant_w/2),
            (ant_x + ant_l/2, ant_y + ant_w/2),
            (ant_x - ant_l/2, ant_y + ant_w/2),
        ], close=True, dxfattribs={"layer": "ANTENNA"})

    # Bolt holes (4 holes for neck)
    bolt_d = 4.5  # M4 clearance hole
    bolt_positions = [
        (-20, length_mm/2 - 20),
        (20, length_mm/2 - 20),
        (-20, length_mm/2 - 60),
        (20, length_mm/2 - 60),
    ]
    for x, y in bolt_positions:
        msp.add_circle((x, y), bolt_d/2, dxfattribs={"layer": "BOLT_HOLES"})

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output_path))

    # Count entities
    entity_count = len(list(msp))
    layer_count = len([l for l in doc.layers if l.dxf.name != "0"])

    print(f"Created: {output_path}")
    print(f"Body dimensions: {length_mm:.1f} x {width_mm:.1f} mm")
    print(f"Entities: {entity_count}")
    print(f"Layers: {layer_count}")

    return doc


def main():
    parser = argparse.ArgumentParser(description="Generate Smart Guitar DXF from spec")
    parser.add_argument("--spec", required=True, help="Path to spec JSON")
    parser.add_argument("--output", required=True, help="Output DXF path")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    output_path = Path(args.output)

    if not spec_path.exists():
        print(f"Error: Spec not found: {spec_path}")
        return 1

    spec = load_spec(spec_path)
    create_dxf(spec, output_path)
    return 0


if __name__ == "__main__":
    exit(main())
