"""GA-HIST-01..05 — witness known stale-handoff failure classes.

These are recorded deterministic fixtures, not live tests against GitHub's
changing present. Each fixture carries the request, the recorded evidence, and
the expected verdicts; the test rebuilds in-memory adapters from the recorded
evidence and asserts the engine's report.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.grounding_agent.adapters.git_repo import WorktreeStatus
from tools.grounding_agent.adapters.github_api import (
    GitHubAuthError,
    GitHubNotFound,
    GitHubUnavailable,
)
from tools.grounding_agent.engine import ground
from tools.grounding_agent.models import GroundingRequest

from ._fakes import FakeFS, FakeGit, FakeGitHub

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_ERROR_MARKERS = {
    "__auth__": GitHubAuthError("recorded: auth failure"),
    "__unavailable__": GitHubUnavailable("recorded: unavailable"),
    "__not_found__": GitHubNotFound("recorded: 404"),
}


def _fixture_files():
    return sorted(FIXTURES_DIR.glob("*.json"))


def _build_github(recorded):
    prs = {}
    for key, value in (recorded.get("github_prs") or {}).items():
        repo, num = key.split("#")
        prs[(repo, int(num))] = _ERROR_MARKERS.get(value, value) if isinstance(value, str) else value
    refs = {}
    for key, value in (recorded.get("github_refs") or {}).items():
        repo, ref = key.split("@")
        refs[(repo, ref)] = _ERROR_MARKERS.get(value, value) if isinstance(value, str) else value
    return FakeGitHub(prs=prs, refs=refs)


def _build_git(recorded):
    ancestry = {}
    for key, value in (recorded.get("git_ancestry") or {}).items():
        commit, ref = key.split("|")
        ancestry[(commit, ref)] = value
    files = {}
    for key, value in (recorded.get("git_files") or {}).items():
        ref, path = key.split(":", 1)
        files[(ref, path)] = value
    worktree = None
    if recorded.get("worktree"):
        w = recorded["worktree"]
        worktree = WorktreeStatus(
            tracked_dirty=w["tracked_dirty"],
            untracked=w["untracked"],
            tracked_files=w.get("tracked_files", []),
            untracked_files=w.get("untracked_files", []),
        )
    return FakeGit(refs=recorded.get("git_refs") or {}, ancestry=ancestry, files=files, worktree=worktree)


@pytest.mark.parametrize("fixture_path", _fixture_files(), ids=lambda p: p.stem)
def test_historical_fixture(fixture_path):
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    request = GroundingRequest.from_dict(data["request"])
    recorded = data.get("recorded", {})

    report = ground(
        request,
        git=_build_git(recorded),
        github=_build_github(recorded),
        fs=FakeFS(paths=recorded.get("local_paths") or {}),
    )

    expected = data["expected"]
    assert report.status.value == expected["status"], f"{fixture_path.stem}: status"
    assert report.decision.value == expected["decision"], f"{fixture_path.stem}: decision"

    if "material_divergences" in expected:
        assert sorted(report.material_divergences) == sorted(expected["material_divergences"])

    by_id = {c.claim_id: c for c in report.claims}
    for claim_id, verdict in expected.get("claim_verdicts", {}).items():
        assert by_id[claim_id].verdict.value == verdict, f"{fixture_path.stem}:{claim_id} verdict"
    for claim_id, ev in expected.get("evidence_classes", {}).items():
        assert by_id[claim_id].evidence_class.value == ev, f"{fixture_path.stem}:{claim_id} evidence"
    for claim_id, scope in expected.get("scopes", {}).items():
        assert by_id[claim_id].scope == scope
    for claim_id, needle in expected.get("message_contains", {}).items():
        assert needle in by_id[claim_id].message
    for claim_id, reason in expected.get("reasons", {}).items():
        got = by_id[claim_id].reason
        assert (got.value if got is not None else None) == reason, (
            f"{fixture_path.stem}:{claim_id} reason"
        )


def test_all_five_historical_fixtures_present():
    stems = {p.stem for p in _fixture_files()}
    required = {
        "pr_312_not_merged",
        "cursor_artifact_missing",
        "stale_base_sha",
        "pr_state_superseded",
        "cross_repo_lane_conflict",
    }
    assert required.issubset(stems), f"missing fixtures: {required - stems}"
