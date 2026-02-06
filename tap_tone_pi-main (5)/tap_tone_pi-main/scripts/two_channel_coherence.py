#!/usr/bin/env python3
"""
scripts/two_channel_coherence.py  (MERGED: includes --write-plots)

Phase 2 starter: 2-channel synchronous capture + coherence + delay + phase.
Optionally writes inspection plots (PNG) into the bundle.

Outputs (capture_<ts>/ under --out):
- audio.wav, analysis.json, spectrum.csv
- optional: channels.json, geometry.json
- optional plots: coherence.png, phase_deg.png, spectrum.png, waveform.png
- session.jsonl (append-only at --out root)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.fft import rfft, rfftfreq
from scipy.signal import butter, filtfilt, coherence, csd, correlate

import matplotlib.pyplot as plt

# Canonical WAV I/O
from modes._shared.wav_io import write_wav_2ch


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _append_jsonl(path: Path, obj: Any) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True))
        f.write("\n")


def list_devices() -> list[dict[str, Any]]:
    devs = sd.query_devices()
    out: list[dict[str, Any]] = []
    for i, d in enumerate(devs):
        out.append(
            {
                "index": i,
                "name": d.get("name"),
                "max_input_channels": int(d.get("max_input_channels") or 0),
                "default_samplerate": d.get("default_samplerate"),
            }
        )
    return out


def _highpass(x: np.ndarray, fs: int, hz: float) -> np.ndarray:
    if hz <= 0:
        return x
    nyq = 0.5 * fs
    w = hz / nyq
    b, a = butter(2, w, btype="highpass")
    return filtfilt(b, a, x).astype(np.float32)


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x * x)))


def _is_clipped(x: np.ndarray) -> bool:
    return bool(np.any(np.abs(x) >= 0.999))


def _normalize_spec(spec: np.ndarray) -> np.ndarray:
    m = float(np.max(spec)) if spec.size else 0.0
    return (spec / m).astype(np.float32) if m > 0 else spec.astype(np.float32)


def _dominant_peak(freqs: np.ndarray, mag: np.ndarray, fmin: float, fmax: float) -> float | None:
    if freqs.size == 0:
        return None
    mask = (freqs >= fmin) & (freqs <= fmax)
    if not np.any(mask):
        return None
    idx = int(np.argmax(mag[mask]))
    freqs_m = freqs[mask]
    return float(freqs_m[idx])


def _downsample_series(f: np.ndarray, y: np.ndarray, max_points: int) -> list[dict[str, float]]:
    if f.size == 0:
        return []
    if f.size <= max_points:
        idxs = np.arange(f.size)
    else:
        idxs = np.linspace(0, f.size - 1, num=max_points).astype(int)
    return [{"freq_hz": float(f[i]), "value": float(y[i])} for i in idxs]


def _save_line_plot(
    *,
    out_path: Path,
    x: np.ndarray,
    y: np.ndarray,
    title: str,
    xlabel: str,
    ylabel: str,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
) -> None:
    fig = plt.figure(figsize=(10, 4))
    ax = fig.add_subplot(111)
    ax.plot(x, y)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _save_two_line_plot(
    *,
    out_path: Path,
    x: np.ndarray,
    y0: np.ndarray,
    y1: np.ndarray,
    title: str,
    xlabel: str,
    ylabel: str,
    labels: tuple[str, str] = ("ch0", "ch1"),
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
) -> None:
    fig = plt.figure(figsize=(10, 4))
    ax = fig.add_subplot(111)
    ax.plot(x, y0, label=labels[0])
    ax.plot(x, y1, label=labels[1])
    ax.legend()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _write_plots(
    *,
    cap_dir: Path,
    max_hz: float,
    freqs_fft: np.ndarray,
    ch0_mag: np.ndarray,
    ch1_mag: np.ndarray,
    t_s: np.ndarray,
    raw0: np.ndarray,
    raw1: np.ndarray,
    coh_f: np.ndarray,
    coh: np.ndarray,
    ph_f: np.ndarray,
    ph_deg: np.ndarray,
) -> None:
    _save_line_plot(
        out_path=cap_dir / "coherence.png",
        x=coh_f,
        y=coh,
        title="Magnitude-Squared Coherence (ch0 vs ch1)",
        xlabel="Frequency (Hz)",
        ylabel="Coherence",
        xlim=(0.0, float(max_hz)),
        ylim=(0.0, 1.0),
    )

    _save_line_plot(
        out_path=cap_dir / "phase_deg.png",
        x=ph_f,
        y=ph_deg,
        title="Cross-Spectral Phase Difference (degrees)",
        xlabel="Frequency (Hz)",
        ylabel="Phase (deg)",
        xlim=(0.0, float(max_hz)),
    )

    _save_two_line_plot(
        out_path=cap_dir / "spectrum.png",
        x=freqs_fft,
        y0=ch0_mag,
        y1=ch1_mag,
        title="Spectrum (normalized)",
        xlabel="Frequency (Hz)",
        ylabel="Magnitude",
        xlim=(0.0, float(max_hz)),
        labels=("ch0", "ch1"),
    )

    _save_two_line_plot(
        out_path=cap_dir / "waveform.png",
        x=t_s,
        y0=raw0,
        y1=raw1,
        title="Waveform (ch0, ch1)",
        xlabel="Time (s)",
        ylabel="Amplitude",
        labels=("ch0", "ch1"),
    )


@dataclass(frozen=True)
class Capture2Ch:
    sample_rate: int
    audio: np.ndarray  # (n,2) float32


def record_2ch(*, device: int, sample_rate: int, seconds: float) -> Capture2Ch:
    sd.default.samplerate = sample_rate
    sd.default.device = (device, None)
    n_samples = int(sample_rate * seconds)
    audio = sd.rec(frames=n_samples, channels=2, dtype="float32", blocking=True)
    audio = np.nan_to_num(audio, nan=0.0)
    return Capture2Ch(sample_rate=sample_rate, audio=audio)


def analyze_2ch(
    audio_2ch: np.ndarray,
    fs: int,
    *,
    highpass_hz: float,
    peak_min_hz: float,
    peak_max_hz: float,
    coherence_nperseg: int,
    coherence_max_points: int,
    band_focus: tuple[float, float],
) -> dict[str, Any]:
    if audio_2ch.ndim != 2 or audio_2ch.shape[1] != 2:
        raise ValueError("Expected audio shape (n,2)")

    raw0 = audio_2ch[:, 0].astype(np.float32)
    raw1 = audio_2ch[:, 1].astype(np.float32)

    x0 = raw0 - float(np.mean(raw0))
    x1 = raw1 - float(np.mean(raw1))
    x0 = _highpass(x0, fs, highpass_hz)
    x1 = _highpass(x1, fs, highpass_hz)

    rms0, rms1 = _rms(x0), _rms(x1)
    clip0, clip1 = _is_clipped(raw0), _is_clipped(raw1)

    w = np.hanning(x0.size).astype(np.float32)
    X0 = np.abs(rfft(x0 * w)).astype(np.float32)
    X1 = np.abs(rfft(x1 * w)).astype(np.float32)
    freqs = rfftfreq(x0.size, d=1.0 / fs).astype(np.float32)

    X0n = _normalize_spec(X0)
    X1n = _normalize_spec(X1)

    dom0 = _dominant_peak(freqs, X0n, peak_min_hz, peak_max_hz)
    dom1 = _dominant_peak(freqs, X1n, peak_min_hz, peak_max_hz)

    nperseg = int(min(coherence_nperseg, x0.size))
    if nperseg < 256:
        nperseg = max(128, nperseg)

    f_coh, coh = coherence(x0, x1, fs=fs, nperseg=nperseg)
    f_coh = f_coh.astype(np.float32)
    coh = coh.astype(np.float32)

    f_csd, Pxy = csd(x0, x1, fs=fs, nperseg=nperseg)
    f_csd = f_csd.astype(np.float32)
    ph_deg = (np.angle(Pxy).astype(np.float32) * (180.0 / math.pi)).astype(np.float32)

    corr = correlate(x1, x0, mode="full", method="auto")
    lag = int(np.argmax(corr) - (x0.size - 1))
    delay_samples = lag
    delay_seconds = float(delay_samples / fs)

    f_lo, f_hi = band_focus
    mask_focus = (f_coh >= f_lo) & (f_coh <= f_hi)
    coh_mean_focus = float(np.mean(coh[mask_focus])) if np.any(mask_focus) else float(np.mean(coh)) if coh.size else 0.0

    conf = 0.0
    if clip0 or clip1:
        conf = 0.0
    else:
        if (rms0 > 0.005 and rms1 > 0.005):
            conf = min(1.0, 0.4 + 0.6 * max(0.0, min(1.0, coh_mean_focus)))
        elif (rms0 > 0.01 or rms1 > 0.01):
            conf = 0.25

    analysis: dict[str, Any] = {
        "sample_rate": int(fs),
        "channels": 2,
        "dominant_hz": dom0 if dom0 is not None else dom1,
        "rms": [rms0, rms1],
        "clipped": [clip0, clip1],
        "confidence": float(conf),
        "peaks": {
            "ch0": [{"freq_hz": dom0, "magnitude": None}] if dom0 is not None else [],
            "ch1": [{"freq_hz": dom1, "magnitude": None}] if dom1 is not None else [],
        },
        "cross_channel": {
            "pair": [0, 1],
            "delay_samples": int(delay_samples),
            "delay_seconds": float(delay_seconds),
            "coherence_focus_band_hz": [float(f_lo), float(f_hi)],
            "coherence_focus_mean": float(coh_mean_focus),
            "coherence": _downsample_series(f_coh, coh, coherence_max_points),
            "phase_deg": _downsample_series(f_csd, ph_deg, coherence_max_points),
        },
        "algo": {
            "version": "0.2.1-phase2-plots",
            "window": "hann",
            "highpass_hz": float(highpass_hz),
            "peak_min_hz": float(peak_min_hz),
            "peak_max_hz": float(peak_max_hz),
            "coherence_nperseg": int(nperseg),
        },
    }

    return {
        "analysis": analysis,
        "freqs": freqs,
        "ch0_mag": X0n,
        "ch1_mag": X1n,
        "raw0": raw0,
        "raw1": raw1,
        "coh_f": f_coh,
        "coh": coh,
        "ph_f": f_csd,
        "ph_deg": ph_deg,
    }


def persist_bundle(
    *,
    out_root: Path,
    label: str | None,
    cap: Capture2Ch,
    analysis: dict[str, Any],
    freqs: np.ndarray,
    ch0_mag: np.ndarray,
    ch1_mag: np.ndarray,
    raw0: np.ndarray,
    raw1: np.ndarray,
    coh_f: np.ndarray,
    coh: np.ndarray,
    ph_f: np.ndarray,
    ph_deg: np.ndarray,
    write_channels: bool,
    write_geometry: bool,
    mic_distance_mm: float | None,
    write_plots: bool,
    plot_max_hz: float,
) -> Path:
    _ensure_dir(out_root)
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    cap_dir = out_root / f"capture_{ts}"
    _ensure_dir(cap_dir)

    # Write 2-channel WAV using canonical layer
    wav_path = cap_dir / "audio.wav"
    x = np.clip(cap.audio, -1.0, 1.0)
    write_wav_2ch(wav_path, cap.sample_rate, x[:, 0], x[:, 1])

    analysis_path = cap_dir / "analysis.json"
    analysis_out = dict(analysis)
    analysis_out["ts_utc"] = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    analysis_out["label"] = label
    _write_json(analysis_path, analysis_out)

    spec_path = cap_dir / "spectrum.csv"
    lines = ["freq_hz,ch0_mag,ch1_mag\n"]
    for i in range(freqs.size):
        lines.append(f"{float(freqs[i]):.6f},{float(ch0_mag[i]):.8f},{float(ch1_mag[i]):.8f}\n")
    spec_path.write_text("".join(lines), encoding="utf-8")

    if write_channels:
        _write_json(
            cap_dir / "channels.json",
            {
                "channels": [
                    {"index": 0, "id": "mic_0", "type": "microphone", "role": "reference"},
                    {"index": 1, "id": "mic_1", "type": "microphone", "role": "secondary"},
                ]
            },
        )

    if write_geometry:
        z = float(mic_distance_mm) if mic_distance_mm is not None else 300.0
        _write_json(
            cap_dir / "geometry.json",
            {
                "coordinate_system": "instrument_body",
                "units": "mm",
                "origin": "bridge_center",
                "microphones": [
                    {"id": "mic_0", "position": [0.0, 0.0, z], "estimated": True},
                    {"id": "mic_1", "position": [120.0, 40.0, z], "estimated": True},
                ],
            },
        )

    _append_jsonl(
        out_root / "session.jsonl",
        {
            "ts_utc": ts,
            "label": label,
            "capture_dir": str(cap_dir),
            "dominant_hz": analysis_out.get("dominant_hz"),
            "confidence": analysis_out.get("confidence"),
            "clipped": analysis_out.get("clipped"),
            "rms": analysis_out.get("rms"),
            "cross_delay_s": (analysis_out.get("cross_channel") or {}).get("delay_seconds"),
            "coherence_focus_mean": (analysis_out.get("cross_channel") or {}).get("coherence_focus_mean"),
        },
    )

    if write_plots:
        n = raw0.size
        t_s = (np.arange(n, dtype=np.float32) / float(cap.sample_rate)).astype(np.float32)
        _write_plots(
            cap_dir=cap_dir,
            max_hz=plot_max_hz,
            freqs_fft=freqs,
            ch0_mag=ch0_mag,
            ch1_mag=ch1_mag,
            t_s=t_s,
            raw0=raw0,
            raw1=raw1,
            coh_f=coh_f,
            coh=coh,
            ph_f=ph_f,
            ph_deg=ph_deg,
        )

    return cap_dir


def main() -> None:
    ap = argparse.ArgumentParser(description="2-channel capture + coherence + delay + phase (Phase 2).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_dev = sub.add_parser("devices", help="List audio input devices")
    p_dev.add_argument("--all", action="store_true", help="Show devices even if no input channels")

    p_run = sub.add_parser("run", help="Capture 2ch audio and compute coherence/delay/phase")
    p_run.add_argument("--device", type=int, required=True, help="Input device index with >=2 inputs")
    p_run.add_argument("--sample-rate", type=int, default=48000)
    p_run.add_argument("--seconds", type=float, default=2.5)
    p_run.add_argument("--label", type=str, default=None)
    p_run.add_argument("--out", type=str, required=True, help="Output root directory")
    p_run.add_argument("--highpass-hz", type=float, default=20.0)
    p_run.add_argument("--peak-min-hz", type=float, default=40.0)
    p_run.add_argument("--peak-max-hz", type=float, default=2000.0)
    p_run.add_argument("--nperseg", type=int, default=4096)
    p_run.add_argument("--coh-max-points", type=int, default=300)
    p_run.add_argument("--focus-band", type=str, default="60,600", help="e.g. '60,600' Hz")
    p_run.add_argument("--write-channels", action="store_true")
    p_run.add_argument("--write-geometry", action="store_true")
    p_run.add_argument("--mic-distance-mm", type=float, default=None)

    p_run.add_argument("--write-plots", action="store_true")
    p_run.add_argument("--plot-max-hz", type=float, default=1500.0)

    args = ap.parse_args()

    if args.cmd == "devices":
        devs = list_devices()
        for d in devs:
            if (not args.all) and (d["max_input_channels"] <= 0):
                continue
            print(f'[{d["index"]}] {d["name"]} (in={d["max_input_channels"]}, default_sr={d["default_samplerate"]})')
        return

    # run
    f0, f1 = [float(x.strip()) for x in args.focus_band.split(",")]
    if f0 <= 0 or f1 <= 0 or f1 <= f0:
        raise SystemExit("Invalid --focus-band. Use like '60,600' with 0 < f0 < f1.")
    if args.plot_max_hz <= 0:
        raise SystemExit("--plot-max-hz must be > 0")

    dev = sd.query_devices(args.device)
    if int(dev.get("max_input_channels") or 0) < 2:
        raise SystemExit(f"Device {args.device} has <2 input channels: {dev.get('name')}")

    print("Recording 2-channel audio...")
    cap = record_2ch(device=args.device, sample_rate=args.sample_rate, seconds=args.seconds)

    print("Analyzing coherence / delay / phase...")
    out = analyze_2ch(
        cap.audio,
        cap.sample_rate,
        highpass_hz=args.highpass_hz,
        peak_min_hz=args.peak_min_hz,
        peak_max_hz=args.peak_max_hz,
        coherence_nperseg=args.nperseg,
        coherence_max_points=args.coh_max_points,
        band_focus=(f0, f1),
    )

    analysis = out["analysis"]
    cc = analysis.get("cross_channel", {})
    print("")
    print(f"Dominant: {analysis.get('dominant_hz')} Hz")
    print(f"RMS: {analysis['rms']}  Clipped: {analysis['clipped']}  Conf: {analysis['confidence']:.2f}")
    print(f"Delay: {cc.get('delay_seconds')} s (samples={cc.get('delay_samples')})")
    print(f"Coherence mean [{f0:.0f},{f1:.0f}] Hz: {cc.get('coherence_focus_mean')}")
    print("")

    cap_dir = persist_bundle(
        out_root=Path(args.out).expanduser().resolve(),
        label=args.label,
        cap=cap,
        analysis=analysis,
        freqs=out["freqs"],
        ch0_mag=out["ch0_mag"],
        ch1_mag=out["ch1_mag"],
        raw0=out["raw0"],
        raw1=out["raw1"],
        coh_f=out["coh_f"],
        coh=out["coh"],
        ph_f=out["ph_f"],
        ph_deg=out["ph_deg"],
        write_channels=args.write_channels,
        write_geometry=args.write_geometry,
        mic_distance_mm=args.mic_distance_mm,
        write_plots=args.write_plots,
        plot_max_hz=args.plot_max_hz,
    )

    print(f"[OK] Wrote bundle: {cap_dir}")
    if args.write_plots:
        print("      + coherence.png, phase_deg.png, spectrum.png, waveform.png")


if __name__ == "__main__":
    main()
