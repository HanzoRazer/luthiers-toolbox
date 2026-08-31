"""Engine tests — the GA-001..GA-020 core cases from the dev order."""

from __future__ import annotations

from tools.grounding_agent.adapters.git_repo import WorktreeStatus
from tools.grounding_agent.adapters.github_api import (
    GitHubAuthError,
    GitHubNotFound,
    GitHubUnavailable,
)
from tools.grounding_agent.engine import ground
from tools.grounding_agent.models import (
    ActiveLane,
    ClaimReason,
    ClaimVerdict,
    Confidence,
    EvidenceClass,
    ExecutionDecision,
    GroundingClaim,
    GroundingRequest,
    GroundingStatus,
)

LANE = {
    "project": "Luthiers-Toolbox-Consolidation-Lab",
    "active_repository": "HanzoRazer/luthiers-toolbox",
    "active_program": "RMOS-CONVERGE",
    "active_order": "RMOS-CONVERGE-001B-B2",
    "active_state": "IMPLEMENTATION",
    "cross_repo_policy": "EVIDENCE_ONLY",
}

FULL_SHA = "abcdef1234567890abcdef1234567890abcdef12"


def _req(claims, lane=LANE):
    return GroundingRequest(
        active_lane=ActiveLane.from_dict(lane),
        claims=[GroundingClaim.from_dict(c) for c in claims],
    )


def _pr(**kwargs):
    base = {
        "number": 312,
        "state": "open",
        "draft": False,
        "merged": False,
        "head": {"sha": FULL_SHA},
        "base": {"ref": "main"},
    }
    base.update(kwargs)
    return base


def _by_id(report, claim_id):
    return next(c for c in report.claims if c.claim_id == claim_id)


# --- GA-001 ---------------------------------------------------------------

def test_ga001_all_match(make_git, make_github, make_fs):
    git = make_git(refs={"main": FULL_SHA})
    github = make_github(prs={("HanzoRazer/luthiers-toolbox", 312): _pr(state="closed", merged=True)})
    fs = make_fs(paths={"/tmp": True})
    report = ground(
        _req([
            {"claim_id": "C-1", "type": "repo_head", "repository": "HanzoRazer/luthiers-toolbox",
             "ref": "main", "expected_sha": FULL_SHA, "material": True},
            {"claim_id": "C-2", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 312, "expected": {"merged": True}, "material": True},
        ]),
        git=git, github=github, fs=fs,
    )
    assert report.status is GroundingStatus.MATCH
    assert report.decision is ExecutionDecision.PROCEED
    assert report.summary["matched"] == 2


# --- GA-002 ---------------------------------------------------------------

def test_ga002_material_pr_mismatch_is_stale(make_git, make_github, make_fs):
    github = make_github(prs={("HanzoRazer/luthiers-toolbox", 312): _pr(draft=True, merged=False)})
    report = ground(
        _req([
            {"claim_id": "C-2", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 312, "expected": {"merged": True}, "material": True},
        ]),
        git=make_git(), github=github, fs=make_fs(),
    )
    assert report.status is GroundingStatus.STALE
    assert report.decision is ExecutionDecision.STOP
    assert report.material_divergences == ["C-2"]
    assert _by_id(report, "C-2").evidence_class is EvidenceClass.GITHUB_STATE


# --- GA-003 ---------------------------------------------------------------

def test_ga003_non_material_mismatch_still_proceeds(make_git, make_github, make_fs):
    github = make_github(prs={("HanzoRazer/luthiers-toolbox", 9): _pr(number=9, merged=False)})
    report = ground(
        _req([
            {"claim_id": "C-N", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 9, "expected": {"merged": True}, "material": False},
        ]),
        git=make_git(), github=github, fs=make_fs(),
    )
    assert report.status is GroundingStatus.MATCH
    assert report.decision is ExecutionDecision.PROCEED
    assert _by_id(report, "C-N").verdict is ClaimVerdict.MISMATCH
    assert report.material_divergences == []


# --- GA-004 ---------------------------------------------------------------

def test_ga004_github_unavailable_material_is_blocked(make_git, make_github, make_fs):
    github = make_github(prs={("HanzoRazer/luthiers-toolbox", 312): GitHubUnavailable("503")})
    report = ground(
        _req([
            {"claim_id": "C-2", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 312, "expected": {"merged": True}, "material": True},
        ]),
        git=make_git(), github=github, fs=make_fs(),
    )
    assert report.status is GroundingStatus.BLOCKED
    assert report.decision is ExecutionDecision.STOP
    assert report.blocked_checks == ["C-2"]


# --- GA-005 ---------------------------------------------------------------

def test_ga005_undeterminable_material_claim_insufficient(make_git, make_github, make_fs):
    # repo_head missing expected_sha -> cannot be determined.
    report = ground(
        _req([
            {"claim_id": "C-5", "type": "repo_head", "repository": "HanzoRazer/luthiers-toolbox",
             "ref": "main", "material": True},
        ]),
        git=make_git(refs={"main": FULL_SHA}), github=make_github(), fs=make_fs(),
    )
    assert report.status is GroundingStatus.INSUFFICIENT_EVIDENCE
    assert report.decision is ExecutionDecision.STOP


# --- GA-006 ---------------------------------------------------------------

def test_ga006_ref_sha_exact_match_git_ref(make_git, make_github, make_fs):
    report = ground(
        _req([
            {"claim_id": "C-6", "type": "repo_head", "repository": "HanzoRazer/luthiers-toolbox",
             "ref": "main", "expected_sha": FULL_SHA, "material": True},
        ]),
        git=make_git(refs={"main": FULL_SHA}), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-6")
    assert r.verdict is ClaimVerdict.MATCH
    assert r.evidence_class is EvidenceClass.GIT_REF
    assert r.confidence is Confidence.HIGH


# --- GA-007 ---------------------------------------------------------------

def test_ga007_short_sha_prefix_matches(make_git, make_github, make_fs):
    report = ground(
        _req([
            {"claim_id": "C-7", "type": "repo_head", "repository": "HanzoRazer/luthiers-toolbox",
             "ref": "main", "expected_sha": "abcdef1", "material": True},
        ]),
        git=make_git(refs={"main": FULL_SHA}), github=make_github(), fs=make_fs(),
    )
    assert _by_id(report, "C-7").verdict is ClaimVerdict.MATCH


def test_ga007_too_short_sha_is_insufficient(make_git, make_github, make_fs):
    report = ground(
        _req([
            {"claim_id": "C-7b", "type": "repo_head", "repository": "HanzoRazer/luthiers-toolbox",
             "ref": "main", "expected_sha": "abc", "material": True},
        ]),
        git=make_git(refs={"main": FULL_SHA}), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-7b")
    assert r.verdict is ClaimVerdict.INSUFFICIENT_EVIDENCE
    assert report.status is GroundingStatus.INSUFFICIENT_EVIDENCE


# --- GA-008 / GA-009 ------------------------------------------------------

def test_ga008_ancestry_true_match(make_git, make_github, make_fs):
    git = make_git(refs={"X": "x", "feature": "f"}, ancestry={("X", "feature"): True})
    report = ground(
        _req([
            {"claim_id": "C-8", "type": "commit_ancestor", "commit": "X", "target_ref": "feature",
             "material": True},
        ]),
        git=git, github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-8")
    assert r.verdict is ClaimVerdict.MATCH
    assert r.evidence_class is EvidenceClass.GIT_ANCESTRY


def test_ga009_ancestry_false_mismatch(make_git, make_github, make_fs):
    git = make_git(ancestry={("X", "feature"): False})
    report = ground(
        _req([
            {"claim_id": "C-9", "type": "commit_ancestor", "commit": "X", "target_ref": "feature",
             "material": True},
        ]),
        git=git, github=make_github(), fs=make_fs(),
    )
    assert _by_id(report, "C-9").verdict is ClaimVerdict.MISMATCH
    assert report.status is GroundingStatus.STALE


def test_ancestry_unknown_commit_is_insufficient(make_git, make_github, make_fs):
    git = make_git(ancestry={("X", "feature"): None})
    report = ground(
        _req([
            {"claim_id": "C-9c", "type": "commit_ancestor", "commit": "X", "target_ref": "feature",
             "material": True},
        ]),
        git=git, github=make_github(), fs=make_fs(),
    )
    assert _by_id(report, "C-9c").verdict is ClaimVerdict.INSUFFICIENT_EVIDENCE


# --- GA-010 ---------------------------------------------------------------

def test_ga010_file_exists_at_ref(make_git, make_github, make_fs):
    git = make_git(refs={"main": FULL_SHA}, files={("main", "services/api/app/core/safety.py"): True})
    report = ground(
        _req([
            {"claim_id": "C-10", "type": "file_exists", "repository": "HanzoRazer/luthiers-toolbox",
             "ref": "main", "path": "services/api/app/core/safety.py", "expected": True,
             "material": True},
        ]),
        git=git, github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-10")
    assert r.verdict is ClaimVerdict.MATCH
    assert r.evidence_class is EvidenceClass.FILE_PRESENCE


# --- GA-011 ---------------------------------------------------------------

def test_ga011_local_path_absent_wording(make_git, make_github, make_fs):
    fs = make_fs(paths={"/opt/cursor/artifacts/x.patch": False})
    report = ground(
        _req([
            {"claim_id": "C-11", "type": "local_path_exists",
             "path": "/opt/cursor/artifacts/x.patch", "expected": True, "material": True},
        ]),
        git=make_git(), github=make_github(), fs=fs,
    )
    r = _by_id(report, "C-11")
    assert r.verdict is ClaimVerdict.MISMATCH
    assert r.scope == "LOCAL_ENVIRONMENT"
    assert "not present in current environment" in r.message
    assert "does not exist" not in r.message


# --- GA-012 / GA-013 ------------------------------------------------------

def test_ga012_tracked_dirty(make_git, make_github, make_fs):
    ws = WorktreeStatus(tracked_dirty=True, untracked=False, tracked_files=["a.py"], untracked_files=[])
    report = ground(
        _req([
            {"claim_id": "C-12", "type": "worktree_clean", "material": True},
        ]),
        git=make_git(worktree=ws), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-12")
    assert r.verdict is ClaimVerdict.MISMATCH
    assert r.observed["tracked_dirty"] is True
    assert r.observed["untracked"] is False


def test_ga013_untracked_only_not_collapsed(make_git, make_github, make_fs):
    ws = WorktreeStatus(tracked_dirty=False, untracked=True, tracked_files=[], untracked_files=["new.py"])
    report = ground(
        _req([
            # Default expects tracked clean, untracked allowed -> MATCH.
            {"claim_id": "C-13", "type": "worktree_clean", "material": True},
        ]),
        git=make_git(worktree=ws), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-13")
    assert r.verdict is ClaimVerdict.MATCH
    assert r.observed["untracked"] is True
    assert r.observed["tracked_dirty"] is False


def test_untracked_flagged_when_untracked_clean_expected(make_git, make_github, make_fs):
    ws = WorktreeStatus(tracked_dirty=False, untracked=True, tracked_files=[], untracked_files=["new.py"])
    report = ground(
        _req([
            {"claim_id": "C-13b", "type": "worktree_clean",
             "expected": {"tracked_clean": True, "untracked_clean": True}, "material": True},
        ]),
        git=make_git(worktree=ws), github=make_github(), fs=make_fs(),
    )
    assert _by_id(report, "C-13b").verdict is ClaimVerdict.MISMATCH


# --- GA-014 / GA-015 / GA-016 --------------------------------------------

def test_ga014_active_lane_same_repo(make_git, make_github, make_fs):
    report = ground(
        _req([
            {"claim_id": "C-14", "type": "active_lane",
             "target_repository": "HanzoRazer/luthiers-toolbox", "action": "mutation",
             "material": True},
        ]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-14")
    assert r.verdict is ClaimVerdict.MATCH
    assert r.evidence_class is EvidenceClass.INPUT_CONTRACT


def test_ga015_cross_repo_evidence_permitted(make_git, make_github, make_fs):
    report = ground(
        _req([
            {"claim_id": "C-15", "type": "active_lane",
             "target_repository": "HanzoRazer/code-analysis-tool", "action": "evidence",
             "material": True},
        ]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-15")
    assert r.verdict is ClaimVerdict.MATCH
    assert r.observed["classification"] == "CROSS_REPO_EVIDENCE"


def test_ga016_cross_repo_mutation_blocked_by_policy(make_git, make_github, make_fs):
    report = ground(
        _req([
            {"claim_id": "C-16", "type": "active_lane",
             "target_repository": "HanzoRazer/code-analysis-tool", "action": "mutation",
             "material": True},
        ]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "C-16")
    assert r.verdict is ClaimVerdict.MISMATCH
    assert r.evidence_class is EvidenceClass.INPUT_CONTRACT
    assert r.observed["classification"] == "OUT_OF_LANE_MUTATION"
    assert report.status is GroundingStatus.STALE


# --- GA-017 / GA-018 ------------------------------------------------------

def test_ga017_github_malformed_is_blocked_not_stale(make_git, make_github, make_fs):
    github = make_github(prs={("HanzoRazer/luthiers-toolbox", 312): GitHubUnavailable("malformed JSON")})
    report = ground(
        _req([
            {"claim_id": "C-17", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 312, "expected": {"merged": True}, "material": True},
        ]),
        git=make_git(), github=github, fs=make_fs(),
    )
    assert report.status is GroundingStatus.BLOCKED
    assert _by_id(report, "C-17").verdict is ClaimVerdict.BLOCKED


def test_ga018_missing_token_material_github_blocked(make_git, make_github, make_fs):
    github = make_github(prs={("HanzoRazer/luthiers-toolbox", 312): GitHubAuthError("no token")})
    report = ground(
        _req([
            {"claim_id": "C-18", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 312, "expected": {"merged": True}, "material": True},
        ]),
        git=make_git(), github=github, fs=make_fs(),
    )
    assert report.status is GroundingStatus.BLOCKED


def test_pr_not_found_expected_exists_mismatch(make_git, make_github, make_fs):
    github = make_github(prs={("HanzoRazer/luthiers-toolbox", 999): GitHubNotFound("404")})
    report = ground(
        _req([
            {"claim_id": "C-nf", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 999, "expected": {"merged": True}, "material": True},
        ]),
        git=make_git(), github=github, fs=make_fs(),
    )
    assert _by_id(report, "C-nf").verdict is ClaimVerdict.MISMATCH


def test_precedence_material_mismatch_over_blocked(make_git, make_github, make_fs):
    github = make_github(prs={
        ("HanzoRazer/luthiers-toolbox", 1): _pr(number=1, merged=False),
        ("HanzoRazer/luthiers-toolbox", 2): GitHubUnavailable("503"),
    })
    report = ground(
        _req([
            {"claim_id": "M", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 1, "expected": {"merged": True}, "material": True},
            {"claim_id": "B", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
             "pr_number": 2, "expected": {"merged": True}, "material": True},
        ]),
        git=make_git(), github=github, fs=make_fs(),
    )
    # Material mismatch takes precedence over blocked (spec section 7 ordering).
    assert report.status is GroundingStatus.STALE
    assert report.blocked_checks == ["B"]


# =========================================================================
# v0.2 (GROUNDING-AGENT-002) — handoff_provenance / lane conflict cases.
# active_lane's existing repo/cross-repo behavior is unchanged and covered
# above (GA-014/015/016); these exercise the NEW provenance dimension.
# =========================================================================

FOREIGN = "HanzoRazer/vectorizer-sandbox"


def _preq(claims, *, lane=LANE, evidence_lanes=None):
    payload = {"active_lane": lane, "claims": claims}
    if evidence_lanes is not None:
        payload["evidence_lanes"] = evidence_lanes
    return GroundingRequest.from_dict(payload)


def _prov(claim_id, expected, material=True):
    return {"claim_id": claim_id, "type": "handoff_provenance",
            "expected": expected, "material": material}


def test_ga2_001_exact_lane_match(make_git, make_github, make_fs):
    report = ground(
        _preq([_prov("P", {"repository": "HanzoRazer/luthiers-toolbox",
                           "program": "RMOS-CONVERGE", "work_order": "RMOS-CONVERGE-001B-B2"})]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    assert report.status is GroundingStatus.MATCH
    assert report.decision is ExecutionDecision.PROCEED
    assert _by_id(report, "P").verdict is ClaimVerdict.MATCH


def test_ga2_002_same_repo_wrong_program(make_git, make_github, make_fs):
    report = ground(
        _preq([_prov("P", {"repository": "HanzoRazer/luthiers-toolbox",
                           "program": "SGAQ"})]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "P")
    assert r.verdict is ClaimVerdict.MISMATCH
    assert r.reason is ClaimReason.HANDOFF_LANE_CONFLICT
    assert r.evidence_class is EvidenceClass.INPUT_CONTRACT
    assert report.status is GroundingStatus.STALE
    assert report.decision is ExecutionDecision.STOP


def test_ga2_003_same_program_wrong_work_order(make_git, make_github, make_fs):
    report = ground(
        _preq([_prov("P", {"program": "RMOS-CONVERGE", "work_order": "SOME-OTHER-ORDER",
                           "required": ["work_order"]})]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "P")
    assert r.verdict is ClaimVerdict.MISMATCH
    assert r.reason is ClaimReason.HANDOFF_LANE_CONFLICT
    assert report.status is GroundingStatus.STALE


def test_ga2_004_foreign_repo_evidence_only_permitted(make_git, make_github, make_fs):
    report = ground(
        _preq(
            [_prov("P", {"repository": FOREIGN, "required": ["repository"]})],
            evidence_lanes=[{"repository": FOREIGN, "mode": "EVIDENCE_ONLY"}],
        ),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "P")
    assert r.verdict is ClaimVerdict.MATCH
    assert r.observed.get("classification") == "CROSS_REPO_EVIDENCE"
    assert report.status is GroundingStatus.MATCH


def test_ga2_005_foreign_repo_without_evidence_declaration_conflicts(make_git, make_github, make_fs):
    report = ground(
        _preq([_prov("P", {"repository": FOREIGN, "required": ["repository"]})]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "P")
    assert r.verdict is ClaimVerdict.MISMATCH
    assert r.reason is ClaimReason.HANDOFF_LANE_CONFLICT
    assert report.status is GroundingStatus.STALE


def test_ga2_006_missing_required_provenance_is_insufficient(make_git, make_github, make_fs):
    # program required but not declared -> INSUFFICIENT_EVIDENCE, not a guessed mismatch.
    report = ground(
        _preq([_prov("P", {"repository": "HanzoRazer/luthiers-toolbox",
                           "required": ["repository", "program"]})]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    r = _by_id(report, "P")
    assert r.verdict is ClaimVerdict.INSUFFICIENT_EVIDENCE
    assert r.reason is None
    assert report.status is GroundingStatus.INSUFFICIENT_EVIDENCE
    assert report.decision is ExecutionDecision.STOP


def test_ga2_007_provenance_uses_input_contract_class(make_git, make_github, make_fs):
    report = ground(
        _preq([_prov("P", {"repository": "HanzoRazer/luthiers-toolbox"})]),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    assert _by_id(report, "P").evidence_class is EvidenceClass.INPUT_CONTRACT


def test_ga2_008_lane_match_cannot_override_stale_sha(make_git, make_github, make_fs):
    git = make_git(refs={"main": FULL_SHA})
    report = ground(
        _preq([
            _prov("P", {"repository": "HanzoRazer/luthiers-toolbox", "program": "RMOS-CONVERGE"}),
            {"claim_id": "S", "type": "repo_head", "repository": "HanzoRazer/luthiers-toolbox",
             "ref": "main", "expected_sha": "0000000000000000000000000000000000000000", "material": True},
        ]),
        git=git, github=make_github(), fs=make_fs(),
    )
    assert _by_id(report, "P").verdict is ClaimVerdict.MATCH
    assert _by_id(report, "S").verdict is ClaimVerdict.MISMATCH
    assert report.status is GroundingStatus.STALE


def test_ga2_009_lane_mismatch_dominates_clean_repo(make_git, make_github, make_fs):
    git = make_git(files={("main", "README.md"): True})
    report = ground(
        _preq([
            _prov("P", {"program": "SGAQ", "required": ["program"]}),
            {"claim_id": "F", "type": "file_exists", "ref": "main", "path": "README.md",
             "expected": True, "material": True},
        ]),
        git=git, github=make_github(), fs=make_fs(),
    )
    assert _by_id(report, "F").verdict is ClaimVerdict.MATCH
    assert _by_id(report, "P").verdict is ClaimVerdict.MISMATCH
    assert report.status is GroundingStatus.STALE


def test_ga2_010_evidence_only_does_not_authorize_mutation(make_git, make_github, make_fs):
    # A foreign repo declared as evidence must NOT let an active_lane mutation
    # claim against it pass. active_lane ignores evidence_lanes by design.
    report = ground(
        _preq(
            [{"claim_id": "M", "type": "active_lane", "target_repository": FOREIGN,
              "action": "mutation", "material": True}],
            evidence_lanes=[{"repository": FOREIGN, "mode": "EVIDENCE_ONLY"}],
        ),
        git=make_git(), github=make_github(), fs=make_fs(),
    )
    assert _by_id(report, "M").verdict is ClaimVerdict.MISMATCH
    assert report.status is GroundingStatus.STALE


def test_ga2_012_v01_active_lane_behavior_unchanged(make_git, make_github, make_fs):
    # Same-repo mutation still MATCH; cross-repo mutation still MISMATCH — the
    # existing active_lane claim is untouched by v0.2.
    ok = ground(_preq([{"claim_id": "A", "type": "active_lane",
                        "target_repository": "HanzoRazer/luthiers-toolbox",
                        "action": "mutation", "material": True}]),
                git=make_git(), github=make_github(), fs=make_fs())
    assert _by_id(ok, "A").verdict is ClaimVerdict.MATCH
    assert "classification" not in _by_id(ok, "A").expected  # shape unchanged
