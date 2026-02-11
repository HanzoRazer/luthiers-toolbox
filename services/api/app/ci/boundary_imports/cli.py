"""CLI entry point for boundary import checker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from .baseline import load_baseline, serialize
from .core import check_boundaries
from .reporter import has_violations, print_baseline_delta, print_report, sort_imports, sort_symbols


def parse_args(argv: List[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    p = argparse.ArgumentParser(
        prog="python -m app.ci.check_boundary_imports",
        description="Fence-aware boundary import checker for ToolBox API",
    )
    p.add_argument(
        "--profile",
        type=str,
        default="toolbox",
        help="Profile name (currently only 'toolbox' is supported).",
    )
    p.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Path to baseline JSON. If provided, fail only on NEW violations vs baseline.",
    )
    p.add_argument(
        "--write-baseline",
        type=str,
        default=None,
        help="Write current violations to baseline JSON and exit 0.",
    )
    return p.parse_args(argv)


def main() -> int:
    """Main entry point for boundary import checker."""
    try:
        args = parse_args(sys.argv[1:])
        import_violations, symbol_violations = check_boundaries()
    except Exception as e:
        print(f"Boundary checker error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 3

    import_violations = sort_imports(import_violations)
    symbol_violations = sort_symbols(symbol_violations)

    current = serialize(import_violations, symbol_violations)

    # 1) Write baseline mode (always exit 0)
    if args.write_baseline:
        path = Path(args.write_baseline)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote baseline: {path}")
        print(f"  imports: {len(current['imports'])}")
        print(f"  symbols: {len(current['symbols'])}")
        return 0

    # 2) Baseline compare mode (fail only on NEW)
    if args.baseline:
        bpath = Path(args.baseline)
        if not bpath.exists():
            print(f"Baseline not found: {bpath}", file=sys.stderr)
            print("Tip: generate it with --write-baseline <path>", file=sys.stderr)
            return 3
        try:
            baseline = load_baseline(bpath)
        except (OSError, json.JSONDecodeError, ValueError) as e:
            print(f"Failed to read baseline {bpath}: {e}", file=sys.stderr)
            return 3

        b_imports = set(baseline.get("imports", []))
        b_symbols = set(baseline.get("symbols", []))
        c_imports = set(current.get("imports", []))
        c_symbols = set(current.get("symbols", []))

        new_imports = c_imports - b_imports
        new_symbols = c_symbols - b_symbols

        if new_imports or new_symbols:
            print_baseline_delta(baseline, current, baseline_path=bpath)
            return 2

        # All good: no NEW violations (resolved ones are fine)
        resolved_imports = len(b_imports - c_imports)
        resolved_symbols = len(b_symbols - c_symbols)
        print("Boundary import check: OK (baseline mode)")
        if resolved_imports or resolved_symbols:
            print(f"  resolved since baseline: imports={resolved_imports} symbols={resolved_symbols}")
        return 0

    # 3) Default strict mode (fail on any violation)
    if has_violations(import_violations, symbol_violations):
        print_report(import_violations, symbol_violations)
        return 2

    print("Boundary import check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
