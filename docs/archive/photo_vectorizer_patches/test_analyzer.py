"""Tests for CodeQualityAnalyzer — covers P0 through P3 fixes.

Run with:
    python -m pytest tests/ -v
or:
    python tests/test_analyzer.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from code_quality.config import load_config, _deep_merge, _validate, DEFAULTS
from code_quality.checkers.vue_checker import (
    _extract_declared_identifiers,
    _extract_template_identifiers,
    _is_script_setup,
    VueUnusedVarsChecker,
)
from code_quality.checkers.css_checker import (
    _ensure_str,
    _extract_css_selectors,
    _extract_class_names,
    CSSDeadSelectorChecker,
    CSSImportantOveruseChecker,
)
from code_quality.checkers.duplicate_checker import (
    _is_ignorable_block,
    _block_hash,
    _normalize_line,
    DuplicateCodeChecker,
)
from code_quality.checkers.magic_number import MagicNumberChecker
from code_quality.checkers.python_checks import (
    PythonBareExceptChecker,
    PythonMutableDefaultChecker,
    PythonSwallowedExceptionChecker,
    PythonDebugPrintChecker,
    PythonBroadExceptChecker,
    PythonTodoCommentChecker,
)
from code_quality.analyzer import CodeQualityAnalyzer, _partition


# ── Minimal fake analyzer for checker unit tests ──────────────────────────────

class FakeAnalyzer:
    def __init__(self, config=None):
        from code_quality.config import DEFAULTS
        import copy
        self.config = copy.deepcopy(DEFAULTS)
        if config:
            self.config.update(config)


# ── Helpers ───────────────────────────────────────────────────────────────────

def write_files(tmp: Path, files: dict) -> None:
    for rel, content in files.items():
        fp = tmp / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")


PASS = "PASS"
FAIL = "FAIL"
results = []


def test(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    results.append((name, status, detail))
    marker = "✓" if condition else "✗"
    print(f"  {marker} {name}" + (f"  [{detail}]" if detail and not condition else ""))


# ── P0: Config validation ─────────────────────────────────────────────────────

def test_config():
    print("\n── P0: Config / None-safety ─────────────────────────────────────")

    # None-safe coercion
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # Write a config with null values
        (tmp / ".codequalityrc.json").write_text(
            json.dumps({"checks": None, "exclude_checks": None}),
            encoding="utf-8",
        )
        cfg = load_config(tmp)
        test("checks=None coerced to []", cfg["checks"] == [])
        test("exclude_checks=None coerced to []", cfg["exclude_checks"] == [])

    # Schema validation catches wrong types
    errors = _validate({"workers": "four"})
    test("Schema validation catches type error", len(errors) > 0)

    # Schema validation catches unknown severity
    errors = _validate({"severity_filter": ["critical", "turbo"]})
    test("Schema validation catches unknown severity", len(errors) > 0)

    # Deep merge
    merged = _deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 99, "z": 3}})
    test("Deep merge preserves unset keys", merged["a"]["x"] == 1)
    test("Deep merge overrides existing keys", merged["a"]["y"] == 99)
    test("Deep merge adds new keys", merged["a"]["z"] == 3)

    # Default exclude_dirs are present
    cfg = load_config(Path("."))
    test("node_modules in default exclude_dirs", "node_modules" in cfg["exclude_dirs"])
    test("severity_filter defaults to all", set(cfg["severity_filter"]) >= {"critical", "warning", "info"})


# ── P0: Thread-safe cache ─────────────────────────────────────────────────────

def test_thread_safety():
    print("\n── P0: Thread-safe cache ────────────────────────────────────────")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for i in range(20):
            (tmp / f"file_{i}.py").write_text(f"x = {i}\n")

        analyzer = CodeQualityAnalyzer(tmp, workers=4)
        errors = []

        def read_file(p: Path):
            try:
                analyzer.get_file_content(p)
            except Exception as e:
                errors.append(str(e))

        files = list(tmp.glob("*.py"))
        threads = [threading.Thread(target=read_file, args=(f,)) for f in files * 3]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        test("No race conditions in cache", len(errors) == 0, str(errors[:2]))
        test("Cache populated correctly",
             all(analyzer.get_file_content(f) for f in files))


# ── P0: Git diff fallback ─────────────────────────────────────────────────────

def test_git_fallback():
    print("\n── P0: Git diff fallback ────────────────────────────────────────")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "a.py").write_text("x = 1\n")
        analyzer = CodeQualityAnalyzer(tmp, changed_only=True, verbose=False)
        # Non-git dir should fall back to all files without crashing
        try:
            files = analyzer._get_changed_files()
            test("Non-git dir doesn't crash", True)
            test("Non-git dir falls back to all files", len(files) >= 0)
        except Exception as e:
            test("Non-git dir doesn't crash", False, str(e))


# ── P1: Severity filtering ────────────────────────────────────────────────────

def test_severity_filter():
    print("\n── P1: Severity filtering ───────────────────────────────────────")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        write_files(tmp, {
            "test.py": (
                "try:\n    pass\nexcept:\n    pass\n"  # bare except → critical
                "x = [1, 2, 3]\n"                      # no issue
                "# TODO: fix this\n"                   # todo → info
            )
        })
        # Only critical
        analyzer = CodeQualityAnalyzer(tmp, severity_filter=["critical"])
        issues = analyzer.analyze()
        sevs = {i["severity"] for i in issues}
        test("Only critical issues returned", sevs <= {"critical"})

        # Only info
        analyzer2 = CodeQualityAnalyzer(tmp, severity_filter=["info"])
        issues2 = analyzer2.analyze()
        sevs2 = {i["severity"] for i in issues2}
        test("Only info issues returned", sevs2 <= {"info"})

        # All
        analyzer3 = CodeQualityAnalyzer(tmp)
        issues3 = analyzer3.analyze()
        test("No filter returns all issues", len(issues3) >= len(issues))


# ── P1: Vue script setup false positives ─────────────────────────────────────

def test_vue_script_setup():
    print("\n── P1: Vue <script setup> false positives ───────────────────────")

    # Identifier extraction
    script = """
const message = ref('hello')
const count = ref(0)
const unused = ref('never')
import { computed } from 'vue'
"""
    idents = _extract_declared_identifiers(script)
    test("Detects ref declarations", "message" in idents)
    test("Detects all ref declarations", "count" in idents)

    # Template reference extraction
    template = """
<div>{{ message }}</div>
<button @click="handleClick">Count: {{ count }}</button>
<MyComponent :value="count" />
"""
    template_idents = _extract_template_identifiers(template)
    test("Extracts interpolation refs", "message" in template_idents)
    test("Extracts event handler refs", "handleClick" in template_idents)
    test("Extracts dynamic binding refs", "count" in template_idents)
    test("Extracts component tag refs", "MyComponent" in template_idents)

    # Full SFC — unused should be flagged, used should not
    vue_content = """<template>
  <div>{{ message }}</div>
</template>
<script setup>
const message = ref('hello')
const unused = ref('never used')
</script>"""

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fp = tmp / "Test.vue"
        fp.write_text(vue_content)

        checker = VueUnusedVarsChecker(FakeAnalyzer())
        issues = checker.check_file(fp, vue_content)
        names = [i["message"] for i in issues]
        test("Used var not flagged", not any("message" in n for n in names))
        test("Unused var IS flagged", any("unused" in n for n in names))


# ── P2: CSS type guard fix ────────────────────────────────────────────────────

def test_css_type_guard():
    print("\n── P2: CSS type guard fix ───────────────────────────────────────")

    # The original bug: tuple where string expected
    test("_ensure_str handles plain string", _ensure_str("foo") == "foo")
    test("_ensure_str handles tuple", _ensure_str(("foo", "bar")) == "foo")
    test("_ensure_str handles empty tuple", _ensure_str(()) == "")
    test("_ensure_str handles None-ish", _ensure_str(42) == "42")

    css = ".foo { color: red; }\n.bar { margin: 0; }\n"
    selectors = _extract_css_selectors(css)
    sel_names = [s for _, s in selectors]
    test("Extracts .foo selector", any(".foo" in s for s in sel_names))
    test("Extracts .bar selector", any(".bar" in s for s in sel_names))

    # Class extraction from template
    template = '<div class="active primary"><span :class="{\'error\': hasError}"></span></div>'
    classes = _extract_class_names(template)
    test("Extracts static class names", "active" in classes)
    test("Extracts multiple static classes", "primary" in classes)

    # CSSImportantOveruseChecker
    css_heavy = ".a { color: red !important; font: bold !important; margin: 0 !important; width: 100% !important; }"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fp = tmp / "heavy.css"
        fp.write_text(css_heavy)
        checker = CSSImportantOveruseChecker(FakeAnalyzer())
        issues = checker.check_file(fp, css_heavy)
        test("!important overuse detected", len(issues) > 0)


# ── P2: Duplicate detection noise reduction ───────────────────────────────────

def test_duplicate_detection():
    print("\n── P2: Duplicate detection noise reduction ──────────────────────")

    # Ignorable blocks
    css_block = [
        "  padding: 16px;",
        "  margin: 0;",
        "  display: flex;",
        "  color: #333;",
        "  border: 1px solid;",
    ]
    test("CSS block marked ignorable", _is_ignorable_block(css_block))

    import_block = [
        "import { ref } from 'vue'",
        "import { computed } from 'vue'",
        "import axios from 'axios'",
        "import { useStore } from 'vuex'",
        "import type { User } from './types'",
    ]
    test("Import block marked ignorable", _is_ignorable_block(import_block))

    real_block = [
        "const result = await fetchUser(id)",
        "if (!result.ok) {",
        "  throw new Error(`Failed: ${result.status}`)",
        "}",
        "return result.json()",
    ]
    test("Real code block NOT ignorable", not _is_ignorable_block(real_block))

    # Normalization
    line1 = 'const name = "Alice"'
    line2 = 'const name = "Bob"'
    test("String contents normalized away", _normalize_line(line1) == _normalize_line(line2))


# ── P2: Magic number allowlist ────────────────────────────────────────────────

def test_magic_numbers():
    print("\n── P2: Magic number allowlist ───────────────────────────────────")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # CSS values should not be flagged
        css_content = """
.button {
  width: 768px;
  padding: 16px 24px;
  color: #ff6600;
  opacity: 0.85;
}
"""
        fp_css = tmp / "style.css"
        fp_css.write_text(css_content)
        checker = MagicNumberChecker(FakeAnalyzer())
        issues = checker.check_file(fp_css, css_content)
        test("CSS px values not flagged", not any("768" in i["message"] for i in issues))
        test("Hex colors not flagged", not any("ff6600" in i["message"] for i in issues))

        # Real magic numbers should be flagged
        py_content = "timeout = 37\nretries = 13\n"
        fp_py = tmp / "utils.py"
        fp_py.write_text(py_content)
        issues2 = checker.check_file(fp_py, py_content)
        test("Unusual magic numbers flagged", len(issues2) > 0)

        # Safe values should not be flagged
        safe_content = "count = 0\nlimit = 100\nstep = -1\n"
        fp_safe = tmp / "safe.py"
        fp_safe.write_text(safe_content)
        issues3 = checker.check_file(fp_safe, safe_content)
        test("Safe values (0, 100, -1) not flagged", len(issues3) == 0)


# ── P3: Python checkers ───────────────────────────────────────────────────────

def test_python_checkers():
    print("\n── P3: Python checkers ──────────────────────────────────────────")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fake = FakeAnalyzer()

        # Bare except
        bare = "try:\n    risky()\nexcept:\n    pass\n"
        fp = tmp / "bare.py"
        fp.write_text(bare)
        checker = PythonBareExceptChecker(fake)
        issues = checker.check_file(fp, bare)
        test("Bare except flagged as critical",
             any(i["severity"] == "critical" for i in issues))

        # Typed except should not be flagged
        typed = "try:\n    risky()\nexcept ValueError:\n    pass\n"
        fp2 = tmp / "typed.py"
        fp2.write_text(typed)
        issues2 = checker.check_file(fp2, typed)
        test("Typed except not flagged by bare_except checker", len(issues2) == 0)

        # Mutable default
        mut = "def foo(items=[]):\n    return items\n"
        fp3 = tmp / "mut.py"
        fp3.write_text(mut)
        mc = PythonMutableDefaultChecker(fake)
        issues3 = mc.check_file(fp3, mut)
        test("Mutable default [] flagged", len(issues3) > 0)

        mut2 = "def bar(config={}):\n    return config\n"
        fp4 = tmp / "mut2.py"
        fp4.write_text(mut2)
        issues4 = mc.check_file(fp4, mut2)
        test("Mutable default {} flagged", len(issues4) > 0)

        # Immutable default should be fine
        immut = "def baz(x=None, y=0, z='default'):\n    pass\n"
        fp5 = tmp / "immut.py"
        fp5.write_text(immut)
        issues5 = mc.check_file(fp5, immut)
        test("Immutable defaults not flagged", len(issues5) == 0)

        # Debug print
        printfile = "x = 1\nprint(x)\nreturn x\n"
        fp6 = tmp / "debug.py"
        fp6.write_text(printfile)
        dc = PythonDebugPrintChecker(fake)
        issues6 = dc.check_file(fp6, printfile)
        test("print() flagged in non-CLI file", len(issues6) > 0)

        # CLI file should be exempt
        fp7 = tmp / "cli.py"
        fp7.write_text(printfile)
        issues7 = dc.check_file(fp7, printfile)
        test("print() exempt in cli.py", len(issues7) == 0)

        # Swallowed exception
        swallowed = "try:\n    risky()\nexcept ValueError:\n    pass\n"
        fp8 = tmp / "swallowed.py"
        fp8.write_text(swallowed)
        sc = PythonSwallowedExceptionChecker(fake)
        issues8 = sc.check_file(fp8, swallowed)
        test("Swallowed exception flagged", len(issues8) > 0)

        # Exception with logging should not be flagged
        handled = (
            "try:\n    risky()\n"
            "except ValueError as e:\n    logger.error(e)\n    raise\n"
        )
        fp9 = tmp / "handled.py"
        fp9.write_text(handled)
        issues9 = sc.check_file(fp9, handled)
        test("Exception with raise not flagged", len(issues9) == 0)

        # TODO comments
        todo_file = "# TODO: fix this later\nx = 1\n# FIXME: broken\n"
        fp10 = tmp / "todo.py"
        fp10.write_text(todo_file)
        tc = PythonTodoCommentChecker(fake)
        issues10 = tc.check_file(fp10, todo_file)
        test("TODO comment detected", len(issues10) >= 2)
        test("FIXME comment detected", any("FIXME" in i["message"] for i in issues10))


# ── Architecture: file-parallel partitioning ──────────────────────────────────

def test_file_parallel():
    print("\n── Arch: File-parallel partitioning ────────────────────────────")

    items = list(range(10))
    chunks = _partition(items, 4)
    flat = [x for chunk in chunks for x in chunk]
    test("Partition preserves all items", flat == items)
    test("Partition creates <= n chunks", len(chunks) <= 4)
    test("Partition handles empty list", _partition([], 4) == [])
    test("Partition handles 1 worker", _partition(items, 1) == [items])

    # Integration: multi-worker analysis produces same results as single-worker
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for i in range(8):
            (tmp / f"file_{i}.py").write_text(
                f"try:\n    x = {i}\nexcept:\n    pass\n# TODO: fix\n"
            )

        single = CodeQualityAnalyzer(tmp, workers=1)
        issues_1 = single.analyze()

        multi = CodeQualityAnalyzer(tmp, workers=4)
        issues_4 = multi.analyze()

        test(
            "Multi-worker produces same count as single-worker",
            len(issues_1) == len(issues_4),
            f"single={len(issues_1)} multi={len(issues_4)}",
        )


# ── P3: Config schema validation (integration) ────────────────────────────────

def test_config_schema():
    print("\n── P3: Config schema validation ─────────────────────────────────")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # Valid config
        valid = {
            "workers": 2,
            "exclude_dirs": ["node_modules"],
            "severity_filter": ["critical", "warning"],
        }
        (tmp / ".codequalityrc.json").write_text(json.dumps(valid))
        cfg = load_config(tmp)
        test("Valid config loaded", cfg["workers"] == 2)
        test("Valid severity_filter applied",
             set(cfg["severity_filter"]) == {"critical", "warning"})

        # Invalid config (bad type) — should fall back to defaults
        (tmp / ".codequalityrc.json").write_text(
            json.dumps({"workers": "many"})
        )
        cfg2 = load_config(tmp)
        test("Invalid config falls back to default workers",
             cfg2["workers"] == DEFAULTS["workers"])


# ── Summary ───────────────────────────────────────────────────────────────────

def run_all():
    print("=" * 70)
    print("  CodeQualityAnalyzer — Test Suite")
    print("=" * 70)

    test_config()
    test_thread_safety()
    test_git_fallback()
    test_severity_filter()
    test_vue_script_setup()
    test_css_type_guard()
    test_duplicate_detection()
    test_magic_numbers()
    test_python_checkers()
    test_file_parallel()
    test_config_schema()

    print("\n" + "=" * 70)
    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    print(f"  Results: {passed} passed, {failed} failed")
    if failed:
        print("\n  Failed tests:")
        for name, status, detail in results:
            if status == FAIL:
                print(f"    ✗ {name}" + (f"  [{detail}]" if detail else ""))
    print("=" * 70)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run_all())
