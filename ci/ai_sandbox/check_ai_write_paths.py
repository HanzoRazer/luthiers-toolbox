#!/usr/bin/env python3
"""
AI Sandbox Write-Path Enforcement

Fails CI if AI code writes into RMOS execution directories.
This prevents AI from tampering with authoritative data.

Usage:
    python ci/ai_sandbox/check_ai_write_paths.py
"""

import pathlib
import sys
import re
from typing import List, Set

ROOT = pathlib.Path(__file__).resolve().parents[2]
AI_ROOT = ROOT / "services" / "api" / "app" / "_experimental"

# Path patterns that AI sandbox must not write to
FORBIDDEN_PATH_PATTERNS = [
    r"app/rmos",
    r"rmos/runs",
    r"rmos/toolpaths",
    r"rmos/workflow",
    r"services/api/app/rmos",
    r"services/api/app/data/runs",
]

# Functions that indicate file writing
WRITE_FUNCS: Set[str] = {
    "open",
    "write",
    "writelines",
    "mkdir",
    "makedirs",
    "touch",
    "write_text",
    "write_bytes",
    "persist_run",
    "save_session",
}


def check_file(path: pathlib.Path) -> List[str]:
    """Check a single file for forbidden write paths."""
    violations = []
    
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations
    
    rel_path = path.relative_to(ROOT)
    
    # Check if file contains both a forbidden path and a write function
    for pattern in FORBIDDEN_PATH_PATTERNS:
        if re.search(pattern, text):
            # Now check if any write functions are also present
            for func in WRITE_FUNCS:
                if func in text:
                    # More precise check: is this a real write operation?
                    # Look for patterns like: open(..., 'w'), .write(, makedirs(
                    write_patterns = [
                        rf"{func}\s*\(",  # function call
                        rf"\.{func}\s*\(",  # method call
                    ]
                    for wp in write_patterns:
                        if re.search(wp, text):
                            violations.append(
                                f"{rel_path}: potential write to forbidden RMOS path "
                                f"(pattern: {pattern}, function: {func})"
                            )
                            break
    
    return violations


def main() -> int:
    """Run the write-path check."""
    ai_dirs = [
        AI_ROOT / "ai",
        AI_ROOT / "ai_graphics",
    ]
    
    errors = []
    checked = 0
    
    for ai_dir in ai_dirs:
        if not ai_dir.exists():
            continue
        
        for py_file in ai_dir.rglob("*.py"):
            checked += 1
            file_violations = check_file(py_file)
            # Deduplicate violations per file
            errors.extend(list(set(file_violations)))
    
    if checked == 0:
        print("[WARN] No AI sandbox directories found to check.")
        print("       Skipping write-path check.")
        return 0

    if errors:
        print("[FAIL] AI sandbox write-path violations detected:")
        print()
        for e in sorted(set(errors)):
            print(f"  {e}")
        print()
        print(f"Checked {checked} files, found {len(set(errors))} violations.")
        print()
        print("AI sandbox code must not write to RMOS execution directories.")
        print("See docs/AI_SANDBOX_GOVERNANCE.md for details.")
        return 1

    print(f"[PASS] AI sandbox write-path check passed. ({checked} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
