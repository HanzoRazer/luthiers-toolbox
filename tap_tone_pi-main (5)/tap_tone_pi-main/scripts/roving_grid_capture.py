#!/usr/bin/env python3
"""
roving_grid_capture.py — Point-by-point 2-channel capture for ODS grid measurement.

Physical setup:
- Channel 0: Reference sensor (fixed position)
- Channel 1: Roving sensor (moved point-to-point)
- Excitation: Speaker-driven chirp or sine sweep (external)

Outputs per point:
- points/<point_id>/audio.wav (2-channel)
- points/<point_id>/capture_meta.json

Usage:
    # Interactive mode (prompts for each point)
    python scripts/roving_grid_capture.py capture \
        --grid config/grids/example_grid.json \
        --device 3 --seconds 3 --sample-rate 48000 \
        --out ./captures/grid_run_001

    # Single point (for automation)
    python scripts/roving_grid_capture.py point \
        --point-id A1 --x 0 --y 0 \
        --device 3 --seconds 3 --sample-rate 48000 \
        --out ./captures/grid_run_001
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import sounddevice as sd

# Canonical WAV I/O
from modes._shared.wav_io import write_wav_2ch


@dataclass
class GridPoint:
    """A single point in the measurement grid."""
    id: str
    x: float
    y: float


def load_grid(path: str) -> tuple[str, str, List[GridPoint]]:
    """Load grid definition from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    units = data.get("units", "mm")
    origin = data.get("origin", "unspecified")
    points = [GridPoint(id=p["id"], x=p["x"], y=p["y"]) for p in data["points"]]
    return units, origin, points


def list_devices() -> List[Dict[str, Any]]:
    """List available audio devices."""
    devs = sd.query_devices()
    out: List[Dict[str, Any]] = []
    for i, d in enumerate(devs):
        out.append({
            "index": i,
            "name": d.get("name"),
            "max_input_channels": int(d.get("max_input_channels") or 0),
            "default_samplerate": d.get("default_samplerate"),
        })
    return out


def capture_2ch(
    device: int,
    sample_rate: int,
    seconds: float,
) -> np.ndarray:
    """
    Capture 2-channel synchronized audio.
    
    Returns:
        np.ndarray of shape (n_samples, 2), float32 in [-1, 1]
    """
    sd.default.samplerate = sample_rate
    sd.default.device = (device, None)
    
    n_samples = int(sample_rate * seconds)
    audio = sd.rec(frames=n_samples, channels=2, dtype="float32", blocking=True)
    audio = np.nan_to_num(audio, nan=0.0)
    return audio


def save_point_capture(
    out_dir: Path,
    point: GridPoint,
    audio: np.ndarray,
    sample_rate: int,
    units: str,
    origin: str,
    device_info: Optional[Dict[str, Any]] = None,
) -> Path:
    """Save captured audio and metadata for a single point."""
    point_dir = out_dir / "points" / point.id
    point_dir.mkdir(parents=True, exist_ok=True)
    
    # Save audio as 2-channel WAV using canonical layer
    audio_path = point_dir / "audio.wav"
    write_wav_2ch(audio_path, sample_rate, audio[:, 0], audio[:, 1])
    
    # Save metadata
    meta = {
        "artifact_type": "grid_point_capture",
        "point_id": point.id,
        "position": {"x": point.x, "y": point.y, "units": units},
        "origin": origin,
        "sample_rate": sample_rate,
        "channels": 2,
        "channel_map": {"0": "reference", "1": "roving"},
        "n_samples": audio.shape[0],
        "duration_s": audio.shape[0] / sample_rate,
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rms_ch0": float(np.sqrt(np.mean(audio[:, 0] ** 2))),
        "rms_ch1": float(np.sqrt(np.mean(audio[:, 1] ** 2))),
        "clipped_ch0": bool(np.any(np.abs(audio[:, 0]) >= 0.999)),
        "clipped_ch1": bool(np.any(np.abs(audio[:, 1]) >= 0.999)),
    }
    if device_info:
        meta["device"] = device_info
    
    meta_path = point_dir / "capture_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    
    return point_dir


def cmd_devices(_args: argparse.Namespace) -> int:
    """List audio devices."""
    devs = list_devices()
    print("Available audio devices (2+ input channels for stereo capture):")
    for d in devs:
        marker = "✓" if d["max_input_channels"] >= 2 else " "
        print(f"  [{d['index']}] {marker} {d['name']} (in={d['max_input_channels']})")
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    """Interactive grid capture - prompts for each point."""
    units, origin, points = load_grid(args.grid)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save grid definition to output
    grid_copy = out_dir / "grid.json"
    with open(args.grid, "r", encoding="utf-8") as f:
        grid_data = json.load(f)
    with open(grid_copy, "w", encoding="utf-8") as f:
        json.dump(grid_data, f, indent=2)
    
    device_info = {"index": args.device, "sample_rate": args.sample_rate}
    
    print(f"Grid capture: {len(points)} points")
    print(f"Output: {out_dir}")
    print(f"Device: {args.device}, Rate: {args.sample_rate} Hz, Duration: {args.seconds}s")
    print("-" * 40)
    
    captured = []
    for i, point in enumerate(points):
        print(f"\n[{i+1}/{len(points)}] Point {point.id} at ({point.x}, {point.y}) {units}")
        input("  Position roving sensor, then press ENTER to capture...")
        
        print("  Capturing...", end="", flush=True)
        audio = capture_2ch(args.device, args.sample_rate, args.seconds)
        print(" done.")
        
        point_dir = save_point_capture(
            out_dir, point, audio, args.sample_rate, units, origin, device_info
        )
        captured.append(point.id)
        
        rms0 = np.sqrt(np.mean(audio[:, 0] ** 2))
        rms1 = np.sqrt(np.mean(audio[:, 1] ** 2))
        print(f"  Saved: {point_dir}")
        print(f"  RMS: ref={rms0:.4f}, roving={rms1:.4f}")
    
    # Write capture summary
    summary = {
        "artifact_type": "grid_capture_summary",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "grid_source": args.grid,
        "n_points": len(points),
        "captured_points": captured,
        "sample_rate": args.sample_rate,
        "seconds_per_point": args.seconds,
        "device": device_info,
    }
    with open(out_dir / "capture_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nCapture complete: {len(captured)} points")
    return 0


def cmd_point(args: argparse.Namespace) -> int:
    """Capture a single point (for automation)."""
    out_dir = Path(args.out)
    point = GridPoint(id=args.point_id, x=args.x, y=args.y)
    
    print(f"Capturing point {point.id} at ({point.x}, {point.y})...")
    audio = capture_2ch(args.device, args.sample_rate, args.seconds)
    
    device_info = {"index": args.device, "sample_rate": args.sample_rate}
    point_dir = save_point_capture(
        out_dir, point, audio, args.sample_rate,
        units=args.units, origin="manual", device_info=device_info
    )
    
    print(f"Saved: {point_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="roving_grid_capture",
        description="Point-by-point 2-channel capture for ODS grid measurement",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    
    # devices
    p_dev = sub.add_parser("devices", help="List audio devices")
    p_dev.set_defaults(fn=cmd_devices)
    
    # capture (interactive grid)
    p_cap = sub.add_parser("capture", help="Interactive grid capture")
    p_cap.add_argument("--grid", required=True, help="Grid definition JSON")
    p_cap.add_argument("--device", type=int, required=True, help="Audio device index")
    p_cap.add_argument("--sample-rate", type=int, default=48000)
    p_cap.add_argument("--seconds", type=float, default=3.0)
    p_cap.add_argument("--out", required=True, help="Output directory")
    p_cap.set_defaults(fn=cmd_capture)
    
    # point (single point)
    p_pt = sub.add_parser("point", help="Capture single point")
    p_pt.add_argument("--point-id", required=True)
    p_pt.add_argument("--x", type=float, required=True)
    p_pt.add_argument("--y", type=float, required=True)
    p_pt.add_argument("--units", default="mm")
    p_pt.add_argument("--device", type=int, required=True)
    p_pt.add_argument("--sample-rate", type=int, default=48000)
    p_pt.add_argument("--seconds", type=float, default=3.0)
    p_pt.add_argument("--out", required=True)
    p_pt.set_defaults(fn=cmd_point)
    
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
