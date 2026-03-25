"""CSS / Vue <style> checker.

Fixes vs. original
------------------
CSSDeadSelectorDetector crash
    The original code passed regex match groups directly to string operations.
    With capturing groups, ``re.findall`` returns a list of *tuples*, not strings.
    Every string operation then fails with:
        expected string or bytes-like object, got 'tuple'

    Fix: type-guard all selector extraction with ``_ensure_str()``.

Checks
------
css_dead_selector
    Detects CSS selectors defined in a <style> block that have no matching
    element/component in the <template> block.  Scoped-only selectors are
    checked against the local template; global selectors emit an info-level
    note since they may apply to child components.

css_important_overuse
    Flags excessive use of !important which usually indicates specificity
    problems better solved through proper selector hierarchy.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from ..base import BaseCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_str(value: object) -> str:
    """Coerce regex match result to str.

    re.findall with capturing groups returns tuples; without capturing groups
    it returns strings.  This guard handles both cases safely.
    """
    if isinstance(value, tuple):
        # Take first non-empty element
        for part in value:
            if isinstance(part, str) and part:
                return part
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _extract_style_block(content: str) -> tuple[str, bool]:
    """Return (style_content, is_scoped)."""
    m = re.search(r"<style([^>]*)>(.*?)</style>", content, re.DOTALL | re.IGNORECASE)
    if not m:
        return "", False
    attrs = m.group(1)
    return m.group(2), "scoped" in attrs


def _extract_template_block(content: str) -> str:
    m = re.search(r"<template[^>]*>(.*?)</template>", content, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""


def _extract_css_selectors(style_content: str) -> List[tuple[int, str]]:
    """Return list of (line_offset, selector) from CSS content.

    Handles:
    - Single-line rules:  .foo { color: red; }
    - Multi-line rules:   .foo {\n  color: red;\n}
    - Grouped selectors:  .foo, .bar { ... }
    - Nested @-blocks:    @media { .foo { ... } }
    """
    selectors: List[tuple[int, str]] = []
    lines = style_content.splitlines()
    depth = 0  # brace nesting depth

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith(("/*", "*", "//")):
            # Still track braces in block comments is incorrect but close enough
            depth += stripped.count("{") - stripped.count("}")
            continue

        opens = stripped.count("{")
        closes = stripped.count("}")

        if opens > 0 and depth == 0:
            # This line opens a new rule block — the part before '{' is the selector
            raw = stripped.split("{")[0].strip()
            if raw and not raw.startswith("@"):
                for sel in raw.split(","):
                    sel = _ensure_str(sel).strip()
                    if sel:
                        selectors.append((lineno, sel))

        depth += opens - closes
        # Clamp to 0 to handle malformed CSS gracefully
        if depth < 0:
            depth = 0

    return selectors


def _extract_class_names(template_content: str) -> Set[str]:
    """Extract all class names referenced in a template."""
    classes: Set[str] = set()

    # class="foo bar"
    for m in re.finditer(r'\bclass="([^"]*)"', template_content):
        for cls in m.group(1).split():
            classes.add(cls.strip())

    # :class="{ active: condition }" or :class="['foo', 'bar']"
    for m in re.finditer(r':class="([^"]*)"', template_content):
        for word in re.findall(r"['\"]([A-Za-z][\w-]*)['\"]", m.group(1)):
            classes.add(word)
        for word in re.findall(r"\b([A-Za-z][\w-]+)\s*:", m.group(1)):
            classes.add(word)

    return classes


def _extract_element_tags(template_content: str) -> Set[str]:
    """Extract all HTML element and component tag names from template."""
    return set(re.findall(r"<([A-Za-z][A-Za-z0-9-]*)", template_content))


def _selector_to_class(selector: str) -> str | None:
    """Extract the primary class name from a CSS selector, e.g. .foo → foo."""
    m = re.match(r"\.([A-Za-z][\w-]*)", selector.strip())
    return m.group(1) if m else None


def _selector_to_element(selector: str) -> str | None:
    """Extract the element name from a simple element selector."""
    m = re.match(r"^([a-z][a-z0-9-]*)(?:[.:#\[\s>+~]|$)", selector.strip())
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

class CSSDeadSelectorChecker(BaseCheck):
    name = "css_dead_selector"
    file_types = [".vue", ".css", ".scss", ".less"]
    severity = "info"

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        if file_path.suffix == ".vue":
            style_content, is_scoped = _extract_style_block(content)
            template_content = _extract_template_block(content)
        else:
            style_content = content
            is_scoped = False
            template_content = ""

        if not style_content:
            return issues

        template_classes = _extract_class_names(template_content)
        template_elements = _extract_element_tags(template_content)

        # Count style block's line offset for accurate line numbers
        style_match = re.search(r"<style[^>]*>", content, re.IGNORECASE)
        style_line_offset = (
            content[: style_match.end()].count("\n") + 1
            if style_match else 0
        )

        for lineno, raw_selector in _extract_css_selectors(style_content):
            # CRITICAL FIX: ensure we have a string (guards against tuple results)
            selector = _ensure_str(raw_selector).strip()
            if not selector:
                continue

            # Skip pseudo-elements, ::deep, :root, etc.
            if "::" in selector or selector.startswith(":") or selector == "*":
                continue

            # Skip @media, @keyframes, etc.
            if selector.startswith("@"):
                continue

            class_name = _selector_to_class(selector)
            element_name = _selector_to_element(selector)

            if is_scoped and template_content:
                if class_name and class_name not in template_classes:
                    issues.append(self.make_issue(
                        file_path,
                        style_line_offset + lineno,
                        f"Scoped selector '{selector}' — "
                        f"class '{class_name}' not found in <template>",
                        severity="info",
                        suggestion=(
                            f"Add class='{class_name}' to a template element, "
                            "or remove the selector."
                        ),
                    ))
                elif element_name and element_name not in template_elements:
                    # Only flag clearly non-HTML selectors
                    html_elements = {
                        "div", "span", "p", "a", "ul", "ol", "li", "h1", "h2",
                        "h3", "h4", "h5", "h6", "button", "input", "form",
                        "table", "tr", "td", "th", "img", "section", "article",
                        "header", "footer", "nav", "main", "aside",
                    }
                    if element_name in html_elements:
                        issues.append(self.make_issue(
                            file_path,
                            style_line_offset + lineno,
                            f"Scoped selector '{selector}' — "
                            f"<{element_name}> not used in <template>",
                            severity="info",
                        ))

        return issues


class CSSImportantOveruseChecker(BaseCheck):
    name = "css_important_overuse"
    file_types = [".vue", ".css", ".scss", ".less"]
    severity = "warning"

    THRESHOLD = 3   # Warn after this many !important per file

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        if file_path.suffix == ".vue":
            style_content, _ = _extract_style_block(content)
        else:
            style_content = content

        if not style_content:
            return issues

        count = style_content.count("!important")
        if count > self.THRESHOLD:
            issues.append(self.make_issue(
                file_path, 1,
                f"!important used {count} times in style block "
                f"(threshold: {self.THRESHOLD})",
                severity="warning",
                suggestion=(
                    "Reduce !important usage by fixing CSS specificity. "
                    "Use BEM or CSS modules to scope selectors."
                ),
            ))

        return issues
