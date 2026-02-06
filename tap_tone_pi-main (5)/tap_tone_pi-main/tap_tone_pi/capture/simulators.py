#!/usr/bin/env python3
"""
Simulators for load cell and dial indicator (no hardware required).

These generate synthetic time-series data for testing the bending rig
pipeline without physical sensors.

Usage:
    # Load cell simulator
    python -m tap_tone_pi.capture.simulators loadcell \\
        --out out/RUN/load_series.json --unit N --rate 50 --duration 10 --seed 42

    # Dial indicator simulator
    python -m tap_tone_pi.capture.simulators dial \\
        --out out/RUN/displacement_series.json --unit mm --rate 20 --duration 10 --seed 42

Migration:
    # Old paths (deprecated)
    python modes/acquisition/loadcell_sim.py --out ...
    python modes/acquisition/dial_indicator_sim.py --out ...
    
    # New path (v2.0.0+)
    python -m tap_tone_pi.capture.simulators loadcell --out ...
    python -m tap_tone_pi.capture.simulators dial --out ...
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import time


def simulate_loadcell(
    duration: float = 10.0,
    rate: float = 50.0,
    unit: str = "N",
    amp: float = 10.0,
    baseline: float = 0.0,
    noise: float = 0.1,
    freq: float = 0.25,
    drift: float = 0.02,
    seed: int | None = None,
) -> dict:
    """Generate synthetic load cell data."""
    if seed is not None:
        random.seed(seed)
    else:
        random.seed()

    fs = max(1.0, rate)
    dt = 1.0 / fs
    n = int(round(duration * fs))
    t0 = time.time()
    rows = []

    phi = random.uniform(0.0, 2.0 * math.pi)

    for i in range(n):
        t = i * dt
        F = (
            baseline
            + amp * math.sin(2 * math.pi * freq * t)
            + (amp / 5.0) * math.sin(2 * math.pi * drift * t + phi)
            + random.gauss(0.0, noise)
        )
        rows.append([round(t, 5), float(F)])

    return {
        "artifact_type": "load_series",
        "unit": unit,
        "sample_rate_hz": fs,
        "ts_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t0))),
        "sim_params": {
            "seed": seed,
            "amp": amp,
            "baseline": baseline,
            "noise": noise,
            "freq": freq,
            "drift": drift,
        },
        "data": rows,
    }


def simulate_dial_indicator(
    duration: float = 10.0,
    rate: float = 20.0,
    unit: str = "mm",
    amp: float = 0.5,
    baseline: float = 0.0,
    noise: float = 0.005,
    freq: float = 0.25,
    drift: float = 0.015,
    seed: int | None = None,
) -> dict:
    """Generate synthetic dial indicator data."""
    if seed is not None:
        random.seed(seed)
    else:
        random.seed()

    fs = max(1.0, rate)
    dt = 1.0 / fs
    n = int(round(duration * fs))
    t0 = time.time()
    rows = []

    phi = random.uniform(0.0, 2.0 * math.pi)

    for i in range(n):
        t = i * dt
        d = (
            baseline
            + amp * math.sin(2 * math.pi * freq * t)
            + (amp / 6.0) * math.sin(2 * math.pi * drift * t + phi)
            + random.gauss(0.0, noise)
        )
        rows.append([round(t, 5), float(d)])

    return {
        "artifact_type": "displacement_series",
        "unit": unit,
        "sample_rate_hz": round(len(rows) / max(duration, 1e-6), 3),
        "ts_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t0))),
        "sim_params": {
            "seed": seed,
            "amp": amp,
            "baseline": baseline,
            "noise": noise,
            "freq": freq,
            "drift": drift,
        },
        "data": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Hardware simulators")
    subparsers = parser.add_subparsers(dest="command", help="Simulator type")

    # Load cell subcommand
    lc = subparsers.add_parser("loadcell", help="Simulate load cell")
    lc.add_argument("--out", required=True)
    lc.add_argument("--unit", default="N", choices=["N", "lbf"])
    lc.add_argument("--rate", type=float, default=50.0, help="Hz")
    lc.add_argument("--duration", type=float, default=10.0, help="seconds")
    lc.add_argument("--amp", type=float, default=10.0, help="peak force")
    lc.add_argument("--baseline", type=float, default=0.0, help="DC offset")
    lc.add_argument("--noise", type=float, default=0.1, help="noise std-dev")
    lc.add_argument("--freq", type=float, default=0.25, help="Hz for sinusoid")
    lc.add_argument("--drift", type=float, default=0.02, help="Hz for drift")
    lc.add_argument("--seed", type=int, default=None, help="PRNG seed")

    # Dial indicator subcommand
    di = subparsers.add_parser("dial", help="Simulate dial indicator")
    di.add_argument("--out", required=True)
    di.add_argument("--unit", default="mm", choices=["mm", "in"])
    di.add_argument("--rate", type=float, default=20.0, help="Hz")
    di.add_argument("--duration", type=float, default=10.0, help="seconds")
    di.add_argument("--amp", type=float, default=0.5, help="peak displacement")
    di.add_argument("--baseline", type=float, default=0.0, help="DC offset")
    di.add_argument("--noise", type=float, default=0.005, help="noise std-dev")
    di.add_argument("--freq", type=float, default=0.25, help="Hz for sinusoid")
    di.add_argument("--drift", type=float, default=0.015, help="Hz for drift")
    di.add_argument("--seed", type=int, default=None, help="PRNG seed")

    args = parser.parse_args()

    if args.command == "loadcell":
        data = simulate_loadcell(
            duration=args.duration,
            rate=args.rate,
            unit=args.unit,
            amp=args.amp,
            baseline=args.baseline,
            noise=args.noise,
            freq=args.freq,
            drift=args.drift,
            seed=args.seed,
        )
    elif args.command == "dial":
        data = simulate_dial_indicator(
            duration=args.duration,
            rate=args.rate,
            unit=args.unit,
            amp=args.amp,
            baseline=args.baseline,
            noise=args.noise,
            freq=args.freq,
            drift=args.drift,
            seed=args.seed,
        )
    else:
        parser.print_help()
        return

    p = pathlib.Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {p} ({len(data['data'])} samples)")


if __name__ == "__main__":
    main()
