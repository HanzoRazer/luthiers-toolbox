#!/usr/bin/env python3
"""
Bare Except Gate

Fails if any Python file contains bare except clauses.
Bare except: catches all exceptions including KeyboardInterrupt/SystemExit.

Usage:
    python -m app.ci.check_bare_except [--baseline FILE]

Exit codes:
    0 = OK (no violations or all in baseline)
    1 = violations found
    2 = runtime error
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _repo_root() -> Path:
    """Find repo root by looking for .git or pyproject.toml."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _find_python_files(root: Path) -> List[Path]:
    """Find all Python files under root, excluding venv/cache."""
    files = []
    for pyfile in root.rglob("*.py"):
        rel = str(pyfile.relative_to(root))
        if any(skip in rel for skip in [
            "venv", "__pycache__", ".git", "node_modules",
            "site-packages", ".eggs", "build", "dist"
        ]):
            continue
        files.append(pyfile)
    return files


def check_bare_except(
    root: Path,
    baseline: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Check all Python files for bare except clauses.

    Returns list of violations (empty if OK).
    """
    violations = []
    baseline_set = set()

    if baseline:
        for v in baseline.get("violations", []):
            key = f"{v['file']}:{v['line']}"
            baseline_set.add(key)

    for pyfile in _find_python_files(root):
        try:
            code = pyfile.read_text(encoding="utf-8")
            lines = code.splitlines()
            tree = ast.parse(code, filename=str(pyfile))

            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:  # Bare except
                        rel_path = str(pyfile.relative_to(root))
                        key = f"{rel_path}:{node.lineno}"

                        if key in baseline_set:
                            continue  # Skip baselined violations

                        # Get the actual line content
                        line_content = ""
                        if node.lineno <= len(lines):
                            line_content = lines[node.lineno - 1].strip()

                        violations.append({
                            "file": rel_path,
                            "line": node.lineno,
                            "code": line_content,
                        })
        except SyntaxError:
            pass  # Skip files with syntax errors (expected for some generated files)
        except (OSError, UnicodeDecodeError):
            pass  # Skip files that can't be read

    # Sort by file then line
    violations.sort(key=lambda x: (x["file"], x["line"]))
    return violations


def main():
    parser = argparse.ArgumentParser(description="Check for bare except clauses")
    parser.add_argument("--baseline", type=str, help="Baseline JSON file (ratchet mode)")
    parser.add_argument("--write-baseline", action="store_true", help="Write current violations to baseline")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    root = _repo_root()
    app_root = root / "services" / "api" / "app"

    if not app_root.exists():
        app_root = root / "app"
    if not app_root.exists():
        print(f"ERROR: Cannot find app directory from {root}")
        sys.exit(2)

    baseline = None
    if args.baseline and Path(args.baseline).exists():
        baseline = json.loads(Path(args.baseline).read_text())

    violations = check_bare_except(app_root.parent, baseline)

    if args.write_baseline:
        baseline_data = {
            "violation_count": len(violations),
            "violations": violations,
        }
        out_path = Path(args.baseline) if args.baseline else Path("bare_except_baseline.json")
        out_path.write_text(json.dumps(baseline_data, indent=2))
        print(f"Wrote {len(violations)} violations to {out_path}")
        return 0

    if args.json:
        print(json.dumps(violations, indent=2))
    else:
        if violations:
            print("BARE EXCEPT VIOLATIONS:")
            print("=" * 60)
            for v in violations[:25]:
                print(f"  {v['file']}:{v['line']}")
                print(f"    {v['code']}")
            if len(violations) > 25:
                print(f"  ... and {len(violations) - 25} more")
            print()
            print(f"Total: {len(violations)} bare except clauses")
            print()
            print("Fix: Replace 'except:' with 'except Exception:' or specific types")
        else:
            print("OK: No bare except clauses found")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
