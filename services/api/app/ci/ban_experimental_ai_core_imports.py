"""Ban new imports from deprecated _experimental/ai_core module.

This CI check ensures no new code imports from the deprecated
_experimental/ai_core module. Use app.rmos.ai instead.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Paths to scan
SCAN_ROOTS = [
    Path(__file__).parent.parent,  # app/
]

# Paths to skip (already using legacy imports, not new code)
SKIP_PATHS = {
    "app/_experimental/",
    "app/ci/",
    "__pycache__",
}

# The banned import pattern
BANNED_MODULES = [
    "app._experimental.ai_core",
    "_experimental.ai_core",
]


def is_banned_import(import_str: str) -> bool:
    """Check if an import string matches a banned pattern."""
    for banned in BANNED_MODULES:
        if import_str.startswith(banned) or import_str == banned:
            return True
    return False


def should_skip(path: Path) -> bool:
    """Check if a path should be skipped."""
    path_str = str(path).replace("\\", "/")
    for skip in SKIP_PATHS:
        if skip in path_str:
            return True
    return False


def check_file(path: Path) -> list[str]:
    """Check a Python file for banned imports. Returns list of violations."""
    if should_skip(path):
        return []

    violations = []
    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if is_banned_import(alias.name):
                        violations.append(
                            f"{path}:{node.lineno}: import {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module and is_banned_import(node.module):
                    names = ", ".join(a.name for a in node.names)
                    violations.append(
                        f"{path}:{node.lineno}: from {node.module} import {names}"
                    )
    except SyntaxError:
        pass  # Skip files with syntax errors
    except Exception:
        pass  # Skip unreadable files

    return violations


def main() -> int:
    """Run the banned import check."""
    all_violations = []

    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for py_file in root.rglob("*.py"):
            violations = check_file(py_file)
            all_violations.extend(violations)

    if all_violations:
        print(f"Found {len(all_violations)} banned imports from _experimental/ai_core:")
        for v in all_violations:
            print(f"  - {v}")
        print()
        print("Please migrate to: from app.rmos.ai import ...")
        return 1

    print("✓ No banned imports from _experimental/ai_core found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
