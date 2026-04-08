#!/usr/bin/env python3
"""
archtop_stiffness_map.py

Approximate curvature -> stiffness mapping for archtop plates.

Purpose
-------
Given a measured archtop surface z(x,y) from CSV points (x,y,height),
this script:

1) interpolates the height field z(x,y)
2) computes first and second derivatives
3) estimates local mean/Gaussian/principal curvatures
4) converts curvature into a shell-stiffness proxy
5) writes maps to CSV and optional PNG heatmaps

This is a first-order engineering tool, not a full shell FEM.

Model summary
-------------
Bending stiffness of a thin isotropic plate:
    D_b = E h^3 / (12 (1 - nu^2))

Shell/membrane-style curvature stiffening proxy:
    K_shell(x,y) = alpha * E * h / R_eff(x,y)^2

where R_eff is derived from local principal curvatures:
    k1, k2 = principal curvatures
    R1 = 1/|k1|, R2 = 1/|k2|

We define:
    k_eff^2 = 0.5 * (k1^2 + k2^2)
    R_eff = 1 / sqrt(k_eff^2)

so:
    K_shell = alpha * E * h * k_eff^2

And an "effective stiffness index":
    K_eff = D_b + L_ref^2 * K_shell

where L_ref is a chosen reference span used only to put the shell term
on a roughly comparable scale to the bending term.

Units
-----
Input:
- x, y, height in mm
- E in GPa
- h in mm

Internal:
- meters, pascals

Outputs:
- CSV in SI-friendly values
- PNG heatmaps

Usage
-----
python archtop_stiffness_map.py \
  --in sample_top_points.csv \
  --out-prefix top_shell \
  --E 11.0 \
  --nu 0.35 \
  --thickness 4.0 \
  --alpha 1.0 \
  --res 2.0

Requires:
    pip install numpy matplotlib
"""

import argparse
import csv
import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


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
    """Simple inverse-distance interpolation onto a regular grid."""
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


def derivatives_from_surface(Z, dx_m, dy_m):
    """Return first and second derivatives using finite differences."""
    Zy, Zx = np.gradient(Z, dy_m, dx_m)
    Zyy, Zyx = np.gradient(Zy, dy_m, dx_m)
    Zxy, Zxx = np.gradient(Zx, dy_m, dx_m)
    # Symmetrize mixed second derivative to reduce noise.
    Zxy = 0.5 * (Zxy + Zyx)
    return Zx, Zy, Zxx, Zyy, Zxy


def curvature_maps(Zx, Zy, Zxx, Zyy, Zxy):
    """
    Curvature for Monge patch z = z(x,y).

    Principal curvatures are eigenvalues of:
        S = I^{-1} II

    where for surface graph:
        I = [[E, F], [F, G]]
        II = [[L, M], [M, N]]

    with:
        E = 1 + zx^2
        F = zx zy
        G = 1 + zy^2

        L = zxx / sqrt(1 + zx^2 + zy^2)
        M = zxy / sqrt(1 + zx^2 + zy^2)
        N = zyy / sqrt(1 + zx^2 + zy^2)
    """
    q = np.sqrt(1.0 + Zx**2 + Zy**2)

    E1 = 1.0 + Zx**2
    F1 = Zx * Zy
    G1 = 1.0 + Zy**2

    L2 = Zxx / q
    M2 = Zxy / q
    N2 = Zyy / q

    detI = E1 * G1 - F1**2

    # Mean curvature H and Gaussian curvature K
    H = (E1 * N2 - 2.0 * F1 * M2 + G1 * L2) / (2.0 * detI)
    K = (L2 * N2 - M2**2) / detI

    disc = np.maximum(H**2 - K, 0.0)
    sqrt_disc = np.sqrt(disc)

    k1 = H + sqrt_disc
    k2 = H - sqrt_disc

    return H, K, k1, k2


def stiffness_proxy_maps(k1, k2, E_pa, nu, h_m, alpha=1.0, L_ref_m=0.25):
    """
    Convert curvature to bending + shell-style stiffness proxy.

    D_b has units N*m.
    K_shell has units N/m.
    We scale K_shell by L_ref^2 so the combined metric K_eff
    has the same units as D_b and can be viewed as an 'effective
    stiffness index' for comparison across the plate.

    This is not an exact shell constitutive relation; it is a useful
    design-side proxy for where arching is contributing more stiffness.
    """
    D_b = E_pa * h_m**3 / (12.0 * (1.0 - nu**2))

    k_eff_sq = 0.5 * (k1**2 + k2**2)
    R_eff_m = np.full_like(k_eff_sq, np.inf, dtype=float)
    mask = k_eff_sq > 1e-18
    R_eff_m[mask] = 1.0 / np.sqrt(k_eff_sq[mask])

    K_shell = alpha * E_pa * h_m * k_eff_sq   # N/m
    K_eff = D_b + (L_ref_m**2) * K_shell      # N*m-like combined index

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
                row = {
                    "x_mm": float(X_mm[i, j]),
                    "y_mm": float(Y_mm[i, j]),
                }
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


def _plot_map_to_bytes(X_mm, Y_mm, Z, title, cbar_label, cmap="viridis") -> bytes:
    """Render heatmap to PNG bytes (for API response)."""
    import io
    plt.figure(figsize=(7, 5.5))
    im = plt.pcolormesh(X_mm, Y_mm, Z, shading="auto", cmap=cmap)
    plt.gca().set_aspect("equal", "box")
    plt.xlabel("x (mm)")
    plt.ylabel("y (mm)")
    plt.title(title)
    cb = plt.colorbar(im)
    cb.set_label(cbar_label)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200)
    plt.close()
    buf.seek(0)
    return buf.read()


# =============================================================================
# LIBRARY FUNCTION (called by archtop_router.py)
# =============================================================================


def compute_stiffness_from_points(
    xs_mm: np.ndarray,
    ys_mm: np.ndarray,
    heights_mm: np.ndarray,
    E_gpa: float = 11.0,
    nu: float = 0.35,
    thickness_mm: float = 4.0,
    alpha: float = 1.0,
    Lref_mm: float = 250.0,
    resolution_mm: float = 2.0,
    heatmap_type: str = "K_eff",
) -> dict:
    """Compute curvature-based stiffness proxy from measured surface points.

    Args:
        xs_mm: X coordinates in mm
        ys_mm: Y coordinates in mm
        heights_mm: Height values in mm
        E_gpa: Young's modulus in GPa
        nu: Poisson ratio
        thickness_mm: Plate thickness in mm
        alpha: Shell stiffness scale factor
        Lref_mm: Reference span for combined stiffness index
        resolution_mm: Grid resolution in mm
        heatmap_type: Which map to render ("K_eff", "K_shell", "R_eff", "height")

    Returns:
        dict with grid data and summary statistics
    """
    import base64

    if len(xs_mm) < 4:
        raise ValueError("At least 4 points required for interpolation")

    X_mm, Y_mm, Z_mm = idw_grid(xs_mm, ys_mm, heights_mm, resolution_mm=resolution_mm)

    dx_m = resolution_mm / 1000.0
    dy_m = resolution_mm / 1000.0
    Z_m = Z_mm / 1000.0

    Zx, Zy, Zxx, Zyy, Zxy = derivatives_from_surface(Z_m, dx_m, dy_m)
    H, K, k1, k2 = curvature_maps(Zx, Zy, Zxx, Zyy, Zxy)

    E_pa = E_gpa * 1e9
    h_m = thickness_mm / 1000.0
    L_ref_m = Lref_mm / 1000.0

    proxy = stiffness_proxy_maps(
        k1=k1,
        k2=k2,
        E_pa=E_pa,
        nu=nu,
        h_m=h_m,
        alpha=alpha,
        L_ref_m=L_ref_m,
    )

    # Select heatmap to render
    heatmap_configs = {
        "K_eff": (proxy["K_eff"], "Effective Stiffness Index", "K_eff (N*m proxy)", "viridis"),
        "K_shell": (proxy["K_shell"], "Shell Stiffness Proxy", "K_shell (N/m)", "magma"),
        "R_eff": (proxy["R_eff_m"] * 1000.0, "Effective Radius Map", "R_eff (mm)", "plasma"),
        "height": (Z_mm, "Height Map", "height (mm)", "terrain"),
    }

    if heatmap_type not in heatmap_configs:
        heatmap_type = "K_eff"

    Z_plot, title, label, cmap = heatmap_configs[heatmap_type]
    png_bytes = _plot_map_to_bytes(X_mm, Y_mm, Z_plot, title, label, cmap)
    png_b64 = base64.b64encode(png_bytes).decode("ascii")

    return {
        "X_mm": X_mm,
        "Y_mm": Y_mm,
        "K_eff": proxy["K_eff"],
        "height_mm": Z_mm,
        "png_b64": png_b64,
        "D_b": proxy["D_b"],
        "max_K_shell": float(np.nanmax(proxy["K_shell"])),
        "mean_K_shell": float(np.nanmean(proxy["K_shell"])),
        "max_K_eff": float(np.nanmax(proxy["K_eff"])),
        "mean_K_eff": float(np.nanmean(proxy["K_eff"])),
    }


# =============================================================================
# CLI FUNCTION
# =============================================================================


def main():
    ap = argparse.ArgumentParser(description="Compute curvature -> stiffness proxy maps for archtop plates.")
    ap.add_argument("--in", dest="infile", required=True, help="CSV with x,y,height columns in mm")
    ap.add_argument("--out-prefix", required=True, help="Output prefix")
    ap.add_argument("--E", type=float, required=True, help="Young's modulus in GPa")
    ap.add_argument("--nu", type=float, default=0.35, help="Poisson ratio (default 0.35)")
    ap.add_argument("--thickness", type=float, required=True, help="Plate thickness in mm")
    ap.add_argument("--alpha", type=float, default=1.0, help="Shell stiffness scale factor")
    ap.add_argument("--Lref", type=float, default=250.0, help="Reference span in mm for combined index")
    ap.add_argument("--res", type=float, default=2.0, help="Grid resolution in mm")
    args = ap.parse_args()

    xs_mm, ys_mm, hs_mm = read_csv_points(args.infile)
    X_mm, Y_mm, Z_mm = idw_grid(xs_mm, ys_mm, hs_mm, resolution_mm=args.res)

    dx_m = args.res / 1000.0
    dy_m = args.res / 1000.0
    Z_m = Z_mm / 1000.0

    Zx, Zy, Zxx, Zyy, Zxy = derivatives_from_surface(Z_m, dx_m, dy_m)
    H, K, k1, k2 = curvature_maps(Zx, Zy, Zxx, Zyy, Zxy)

    E_pa = args.E * 1e9
    h_m = args.thickness / 1000.0
    L_ref_m = args.Lref / 1000.0

    proxy = stiffness_proxy_maps(
        k1=k1,
        k2=k2,
        E_pa=E_pa,
        nu=args.nu,
        h_m=h_m,
        alpha=args.alpha,
        L_ref_m=L_ref_m,
    )

    base = Path(args.out_prefix)
    csv_path = Path(f"{base}_stiffness_map.csv")

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

    # Heatmaps
    plot_map(X_mm, Y_mm, Z_mm,
             "Height Map", "height (mm)",
             f"{base}_height.png", cmap="terrain")

    plot_map(X_mm, Y_mm, proxy["R_eff_m"] * 1000.0,
             "Effective Radius Map", "R_eff (mm)",
             f"{base}_effective_radius.png", cmap="plasma")

    plot_map(X_mm, Y_mm, proxy["K_shell"],
             "Shell Stiffness Proxy", "K_shell (N/m)",
             f"{base}_shell_stiffness.png", cmap="magma")

    plot_map(X_mm, Y_mm, proxy["K_eff"],
             "Effective Stiffness Index", "K_eff (N·m proxy)",
             f"{base}_effective_stiffness.png", cmap="viridis")

    summary = {
        "input_csv": args.infile,
        "E_GPa": args.E,
        "nu": args.nu,
        "thickness_mm": args.thickness,
        "alpha": args.alpha,
        "Lref_mm": args.Lref,
        "grid_resolution_mm": args.res,
        "uniform_bending_D_Nm": proxy["D_b"],
        "max_shell_stiffness_N_per_m": float(np.nanmax(proxy["K_shell"])),
        "mean_shell_stiffness_N_per_m": float(np.nanmean(proxy["K_shell"])),
        "max_effective_stiffness_proxy_Nm": float(np.nanmax(proxy["K_eff"])),
        "mean_effective_stiffness_proxy_Nm": float(np.nanmean(proxy["K_eff"])),
    }

    summary_path = Path(f"{base}_summary.json")
    summary_path.write_text(json_dump(summary), encoding="utf-8")

    print("Saved:")
    print(f"  {csv_path}")
    print(f"  {base}_height.png")
    print(f"  {base}_effective_radius.png")
    print(f"  {base}_shell_stiffness.png")
    print(f"  {base}_effective_stiffness.png")
    print(f"  {summary_path}")


def json_dump(d):
    import json
    return json.dumps(d, indent=2)


if __name__ == "__main__":
    main()
