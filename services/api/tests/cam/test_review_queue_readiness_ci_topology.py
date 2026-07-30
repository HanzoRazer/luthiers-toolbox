"""
CI topology tests for the review-queue readiness check.

These assert the property that TD-3 would have broken: the required status check must
report on EVERY pull request. A path filter on the workflow that hosts it would leave
docs-only PRs stranded at "Expected — waiting", permanently unmergeable.

Static parsing of the workflow file — no CI execution.
"""

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "architecture_scan.yml"

pytestmark = pytest.mark.skipif(
    not _WORKFLOW.exists(), reason="architecture_scan.yml not present"
)


def _text() -> str:
    return _WORKFLOW.read_text(encoding="utf-8")


class TestRequiredCheckAlwaysReports:
    def test_workflow_has_no_path_filter(self):
        """CI-RED-004: a path filter here strands docs-only PRs on the required check."""
        assert "paths:" not in _text()

    def test_workflow_triggers_on_all_pull_requests(self):
        body = _text()
        assert "pull_request:" in body

    def test_required_check_name_is_unchanged(self):
        """The ruleset requires this exact name; renaming it breaks branch protection."""
        assert "name: Fence Checks (Blocking)" in _text()


class TestReadinessStepHosting:
    def test_readiness_step_exists(self):
        assert "Review queue readiness" in _text()

    def test_readiness_runs_in_the_blocking_job_not_a_new_workflow(self):
        """Hosting it in the always-reported job is what keeps docs-only PRs mergeable."""
        body = _text()
        fence_index = body.index("name: Fence Checks (Blocking)")
        readiness_index = body.index("Review queue readiness")
        assert readiness_index > fence_index, (
            "readiness step must live inside the Fence Checks (Blocking) job"
        )

    def test_readiness_runs_report_only_during_rollout(self):
        """Known gaps must not fail the sole required check."""
        assert "--report-only" in _text()

    def test_blocking_job_still_fails_on_error(self):
        assert "continue-on-error: false" in _text()


class TestNoSecondWorkflowIntroduced:
    def test_no_standalone_readiness_workflow_file(self):
        workflows = (_REPO_ROOT / ".github" / "workflows")
        offenders = [
            p.name for p in workflows.glob("*readiness*")
        ]
        assert not offenders, (
            f"a standalone readiness workflow would be conditionally absent: {offenders}"
        )
