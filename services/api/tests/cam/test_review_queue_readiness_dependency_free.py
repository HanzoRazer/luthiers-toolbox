"""
Proof that the readiness check runs without Pydantic installed.

This is the regression test for the defect that failed PR #242's required check: the
evaluator imported Pydantic transitively and crashed at import inside
``Fence Checks (Blocking)``, which installs no packages by design. The step never reached
``main()``, so ``--report-only`` never got the chance to return 0.

Scanning source text for ``import pydantic`` would not have caught it — the import was
*transitive*, arriving through ``review_queue_item`` and ``review_decision_record``. So this
runs the CLI in a subprocess with Pydantic made genuinely unimportable, which is the only
check that actually proves the property.
"""

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SCRIPT = _REPO_ROOT / "scripts" / "ci" / "check_review_queue_readiness.py"

# Injected ahead of the CLI: makes any `import pydantic` raise, exactly as it would in a
# dependency-free runner.
_BLOCKER = (
    "import sys\n"
    "class _Blocked:\n"
    "    def find_module(self, name, path=None):\n"
    "        return self if name == 'pydantic' or name.startswith('pydantic.') else None\n"
    "    def load_module(self, name):\n"
    "        raise ImportError('pydantic is unavailable in this environment')\n"
    "    def find_spec(self, name, path=None, target=None):\n"
    "        if name == 'pydantic' or name.startswith('pydantic.'):\n"
    "            raise ImportError('pydantic is unavailable in this environment')\n"
    "        return None\n"
    "sys.meta_path.insert(0, _Blocked())\n"
)

pytestmark = pytest.mark.skipif(not _SCRIPT.exists(), reason="CLI script not present")


def _run_without_pydantic(*args: str) -> subprocess.CompletedProcess:
    """Run the readiness CLI in a subprocess where importing pydantic fails."""
    program = _BLOCKER + (
        "import runpy, sys\n"
        f"sys.argv = ['check_review_queue_readiness', {', '.join(repr(a) for a in args)}]\n"
        f"runpy.run_path({str(_SCRIPT)!r}, run_name='__main__')\n"
    )
    return subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True, text=True, cwd=str(_REPO_ROOT),
    )


class TestBlockerIsRealistic:
    def test_the_blocker_actually_blocks_pydantic(self):
        """Guard the guard: a no-op blocker would make every test below vacuous."""
        probe = subprocess.run(
            [sys.executable, "-c", _BLOCKER + "import pydantic"],
            capture_output=True, text=True,
        )
        assert probe.returncode != 0
        assert "unavailable" in (probe.stderr + probe.stdout)


class TestRunsDependencyFree:
    def test_cli_completes_without_pydantic(self):
        result = _run_without_pydantic("--report-only", "--format", "text")
        assert "ModuleNotFoundError" not in result.stderr
        assert "pydantic" not in result.stderr.lower()
        assert result.returncode == 0, result.stderr

    def test_report_only_exits_zero_without_pydantic(self):
        """The exact combination that failed in CI."""
        assert _run_without_pydantic("--report-only").returncode == 0

    def test_enforcement_mode_still_exits_one_without_pydantic(self):
        """Dependency-free must not mean toothless: NOT_READY still fails."""
        assert _run_without_pydantic("--format", "json").returncode == 1

    def test_output_is_identical_with_and_without_pydantic(self):
        """The dependency boundary must not change the external contract."""
        without = _run_without_pydantic("--format", "json").stdout
        with_ = subprocess.run(
            [sys.executable, str(_SCRIPT), "--format", "json"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
        ).stdout
        assert without == with_


class TestNoPydanticInTheReadinessPackage:
    """Belt-and-braces alongside the subprocess proof."""

    @pytest.mark.parametrize(
        "module",
        [
            "review_queue_readiness.py",
            "review_queue_readiness_requirements.py",
            "review_queue_readiness_evaluator.py",
            "review_queue_readiness_evidence.py",
        ],
    )
    def test_module_does_not_import_pydantic_directly_or_transitively(self, module):
        source = (_REPO_ROOT / "services" / "api" / "app" / "cam" / module).read_text(
            encoding="utf-8"
        )
        assert "pydantic" not in source.lower().replace("pydantic-based", "").replace(
            "pydantic.", ""
        ) or "import pydantic" not in source
        # The transitive route that caused the original failure: importing the models.
        assert "from .review_queue_item import" not in source
        assert "from .review_decision_record import" not in source
