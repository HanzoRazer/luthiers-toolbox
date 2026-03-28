"""
Smart Guitar — Back Face DXF Generator
=======================================
Generates rear routing plan.
Body outline: same orientation as front (NOT mirrored).
Cavities: rear-only (electronics, preamp, antenna, wiring).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api"))

import ezdxf
from ezdxf import units

# ── Import traced outline (scaled, 60 pts) ───────────────────────────────────
from app.instrument_geometry.body.traced_outlines.smart_guitar_traced_outline import (
    body_pts,
    void_upper_bass_pts as upper_bass_void,
    void_upper_treble_pts as upper_treble_void,
    void_lower_bass_pts as lower_bass_void,
)

# ── Constants ────────────────────────────────────────────────────────────────
BODY_TOP_Y = 114.87   # mm — body top in traced outline world coordinates
OUTPUT = Path(r"C:\Users\thepr\Downloads\Smart Guitar _DXFs\smart_guitar_back_v3.dxf")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def add_rounded_rect(msp, layer, cx, cy, w, h, r, color):
    """Add a rounded rectangle as LWPOLYLINE."""
    hw, hh = w / 2, h / 2
    r = min(r, hw - 0.1, hh - 0.1)
    pts = [
        (cx - hw + r, cy + hh),
        (cx + hw - r, cy + hh),
        (cx + hw,     cy + hh - r),
        (cx + hw,     cy - hh + r),
        (cx + hw - r, cy - hh),
        (cx - hw + r, cy - hh),
        (cx - hw,     cy - hh + r),
        (cx - hw,     cy + hh - r),
    ]
    poly = msp.add_lwpolyline(pts, close=True)
    poly.dxf.layer = layer
    poly.dxf.color = color
    return poly


def main():
    doc = ezdxf.new("R2000")
    doc.header["$INSUNITS"] = 4  # mm
    msp = doc.modelspace()

    # ── Layers ────────────────────────────────────────────────────────────────
    layers = {
        "BODY_OUTLINE":      (7,  "Continuous"),   # white
        "VOID_UPPER_BASS":   (8,  "Continuous"),   # gray
        "VOID_UPPER_TREBLE": (8,  "Continuous"),
        "VOID_LOWER_BASS":   (8,  "Continuous"),
        "CENTERLINE":        (8,  "CENTER"),        # gray dashed
        "REAR_ELECTRONICS":  (5,  "Continuous"),   # blue
        "ARDUINO_POCKET":    (4,  "Continuous"),   # cyan
        "ANTENNA_RECESS":    (6,  "Continuous"),   # magenta
        "WIRING_CHANNEL":    (30, "Continuous"),   # orange
    }
    for name, (color, ltype) in layers.items():
        layer = doc.layers.new(name)
        layer.color = color

    # ── Body outline (NOT mirrored — same orientation as front) ───────────────
    poly = msp.add_lwpolyline(body_pts, close=True)
    poly.dxf.layer = "BODY_OUTLINE"
    poly.dxf.color = 7

    # ── Weight reduction voids ────────────────────────────────────────────────
    for pts, layer in [
        (upper_bass_void,    "VOID_UPPER_BASS"),
        (upper_treble_void,  "VOID_UPPER_TREBLE"),
        (lower_bass_void,    "VOID_LOWER_BASS"),
    ]:
        poly = msp.add_lwpolyline(pts, close=True)
        poly.dxf.layer = layer
        poly.dxf.color = 8

    # ── Centerline ────────────────────────────────────────────────────────────
    body_ys = [p[1] for p in body_pts]
    msp.add_line(
        (0, max(body_ys) + 10),
        (0, min(body_ys) - 10),
        dxfattribs={"layer": "CENTERLINE", "color": 8},
    )

    # ── Rear Electronics Cavity (Pi 5 + battery) ──────────────────────────────
    # y_from_top = 275.7mm → cy = 114.87 - 275.7 = -160.83
    add_rounded_rect(
        msp, "REAR_ELECTRONICS", cx=0,
        cy=BODY_TOP_Y - 275.7,
        w=65, h=95, r=6.0, color=5,
    )

    # ── Arduino / Preamp Pocket (Teensy 4.1) ──────────────────────────────────
    # y_from_top = 133.5mm → cy = 114.87 - 133.5 = -18.63
    add_rounded_rect(
        msp, "ARDUINO_POCKET", cx=0,
        cy=BODY_TOP_Y - 133.5,
        w=60, h=80, r=4.0, color=4,
    )

    # ── Antenna Recess (inside rear electronics cavity) ───────────────────────
    # y_from_top = 202.6mm → cy = 114.87 - 202.6 = -87.73
    add_rounded_rect(
        msp, "ANTENNA_RECESS", cx=0,
        cy=BODY_TOP_Y - 202.6,
        w=30, h=50, r=3.0, color=6,
    )

    # ── Wiring Channels (connecting preamp pocket to rear electronics) ─────────
    # Vertical channel: between arduino pocket bottom and rear electronics top
    # arduino bottom ≈ cy_arduino - 40mm, rear_elec top ≈ cy_rear + 47.5mm
    cy_arduino = BODY_TOP_Y - 133.5
    cy_rear    = BODY_TOP_Y - 275.7
    channel_top    = cy_arduino - 40    # bottom of arduino pocket
    channel_bottom = cy_rear + 47.5     # top of rear electronics
    channel_mid    = (channel_top + channel_bottom) / 2
    channel_h      = channel_top - channel_bottom

    if channel_h > 0:
        add_rounded_rect(
            msp, "WIRING_CHANNEL", cx=0,
            cy=channel_mid,
            w=10, h=channel_h, r=3.175, color=30,
        )

    # ── Save ──────────────────────────────────────────────────────────────────
    doc.saveas(str(OUTPUT))

    # ── Report ────────────────────────────────────────────────────────────────
    doc2 = ezdxf.readfile(str(OUTPUT))
    msp2 = doc2.modelspace()
    entities = list(msp2)
    all_xs, all_ys = [], []
    for e in entities:
        if hasattr(e, "get_points"):
            for pt in e.get_points():
                all_xs.append(pt[0])
                all_ys.append(pt[1])

    print(f"\n=== Smart Guitar Back View DXF ===")
    print(f"Output:   {OUTPUT}")
    print(f"Entities: {len(entities)}")
    print(f"X range:  {min(all_xs):.1f} to {max(all_xs):.1f} mm")
    print(f"Y range:  {min(all_ys):.1f} to {max(all_ys):.1f} mm")
    print(f"\nLayers:")
    by_layer = {}
    for e in entities:
        layer = e.dxf.layer
        by_layer[layer] = by_layer.get(layer, 0) + 1
    for layer, count in sorted(by_layer.items()):
        print(f"  {layer}: {count}")

    print(f"\nCavity positions (cy = BODY_TOP_Y - y_from_top):")
    print(f"  REAR_ELECTRONICS cy: {BODY_TOP_Y - 275.7:.2f}mm")
    print(f"  ARDUINO_POCKET   cy: {BODY_TOP_Y - 133.5:.2f}mm")
    print(f"  ANTENNA_RECESS   cy: {BODY_TOP_Y - 202.6:.2f}mm")
    print(f"\nVerification:")
    body_y_min = min(p[1] for p in body_pts)
    body_y_max = max(p[1] for p in body_pts)
    rear_cy = BODY_TOP_Y - 275.7
    arduino_cy = BODY_TOP_Y - 133.5
    print(f"  Body Y range: {body_y_min:.1f} to {body_y_max:.1f}")
    print(f"  REAR_ELECTRONICS extents: {rear_cy - 47.5:.1f} to {rear_cy + 47.5:.1f}")
    print(f"  ARDUINO_POCKET extents:   {arduino_cy - 40:.1f} to {arduino_cy + 40:.1f}")
    all_inside = (
        rear_cy - 47.5 > body_y_min and rear_cy + 47.5 < body_y_max and
        arduino_cy - 40 > body_y_min and arduino_cy + 40 < body_y_max
    )
    print(f"  All cavities inside body: {all_inside}")
    print(f"\nDone.")


if __name__ == "__main__":
    main()
