#!/usr/bin/env python3
"""
Quick import-check for recovered files.

For each .py file in the __RECOVERED__ tree, attempts an AST parse
and reports:
  - Whether the file parses cleanly
  - All imports and whether those modules exist in the current codebase
  - A dependency-satisfaction percentage

Usage:
    cd services/api
    python ../../__RECOVERED__/check_imports.py
"""

import ast
import importlib.util
import os
import sys
from pathlib import Path

RECOVERED_ROOT = Path(__file__).resolve().parent
API_ROOT = RECOVERED_ROOT.parent / "services" / "api"

# Add services/api to sys.path so we can probe internal imports
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def check_file(py_path: Path) -> dict:
    """Parse a recovered .py file and check its imports."""
    result = {
        "file": str(py_path.relative_to(RECOVERED_ROOT)),
        "parses": False,
        "lines": 0,
        "imports": [],
        "satisfied": 0,
        "missing": 0,
        "details": [],
    }

    try:
        source = py_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        result["error"] = f"Cannot read: {e}"
        return result

    result["lines"] = len(source.splitlines())

    try:
        tree = ast.parse(source, filename=str(py_path))
        result["parses"] = True
    except SyntaxError as e:
        result["error"] = f"SyntaxError line {e.lineno}: {e.msg}"
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _check_import(alias.name, result)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                _check_import(node.module, result)

    return result


def _check_import(module_name: str, result: dict):
    """Check if a module is available."""
    result["imports"].append(module_name)

    # Try stdlib / installed packages
    try:
        spec = importlib.util.find_spec(module_name.split(".")[0])
        if spec is not None:
            result["satisfied"] += 1
            result["details"].append(f"  OK  {module_name}")
            return
    except (ModuleNotFoundError, ValueError):
        pass

    # Try as relative app import (convert dotted to path)
    if module_name.startswith("app.") or module_name.startswith(".."):
        rel = module_name.lstrip(".").replace(".", os.sep) + ".py"
        candidate = API_ROOT / rel
        if candidate.exists() or (API_ROOT / rel.replace(".py", "")).is_dir():
            result["satisfied"] += 1
            result["details"].append(f"  OK  {module_name} (app path)")
            return

    result["missing"] += 1
    result["details"].append(f"  MISS {module_name}")


def main():
    py_files = sorted(RECOVERED_ROOT.rglob("*.py"))
    py_files = [f for f in py_files if f.name != "check_imports.py"]

    total_sat = 0
    total_miss = 0
    total_imports = 0

    print(f"{'='*70}")
    print(f"  RECOVERED FILE IMPORT CHECK")
    print(f"  Scanning {len(py_files)} Python files")
    print(f"  API root: {API_ROOT}")
    print(f"{'='*70}\n")

    for py in py_files:
        r = check_file(py)
        n_imp = r["satisfied"] + r["missing"]
        total_imports += n_imp
        total_sat += r["satisfied"]
        total_miss += r["missing"]

        status = "PARSE OK" if r["parses"] else "PARSE FAIL"
        pct = f"{r['satisfied']}/{n_imp}" if n_imp else "no imports"
        print(f"[{status}] {r['file']}  ({r['lines']} lines, deps: {pct})")

        if r.get("error"):
            print(f"         ERROR: {r['error']}")

        for d in r["details"]:
            if "MISS" in d:
                print(f"       {d}")

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"  Files scanned:    {len(py_files)}")
    print(f"  Total imports:    {total_imports}")
    print(f"  Satisfied:        {total_sat}")
    print(f"  Missing:          {total_miss}")
    if total_imports:
        print(f"  Satisfaction:     {total_sat/total_imports*100:.0f}%")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
