#!/usr/bin/env python3
"""
ods_compute.py — Compute Operating Deflection Shapes from grid captures.

For each point p:
    H_p(f) = FFT(roving_p) / FFT(reference)
    magnitude_p(f) = |H_p(f)|
    phase_p(f) = angle(H_p(f))

Outputs:
    derived/ods/ods_summary.json
    derived/ods/ods_f_{freq}Hz.json (per frequency of interest)
    derived/ods/transfer_functions.npz (full H(f) matrix for all points)

Usage:
    python scripts/ods_compute.py \
        --capture-dir ./captures/grid_run_001 \
        --frequencies 100,150,185,220,300 \
        --out ./captures/grid_run_001/derived/ods
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.signal import butter, filtfilt

# Canonical WAV I/O
from modes._shared.wav_io import read_wav_2ch


def _highpass(x: np.ndarray, fs: int, hz: float = 20.0) -> np.ndarray:
    """Apply 2nd-order Butterworth highpass filter."""
    if hz <= 0:
        return x
    nyq = 0.5 * fs
    w = hz / nyq
    b, a = butter(2, w, btype="highpass")
    return filtfilt(b, a, x).astype(np.float32)


def load_point_audio(point_dir: Path) -> Tuple[np.ndarray, int]:
    """Load 2-channel audio from a point directory."""
    audio_path = point_dir / "audio.wav"
    meta, ref, rov = read_wav_2ch(audio_path)
    # Stack back to (n, 2) for downstream compatibility
    audio = np.stack([ref, rov], axis=1)
    return audio, meta.sample_rate


def compute_transfer_function(
    reference: np.ndarray,
    roving: np.ndarray,
    sample_rate: int,
    highpass_hz: float = 20.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute transfer function H(f) = FFT(roving) / FFT(reference).
    
    Returns:
        freqs: frequency bins (Hz)
        H: complex transfer function
    """
    # Preprocessing
    ref = _highpass(reference - np.mean(reference), sample_rate, highpass_hz)
    rov = _highpass(roving - np.mean(roving), sample_rate, highpass_hz)
    
    # Window
    window = np.hanning(len(ref)).astype(np.float32)
    ref_w = ref * window
    rov_w = rov * window
    
    # FFT
    ref_fft = rfft(ref_w)
    rov_fft = rfft(rov_w)
    freqs = rfftfreq(len(ref), d=1.0 / sample_rate)
    
    # Transfer function with regularization to avoid division by zero
    eps = 1e-10 * np.max(np.abs(ref_fft))
    H = rov_fft / (ref_fft + eps)
    
    return freqs.astype(np.float32), H.astype(np.complex64)


def find_nearest_freq_idx(freqs: np.ndarray, target_hz: float) -> int:
    """Find index of nearest frequency bin."""
    return int(np.argmin(np.abs(freqs - target_hz)))


def load_grid_points(capture_dir: Path) -> List[Dict[str, Any]]:
    """Load grid definition and point metadata from capture directory."""
    grid_path = capture_dir / "grid.json"
    if not grid_path.exists():
        # Fall back to discovering points from directories
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
        description="Compute Operating Deflection Shapes from grid captures"
    )
    ap.add_argument("--capture-dir", required=True, help="Grid capture directory")
    ap.add_argument(
        "--frequencies",
        required=True,
        help="Comma-separated frequencies of interest (Hz)",
    )
    ap.add_argument("--out", required=True, help="Output directory for ODS results")
    ap.add_argument("--highpass", type=float, default=20.0, help="Highpass filter (Hz)")
    args = ap.parse_args()
    
    capture_dir = Path(args.capture_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse target frequencies
    target_freqs = [float(f.strip()) for f in args.frequencies.split(",")]
    
    # Load grid points
    points = load_grid_points(capture_dir)
    print(f"Processing {len(points)} grid points...")
    
    # Compute transfer functions for all points
    all_H: Dict[str, np.ndarray] = {}
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
        
        f, H = compute_transfer_function(reference, roving, sr, args.highpass)
        
        if freqs is None:
            freqs = f
        
        all_H[point_id] = H
        print(f"  {point_id}: H(f) computed ({len(H)} bins)")
    
    if freqs is None:
        print("Error: No valid captures found")
        return 1
    
    # Save full transfer function data (for later analysis)
    point_ids = list(all_H.keys())
    H_matrix = np.array([all_H[pid] for pid in point_ids])  # shape: (n_points, n_freqs)
    
    np.savez_compressed(
        out_dir / "transfer_functions.npz",
        point_ids=np.array(point_ids),
        freqs=freqs,
        H_real=H_matrix.real,
        H_imag=H_matrix.imag,
    )
    
    # Generate ODS for each target frequency
    ods_files = []
    for target_hz in target_freqs:
        idx = find_nearest_freq_idx(freqs, target_hz)
        actual_hz = float(freqs[idx])
        
        ods_values = []
        for point in points:
            pid = point["id"]
            if pid not in all_H:
                continue
            
            H_val = all_H[pid][idx]
            ods_values.append({
                "point_id": pid,
                "x": point["x"],
                "y": point["y"],
                "magnitude": float(np.abs(H_val)),
                "phase_deg": float(np.angle(H_val, deg=True)),
            })
        
        ods_data = {
            "artifact_type": "ods_shape",
            "target_frequency_hz": target_hz,
            "actual_frequency_hz": actual_hz,
            "frequency_bin_idx": idx,
            "n_points": len(ods_values),
            "values": ods_values,
        }
        
        filename = f"ods_f_{actual_hz:.1f}Hz.json"
        ods_path = out_dir / filename
        with open(ods_path, "w", encoding="utf-8") as f:
            json.dump(ods_data, f, indent=2)
        
        ods_files.append(filename)
        print(f"  ODS @ {actual_hz:.1f} Hz → {filename}")
    
    # Write summary
    summary = {
        "artifact_type": "ods_summary",
        "capture_dir": str(capture_dir),
        "n_points": len(point_ids),
        "point_ids": point_ids,
        "sample_rate": sample_rate,
        "n_frequency_bins": len(freqs),
        "frequency_range_hz": [float(freqs[0]), float(freqs[-1])],
        "target_frequencies_hz": target_freqs,
        "ods_files": ods_files,
        "transfer_function_file": "transfer_functions.npz",
    }
    
    with open(out_dir / "ods_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nODS computation complete: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
