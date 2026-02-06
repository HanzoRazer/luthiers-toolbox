#!/usr/bin/env python3
import argparse, json, os, pathlib, numpy as np
from numpy.fft import rfft, rfftfreq
from scipy.signal import find_peaks
import sounddevice as sd
import matplotlib.pyplot as plt

def record(sr, duration):
    y = sd.rec(int(duration*sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait(); return y[:,0]

def analyze(y, sr, n_peaks=6):
    y = y - np.mean(y)
    N = len(y); Y = np.abs(rfft(np.hanning(N)*y)); freqs = rfftfreq(N, 1/sr)
    thresh = np.max(Y) * 0.08
    peaks, _ = find_peaks(Y, height=thresh, distance=20)
    idx = np.argsort(Y[peaks])[::-1][:n_peaks]
    return freqs, Y, sorted([(float(freqs[peaks[i]]), float(Y[peaks[i]])) for i in idx], key=lambda x: x[0])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, default=44100)
    ap.add_argument("--duration", type=float, default=4.0)
    ap.add_argument("--peaks", type=int, default=6)
    ap.add_argument("--labels", nargs='*', default=[])
    ap.add_argument("--outfile", required=True)
    ap.add_argument("--plot", default="")
    a = ap.parse_args()

    y = record(a.sr, a.duration)
    freqs, Y, top = analyze(y, a.sr, a.peaks)

    labels = {}
    for i, (f, amp) in enumerate(top):
        labels[(a.labels[i] if i < len(a.labels) else f"p{i+1}")]= {"freq_hz": round(f,2), "amp": round(float(amp),2)}

    pathlib.Path(a.outfile).parent.mkdir(parents=True, exist_ok=True)
    with open(a.outfile, "w", encoding="utf-8") as f:
        json.dump({
          "artifact_type": "tap_tone",
          "sample_rate": a.sr,
          "duration_s": a.duration,
          "peaks": labels
        }, f, indent=2)
    print(f"Wrote {a.outfile}")

    if a.plot:
        plt.figure(figsize=(8,4))
        import numpy as _np
        plt.plot(freqs, 20*_np.log10(Y+1e-12))
        plt.xlabel('Hz'); plt.ylabel('dB'); plt.title('Tap Spectrum')
        for name, d in labels.items():
            plt.axvline(d['freq_hz'], color='r', alpha=0.35); plt.text(d['freq_hz'], plt.ylim()[1]*0.92, name, rotation=90, va='top')
        plt.tight_layout(); plt.savefig(a.plot, dpi=150)
        print(f"Wrote {a.plot}")

if __name__ == "__main__":
    main()
