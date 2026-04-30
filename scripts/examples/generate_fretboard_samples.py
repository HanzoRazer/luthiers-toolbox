#!/usr/bin/env python
"""Generate canonical fretboard ecosphere sample outputs.

PREREQUISITE: API server must be running on localhost:8000.
Start it from the repo root with:

    cd services/api
    uvicorn app.main:app --port 8000

Then run this script from the repo root:

    python scripts/examples/generate_fretboard_samples.py

Output: three JSON files in data/ecosphere_samples/ representing
distinct code paths through the ecosphere builder:

  single_scale_fender_strat.json     - Single-scale 25.5" 12-TET
  fan_fret_smart_guitar_pro.json     - Fan-fret 686/648mm 12-TET
  custom_temperament_pythagorean.json - Pythagorean 12-fret octave
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen


SAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "ecosphere_samples"
API_BASE = "http://localhost:8000/api/v1/fretboard"


SAMPLES = [
    ("single_scale_fender_strat.json", {
        "scale_length_mm": 647.7,
        "fret_count": 22,
        "temperament": "equal_12",
        "string_count": 6,
        "slot_width_mm": 0.58,
    }),
    ("fan_fret_smart_guitar_pro.json", {
        "scale_type": "multiscale",
        "bass_scale_length_mm": 686.0,
        "scale_length_mm": 648.0,
        "fret_count": 24,
        "temperament": "equal_12",
        "string_count": 6,
        "slot_width_mm": 0.58,
        "perpendicular_fret": 12,
    }),
    ("custom_temperament_pythagorean.json", {
        "scale_length_mm": 647.7,
        "fret_count": 12,
        "temperament": "pythagorean",
        "string_count": 6,
        "slot_width_mm": 0.58,
    }),
]


def fetch_ecosphere(payload: dict) -> dict:
    """POST to /compute and return the ecosphere JSON."""
    req = Request(
        f"{API_BASE}/compute",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    for filename, payload in SAMPLES:
        print(f"Generating {filename}...")
        eco = fetch_ecosphere(payload)
        out_path = SAMPLES_DIR / filename
        out_path.write_text(json.dumps(eco, indent=2) + "\n")
        print(f"  -> {out_path.relative_to(SAMPLES_DIR.parent.parent)} ({out_path.stat().st_size} bytes)")
    print("Done.")


if __name__ == "__main__":
    main()
