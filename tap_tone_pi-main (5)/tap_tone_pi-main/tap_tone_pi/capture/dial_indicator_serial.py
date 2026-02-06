#!/usr/bin/env python3
"""
Dial indicator serial capture → displacement_series.json (displacement vs time)

Typical indicators stream ASCII lines; adapt --pattern / --scale to your device.

Usage:
    python -m tap_tone_pi.capture.dial_indicator_serial \\
        --port COM3 --out out/disp.json --unit mm --duration 8 --rate 20

    python -m tap_tone_pi.capture.dial_indicator_serial \\
        --port /dev/ttyUSB0 --out out/disp.json --unit in --scale 25.4 --duration 10

Migration:
    # Old path (deprecated)
    python modes/acquisition/dial_indicator_serial.py --port ... --out ...
    
    # New path (v2.0.0+)
    python -m tap_tone_pi.capture.dial_indicator_serial --port ... --out ...
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import time

import serial  # pyserial


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Capture dial indicator data to displacement_series.json"
    )
    ap.add_argument("--port", required=True, help="Serial port (COM3, /dev/ttyUSB0)")
    ap.add_argument("--baud", type=int, default=9600, help="Baud rate")
    ap.add_argument("--unit", default="mm", help="Output unit: mm or in")
    ap.add_argument(
        "--pattern",
        default=r"(-?[0-9]+\.?[0-9]*)",
        help="Regex pattern to extract numeric value",
    )
    ap.add_argument(
        "--scale", type=float, default=1.0, help="Scale factor: raw → engineering units"
    )
    ap.add_argument("--duration", type=float, default=10.0, help="Capture duration (s)")
    ap.add_argument("--rate", type=float, default=20.0, help="Target sample rate (Hz)")
    ap.add_argument("--out", required=True, help="Output JSON path")
    args = ap.parse_args()

    # Open serial port
    ser = serial.Serial(args.port, args.baud, timeout=0.1)
    pattern = re.compile(args.pattern)
    t0 = time.time()
    rows = []
    period = 1.0 / max(args.rate, 1e-6)

    print(f"Capturing from {args.port} @ {args.baud} baud for {args.duration}s...")

    try:
        while (time.time() - t0) < args.duration:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                time.sleep(period)
                continue

            match = pattern.search(line)
            if not match:
                continue

            try:
                val = float(match.group(1)) * args.scale
            except ValueError:
                continue

            t = time.time() - t0
            rows.append([round(t, 5), float(val)])

            # Progress indicator
            if len(rows) % 20 == 0:
                print(f"  {len(rows)} samples...")

            time.sleep(period)

    except KeyboardInterrupt:
        print("\nCapture interrupted by user.")
    finally:
        ser.close()

    # Calculate actual sample rate
    elapsed = time.time() - t0
    actual_rate = round(len(rows) / max(elapsed, 1e-6), 3)

    # Write output
    out = {
        "artifact_type": "displacement_series",
        "unit": args.unit,
        "sample_rate_hz": actual_rate,
        "ts_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t0))),
        "n_samples": len(rows),
        "data": rows,
    }

    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote {args.out} ({len(rows)} samples, {actual_rate:.1f} Hz actual)")


if __name__ == "__main__":
    main()
