#!/usr/bin/env python3
"""
Force vs Displacement plot with linear fit overlay.
Measurement visualization only — no interpretation.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import List, Tuple

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def linear_fit(forces: np.ndarray, displacements: np.ndarray) -> Tuple[float, float, float]:
    """Returns (slope, intercept, r_squared)."""
    if len(forces) < 2:
        return 0.0, 0.0, 0.0
    coeffs = np.polyfit(displacements, forces, 1)
    slope, intercept = float(coeffs[0]), float(coeffs[1])
    # R² calculation
    fitted = slope * displacements + intercept
    ss_res = np.sum((forces - fitted) ** 2)
    ss_tot = np.sum((forces - np.mean(forces)) ** 2)
    r_sq = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return slope, intercept, float(r_sq)


def plot_f_vs_d(
    forces: List[float],
    displacements: List[float],
    out_png: str,
    *,
    title: str = "Force vs Displacement",
    units_force: str = "N",
    units_disp: str = "mm",
) -> dict:
    """
    Generate F-vs-d scatter + linear fit overlay.
    Returns fit metadata dict (slope, intercept, r_squared).
    """
    if not HAS_MPL:
        raise ImportError("matplotlib required for plotting: pip install matplotlib")

    f_arr = np.array(forces, dtype=np.float64)
    d_arr = np.array(displacements, dtype=np.float64)

    slope, intercept, r_sq = linear_fit(f_arr, d_arr)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(d_arr, f_arr, marker="o", s=40, label="Data", zorder=3)

    # Fit line
    if len(d_arr) >= 2:
        d_fit = np.linspace(d_arr.min(), d_arr.max(), 50)
        f_fit = slope * d_fit + intercept
        ax.plot(d_fit, f_fit, "r--", linewidth=1.5,
                label=f"Fit: slope={slope:.3f} {units_force}/{units_disp}")

    ax.set_xlabel(f"Displacement ({units_disp})")
    ax.set_ylabel(f"Force ({units_force})")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)

    pathlib.Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)

    return {
        "artifact_type": "f_vs_d_plot",
        "plot_path": out_png,
        "fit": {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_sq,
            "units_slope": f"{units_force}/{units_disp}",
        },
        "n_points": len(forces),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot Force vs Displacement with fit")
    ap.add_argument("--forces", type=float, nargs="+", help="Force values")
    ap.add_argument("--displacements", type=float, nargs="+", help="Displacement values")
    ap.add_argument("--pair", action="append", metavar="F,D",
                    help="Force,Displacement pair (repeatable)")
    ap.add_argument("--json-in", type=str,
                    help="JSON file with 'forces' and 'displacements' arrays")
    ap.add_argument("--out", type=str, default="f_vs_d.png", help="Output PNG path")
    ap.add_argument("--meta-out", type=str, help="Optional JSON output for fit metadata")
    ap.add_argument("--title", type=str, default="Force vs Displacement")
    ap.add_argument("--units-force", type=str, default="N")
    ap.add_argument("--units-disp", type=str, default="mm")
    args = ap.parse_args()

    forces: List[float] = []
    displacements: List[float] = []

    # Load from --json-in
    if args.json_in:
        data = json.loads(pathlib.Path(args.json_in).read_text())
        forces = list(data.get("forces", []))
        displacements = list(data.get("displacements", []))

    # Load from --forces / --displacements
    if args.forces and args.displacements:
        forces = list(args.forces)
        displacements = list(args.displacements)

    # Load from --pair F,D
    if args.pair:
        for p in args.pair:
            f, d = p.split(",")
            forces.append(float(f))
            displacements.append(float(d))

    if len(forces) != len(displacements) or len(forces) == 0:
        raise ValueError("Must provide equal-length forces and displacements (at least 1 point)")

    meta = plot_f_vs_d(
        forces, displacements, args.out,
        title=args.title,
        units_force=args.units_force,
        units_disp=args.units_disp,
    )

    print(f"Wrote {args.out}")
    print(f"  slope: {meta['fit']['slope']:.4f} {meta['fit']['units_slope']}")
    print(f"  R²: {meta['fit']['r_squared']:.4f}")

    if args.meta_out:
        pathlib.Path(args.meta_out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.meta_out).write_text(json.dumps(meta, indent=2))
        print(f"Wrote {args.meta_out}")


if __name__ == "__main__":
    main()
