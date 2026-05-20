"""
Governance Utilities Library

Shared utilities for governance scripts. Dependency-free (stdlib only).

Part of Governance Execution Alignment Sprint.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

# Repository root (two levels up from scripts/governance/)
REPO_ROOT = Path(__file__).resolve().parents[2]


class Severity(str, Enum):
    """Governance check severity levels."""
    INFORMATIONAL = "informational"
    ADVISORY = "advisory"
    WARNING = "warning"
    BLOCKING = "blocking"


class CheckStatus(str, Enum):
    """Check execution status."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class GovernanceIssue:
    """A governance finding or violation."""
    id: str
    severity: Severity
    message: str
    path: Optional[str] = None
    line: Optional[int] = None
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class CheckResult:
    """Result of a governance check execution."""
    id: str
    script: str
    description: str
    tier: str
    severity: str
    exists: bool
    passed: bool
    duration_ms: int
    output: str = ""
    error: str = ""
    issues: List[GovernanceIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["issues"] = [i.to_dict() if hasattr(i, "to_dict") else i for i in self.issues]
        return d


@dataclass
class GovernanceReport:
    """Complete governance check report."""
    timestamp: str
    mode: str
    tier: str
    policy_file: Optional[str]
    passed: int
    failed_blocking: int
    failed_warning: int
    failed_advisory: int
    missing_active_scripts: List[str]
    checks: List[CheckResult]
    exit_code: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["checks"] = [c.to_dict() if hasattr(c, "to_dict") else c for c in self.checks]
        return d


def repo_path(*parts: str) -> Path:
    """Construct a path relative to repository root."""
    return REPO_ROOT.joinpath(*parts)


def load_json(path: Path) -> Dict[str, Any]:
    """
    Load JSON file with useful error messages.

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    """
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_json_safe(path: Path) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Load JSON file, returning (data, None) on success or (None, error_message) on failure.
    """
    try:
        data = load_json(path)
        return data, None
    except FileNotFoundError as e:
        return None, str(e)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {path}: {e}"


def write_json_report(path: Path, data: Dict[str, Any], indent: int = 2) -> None:
    """Write JSON report to file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def utc_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


# Default patterns for file iteration
DEFAULT_INCLUDE_PATTERNS = [
    "services/**/*.py",
    "scripts/**/*.py",
    "docs/governance/**/*.md",
    "docs/governance/**/*.json",
]

DEFAULT_EXCLUDE_PATTERNS = [
    ".git/**",
    "node_modules/**",
    "dist/**",
    "build/**",
    "__pycache__/**",
    ".venv/**",
    "venv/**",
    "reports/governance/**",
    "*.pyc",
]


def iter_repo_files(
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    root: Optional[Path] = None
) -> Iterable[Path]:
    """
    Iterate over repository files matching include patterns, excluding specified patterns.

    Args:
        include: Glob patterns to include (default: Python/MD/JSON in services/scripts/docs)
        exclude: Glob patterns to exclude (default: .git, node_modules, etc.)
        root: Root directory (default: REPO_ROOT)

    Yields:
        Path objects for matching files
    """
    root = root or REPO_ROOT
    include = include or DEFAULT_INCLUDE_PATTERNS
    exclude = exclude or DEFAULT_EXCLUDE_PATTERNS

    # Build exclude set for fast lookup
    exclude_set: Set[Path] = set()
    for pattern in exclude:
        exclude_set.update(root.glob(pattern))

    # Yield matching files
    for pattern in include:
        for path in root.glob(pattern):
            if path.is_file() and path not in exclude_set:
                # Also check if any parent is excluded
                excluded = False
                for exc_path in exclude_set:
                    try:
                        path.relative_to(exc_path)
                        excluded = True
                        break
                    except ValueError:
                        continue
                if not excluded:
                    yield path


def print_issues(issues: List[GovernanceIssue], prefix: str = "  ") -> None:
    """Print governance issues in a readable format."""
    for issue in issues:
        severity_tag = f"[{issue.severity.value.upper()}]"
        location = ""
        if issue.path:
            location = f" {issue.path}"
            if issue.line:
                location += f":{issue.line}"
        print(f"{prefix}{severity_tag}{location}: {issue.message}")


def severity_from_string(s: str) -> Severity:
    """Convert string to Severity enum, defaulting to WARNING if unknown."""
    try:
        return Severity(s.lower())
    except ValueError:
        return Severity.WARNING


def is_blocking_severity(severity: str | Severity) -> bool:
    """Check if severity level is blocking."""
    if isinstance(severity, Severity):
        return severity == Severity.BLOCKING
    return severity.lower() == "blocking"


# Policy loading utilities

@dataclass
class PolicyCheck:
    """A check defined in the governance policy."""
    id: str
    script: str
    description: str
    severity: str
    tier: str
    active: bool
    missing_script_behavior: str = "fail"
    owner: str = "governance"
    status_note: Optional[str] = None

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "PolicyCheck":
        return cls(
            id=id,
            script=data.get("script", ""),
            description=data.get("description", ""),
            severity=data.get("severity", "warning"),
            tier=data.get("tier", "ci"),
            active=data.get("active", True),
            missing_script_behavior=data.get("missing_script_behavior", "fail"),
            owner=data.get("owner", "governance"),
            status_note=data.get("status_note"),
        )


def load_policy(path: Path) -> tuple[List[PolicyCheck], Optional[str]]:
    """
    Load governance policy from JSON file.

    Returns:
        (list of PolicyCheck, error_message or None)
    """
    data, err = load_json_safe(path)
    if err:
        return [], err

    checks_data = data.get("checks", {})
    checks = []
    for check_id, check_data in checks_data.items():
        checks.append(PolicyCheck.from_dict(check_id, check_data))

    return checks, None


def validate_policy_scripts(
    policy_checks: List[PolicyCheck],
    root: Optional[Path] = None
) -> tuple[List[PolicyCheck], List[str]]:
    """
    Validate that active policy scripts exist.

    Returns:
        (valid_checks, list of missing script paths for active checks)
    """
    root = root or REPO_ROOT
    valid = []
    missing = []

    for check in policy_checks:
        script_path = root / check.script
        if check.active and not script_path.exists():
            if check.missing_script_behavior == "fail":
                missing.append(check.script)
            # If behavior is "ignore", we skip it silently
        valid.append(check)

    return valid, missing
