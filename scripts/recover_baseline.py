#!/usr/bin/env python3
"""
Historical Baseline Recovery Script
====================================

Locates the exact working commit around 04/11/2026 and reproduces
the Melody Maker PDF behavior for comparison.

Usage:
    python scripts/recover_baseline.py --list-candidates
    python scripts/recover_baseline.py --file "Guitar Plans/Gibson-Melody-Maker.pdf"
    python scripts/recover_baseline.py --diff-against HEAD

Author: Production Shop
Date: 2026-04-13
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# Known historical commits around the working 04/11/2026 18:51 timestamp
CANDIDATE_COMMITS = {
    "86c49526": {
        "date": "2026-04-11 01:41:33",
        "message": "fix(blueprint): sync orchestrator and router with production",
        "status": "CANDIDATE - last code change before 18:51 DXF",
    },
    "28bb95d1": {
        "date": "2026-04-11 20:55:46",
        "message": "docs: add vectorizer architecture documentation",
        "status": "docs only - same code as 86c49526",
    },
    "ec9c26af": {
        "date": "2026-04-12 13:49:31",
        "message": "fix(async): treat non-accept blueprint results as COMPLETE",
        "status": "last commit before hierarchy regression",
    },
    "f49ead1d": {
        "date": "2026-04-12 15:42:22",
        "message": "feat(vectorizer): hierarchy-based contour isolation + debug overlay",
        "status": "REGRESSION INTRODUCED - do not use",
    },
}

# The target historical commit for restoration
HISTORICAL_TARGET = "86c49526"


@dataclass
class CandidateResult:
    """Result from running a file against a candidate commit."""
    commit: str
    commit_date: str
    file_path: str
    success: bool
    artifacts_present: bool
    svg_present: bool
    dxf_present: bool
    dimensions_mm: tuple[float, float]
    chains_found: int
    contours_found: int
    recommendation_action: str
    selection_score: float
    warnings: list[str]
    error: str
    is_page_border_fallback: bool
    notes: str


def list_candidate_commits(after: str = "2026-04-10", before: str = "2026-04-13") -> list[dict]:
    """
    List candidate commits in the recovery time window.

    Uses git log to find commits between the specified dates.
    """
    cmd = [
        "git", "log",
        f"--after={after}",
        f"--before={before}",
        "--format=%H|%ad|%s",
        "--date=iso",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running git log: {result.stderr}")
        return []

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            sha, date, msg = parts
            status = CANDIDATE_COMMITS.get(sha[:8], {}).get("status", "")
            commits.append({
                "sha": sha,
                "sha_short": sha[:8],
                "date": date,
                "message": msg,
                "status": status,
            })

    return commits


def diff_against_commit(target_commit: str, files: list[str] = None) -> str:
    """
    Generate diff between target commit and HEAD for specified files.

    If files is None, diffs the critical blueprint pipeline files.
    """
    if files is None:
        files = [
            "services/photo-vectorizer/edge_to_dxf.py",
            "services/api/app/services/blueprint_extract.py",
            "services/api/app/services/blueprint_clean.py",
            "services/api/app/services/contour_scoring.py",
            "services/api/app/services/blueprint_orchestrator.py",
        ]

    diff_output = []
    for file_path in files:
        cmd = ["git", "diff", f"{target_commit}..HEAD", "--", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            diff_output.append(f"\n{'='*60}\n{file_path}\n{'='*60}\n")
            diff_output.append(result.stdout)

    return "".join(diff_output)


def get_diff_stats(target_commit: str) -> dict:
    """Get summary statistics of changes since target commit."""
    cmd = ["git", "diff", f"{target_commit}..HEAD", "--stat"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    stats = {
        "files_changed": 0,
        "insertions": 0,
        "deletions": 0,
        "critical_files": {},
    }

    critical_files = [
        "edge_to_dxf.py",
        "blueprint_extract.py",
        "blueprint_clean.py",
        "contour_scoring.py",
        "blueprint_orchestrator.py",
    ]

    for line in result.stdout.split("\n"):
        for cf in critical_files:
            if cf in line:
                stats["critical_files"][cf] = line.strip()

    # Parse summary line
    for line in result.stdout.split("\n"):
        if "files changed" in line or "file changed" in line:
            parts = line.split(",")
            for part in parts:
                if "files changed" in part or "file changed" in part:
                    stats["files_changed"] = int(part.strip().split()[0])
                elif "insertion" in part:
                    stats["insertions"] = int(part.strip().split()[0])
                elif "deletion" in part:
                    stats["deletions"] = int(part.strip().split()[0])

    return stats


def generate_recovery_report(commits: list[dict], diff_stats: dict) -> str:
    """Generate markdown recovery report."""
    report = []
    report.append("# Historical Baseline Recovery Report")
    report.append(f"\nGenerated: {datetime.now().isoformat()}")
    report.append(f"\nTarget Historical Commit: `{HISTORICAL_TARGET}`")

    report.append("\n## Candidate Commits")
    report.append("\n| SHA | Date | Message | Status |")
    report.append("|-----|------|---------|--------|")
    for c in commits:
        status = c.get("status", "")
        if "REGRESSION" in status:
            status = f"**{status}**"
        report.append(f"| `{c['sha_short']}` | {c['date'][:19]} | {c['message'][:50]} | {status} |")

    report.append("\n## Diff Statistics vs HEAD")
    report.append(f"\n- Files changed: {diff_stats['files_changed']}")
    report.append(f"- Insertions: {diff_stats['insertions']}")
    report.append(f"- Deletions: {diff_stats['deletions']}")

    if diff_stats['critical_files']:
        report.append("\n### Critical File Changes")
        for name, line in diff_stats['critical_files'].items():
            report.append(f"- `{name}`: {line}")

    report.append("\n## Historical Behavior Summary")
    report.append("""
At commit `86c49526` (the working state):

### edge_to_dxf.py
- `convert()` has NO `isolate_body` parameter
- Uses `cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)`
- NO hierarchy handling
- NO border removal
- NO grouping
- ALL valid contours (>= 3 points) are converted to LINE entities

### blueprint_clean.py
- NO `_remove_page_border_chains()` function
- NO 5-tier fallback ladder
- Simple scoring with `score_contours()`
- Single-pass fallback: find first chain that passes length/closure filters
- NO `cv2` import (no border detection at cleanup stage)

## Regression Root Cause

Commit `f49ead1d` introduced hierarchy-based isolation that:
1. Uses `RETR_TREE` instead of `RETR_LIST`
2. Adds `_remove_page_borders_early()` which nullifies border contours
3. Adds `_isolate_with_grouping()` which filters to winning group only
4. Adds cleanup-stage border removal

When the body contour is fragmented, this filtering removes everything except
the page border, causing the regression.
""")

    report.append("\n## Restoration Plan")
    report.append("""
1. Add `CleanupMode.RESTORED_BASELINE` enum value
2. In `edge_to_dxf.py`: bypass `isolate_body` logic, use `RETR_LIST`
3. In `blueprint_clean.py`: bypass border removal and tier system
4. Propagate mode through orchestrator and routers
5. Benchmark against Melody Maker PDF
""")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Historical baseline recovery utility")
    parser.add_argument("--list-candidates", action="store_true", help="List candidate commits")
    parser.add_argument("--diff-against", type=str, help="Show diff against specified commit (default: HEAD)")
    parser.add_argument("--generate-report", action="store_true", help="Generate recovery report")
    parser.add_argument("--target", type=str, default=HISTORICAL_TARGET, help="Target commit SHA")
    parser.add_argument("--output-dir", type=str, default="artifacts/recovery", help="Output directory")

    args = parser.parse_args()

    if args.list_candidates:
        commits = list_candidate_commits()
        print("\nCandidate Commits for Recovery:")
        print("-" * 80)
        for c in commits:
            status = c.get("status", "")
            marker = " <-- TARGET" if c["sha_short"] == HISTORICAL_TARGET else ""
            marker = " <-- REGRESSION" if "REGRESSION" in status else marker
            print(f"{c['sha_short']} | {c['date'][:19]} | {c['message'][:40]}{marker}")
        return

    if args.diff_against or args.generate_report:
        target = args.diff_against or args.target
        print(f"\nAnalyzing diff between {target} and HEAD...")

        diff_stats = get_diff_stats(target)
        print(f"\nDiff Statistics:")
        print(f"  Files changed: {diff_stats['files_changed']}")
        print(f"  Insertions: {diff_stats['insertions']}")
        print(f"  Deletions: {diff_stats['deletions']}")

        if diff_stats['critical_files']:
            print(f"\nCritical file changes:")
            for name, line in diff_stats['critical_files'].items():
                print(f"  {name}: {line}")

        if args.generate_report:
            commits = list_candidate_commits()
            report = generate_recovery_report(commits, diff_stats)

            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            report_path = output_dir / "recovery_report.md"
            report_path.write_text(report)
            print(f"\nReport written to: {report_path}")

            # Also write candidate info as JSON
            candidates_path = output_dir / "recovery_candidates.json"
            candidates_path.write_text(json.dumps({
                "target_commit": HISTORICAL_TARGET,
                "candidates": CANDIDATE_COMMITS,
                "commits": commits,
                "diff_stats": diff_stats,
            }, indent=2))
            print(f"Candidates written to: {candidates_path}")

        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
