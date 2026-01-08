#!/usr/bin/env python3
"""
Art Studio Scope Gate (v1)

Goal:
  Prevent feature creep by ensuring Art Studio remains ornament-authority only.

This is intentionally conservative and simple:
  - keyword/regex scanning across Art Studio + RMOS UI lane files
  - blocks on structural host-geometry intent or manufacturing authority calls

Exit codes:
  0 = pass
  1 = violations found
  2 = execution error
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


# --- Config ------------------------------------------------------------------

DEFAULT_TARGETS = [
    # Frontend (adjust if your repo uses packages/client/src instead of client/src)
    "client/src/components/rmos",
    "client/src/features/art_studio",
    "client/src/features/rmos",
    # Backend
    "services/api/app/art_studio",
]

ALT_FRONTEND_TARGETS = [
    "packages/client/src/components/rmos",
    "packages/client/src/features/art_studio",
    "packages/client/src/features/rmos",
]

INCLUDE_EXTS = {".ts", ".tsx", ".vue", ".py", ".md"}

# Things Art Studio must not authoritatively do.
FORBIDDEN_PATTERNS: List[Tuple[str, str]] = [
    # Host geometry creep (structural domains)
    ("HOST_GEOMETRY", r"\b(headstock|bridge|neck|body|tuner_hole|pin_hole|truss_rod)\b"),
    ("HOST_GEOMETRY", r"\b(tuner(s)?|string\s*tension|saddle|bridge\s*pin)\b"),

    # CAM / machine execution creep
    ("MACHINE_OUTPUT", r"\b(gcode|toolpath(s)?|post[-_ ]?processor|\bnc\b)\b"),

    # Authority creation / governance bypass
    ("AUTHORITY", r"\b(create_run_id|persist_run|store_artifact|write_run_artifact)\b"),
    ("AUTHORITY", r"\b/api/(cam|saw)/\b"),
    ("AUTHORITY", r"\b(promote|decideManufacturingCandidate|bulk-review)\b"),
]

# Minimal allow mechanism (v1)
# Syntax (single-line):
#   SCOPE_ALLOW: <TAG> <reason...>
ALLOW_INLINE_RE = re.compile(r"SCOPE_ALLOW:\s*(\w+)\b", re.IGNORECASE)


# --- Implementation -----------------------------------------------------------

@dataclass
class Finding:
    tag: str
    relpath: str
    line_no: int
    line: str
    pattern: str


def iter_files(root: Path, targets: Iterable[str]) -> Iterable[Path]:
    for t in targets:
        p = (root / t).resolve()
        if not p.exists():
            continue
        if p.is_file():
            if p.suffix in INCLUDE_EXTS:
                yield p
            continue
        for fp in p.rglob("*"):
            if fp.is_file() and fp.suffix in INCLUDE_EXTS:
                yield fp


def _detect_frontend_targets(root: Path) -> List[str]:
    """Detect whether to use client/src or packages/client/src structure."""
    # Check if packages/client/src exists (monorepo structure)
    if (root / "packages" / "client" / "src").exists():
        return ALT_FRONTEND_TARGETS + ["services/api/app/art_studio"]
    return DEFAULT_TARGETS


def _line_has_allow(line: str, tag: str) -> bool:
    """Check if line contains SCOPE_ALLOW: TAG for the given tag."""
    m = ALLOW_INLINE_RE.search(line)
    if m and m.group(1).upper() == tag.upper():
        return True
    return False


def scan_file(root: Path, fp: Path) -> List[Finding]:
    """Scan a single file for scope violations."""
    rel = str(fp.relative_to(root)).replace("\\", "/")

    findings: List[Finding] = []
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        findings.append(Finding("READ_ERROR", rel, 0, f"<read failed: {e}>", ""))
        return findings

    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        # quick skip for empty lines
        if not line.strip():
            continue
        for tag, pat in FORBIDDEN_PATTERNS:
            if re.search(pat, line, flags=re.IGNORECASE):
                # Check for inline allow: SCOPE_ALLOW: TAG
                if _line_has_allow(line, tag):
                    continue
                findings.append(Finding(tag, rel, i, line.rstrip(), pat))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Art Studio Scope Gate - prevents ornament-authority creep"
    )
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument(
        "--targets",
        nargs="*",
        default=None,
        help="Targets to scan (default: auto-detect frontend structure)",
    )
    ap.add_argument("--max-findings", type=int, default=200, help="Limit output")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()

    # Auto-detect targets if not specified
    targets = args.targets if args.targets else _detect_frontend_targets(root)

    all_findings: List[Finding] = []
    for fp in iter_files(root, targets):
        all_findings.extend(scan_file(root, fp))

    # Filter out read errors from counting as violations? No — fail fast.
    violations = [f for f in all_findings if f.tag != "READ_ERROR"]
    read_errors = [f for f in all_findings if f.tag == "READ_ERROR"]

    if read_errors:
        print("[art-studio-scope] ERROR: failed to read some files:", file=sys.stderr)
        for f in read_errors[: args.max_findings]:
            print(f"  {f.relpath}: {f.line}", file=sys.stderr)
        return 2

    if not violations:
        print("[art-studio-scope] PASS: no scope violations found")
        return 0

    print(f"[art-studio-scope] FAIL: {len(violations)} scope violations found\n", file=sys.stderr)

    # Group by file for readability
    by_file: dict[str, List[Finding]] = {}
    for f in violations:
        by_file.setdefault(f.relpath, []).append(f)

    printed = 0
    for rel, fs in sorted(by_file.items()):
        print(f"--- {rel} ---", file=sys.stderr)
        for f in fs:
            print(f"{f.line_no:4d} [{f.tag}] {f.line}", file=sys.stderr)
            printed += 1
            if printed >= args.max_findings:
                print(f"\n[art-studio-scope] output truncated at {args.max_findings}", file=sys.stderr)
                return 1

    print(
        "\n[art-studio-scope] Guidance: Art Studio may author ornament intent only "
        "(rosette/inlay/mosaic). Host geometry + CAM + authority creation must live elsewhere.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"[art-studio-scope] ERROR: {e}", file=sys.stderr)
        raise SystemExit(2)
