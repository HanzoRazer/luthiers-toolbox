#!/usr/bin/env python3
"""
Consolidated Technical Debt Report Generator

Runs all debt checks and produces a unified markdown report.

Usage:
    python -m app.ci.generate_debt_report [--output FILE]

Output: Markdown report suitable for GitHub artifacts or PR comments.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _repo_root() -> Path:
    """Find repo root."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def run_check(module: str, extra_args: List[str] = None) -> Dict[str, Any]:
    """Run a check module and capture JSON output."""
    args = [sys.executable, "-m", module, "--json"] + (extra_args or [])
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=str(_repo_root() / "services" / "api"),
            timeout=120,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {"error": result.stderr or "No output", "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout", "exit_code": -1}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "exit_code": -1}
    except Exception as e:
        return {"error": str(e), "exit_code": -1}


def get_git_info() -> Dict[str, str]:
    """Get current git commit info."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(_repo_root())
        )
        commit = result.stdout.strip() if result.returncode == 0 else "unknown"

        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(_repo_root())
        )
        branch = result.stdout.strip() if result.returncode == 0 else "unknown"

        return {"commit": commit, "branch": branch}
    except Exception:
        return {"commit": "unknown", "branch": "unknown"}


def generate_report() -> str:
    """Generate consolidated debt report."""
    lines = []
    git_info = get_git_info()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("# Technical Debt Report")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Branch:** {git_info['branch']}")
    lines.append(f"**Commit:** {git_info['commit']}")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Check | Status | Count | Threshold |")
    lines.append("|-------|--------|-------|-----------|")

    checks = []

    # Complexity
    complexity = run_check("app.ci.check_complexity")
    if "error" not in complexity:
        count = len(complexity) if isinstance(complexity, list) else complexity.get("violation_count", 0)
        status = "PASS" if count == 0 else f"WARN ({count} baselined)"
        lines.append(f"| Complexity (>15) | {status} | {count} | 15 |")
        checks.append(("complexity", complexity))
    else:
        lines.append(f"| Complexity | ERROR | - | - |")

    # File sizes
    file_sizes = run_check("app.ci.check_file_sizes")
    if "error" not in file_sizes:
        count = len(file_sizes) if isinstance(file_sizes, list) else file_sizes.get("violation_count", 0)
        status = "PASS" if count == 0 else f"WARN ({count} baselined)"
        lines.append(f"| File size (>500) | {status} | {count} | 500 |")
        checks.append(("file_sizes", file_sizes))
    else:
        lines.append(f"| File size | ERROR | - | - |")

    # Bare except
    bare_except = run_check("app.ci.check_bare_except")
    if "error" not in bare_except:
        count = len(bare_except) if isinstance(bare_except, list) else 0
        status = "PASS" if count == 0 else f"FAIL ({count} violations)"
        lines.append(f"| Bare except | {status} | {count} | 0 |")
        checks.append(("bare_except", bare_except))
    else:
        lines.append(f"| Bare except | ERROR | - | - |")

    # Fence checker
    fence = run_check("app.ci.fence_checker_v2")
    if "error" not in fence:
        count = fence.get("failed", 0)
        status = "PASS" if count == 0 else f"WARN ({count} warnings)"
        lines.append(f"| Safety fences | {status} | {count} | 0 |")
        checks.append(("fence", fence))
    else:
        lines.append(f"| Safety fences | ERROR | - | - |")

    # Duplication
    duplication = run_check("app.ci.check_duplication")
    if "error" not in duplication:
        stats = duplication.get("stats", {})
        count = stats.get("clone_groups", 0)
        dup_lines = stats.get("duplicate_lines", 0)
        status = "PASS" if duplication.get("passed", True) else f"WARN ({count} clones)"
        lines.append(f"| Duplication | {status} | {dup_lines} lines | 50 groups |")
        checks.append(("duplication", duplication))
    else:
        lines.append(f"| Duplication | ERROR | - | - |")

    lines.append("")

    # Detailed sections
    lines.append("## Details")
    lines.append("")

    # Top complexity violations
    if checks:
        for name, data in checks:
            if name == "complexity" and isinstance(data, list) and data:
                lines.append("### Worst Complexity")
                lines.append("")
                lines.append("| Function | Score | File |")
                lines.append("|----------|-------|------|")
                for v in data[:10]:
                    lines.append(f"| `{v.get('function', '?')}` | {v.get('complexity', '?')} | {v.get('file', '?')} |")
                lines.append("")

            if name == "file_sizes" and isinstance(data, list) and data:
                lines.append("### Large Files")
                lines.append("")
                lines.append("| File | Lines | Over By |")
                lines.append("|------|-------|---------|")
                for v in data[:10]:
                    lines.append(f"| {v.get('file', '?')} | {v.get('lines', '?')} | +{v.get('over_by', '?')} |")
                lines.append("")

            if name == "duplication":
                dups = data.get("duplicates", [])
                if dups:
                    lines.append("### Top Duplicates")
                    lines.append("")
                    for dup in dups[:5]:
                        lines.append(f"**Clone group** ({dup.get('count', 0)} copies):")
                        for loc in dup.get("locations", [])[:3]:
                            lines.append(f"- `{loc.get('file')}:{loc.get('start')}-{loc.get('end')}`")
                        lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Generated by `app.ci.generate_debt_report`*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate technical debt report")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")
    args = parser.parse_args()

    report = generate_report()

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
