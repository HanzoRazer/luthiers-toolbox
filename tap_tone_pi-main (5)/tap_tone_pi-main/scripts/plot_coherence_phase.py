#!/usr/bin/env python3
"""
plot_coherence_phase.py

Companion script for Phase-2 bundles created by two_channel_coherence.py.

Reads a capture_<ts>/ folder containing:
- analysis.json (with cross_channel.coherence and cross_channel.phase_deg series)
- spectrum.csv  (freq_hz,ch0_mag,ch1_mag)  [optional for spectrum plot]

Writes PNGs into the same folder:
- coherence.png
- phase_deg.png
- spectrum.png (optional if spectrum.csv exists)
- waveform.png (optional if audio.wav exists)

This is intentionally file-based so you can inspect results without running notebooks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import matplotlib.pyplot as plt
import wave


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_spectrum_csv(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # freq_hz,ch0_mag,ch1_mag
    rows = path.read_text(encoding="utf-8").strip().splitlines()
    if len(rows) < 2:
        return np.array([]), np.array([]), np.array([])
    data = []
    for line in rows[1:]:
        parts = line.split(",")
        if len(parts) != 3:
            continue
        data.append((float(parts[0]), float(parts[1]), float(parts[2])))
    arr = np.array(data, dtype=np.float32)
    return arr[:, 0], arr[:, 1], arr[:, 2]


def read_wav_mono_or_stereo(wav_path: Path) -> tuple[int, np.ndarray]:
    # returns fs, float32 audio array shape (n,ch)
    with wave.open(str(wav_path), "rb") as wf:
        ch = wf.getnchannels()
        fs = wf.getframerate()
        n = wf.getnframes()
        sampwidth = wf.getsampwidth()
        frames = wf.readframes(n)

    # decode PCM (supports 16-bit only here; keep simple)
    if sampwidth != 2:
        raise ValueError(f"Unsupported WAV sample width {sampwidth*8} bits. Expected 16-bit PCM.")
    x = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767.0
    if ch > 1:
        x = x.reshape(-1, ch)
    else:
        x = x.reshape(-1, 1)
    return fs, x


def save_line_plot(
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


def save_two_line_plot(
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot coherence/phase (+ optional spectrum/waveform) to PNGs.")
    ap.add_argument("--capture-dir", required=True, help="Path to capture_<ts>/ folder")
    ap.add_argument("--max-hz", type=float, default=2000.0, help="Max frequency to plot for spectrum/coh/phase")
    ap.add_argument("--plot-spectrum", action="store_true", help="Plot spectrum.png if spectrum.csv exists")
    ap.add_argument("--plot-waveform", action="store_true", help="Plot waveform.png if audio.wav exists")
    args = ap.parse_args()

    cap_dir = Path(args.capture_dir).expanduser().resolve()
    if not cap_dir.exists():
        raise SystemExit(f"Capture dir not found: {cap_dir}")

    analysis_path = cap_dir / "analysis.json"
    if not analysis_path.exists():
        raise SystemExit(f"Missing: {analysis_path}")

    analysis = load_json(analysis_path)
    cc = analysis.get("cross_channel") or {}
    coh_series = cc.get("coherence") or []
    ph_series = cc.get("phase_deg") or []

    if not coh_series:
        raise SystemExit("analysis.json has no cross_channel.coherence series to plot.")
    if not ph_series:
        raise SystemExit("analysis.json has no cross_channel.phase_deg series to plot.")

    f_coh = np.array([float(p["freq_hz"]) for p in coh_series], dtype=np.float32)
    coh = np.array([float(p["value"]) for p in coh_series], dtype=np.float32)

    f_ph = np.array([float(p["freq_hz"]) for p in ph_series], dtype=np.float32)
    ph = np.array([float(p["value"]) for p in ph_series], dtype=np.float32)

    # coherence plot
    save_line_plot(
        out_path=cap_dir / "coherence.png",
        x=f_coh,
        y=coh,
        title="Magnitude-Squared Coherence (ch0 vs ch1)",
        xlabel="Frequency (Hz)",
        ylabel="Coherence",
        xlim=(0.0, float(args.max_hz)),
        ylim=(0.0, 1.0),
    )

    # phase plot
    save_line_plot(
        out_path=cap_dir / "phase_deg.png",
        x=f_ph,
        y=ph,
        title="Cross-Spectral Phase Difference (degrees)",
        xlabel="Frequency (Hz)",
        ylabel="Phase (deg)",
        xlim=(0.0, float(args.max_hz)),
        ylim=None,
    )

    # optional spectrum
    spec_path = cap_dir / "spectrum.csv"
    if args.plot_spectrum and spec_path.exists():
        f, m0, m1 = read_spectrum_csv(spec_path)
        if f.size:
            save_two_line_plot(
                out_path=cap_dir / "spectrum.png",
                x=f,
                y0=m0,
                y1=m1,
                title="Spectrum (normalized)",
                xlabel="Frequency (Hz)",
                ylabel="Magnitude",
                xlim=(0.0, float(args.max_hz)),
            )

    # optional waveform
    wav_path = cap_dir / "audio.wav"
    if args.plot_waveform and wav_path.exists():
        fs, x = read_wav_mono_or_stereo(wav_path)
        t = np.arange(x.shape[0], dtype=np.float32) / float(fs)
        if x.shape[1] == 1:
            save_line_plot(
                out_path=cap_dir / "waveform.png",
                x=t,
                y=x[:, 0],
                title="Waveform (ch0)",
                xlabel="Time (s)",
                ylabel="Amplitude",
            )
        else:
            save_two_line_plot(
                out_path=cap_dir / "waveform.png",
                x=t,
                y0=x[:, 0],
                y1=x[:, 1],
                title="Waveform (ch0,ch1)",
                xlabel="Time (s)",
                ylabel="Amplitude",
                labels=("ch0", "ch1"),
            )

    print("[OK] Wrote PNGs:")
    print(f"  {cap_dir/'coherence.png'}")
    print(f"  {cap_dir/'phase_deg.png'}")
    if args.plot_spectrum and spec_path.exists():
        print(f"  {cap_dir/'spectrum.png'}")
    if args.plot_waveform and wav_path.exists():
        print(f"  {cap_dir/'waveform.png'}")


if __name__ == "__main__":
    main()
