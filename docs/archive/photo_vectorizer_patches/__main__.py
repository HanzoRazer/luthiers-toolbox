"""Command-line entry point.

Usage
-----
  python -m code_quality /path/to/project [options]

Options
-------
  --severity LEVEL[,LEVEL]  Filter by severity: critical, warning, info
                            Default: show all
  --summary                 Show counts only, not individual issues
  --changed-only            Only analyze git-changed files
  --fix                     Apply auto-fixes where available
  --workers N               Parallel workers (default: from config or 4)
  --baseline FILE           Suppress issues present in this JSON baseline
  --format {human,json}     Output format (default: human)
  --verbose                 Print progress to stderr
  --exclude-check NAME,...  Skip named checkers
  --save-baseline FILE      Write current issues as a baseline JSON file
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="code_quality",
        description="Static analysis for Vue/TypeScript/Python codebases.",
    )
    parser.add_argument("path", help="Project root to analyze")

    parser.add_argument(
        "--severity",
        metavar="LEVEL[,LEVEL]",
        default=None,
        help="Comma-separated severity levels to report: critical,warning,info",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show aggregated counts only, not individual issues",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Only analyze files changed in git",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply auto-fixes where available",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        metavar="N",
        help="Number of parallel workers (default: from config or 4)",
    )
    parser.add_argument(
        "--baseline",
        metavar="FILE",
        help="Path to baseline JSON — suppress known issues",
    )
    parser.add_argument(
        "--save-baseline",
        metavar="FILE",
        help="Write current issues as a new baseline JSON file",
    )
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format",
    )
    parser.add_argument(
        "--exclude-check",
        metavar="NAME[,NAME]",
        default="",
        help="Comma-separated checker names to skip",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information to stderr",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    project_path = Path(args.path)
    if not project_path.exists():
        print(f"error: path does not exist: {project_path}", file=sys.stderr)
        return 2

    # Parse severity filter
    severity_filter: list[str] | None = None
    if args.severity:
        severity_filter = [s.strip().lower() for s in args.severity.split(",")]
        valid = {"critical", "warning", "info"}
        bad = set(severity_filter) - valid
        if bad:
            print(
                f"error: unknown severity level(s): {', '.join(sorted(bad))}.\n"
                f"       Valid: {', '.join(sorted(valid))}",
                file=sys.stderr,
            )
            return 2

    # Config overrides from CLI flags
    config_overrides: dict = {}
    if args.exclude_check:
        config_overrides["exclude_checks"] = [
            n.strip() for n in args.exclude_check.split(",") if n.strip()
        ]

    from .analyzer import CodeQualityAnalyzer

    analyzer = CodeQualityAnalyzer(
        project_path,
        config_overrides=config_overrides,
        baseline_path=Path(args.baseline) if args.baseline else None,
        changed_only=args.changed_only,
        fix=args.fix,
        workers=args.workers,
        severity_filter=severity_filter,
        verbose=args.verbose,
        summary_only=args.summary,
    )

    issues = analyzer.analyze()

    # Save baseline if requested
    if args.save_baseline:
        save_path = Path(args.save_baseline)
        try:
            save_path.write_text(json.dumps(issues, indent=2), encoding="utf-8")
            print(
                f"Baseline saved: {save_path} ({len(issues)} issues)",
                file=sys.stderr,
            )
        except OSError as exc:
            print(f"error: could not save baseline: {exc}", file=sys.stderr)

    # Output
    if args.summary:
        _print_summary(analyzer.summary(), args.format)
    elif args.format == "json":
        print(json.dumps(issues, indent=2))
    else:
        _print_human(issues, analyzer.summary())

    # Exit code: 0 = clean, 1 = issues found, 2 = error
    return 1 if issues else 0


def _print_human(issues: list, summary_data: dict) -> None:
    if not issues:
        print("✓ No issues found.")
        return

    # Group by file for readable output
    from collections import defaultdict
    by_file: dict[str, list] = defaultdict(list)
    for issue in issues:
        by_file[issue["file"]].append(issue)

    sev_icon = {"critical": "✗", "warning": "⚠", "info": "ℹ"}

    for file_path, file_issues in sorted(by_file.items()):
        print(f"\n{file_path}  ({len(file_issues)} issue(s))")
        print("─" * 60)
        for issue in file_issues:
            icon = sev_icon.get(issue.get("severity", ""), "·")
            print(
                f"  {icon} [{issue['severity']:8s}] "
                f"L{issue['line']:4d}  [{issue['check']}]  {issue['message']}"
            )
            if issue.get("suggestion"):
                print(f"             → {issue['suggestion']}")

    print()
    _print_summary(summary_data, "human")


def _print_summary(summary_data: dict, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(summary_data, indent=2))
        return

    total = summary_data.get("total", 0)
    by_sev = summary_data.get("by_severity", {})
    crit = by_sev.get("critical", 0)
    warn = by_sev.get("warning", 0)
    info = by_sev.get("info", 0)

    print(
        f"Total: {total}  "
        f"({crit} critical, {warn} warnings, {info} info)"
    )
    by_dir = summary_data.get("by_directory", {})
    if by_dir and total:
        print("\nBy directory:")
        for directory, counts in sorted(by_dir.items()):
            c = counts.get("critical", 0)
            w = counts.get("warning", 0)
            i = counts.get("info", 0)
            print(f"  {directory:<50s} {c:3d}c {w:3d}w {i:3d}i")


if __name__ == "__main__":
    sys.exit(main())
