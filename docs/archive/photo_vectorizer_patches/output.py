"""Output formatters.

Provides human-readable and machine-readable (JSON) output modes.
Both formatters consume the same issue list produced by the analyzer.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, TextIO


_SEV_ICONS = {
    "critical": "✗",
    "warning":  "⚠",
    "info":     "ℹ",
}

_SEV_ORDER = {"critical": 0, "warning": 1, "info": 2}


def print_human(
    issues: List[Dict[str, Any]],
    summary_data: Dict[str, Any],
    *,
    out: TextIO = sys.stdout,
    summary_only: bool = False,
) -> None:
    if not issues:
        print("✓ No issues found.", file=out)
        return

    if not summary_only:
        by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for issue in issues:
            by_file[issue["file"]].append(issue)

        for file_path in sorted(by_file):
            file_issues = sorted(
                by_file[file_path],
                key=lambda x: (_SEV_ORDER.get(x.get("severity", "info"), 99), x["line"]),
            )
            print(f"\n{file_path}  ({len(file_issues)} issue(s))", file=out)
            print("─" * 70, file=out)
            for issue in file_issues:
                icon = _SEV_ICONS.get(issue.get("severity", ""), "·")
                print(
                    f"  {icon} [{issue['severity']:8s}] "
                    f"L{issue['line']:4d}  [{issue['check']}]  {issue['message']}",
                    file=out,
                )
                if issue.get("suggestion"):
                    print(f"             → {issue['suggestion']}", file=out)

        print(file=out)

    _print_summary_human(summary_data, out=out)


def _print_summary_human(summary_data: Dict[str, Any], *, out: TextIO = sys.stdout) -> None:
    total = summary_data.get("total", 0)
    by_sev = summary_data.get("by_severity", {})
    crit = by_sev.get("critical", 0)
    warn = by_sev.get("warning", 0)
    info = by_sev.get("info", 0)

    print(
        f"Total: {total}  ({crit} critical, {warn} warnings, {info} info)",
        file=out,
    )

    by_dir = summary_data.get("by_directory", {})
    if by_dir and total:
        print("\nBy directory:", file=out)
        for directory, counts in sorted(by_dir.items()):
            c = counts.get("critical", 0)
            w = counts.get("warning", 0)
            i_count = counts.get("info", 0)
            print(
                f"  {directory:<55s}  {c:3d}c  {w:4d}w  {i_count:4d}i",
                file=out,
            )


def print_json(
    issues: List[Dict[str, Any]],
    summary_data: Dict[str, Any],
    *,
    out: TextIO = sys.stdout,
    summary_only: bool = False,
) -> None:
    if summary_only:
        print(json.dumps(summary_data, indent=2), file=out)
    else:
        print(
            json.dumps({"summary": summary_data, "issues": issues}, indent=2),
            file=out,
        )
