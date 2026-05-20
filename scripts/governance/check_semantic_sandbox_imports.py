#!/usr/bin/env python3
"""
Block production imports of semantic-sandbox / archaeological modules.

Phase 0.5 gate (VECTORIZER_SANDBOX_MIGRATION_PLAN): Tier A cognition and grid
lineage must not be imported under services/ until explicitly graduated via the
constitutional intake bridge. Re-home target: vectorizer-sandbox.

Usage:
    python scripts/governance/check_semantic_sandbox_imports.py

Exit codes:
    0 — no forbidden imports under services/
    1 — one or more violations
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICES_ROOT = REPO_ROOT / "services"

# Tier A modules (basename). Imports of these from other services/ files are forbidden.
FORBIDDEN_MODULE_PREFIXES: Tuple[str, ...] = (
    "cognitive_extractor",
    "cognitive_extraction_engine",
    "extract_body_grid",
)

# Tier A modules removed from runtime spine (2026-05-20). Any import is a violation.
ALLOWLIST_RELATIVE: Tuple[str, ...] = ()

IMPORT_LINE = re.compile(r"^\s*(?:from|import)\s+")

# Optional: block submodule / package install of sandbox into services
FORBIDDEN_SNIPPETS: Tuple[str, ...] = (
    "vectorizer-sandbox",
    "vectorizer_sandbox",
)


def _normalize_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _line_forbids_import(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    if not IMPORT_LINE.match(stripped):
        return False
    for prefix in FORBIDDEN_MODULE_PREFIXES:
        if prefix in stripped:
            return True
    for snippet in FORBIDDEN_SNIPPETS:
        if snippet in stripped:
            return True
    return False


def scan_services() -> List[Tuple[str, int, str]]:
    violations: List[Tuple[str, int, str]] = []
    allow = {p.replace("/", "\\") for p in ALLOWLIST_RELATIVE} | set(ALLOWLIST_RELATIVE)

    if not SERVICES_ROOT.is_dir():
        return [("services/", 0, "services/ directory missing")]

    for py_file in sorted(SERVICES_ROOT.rglob("*.py")):
        rel = _normalize_rel(py_file)
        if rel in allow:
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            violations.append((rel, 0, f"cannot read file: {exc}"))
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _line_forbids_import(line):
                violations.append((rel, line_no, line.strip()))
    return violations


def main() -> int:
    violations = scan_services()
    if not violations:
        print("check_semantic_sandbox_imports: PASS (no forbidden imports under services/)")
        return 0

    print("check_semantic_sandbox_imports: FAIL", file=sys.stderr)
    print(
        "Production services/ must not import Tier A cognition/grid modules.",
        file=sys.stderr,
    )
    print(
        "Re-home target: https://github.com/HanzoRazer/vectorizer-sandbox",
        file=sys.stderr,
    )
    print(f"Forbidden prefixes: {', '.join(FORBIDDEN_MODULE_PREFIXES)}", file=sys.stderr)
    for rel, line_no, detail in violations[:30]:
        loc = f"{rel}:{line_no}" if line_no else rel
        print(f"  {loc}: {detail}", file=sys.stderr)
    if len(violations) > 30:
        print(f"  ... and {len(violations) - 30} more", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
