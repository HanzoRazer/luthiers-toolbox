#!/usr/bin/env python3
"""
merge_and_moe.py — Merge load/displacement streams → synchronized pairs → derived MOE.

Inputs:
    - load_series.json:  {"unit": "N"|"lbf", "data": [[t, force], ...]}
    - displacement_series.json: {"unit": "mm"|"in", "data": [[t, disp], ...]}

Outputs:
    - pairs.csv:           t_s,force_N,disp_mm (synchronized, resampled)
    - pairs_sidecar.json:  provenance + units + sample rate
    - bending_moe.json:    derived MOE with fit statistics

Usage:
    python modes/bending_rig/merge_and_moe.py \
        --load load_series.json --disp displacement_series.json \
        --out-dir ./out/rig \
        --method 3point --span 400 --width 20 --thickness 3.0 \
        --rate 50 --fit-pct-low 10 --fit-pct-high 90
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _sha256(p: Path) -> str:
    """Compute SHA-256 hash of file."""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_series(path: str) -> Tuple[Optional[str], List[Tuple[float, float]]]:
    """
    Load a time-series JSON file.

    Expected format: {"unit": "N"|"lbf"|"mm"|"in", "data": [[t, value], ...]}
    """
    with open(path, "r", encoding="utf-8") as f:
        js = json.load(f)
    unit = js.get("unit")
    data = [(float(t), float(v)) for t, v in js["data"]]
    return unit, data


def _lin_interp(samples: List[Tuple[float, float]], t: float) -> float:
    """Linear interpolation at time t."""
    if t <= samples[0][0]:
        return samples[0][1]
    if t >= samples[-1][0]:
        return samples[-1][1]

    # Binary search for bracketing samples
    lo, hi = 0, len(samples) - 1
    while lo + 1 < hi:
        m = (lo + hi) // 2
        if samples[m][0] <= t:
            lo = m
        else:
            hi = m

    t0, y0 = samples[lo]
    t1, y1 = samples[hi]
    alpha = (t - t0) / (t1 - t0 + 1e-12)
    return y0 + alpha * (y1 - y0)


def _resample(
    load: List[Tuple[float, float]],
    disp: List[Tuple[float, float]],
    rate_hz: float,
    t0: float,
    t1: float,
) -> List[Tuple[float, float, float]]:
    """Resample load and displacement to uniform time grid."""
    dt = 1.0 / max(rate_hz, 1e-6)
    out: List[Tuple[float, float, float]] = []
    t = t0
    while t <= t1 + 1e-12:
        f = _lin_interp(load, t)
        d = _lin_interp(disp, t)
        out.append((t, f, d))
        t += dt
    return out


def _linear_fit(F: List[float], d: List[float]) -> Tuple[float, float]:
    """
    Compute linear regression slope and R² for F vs d.

    Returns:
        (slope in N/mm, r-squared)
    """
    xbar = statistics.mean(d)
    ybar = statistics.mean(F)

    num = sum((x - xbar) * (y - ybar) for x, y in zip(d, F))
    den = sum((x - xbar) ** 2 for x in d) + 1e-12
    slope = num / den

    ss_tot = sum((y - ybar) ** 2 for y in F) + 1e-12
    ss_res = sum((y - (slope * (x - xbar) + ybar)) ** 2 for x, y in zip(d, F))
    r2 = 1.0 - ss_res / ss_tot

    return slope, r2


def _calculate_moe(
    method: str,
    slope_N_per_mm: float,
    span_mm: float,
    width_mm: float,
    thickness_mm: float,
    inner_span_mm: Optional[float] = None,
) -> float:
    """
    Calculate MOE (Pa) from force-displacement slope.

    Args:
        method: "3point" or "4point"
        slope_N_per_mm: dF/dd from linear fit
        span_mm: support span
        width_mm: specimen width
        thickness_mm: specimen thickness
        inner_span_mm: inner load span for 4-point (optional)

    Returns:
        MOE in Pascals
    """
    # Convert to meters
    L = span_mm / 1000.0
    b = width_mm / 1000.0
    h = thickness_mm / 1000.0

    # Second moment of area (m^4)
    I = b * h**3 / 12.0

    # Slope in N/m
    S = slope_N_per_mm * 1000.0

    if method == "3point":
        # E = S * L³ / (48 * I)
        return S * L**3 / (48.0 * I)
    else:
        # 4-point: E = S * a * (3L² - 4a²) / (24 * I)
        a = (inner_span_mm / 1000.0) if inner_span_mm else L / 3.0
        return S * a * (3 * L * L - 4 * a * a) / (24.0 * I)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Merge load/disp streams and compute bending MOE."
    )
    ap.add_argument("--load", required=True, help="Path to load_series.json")
    ap.add_argument("--disp", required=True, help="Path to displacement_series.json")
    ap.add_argument("--out-dir", required=True, help="Output directory")
    ap.add_argument("--rate", type=float, default=50.0, help="Resample rate (Hz)")
    ap.add_argument(
        "--method",
        choices=["3point", "4point"],
        default="3point",
        help="Bending test method",
    )
    ap.add_argument("--span", type=float, required=True, help="Support span (mm)")
    ap.add_argument("--width", type=float, required=True, help="Specimen width (mm)")
    ap.add_argument(
        "--thickness", type=float, required=True, help="Specimen thickness (mm)"
    )
    ap.add_argument(
        "--inner-span",
        type=float,
        default=None,
        help="Inner load span for 4-point (mm)",
    )
    ap.add_argument(
        "--fit-pct-low",
        type=float,
        default=10.0,
        help="Lower percentile for fit range",
    )
    ap.add_argument(
        "--fit-pct-high",
        type=float,
        default=90.0,
        help="Upper percentile for fit range",
    )
    args = ap.parse_args()

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Load input series
    unit_F, load = _load_series(args.load)
    unit_D, disp = _load_series(args.disp)

    # Unit conversion to SI (N, mm)
    if unit_F == "lbf":
        load = [(t, v * 4.4482216153) for t, v in load]
    if unit_D == "in":
        disp = [(t, v * 25.4) for t, v in disp]

    # Sort by time
    load = sorted(load, key=lambda x: x[0])
    disp = sorted(disp, key=lambda x: x[0])

    # Find overlapping time range
    t0 = max(load[0][0], disp[0][0])
    t1 = min(load[-1][0], disp[-1][0])

    # Resample to uniform grid
    pairs = _resample(load, disp, args.rate, t0, t1)

    # Write synchronized pairs CSV
    csv_path = outdir / "pairs.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("t_s,force_N,disp_mm\n")
        for t, F, d in pairs:
            f.write(f"{t:.5f},{F:.6f},{d:.6f}\n")

    # Write sidecar JSON with provenance
    sidecar: Dict[str, Any] = {
        "artifact_type": "bending_rig_pairs",
        "pair_csv_path": csv_path.as_posix(),
        "units": {"force": "N", "disp": "mm"},
        "sample_rate_hz_est": args.rate,
        "n_samples": len(pairs),
        "time_range_s": [t0, t1],
        "provenance": {
            "load_series_path": args.load,
            "load_sha256": _sha256(Path(args.load)),
            "disp_series_path": args.disp,
            "disp_sha256": _sha256(Path(args.disp)),
        },
    }
    sidecar_path = outdir / "pairs_sidecar.json"
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(sidecar, f, indent=2)

    # Fit on mid-range displacement (exclude toe region and yield)
    d_vals = [d for _, _, d in pairs]
    d_sorted = sorted(d_vals)
    n = len(d_sorted) - 1
    d_lo = d_sorted[max(0, min(n, round(args.fit_pct_low / 100 * n)))]
    d_hi = d_sorted[max(0, min(n, round(args.fit_pct_high / 100 * n)))]

    F_fit = [F for _, F, d in pairs if d_lo <= d <= d_hi]
    d_fit = [d for _, F, d in pairs if d_lo <= d <= d_hi]

    slope, r2 = _linear_fit(F_fit, d_fit)

    # Calculate MOE
    E_pa = _calculate_moe(
        args.method, slope, args.span, args.width, args.thickness, args.inner_span
    )

    # Write MOE result
    moe_result: Dict[str, Any] = {
        "artifact_type": "bending_moe",
        "E_GPa": E_pa / 1e9,
        "method": args.method,
        "geometry": {
            "span_mm": args.span,
            "width_mm": args.width,
            "thickness_mm": args.thickness,
            "inner_span_mm": args.inner_span,
        },
        "fit": {
            "pct_low": args.fit_pct_low,
            "pct_high": args.fit_pct_high,
            "disp_range_mm": [d_lo, d_hi],
            "n_points": len(F_fit),
            "slope_N_per_mm": round(slope, 6),
            "r2": round(r2, 6),
        },
        "provenance": {
            "pairs_csv_path": csv_path.as_posix(),
            "pairs_sha256": _sha256(csv_path),
            "pairs_sidecar_path": sidecar_path.as_posix(),
            "pairs_sidecar_sha256": _sha256(sidecar_path),
            "load_series_path": args.load,
            "load_sha256": sidecar["provenance"]["load_sha256"],
            "disp_series_path": args.disp,
            "disp_sha256": sidecar["provenance"]["disp_sha256"],
        },
    }
    moe_path = outdir / "bending_moe.json"
    with open(moe_path, "w", encoding="utf-8") as f:
        json.dump(moe_result, f, indent=2)

    print(f"Wrote {csv_path}")
    print(f"Wrote {sidecar_path}")
    print(f"Wrote {moe_path}")
    print(f"  E = {E_pa/1e9:.3f} GPa (R² = {r2:.4f})")


if __name__ == "__main__":
    main()
