#!/usr/bin/env python3
"""
wolf_metrics.py — Compute Wolf Stress Index (WSI) and related metrics.

Metrics computed:
    E∇(f)  — Gradient energy (spatial variation in magnitude)
    Eφ(f)  — Phase entropy (phase disorder across grid)
    L(f)   — Localization index (concentration of energy)
    WSI(f) — Wolf Stress Index composite: w1*E∇ + w2*Eφ + w3*(1-L)

Wolf note signature: Low coherence + high phase entropy + localized energy.

Outputs:
    derived/wolf/wsi_curve.csv      — WSI(f) across frequency range
    derived/wolf/wolf_candidates.json — Frequencies flagged as wolf candidates
    derived/wolf/wolf_metrics.json    — Full metrics summary

Usage:
    python scripts/wolf_metrics.py \
        --ods-dir ./captures/grid_run_001/derived/ods \
        --coherence-dir ./captures/grid_run_001/derived/coherence \
        --frequencies 80,100,120,150,185,220,280 \
        --out ./captures/grid_run_001/derived/wolf
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def load_ods_file(ods_path: Path) -> Dict[str, Any]:
    """Load ODS shape data from JSON file."""
    with open(ods_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_transfer_functions(npz_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load transfer function matrix from npz file.
    
    Returns:
        point_ids: array of point identifiers
        freqs: frequency bins
        H: complex transfer function matrix (n_points, n_freqs)
    """
    data = np.load(npz_path)
    point_ids = data["point_ids"]
    freqs = data["freqs"]
    H = data["H_real"] + 1j * data["H_imag"]
    return point_ids, freqs, H


def load_coherence_matrix(npz_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load coherence matrix from npz file.
    
    Returns:
        point_ids: array of point identifiers
        freqs: frequency bins
        coh: coherence matrix (n_points, n_freqs)
    """
    data = np.load(npz_path)
    return data["point_ids"], data["freqs"], data["coherence"]


def compute_gradient_energy(magnitudes: np.ndarray, positions: np.ndarray) -> float:
    """
    Compute gradient energy E∇(f) — spatial variation in magnitude.
    
    High gradient energy indicates rapid spatial changes in deflection shape,
    characteristic of wolf notes where energy is trapped/focused.
    
    Args:
        magnitudes: array of |H(f)| values per point
        positions: array of (x, y) coordinates per point
    
    Returns:
        Normalized gradient energy [0, 1+]
    """
    if len(magnitudes) < 2:
        return 0.0
    
    # Compute pairwise magnitude differences weighted by distance
    n = len(magnitudes)
    total_grad = 0.0
    count = 0
    
    for i in range(n):
        for j in range(i + 1, n):
            dist = np.sqrt(np.sum((positions[i] - positions[j]) ** 2))
            if dist > 1e-6:  # Avoid division by zero
                mag_diff = abs(magnitudes[i] - magnitudes[j])
                total_grad += mag_diff / dist
                count += 1
    
    if count == 0:
        return 0.0
    
    # Normalize by number of pairs and mean magnitude
    mean_mag = np.mean(np.abs(magnitudes)) + 1e-10
    return float(total_grad / (count * mean_mag))


def compute_phase_entropy(phases_deg: np.ndarray) -> float:
    """
    Compute phase entropy Eφ(f) — disorder in phase distribution.
    
    High phase entropy indicates incoherent vibration across the grid,
    a signature of wolf notes where modes interact destructively.
    
    Args:
        phases_deg: array of phase angles in degrees
    
    Returns:
        Normalized entropy [0, 1] where 1 = max disorder
    """
    if len(phases_deg) < 2:
        return 0.0
    
    # Convert to radians and wrap to [-π, π]
    phases_rad = np.deg2rad(phases_deg)
    phases_wrapped = np.angle(np.exp(1j * phases_rad))
    
    # Bin phases into 12 bins (30° each)
    n_bins = 12
    hist, _ = np.histogram(phases_wrapped, bins=n_bins, range=(-np.pi, np.pi))
    
    # Compute entropy
    probs = hist / hist.sum()
    probs = probs[probs > 0]  # Avoid log(0)
    entropy = -np.sum(probs * np.log2(probs))
    
    # Normalize by max entropy (uniform distribution)
    max_entropy = np.log2(n_bins)
    return float(entropy / max_entropy) if max_entropy > 0 else 0.0


def compute_localization_index(magnitudes: np.ndarray) -> float:
    """
    Compute localization index L(f) — concentration of energy.
    
    High localization indicates energy focused in few points,
    opposite of a distributed mode shape.
    
    Uses inverse participation ratio (IPR):
        L = sum(|m|^4) / sum(|m|^2)^2
    
    Args:
        magnitudes: array of |H(f)| values per point
    
    Returns:
        Localization index [1/N, 1] where 1 = fully localized
    """
    mags = np.abs(magnitudes)
    sum_sq = np.sum(mags ** 2)
    
    if sum_sq < 1e-10:
        return 0.0
    
    sum_fourth = np.sum(mags ** 4)
    return float(sum_fourth / (sum_sq ** 2))


def compute_wsi(
    gradient_energy: float,
    phase_entropy: float,
    localization: float,
    mean_coherence: float,
    weights: Tuple[float, float, float, float] = (0.3, 0.3, 0.2, 0.2),
) -> float:
    """
    Compute Wolf Stress Index (WSI).
    
    WSI = w1*E∇ + w2*Eφ + w3*(1-L) + w4*(1-γ²)
    
    High WSI indicates wolf note characteristics:
    - High gradient energy (trapped/focused vibration)
    - High phase entropy (mode interference)
    - Low localization (distributed but chaotic)
    - Low coherence (unstable response)
    
    Args:
        gradient_energy: E∇(f)
        phase_entropy: Eφ(f)
        localization: L(f)
        mean_coherence: mean γ²(f) across grid
        weights: (w1, w2, w3, w4) weights
    
    Returns:
        WSI value [0, 1+]
    """
    w1, w2, w3, w4 = weights
    
    # Normalize components
    grad_norm = min(gradient_energy, 2.0) / 2.0  # Cap at 2x
    
    wsi = (
        w1 * grad_norm +
        w2 * phase_entropy +
        w3 * (1.0 - localization) +
        w4 * (1.0 - mean_coherence)
    )
    
    return float(wsi)


def find_nearest_freq_idx(freqs: np.ndarray, target_hz: float) -> int:
    """Find index of nearest frequency bin."""
    return int(np.argmin(np.abs(freqs - target_hz)))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute Wolf Stress Index and related metrics"
    )
    ap.add_argument("--ods-dir", required=True, help="ODS output directory")
    ap.add_argument("--coherence-dir", required=True, help="Coherence output directory")
    ap.add_argument(
        "--frequencies",
        default="",
        help="Comma-separated frequencies to analyze (Hz), or empty for auto-range",
    )
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--wsi-threshold", type=float, default=0.6, help="WSI wolf threshold")
    ap.add_argument(
        "--weights",
        default="0.3,0.3,0.2,0.2",
        help="WSI weights: w_gradient,w_phase,w_localization,w_coherence",
    )
    args = ap.parse_args()
    
    ods_dir = Path(args.ods_dir)
    coh_dir = Path(args.coherence_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse weights
    weights = tuple(float(w.strip()) for w in args.weights.split(","))
    if len(weights) != 4:
        print("Error: weights must have 4 values")
        return 1
    
    # Load transfer functions
    tf_path = ods_dir / "transfer_functions.npz"
    if not tf_path.exists():
        print(f"Error: {tf_path} not found. Run ods_compute.py first.")
        return 1
    
    point_ids, tf_freqs, H_matrix = load_transfer_functions(tf_path)
    print(f"Loaded transfer functions: {len(point_ids)} points, {len(tf_freqs)} freq bins")
    
    # Load coherence matrix
    coh_path = coh_dir / "coherence_matrix.npz"
    if not coh_path.exists():
        print(f"Error: {coh_path} not found. Run grid_coherence.py first.")
        return 1
    
    _, coh_freqs, coh_matrix = load_coherence_matrix(coh_path)
    print(f"Loaded coherence: {coh_matrix.shape}")
    
    # Load point positions from ODS summary
    ods_summary_path = ods_dir / "ods_summary.json"
    with open(ods_summary_path, "r", encoding="utf-8") as f:
        ods_summary = json.load(f)
    
    # Get positions from any ODS file
    positions = {}
    for ods_file in ods_summary.get("ods_files", []):
        ods_data = load_ods_file(ods_dir / ods_file)
        for val in ods_data["values"]:
            positions[val["point_id"]] = np.array([val["x"], val["y"]])
        break  # Only need one file for positions
    
    # Build position array in same order as point_ids
    pos_array = np.array([positions.get(str(pid), [0, 0]) for pid in point_ids])
    
    # Determine frequencies to analyze
    target_freqs: List[float] = []
    if args.frequencies.strip():
        target_freqs = [float(f.strip()) for f in args.frequencies.split(",")]
    else:
        # Auto-range: 50-500 Hz in 10 Hz steps
        target_freqs = list(range(50, 501, 10))
    
    # Compute metrics for each frequency
    wsi_rows = []
    wolf_candidates = []
    
    for target_hz in target_freqs:
        tf_idx = find_nearest_freq_idx(tf_freqs, target_hz)
        actual_hz = float(tf_freqs[tf_idx])
        
        # Get magnitudes and phases at this frequency
        H_at_f = H_matrix[:, tf_idx]
        magnitudes = np.abs(H_at_f)
        phases_deg = np.angle(H_at_f, deg=True)
        
        # Get coherence at this frequency (may have different binning)
        coh_idx = find_nearest_freq_idx(coh_freqs, target_hz)
        coh_at_f = coh_matrix[:, coh_idx]
        mean_coh = float(np.mean(coh_at_f))
        
        # Compute metrics
        grad_energy = compute_gradient_energy(magnitudes, pos_array)
        phase_ent = compute_phase_entropy(phases_deg)
        localization = compute_localization_index(magnitudes)
        wsi = compute_wsi(grad_energy, phase_ent, localization, mean_coh, weights)
        
        row = {
            "freq_hz": actual_hz,
            "gradient_energy": grad_energy,
            "phase_entropy": phase_ent,
            "localization": localization,
            "mean_coherence": mean_coh,
            "wsi": wsi,
        }
        wsi_rows.append(row)
        
        # Flag wolf candidates
        if wsi > args.wsi_threshold:
            wolf_candidates.append({
                "frequency_hz": actual_hz,
                "wsi": wsi,
                "gradient_energy": grad_energy,
                "phase_entropy": phase_ent,
                "localization": localization,
                "mean_coherence": mean_coh,
            })
    
    # Write WSI curve CSV
    csv_path = out_dir / "wsi_curve.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=wsi_rows[0].keys())
        writer.writeheader()
        writer.writerows(wsi_rows)
    
    # Sort candidates by WSI
    wolf_candidates.sort(key=lambda x: x["wsi"], reverse=True)
    
    # Write wolf candidates
    candidates_data = {
        "artifact_type": "wolf_candidates",
        "wsi_threshold": args.wsi_threshold,
        "weights": {
            "gradient_energy": weights[0],
            "phase_entropy": weights[1],
            "localization": weights[2],
            "coherence": weights[3],
        },
        "n_candidates": len(wolf_candidates),
        "candidates": wolf_candidates,
    }
    
    with open(out_dir / "wolf_candidates.json", "w", encoding="utf-8") as f:
        json.dump(candidates_data, f, indent=2)
    
    # Write full metrics summary
    wsi_values = [r["wsi"] for r in wsi_rows]
    summary = {
        "artifact_type": "wolf_metrics",
        "frequency_range_hz": [wsi_rows[0]["freq_hz"], wsi_rows[-1]["freq_hz"]],
        "n_frequencies_analyzed": len(wsi_rows),
        "wsi_stats": {
            "mean": float(np.mean(wsi_values)),
            "max": float(np.max(wsi_values)),
            "min": float(np.min(wsi_values)),
            "std": float(np.std(wsi_values)),
        },
        "wsi_threshold": args.wsi_threshold,
        "n_wolf_candidates": len(wolf_candidates),
        "top_wolf_candidates": wolf_candidates[:5] if wolf_candidates else [],
        "weights": {
            "gradient_energy": weights[0],
            "phase_entropy": weights[1],
            "localization": weights[2],
            "coherence": weights[3],
        },
        "output_files": {
            "wsi_curve": "wsi_curve.csv",
            "candidates": "wolf_candidates.json",
        },
    }
    
    with open(out_dir / "wolf_metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nWolf metrics complete: {out_dir}")
    print(f"  Frequencies analyzed: {len(wsi_rows)}")
    print(f"  WSI range: {min(wsi_values):.3f} - {max(wsi_values):.3f}")
    print(f"  Wolf candidates (WSI > {args.wsi_threshold}): {len(wolf_candidates)}")
    
    if wolf_candidates:
        print("\n  Top wolf candidate frequencies:")
        for c in wolf_candidates[:3]:
            print(f"    {c['frequency_hz']:.1f} Hz (WSI={c['wsi']:.3f})")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
