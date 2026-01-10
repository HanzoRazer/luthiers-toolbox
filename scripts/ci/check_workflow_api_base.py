#!/usr/bin/env python3
"""
Bundle 15: CI gate to prevent hardcoded API base URLs in workflow files.

Scans .github/workflows/**/*.yml for hardcoded API base patterns and fails CI
if any are found (unless explicitly ignored).

Usage:
    python scripts/ci/check_workflow_api_base.py
    python scripts/ci/check_workflow_api_base.py --root .github/workflows
    python scripts/ci/check_workflow_api_base.py --ignore .github/workflows/.api_base_ignore.txt
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Tuple

DEFAULT_SCAN_ROOT = ".github/workflows"
DEFAULT_IGNORE = ".github/workflows/.api_base_ignore.txt"

# Patterns we want to eliminate from workflows
BANNED_TOKENS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://127.0.0.1:8000",
    "https://localhost:8000",
    ":8000/api",
]


def _iter_workflow_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return root.rglob("*.yml")


def _load_ignore(ignore_path: Path) -> List[str]:
    if not ignore_path.exists():
        return []
    out: List[str] = []
    for raw in ignore_path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def _is_ignored(file_rel: str, lineno: int, ignores: List[str]) -> bool:
    key = f"{file_rel}:{lineno}"
    return key in ignores or file_rel in ignores


def _scan_file(path: Path, ignores: List[str]) -> List[Tuple[str, int, str]]:
    rel = path.as_posix()
    findings: List[Tuple[str, int, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    for i, line in enumerate(text.splitlines(), start=1):
        if _is_ignored(rel, i, ignores):
            continue

        # Allow lines that already use API_BASE (bash or GitHub env)
        if "API_BASE" in line or "env.API_BASE" in line:
            continue

        for tok in BANNED_TOKENS:
            if tok in line:
                findings.append((rel, i, line.strip()))
                break

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(
        description="CI gate: prevent hardcoded API base URLs in workflow files"
    )
    ap.add_argument("--root", default=DEFAULT_SCAN_ROOT)
    ap.add_argument("--ignore", default=DEFAULT_IGNORE)
    args = ap.parse_args()

    root = Path(args.root)
    ignore_path = Path(args.ignore)
    ignores = _load_ignore(ignore_path)

    all_findings: List[Tuple[str, int, str]] = []
    for f in _iter_workflow_files(root):
        all_findings.extend(_scan_file(f, ignores))

    if not all_findings:
        print("✅ Workflow API_BASE gate: no hardcoded API bases found.")
        return 0

    print("❌ Workflow API_BASE gate failed: hardcoded API base URLs found.")
    print("Fix: define API_BASE once and reference it everywhere.")
    print("")
    for rel, lineno, line in all_findings:
        print(f"- {rel}:{lineno}: {line}")
    print("")
    print("Recommendation:")
    print("  env:")
    print("    API_BASE: http://127.0.0.1:8000/api")
    print("Then use:")
    print("  curl $API_BASE/...")
    print("")
    print(f"Temporary migration ignore list: {ignore_path.as_posix()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
