"""TOOLS-GITIGNORE-001 — regression witness for the /tools/ ignore rule.

The defect these guard against is silent, which is what makes it dangerous: a
new file under a tracked tool package is ignored, tests still pass because the
file is on disk, `git status` still looks clean, and the PR ships without it.
Already-tracked files behave normally throughout, so nothing looks wrong.

These tests ask git directly via `git check-ignore` rather than re-implementing
gitignore precedence. Re-implementing it would test our model of the rules, not
the rules -- and the original defect was precisely a wrong model of them.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Families deliberately tracked under tools/. Adding a new one means adding a
# `!` rule in .gitignore and a row here.
TRACKED_TOOL_PACKAGES = [
    "tools/codegen",
    "tools/grounding_agent",
    "tools/grounding_agent/adapters",
    "tools/agent_program",
]

# Loose files tracked at the tools/ root.
TRACKED_LOOSE_TOOLS = [
    "tools/archtop-graduation-studio.html",
    "tools/backRadiusCalculator.js",
    "tools/blueprint-reader.html",
    "tools/body-outline-editor.html",
    "tools/package_sessions.sh",
    "tools/production-shop-hub.html",
    "tools/run_helical_smoke.py",
    "tools/smoke_helix_posts.ps1",
    "tools/verify_policy.py",
]


def _is_ignored(relative_path: str) -> bool:
    """Ask git, do not model gitignore ourselves.

    `git check-ignore -q` exits 0 when the path IS ignored, 1 when it is not,
    and >1 on error. The error case is raised rather than folded into "not
    ignored", because a broken invocation must not read as a passing test.
    """
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", relative_path],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    if result.returncode > 1:
        raise RuntimeError(
            f"git check-ignore failed for {relative_path!r}: "
            f"rc={result.returncode} {result.stderr.decode(errors='replace')}"
        )
    return result.returncode == 0


@pytest.mark.parametrize("package", TRACKED_TOOL_PACKAGES)
def test_new_file_in_tracked_package_is_not_ignored(package: str) -> None:
    """A file that does not exist yet must already be un-ignored.

    This is the actual regression. It uses a path that is deliberately absent
    from disk, because the failure mode is about a file being added *later* --
    testing an existing tracked file would pass even under the blanket rule,
    since tracking survives .gitignore.
    """
    candidate = f"{package}/__tools_gitignore_regression_probe__.py"
    assert not _is_ignored(candidate), (
        f"{candidate} is ignored. A new file added to {package} would be "
        "silently dropped from commits while tests pass and git status looks "
        "clean. Add a '!' rule for this package in .gitignore."
    )


@pytest.mark.parametrize("path", TRACKED_LOOSE_TOOLS)
def test_tracked_loose_tool_is_not_ignored(path: str) -> None:
    assert not _is_ignored(path), f"{path} is tracked but ignored by .gitignore"


def test_generated_content_under_tools_stays_ignored() -> None:
    """The un-ignore must not become a blanket un-ignore.

    __pycache__/ is globally ignored (.gitignore line 20) and must remain so
    inside tracked tool packages, otherwise this repair trades one noise problem
    for another.
    """
    assert _is_ignored("tools/grounding_agent/__pycache__/engine.cpython-311.pyc")
    assert _is_ignored("tools/agent_program/__pycache__/analyze_incidents.cpython-311.pyc")


def test_untracked_tools_root_content_is_still_ignored() -> None:
    """A brand-new loose file at the tools/ root is still ignored, by design.

    The repair re-admits *named* families, not the whole directory. Anyone
    adding a new loose tool must declare it -- which is the intent, and is why
    this asserts the ignore rather than treating it as a leftover defect.
    """
    assert _is_ignored("tools/__some_new_undeclared_tool__.py")
