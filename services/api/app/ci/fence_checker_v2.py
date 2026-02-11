#!/usr/bin/env python3
"""
Fence Checker v2 - Contract Validation System
Run with: python -m app.ci.fence_checker_v2 [--strict] [--json]
"""
from __future__ import annotations

import os
import sys
import ast
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class FenceSeverity(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3
    BLOCKER = 4


class FenceType(Enum):
    SAFETY_CRITICAL = "safety_critical"
    GCODE_GENERATION = "gcode_generation"
    LAYER_BOUNDARY = "layer_boundary"
    CUSTOM = "custom"


@dataclass
class Fence:
    id: str
    name: str
    type: FenceType
    target: str
    severity: FenceSeverity
    description: str = ""
    condition: str = ""
    owner: str = "unknown"


@dataclass
class FenceViolation:
    fence_id: str
    fence_name: str
    severity: FenceSeverity
    location: str
    message: str
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None


@dataclass
class FenceReport:
    total_fences: int = 0
    passed_fences: int = 0
    failed_fences: int = 0
    violations: List[FenceViolation] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def exit_code(self) -> int:
        if any(v.severity == FenceSeverity.BLOCKER for v in self.violations):
            return 4
        if any(v.severity == FenceSeverity.CRITICAL for v in self.violations):
            return 3
        if any(v.severity == FenceSeverity.ERROR for v in self.violations):
            return 2
        return 0


class SafetyFenceChecker:
    """Check safety-critical fences"""

    def __init__(self):
        self.violations: List[FenceViolation] = []

    def _find_python_files(self, root: Path) -> List[Path]:
        files = []
        for pyfile in root.rglob("*.py"):
            rel = str(pyfile)
            if not any(s in rel for s in ["venv", "__pycache__", "node_modules", "site-packages"]):
                files.append(pyfile)
        return files

    def check_bare_except(self, root: Path) -> List[FenceViolation]:
        """Check for bare except clauses"""
        for pyfile in self._find_python_files(root):
            try:
                code = pyfile.read_text(encoding="utf-8")
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler) and node.type is None:
                        fence = Fence(
                            id=f"bare_except_{pyfile.name}_{node.lineno}",
                            name="Bare except clause",
                            type=FenceType.SAFETY_CRITICAL,
                            target=str(pyfile),
                            severity=FenceSeverity.ERROR,
                        )
                        self.violations.append(
                            FenceViolation(
                                fence_id=fence.id,
                                fence_name=fence.name,
                                severity=fence.severity,
                                location=f"{pyfile}:{node.lineno}",
                                message="Bare except: clause detected",
                                actual_value="except:",
                                expected_value="except SpecificError:",
                            )
                        )
            except (SyntaxError, UnicodeDecodeError):
                pass
        return self.violations

    def check_safety_decorators(self, root: Path) -> List[FenceViolation]:
        """Check for missing @safety_critical decorators on safety functions"""
        patterns = ["generate_gcode", "calculate_feeds", "compute_feasibility", "validate_toolpath"]
        for pyfile in self._find_python_files(root):
            try:
                code = pyfile.read_text(encoding="utf-8")
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        is_safety = any(p in node.name for p in patterns)
                        if is_safety:
                            has_deco = any(
                                (isinstance(d, ast.Name) and d.id == "safety_critical")
                                for d in node.decorator_list
                            )
                            if not has_deco:
                                fence = Fence(
                                    id=f"missing_safety_{node.name}",
                                    name=f"Missing @safety_critical on {node.name}",
                                    type=FenceType.SAFETY_CRITICAL,
                                    target=str(pyfile),
                                    severity=FenceSeverity.WARNING,
                                )
                                self.violations.append(
                                    FenceViolation(
                                        fence_id=fence.id,
                                        fence_name=fence.name,
                                        severity=fence.severity,
                                        location=f"{pyfile}:{node.lineno}",
                                        message=f"Function {node.name} appears safety-critical but lacks @safety_critical",
                                    )
                                )
            except (SyntaxError, UnicodeDecodeError):
                pass
        return self.violations


def _repo_root() -> Path:
    """Find repo root by looking for .git or pyproject.toml."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def main():
    parser = argparse.ArgumentParser(description="Fence Checker v2 - Contract Validation")
    parser.add_argument("--strict", action="store_true", help="Fail on any violation")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    root = _repo_root()
    app_root = root / "services" / "api" / "app"
    if not app_root.exists():
        app_root = root / "app"
    if not app_root.exists():
        print(f"ERROR: Cannot find app directory from {root}")
        return 2

    start = datetime.now()
    checker = SafetyFenceChecker()
    checker.check_bare_except(app_root)
    checker.check_safety_decorators(app_root)

    report = FenceReport(
        total_fences=2,
        violations=checker.violations,
        failed_fences=len(set(v.fence_id for v in checker.violations)),
        duration_ms=int((datetime.now() - start).total_seconds() * 1000),
    )
    report.passed_fences = report.total_fences - min(report.failed_fences, report.total_fences)

    if args.json:
        print(
            json.dumps(
                {
                    "total": report.total_fences,
                    "passed": report.passed_fences,
                    "failed": report.failed_fences,
                    "exit_code": report.exit_code,
                    "violations": [
                        {
                            "id": v.fence_id,
                            "severity": v.severity.name,
                            "location": v.location,
                            "message": v.message,
                        }
                        for v in report.violations[:25]
                    ],
                },
                indent=2,
            )
        )
    else:
        print("=" * 60)
        print("FENCE CHECKER v2 REPORT")
        print("=" * 60)
        print(f"Duration: {report.duration_ms}ms")
        print(f"Total: {report.total_fences} | Passed: {report.passed_fences} | Failed: {report.failed_fences}")
        print()

        for sev in [FenceSeverity.CRITICAL, FenceSeverity.ERROR, FenceSeverity.WARNING]:
            vios = [v for v in report.violations if v.severity == sev]
            if vios:
                print(f"{sev.name} ({len(vios)})")
                print("-" * 40)
                for v in vios[:10]:
                    print(f"  {v.location}")
                    print(f"    {v.message}")
                if len(vios) > 10:
                    print(f"  ... and {len(vios) - 10} more")
                print()

        print("=" * 60)
        print(f"Exit Code: {report.exit_code}")

    if args.strict:
        return max((v.severity.value for v in report.violations), default=0)
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
