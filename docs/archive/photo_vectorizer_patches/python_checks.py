"""Python-specific code quality checkers.

Checks
------
py_bare_except
    Flags ``except:`` without an exception type.  These silently catch
    SystemExit, KeyboardInterrupt, and GeneratorExit — almost never intended.

py_mutable_default
    Detects mutable default arguments (``def f(x=[])`` / ``def f(x={})``).
    These are shared across all calls and cause notorious state-leakage bugs.

py_swallowed_exception
    Finds ``except`` blocks that catch an exception but do nothing with it
    (no re-raise, no log, no assignment).  These hide bugs silently.

py_debug_print
    Detects ``print()`` calls in non-CLI Python files.  These are commonly
    left in accidentally and pollute production logs.

py_broad_except
    Flags ``except Exception:`` without re-raising or logging, which is only
    slightly better than a bare except.

py_todo_fixme
    Surfaces TODO/FIXME/HACK/XXX comments as info-level issues so they appear
    in the analysis report rather than getting lost in the source.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from ..base import BaseCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_strings(line: str) -> str:
    """Remove string literals from a line to avoid false matches inside strings."""
    line = re.sub(r'"[^"]*"', '""', line)
    line = re.sub(r"'[^']*'", "''", line)
    line = re.sub(r"`[^`]*`", "``", line)
    return line


def _is_comment(line: str) -> bool:
    return line.lstrip().startswith("#")


def _except_block_is_empty_or_pass(lines: List[str], except_line_idx: int) -> bool:
    """Check if the except block body is just 'pass' or empty."""
    # Look ahead for the block body
    for i in range(except_line_idx + 1, min(except_line_idx + 5, len(lines))):
        body_line = lines[i].strip()
        if not body_line or body_line.startswith("#"):
            continue
        if body_line == "pass":
            return True
        return False  # Has real content
    return True


def _except_block_reraises(lines: List[str], except_line_idx: int, except_indent: int) -> bool:
    """Check if an except block contains a raise statement."""
    for i in range(except_line_idx + 1, min(except_line_idx + 20, len(lines))):
        line = lines[i]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= except_indent:
            break   # Left the block
        stripped = line.strip()
        if stripped.startswith("raise") or re.search(r"\blog\w*\s*\(", stripped):
            return True
    return False


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

class PythonBareExceptChecker(BaseCheck):
    name = "py_bare_except"
    file_types = [".py"]
    severity = "critical"

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for i, line in enumerate(content.splitlines(), start=1):
            if _is_comment(line):
                continue
            if re.match(r"^\s*except\s*:", line):
                issues.append(self.make_issue(
                    file_path, i,
                    "Bare 'except:' catches SystemExit and KeyboardInterrupt",
                    severity="critical",
                    suggestion="Use 'except Exception:' at minimum, or a specific type.",
                ))
        return issues


class PythonMutableDefaultChecker(BaseCheck):
    name = "py_mutable_default"
    file_types = [".py"]
    severity = "critical"

    # Matches def foo(x=[], y={}, z=set())
    _PATTERN = re.compile(
        r"def\s+\w+\s*\([^)]*\b\w+\s*=\s*(\[\s*\]|\{\s*\}|list\(\s*\)|dict\(\s*\)|set\(\s*\))"
    )

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for i, line in enumerate(content.splitlines(), start=1):
            if _is_comment(line):
                continue
            if self._PATTERN.search(_strip_strings(line)):
                issues.append(self.make_issue(
                    file_path, i,
                    "Mutable default argument — shared state across all calls",
                    severity="critical",
                    suggestion="Use None as default and initialize inside the function body.",
                ))
        return issues


class PythonSwallowedExceptionChecker(BaseCheck):
    name = "py_swallowed_exception"
    file_types = [".py"]
    severity = "warning"

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        lines = content.splitlines()

        for i, line in enumerate(lines):
            if _is_comment(line):
                continue
            # Match "except SomeException:" or "except (A, B):"
            m = re.match(r"^(\s*)except\s+[A-Z(][^:]*:\s*$", line)
            if not m:
                continue
            indent = len(m.group(1))
            if (_except_block_is_empty_or_pass(lines, i) and
                    not _except_block_reraises(lines, i, indent)):
                issues.append(self.make_issue(
                    file_path, i + 1,
                    "Exception caught but silently swallowed (no raise, log, or handling)",
                    severity="warning",
                    suggestion=(
                        "Add logging, re-raise with context "
                        "('raise NewError() from exc'), or handle explicitly."
                    ),
                ))
        return issues


class PythonDebugPrintChecker(BaseCheck):
    name = "py_debug_print"
    file_types = [".py"]
    severity = "warning"

    # Files that legitimately use print()
    _CLI_PATTERNS = re.compile(
        r"(?:__main__|cli|command|manage|script|runner|entry)",
        re.IGNORECASE,
    )

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        # Allow print() in CLI / management scripts
        if self._CLI_PATTERNS.search(file_path.stem):
            return []

        issues: List[Dict[str, Any]] = []
        for i, line in enumerate(content.splitlines(), start=1):
            if _is_comment(line):
                continue
            clean = _strip_strings(line)
            if re.search(r"\bprint\s*\(", clean):
                issues.append(self.make_issue(
                    file_path, i,
                    "print() call — likely debug output left in production code",
                    severity="warning",
                    suggestion="Replace with logging.debug() or logging.info().",
                ))
        return issues


class PythonBroadExceptChecker(BaseCheck):
    name = "py_broad_except"
    file_types = [".py"]
    severity = "warning"

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        lines = content.splitlines()

        for i, line in enumerate(lines):
            if _is_comment(line):
                continue
            m = re.match(r"^(\s*)except\s+Exception\s*(?:as\s+\w+)?\s*:", line)
            if not m:
                continue
            indent = len(m.group(1))
            if not _except_block_reraises(lines, i, indent):
                issues.append(self.make_issue(
                    file_path, i + 1,
                    "'except Exception' without re-raise or logging hides bugs",
                    severity="warning",
                    suggestion=(
                        "Log the exception or re-raise with context. "
                        "Prefer specific exception types where possible."
                    ),
                ))
        return issues


class PythonTodoCommentChecker(BaseCheck):
    name = "py_todo_fixme"
    file_types = [".py", ".ts", ".tsx", ".js", ".jsx", ".vue"]
    severity = "info"

    _PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX|NOCOMMIT)\b", re.IGNORECASE)

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for i, line in enumerate(content.splitlines(), start=1):
            m = self._PATTERN.search(line)
            if m:
                tag = m.group(1).upper()
                rest = line[m.end():].strip().lstrip(":").strip()
                issues.append(self.make_issue(
                    file_path, i,
                    f"{tag}: {rest}" if rest else f"{tag} comment",
                    severity="info",
                ))
        return issues
