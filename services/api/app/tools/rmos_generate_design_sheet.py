"""
RMOS Design Sheet Generator CLI (MM-3)

Command-line tool to generate PDF design sheets from JSON files.

Usage:
    python -m app.tools.rmos_generate_design_sheet \
        --plan-json data/rmos/plans/my_plan.json \
        --strip-family-json data/rmos/strip_families/my_family.json \
        --out exports/design_sheets/my_sheet.pdf
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from ..core.rosette_design_sheet import generate_rosette_design_sheet


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file and return dict."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a PDF design sheet for a mixed-material rosette."
    )
    parser.add_argument(
        "--plan-json", 
        type=Path, 
        required=True, 
        help="Path to rosette plan JSON"
    )
    parser.add_argument(
        "--strip-family-json", 
        type=Path, 
        required=True, 
        help="Path to strip family JSON (single object)"
    )
    parser.add_argument(
        "--machine-defaults-json",
        type=Path,
        help="Optional path to machine defaults JSON (spindle, feed, plunge, stepdown)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output PDF file path (will be suffixed with .pdf if not present)",
    )
    args = parser.parse_args()

    print(f"Loading plan from: {args.plan_json}")
    plan = _load_json(args.plan_json)
    
    print(f"Loading strip family from: {args.strip_family_json}")
    strip_family = _load_json(args.strip_family_json)
    
    machine_defaults = {}
    if args.machine_defaults_json:
        print(f"Loading machine defaults from: {args.machine_defaults_json}")
        machine_defaults = _load_json(args.machine_defaults_json)

    print(f"Generating design sheet...")
    output_path = generate_rosette_design_sheet(plan, strip_family, machine_defaults, args.out)
    print(f"✓ Design sheet written to: {output_path}")


if __name__ == "__main__":
    main()
