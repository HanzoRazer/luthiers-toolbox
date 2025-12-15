#!/usr/bin/env python
"""Convert Saw Lab materials CSV to JSON format.

Usage:
    python scripts/materials_csv_to_json.py <input.csv> <output.json>

The CSV must have columns:
    id, name, density_kg_per_m3, burn_tendency, tearout_tendency, hardness_scale

Output JSON structure:
    {
      "materials": [
        {
          "id": "hardwood_maple",
          "name": "Maple (Hardwood)",
          "density_kg_per_m3": 700.0,
          "burn_tendency": 0.5,
          "tearout_tendency": 0.5,
          "hardness_scale": 0.6
        },
        ...
      ]
    }
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def convert_materials_csv_to_json(csv_path: Path, json_path: Path) -> None:
    """
    Convert a materials CSV file to JSON format.
    
    CSV columns: id, name, density_kg_per_m3, burn_tendency, tearout_tendency, hardness_scale
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    materials: List[Dict[str, Any]] = []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            material = {
                "id": row.get("id", "").strip(),
                "name": row.get("name", "").strip(),
                "density_kg_per_m3": _parse_float(row.get("density_kg_per_m3", "0")),
                "burn_tendency": _parse_float(row.get("burn_tendency", "0")),
                "tearout_tendency": _parse_float(row.get("tearout_tendency", "0")),
                "hardness_scale": _parse_float(row.get("hardness_scale", "0")),
            }
            materials.append(material)

    payload = {"materials": materials}

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _parse_float(value: str) -> float:
    """Safely parse a float value, returning 0.0 on failure."""
    try:
        return float(value.strip()) if value.strip() else 0.0
    except (ValueError, TypeError):
        return 0.0


def main(argv: List[str]) -> None:
    if len(argv) != 3:
        print(
            "Usage: materials_csv_to_json.py <input.csv> <output.json>",
            file=sys.stderr,
        )
        raise SystemExit(1)

    csv_path = Path(argv[1]).resolve()
    json_path = Path(argv[2]).resolve()

    convert_materials_csv_to_json(csv_path, json_path)
    print(f"Wrote materials JSON to: {json_path}")


if __name__ == "__main__":
    main(sys.argv)
