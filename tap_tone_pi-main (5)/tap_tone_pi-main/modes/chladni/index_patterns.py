#!/usr/bin/env python3
"""
Chladni v1 — index (facts only)

Associates image files to frequencies (by filename tag like F0148.png) and
writes a chladni_run.json with environment + provenance.

Frequency Mismatch Policy (G.2):
  - Warn + keep if delta_hz > 0
  - FAIL if delta_hz > CHLADNI_FREQ_TOLERANCE_HZ (default 5.0 Hz)

Usage:
  python modes/chladni/index_patterns.py \
    --peaks-json out/RUN/chladni/peaks.json \
    --images out/RUN/chladni/F0148.png out/RUN/chladni/F0226.png \
    --plate-id J45_TOP_2025_12_31_A \
    --tempC 22.0 --rh 45.0 \
    --out out/RUN/chladni/chladni_run.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import time

from .policy import attach_pattern_record, finalize_run
from .manifest_utils import append_chladni_to_run_manifest

# Frequency mismatch tolerance (Hz) - configurable via environment
CHLADNI_FREQ_TOLERANCE_HZ = float(os.getenv("CHLADNI_FREQ_TOLERANCE_HZ", "5.0"))


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Index Chladni pattern images to frequencies"
    )
    ap.add_argument("--peaks-json", required=True, help="Path to peaks.json")
    ap.add_argument(
        "--images", nargs="+", required=True, help="Image files (e.g., F0148.png)"
    )
    ap.add_argument("--plate-id", required=True, help="Plate identifier")
    ap.add_argument("--tempC", type=float, default=None, help="Temperature (C)")
    ap.add_argument("--rh", type=float, default=None, help="Relative humidity (pct)")
    ap.add_argument("--out", required=True, help="Output chladni_run.json path")
    ap.add_argument("--tolerance-hz", type=float, default=CHLADNI_FREQ_TOLERANCE_HZ,
                    help=f"Frequency mismatch tolerance (default: {CHLADNI_FREQ_TOLERANCE_HZ} Hz)")
    args = ap.parse_args()

    with open(args.peaks_json, "r", encoding="utf-8") as fp:
        peaks = json.load(fp)

    detected_peaks_hz = peaks.get("peaks_hz", [])
    patterns = []
    
    for img in args.images:
        name = pathlib.Path(img).name
        # Match F0148.png → 148 Hz, F1234.png → 1234 Hz
        m = re.search(r"F(\d+)", name)
        if not m:
            print(f"Warning: skipping {name} (no F<freq> pattern)")
            continue
        freq = int(m.group(1))
        rec = {
            "freq_hz": freq,
            "image_path": img,
            "image_sha256": sha256(img),
            "image_freq_tag_hz": freq,  # from filename
        }
        # Attach nearest peak and compute delta
        delta = attach_pattern_record(rec, detected_peaks_hz)
        if delta > 0:
            print(f"Warning: {name} freq_hz={freq} -> nearest_detected={rec['nearest_detected_hz']}, delta={delta:.2f} Hz")
        patterns.append(rec)

    run = {
        "schema_id": "chladni_run",
        "schema_version": "1.0",
        "artifact_type": "chladni_run",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "plate_id": args.plate_id,
        "environment": {
            "temp_C": args.tempC,
            "rh_pct": args.rh,
        },
        "excitation": {
            "mode": "external/unknown",  # measurement-only sandbox
        },
        "peaks_hz": detected_peaks_hz,
        "patterns": sorted(patterns, key=lambda x: x["freq_hz"]),
        "provenance": {
            "peaks_json_path": args.peaks_json,
            "peaks_sha256": sha256(args.peaks_json),
            "mic_wav_path": peaks.get("wav_path"),
            "mic_wav_sha256": peaks.get("wav_sha256"),
        },
    }

    # Apply frequency mismatch policy (may raise SystemExit(2))
    finalize_run(run, tolerance_hz=args.tolerance_hz)

    p = pathlib.Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fp:
        json.dump(run, fp, indent=2)

    print(f"Wrote {p} (patterns={len(run['patterns'])})")

    # Append artifacts to run-level manifest
    run_dir = p.parent
    # Heuristic: guess WAV and images from common demo paths (safe no-op if missing)
    wav = run_dir / "capture.wav"
    peaks_json = run_dir / "peaks.json"
    images = [ip for ip in [run_dir / "F0148.png", run_dir / "F0226.png"] if ip.exists()]
    try:
        if wav.exists() and peaks_json.exists() and images:
            man = append_chladni_to_run_manifest(
                run_dir,
                wav_path=wav,
                peaks_json_path=peaks_json,
                image_paths=images,
                chladni_run_json_path=p,
            )
            print(f"Updated manifest: {man}")
    except Exception as e:
        print(f"[warn] manifest append skipped: {e}")


if __name__ == "__main__":
    main()
