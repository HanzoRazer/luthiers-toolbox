#!/usr/bin/env python3
"""
phase2_slice.py — Phase 2 vertical slice: grid capture + TF/coherence + ODS snapshot + WSI

Usage:
    # Deterministic validation (no hardware)
    python scripts/phase2_slice.py run \
        --grid examples/phase2_grid_mm.json \
        --out ./runs_phase2 \
        --synthetic

    # Hardware run (2-channel capture)
    python scripts/phase2_slice.py devices
    python scripts/phase2_slice.py run \
        --grid examples/phase2_grid_mm.json \
        --out ./runs_phase2 \
        --device 1
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Optional hardware capture (only used when not --synthetic)
try:
    import sounddevice as sd
except Exception:
    sd = None  # type: ignore

import sys
from pathlib import Path
# Add scripts directory to path for package imports
sys.path.insert(0, str(Path(__file__).parent))

from phase2.grid import load_grid
from phase2.io_wav import write_wav_2ch, read_wav_2ch
from phase2.dsp import compute_transfer_and_coherence, nearest_bin, get_dsp_provenance
from phase2.metrics import PointSpectrum, wsi_curve, get_metrics_provenance
from phase2.viz import heatmap_scatter, plot_curve


def utc_stamp() -> str:
    return dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def save_csv(path: Path, header: str, rows: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def generate_synthetic_point_signals(
    *,
    fs: int,
    seconds: float,
    point_id: str,
    base_freqs: List[float],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Deterministic synthetic 2ch signals:
      ch0(ref): sum of sines (fixed)
      ch1(rov): same freqs but with point-dependent amplitude/phase + mild noise
    This is for pipeline validation, not physics truth.
    """
    n = int(fs * seconds)
    t = np.arange(n, dtype=np.float32) / float(fs)

    # reference: stable excitation proxy
    ref = np.zeros_like(t)
    for f in base_freqs:
        ref += 0.6 * np.sin(2.0 * np.pi * f * t).astype(np.float32)

    # point-dependent magnitude/phase shaping from point_id hash
    h = sum(ord(c) for c in point_id)
    amp_scale = 0.4 + (h % 17) / 40.0      # ~[0.4..0.825]
    ph_off = ((h % 31) - 15) * 2.0         # degrees

    rov = np.zeros_like(t)
    for k, f in enumerate(base_freqs):
        a = amp_scale * (1.0 + 0.15 * np.cos(k + h))
        ph = (ph_off + 10.0 * k) * (np.pi / 180.0)
        rov += a * np.sin(2.0 * np.pi * f * t + ph).astype(np.float32)

    # deterministic noise (seeded)
    rng = np.random.default_rng(h)
    ref += (0.01 * rng.standard_normal(n)).astype(np.float32)
    rov += (0.01 * rng.standard_normal(n)).astype(np.float32)

    # light fade in/out to avoid sharp edges
    w = np.hanning(n).astype(np.float32)
    ref *= w
    rov *= w
    return ref, rov


def capture_point_audio_2ch(
    *,
    device: int | None,
    fs: int,
    seconds: float,
    channels: int = 2,
) -> tuple[np.ndarray, np.ndarray]:
    if sd is None:
        raise RuntimeError("sounddevice not available; install it or use --synthetic")
    if channels != 2:
        raise ValueError("Phase 2 capture expects exactly 2 channels")

    sd.default.samplerate = fs
    if device is not None:
        sd.default.device = (device, None)

    n_samples = int(fs * seconds)
    data = sd.rec(frames=n_samples, channels=2, dtype="float32", blocking=True)
    x = np.nan_to_num(data, nan=0.0).astype(np.float32)
    return x[:, 0].copy(), x[:, 1].copy()


def cmd_run(args: argparse.Namespace) -> int:
    out_root = Path(args.out).expanduser().resolve()
    ensure_dir(out_root)

    grid = load_grid(Path(args.grid))
    session_id = f"session_{utc_stamp()}"
    session_dir = out_root / session_id
    points_dir = session_dir / "points"
    derived_dir = session_dir / "derived"
    plots_dir = session_dir / "plots"

    ensure_dir(points_dir)
    ensure_dir(derived_dir)
    ensure_dir(plots_dir)

    save_json(session_dir / "metadata.json", {
        "session_id": session_id,
        "created_at_utc": utc_stamp(),
        "phase": 2,
        "mode": "roving_grid_vertical_slice",
        "units": grid.units,
        "origin": grid.origin,
        "capture": {
            "synthetic": bool(args.synthetic),
            "device": args.device,
            "sample_rate_hz": args.sample_rate,
            "seconds": args.seconds,
        },
        "analysis": {
            "window": args.window,
            "nperseg": args.nperseg,
            "noverlap": args.noverlap if args.noverlap is not None else (args.nperseg // 2),
            "fmin_hz": args.fmin_hz,
            "fmax_hz": args.fmax_hz,
        }
    })

    save_json(session_dir / "grid.json", json.loads(Path(args.grid).read_text(encoding="utf-8")))

    # 1) CAPTURE (raw first)
    base_freqs = [110.0, 185.0, 220.0, 330.0, 440.0, 660.0]  # pipeline stimulus for synthetic
    for p in grid.points:
        pdir = points_dir / f"point_{p.id}"
        ensure_dir(pdir)

        if args.synthetic:
            x_ref, x_rov = generate_synthetic_point_signals(
                fs=args.sample_rate,
                seconds=args.seconds,
                point_id=p.id,
                base_freqs=base_freqs,
            )
        else:
            x_ref, x_rov = capture_point_audio_2ch(
                device=args.device,
                fs=args.sample_rate,
                seconds=args.seconds,
            )

        wav_path = pdir / "audio.wav"
        write_wav_2ch(wav_path, args.sample_rate, x_ref, x_rov)

        save_json(pdir / "capture_meta.json", {
            "point_id": p.id,
            "x": p.x,
            "y": p.y,
            "units": grid.units,
            "created_at_utc": utc_stamp(),
            "synthetic": bool(args.synthetic),
            "sample_rate_hz": args.sample_rate,
            "seconds": args.seconds,
            "wav": "audio.wav",
        })

    # 2) ANALYZE: compute transfer + coherence for each point
    spectra: List[PointSpectrum] = []
    for p in grid.points:
        pdir = points_dir / f"point_{p.id}"
        w = read_wav_2ch(pdir / "audio.wav")

        tf = compute_transfer_and_coherence(
            w.x_ref, w.x_rov, w.sample_rate,
            nperseg=args.nperseg,
            noverlap=args.noverlap,
            window=args.window,
            fmin_hz=args.fmin_hz,
            fmax_hz=args.fmax_hz,
        )

        # store point spectrum CSV (inspectable)
        rows = []
        for f, hm, coh, ph in zip(tf.freq_hz, tf.H_mag, tf.coherence, tf.H_phase_deg):
            rows.append(f"{float(f):.6f},{float(hm):.8e},{float(coh):.6f},{float(ph):.3f}")
        save_csv(
            pdir / "spectrum.csv",
            "freq_hz,H_mag,coherence,phase_deg",
            rows,
        )

        save_json(pdir / "analysis.json", {
            "point_id": p.id,
            "x": p.x,
            "y": p.y,
            "units": grid.units,
            "sample_rate_hz": w.sample_rate,
            "band_hz": [args.fmin_hz, args.fmax_hz],
            "window": args.window,
            "nperseg": args.nperseg,
            "noverlap": args.noverlap if args.noverlap is not None else (args.nperseg // 2),
            "summary": {
                "coherence_mean": float(np.mean(tf.coherence)) if tf.coherence.size else 0.0,
                "coherence_min": float(np.min(tf.coherence)) if tf.coherence.size else 0.0,
                "H_mag_max": float(np.max(tf.H_mag)) if tf.H_mag.size else 0.0
            }
        })

        spectra.append(PointSpectrum(
            point_id=p.id,
            x_mm=p.x,
            y_mm=p.y,
            freq_hz=tf.freq_hz,
            H_mag=tf.H_mag,
            coherence=tf.coherence,
            phase_deg=tf.H_phase_deg,
        ))

    # 3) WSI curve + candidates
    freqs, wsi, details = wsi_curve(spectra, grid, fmin_hz=args.fmin_hz, fmax_hz=args.fmax_hz)

    # CSV curve (includes admissible flag)
    rows = []
    for f, w, d in zip(freqs, wsi, details):
        rows.append(f"{float(f):.6f},{float(w):.6f},{d['loc']:.6f},{d['grad']:.6f},{d['phase_disorder']:.6f},{d['coh_mean']:.6f},{d['admissible']}")
    save_csv(
        derived_dir / "wsi_curve.csv",
        "freq_hz,wsi,loc,grad,phase_disorder,coh_mean,admissible",
        rows,
    )

    # candidates (top N by WSI with coherence gating)
    # Schema v2: each candidate needs freq_hz, wsi, admissible, coh_mean, top_points[]
    N = int(args.top_n)
    order = np.argsort(-wsi)  # descending

    # Helper: get top_points for a specific frequency bin
    def _top_points_at_freq(freq_bin_idx: int, max_points: int = 5) -> List[Dict[str, Any]]:
        """Return top points by coherence*H_mag score at given frequency bin."""
        scored = []
        for s in spectra:
            h_mag = float(s.H_mag[freq_bin_idx])
            coh = float(s.coherence[freq_bin_idx])
            # score: weighted combination favoring high coherence
            score = 0.6 * coh + 0.4 * min(h_mag, 1.0)
            scored.append({
                "point_id": s.point_id,
                "x_mm": s.x_mm,
                "y_mm": s.y_mm,
                "score": float(np.clip(score, 0.0, 1.0)),
            })
        scored.sort(key=lambda p: p["score"], reverse=True)
        return scored[:max_points]

    candidates_v2: List[Dict[str, Any]] = []
    for idx in order[: max(N, 1)]:
        cand = {
            "freq_hz": float(freqs[idx]),
            "wsi": float(wsi[idx]),
            "admissible": details[idx]["admissible"],
            "coh_mean": float(details[idx]["coh_mean"]),
            "top_points": _top_points_at_freq(idx, max_points=5),
        }
        # Optional notes field (schema allows it)
        if not details[idx]["admissible"]:
            cand["notes"] = "Low coherence - measurement quality insufficient"
        candidates_v2.append(cand)

    # Provenance per schema: algo_id, algo_version, numpy_version, computed_at_utc, dsp_provenance (optional)
    dsp_prov = get_dsp_provenance()
    metrics_prov = get_metrics_provenance()

    save_json(derived_dir / "wolf_candidates.json", {
        "schema_version": "phase2_wolf_candidates_v2",
        "wsi_threshold": 0.5,
        "coherence_threshold": 0.8,
        "candidates": candidates_v2,
        "provenance": {
            "algo_id": metrics_prov["algo_id"],
            "algo_version": metrics_prov["algo_version"],
            "numpy_version": metrics_prov["numpy_version"],
            "computed_at_utc": utc_stamp(),
            "dsp_provenance": dsp_prov,
        },
    })

    # ODS target for snapshot
    target = float(args.ods_target_hz)
    bi = nearest_bin(spectra[0].freq_hz, target)
    target_actual = float(spectra[0].freq_hz[bi])

    # 4) One ODS snapshot at a target frequency (default 185 Hz)
    # Schema v2: freqs_hz (array), points with x_mm, y_mm, H_mag[], H_phase_deg[], coherence[]
    # capdir is the session folder name (no absolute paths)
    capdir_logical = session_dir.name

    # Build points with array values (one element per frequency in freqs_hz)
    ods_points = []
    for s in spectra:
        ods_points.append({
            "point_id": s.point_id,
            "x_mm": s.x_mm,
            "y_mm": s.y_mm,
            "H_mag": [float(s.H_mag[bi])],
            "H_phase_deg": [float(s.phase_deg[bi])],
            "coherence": [float(s.coherence[bi])],
        })

    save_json(derived_dir / "ods_snapshot.json", {
        "schema_version": "phase2_ods_snapshot_v2",
        "capdir": capdir_logical,
        "freqs_hz": [target_actual],
        "points": ods_points,
        "provenance": {
            "algo_id": dsp_prov["algo_id"],
            "algo_version": dsp_prov["algo_version"],
            "numpy_version": dsp_prov["numpy_version"],
            "scipy_version": dsp_prov["scipy_version"],
            "computed_at_utc": utc_stamp(),
        },
    })

    # Build lookup dicts for plots
    mag_by_id = {s.point_id: float(s.H_mag[bi]) for s in spectra}
    coh_by_id = {s.point_id: float(s.coherence[bi]) for s in spectra}

    # Plots (optional but useful)
    plot_curve(
        freqs, wsi,
        title="WSI curve (measurement-only composite)",
        xlabel="Frequency (Hz)",
        ylabel="WSI (0..1)",
        out_path=plots_dir / "wsi_curve.png",
    )
    heatmap_scatter(
        grid, mag_by_id,
        title=f"ODS snapshot |H| at {target_actual:.1f} Hz",
        out_path=plots_dir / f"ods_mag_{target_actual:.1f}Hz.png",
    )
    heatmap_scatter(
        grid, coh_by_id,
        title=f"Coherence at {target_actual:.1f} Hz",
        out_path=plots_dir / f"coherence_{target_actual:.1f}Hz.png",
    )

    print(f"Wrote Phase 2 session: {session_dir}")
    return 0


def cmd_devices(_: argparse.Namespace) -> int:
    if sd is None:
        print("sounddevice not available in this environment.")
        return 1
    devs = sd.query_devices()
    for i, d in enumerate(devs):
        print(f"[{i}] {d.get('name')} (in={d.get('max_input_channels')}, out={d.get('max_output_channels')})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="phase2_slice", description="Phase 2 vertical slice: grid capture + TF/coherence + ODS snapshot + WSI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pd = sub.add_parser("devices", help="List audio devices (requires sounddevice)")
    pd.set_defaults(fn=cmd_devices)

    pr = sub.add_parser("run", help="Run the Phase 2 vertical slice")
    pr.add_argument("--grid", type=str, required=True, help="Path to grid.json (mm)")
    pr.add_argument("--out", type=str, required=True, help="Output root (session_* created under here)")
    pr.add_argument("--synthetic", action="store_true", help="Use deterministic synthetic 2ch data (no hardware required)")
    pr.add_argument("--device", type=int, default=None, help="Input device index (hardware mode only)")
    pr.add_argument("--sample-rate", type=int, default=48000)
    pr.add_argument("--seconds", type=float, default=3.0)

    pr.add_argument("--window", type=str, default="hann", choices=["hann", "hamming", "blackman", "boxcar"])
    pr.add_argument("--nperseg", type=int, default=4096)
    pr.add_argument("--noverlap", type=int, default=None)
    pr.add_argument("--fmin-hz", type=float, default=30.0)
    pr.add_argument("--fmax-hz", type=float, default=2000.0)

    pr.add_argument("--top-n", type=int, default=8, help="Top N wolf candidates to write")
    pr.add_argument("--ods-target-hz", type=float, default=185.0, help="ODS snapshot target frequency")
    pr.set_defaults(fn=cmd_run)

    return p


def main(argv: List[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    rc = args.fn(args)
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
