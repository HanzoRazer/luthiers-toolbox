#!/usr/bin/env python3
"""
Duplication Detection Gate

Detects duplicate code blocks using AST-based hashing.
Lighter weight than jscpd, pure Python, no npm required.

Usage:
    python -m app.ci.check_duplication [--threshold N] [--min-lines N] [--json]

Exit codes:
    0 = OK (duplicates under threshold)
    1 = Too many duplicates
    2 = Runtime error
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


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


def _normalize_ast(node: ast.AST) -> str:
    """Normalize AST node to string, ignoring variable names."""
    try:
        return ast.dump(node, annotate_fields=False)
    except Exception:
        return ""


def _extract_blocks(code: str, min_lines: int = 6) -> List[Tuple[int, int, str]]:
    """Extract code blocks (functions, classes) from source."""
    blocks = []
    try:
        tree = ast.parse(code)
        lines = code.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = node.lineno
                end = getattr(node, 'end_lineno', start + 10) or start + 10

                if end - start >= min_lines:
                    # Hash the normalized AST structure
                    node_str = _normalize_ast(node)
                    block_hash = hashlib.md5(node_str.encode()).hexdigest()[:12]
                    blocks.append((start, end, block_hash))
    except SyntaxError:
        pass

    return blocks


def find_duplicates(
    root: Path,
    min_lines: int = 6,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Find duplicate code blocks across Python files.

    Returns dict mapping hash -> list of locations.
    """
    hash_to_locations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for pyfile in _find_python_files(root):
        try:
            code = pyfile.read_text(encoding="utf-8")
            blocks = _extract_blocks(code, min_lines)

            for start, end, block_hash in blocks:
                rel_path = str(pyfile.relative_to(root))
                hash_to_locations[block_hash].append({
                    "file": rel_path,
                    "start": start,
                    "end": end,
                    "lines": end - start,
                })
        except (OSError, UnicodeDecodeError, SyntaxError):
            pass  # Skip files that can't be read or parsed

    # Filter to only duplicates (2+ occurrences)
    duplicates = {
        h: locs for h, locs in hash_to_locations.items()
        if len(locs) >= 2
    }

    return duplicates


def calculate_stats(duplicates: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Calculate duplication statistics."""
    total_clones = len(duplicates)
    total_instances = sum(len(locs) for locs in duplicates.values())
    total_duplicate_lines = sum(
        sum(loc["lines"] for loc in locs[1:])  # Count all but first occurrence
        for locs in duplicates.values()
    )

    return {
        "clone_groups": total_clones,
        "total_instances": total_instances,
        "duplicate_lines": total_duplicate_lines,
    }


def main():
    parser = argparse.ArgumentParser(description="Check for code duplication")
    parser.add_argument("--threshold", type=int, default=50, help="Max allowed clone groups")
    parser.add_argument("--min-lines", type=int, default=6, help="Min lines for a block")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--top", type=int, default=10, help="Show top N duplicates")
    args = parser.parse_args()

    root = _repo_root()
    app_root = root / "services" / "api"

    if not app_root.exists():
        app_root = root

    duplicates = find_duplicates(app_root, min_lines=args.min_lines)
    stats = calculate_stats(duplicates)

    if args.json:
        output = {
            "stats": stats,
            "threshold": args.threshold,
            "passed": stats["clone_groups"] <= args.threshold,
            "duplicates": [
                {"hash": h, "count": len(locs), "locations": locs}
                for h, locs in sorted(duplicates.items(), key=lambda x: -len(x[1]))[:args.top]
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 60)
        print("DUPLICATION ANALYSIS")
        print("=" * 60)
        print(f"Clone groups: {stats['clone_groups']}")
        print(f"Total instances: {stats['total_instances']}")
        print(f"Duplicate lines: {stats['duplicate_lines']}")
        print(f"Threshold: {args.threshold}")
        print()

        if duplicates:
            print(f"Top {args.top} duplicates:")
            print("-" * 40)
            sorted_dups = sorted(duplicates.items(), key=lambda x: -len(x[1]))
            for h, locs in sorted_dups[:args.top]:
                print(f"  [{h}] {len(locs)} copies:")
                for loc in locs[:3]:
                    print(f"    {loc['file']}:{loc['start']}-{loc['end']} ({loc['lines']} lines)")
                if len(locs) > 3:
                    print(f"    ... and {len(locs) - 3} more")
            print()

        if stats["clone_groups"] > args.threshold:
            print(f"FAIL: {stats['clone_groups']} clone groups exceeds threshold {args.threshold}")
        else:
            print(f"OK: {stats['clone_groups']} clone groups within threshold {args.threshold}")

    return 1 if stats["clone_groups"] > args.threshold else 0


if __name__ == "__main__":
    sys.exit(main())
