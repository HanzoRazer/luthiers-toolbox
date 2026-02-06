#!/usr/bin/env python3
"""
Simulated dial indicator → displacement_series.json (displacement vs time, 'mm' or 'in').

Determinism: pass --seed to reproduce the same series.

Example:
  python modes/acquisition/dial_indicator_sim.py --out out/RUN/displacement_series.json \
    --unit mm --rate 20 --duration 10 --amp 0.8 --baseline 0.1 --noise 0.01 --seed 42
"""
from __future__ import annotations
import argparse, json, math, random, time, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--unit", default="mm", choices=["mm","in"])
    ap.add_argument("--rate", type=float, default=20.0, help="Hz")
    ap.add_argument("--duration", type=float, default=10.0, help="seconds")
    ap.add_argument("--amp", type=float, default=0.5, help="peak displacement about baseline (unit)")
    ap.add_argument("--baseline", type=float, default=0.0, help="DC offset (unit)")
    ap.add_argument("--noise", type=float, default=0.005, help="white noise std-dev (unit)")
    ap.add_argument("--freq", type=float, default=0.25, help="Hz for primary sinusoid")
    ap.add_argument("--drift", type=float, default=0.015, help="Hz for very slow drift")
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

    # stable per-run phase for slow drift
    phi = random.uniform(0.0, 2.0*math.pi)

    for i in range(n):
        t = i * dt
        d = (a.baseline
             + a.amp * math.sin(2*math.pi*a.freq*t)
             + (a.amp/6.0) * math.sin(2*math.pi*a.drift*t + phi)
             + random.gauss(0.0, a.noise))
        rows.append([round(t, 5), float(d)])

    out = {
        "artifact_type": "displacement_series",
        "unit": a.unit,
        "sample_rate_hz": round(len(rows)/max(a.duration, 1e-6), 3),
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
