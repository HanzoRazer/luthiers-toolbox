#!/usr/bin/env python3
"""
Fence Runner - Unified Architectural Boundary Enforcement

Reads FENCE_REGISTRY.json and executes all enabled fence checks.
Returns non-zero exit code if any violations are found.

Usage:
    python -m app.ci.fence_runner                    # Run all enabled fences
    python -m app.ci.fence_runner --profile rmos_cam # Run specific fence
    python -m app.ci.fence_runner --list             # List all fences
    python -m app.ci.fence_runner --dry-run          # Show what would run

Reference: docs/governance/FENCE_ARCHITECTURE.md
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# Resolve paths relative to repo root
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent  # services/api/app/ci -> repo root
FENCE_REGISTRY_PATH = REPO_ROOT / "FENCE_REGISTRY.json"


class FenceViolation:
    """Represents a single fence violation."""

    def __init__(self, fence_id: str, file_path: str, line: int, message: str, severity: str = "ERROR"):
        self.fence_id = fence_id
        self.file_path = file_path
        self.line = line
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        return f"[{self.severity}] {self.fence_id} @ {self.file_path}:{self.line} - {self.message}"


class FenceRunner:
    """Runs architectural fence checks from FENCE_REGISTRY.json."""

    def __init__(self, registry_path: Path = FENCE_REGISTRY_PATH):
        self.registry_path = registry_path
        self.registry: Dict[str, Any] = {}
        self.violations: List[FenceViolation] = []
        self._load_registry()

    def _load_registry(self) -> None:
        """Load fence definitions from JSON registry."""
        if not self.registry_path.exists():
            print(f"ERROR: FENCE_REGISTRY.json not found at {self.registry_path}")
            sys.exit(1)

        with open(self.registry_path) as f:
            self.registry = json.load(f)

    def list_fences(self) -> None:
        """Print all available fences."""
        print(f"Fence Registry: {self.registry.get('repo_name', 'unknown')}")
        print(f"Version: {self.registry.get('version', 'unknown')}")
        print(f"Last Updated: {self.registry.get('last_updated', 'unknown')}")
        print()
        print("Available Fences:")
        print("-" * 60)

        for fence_id, fence in self.registry.get("profiles", {}).items():
            enabled = "[ON]" if fence.get("enabled", False) else "[OFF]"
            desc = fence.get("description", "No description")
            print(f"  {enabled} {fence_id}")
            print(f"        {desc}")
            print()

    def run_fence(self, fence_id: str, dry_run: bool = False) -> List[FenceViolation]:
        """Run a specific fence check."""
        profiles = self.registry.get("profiles", {})

        if fence_id not in profiles:
            print(f"ERROR: Unknown fence profile: {fence_id}")
            return []

        fence = profiles[fence_id]

        if not fence.get("enabled", False):
            print(f"SKIP: Fence '{fence_id}' is disabled")
            return []

        print(f"\n{'[DRY-RUN] ' if dry_run else ''}Running fence: {fence_id}")
        print(f"  Description: {fence.get('description', 'N/A')}")

        violations = []

        # Check for forbidden_imports rules
        if "forbidden_imports" in fence:
            violations.extend(
                self._check_forbidden_imports(fence_id, fence, dry_run)
            )

        # Check for domain rules
        if "rules" in fence:
            for rule in fence["rules"]:
                violations.extend(
                    self._check_domain_rule(fence_id, rule, dry_run)
                )

        # Check for pattern-based rules
        if "patterns" in fence:
            violations.extend(
                self._check_patterns(fence_id, fence, dry_run)
            )

        return violations

    def _check_forbidden_imports(
        self, fence_id: str, fence: Dict[str, Any], dry_run: bool
    ) -> List[FenceViolation]:
        """Check for forbidden import patterns."""
        violations = []
        scan_roots = fence.get("scan_roots", [])
        forbidden = fence.get("forbidden_imports", [])

        for root in scan_roots:
            root_path = REPO_ROOT / root
            if not root_path.exists():
                print(f"  WARN: Scan root not found: {root}")
                continue

            if dry_run:
                print(f"  Would scan: {root}")
                for f in forbidden:
                    print(f"    Looking for: {f.get('prefix', f)}")
                continue

            # Scan Python files
            for py_file in root_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            import_name = self._get_import_name(node)

                            for rule in forbidden:
                                prefix = rule.get("prefix", rule) if isinstance(rule, dict) else rule
                                if import_name and import_name.startswith(prefix):
                                    reason = rule.get("reason", "Forbidden import") if isinstance(rule, dict) else "Forbidden import"
                                    violations.append(FenceViolation(
                                        fence_id=fence_id,
                                        file_path=str(py_file.relative_to(REPO_ROOT)),
                                        line=node.lineno,
                                        message=f"Forbidden import '{import_name}': {reason}"
                                    ))
                except SyntaxError:
                    pass  # Skip files with syntax errors

        return violations

    def _check_domain_rule(
        self, fence_id: str, rule: Dict[str, Any], dry_run: bool
    ) -> List[FenceViolation]:
        """Check domain-specific import rules."""
        violations = []
        domain = rule.get("domain", "unknown")
        paths = rule.get("paths", [])
        allowed = set(rule.get("allowed_imports", []))
        forbidden = rule.get("forbidden_imports", [])

        for path_pattern in paths:
            # Convert glob pattern to Path
            base_path = path_pattern.replace("/**", "").replace("/*", "")
            root_path = REPO_ROOT / base_path

            if not root_path.exists():
                continue

            if dry_run:
                print(f"  Would check domain '{domain}' in: {base_path}")
                continue

            for py_file in root_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            import_name = self._get_import_name(node)
                            if not import_name:
                                continue

                            # Check forbidden imports
                            for f_rule in forbidden:
                                prefix = f_rule.get("prefix", f_rule) if isinstance(f_rule, dict) else f_rule
                                if import_name.startswith(prefix):
                                    reason = f_rule.get("reason", "Forbidden") if isinstance(f_rule, dict) else "Forbidden"
                                    violations.append(FenceViolation(
                                        fence_id=fence_id,
                                        file_path=str(py_file.relative_to(REPO_ROOT)),
                                        line=node.lineno,
                                        message=f"[{domain}] Forbidden import '{import_name}': {reason}"
                                    ))
                except SyntaxError:
                    pass

        return violations

    def _check_patterns(
        self, fence_id: str, fence: Dict[str, Any], dry_run: bool
    ) -> List[FenceViolation]:
        """Check for forbidden code patterns using regex."""
        violations = []
        scan_roots = fence.get("scan_roots", [])
        patterns = fence.get("patterns", [])

        for root in scan_roots:
            root_path = REPO_ROOT / root
            if not root_path.exists():
                continue

            if dry_run:
                print(f"  Would scan patterns in: {root}")
                continue

            for py_file in root_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()

                    for pattern_rule in patterns:
                        regex = pattern_rule.get("regex", "")
                        reason = pattern_rule.get("reason", "Pattern violation")

                        for i, line in enumerate(lines, 1):
                            if re.search(regex, line):
                                violations.append(FenceViolation(
                                    fence_id=fence_id,
                                    file_path=str(py_file.relative_to(REPO_ROOT)),
                                    line=i,
                                    message=f"Pattern match: {reason}"
                                ))
                except OSError:  # WP-1: narrowed from except Exception
                    pass

        return violations

    def _get_import_name(self, node: ast.AST) -> Optional[str]:
        """Extract the import module name from an AST node."""
        if isinstance(node, ast.Import):
            return node.names[0].name if node.names else None
        elif isinstance(node, ast.ImportFrom):
            return node.module or ""
        return None

    def run_all(self, dry_run: bool = False) -> List[FenceViolation]:
        """Run all enabled fence checks."""
        all_violations = []

        for fence_id in self.registry.get("profiles", {}):
            violations = self.run_fence(fence_id, dry_run)
            all_violations.extend(violations)
            self.violations.extend(violations)

        return all_violations

    def print_summary(self) -> None:
        """Print violation summary."""
        print("\n" + "=" * 60)
        print("FENCE CHECK SUMMARY")
        print("=" * 60)

        if not self.violations:
            print("PASS: No violations found")
            return

        print(f"FAIL: Found {len(self.violations)} violation(s):\n")

        # Group by fence
        by_fence: Dict[str, List[FenceViolation]] = {}
        for v in self.violations:
            by_fence.setdefault(v.fence_id, []).append(v)

        for fence_id, violations in by_fence.items():
            print(f"[{fence_id}] - {len(violations)} violation(s)")
            for v in violations[:5]:  # Show first 5
                print(f"  {v.file_path}:{v.line}")
                print(f"    {v.message}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Run architectural fence checks from FENCE_REGISTRY.json"
    )
    parser.add_argument(
        "--profile", "-p",
        help="Run specific fence profile (default: all enabled)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available fences"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be checked without running"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=FENCE_REGISTRY_PATH,
        help="Path to FENCE_REGISTRY.json"
    )

    args = parser.parse_args()

    runner = FenceRunner(args.registry)

    if args.list:
        runner.list_fences()
        return 0

    if args.profile:
        violations = runner.run_fence(args.profile, args.dry_run)
    else:
        violations = runner.run_all(args.dry_run)

    runner.print_summary()

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
