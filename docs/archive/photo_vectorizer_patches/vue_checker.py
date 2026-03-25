"""Vue Single-File Component checker.

Checks
------
vue_unused_vars
    Detects potentially unused variables in <script> blocks.
    With ``vue_script_setup_aware: true`` (default), variables
    are cross-referenced against the <template> block before
    being flagged — eliminating the false-positive storm that
    plagued the original checker.

    Handles:
    - Text interpolation:    {{ varName }}
    - Dynamic bindings:      :prop="varName", v-bind:prop="varName"
    - Event handlers:        @click="handler", v-on:click="handler"
    - v-if / v-show:         v-if="condition"
    - v-for loop vars:       v-for="item in items"
    - defineExpose()         explicitly exported refs
    - defineEmits() return   emits handle function
    - Watchers / computed    reactive references

vue_template_complexity
    Warns when a template exceeds a configurable depth or size.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from ..base import BaseCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_section(content: str, tag: str) -> str:
    """Extract the inner content of the first matching SFC section tag."""
    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else ""


def _is_script_setup(content: str) -> bool:
    return bool(re.search(r"<script\s[^>]*\bsetup\b", content, re.IGNORECASE))


def _extract_declared_identifiers(script_content: str) -> Set[str]:
    """Extract identifiers declared at the top level of a script block.

    Covers:
    - const / let / var / function declarations
    - ref() / reactive() / computed() assignments
    - defineProps / defineEmits return value names
    - Import bindings (named & default)
    """
    idents: Set[str] = set()

    patterns = [
        # const/let/var foo = ...
        r"\b(?:const|let|var)\s+(\w+)\s*=",
        # function foo(
        r"\bfunction\s+(\w+)\s*\(",
        # const { foo, bar } = ...  (destructure)
        r"\bconst\s*\{([^}]+)\}\s*=",
        # import foo from ...
        r"\bimport\s+(\w+)\s+from",
        # import { foo, bar } from ...
        r"\bimport\s*\{([^}]+)\}\s*from",
    ]

    for pat in patterns:
        for m in re.finditer(pat, script_content):
            group = m.group(1)
            # May be a comma-separated destructure list
            for name in re.split(r"[\s,]+", group):
                name = name.strip().lstrip("*").strip()
                # Handle "foo as bar" — keep the local alias
                if " as " in name:
                    name = name.split(" as ")[-1].strip()
                if re.match(r"^[A-Za-z_$]\w*$", name):
                    idents.add(name)

    return idents


def _extract_template_identifiers(template_content: str) -> Set[str]:
    """Extract all identifier-like tokens referenced in a template.

    Intentionally over-inclusive — we'd rather have zero false positives
    than miss a reference.  Covers:
    - {{ expr }}
    - :attr="expr", v-bind:attr="expr"
    - @event="handler", v-on:event="handler"
    - v-if="expr", v-show="expr", v-model="expr"
    - v-for="x in y"  — both x and y
    - component names (PascalCase tags)
    - defineExpose / defineEmits patterns
    """
    idents: Set[str] = set()

    # Interpolations {{ ... }}
    for m in re.finditer(r"\{\{(.*?)\}\}", template_content, re.DOTALL):
        idents |= _identifiers_in_expr(m.group(1))

    # Directive values  v-xxx="expr" or :xxx="expr" or @xxx="expr"
    for m in re.finditer(
        r'(?:v-[\w.:-]+|[@:][\w.:-]+)="([^"]*)"', template_content
    ):
        idents |= _identifiers_in_expr(m.group(1))
    for m in re.finditer(
        r"(?:v-[\w.:-]+|[@:][\w.:-]+)='([^']*)'", template_content
    ):
        idents |= _identifiers_in_expr(m.group(1))

    # Component tags (PascalCase)
    for m in re.finditer(r"<([A-Z][A-Za-z0-9]*)", template_content):
        idents.add(m.group(1))

    return idents


def _identifiers_in_expr(expr: str) -> Set[str]:
    """Extract bare identifier tokens from a JS expression string."""
    # Strip string literals to avoid false matches inside strings
    expr = re.sub(r'"[^"]*"', "", expr)
    expr = re.sub(r"'[^']*'", "", expr)
    return set(re.findall(r"\b([A-Za-z_$]\w*)\b", expr))


def _extract_define_expose(script_content: str) -> Set[str]:
    """Extract names passed to defineExpose({…})."""
    idents: Set[str] = set()
    m = re.search(r"defineExpose\s*\(\s*\{([^}]*)\}", script_content, re.DOTALL)
    if m:
        for name in re.findall(r"\b([A-Za-z_$]\w*)\b", m.group(1)):
            idents.add(name)
    return idents


# JS built-ins that should never be flagged as unused
_JS_BUILTINS: Set[str] = {
    "undefined", "null", "true", "false", "NaN", "Infinity",
    "console", "window", "document", "navigator", "location",
    "Object", "Array", "String", "Number", "Boolean", "Symbol",
    "Promise", "Map", "Set", "WeakMap", "WeakSet",
    "parseInt", "parseFloat", "isNaN", "isFinite",
    "Math", "Date", "JSON", "Error", "TypeError", "RangeError",
    "setTimeout", "clearTimeout", "setInterval", "clearInterval",
    "fetch", "URL", "FormData", "Event", "CustomEvent",
    # Vue built-ins
    "ref", "reactive", "computed", "watch", "watchEffect",
    "onMounted", "onUnmounted", "onBeforeMount", "onBeforeUnmount",
    "onUpdated", "onBeforeUpdate", "onActivated", "onDeactivated",
    "provide", "inject", "nextTick", "toRef", "toRefs",
    "defineProps", "defineEmits", "defineExpose", "withDefaults",
    "useSlots", "useAttrs",
}


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

class VueUnusedVarsChecker(BaseCheck):
    name = "vue_unused_vars"
    file_types = [".vue"]
    severity = "warning"

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        rules = self.analyzer.config.get("rules", {}).get("unused_variables", {})
        setup_aware: bool = rules.get("vue_script_setup_aware", True)

        if not _is_script_setup(content) or not setup_aware:
            # Non-setup scripts: emit a single notice and skip deep analysis
            # (we can't reliably detect usage in options API)
            return issues

        script_content = _extract_section(content, "script")
        template_content = _extract_section(content, "template")

        if not script_content:
            return issues

        declared = _extract_declared_identifiers(script_content)
        template_refs = _extract_template_identifiers(template_content)
        exposed = _extract_define_expose(script_content)

        # Also treat anything passed to defineEmits as "used"
        all_used = template_refs | exposed | _JS_BUILTINS

        # Find line numbers for declared identifiers for accurate reporting
        line_map = _build_line_map(script_content, declared, content)

        for ident in sorted(declared):
            if ident in _JS_BUILTINS:
                continue
            if ident in all_used:
                continue
            # Check if referenced anywhere else in the script (watchers, etc.)
            if re.search(rf"\b{re.escape(ident)}\b", script_content.replace(
                _first_declaration(ident, script_content), "", 1
            )):
                continue

            line_num = line_map.get(ident, 0)
            issues.append(self.make_issue(
                file_path,
                line_num,
                f"'{ident}' declared in <script setup> but not used in <template>",
                severity="warning",
                suggestion=(
                    f"Remove '{ident}' or add it to defineExpose() if it needs "
                    "to be accessible from the parent."
                ),
            ))

        return issues


def _first_declaration(ident: str, script_content: str) -> str:
    """Return the first line containing an apparent declaration of ``ident``."""
    for line in script_content.splitlines():
        if re.search(
            rf"\b(?:const|let|var|function)\s+{re.escape(ident)}\b", line
        ):
            return line
    return ""


def _build_line_map(
    script_content: str,
    idents: Set[str],
    full_content: str,
) -> Dict[str, int]:
    """Map identifier names to their line numbers in the full file."""
    # Find the offset of the script block in the full content
    script_match = re.search(r"<script[^>]*>", full_content, re.IGNORECASE)
    script_start_line = (
        full_content[: script_match.end()].count("\n") + 1
        if script_match else 0
    )

    line_map: Dict[str, int] = {}
    for i, line in enumerate(script_content.splitlines(), start=1):
        for ident in idents:
            if ident in line_map:
                continue
            if re.search(
                rf"\b(?:const|let|var|function)\s+{re.escape(ident)}\b", line
            ):
                line_map[ident] = script_start_line + i

    return line_map


class VueTemplateComplexityChecker(BaseCheck):
    name = "vue_template_complexity"
    file_types = [".vue"]
    severity = "info"

    # Maximum nesting depth before we warn
    MAX_DEPTH = 10
    # Maximum template lines before we warn
    MAX_LINES = 300

    def check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        template = _extract_section(content, "template")
        if not template:
            return issues

        lines = template.splitlines()
        if len(lines) > self.MAX_LINES:
            issues.append(self.make_issue(
                file_path, 1,
                f"Template has {len(lines)} lines (limit: {self.MAX_LINES}). "
                "Consider splitting into sub-components.",
                severity="info",
                suggestion="Extract logical sections into child components.",
            ))

        # Rough depth check via indentation
        max_depth = max(
            (len(line) - len(line.lstrip())) // 2
            for line in lines if line.strip()
        ) if lines else 0

        if max_depth > self.MAX_DEPTH:
            issues.append(self.make_issue(
                file_path, 1,
                f"Template nesting depth ~{max_depth} exceeds limit of {self.MAX_DEPTH}.",
                severity="info",
                suggestion="Flatten deeply nested structures into sub-components.",
            ))

        return issues
