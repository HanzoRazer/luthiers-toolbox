#!/usr/bin/env python3
"""
Hardware-free Phase-2 ODS demo:
Creates runs_phase2/DEMO/session_0001/ with canonical filenames.
This is a minimal "facts-only" artifact set for CI validation (no hardware).
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
import sys

# Ensure repo root is in path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from modes._shared.wav_io import write_wav_2ch

OUT = Path("runs_phase2/DEMO/session_0001")
FS = 48000
DUR = 1.0


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(p: Path, d: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")


def synth_2ch(freq: float = 200.0):
    """Generate 2-channel test signal (ref + roving)."""
    n = int(FS * DUR)
    t = np.arange(n, dtype=np.float32) / FS
    # Reference: clean sine
    ref = 0.3 * np.sin(2 * np.pi * freq * t)
    # Roving: same + slight phase shift + noise
    rov = 0.25 * np.sin(2 * np.pi * freq * t + 0.3) + 0.02 * np.random.randn(n).astype(np.float32)
    return ref.astype(np.float32), rov.astype(np.float32)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    points_dir = OUT / "points"
    derived_dir = OUT / "derived"
    points_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)

    # Create session metadata (matches phase2_session_meta.schema.json)
    session_meta = {
        "schema_version": "phase2_session_meta_v1",
        "phase": 2,
        "created_at_utc": now(),
        "operator": "DEMO",
        "channel_roles": {"ch0": "reference", "ch1": "roving"},
        "environment": {"temp_c": 22.0, "humidity_rh": 45.0},
    }
    write_json(OUT / "session_meta.json", session_meta)
    print(f"Wrote session_meta.json")

    # Create 3 demo points
    point_ids = ["A1", "A2", "B1"]
    for pid in point_ids:
        pt_dir = points_dir / f"point_{pid}"
        pt_dir.mkdir(parents=True, exist_ok=True)

        # Audio
        ref, rov = synth_2ch(200.0 + hash(pid) % 50)
        write_wav_2ch(str(pt_dir / "audio.wav"), ref, rov, FS)

        # Capture metadata (matches phase2_point_capture_meta.schema.json)
        capture_meta = {
            "schema_version": "phase2_point_capture_meta_v1",
            "point_id": pid,
            "created_at_utc": now(),
            "sample_rate_hz": FS,
            "channels": 2,
            "seconds": DUR,
            "channel_roles": {"ch0": "reference", "ch1": "roving"},
            "excitation": {"type": "tap_impulse"},
        }
        write_json(pt_dir / "capture_meta.json", capture_meta)

    print(f"Wrote {len(point_ids)} point captures")

    # Create minimal ODS snapshot (matches phase2_ods_snapshot.schema.json)
    # Points as array with x_mm, y_mm; capdir and provenance required
    grid_coords = {"A1": (0.0, 0.0), "A2": (50.0, 0.0), "B1": (0.0, 50.0)}
    ods_snapshot = {
        "schema_version": "phase2_ods_snapshot_v2",
        "capdir": str(points_dir),
        "freqs_hz": [100.0, 150.0, 200.0, 250.0],
        "points": [
            {
                "point_id": pid,
                "x_mm": grid_coords[pid][0],
                "y_mm": grid_coords[pid][1],
                "H_mag": [0.5, 0.8, 1.0, 0.6],
                "H_phase_deg": [10.0, 20.0, 30.0, 40.0],
                "coherence": [0.9, 0.95, 0.98, 0.85],
            }
            for pid in point_ids
        ],
        "provenance": {
            "algo_id": "phase2_demo_synth",
            "algo_version": "1.0.0",
            "numpy_version": np.__version__,
            "scipy_version": "1.11.0",
            "computed_at_utc": now(),
        },
    }
    write_json(derived_dir / "ods_snapshot.json", ods_snapshot)
    print(f"Wrote ods_snapshot.json")

    # Create minimal wolf candidates (matches phase2_wolf_candidates.schema.json)
    # Flat thresholds, not nested; provenance required
    wolf_candidates = {
        "schema_version": "phase2_wolf_candidates_v2",
        "wsi_threshold": 0.6,
        "coherence_threshold": 0.7,
        "candidates": [],  # No wolves in demo
        "provenance": {
            "algo_id": "phase2_wsi_demo",
            "algo_version": "1.0.0",
            "numpy_version": np.__version__,
            "computed_at_utc": now(),
        },
    }
    write_json(derived_dir / "wolf_candidates.json", wolf_candidates)
    print(f"Wrote wolf_candidates.json")

    print(f"\nPhase-2 demo complete!")
    print(f"Artifacts under: {OUT}")


if __name__ == "__main__":
    main()
