#!/usr/bin/env python3
"""
Martin OO custom build — rosette design via RMOS rosette API.

Rosette spec:
  Outer ring: walnut (warm brown), 5mm
  Purfling: Spanish wave pattern, 2mm
  Inner ring: mahogany (reddish brown), 4mm
  Soundhole diameter: standard OO = 85mm

Calls:
  POST /api/rmos/rosette/segment-ring
  POST /api/rmos/rosette/generate-slices
  POST /api/rmos/rosette/export-cnc

Reports API responses. If spanish_wave is not in the pattern registry,
lists available tile patterns.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add app to path
API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))

from fastapi.testclient import TestClient
from app.main import app

# Available tile patterns (from cam/rosette/tile_segmentation.py TilePattern)
TILE_PATTERNS = ["checkerboard", "herringbone", "radial", "solid", "spanish_wave"]

# User's desired payload (designer-style: soundhole + rings array)
USER_PAYLOAD = {
    "soundhole_diameter_mm": 85,
    "rings": [
        {"role": "inner", "material": "mahogany_honduran", "width_mm": 4.0},
        {"role": "purfling", "pattern": "spanish_wave", "width_mm": 2.0},
        {"role": "outer", "material": "walnut", "width_mm": 5.0},
    ],
}

# API expects single ring: ring_id, radius_mm (average), width_mm, tile_length_mm, kerf_mm, etc.
# OO soundhole 85mm -> inner radius 42.5mm
# Inner ring: r_avg = 42.5 + 2 = 44.5, width 4
# Purfling:   r_avg = 46.5 + 1 = 47.5, width 2  (use herringbone as purfling lookalike; no spanish_wave)
# Outer ring: r_avg = 48.5 + 2.5 = 51, width 5
MARTIN_OO_RINGS = [
    {"ring_id": 0, "radius_mm": 44.5, "width_mm": 4.0, "tile_length_mm": 5.0, "pattern": "checkerboard"},
    {"ring_id": 1, "radius_mm": 47.5, "width_mm": 2.0, "tile_length_mm": 4.0, "pattern": "herringbone"},
    {"ring_id": 2, "radius_mm": 51.0, "width_mm": 5.0, "tile_length_mm": 6.0, "pattern": "checkerboard"},
]


def main() -> None:
    client = TestClient(app)

    print("=" * 60)
    print("TILE PATTERN REGISTRY (segment-ring 'pattern' field)")
    print("=" * 60)
    print("Available patterns:", ", ".join(TILE_PATTERNS))
    if "spanish_wave" not in TILE_PATTERNS:
        print("NOTE: 'spanish_wave' is NOT in the registry. Use one of the above.")
        print("      (Herringbone is often used for purfling-style segments.)")
    print()

    print("=" * 60)
    print("STEP 1: POST /api/rmos/rosette/segment-ring")
    print("=" * 60)
    print("(A) Your payload (designer format: soundhole_diameter_mm + rings[])")
    print(json.dumps(USER_PAYLOAD, indent=2))
    resp_a = client.post("/api/rmos/rosette/segment-ring", json=USER_PAYLOAD)
    print("Response status:", resp_a.status_code)
    body_a = resp_a.json()
    print("Response body:", json.dumps(body_a, indent=2))
    if body_a.get("ok") and body_a.get("segments"):
        print("Segments count:", len(body_a["segments"]))
    print()

    print("(B) API-native format (single ring: outer walnut, radius_mm=51, width_mm=5)")
    ring_outer = {"ring_id": 2, "radius_mm": 51.0, "width_mm": 5.0, "tile_length_mm": 6.0}
    print(json.dumps({"ring": ring_outer}, indent=2))
    resp_b = client.post("/api/rmos/rosette/segment-ring", json={"ring": ring_outer})
    print("Response status:", resp_b.status_code)
    body_b = resp_b.json()
    print("Response body:", json.dumps(body_b, indent=2))
    if body_b.get("ok"):
        print("Segmentation ID:", body_b.get("segmentation_id"))
        print("Tile count:", body_b.get("tile_count"))
    print()

    print("=" * 60)
    print("STEP 2: POST /api/rmos/rosette/generate-slices")
    print("=" * 60)
    payload_slices = {"ring": ring_outer}
    print("Payload:", json.dumps(payload_slices, indent=2))
    resp_s = client.post("/api/rmos/rosette/generate-slices", json=payload_slices)
    print("Response status:", resp_s.status_code)
    body_s = resp_s.json()
    print("Response body:", json.dumps(body_s, indent=2))
    if body_s.get("ok") and body_s.get("slices"):
        print("Slices count:", len(body_s["slices"]))
    print()

    print("=" * 60)
    print("STEP 3: POST /api/rmos/rosette/export-cnc")
    print("=" * 60)
    payload_cnc = {
        "ring": ring_outer,
        "material": "hardwood",
        "origin_x_mm": 0.0,
        "origin_y_mm": 0.0,
        "rotation_deg": 0.0,
        "safe_z_mm": 5.0,
        "spindle_rpm": 12000,
        "tool_id": 1,
    }
    print("Payload (ring + machine params):", json.dumps(payload_cnc, indent=2))
    resp_c = client.post("/api/rmos/rosette/export-cnc", json=payload_cnc)
    print("Response status:", resp_c.status_code)
    body_c = resp_c.json()
    # Truncate gcode in report for readability
    if body_c.get("ok") and body_c.get("gcode"):
        gcode_preview = body_c["gcode"][:800] + "\n... (truncated)" if len(body_c.get("gcode", "")) > 800 else body_c["gcode"]
        report = {**body_c, "gcode": gcode_preview}
    else:
        report = body_c
    print("Response body:", json.dumps(report, indent=2))
    if body_c.get("ok"):
        print("Job ID:", body_c.get("job_id"))
        print("Segment count:", body_c.get("segment_count"))
        print("G-code length (chars):", len(body_c.get("gcode", "")))
    print()

    # Martin OO full 3-ring design via POST /rosette/design (GAP-NEW-1)
    print("=" * 60)
    print("MARTIN OO 3-RING: POST /api/rmos/rosette/design")
    print("=" * 60)
    design_payload = {
        "soundhole_diameter_mm": 85,
        "rings": [
            {"role": "inner", "material": "mahogany", "width_mm": 4.0, "radius_mm": 46.5},
            {"role": "purfling", "pattern": "herringbone", "width_mm": 2.0, "radius_mm": 50.0},
            {"role": "outer", "material": "walnut", "width_mm": 5.0, "radius_mm": 52.5},
        ],
    }
    print("Payload:", json.dumps(design_payload, indent=2))
    resp_d = client.post("/api/rmos/rosette/design", json=design_payload)
    print("Response status:", resp_d.status_code)
    body_d = resp_d.json()
    if body_d.get("ok"):
        print("ok:", body_d.get("ok"))
        print("ring_count:", body_d.get("ring_count"))
        print("job_ids:", body_d.get("job_ids"))
        for gr in body_d.get("gcode_by_ring", []):
            print(f"  Ring {gr['ring_id']}: job_id={gr['job_id']}, line_count={gr['line_count']}")
        if body_d.get("combined_gcode"):
            total_lines = len(body_d["combined_gcode"].strip().splitlines())
            print("combined_gcode line_count:", total_lines)
    else:
        print("error:", body_d.get("error"))
    print()
    print("Done.")


if __name__ == "__main__":
    main()
