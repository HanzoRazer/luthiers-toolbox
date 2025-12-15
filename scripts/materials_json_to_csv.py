#!/usr/bin/env python
"""Convert Saw Lab materials JSON to CSV format.

Usage:
    python scripts/materials_json_to_csv.py <input.json> <output.csv>

Input JSON structure:
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

Output CSV columns:
    id, name, density_kg_per_m3, burn_tendency, tearout_tendency, hardness_scale
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def convert_materials_json_to_csv(json_path: Path, csv_path: Path) -> None:
    """
    Convert a materials JSON file to CSV format.
    
    JSON must have a "materials" array with objects containing:
    id, name, density_kg_per_m3, burn_tendency, tearout_tendency, hardness_scale
    """
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        payload: Dict[str, Any] = json.load(f)

    materials: List[Dict[str, Any]] = payload.get("materials", [])
    if not isinstance(materials, list):
        raise ValueError("JSON is missing a 'materials' list")

    fieldnames = [
        "id",
        "name",
        "density_kg_per_m3",
        "burn_tendency",
        "tearout_tendency",
        "hardness_scale",
    ]

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for m in materials:
            row = {
                "id": m.get("id", ""),
                "name": m.get("name", ""),
                "density_kg_per_m3": m.get("density_kg_per_m3", ""),
                "burn_tendency": m.get("burn_tendency", ""),
                "tearout_tendency": m.get("tearout_tendency", ""),
                "hardness_scale": m.get("hardness_scale", ""),
            }
            writer.writerow(row)


def main(argv: List[str]) -> None:
    if len(argv) != 3:
        print(
            "Usage: materials_json_to_csv.py <input.json> <output.csv>",
            file=sys.stderr,
        )
        raise SystemExit(1)

    json_path = Path(argv[1]).resolve()
    csv_path = Path(argv[2]).resolve()

    convert_materials_json_to_csv(json_path, csv_path)
    print(f"Wrote materials CSV to: {csv_path}")


if __name__ == "__main__":
    main(sys.argv)
