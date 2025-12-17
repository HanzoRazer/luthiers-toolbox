#!/usr/bin/env python3
"""
AI Sandbox Import Boundary Enforcement

Fails CI if any file under app/rmos/ imports AI sandbox code.
This prevents RMOS (authoritative) from depending on AI (advisory).

Usage:
    python ci/ai_sandbox/check_ai_import_boundaries.py
"""

import pathlib
import sys
import ast
from typing import List

ROOT = pathlib.Path(__file__).resolve().parents[2]
RMOS_DIR = ROOT / "services" / "api" / "app" / "rmos"

# Patterns that indicate AI sandbox imports
AI_PATTERNS = [
    "_experimental.ai",
    "_experimental.ai_graphics",
    "app._experimental.ai",
    "app._experimental.ai_graphics",
]


def check_file(path: pathlib.Path) -> List[str]:
    """Check a single file for forbidden imports."""
    violations = []
    
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        # Skip files that can't be parsed
        return violations
    
    for node in ast.walk(tree):
        module = ""
        
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                if any(pattern in module for pattern in AI_PATTERNS):
                    violations.append(
                        f"{path.relative_to(ROOT)}:{node.lineno}: "
                        f"illegal import from AI sandbox: {module}"
                    )
            continue
        
        if any(pattern in module for pattern in AI_PATTERNS):
            violations.append(
                f"{path.relative_to(ROOT)}:{node.lineno}: "
                f"illegal import from AI sandbox: {module}"
            )
    
    return violations


def main() -> int:
    """Run the boundary check."""
    if not RMOS_DIR.exists():
        print(f"⚠️  RMOS directory not found: {RMOS_DIR}")
        print("   Skipping import boundary check.")
        return 0
    
    errors = []
    checked = 0
    
    for py_file in RMOS_DIR.rglob("*.py"):
        checked += 1
        errors.extend(check_file(py_file))
    
    if errors:
        print("❌ AI Sandbox import boundary violations detected:")
        print()
        for e in errors:
            print(f"  {e}")
        print()
        print(f"Checked {checked} files, found {len(errors)} violations.")
        print()
        print("RMOS code must not import from _experimental/ai* directories.")
        print("See docs/AI_SANDBOX_GOVERNANCE.md for details.")
        return 1
    
    print(f"✅ AI sandbox import boundary check passed. ({checked} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
