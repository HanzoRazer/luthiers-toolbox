"""Base checker class with auto-registry via __init_subclass__.

Design notes:
  - Checkers are registered automatically when their module is imported.
  - Each checker receives a single file at a time (file-parallel model).
  - Thread safety: checkers must not share mutable state; all results are
    returned as plain dicts rather than written to a shared list.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .analyzer import CodeQualityAnalyzer

_REGISTRY: List[type["BaseCheck"]] = []


def get_registered_checkers() -> List[type["BaseCheck"]]:
    return list(_REGISTRY)


class BaseCheck:
    """Abstract base for all code-quality checks.

    Subclass attributes
    -------------------
    name        Unique snake_case identifier.
    file_types  Extensions this checker cares about, e.g. ['.vue', '.ts'].
                Empty list means "all files".
    severity    Default severity for issues emitted by this checker.
    fixable     True if ``fix()`` is implemented.
    """

    name: ClassVar[str] = ""
    file_types: ClassVar[List[str]] = []
    severity: ClassVar[str] = "warning"
    fixable: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.name:  # Only register concrete checkers that declare a name
            _REGISTRY.append(cls)

    def __init__(self, analyzer: "CodeQualityAnalyzer") -> None:
        self.analyzer = analyzer
        self.config: Dict[str, Any] = analyzer.config.get(self.name, {})

    # ── Public API ────────────────────────────────────────────────────────

    def accepts(self, file_path: Path) -> bool:
        """Return True if this checker should run on ``file_path``."""
        if not self.file_types:
            return True
        return file_path.suffix.lower() in self.file_types

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Run checks against a single file's content.

        Returns a list of raw issue dicts (not yet filtered by baseline).
        Subclasses MUST override this method.
        """
        raise NotImplementedError

    def fix(self, file_path: Path, issue: Dict[str, Any]) -> Optional[str]:
        """Return fixed file content, or None if unfixable.

        Only called when ``fixable = True``.
        """
        return None

    # ── Helpers ───────────────────────────────────────────────────────────

    def make_issue(
        self,
        file_path: Path,
        line: int,
        message: str,
        *,
        severity: Optional[str] = None,
        suggestion: str = "",
    ) -> Dict[str, Any]:
        return {
            "check": self.name,
            "file": str(file_path),
            "line": line,
            "message": message,
            "severity": severity or self.severity,
            "suggestion": suggestion,
        }

    def lines(self, content: str) -> List[str]:
        return content.splitlines()

    def find_all(self, pattern: str, content: str, flags: int = 0) -> List[re.Match]:
        return list(re.finditer(pattern, content, flags))
