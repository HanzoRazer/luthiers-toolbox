#!/usr/bin/env python3
"""
archtop_surface_tools.py

Combined archtop utility:
1) contour extraction from measured (x,y,height) CSV
2) curvature/effective-radius/shell-stiffness maps from the same surface

This merges the earlier contour-ring workflow with the new curvature->stiffness
workflow so one measured surface can generate both manufacturing contours and
engineering maps.

Requires:
    pip install numpy matplotlib ezdxf

Usage:
    python archtop_surface_tools.py csv \
      --in sample_top_points.csv \
      --levels 0,1,2,3 \
      --out-prefix top_eval \
      --res 2.0 \
      --E 11.0 \
      --nu 0.35 \
      --thickness 4.0 \
      --alpha 1.0 \
      --Lref 250

Outputs:
    *_Contours.dxf
    *_Contours.svg
    *_Contours.png
    *_stiffness_map.csv
    *_height.png
    *_effective_radius.png
    *_shell_stiffness.png
    *_effective_stiffness.png
    *_summary.json
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import ezdxf


# ---------------------------
# CSV / interpolation helpers
# ---------------------------

def read_csv_points(csv_path):
    xs, ys, hs = [], [], []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise ValueError("CSV has no header row.")
        cols = {c.lower(): c for c in r.fieldnames}

        def pick(prefix):
            for k, original in cols.items():
                if k.startswith(prefix):
                    return original
            raise ValueError(f"CSV missing column like '{prefix}'")

        cx = pick("x")
        cy = pick("y")
        ch = pick("height")

        for row in r:
            xs.append(float(row[cx]))
            ys.append(float(row[cy]))
            hs.append(float(row[ch]))

    return np.array(xs, dtype=float), np.array(ys, dtype=float), np.array(hs, dtype=float)


def idw_grid(xs, ys, hs, resolution_mm=2.0):
    xi = np.arange(xs.min(), xs.max() + resolution_mm, resolution_mm)
    yi = np.arange(ys.min(), ys.max() + resolution_mm, resolution_mm)
    XI, YI = np.meshgrid(xi, yi)
    ZI = np.zeros_like(XI, dtype=float)

    power = 2.0
    eps = 1e-12
    for i in range(XI.shape[0]):
        for j in range(XI.shape[1]):
            dx = xs - XI[i, j]
            dy = ys - YI[i, j]
            d2 = dx * dx + dy * dy + eps
            w = 1.0 / (d2 ** (power / 2.0))
            ZI[i, j] = np.sum(w * hs) / np.sum(w)
    return XI, YI, ZI


# ---------------------------
# Contour export helpers
# ---------------------------

def ensure_closed(arr):
    if len(arr) < 3:
        return arr
    if not (abs(arr[0, 0] - arr[-1, 0]) < 1e-9 and abs(arr[0, 1] - arr[-1, 1]) < 1e-9):
        arr = np.vstack([arr, arr[0]])
    return arr


def save_svg_polylines(paths, svg_path):
    minx = min(np.min(p[:, 0]) for p in paths)
    maxx = max(np.max(p[:, 0]) for p in paths)
    miny = min(np.min(p[:, 1]) for p in paths)
    maxy = max(np.max(p[:, 1]) for p in paths)
    pad = 10
    vw = (maxx - minx) + 2 * pad
    vh = (maxy - miny) + 2 * pad

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}">\n')
        f.write(f'<g transform="translate({pad - minx},{pad + maxy}) scale(1,-1)">\n')
        for p in paths:
            d = "M " + " L ".join([f"{x:.3f},{y:.3f}" for x, y in p]) + " Z"
            f.write(f'  <path d="{d}" fill="none" stroke="black" stroke-width="0.3"/>\n')
        f.write("</g>\n</svg>\n")


def export_contours(X_mm, Y_mm, Z_mm, levels, out_prefix):
    cs = plt.contour(X_mm, Y_mm, Z_mm, levels=levels)
    paths = []
    for collection in cs.collections:
        for seg in collection.get_paths():
            v = seg.vertices
            if v.shape[0] >= 3:
                paths.append(ensure_closed(v.copy()))
    plt.close()

    if not paths:
        raise RuntimeError("No contour paths found; adjust --levels or --res.")

    dxf_path = f"{out_prefix}_Contours.dxf"
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for p in paths:
        msp.add_lwpolyline(
            [(float(x), float(y)) for x, y in p[:-1]],
            format="xy",
            dxfattribs={"closed": True, "layer": "Contours"},
        )
    doc.header["$INSUNITS"] = 4
    doc.saveas(dxf_path)

    svg_path = f"{out_prefix}_Contours.svg"
    png_path = f"{out_prefix}_Contours.png"
    save_svg_polylines(paths, svg_path)

    plt.figure()
    for p in paths:
        plt.plot(p[:, 0], p[:, 1])
    plt.gca().set_aspect("equal", "box")
    plt.title("Archtop Contours")
    plt.tight_layout()
    plt.savefig(png_path, dpi=220)
    plt.close()

    return {
        "count": len(paths),
        "dxf": dxf_path,
        "svg": svg_path,
        "png": png_path,
    }


# ---------------------------
# Curvature / stiffness helpers
# ---------------------------

def derivatives_from_surface(Z, dx_m, dy_m):
    Zy, Zx = np.gradient(Z, dy_m, dx_m)
    Zyy, Zyx = np.gradient(Zy, dy_m, dx_m)
    Zxy, Zxx = np.gradient(Zx, dy_m, dx_m)
    Zxy = 0.5 * (Zxy + Zyx)
    return Zx, Zy, Zxx, Zyy, Zxy


def curvature_maps(Zx, Zy, Zxx, Zyy, Zxy):
    q = np.sqrt(1.0 + Zx**2 + Zy**2)

    E1 = 1.0 + Zx**2
    F1 = Zx * Zy
    G1 = 1.0 + Zy**2

    L2 = Zxx / q
    M2 = Zxy / q
    N2 = Zyy / q

    detI = E1 * G1 - F1**2
    H = (E1 * N2 - 2.0 * F1 * M2 + G1 * L2) / (2.0 * detI)
    K = (L2 * N2 - M2**2) / detI

    disc = np.maximum(H**2 - K, 0.0)
    sqrt_disc = np.sqrt(disc)
    k1 = H + sqrt_disc
    k2 = H - sqrt_disc

    return H, K, k1, k2


def stiffness_proxy_maps(k1, k2, E_pa, nu, h_m, alpha=1.0, L_ref_m=0.25):
    D_b = E_pa * h_m**3 / (12.0 * (1.0 - nu**2))
    k_eff_sq = 0.5 * (k1**2 + k2**2)

    R_eff_m = np.full_like(k_eff_sq, np.inf, dtype=float)
    mask = k_eff_sq > 1e-18
    R_eff_m[mask] = 1.0 / np.sqrt(k_eff_sq[mask])

    K_shell = alpha * E_pa * h_m * k_eff_sq
    K_eff = D_b + (L_ref_m**2) * K_shell

    return {
        "D_b": D_b,
        "k_eff_sq": k_eff_sq,
        "R_eff_m": R_eff_m,
        "K_shell": K_shell,
        "K_eff": K_eff,
    }


def save_grid_csv(path, X_mm, Y_mm, maps):
    fieldnames = ["x_mm", "y_mm"] + list(maps.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        ny, nx = X_mm.shape
        for i in range(ny):
            for j in range(nx):
                row = {"x_mm": float(X_mm[i, j]), "y_mm": float(Y_mm[i, j])}
                for key, arr in maps.items():
                    row[key] = float(arr[i, j])
                w.writerow(row)


def plot_map(X_mm, Y_mm, Z, title, cbar_label, out_path, cmap="viridis"):
    plt.figure(figsize=(7, 5.5))
    im = plt.pcolormesh(X_mm, Y_mm, Z, shading="auto", cmap=cmap)
    plt.gca().set_aspect("equal", "box")
    plt.xlabel("x (mm)")
    plt.ylabel("y (mm)")
    plt.title(title)
    cb = plt.colorbar(im)
    cb.set_label(cbar_label)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def export_stiffness_maps(X_mm, Y_mm, Z_mm, E_gpa, nu, thickness_mm, alpha, Lref_mm, out_prefix):
    dx_m = (X_mm[0, 1] - X_mm[0, 0]) / 1000.0 if X_mm.shape[1] > 1 else 0.002
    dy_m = (Y_mm[1, 0] - Y_mm[0, 0]) / 1000.0 if Y_mm.shape[0] > 1 else 0.002
    Z_m = Z_mm / 1000.0

    Zx, Zy, Zxx, Zyy, Zxy = derivatives_from_surface(Z_m, dx_m, dy_m)
    H, K, k1, k2 = curvature_maps(Zx, Zy, Zxx, Zyy, Zxy)

    E_pa = E_gpa * 1e9
    h_m = thickness_mm / 1000.0
    L_ref_m = Lref_mm / 1000.0

    proxy = stiffness_proxy_maps(k1, k2, E_pa, nu, h_m, alpha=alpha, L_ref_m=L_ref_m)

    csv_path = f"{out_prefix}_stiffness_map.csv"
    save_maps = {
        "height_mm": Z_mm,
        "mean_curvature_1_per_m": H,
        "gaussian_curvature_1_per_m2": K,
        "k1_1_per_m": k1,
        "k2_1_per_m": k2,
        "R_eff_mm": proxy["R_eff_m"] * 1000.0,
        "k_eff_sq_1_per_m2": proxy["k_eff_sq"],
        "K_shell_N_per_m": proxy["K_shell"],
        "K_eff_Nm": proxy["K_eff"],
    }
    save_grid_csv(csv_path, X_mm, Y_mm, save_maps)

    height_png = f"{out_prefix}_height.png"
    radius_png = f"{out_prefix}_effective_radius.png"
    shell_png = f"{out_prefix}_shell_stiffness.png"
    keff_png = f"{out_prefix}_effective_stiffness.png"

    plot_map(X_mm, Y_mm, Z_mm, "Height Map", "height (mm)", height_png, cmap="terrain")
    plot_map(X_mm, Y_mm, proxy["R_eff_m"] * 1000.0, "Effective Radius Map", "R_eff (mm)", radius_png, cmap="plasma")
    plot_map(X_mm, Y_mm, proxy["K_shell"], "Shell Stiffness Proxy", "K_shell (N/m)", shell_png, cmap="magma")
    plot_map(X_mm, Y_mm, proxy["K_eff"], "Effective Stiffness Index", "K_eff (N·m proxy)", keff_png, cmap="viridis")

    summary = {
        "E_GPa": E_gpa,
        "nu": nu,
        "thickness_mm": thickness_mm,
        "alpha": alpha,
        "Lref_mm": Lref_mm,
        "uniform_bending_D_Nm": proxy["D_b"],
        "max_shell_stiffness_N_per_m": float(np.nanmax(proxy["K_shell"])),
        "mean_shell_stiffness_N_per_m": float(np.nanmean(proxy["K_shell"])),
        "max_effective_stiffness_proxy_Nm": float(np.nanmax(proxy["K_eff"])),
        "mean_effective_stiffness_proxy_Nm": float(np.nanmean(proxy["K_eff"])),
    }
    summary_json = f"{out_prefix}_summary.json"
    Path(summary_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return {
        "csv": csv_path,
        "height_png": height_png,
        "radius_png": radius_png,
        "shell_png": shell_png,
        "keff_png": keff_png,
        "summary_json": summary_json,
    }


# ---------------------------
# Main
# ---------------------------

def main():
    p = argparse.ArgumentParser(description="Generate archtop contour rings and stiffness maps from measured CSV.")
    sub = p.add_subparsers(dest="mode", required=True)

    pcsv = sub.add_parser("csv", help="Generate contours and stiffness maps from measured CSV.")
    pcsv.add_argument("--in", dest="infile", required=True, help="CSV with columns x,y,height (mm)")
    pcsv.add_argument("--levels", required=True, help="Comma-separated contour heights (mm), e.g. 0,1,2,3")
    pcsv.add_argument("--res", type=float, default=2.0, help="Grid resolution (mm)")
    pcsv.add_argument("--out-prefix", required=True, help="Output prefix")
    pcsv.add_argument("--E", type=float, required=True, help="Young's modulus in GPa")
    pcsv.add_argument("--nu", type=float, default=0.35, help="Poisson ratio")
    pcsv.add_argument("--thickness", type=float, required=True, help="Plate thickness in mm")
    pcsv.add_argument("--alpha", type=float, default=1.0, help="Shell stiffness scale factor")
    pcsv.add_argument("--Lref", type=float, default=250.0, help="Reference span in mm for combined index")
    args = p.parse_args()

    xs, ys, hs = read_csv_points(args.infile)
    X_mm, Y_mm, Z_mm = idw_grid(xs, ys, hs, resolution_mm=args.res)
    levels = [float(v) for v in args.levels.split(",")]

    contour_outputs = export_contours(X_mm, Y_mm, Z_mm, levels, args.out_prefix)
    stiffness_outputs = export_stiffness_maps(
        X_mm, Y_mm, Z_mm,
        E_gpa=args.E,
        nu=args.nu,
        thickness_mm=args.thickness,
        alpha=args.alpha,
        Lref_mm=args.Lref,
        out_prefix=args.out_prefix,
    )

    print("Saved contour artifacts:")
    for k, v in contour_outputs.items():
        if k != "count":
            print(f"  {v}")
    print(f"  contour count: {contour_outputs['count']}")

    print("Saved stiffness artifacts:")
    for _, v in stiffness_outputs.items():
        print(f"  {v}")


if __name__ == "__main__":
    main()
