#!/usr/bin/env python3
"""
AI Import Guard - CI Enforcement

Ensures vendor SDK imports (openai, anthropic) only appear in the canonical
AI transport layer, not scattered across the codebase.

This enforces the architectural boundary:
- ALLOWED: services/api/app/ai/transport/
- BLOCKED: everywhere else (except TYPE_CHECKING guards)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RE_VENDOR_IMPORT = re.compile(r'^\s*(import|from)\s+(openai|anthropic)\b', re.IGNORECASE)

# Only these paths may import vendor SDKs:
ALLOW_PREFIXES = (
    "services/api/app/ai/transport/",
)

# Allow under TYPE_CHECKING anywhere
TYPE_CHECKING_GUARD = "TYPE_CHECKING"

SKIP_DIRS = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & SKIP_DIRS)


def is_allowed(path: Path) -> bool:
    s = str(path.as_posix())
    return any(s.startswith(p) for p in ALLOW_PREFIXES)


def scan_file(path: Path) -> list[str]:
    violations = []
    txt = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    in_type_checking_block = False

    for i, line in enumerate(txt, start=1):
        if TYPE_CHECKING_GUARD in line and "if" in line:
            # coarse but high-signal: inside TYPE_CHECKING block
            in_type_checking_block = True

        if RE_VENDOR_IMPORT.search(line):
            if in_type_checking_block:
                continue
            if not is_allowed(path):
                violations.append(f"{path}:{i}: vendor SDK import outside ai/transport")
    return violations


def main() -> int:
    root = Path(os.getenv("REPO_ROOT", ".")).resolve()
    base = root / "services" / "api"

    if not base.exists():
        print(f"ai_import_guard: expected {base} to exist", file=sys.stderr)
        return 2

    violations: list[str] = []
    for p in base.rglob("*.py"):
        if should_skip(p):
            continue
        violations.extend(scan_file(p))

    if violations:
        print("AI import guard FAILED:\n" + "\n".join(violations), file=sys.stderr)
        return 1

    print("AI import guard OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
