#!/usr/bin/env python3
"""
grid_coherence.py — Compute coherence metrics across the capture grid.

For each point p:
    γ²_p(f) = |P_xy(f)|² / (P_xx(f) · P_yy(f))

Outputs:
    derived/coherence/coherence_summary.json
    derived/coherence/coherence_matrix.npz
    derived/coherence/point_coherence_stats.csv

Usage:
    python scripts/grid_coherence.py \
        --capture-dir ./captures/grid_run_001 \
        --frequencies 100,150,185,220,300 \
        --out ./captures/grid_run_001/derived/coherence
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.fft import rfftfreq
from scipy.signal import coherence as scipy_coherence

# Canonical WAV I/O
from modes._shared.wav_io import read_wav_2ch


def load_point_audio(point_dir: Path) -> Tuple[np.ndarray, int]:
    """Load 2-channel audio from a point directory."""
    audio_path = point_dir / "audio.wav"
    meta, ref, rov = read_wav_2ch(audio_path)
    # Stack back to (n, 2) for downstream compatibility
    audio = np.stack([ref, rov], axis=1)
    return audio, meta.sample_rate


def compute_coherence(
    reference: np.ndarray,
    roving: np.ndarray,
    sample_rate: int,
    nperseg: int = 1024,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute magnitude-squared coherence between reference and roving signals.
    
    γ²(f) = |P_xy(f)|² / (P_xx(f) · P_yy(f))
    
    Returns:
        freqs: frequency bins (Hz)
        coh: coherence values [0, 1]
    """
    freqs, coh = scipy_coherence(
        reference, roving,
        fs=sample_rate,
        nperseg=nperseg,
        noverlap=nperseg // 2,
    )
    return freqs.astype(np.float32), coh.astype(np.float32)


def find_nearest_freq_idx(freqs: np.ndarray, target_hz: float) -> int:
    """Find index of nearest frequency bin."""
    return int(np.argmin(np.abs(freqs - target_hz)))


def load_grid_points(capture_dir: Path) -> List[Dict[str, Any]]:
    """Load grid definition and point metadata from capture directory."""
    grid_path = capture_dir / "grid.json"
    if not grid_path.exists():
        points_dir = capture_dir / "points"
        if not points_dir.exists():
            raise FileNotFoundError(f"No grid.json or points/ found in {capture_dir}")
        
        points = []
        for point_dir in sorted(points_dir.iterdir()):
            if point_dir.is_dir():
                meta_path = point_dir / "capture_meta.json"
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    points.append({
                        "id": meta["point_id"],
                        "x": meta["position"]["x"],
                        "y": meta["position"]["y"],
                    })
        return points
    
    with open(grid_path, "r", encoding="utf-8") as f:
        grid_data = json.load(f)
    return grid_data["points"]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute grid coherence metrics from captures"
    )
    ap.add_argument("--capture-dir", required=True, help="Grid capture directory")
    ap.add_argument(
        "--frequencies",
        default="",
        help="Comma-separated frequencies of interest (Hz), or empty for all",
    )
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--nperseg", type=int, default=1024, help="FFT segment length")
    args = ap.parse_args()
    
    capture_dir = Path(args.capture_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse target frequencies (optional)
    target_freqs: List[float] = []
    if args.frequencies.strip():
        target_freqs = [float(f.strip()) for f in args.frequencies.split(",")]
    
    # Load grid points
    points = load_grid_points(capture_dir)
    print(f"Processing coherence for {len(points)} grid points...")
    
    # Compute coherence for all points
    all_coh: Dict[str, np.ndarray] = {}
    freqs: Optional[np.ndarray] = None
    sample_rate: Optional[int] = None
    
    for point in points:
        point_id = point["id"]
        point_dir = capture_dir / "points" / point_id
        
        if not point_dir.exists():
            print(f"  Warning: {point_id} not found, skipping")
            continue
        
        audio, sr = load_point_audio(point_dir)
        if sample_rate is None:
            sample_rate = sr
        
        # Channel 0 = reference, Channel 1 = roving
        reference = audio[:, 0]
        roving = audio[:, 1]
        
        f, coh = compute_coherence(reference, roving, sr, args.nperseg)
        
        if freqs is None:
            freqs = f
        
        all_coh[point_id] = coh
        print(f"  {point_id}: coherence computed ({len(coh)} bins)")
    
    if freqs is None:
        print("Error: No valid captures found")
        return 1
    
    # Save full coherence matrix
    point_ids = list(all_coh.keys())
    coh_matrix = np.array([all_coh[pid] for pid in point_ids])  # shape: (n_points, n_freqs)
    
    np.savez_compressed(
        out_dir / "coherence_matrix.npz",
        point_ids=np.array(point_ids),
        freqs=freqs,
        coherence=coh_matrix,
    )
    
    # Compute per-point statistics
    stats_rows = []
    for i, point_id in enumerate(point_ids):
        coh = coh_matrix[i]
        
        # Find the point's position
        pos_x, pos_y = 0.0, 0.0
        for pt in points:
            if pt["id"] == point_id:
                pos_x, pos_y = pt["x"], pt["y"]
                break
        
        stats = {
            "point_id": point_id,
            "x": pos_x,
            "y": pos_y,
            "mean_coherence": float(np.mean(coh)),
            "min_coherence": float(np.min(coh)),
            "max_coherence": float(np.max(coh)),
            "std_coherence": float(np.std(coh)),
        }
        
        # Add coherence at specific target frequencies
        for tf in target_freqs:
            idx = find_nearest_freq_idx(freqs, tf)
            actual_hz = freqs[idx]
            stats[f"coh_{actual_hz:.0f}Hz"] = float(coh[idx])
        
        stats_rows.append(stats)
    
    # Write CSV stats
    csv_path = out_dir / "point_coherence_stats.csv"
    if stats_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=stats_rows[0].keys())
            writer.writeheader()
            writer.writerows(stats_rows)
    
    # Generate target frequency analysis
    freq_analysis = []
    for tf in target_freqs:
        idx = find_nearest_freq_idx(freqs, tf)
        actual_hz = float(freqs[idx])
        coh_at_freq = coh_matrix[:, idx]
        
        freq_analysis.append({
            "target_hz": tf,
            "actual_hz": actual_hz,
            "mean_coherence": float(np.mean(coh_at_freq)),
            "min_coherence": float(np.min(coh_at_freq)),
            "max_coherence": float(np.max(coh_at_freq)),
            "std_coherence": float(np.std(coh_at_freq)),
            "n_points_above_0.9": int(np.sum(coh_at_freq > 0.9)),
            "n_points_below_0.5": int(np.sum(coh_at_freq < 0.5)),
        })
    
    # Identify low-coherence regions (potential coupling issues)
    mean_coh_per_point = np.mean(coh_matrix, axis=1)
    low_coh_threshold = 0.7
    low_coh_points = [
        {"point_id": point_ids[i], "mean_coherence": float(mean_coh_per_point[i])}
        for i in range(len(point_ids))
        if mean_coh_per_point[i] < low_coh_threshold
    ]
    
    # Write summary
    summary = {
        "artifact_type": "coherence_summary",
        "capture_dir": str(capture_dir),
        "n_points": len(point_ids),
        "point_ids": point_ids,
        "sample_rate": sample_rate,
        "nperseg": args.nperseg,
        "n_frequency_bins": len(freqs),
        "frequency_range_hz": [float(freqs[0]), float(freqs[-1])],
        "target_frequencies_hz": target_freqs,
        "frequency_analysis": freq_analysis,
        "global_stats": {
            "mean_coherence": float(np.mean(coh_matrix)),
            "std_coherence": float(np.std(coh_matrix)),
        },
        "low_coherence_points": low_coh_points,
        "output_files": {
            "matrix": "coherence_matrix.npz",
            "stats": "point_coherence_stats.csv",
        },
    }
    
    with open(out_dir / "coherence_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nCoherence analysis complete: {out_dir}")
    print(f"  Global mean coherence: {np.mean(coh_matrix):.3f}")
    if low_coh_points:
        print(f"  Low coherence points (<{low_coh_threshold}): {len(low_coh_points)}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
