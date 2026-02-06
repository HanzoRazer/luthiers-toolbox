#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Dict, List, Tuple

import numpy as np
from numpy.fft import rfft, rfftfreq
from scipy.signal import find_peaks

# Canonical WAV I/O
from modes._shared.wav_io import read_wav_mono


def analyze(
    y: np.ndarray, sr: int, n_peaks: int = 6
) -> Tuple[np.ndarray, np.ndarray, List[Tuple[float, float]]]:
    """
    Analyze audio and extract top N peaks.

    Returns:
        freqs, Y (magnitude spectrum), sorted peaks [(freq_hz, amplitude), ...]
    """
    y = y.astype(np.float64)
    y = y - np.mean(y)
    N = len(y)

    window = np.hanning(N)
    Y = np.abs(rfft(window * y))
    freqs = rfftfreq(N, 1 / sr)

    # Threshold: 8% of max magnitude
    thresh = np.max(Y) * 0.08
    peaks, _ = find_peaks(Y, height=thresh, distance=20)

    # Get top N by magnitude
    idx = np.argsort(Y[peaks])[::-1][:n_peaks]
    top_peaks = sorted(
        [(float(freqs[peaks[i]]), float(Y[peaks[i]])) for i in idx],
        key=lambda x: x[0],
    )

    return freqs, Y, top_peaks


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Offline tap-tone analysis from WAV file"
    )
    ap.add_argument("--wav", required=True, help="Path to WAV file")
    ap.add_argument(
        "--peaks", type=int, default=6, help="Number of peaks to extract"
    )
    ap.add_argument(
        "--labels",
        nargs="*",
        default=[],
        help="Peak labels (A0 T11 B11 ...). If omitted, use p1, p2, ...",
    )
    ap.add_argument("--outfile", required=True, help="Output JSON path")
    a = ap.parse_args()

    # Read WAV using canonical layer
    meta, y = read_wav_mono(pathlib.Path(a.wav))
    sr = meta.sample_rate

    # Analyze
    freqs, Y, top = analyze(y, sr, a.peaks)

    # Build labels dict
    labels: Dict[str, Any] = {}
    for i, (f, amp) in enumerate(top):
        name = a.labels[i] if i < len(a.labels) else f"p{i+1}"
        labels[name] = {"freq_hz": round(f, 2), "amp": round(float(amp), 2)}

    # Write JSON
    pathlib.Path(a.outfile).parent.mkdir(parents=True, exist_ok=True)
    with open(a.outfile, "w", encoding="utf-8") as f:
        json.dump(
            {
                "artifact_type": "tap_tone",
                "sample_rate": int(sr),
                "duration_s": round(len(y) / sr, 3),
                "peaks": labels,
                "source_wav": a.wav,
            },
            f,
            indent=2,
        )

    print(f"Wrote {a.outfile}")


if __name__ == "__main__":
    main()
