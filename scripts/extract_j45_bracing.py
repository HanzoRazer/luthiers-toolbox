"""
J45 DIMS.dxf -> Layered DXF Extraction
========================================
Reads the original J45 DIMS.dxf (AutoCAD drawing in inches, all on Layer 0)
and produces a clean, layer-organized DXF in mm with separated views:

Views identified in the drawing (all coordinates in inches):
  1. Side profile view (x ~575-596, y ~818-840) — body outline rotated 90deg
  2. Back bracing plan view (x ~646-680, y ~814-835) — 4 back braces (BB-1..BB-4)
  3. Top bracing plan view (x ~684-720, y ~814-836) — 8 top braces (TB-1..TB-8)
  4. Fret layout (x ~584-610, y ~822-826) — 20 frets with positions
  5. Cross-section detail (x ~666-680, y ~828-834) — side wall construction

Output layers:
  BODY_OUTLINE          - Main body perimeter (30-pt with bulge arcs)
  BODY_OUTLINE_INNER    - Inner body outline (inside purfling/binding)
  BACK_BRACING          - Back brace geometry (BB-1 through BB-4)
  TOP_BRACING           - Top brace geometry (TB-1 through TB-8, X-brace)
  SOUNDHOLE             - Soundhole circle
  FRET_POSITIONS        - Fret slot locations
  ANNOTATIONS           - Dimension text and labels
  KERF_LINING           - Kerf lining details
  CROSS_SECTION         - Side wall cross-section
  REFERENCE             - Dimension lines, leaders, misc reference geometry

All geometry converted from inches to mm (x25.4).
"""

import ezdxf
import math
from pathlib import Path

IN_TO_MM = 25.4

# --- Source regions (inch coordinates in the original drawing) ---
# These bounding boxes isolate each "view" in the multi-view DXF

REGIONS = {
    # Side profile / body plan view (body outline rotated - longest span is vertical)
    "side_profile": {"x": (570, 600), "y": (814, 842)},
    # Back bracing plan view
    "back_bracing": {"x": (646, 682), "y": (814, 836)},
    # Top bracing plan view
    "top_bracing": {"x": (683, 722), "y": (813, 837)},
    # Fret layout (along the neck)
    "fret_layout": {"x": (584, 612), "y": (822, 826)},
    # Cross-section detail
    "cross_section": {"x": (665, 681), "y": (827, 835)},
}


def in_region(x, y, region):
    """Check if a point falls within a named region."""
    r = REGIONS[region]
    return r["x"][0] <= x <= r["x"][1] and r["y"][0] <= y <= r["y"][1]


def entity_center(e):
    """Get approximate center of an entity."""
    if e.dxftype() == "LINE":
        return ((e.dxf.start.x + e.dxf.end.x) / 2,
                (e.dxf.start.y + e.dxf.end.y) / 2)
    elif e.dxftype() in ("CIRCLE", "ARC"):
        return (e.dxf.center.x, e.dxf.center.y)
    elif e.dxftype() == "LWPOLYLINE":
        pts = list(e.get_points())
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    elif e.dxftype() == "TEXT":
        return (e.dxf.insert.x, e.dxf.insert.y)
    elif e.dxftype() == "DIMENSION":
        try:
            dp = e.dxf.defpoint
            return (dp.x, dp.y)
        except Exception:
            return (0, 0)
    return (0, 0)


def classify_entity(e, src_msp):
    """Classify an entity into a target layer based on spatial region + type."""
    cx, cy = entity_center(e)
    etype = e.dxftype()

    # --- TEXT classification ---
    if etype == "TEXT":
        txt = e.dxf.text.upper()
        # Bracing labels
        if txt.startswith("BB-"):
            return "BACK_BRACING"
        if txt.startswith("TB-"):
            return "TOP_BRACING"
        if "KERF" in txt or "LINING" in txt:
            return "KERF_LINING"
        if "PURF" in txt:
            return "CROSS_SECTION"
        if "FRET" in txt or "NUT" in txt or "SCALE" in txt:
            return "FRET_POSITIONS"
        if "SECTION" in txt or "TOP" == txt.strip() or "SIDE" == txt.strip() or "BOTTOM" == txt.strip():
            return "CROSS_SECTION"
        # Dimension text with measurements
        if any(c in txt for c in ['"', 'MM', '/']):
            return "ANNOTATIONS"
        if "MAHOG" in txt or "BASSWOOD" in txt:
            return "ANNOTATIONS"

    # --- DIMENSION entities ---
    if etype == "DIMENSION":
        return "REFERENCE"

    # --- SOLID entities (filled shapes in cross-section) ---
    if etype == "SOLID":
        return "CROSS_SECTION"

    # --- IMAGE entities ---
    if etype == "IMAGE":
        return "REFERENCE"

    # --- LWPOLYLINE classification ---
    if etype == "LWPOLYLINE":
        pts = list(e.get_points())
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        mx, my = min(xs), min(ys)

        # Body outlines: 30-pt closed polylines spanning ~15.7-16 x 19.9-20.1 inches
        if len(pts) >= 29 and w > 10 and h > 10:
            # Multiple body outlines exist at different positions:
            # - Side profile view (~575, 818): rotated body
            # - Back bracing view (~646, 814): outer + inner body
            # - Top bracing view (~684, 814): outer + inner body
            if mx < 620:
                return "BODY_OUTLINE"  # Side profile view body
            elif mx < 670:
                # Back view - check if it's the smaller (inner) one
                if w < 15.8:  # Inner body is slightly smaller
                    return "BODY_OUTLINE_INNER"
                return "BODY_OUTLINE"
            else:
                # Top view
                if w < 15.8:
                    return "BODY_OUTLINE_INNER"
                return "BODY_OUTLINE"

        # Soundhole shape in side profile (9-pt closed, ~6x3 in the neck area)
        if len(pts) == 9 and e.closed and 3 < max(w, h) < 7:
            return "SOUNDHOLE"

        # Small polylines in cross-section region
        if in_region(cx, cy, "cross_section"):
            return "CROSS_SECTION"

        # Kerf lining details (small rects near top of body views)
        if h < 1 and w < 1:
            if cy > 827:
                return "KERF_LINING"

    # --- LINE classification by region ---
    if etype == "LINE":
        if in_region(cx, cy, "back_bracing"):
            return "BACK_BRACING"
        if in_region(cx, cy, "top_bracing"):
            return "TOP_BRACING"
        if in_region(cx, cy, "fret_layout"):
            return "FRET_POSITIONS"
        if in_region(cx, cy, "cross_section"):
            return "CROSS_SECTION"
        if in_region(cx, cy, "side_profile"):
            return "BODY_OUTLINE"

    # --- ARC classification by region ---
    if etype == "ARC":
        if in_region(cx, cy, "top_bracing"):
            return "TOP_BRACING"
        if in_region(cx, cy, "back_bracing"):
            return "BACK_BRACING"
        if in_region(cx, cy, "side_profile"):
            return "BODY_OUTLINE"
        if in_region(cx, cy, "cross_section"):
            return "CROSS_SECTION"

    # --- CIRCLE classification ---
    if etype == "CIRCLE":
        r = e.dxf.radius
        # Soundhole: r=2.000 (4" diameter = ~101.6mm)
        if 1.9 < r < 2.1:
            return "SOUNDHOLE"
        # Small circles are reference holes/pins
        if r < 0.2:
            return "REFERENCE"

    return "REFERENCE"


def copy_entity_to_layer(e, src_doc, dst_msp, layer_name, offset_x=0, offset_y=0, scale=IN_TO_MM):
    """Copy an entity to the destination, applying coordinate transform (inches->mm)."""
    etype = e.dxftype()

    if etype == "LINE":
        sx = (e.dxf.start.x + offset_x) * scale
        sy = (e.dxf.start.y + offset_y) * scale
        ex = (e.dxf.end.x + offset_x) * scale
        ey = (e.dxf.end.y + offset_y) * scale
        dst_msp.add_line((sx, sy), (ex, ey), dxfattribs={"layer": layer_name})

    elif etype == "CIRCLE":
        cx = (e.dxf.center.x + offset_x) * scale
        cy = (e.dxf.center.y + offset_y) * scale
        r = e.dxf.radius * scale
        dst_msp.add_circle((cx, cy), r, dxfattribs={"layer": layer_name})

    elif etype == "ARC":
        cx = (e.dxf.center.x + offset_x) * scale
        cy = (e.dxf.center.y + offset_y) * scale
        r = e.dxf.radius * scale
        dst_msp.add_arc(
            (cx, cy), r,
            e.dxf.start_angle, e.dxf.end_angle,
            dxfattribs={"layer": layer_name}
        )

    elif etype == "LWPOLYLINE":
        pts = list(e.get_points(format="xyseb"))
        new_pts = []
        for p in pts:
            x = (p[0] + offset_x) * scale
            y = (p[1] + offset_y) * scale
            # Preserve bulge (index 4), start_width and end_width scale
            sw = p[1] * 0 if len(p) < 3 else p[2] * scale  # start_width
            ew = p[1] * 0 if len(p) < 4 else p[3] * scale  # end_width
            bulge = p[4] if len(p) > 4 else 0.0
            new_pts.append((x, y, sw, ew, bulge))
        poly = dst_msp.add_lwpolyline(
            new_pts, format="xyseb",
            dxfattribs={"layer": layer_name}
        )
        poly.close(e.closed)

    elif etype == "TEXT":
        ix = (e.dxf.insert.x + offset_x) * scale
        iy = (e.dxf.insert.y + offset_y) * scale
        height = e.dxf.height * scale if e.dxf.height else 2.5
        dst_msp.add_text(
            e.dxf.text,
            dxfattribs={
                "layer": layer_name,
                "insert": (ix, iy),
                "height": height,
            }
        )


def main():
    src_path = Path("Guitar Plans/J 45 Plans/J45 DIMS.dxf")
    out_path = Path("Guitar Plans/J 45 Plans/J45_DIMS_Layered.dxf")

    print(f"Reading {src_path}...")
    src_doc = ezdxf.readfile(str(src_path))
    src_msp = src_doc.modelspace()

    # Create output R2000 DXF (LWPOLYLINE requires R2000+)
    dst_doc = ezdxf.new("R2000")
    dst_msp = dst_doc.modelspace()

    # Define layers with colors
    layer_colors = {
        "BODY_OUTLINE": 7,       # White
        "BODY_OUTLINE_INNER": 5, # Blue
        "BACK_BRACING": 1,       # Red
        "TOP_BRACING": 3,        # Green
        "SOUNDHOLE": 6,          # Magenta
        "FRET_POSITIONS": 4,     # Cyan
        "ANNOTATIONS": 8,        # Gray
        "KERF_LINING": 2,        # Yellow
        "CROSS_SECTION": 30,     # Orange
        "REFERENCE": 9,          # Light gray
    }
    for name, color in layer_colors.items():
        dst_doc.layers.add(name, color=color)

    # Classify and copy all entities
    layer_counts = {}
    skipped = 0

    for e in src_msp:
        etype = e.dxftype()
        # Skip IMAGE and DIMENSION entities (not supported in R12 or not geometry)
        if etype in ("IMAGE", "DIMENSION", "SOLID"):
            skipped += 1
            continue

        layer = classify_entity(e, src_msp)
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

        try:
            copy_entity_to_layer(e, src_doc, dst_msp, layer)
        except Exception as ex:
            print(f"  WARN: Failed to copy {etype}: {ex}")
            skipped += 1

    # Save
    dst_doc.saveas(str(out_path))

    print(f"\nOutput: {out_path}")
    print(f"Skipped: {skipped} entities (IMAGE/DIMENSION/SOLID)")
    print(f"\nLayer summary:")
    total = 0
    for layer in sorted(layer_counts.keys()):
        c = layer_counts[layer]
        total += c
        color = layer_colors.get(layer, 7)
        print(f"  {layer:25s}  {c:4d} entities  (color {color})")
    print(f"  {'TOTAL':25s}  {total:4d}")

    # Also produce a bracing-only DXF for CAM use
    brace_path = Path("Guitar Plans/J 45 Plans/J45_Bracing_Only.dxf")
    brace_doc = ezdxf.new("R2000")
    brace_msp = brace_doc.modelspace()

    brace_layers = {
        "BODY_OUTLINE": 7,
        "BACK_BRACING": 1,
        "TOP_BRACING": 3,
        "SOUNDHOLE": 6,
    }
    for name, color in brace_layers.items():
        brace_doc.layers.add(name, color=color)

    brace_count = 0
    for e in src_msp:
        etype = e.dxftype()
        if etype in ("IMAGE", "DIMENSION", "SOLID", "TEXT"):
            continue
        layer = classify_entity(e, src_msp)
        if layer in brace_layers:
            try:
                copy_entity_to_layer(e, src_doc, brace_msp, layer)
                brace_count += 1
            except Exception:
                pass

    brace_doc.saveas(str(brace_path))
    print(f"\nBracing-only DXF: {brace_path} ({brace_count} entities)")


if __name__ == "__main__":
    main()
