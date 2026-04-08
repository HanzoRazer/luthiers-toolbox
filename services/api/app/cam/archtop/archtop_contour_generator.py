#!/usr/bin/env python3
"""
Archtop Contour Generator
- Mode A: CSV (x,y,height) -> contour rings (DXF/SVG/PNG)
- Mode B: Outline DXF + scale factors -> scaled rings (Mottola-style)
Requires: numpy, ezdxf, shapely, matplotlib
"""
import argparse, os, sys, math
import numpy as np
import ezdxf
from shapely.geometry import Polygon, LineString, LinearRing
import matplotlib.pyplot as plt

def read_csv_points(csv_path):
    import csv
    xs, ys, hs = [], [], []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        cols = {c.lower(): c for c in r.fieldnames}
        def col(name):
            for k in cols:
                if k.startswith(name): return cols[k]
            raise ValueError(f"CSV missing column like '{name}'")
        cx, cy, ch = col("x"), col("y"), col("height")
        for row in r:
            xs.append(float(row[cx])); ys.append(float(row[cy])); hs.append(float(row[ch]))
    return np.array(xs), np.array(ys), np.array(hs)

def grid_and_interpolate(xs, ys, hs, resolution=1.5):
    xi = np.arange(xs.min(), xs.max()+resolution, resolution)
    yi = np.arange(ys.min(), ys.max()+resolution, resolution)
    XI, YI = np.meshgrid(xi, yi)
    ZI = np.zeros_like(XI, dtype=float)
    power = 2.0; eps = 1e-9
    for i in range(XI.shape[0]):
        for j in range(XI.shape[1]):
            dx = xs - XI[i, j]; dy = ys - YI[i, j]
            d2 = dx*dx + dy*dy + eps
            w = 1.0 / (d2 ** (power/2))
            ZI[i, j] = np.sum(w * hs) / np.sum(w)
    return XI, YI, ZI

def save_svg_polylines(paths, svg_path):
    minx = min(np.min(p[:,0]) for p in paths); maxx = max(np.max(p[:,0]) for p in paths)
    miny = min(np.min(p[:,1]) for p in paths); maxy = max(np.max(p[:,1]) for p in paths)
    pad = 10; vw = (maxx-minx)+2*pad; vh = (maxy-miny)+2*pad
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}">\n')
        f.write('<g transform="translate({},{}) scale(1,-1)">\n'.format(pad - minx, pad + maxy))
        for p in paths:
            d = "M " + " L ".join([f"{x:.3f},{y:.3f}" for x,y in p]) + " Z"
            f.write(f'  <path d="{d}" fill="none" stroke="black" stroke-width="0.3"/>\n')
        f.write('</g>\n</svg>\n')

def ensure_closed(arr):
    if len(arr) < 3: return arr
    if not (abs(arr[0,0] - arr[-1,0]) < 1e-9 and abs(arr[0,1] - arr[-1,1]) < 1e-9):
        arr = np.vstack([arr, arr[0]])
    return arr


# =============================================================================
# LIBRARY FUNCTION (called by archtop_router.py)
# =============================================================================


def generate_contours_from_points(
    xs: np.ndarray,
    ys: np.ndarray,
    heights: np.ndarray,
    levels: list,
    resolution: float = 2.0,
) -> dict:
    """Generate contour rings from measured surface points.

    Args:
        xs: X coordinates in mm (1D array)
        ys: Y coordinates in mm (1D array)
        heights: Height values in mm (1D array)
        levels: List of contour heights in mm
        resolution: Grid resolution in mm

    Returns:
        dict with:
            paths: List of numpy arrays, each shape (N, 2) representing a closed contour
            levels_found: List of levels that produced at least one contour
    """
    if len(xs) < 4:
        raise ValueError("At least 4 points required for interpolation")

    XI, YI, ZI = grid_and_interpolate(xs, ys, heights, resolution=resolution)

    cs = plt.contour(XI, YI, ZI, levels=levels)
    paths = []
    levels_found = set()

    # Use allsegs for matplotlib >= 3.8 compatibility (collections deprecated)
    for level_idx, level_segs in enumerate(cs.allsegs):
        for seg in level_segs:
            if len(seg) >= 3:
                paths.append(ensure_closed(np.array(seg)))
                if level_idx < len(levels):
                    levels_found.add(levels[level_idx])

    plt.close()

    return {
        "paths": paths,
        "levels_found": sorted(levels_found),
    }


# =============================================================================
# CLI FUNCTIONS
# =============================================================================


def mode_csv(args):
    xs, ys, hs = read_csv_points(args.infile)
    XI, YI, ZI = grid_and_interpolate(xs, ys, hs, resolution=args.res)
    levels = [float(v) for v in args.levels.split(",")]
    cs = plt.contour(XI, YI, ZI, levels=levels)
    paths = []
    # Use allsegs for matplotlib >= 3.8 compatibility
    for level_segs in cs.allsegs:
        for seg in level_segs:
            if len(seg) >= 3:
                paths.append(ensure_closed(np.array(seg)))
    plt.close()
    if not paths:
        print("No contour paths found at given levels; try adjusting --levels or --res."); sys.exit(2)
    dxf_path = f"{args.out_prefix}_Contours.dxf"
    doc = ezdxf.new("R2010"); msp = doc.modelspace()
    for p in paths:
        msp.add_lwpolyline([(float(x), float(y)) for x, y in p[:-1]], format="xy",
                           dxfattribs={"closed": True, "layer": "Contours"})
    doc.header["$INSUNITS"] = 4; doc.saveas(dxf_path)
    svg_path = f"{args.out_prefix}_Contours.svg"; png_path = f"{args.out_prefix}_Contours.png"
    save_svg_polylines(paths, svg_path)
    plt.figure(); 
    for p in paths: plt.plot(p[:,0], p[:,1])
    plt.gca().set_aspect("equal", "box"); plt.title("Archtop Contours"); plt.savefig(png_path, dpi=200); plt.close()
    print(f"Saved {len(paths)} contour rings → {dxf_path}, {svg_path}, {png_path}")

def read_single_outline(dxf_path):
    doc = ezdxf.readfile(dxf_path); msp = doc.modelspace()
    loops = []
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and bool(e.closed):
            pts = [(p[0], p[1]) for p in e.get_points("xy")]; loops.append(pts)
        elif e.dxftype() == "POLYLINE" and e.is_closed:
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]; loops.append(pts)
    if not loops: raise ValueError("No closed (LW)POLYLINE found in outline DXF.")
    from shapely.geometry import Polygon as ShPoly, LinearRing as ShRing
    areas = [abs(ShPoly(ShRing(pts)).area) for pts in loops]
    idx = int(np.argmax(areas))
    return np.array(loops[idx], dtype=float)

def mode_outline(args):
    outline = read_single_outline(args.infile)
    ox, oy = [float(v) for v in args.origin.split(",")]
    scales = [float(s) for s in args.scales.split(",")]
    scaled = []
    outline0 = outline.copy(); outline0[:,0] -= ox; outline0[:,1] -= oy
    for s in scales:
        ring = outline0.copy(); ring[:,0] *= s; ring[:,1] *= s; ring[:,0] += ox; ring[:,1] += oy
        scaled.append(ensure_closed(ring))
    dxf_path = f"{args.out_prefix}_ScaledRings.dxf"
    doc = ezdxf.new("R2010"); msp = doc.modelspace()
    for i, p in enumerate(scaled, start=1):
        msp.add_lwpolyline([(float(x), float(y)) for x,y in p[:-1]], format="xy",
                           dxfattribs={"closed": True, "layer": f"Contour_{i:02d}"})
    doc.header["$INSUNITS"] = 4; doc.saveas(dxf_path)
    svg_path = f"{args.out_prefix}_ScaledRings.svg"; png_path = f"{args.out_prefix}_ScaledRings.png"
    save_svg_polylines(scaled, svg_path)
    plt.figure(); 
    for p in scaled: plt.plot(p[:,0], p[:,1])
    plt.gca().set_aspect("equal", "box"); plt.title("Scaled Outline Rings"); plt.savefig(png_path, dpi=200); plt.close()
    print(f"Saved {len(scaled)} scaled rings → {dxf_path}, {svg_path}, {png_path}")

def main():
    p = argparse.ArgumentParser(description="Generate archtop contour rings from CSV or outline DXF.")
    sub = p.add_subparsers(dest="mode", required=True)
    pcsv = sub.add_parser("csv", help="Generate contours from measured CSV (x,y,height).")
    pcsv.add_argument("--in", dest="infile", required=True, help="CSV with columns x,y,height (mm)")
    pcsv.add_argument("--levels", required=True, help="Comma-separated contour heights (mm), e.g. 0,2,4,6")
    pcsv.add_argument("--res", type=float, default=1.5, help="Grid resolution (mm)")
    pcsv.add_argument("--out-prefix", required=True, help="Output prefix")
    pcsv.set_defaults(func=mode_csv)
    pout = sub.add_parser("outline", help="Generate scaled rings from a closed outline DXF (Mottola-style).")
    pout.add_argument("--in", dest="infile", required=True, help="DXF with ONE primary closed outline")
    pout.add_argument("--origin", required=True, help="Apex/scale origin 'x,y' in mm (e.g., 0,0)")
    pout.add_argument("--scales", required=True, help="Comma-separated scale factors (e.g., 0.90,0.78,0.66,0.54,0.37)")
    pout.add_argument("--out-prefix", required=True, help="Output prefix")
    pout.set_defaults(func=mode_outline)
    args = p.parse_args(); args.func(args)

if __name__ == "__main__":
    main()
