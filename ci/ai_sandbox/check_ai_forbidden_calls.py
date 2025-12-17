#!/usr/bin/env python3
"""
AI Sandbox Forbidden API Usage Enforcement

Fails CI if AI sandbox code references execution-authority APIs.
This prevents AI from bypassing the advisory boundary.

Usage:
    python ci/ai_sandbox/check_ai_forbidden_calls.py
"""

import pathlib
import sys
import ast
from typing import List, Set

ROOT = pathlib.Path(__file__).resolve().parents[2]
AI_ROOT = ROOT / "services" / "api" / "app" / "_experimental"

# Modules that AI sandbox must not import
FORBIDDEN_MODULES: Set[str] = {
    "rmos.workflow",
    "rmos.toolpaths",
    "rmos.runs",
    "rmos.api_workflow",
    "rmos.api_toolpaths",
    "app.rmos.workflow",
    "app.rmos.toolpaths",
    "app.rmos.runs",
    "app.rmos.runs.store",
    "app.rmos.api_workflow",
    "app.rmos.api_toolpaths",
}

# Function names that AI sandbox must not call
FORBIDDEN_SYMBOLS: Set[str] = {
    "approve",
    "approve_workflow",
    "approve_workflow_session",
    "generate_toolpaths",
    "generate_toolpaths_server_side",
    "create_run",
    "create_run_id",
    "persist_run",
    "save_session",
}


def check_file(path: pathlib.Path) -> List[str]:
    """Check a single file for forbidden API usage."""
    violations = []
    
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return violations
    
    rel_path = path.relative_to(ROOT)
    
    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in FORBIDDEN_MODULES:
                violations.append(
                    f"{rel_path}:{node.lineno}: forbidden import from {module}"
                )
            # Also check partial matches
            for forbidden in FORBIDDEN_MODULES:
                if module.startswith(forbidden):
                    violations.append(
                        f"{rel_path}:{node.lineno}: forbidden import from {module}"
                    )
                    break
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_MODULES:
                    violations.append(
                        f"{rel_path}:{node.lineno}: forbidden import {alias.name}"
                    )
        
        # Check function calls
        if isinstance(node, ast.Call):
            func_name = None
            
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            if func_name and func_name in FORBIDDEN_SYMBOLS:
                violations.append(
                    f"{rel_path}:{node.lineno}: forbidden call {func_name}()"
                )
    
    return violations


def main() -> int:
    """Run the forbidden calls check."""
    # Check both ai/ and ai_graphics/ directories
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
            errors.extend(check_file(py_file))
    
    if checked == 0:
        print("⚠️  No AI sandbox directories found to check.")
        print("   Skipping forbidden-call check.")
        return 0
    
    if errors:
        print("❌ Forbidden RMOS execution calls detected in AI sandbox:")
        print()
        for e in errors:
            print(f"  {e}")
        print()
        print(f"Checked {checked} files, found {len(errors)} violations.")
        print()
        print("AI sandbox code must not import RMOS modules or call authority functions.")
        print("See docs/AI_SANDBOX_GOVERNANCE.md for details.")
        return 1
    
    print(f"✅ AI sandbox forbidden-call check passed. ({checked} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
