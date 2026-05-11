#!/usr/bin/env python3
"""
DXF Compatibility Enforcement Script

Enforces the governance rule that all DXF document creation must use
dxf_compat.create_document() instead of direct ezdxf.new() calls.

Usage:
    python scripts/check_dxf_compat.py [path]

Exit codes:
    0 - No violations found
    1 - Violations found

Exemptions are documented in docs/architecture/DXF_COMPAT_EXEMPTIONS.md
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Pattern to match ezdxf.new() calls
VIOLATION_PATTERN = re.compile(r'ezdxf\.new\s*\(')

# Allowed files (canonical wrappers)
CANONICAL_WRAPPERS = {
    'services/api/app/util/dxf_compat.py',
    'services/blueprint-import/dxf_compat.py',
    'services/api/app/cam/dxf_writer.py',  # Central DXF writer (reference in docstring)
}

# Excluded ecosystems (documented in DXF_COMPAT_EXEMPTIONS.md)
EXCLUDED_EXTERNAL_ECOSYSTEM = {
    'services/api/app/instrument_geometry/body/smart_guitar_dxf.py',
    'services/api/app/routers/instruments/guitar/smart_guitar_dxf_router.py',
    'services/api/scripts/generate_smart_guitar_v3_dxf.py',
}

# Excluded R&D sandbox (entire directory)
EXCLUDED_R_AND_D_SANDBOX_DIRS = [
    'services/photo-vectorizer/',
]

# Excluded directories (dependencies, virtual environments)
EXCLUDED_DIRS = [
    '.venv/',
    'venv/',
    'node_modules/',
    '__pycache__/',
]

# Test files (allowed for now, documented for Phase 2 migration)
TEST_FILE_PATTERNS = [
    'tests/',
    'test_',
    '_test.py',
]


def is_test_file(path: str) -> bool:
    """Check if path is a test file."""
    path_lower = path.lower()
    return any(pattern in path_lower for pattern in TEST_FILE_PATTERNS)


def is_excluded_dir(path: str) -> bool:
    """Check if path is in an excluded directory."""
    path_lower = path.lower().replace('\\', '/')
    for excl in EXCLUDED_DIRS:
        if excl in path_lower:
            return True
    return False


def is_rnd_sandbox(path: str) -> bool:
    """Check if path is in the R&D sandbox."""
    path_lower = path.lower().replace('\\', '/')
    for sandbox in EXCLUDED_R_AND_D_SANDBOX_DIRS:
        if sandbox in path_lower:
            return True
    return False


def normalize_path(path: Path, base: Path) -> str:
    """Normalize path for comparison."""
    try:
        rel = path.relative_to(base)
        return str(rel).replace('\\', '/')
    except ValueError:
        return str(path).replace('\\', '/')


def check_file(file_path: Path, base_path: Path) -> List[Tuple[int, str]]:
    """Check a single file for violations. Returns list of (line_number, line_content)."""
    violations = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if VIOLATION_PATTERN.search(line):
                    violations.append((line_num, line.strip()))
    except (OSError, IOError):
        pass
    return violations


def main(search_path: str = None) -> int:
    """Main entry point. Returns exit code."""
    base_path = Path(__file__).parent.parent.resolve()

    if search_path:
        search_root = Path(search_path).resolve()
    else:
        search_root = base_path / 'services'

    if not search_root.exists():
        print(f"Path does not exist: {search_root}")
        return 1

    all_violations = []
    exempt_files = []
    test_files = []
    rnd_files = []

    # Combine all file-level exemptions
    all_exemptions = CANONICAL_WRAPPERS | EXCLUDED_EXTERNAL_ECOSYSTEM

    # Find all Python files
    if search_root.is_file():
        py_files = [search_root]
    else:
        py_files = list(search_root.rglob('*.py'))

    for py_file in py_files:
        rel_path = normalize_path(py_file, base_path)

        # Skip excluded directories (venv, node_modules, etc.)
        if is_excluded_dir(rel_path):
            continue

        # Skip R&D sandbox (entire directory)
        if is_rnd_sandbox(rel_path):
            violations = check_file(py_file, base_path)
            if violations:
                rnd_files.append((rel_path, violations))
            continue

        # Skip exempted files
        if rel_path in all_exemptions:
            violations = check_file(py_file, base_path)
            if violations:
                exempt_files.append((rel_path, violations))
            continue

        # Track test files separately
        if is_test_file(rel_path):
            violations = check_file(py_file, base_path)
            if violations:
                test_files.append((rel_path, violations))
            continue

        # Check for violations
        violations = check_file(py_file, base_path)
        if violations:
            all_violations.append((rel_path, violations))

    # Report results
    print("=" * 70)
    print("DXF Compatibility Check")
    print("=" * 70)

    if all_violations:
        print(f"\n[FAIL] VIOLATIONS FOUND: {len(all_violations)} file(s)\n")
        for file_path, violations in all_violations:
            print(f"  {file_path}:")
            for line_num, line in violations:
                print(f"    Line {line_num}: {line[:60]}...")
        print()
        print("Fix: Replace ezdxf.new() with create_document() from dxf_compat")
        print("See: docs/architecture/DXF_COMPAT_EXEMPTIONS.md for exemption process")
    else:
        print("\n[PASS] No production code violations found\n")

    if exempt_files:
        print(f"\n[INFO] Documented exemptions ({len(exempt_files)} file(s)):")
        for file_path, violations in exempt_files:
            print(f"  {file_path} ({len(violations)} call(s))")

    if test_files:
        print(f"\n[INFO] Test files ({len(test_files)} file(s)) - allowed per TEST_FIXTURE_ALLOWED:")
        for file_path, violations in test_files:
            print(f"  {file_path} ({len(violations)} call(s))")

    if rnd_files:
        print(f"\n[INFO] R&D sandbox ({len(rnd_files)} file(s)) - allowed per EXCLUDED_R_AND_D_SANDBOX:")
        for file_path, violations in rnd_files:
            print(f"  {file_path} ({len(violations)} call(s))")

    print("\n" + "=" * 70)

    return 1 if all_violations else 0


if __name__ == '__main__':
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main(path_arg))
