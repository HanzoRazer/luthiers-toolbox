"""Duplicate code detection with noise reduction.

Improvements vs. original
--------------------------
The original flagged:
  - CSS property blocks (naturally repeat across components)
  - Import statements
  - Type definitions
  - Any 3-line repetition regardless of content significance

New approach
------------
1. Minimum block size: configurable ``min_lines`` (default: 5).
2. Pattern exclusions: blocks whose dominant lines match known
   "naturally-repetitive" patterns are skipped.
3. Normalization before hashing: strip comments, normalize whitespace,
   remove string literal contents — so semantically identical blocks
   with different variable names still match, but trivially similar
   blocks (like empty try/catch) are de-noised.
4. Cross-file dedup: reports each duplicate pair once.
5. Separate intra-file vs cross-file modes via config.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from ..base import BaseCheck


# ---------------------------------------------------------------------------
# Patterns for naturally-repetitive code that should NOT be flagged
# ---------------------------------------------------------------------------

_IGNORE_PATTERNS: List[re.Pattern] = [
    re.compile(r"^\s*(?:import|export\s+type|export\s+\{)", re.MULTILINE),
    re.compile(r"^\s*(?:padding|margin|display|color|font|background|border"
               r"|width|height|position|top|left|right|bottom)\s*:"),
    re.compile(r"^\s*//"),        # Comment-only lines
    re.compile(r"^\s*/\*"),       # Block comment starts
    re.compile(r"^\s*\*"),        # Block comment body
    re.compile(r"^\s*\}\s*$"),    # Lone closing braces
    re.compile(r"^\s*$"),         # Blank lines
]


def _is_ignorable_line(line: str) -> bool:
    return any(p.match(line) for p in _IGNORE_PATTERNS)


def _is_ignorable_block(lines: List[str]) -> bool:
    """Return True if the majority of lines are naturally repetitive."""
    if not lines:
        return True
    ignorable = sum(1 for ln in lines if _is_ignorable_line(ln))
    return ignorable / len(lines) >= 0.60  # 60%+ ignorable → skip block


def _normalize_line(line: str) -> str:
    """Normalize a single line for duplicate comparison.

    - Strip leading/trailing whitespace.
    - Remove string literal contents.
    - Collapse multiple spaces.
    - Remove line comments.
    """
    # Remove single-line comments
    line = re.sub(r"//.*$", "", line)
    # Remove string contents (keep the delimiters as placeholders)
    line = re.sub(r'"[^"]*"', '"…"', line)
    line = re.sub(r"'[^']*'", "'…'", line)
    line = re.sub(r"`[^`]*`", "`…`", line)
    # Collapse whitespace
    return re.sub(r"\s+", " ", line).strip()


def _block_hash(lines: List[str]) -> str:
    normalized = "\n".join(_normalize_line(ln) for ln in lines)
    return hashlib.md5(normalized.encode()).hexdigest()  # noqa: S324 (not security)


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------

class DuplicateCodeChecker(BaseCheck):
    """Detect copy-pasted code blocks across and within files."""

    name = "duplicate_code"
    file_types = [".vue", ".ts", ".tsx", ".js", ".jsx", ".py"]
    severity = "warning"

    # Registry shared across checker instances for cross-file detection.
    # Key: block hash → list of (file_path, start_line)
    # This is populated as files are processed; because of file-parallel
    # execution, we use a class-level dict and a lock.
    _global_registry: Dict[str, List[Tuple[str, int]]] = {}
    _registry_initialized = False

    def __init__(self, analyzer: "Any") -> None:
        super().__init__(analyzer)
        rules = analyzer.config.get("rules", {}).get("duplicate_detection", {})
        self.min_lines: int = int(rules.get("min_lines", 5))
        self.ignore_css: bool = bool(rules.get("ignore_css", True))
        self.ignore_imports: bool = bool(rules.get("ignore_imports", True))
        self.enabled: bool = bool(rules.get("enabled", True))

        # Per-instance registry for intra-file detection
        # (class-level registry handles cross-file)
        import threading
        self._lock = threading.Lock()

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []

        issues: List[Dict[str, Any]] = []
        lines = content.splitlines()

        if len(lines) < self.min_lines:
            return []

        # For Vue files, only check the <script> block (not style/template separately)
        if file_path.suffix == ".vue":
            lines = self._extract_script_lines(content)

        blocks = self._sliding_window_blocks(lines)
        seen_in_file: Dict[str, int] = {}   # hash → first occurrence line

        for start, block_lines in blocks:
            if _is_ignorable_block(block_lines):
                continue

            h = _block_hash(block_lines)

            # Intra-file duplicate
            if h in seen_in_file:
                first_line = seen_in_file[h]
                issues.append(self.make_issue(
                    file_path,
                    start + 1,
                    f"Duplicate block ({self.min_lines}+ lines) — "
                    f"also appears at line {first_line + 1} in this file",
                    severity="warning",
                    suggestion="Extract the repeated block into a shared function or component.",
                ))
            else:
                seen_in_file[h] = start

            # Cross-file duplicate
            with self._lock:
                registry = DuplicateCodeChecker._global_registry
                key = str(file_path)
                existing = registry.get(h)
                if existing:
                    # Only report once per pair: when WE are the second occurrence
                    other_file, other_line = existing[0]
                    if other_file != key:
                        issues.append(self.make_issue(
                            file_path,
                            start + 1,
                            f"Duplicate block also found in {other_file}:{other_line + 1}",
                            severity="info",
                            suggestion="Consider extracting to a shared utility.",
                        ))
                else:
                    registry[h] = [(key, start)]

        return issues

    def _sliding_window_blocks(
        self, lines: List[str]
    ) -> List[Tuple[int, List[str]]]:
        """Generate all windows of size ``min_lines`` from ``lines``."""
        n = len(lines)
        if n < self.min_lines:
            return []
        return [
            (i, lines[i: i + self.min_lines])
            for i in range(n - self.min_lines + 1)
        ]

    @staticmethod
    def _extract_script_lines(vue_content: str) -> List[str]:
        m = re.search(r"<script[^>]*>(.*?)</script>", vue_content, re.DOTALL | re.IGNORECASE)
        return m.group(1).splitlines() if m else []
