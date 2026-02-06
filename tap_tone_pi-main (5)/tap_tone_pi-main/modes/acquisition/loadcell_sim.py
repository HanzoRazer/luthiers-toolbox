#!/usr/bin/env python3
"""
Simulated load cell → load_series.json (force vs time, 'N' or 'lbf').

Determinism: pass --seed to reproduce the same series.

Example:
  python modes/acquisition/loadcell_sim.py --out out/RUN/load_series.json \
    --unit N --rate 50 --duration 10 --amp 12 --baseline 0.5 --noise 0.2 --seed 42
"""
from __future__ import annotations
import argparse, json, math, random, time, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--unit", default="N", choices=["N","lbf"])
    ap.add_argument("--rate", type=float, default=50.0, help="Hz")
    ap.add_argument("--duration", type=float, default=10.0, help="seconds")
    ap.add_argument("--amp", type=float, default=10.0, help="peak force about baseline (unit)")
    ap.add_argument("--baseline", type=float, default=0.0, help="DC offset (unit)")
    ap.add_argument("--noise", type=float, default=0.1, help="white noise std-dev (unit)")
    ap.add_argument("--freq", type=float, default=0.25, help="Hz for primary sinusoid")
    ap.add_argument("--drift", type=float, default=0.02, help="Hz for very slow drift")
    ap.add_argument("--seed", type=int, default=None, help="PRNG seed for determinism")
    a = ap.parse_args()

    # Deterministic PRNG if seed provided
    if a.seed is None:
        random.seed()
    else:
        random.seed(a.seed)

    fs = max(1.0, a.rate); dt = 1.0/fs; n = int(round(a.duration * fs))
    t0 = time.time()
    rows = []

    # stable per-run random phase for the slow drift component
    phi = random.uniform(0.0, 2.0*math.pi)

    for i in range(n):
        t = i * dt
        # Force model: F = baseline + amp*sin(2π f t) + (amp/5)*sin(2π drift t + φ) + noise
        F = (a.baseline
             + a.amp * math.sin(2*math.pi*a.freq*t)
             + (a.amp/5.0) * math.sin(2*math.pi*a.drift*t + phi)
             + random.gauss(0.0, a.noise))
        rows.append([round(t, 5), float(F)])

    out = {
        "artifact_type": "load_series",
        "unit": a.unit,
        "sample_rate_hz": fs,
        "ts_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t0))),
        "sim_params": {
            "seed": a.seed,
            "amp": a.amp, "baseline": a.baseline, "noise": a.noise,
            "freq": a.freq, "drift": a.drift
        },
        "data": rows
    }
    p = pathlib.Path(a.out); p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(p, "w", encoding="utf-8"), indent=2)
    print(f"Wrote {p} ({len(rows)} samples)")

if __name__ == "__main__":
    main()
