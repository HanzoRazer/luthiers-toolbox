#!/usr/bin/env python3
"""
Chladni v1 — peak picker (facts only)

Migration: Canonical location is now tap_tone_pi.chladni.peaks_from_wav
           (previously modes/chladni/peaks_from_wav.py)

Reads a swept/stepped-tone WAV, computes a magnitude spectrum, and emits
prominent peak frequencies (no interpretation).

Usage:
  python -m tap_tone_pi.chladni.peaks_from_wav \\
    --wav out/RUN/chladni/capture.wav \\
    --out out/RUN/chladni/peaks.json \\
    --min-hz 50 --max-hz 2000 --prominence 0.02
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

import numpy as np
from scipy.signal import find_peaks, windows

# Canonical WAV I/O
from modes._shared.wav_io import read_wav_mono


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Extract peak frequencies from a Chladni sweep/stepped-tone WAV"
    )
    ap.add_argument("--wav", required=True, help="Input WAV file")
    ap.add_argument("--out", required=True, help="Output peaks.json path")
    ap.add_argument("--min-hz", type=float, default=50.0, help="Band lower limit")
    ap.add_argument("--max-hz", type=float, default=2000.0, help="Band upper limit")
    ap.add_argument(
        "--prominence",
        type=float,
        default=0.02,
        help="Peak prominence as fraction of max magnitude",
    )
    args = ap.parse_args()

    # Read WAV using canonical layer (returns x, meta)
    x, meta = read_wav_mono(pathlib.Path(args.wav))
    fs = meta.sample_rate

    N = len(x)
    w = windows.hann(N, sym=False)
    X = np.fft.rfft(x * w)
    f = np.fft.rfftfreq(N, 1.0 / fs)
    mag = np.abs(X) / (N / 2.0)

    # Band limit
    band = (f >= args.min_hz) & (f <= args.max_hz)
    fi = np.where(band)[0]
    magb = mag[fi]
    thresh = max(magb.max(), 1e-12) * args.prominence
    peaks, _ = find_peaks(magb, prominence=thresh)

    freqs = [float(f[fi[p]]) for p in peaks]

    out = {
        "artifact_type": "chladni_peaks",
        "wav_path": args.wav,
        "wav_sha256": sha256(args.wav),
        "fs_hz": float(fs),
        "band_hz": [args.min_hz, args.max_hz],
        "prominence_rel": args.prominence,
        "peaks_hz": freqs[:64],  # cap at 64 peaks
    }

    p = pathlib.Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fp:
        json.dump(out, fp, indent=2)

    print(f"Wrote {p} with {len(out['peaks_hz'])} peaks")


if __name__ == "__main__":
    main()
