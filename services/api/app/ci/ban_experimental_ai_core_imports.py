"""
CI Guard: Ban imports from experimental ai_core module

Scans all Python files in app/ (except _experimental/ai_core/* itself) to detect
imports from app._experimental.ai_core. This enforces the migration to app.rmos.ai.

Exit codes:
    0 = No violations found
    2 = Violations detected (import patterns found)

Usage in CI:
    cd services/api
    python -m app.ci.ban_experimental_ai_core_imports
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
"""

import pathlib
import re
import sys
from typing import List, Tuple


def find_violations(root: pathlib.Path) -> List[Tuple[pathlib.Path, int, str]]:
    """
    Scan all Python files under root for banned imports from _experimental/ai_core.
    
    Returns:
        List of (file_path, line_number, line_content) tuples for violations.
    """
    violations = []
    
    # Patterns that indicate import from _experimental.ai_core
    # Use word boundaries to avoid matching in strings/comments
    patterns = [
        re.compile(r"^\s*from\s+app\._experimental\.ai_core"),  # from app._experimental.ai_core import X
        re.compile(r"^\s*from\s+\.\._experimental\.ai_core"),  # from .._experimental.ai_core import X
        re.compile(r"^\s*from\s+\.+ai_core\s+import"),  # from ..ai_core import X (when in app/)
        re.compile(r"^\s*import\s+app\._experimental\.ai_core"),  # import app._experimental.ai_core
    ]
    
    # Scan all Python files recursively
    for py_file in root.rglob("*.py"):
        # Skip files in _experimental/ai_core/* itself (shims need to reference old module)
        if "_experimental" in py_file.parts and "ai_core" in py_file.parts:
            continue
        
        # Skip this CI guard file itself (has examples in docstrings)
        if py_file.name == "ban_experimental_ai_core_imports.py":
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    # Skip comment lines and docstrings
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                        
                    for pattern in patterns:
                        if pattern.search(line):
                            violations.append((py_file, line_num, line.strip()))
                            break  # One violation per line is enough
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {py_file}: {e}", file=sys.stderr)
            continue
    
    return violations


def main() -> int:
    # Root is services/api/app/ (one level up from this file's parent)
    script_path = pathlib.Path(__file__).resolve()
    app_root = script_path.parents[1]  # ci/ -> app/
    
    print(f"[CI Guard] Scanning {app_root} for banned ai_core imports...")
    
    violations = find_violations(app_root)
    
    if not violations:
        print("[CI Guard] ✓ No violations found. Migration enforcement successful.")
        return 0
    
    print(f"[CI Guard] ✗ Found {len(violations)} violation(s):", file=sys.stderr)
    print(file=sys.stderr)
    
    for file_path, line_num, line_content in violations:
        rel_path = file_path.relative_to(app_root)
        print(f"  {rel_path}:{line_num}", file=sys.stderr)
        print(f"    {line_content}", file=sys.stderr)
    
    print(file=sys.stderr)
    print("[CI Guard] Please migrate to canonical imports:", file=sys.stderr)
    print("  OLD: from app._experimental.ai_core import X", file=sys.stderr)
    print("  NEW: from app.rmos.ai import X", file=sys.stderr)
    print(file=sys.stderr)
    
    return 2


if __name__ == "__main__":
    sys.exit(main())
