"""Magic number checker with CSS-aware allowlist.

Improvements vs. original
--------------------------
- CSS hex colors (e.g. #ff6600) are never flagged when ``allow_css_values``
  is true (default).
- Common CSS dimension values (0, 1, 2, 100, 50, 16, 8 etc.) are skipped
  in CSS/style contexts.
- Configurable allowlist extends the built-in safe values.
- TypeScript enum values are given a pass (sequential integers are idiomatic).
- Line context is examined: if the line looks like CSS (ends in ;, contains :
  before the number, is in a <style> block), the number is exempt.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from ..base import BaseCheck


# Built-in safe values that are ubiquitous and meaningful
_DEFAULT_SAFE: Set[float] = {
    0, 1, 2, -1, 100,
    # Powers of 2 commonly used in bit operations and sizing
    8, 16, 32, 64, 128, 256, 512, 1024,
    # Common percentages
    50, 25, 75,
    # Angles
    90, 180, 270, 360,
    # Common HTTP status codes handled in logic
    200, 201, 400, 401, 403, 404, 500,
}

# CSS unit pattern (number immediately followed by a unit or %)
_CSS_UNIT_RE = re.compile(
    r"\b\d+(?:\.\d+)?(?:px|em|rem|vh|vw|vmin|vmax|%|pt|pc|cm|mm|in|fr|deg|rad|ms|s)\b"
)

# Hex color (short or long form)
_HEX_COLOR_RE = re.compile(r"#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\b")

# Numeric literal in source code
_NUMBER_RE = re.compile(r"(?<!['\"])\b(\d+(?:\.\d+)?)\b(?!['\"])")

# Patterns that indicate we're in a CSS context
_CSS_PROPERTY_RE = re.compile(r"^\s*[\w-]+\s*:")


def _is_in_style_block(lines: List[str], line_idx: int) -> bool:
    """Heuristic: scan backwards to find the nearest <style or <script tag."""
    for i in range(line_idx - 1, max(line_idx - 200, -1), -1):
        stripped = lines[i].strip().lower()
        if stripped.startswith("<style"):
            return True
        if stripped.startswith("<script"):
            return False
    return False


def _is_css_value(line: str) -> bool:
    """Return True if the line looks like a CSS property value."""
    return bool(_CSS_PROPERTY_RE.match(line)) or line.rstrip().endswith(";")


class MagicNumberChecker(BaseCheck):
    name = "magic_numbers"
    file_types = [".vue", ".ts", ".tsx", ".js", ".jsx", ".py"]
    severity = "info"

    def __init__(self, analyzer: "Any") -> None:
        super().__init__(analyzer)
        rules = analyzer.config.get("rules", {}).get("magic_numbers", {})
        self.enabled: bool = bool(rules.get("enabled", True))
        self.allow_css_values: bool = bool(rules.get("allow_css_values", True))
        extra_allowlist: List = rules.get("allowlist", [])
        self.safe_values: Set[float] = _DEFAULT_SAFE | {float(v) for v in extra_allowlist}

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []

        issues: List[Dict[str, Any]] = []
        lines = content.splitlines()

        for line_idx, line in enumerate(lines):
            # Skip comment lines entirely
            stripped = line.strip()
            if stripped.startswith(("//", "#", "/*", "*")):
                continue

            # Remove string literals from consideration
            clean_line = re.sub(r'"[^"]*"', '""', line)
            clean_line = re.sub(r"'[^']*'", "''", clean_line)
            clean_line = re.sub(r"`[^`]*`", "``", clean_line)

            # Skip hex colors
            if self.allow_css_values and _HEX_COLOR_RE.search(line):
                clean_line = _HEX_COLOR_RE.sub("0", clean_line)

            # Skip CSS unit values
            if self.allow_css_values:
                if _CSS_UNIT_RE.search(line):
                    continue
                if _is_css_value(stripped):
                    continue
                # Check if we're inside a <style> block
                if file_path.suffix == ".vue" and _is_in_style_block(lines, line_idx):
                    continue

            for m in _NUMBER_RE.finditer(clean_line):
                value_str = m.group(1)
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                if value in self.safe_values:
                    continue

                # Skip array/function literal positions (index access, arg literals)
                # but NOT plain assignments — those ARE the magic numbers we want
                context_before = clean_line[: m.start()].rstrip()
                if context_before.endswith(("[",)):
                    continue  # array index: arr[37]

                # Skip: ++i, i++, i += N increment patterns (loop idioms)
                if re.search(r"\b(?:for|while)\b.*\b\w+\s*[+\-*/%]=\s*$",
                             context_before):
                    continue

                # Skip TypeScript enum-style sequential assignments
                if re.search(r"\w+\s*=\s*" + re.escape(value_str) + r"\s*,", clean_line):
                    continue

                issues.append(self.make_issue(
                    file_path,
                    line_idx + 1,
                    f"Magic number {value_str} — consider naming it as a constant",
                    severity="info",
                    suggestion=(
                        f"const DESCRIPTIVE_NAME = {value_str}  "
                        "// explain what this represents"
                    ),
                ))

        return issues
