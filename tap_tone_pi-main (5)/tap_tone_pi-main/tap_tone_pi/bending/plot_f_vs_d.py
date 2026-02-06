#!/usr/bin/env python3
"""
plot_f_vs_d.py — Plot force vs displacement with linear fit overlay.

Migration: Canonical location is now tap_tone_pi.bending.plot_f_vs_d
           (previously modes/bending_rig/plot_f_vs_d.py)

Reads pairs.csv (t_s, force_N, disp_mm) and generates a scatter plot
with the linear fit region highlighted.

Usage:
    python -m tap_tone_pi.bending.plot_f_vs_d \\
        --pairs-csv out/rig/pairs.csv \\
        --out out/rig/f_vs_d.png \\
        --pct-low 10 --pct-high 90 \\
        --title "F–d — Run 20251231" --dpi 150
"""
from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt


def load_pairs(path: str) -> Tuple[List[float], List[float], List[float]]:
    """Load pairs.csv and return (t, F, d) lists."""
    t_list: List[float] = []
    F_list: List[float] = []
    d_list: List[float] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_list.append(float(row["t_s"]))
            F_list.append(float(row["force_N"]))
            d_list.append(float(row["disp_mm"]))

    return t_list, F_list, d_list


def linear_fit(F: List[float], d: List[float]) -> Tuple[float, float]:
    """Compute slope and R² for linear regression."""
    xbar = statistics.mean(d)
    ybar = statistics.mean(F)

    num = sum((x - xbar) * (y - ybar) for x, y in zip(d, F))
    den = sum((x - xbar) ** 2 for x in d) + 1e-12
    slope = num / den

    ss_tot = sum((y - ybar) ** 2 for y in F) + 1e-12
    ss_res = sum((y - (slope * (x - xbar) + ybar)) ** 2 for x, y in zip(d, F))
    r2 = 1.0 - ss_res / ss_tot

    return slope, r2


def percentile_bounds(vals: List[float], lo_pct: float, hi_pct: float) -> Tuple[float, float]:
    """Get values at given percentiles."""
    vs = sorted(vals)
    n = len(vs) - 1
    i_lo = max(0, min(n, round(lo_pct / 100 * n)))
    i_hi = max(0, min(n, round(hi_pct / 100 * n)))
    return vs[i_lo], vs[i_hi]


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot force vs displacement.")
    ap.add_argument("--pairs-csv", required=True, help="Path to pairs.csv")
    ap.add_argument("--out", required=True, help="Output PNG path")
    ap.add_argument(
        "--pct-low", type=float, default=10.0, help="Lower percentile for fit"
    )
    ap.add_argument(
        "--pct-high", type=float, default=90.0, help="Upper percentile for fit"
    )
    ap.add_argument("--title", default="Force vs Displacement", help="Plot title")
    ap.add_argument("--dpi", type=int, default=150, help="Output DPI")
    args = ap.parse_args()

    _, F, d = load_pairs(args.pairs_csv)

    # Get fit bounds
    d_lo, d_hi = percentile_bounds(d, args.pct_low, args.pct_high)

    # Filter to fit range
    mask = [(d_lo <= x <= d_hi) for x in d]
    F_fit = [y for y, m in zip(F, mask) if m]
    d_fit = [x for x, m in zip(d, mask) if m]

    # Compute fit
    slope, r2 = linear_fit(F_fit, d_fit)

    # Compute fit line endpoints
    d_mean = statistics.mean(d_fit)
    F_mean = statistics.mean(F_fit)
    x0, x1 = min(d_fit), max(d_fit)
    y0 = slope * (x0 - d_mean) + F_mean
    y1 = slope * (x1 - d_mean) + F_mean

    # Plot
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    # All points (faded)
    ax.scatter(d, F, s=8, alpha=0.25, c="gray", label="All data")

    # Fit region (highlighted)
    ax.scatter(
        d_fit,
        F_fit,
        s=12,
        alpha=0.8,
        c="steelblue",
        label=f"Fit [{args.pct_low:.0f}–{args.pct_high:.0f}]%",
    )

    # Fit line
    ax.plot(
        [x0, x1],
        [y0, y1],
        lw=2,
        c="crimson",
        label=f"S = {slope:.3f} N/mm, R² = {r2:.4f}",
    )

    ax.set_xlabel("Displacement (mm)")
    ax.set_ylabel("Force (N)")
    ax.set_title(args.title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")

    # Ensure output directory exists
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout()
    plt.savefig(args.out, dpi=args.dpi)
    plt.close()

    print(f"Wrote {args.out}")
    print(f"  Slope: {slope:.4f} N/mm")
    print(f"  R²:    {r2:.4f}")


if __name__ == "__main__":
    main()
