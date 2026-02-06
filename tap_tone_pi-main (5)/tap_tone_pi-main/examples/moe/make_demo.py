#!/usr/bin/env python3
from __future__ import annotations
"""
Hardware-free MOE demo:
Creates out/DEMO/moe/moe_result.json conforming to moe_result.schema.json.
This is a minimal "facts-only" artifact for CI validation (no hardware).
"""
import json
from pathlib import Path
from datetime import datetime, timezone

OUT = Path("out/DEMO/moe")

def now():
    return datetime.now(timezone.utc).isoformat()

def write_json(p: Path, d: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")

def main():
    art = {
        "schema_id": "moe_result",
        "schema_version": "1.0",
        "artifact_type": "bending_moe",
        "created_utc": now(),
        "specimen_id": "DEMO_BAR_001",
        "method": "3PT",
        "span_mm": 400.0,
        "width_mm": 20.0,
        "thickness_mm": 3.0,
        "E_GPa": 10.8,
        "EI_Nmm2": 175000.0,
        "inputs": {
            "load_series_path": "demo_load.csv",
            "displacement_series_path": "demo_disp.csv",
            "load_series_sha256": "0"*64,
            "displacement_series_sha256": "0"*64,
            "merge_pairs_csv": "demo_pairs.csv"
        },
        "environment": {
            "temp_C": 22.0,
            "rh_pct": 45.0
        }
    }
    outp = OUT/"moe_result.json"
    write_json(outp, art)
    print(f"MOE demo written: {outp}")

if __name__ == "__main__":
    main()
