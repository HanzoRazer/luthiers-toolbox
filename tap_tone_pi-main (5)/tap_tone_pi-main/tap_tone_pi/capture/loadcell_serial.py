#!/usr/bin/env python3
"""
Load cell serial capture → load_series.json (force vs time)

Config JSON example:
{
  "port": "COM4",                 // or "/dev/ttyUSB0"
  "baud": 115200,
  "timeout_s": 0.2,
  "unit": "N",                    // "N" or "lbf" after calibration
  "parse": {                      // how to read a sample from a line
    "kind": "csv_idx",            // "csv_idx" | "regex"
    "index": 0                    // used when kind=csv_idx
    // or: "kind": "regex", "pattern": "F:(-?[0-9.]+)"
  },
  "calibration": {                // convert raw to engineering units
    "kind": "linear",             // y = a*x + b
    "a": 1.0,
    "b": 0.0
  },
  "sample_rate_hz": 50,
  "duration_s": 10
}

Usage:
    python -m tap_tone_pi.capture.loadcell_serial \\
        --config config/devices/loadcell_example.json \\
        --out out/run/load_series.json

Migration:
    # Old path (deprecated)
    python modes/acquisition/loadcell_serial.py --config ... --out ...
    
    # New path (v2.0.0+)
    python -m tap_tone_pi.capture.loadcell_serial --config ... --out ...
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
from typing import Any, Dict, Optional

import serial  # pyserial


def parse_line(line: str, parse_cfg: Dict[str, Any]) -> Optional[float]:
    """Parse a value from a serial line based on config."""
    kind = parse_cfg.get("kind", "csv_idx")

    if kind == "csv_idx":
        idx = int(parse_cfg.get("index", 0))
        parts = [p.strip() for p in line.split(",")]
        if idx >= len(parts):
            return None
        try:
            return float(parts[idx])
        except ValueError:
            return None

    elif kind == "regex":
        pattern = re.compile(parse_cfg["pattern"])
        match = pattern.search(line)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    return None


def calibrate(raw: float, calib: Dict[str, Any]) -> float:
    """Apply calibration to raw value."""
    if not calib:
        return raw
    if calib.get("kind") == "linear":
        a = calib.get("a", 1.0)
        b = calib.get("b", 0.0)
        return a * raw + b
    return raw


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Capture load cell data to load_series.json"
    )
    ap.add_argument(
        "--config", required=True, help="JSON config file for the load cell"
    )
    ap.add_argument(
        "--out", required=True, help="Output JSON path (load_series.json)"
    )
    args = ap.parse_args()

    # Load config
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    port = cfg["port"]
    baud = cfg.get("baud", 115200)
    timeout_s = cfg.get("timeout_s", 0.2)
    unit = cfg.get("unit", "N")
    parse_cfg = cfg.get("parse", {"kind": "csv_idx", "index": 0})
    calib = cfg.get("calibration", {"kind": "linear", "a": 1.0, "b": 0.0})
    sample_rate_hz = float(cfg.get("sample_rate_hz", 50))
    duration_s = float(cfg.get("duration_s", 10))
    n_max = int(max(1, sample_rate_hz * duration_s))

    # Open serial port
    ser = serial.Serial(port, baud, timeout=timeout_s)
    t0 = time.time()
    rows = []

    print(f"Capturing from {port} @ {baud} baud for {duration_s}s...")

    try:
        while len(rows) < n_max:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            raw = parse_line(line, parse_cfg)
            if raw is None:
                continue

            val = calibrate(raw, calib)
            t = time.time() - t0
            rows.append([round(t, 5), float(val)])

            # Progress indicator
            if len(rows) % 50 == 0:
                print(f"  {len(rows)} samples...")

    except KeyboardInterrupt:
        print("\nCapture interrupted by user.")
    finally:
        ser.close()

    # Write output
    out = {
        "artifact_type": "load_series",
        "unit": unit,
        "sample_rate_hz": sample_rate_hz,
        "ts_utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t0))),
        "n_samples": len(rows),
        "data": rows,
    }

    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote {args.out} ({len(rows)} samples)")


if __name__ == "__main__":
    main()
