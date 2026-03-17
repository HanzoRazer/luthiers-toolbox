"""
Design a custom rosette: "Midnight Walnut Burst"

A 16-segment design with:
  - Ring 0 (Soundhole Binding): Ebony binding
  - Ring 1 (Inner Purfling):    W/B/W purfling
  - Ring 2 (Main Channel):      Alternating walnut + abalone burst pattern
  - Ring 3 (Outer Purfling):    B/W/B purfling
  - Ring 4 (Outer Binding):     Walnut binding

Not found in the preset database — a novel custom design.
"""
import requests
import json
import sys
from pathlib import Path

BASE = "http://127.0.0.1:8000"
DESIGNER = f"{BASE}/api/art/rosette-designer"


def check(r, label):
    if r.status_code != 200:
        print(f"  FAIL [{r.status_code}] {label}: {r.text[:200]}")
        return False
    return True


# ─────────────────────────────────────────────────────────────────
# Step 1: Build the grid (tile placements)
# ─────────────────────────────────────────────────────────────────
print("=" * 60)
print("  Designing: Midnight Walnut Burst (16 segments)")
print("=" * 60)

NUM_SEGS = 16
SYM_MODE = "rotational"

# Build grid manually — ring_idx-seg_idx -> tile_id
grid = {}

# Ring 0: Soundhole Binding — solid ebony all segments
for s in range(NUM_SEGS):
    grid[f"0-{s}"] = "ebony"

# Ring 1: Inner Purfling — W/B/W purfling all segments
for s in range(NUM_SEGS):
    grid[f"1-{s}"] = "wbw"

# Ring 2: Main Channel — alternating walnut/abalone burst (the signature pattern)
for s in range(NUM_SEGS):
    if s % 4 == 0:
        grid[f"2-{s}"] = "abalone"
    elif s % 4 == 2:
        grid[f"2-{s}"] = "mop"
    elif s % 2 == 1:
        grid[f"2-{s}"] = "walnut"

# Ring 3: Outer Purfling — B/W/B purfling all segments
for s in range(NUM_SEGS):
    grid[f"3-{s}"] = "bwb"

# Ring 4: Outer Binding — walnut all segments
for s in range(NUM_SEGS):
    grid[f"4-{s}"] = "walnut"

print(f"\n  Grid built: {len(grid)} tile placements across 5 rings x {NUM_SEGS} segments")

# ─────────────────────────────────────────────────────────────────
# Step 2: Preview SVG
# ─────────────────────────────────────────────────────────────────
print("\n--- Step 2: Generate SVG Preview ---")

preview_req = {
    "grid": grid,
    "num_segs": NUM_SEGS,
    "ring_active": [True, True, True, True, True],
    "show_labels": True,
    "annotate_dims": True,
}

r = requests.post(f"{DESIGNER}/preview", json=preview_req)
if check(r, "preview"):
    data = r.json()
    svg = data.get("svg", "")
    fills = data.get("fill_counts", {})
    print(f"  SVG generated: {len(svg)} chars")
    print(f"  Fill counts: {json.dumps(fills, indent=4)}")

    # Save SVG to file
    out_dir = Path("rosette_output")
    out_dir.mkdir(exist_ok=True)
    svg_path = out_dir / "midnight_walnut_burst_preview.svg"
    svg_path.write_text(svg, encoding="utf-8")
    print(f"  Saved: {svg_path}")

# ─────────────────────────────────────────────────────────────────
# Step 3: Manufacturing checks
# ─────────────────────────────────────────────────────────────────
print("\n--- Step 3: Manufacturing Checks ---")

mfg_req = {
    "grid": grid,
    "num_segs": NUM_SEGS,
    "ring_active": [True, True, True, True, True],
}

r = requests.post(f"{DESIGNER}/mfg-check", json=mfg_req)
if check(r, "mfg-check"):
    data = r.json()
    checks = data.get("checks", data.get("issues", []))
    if isinstance(checks, list):
        if not checks:
            print("  No manufacturing issues found!")
        for chk in checks:
            sev = chk.get("severity", "?")
            msg = chk.get("message", chk.get("msg", "?"))
            print(f"  [{sev.upper()}] {msg}")
    else:
        print(f"  Result: {json.dumps(data, indent=2)[:400]}")

# ─────────────────────────────────────────────────────────────────
# Step 4: Bill of Materials
# ─────────────────────────────────────────────────────────────────
print("\n--- Step 4: Bill of Materials ---")

bom_req = {
    "grid": grid,
    "num_segs": NUM_SEGS,
    "ring_active": [True, True, True, True, True],
}

r = requests.post(f"{DESIGNER}/bom", json=bom_req)
if check(r, "bom"):
    data = r.json()
    items = data.get("items", data.get("bom", []))
    total = data.get("total_strips", data.get("total", "?"))
    print(f"  Total strips/items: {total}")
    if isinstance(items, list):
        for item in items:
            tid = item.get("tile_id", item.get("material", "?"))
            count = item.get("count", item.get("qty", "?"))
            print(f"    {tid}: {count}")
    else:
        print(f"  BOM data: {json.dumps(data, indent=2)[:500]}")

# ─────────────────────────────────────────────────────────────────
# Step 5: Export final SVG
# ─────────────────────────────────────────────────────────────────
print("\n--- Step 5: Export Production SVG ---")

export_req = {
    "grid": grid,
    "num_segs": NUM_SEGS,
    "ring_active": [True, True, True, True, True],
    "show_labels": True,
    "annotate_dims": True,
    "title": "Midnight Walnut Burst",
}

r = requests.post(f"{DESIGNER}/export/svg", json=export_req)
if r.status_code == 200:
    content_type = r.headers.get("content-type", "")
    if "svg" in content_type or "xml" in content_type or "text" in content_type:
        svg_export = r.text
    else:
        svg_export = r.content.decode("utf-8", errors="replace")
    export_path = out_dir / "midnight_walnut_burst_export.svg"
    export_path.write_text(svg_export, encoding="utf-8")
    print(f"  Exported SVG: {export_path} ({len(svg_export)} chars)")
else:
    print(f"  FAIL [{r.status_code}]: {r.text[:200]}")

# ─────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  Design Complete: Midnight Walnut Burst")
print("=" * 60)
print(f"  Segments: {NUM_SEGS}")
print(f"  Symmetry: {SYM_MODE}")
print(f"  Total tiles placed: {len(grid)}")
print("""
  Ring Layout:
    0. Soundhole Binding  → Ebony (solid black)
    1. Inner Purfling     → W/B/W stripes
    2. Main Channel       → Walnut + Abalone + MOP burst
    3. Outer Purfling     → B/W/B stripes
    4. Outer Binding      → Walnut
""")
