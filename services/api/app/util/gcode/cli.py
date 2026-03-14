"""
G-code CLI

Command-line interface for G-code analysis and summarization.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .reader import parse_gcode
from .report import print_report, write_csv, write_json


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for G-code reader."""
    p = argparse.ArgumentParser(
        description="Read & summarize a G-code (.nc/.gcode) file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s program.nc --pretty
  %(prog)s program.nc --validate --json summary.json
  %(prog)s program.nc --csv moves.csv --json summary.json

Integration with The Production Shop:
  This tool is integrated into server/pipelines/gcode_explainer/ for
  automated G-code analysis in CAM workflows.
        """
    )
    p.add_argument("file", help="Path to .nc or .gcode file")
    p.add_argument("--csv", help="Optional CSV path to write motion path")
    p.add_argument("--json", help="Optional JSON path to write summary")
    p.add_argument("--pretty", action="store_true", help="Print extra motion listing with enhanced formatting")
    p.add_argument("--validate", action="store_true", help="Run safety validation checks (speeds, coordinates, etc.)")
    p.add_argument("--quiet", action="store_true", help="Suppress report output (useful with --json)")
    args = p.parse_args(argv)

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}", file=sys.stderr)
        return 1

    summary, moves = parse_gcode(args.file, pretty=args.pretty, validate=args.validate)

    if not args.quiet:
        print_report(summary, moves, pretty=args.pretty)

    if args.csv:
        write_csv(args.csv, moves)
        print(f"\nCSV path written: {args.csv} ({len(moves)} rows)")
    if args.json:
        write_json(args.json, summary)
        print(f"JSON summary written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
