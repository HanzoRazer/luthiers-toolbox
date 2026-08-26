"""Grounding engine: validate a request, dispatch each claim to a read-only
adapter, and aggregate a deterministic report.

The engine performs no direct subprocess or network calls; it uses injected
adapters, which makes it fully testable with fixtures.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from . import evidence
from .adapters.filesystem import FileSystemAdapter
from .adapters.git_repo import GitAdapterError, GitRepoAdapter
from .adapters.github_api import (
    GitHubAdapter,
    GitHubAuthError,
    GitHubNotFound,
    GitHubUnavailable,
)
from .models import (
    ClaimResult,
    ClaimType,
    ClaimVerdict,
    Confidence,
    CrossRepoPolicy,
    EvidenceClass,
    GroundingClaim,
    GroundingReport,
    GroundingRequest,
)


def ground(
    request: GroundingRequest,
    *,
    git: GitRepoAdapter,
    github: GitHubAdapter,
    fs: FileSystemAdapter,
) -> GroundingReport:
    """Evaluate every claim and produce a :class:`GroundingReport`."""
    dispatch: Dict[ClaimType, Callable[..., ClaimResult]] = {
        ClaimType.REPO_HEAD: _check_repo_head,
        ClaimType.PR_STATE: _check_pr_state,
        ClaimType.FILE_EXISTS: _check_file_exists,
        ClaimType.LOCAL_PATH_EXISTS: _check_local_path_exists,
        ClaimType.COMMIT_ANCESTOR: _check_commit_ancestor,
        ClaimType.WORKTREE_CLEAN: _check_worktree_clean,
        ClaimType.ACTIVE_LANE: _check_active_lane,
    }

    results = []
    for claim in request.claims:
        handler = dispatch[claim.type]
        results.append(
            handler(claim, request=request, git=git, github=github, fs=fs)
        )

    status, decision = evidence.aggregate_status(results)
    return GroundingReport(
        status=status,
        decision=decision,
        active_lane=request.active_lane.to_dict(),
        repository_state={"active_repository": request.active_lane.active_repository},
        claims=results,
        material_divergences=evidence.material_divergences(results),
        blocked_checks=evidence.blocked_checks(results),
        summary=evidence.summarize(results),
    )


# ---------------------------------------------------------------------------
# Result construction helper
# ---------------------------------------------------------------------------


def _result(
    claim: GroundingClaim,
    verdict: ClaimVerdict,
    evidence_class: EvidenceClass,
    confidence: Confidence,
    *,
    expected: Dict[str, Any] | None = None,
    observed: Dict[str, Any] | None = None,
    source: str | None = None,
    scope: str | None = None,
    message: str = "",
) -> ClaimResult:
    return ClaimResult(
        claim_id=claim.claim_id,
        type=claim.type,
        material=claim.material,
        verdict=verdict,
        evidence_class=evidence_class,
        confidence=confidence,
        expected=expected or {},
        observed=observed or {},
        source=source,
        scope=scope,
        message=message,
    )


# ---------------------------------------------------------------------------
# Claim handlers
# ---------------------------------------------------------------------------


def _check_repo_head(claim, *, request, git, github, fs) -> ClaimResult:
    if not claim.ref or not claim.expected_sha:
        return _result(
            claim,
            ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE,
            Confidence.LOW,
            expected={"ref": claim.ref, "expected_sha": claim.expected_sha},
            message="repo_head requires 'ref' and 'expected_sha'.",
        )

    # Prefer local git evidence; fall back to GitHub for refs the checkout lacks.
    try:
        observed_sha = git.resolve_ref(claim.ref)
    except GitAdapterError:
        observed_sha = None
    evidence_class = EvidenceClass.GIT_REF
    source = f"git ref {claim.ref}"

    if observed_sha is None:
        try:
            data = github.get_ref(claim.repository, claim.ref)
            observed_sha = data.get("sha")
            evidence_class = EvidenceClass.GITHUB_STATE
            source = f"GitHub {claim.repository}@{claim.ref}"
        except GitHubAuthError as exc:
            return _blocked(claim, EvidenceClass.GITHUB_STATE, str(exc),
                            expected={"ref": claim.ref, "expected_sha": claim.expected_sha})
        except GitHubUnavailable as exc:
            return _blocked(claim, EvidenceClass.GITHUB_STATE, str(exc),
                            expected={"ref": claim.ref, "expected_sha": claim.expected_sha})
        except GitHubNotFound:
            return _result(
                claim,
                ClaimVerdict.MISMATCH,
                EvidenceClass.GITHUB_STATE,
                Confidence.HIGH,
                expected={"ref": claim.ref, "expected_sha": claim.expected_sha},
                observed={"ref": "NOT_FOUND"},
                source=f"GitHub {claim.repository}@{claim.ref}",
                message=f"Ref {claim.ref} not found in {claim.repository}.",
            )

    if not observed_sha:
        return _result(
            claim,
            ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE,
            Confidence.LOW,
            expected={"ref": claim.ref, "expected_sha": claim.expected_sha},
            message=f"Could not resolve ref {claim.ref} from any evidence source.",
        )

    comparison = evidence.compare_sha(claim.expected_sha, observed_sha)
    expected_block = {"ref": claim.ref, "sha": evidence.normalize_sha(claim.expected_sha)}
    observed_block = {"ref": claim.ref, "sha": evidence.normalize_sha(observed_sha)}

    if comparison == evidence.ShaComparison.MATCH:
        return _result(
            claim, ClaimVerdict.MATCH, evidence_class, Confidence.HIGH,
            expected=expected_block, observed=observed_block, source=source,
            message=f"{claim.ref} resolves to expected SHA.",
        )
    if comparison == evidence.ShaComparison.MISMATCH:
        return _result(
            claim, ClaimVerdict.MISMATCH, evidence_class, Confidence.HIGH,
            expected=expected_block, observed=observed_block, source=source,
            message=f"Expected {claim.ref}={expected_block['sha']}; observed {observed_block['sha']}.",
        )
    # AMBIGUOUS (short prefix) or INVALID -> not enough to assert a match.
    return _result(
        claim, ClaimVerdict.INSUFFICIENT_EVIDENCE, EvidenceClass.INSUFFICIENT_EVIDENCE,
        Confidence.LOW, expected=expected_block, observed=observed_block, source=source,
        message="Expected SHA is too short/invalid to compare unambiguously.",
    )


def _check_pr_state(claim, *, request, git, github, fs) -> ClaimResult:
    if claim.pr_number is None or not claim.repository:
        return _result(
            claim, ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE, Confidence.LOW,
            message="pr_state requires 'repository' and 'pr_number'.",
        )
    expected = dict(claim.expected or {})
    try:
        pr = github.get_pull_request(claim.repository, claim.pr_number)
    except GitHubAuthError as exc:
        return _blocked(claim, EvidenceClass.GITHUB_STATE, str(exc), expected=expected)
    except GitHubUnavailable as exc:
        return _blocked(claim, EvidenceClass.GITHUB_STATE, str(exc), expected=expected)
    except GitHubNotFound:
        observed = {"exists": False}
        if expected.get("exists", True) is False:
            return _result(
                claim, ClaimVerdict.MATCH, EvidenceClass.GITHUB_STATE, Confidence.HIGH,
                expected=expected, observed=observed,
                source=f"GitHub PR #{claim.pr_number}",
                message=f"PR #{claim.pr_number} absent as expected.",
            )
        return _result(
            claim, ClaimVerdict.MISMATCH, EvidenceClass.GITHUB_STATE, Confidence.HIGH,
            expected=expected, observed=observed,
            source=f"GitHub PR #{claim.pr_number}",
            message=f"Expected PR #{claim.pr_number} to exist; GitHub returned 404.",
        )

    observed = {
        "exists": True,
        "state": pr.get("state"),
        "draft": pr.get("draft"),
        "merged": pr.get("merged"),
        "head_sha": (pr.get("head") or {}).get("sha"),
        "base": (pr.get("base") or {}).get("ref"),
    }

    mismatches = []
    for key, want in expected.items():
        if key == "exists":
            if observed["exists"] != want:
                mismatches.append(f"exists: expected {want}, observed {observed['exists']}")
            continue
        if key == "open":
            got = observed["state"] == "open"
            if got != want:
                mismatches.append(f"open: expected {want}, observed {got}")
            continue
        if key == "closed":
            got = observed["state"] == "closed"
            if got != want:
                mismatches.append(f"closed: expected {want}, observed {got}")
            continue
        if key in ("head_sha",):
            comp = evidence.compare_sha(str(want), str(observed.get("head_sha") or ""))
            if comp != evidence.ShaComparison.MATCH:
                mismatches.append(
                    f"head_sha: expected {want}, observed {observed.get('head_sha')}"
                )
            continue
        # Direct comparison for state/draft/merged/base.
        if observed.get(key) != want:
            mismatches.append(f"{key}: expected {want}, observed {observed.get(key)}")

    if mismatches:
        return _result(
            claim, ClaimVerdict.MISMATCH, EvidenceClass.GITHUB_STATE, Confidence.HIGH,
            expected=expected, observed=observed,
            source=f"GitHub PR #{claim.pr_number}",
            message="; ".join(mismatches) + ".",
        )
    return _result(
        claim, ClaimVerdict.MATCH, EvidenceClass.GITHUB_STATE, Confidence.HIGH,
        expected=expected, observed=observed,
        source=f"GitHub PR #{claim.pr_number}",
        message=f"PR #{claim.pr_number} matches expected state.",
    )


def _check_file_exists(claim, *, request, git, github, fs) -> ClaimResult:
    if not claim.ref or not claim.path:
        return _result(
            claim, ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE, Confidence.LOW,
            message="file_exists requires 'ref' and 'path'.",
        )
    want = (claim.expected or {}).get("exists", True)
    try:
        present = git.file_exists_at_ref(claim.ref, claim.path)
    except GitAdapterError as exc:
        return _blocked(claim, EvidenceClass.FILE_PRESENCE, str(exc),
                        expected={"path": claim.path, "ref": claim.ref, "exists": want})
    if present is None:
        return _result(
            claim, ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE, Confidence.LOW,
            expected={"path": claim.path, "ref": claim.ref, "exists": want},
            source=f"git {claim.ref}:{claim.path}",
            message=f"Ref {claim.ref} could not be resolved in this checkout.",
        )
    observed = {"path": claim.path, "ref": claim.ref, "exists": present}
    expected_block = {"path": claim.path, "ref": claim.ref, "exists": want}
    if present == want:
        return _result(
            claim, ClaimVerdict.MATCH, EvidenceClass.FILE_PRESENCE, Confidence.HIGH,
            expected=expected_block, observed=observed,
            source=f"git {claim.ref}:{claim.path}",
            message=f"{claim.path} presence at {claim.ref} matches expected.",
        )
    return _result(
        claim, ClaimVerdict.MISMATCH, EvidenceClass.FILE_PRESENCE, Confidence.HIGH,
        expected=expected_block, observed=observed,
        source=f"git {claim.ref}:{claim.path}",
        message=f"Expected exists={want} for {claim.path} at {claim.ref}; observed exists={present}.",
    )


def _check_local_path_exists(claim, *, request, git, github, fs) -> ClaimResult:
    if not claim.path:
        return _result(
            claim, ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE, Confidence.LOW,
            message="local_path_exists requires 'path'.",
        )
    want = (claim.expected or {}).get("exists", True)
    present = fs.local_path_exists(claim.path)
    expected_block = {"path": claim.path, "exists": want}
    observed = {"path": claim.path, "exists": present}
    if present == want:
        msg = (
            f"{claim.path} present in current environment."
            if present
            else f"{claim.path} not present in current environment (as expected)."
        )
        return _result(
            claim, ClaimVerdict.MATCH, EvidenceClass.FILE_PRESENCE, Confidence.HIGH,
            expected=expected_block, observed=observed,
            scope="LOCAL_ENVIRONMENT", source="local filesystem", message=msg,
        )
    # Absence is stated as environment-scoped, never as "does not exist"
    # (that would overstate to "never existed", which is not established).
    if not present:
        msg = f"{claim.path} not present in current environment."
    else:
        msg = f"{claim.path} unexpectedly present in current environment."
    return _result(
        claim, ClaimVerdict.MISMATCH, EvidenceClass.FILE_PRESENCE, Confidence.HIGH,
        expected=expected_block, observed=observed,
        scope="LOCAL_ENVIRONMENT", source="local filesystem", message=msg,
    )


def _check_commit_ancestor(claim, *, request, git, github, fs) -> ClaimResult:
    if not claim.commit or not claim.target_ref:
        return _result(
            claim, ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE, Confidence.LOW,
            message="commit_ancestor requires 'commit' and 'target_ref'.",
        )
    want = (claim.expected or {}).get("is_ancestor", True)
    try:
        is_anc = git.is_ancestor(claim.commit, claim.target_ref)
    except GitAdapterError as exc:
        return _blocked(claim, EvidenceClass.GIT_ANCESTRY, str(exc))
    expected_block = {"commit": claim.commit, "target_ref": claim.target_ref, "is_ancestor": want}
    if is_anc is None:
        return _result(
            claim, ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE, Confidence.LOW,
            expected=expected_block,
            source=f"git merge-base --is-ancestor {claim.commit} {claim.target_ref}",
            message="Commit or target ref not present in this checkout.",
        )
    observed = {"commit": claim.commit, "target_ref": claim.target_ref, "is_ancestor": is_anc}
    if is_anc == want:
        return _result(
            claim, ClaimVerdict.MATCH, EvidenceClass.GIT_ANCESTRY, Confidence.HIGH,
            expected=expected_block, observed=observed,
            source="git ancestry",
            message=f"Ancestry is_ancestor={is_anc} matches expected.",
        )
    return _result(
        claim, ClaimVerdict.MISMATCH, EvidenceClass.GIT_ANCESTRY, Confidence.HIGH,
        expected=expected_block, observed=observed, source="git ancestry",
        message=f"Expected is_ancestor={want}; observed is_ancestor={is_anc}.",
    )


def _check_worktree_clean(claim, *, request, git, github, fs) -> ClaimResult:
    expected = dict(claim.expected or {})
    expect_tracked_clean = expected.get("tracked_clean", True)
    expect_untracked_clean = expected.get("untracked_clean", False)
    try:
        status = git.worktree_status()
    except GitAdapterError as exc:
        return _blocked(claim, EvidenceClass.WORKTREE_STATE, str(exc))
    if status is None:
        return _result(
            claim, ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE, Confidence.LOW,
            message="Working-tree status could not be determined.",
        )
    observed = status.to_dict()
    expected_block = {
        "tracked_clean": expect_tracked_clean,
        "untracked_clean": expect_untracked_clean,
    }
    mismatches = []
    if expect_tracked_clean and status.tracked_dirty:
        mismatches.append(f"tracked files dirty ({len(status.tracked_files)})")
    if expect_untracked_clean and status.untracked:
        mismatches.append(f"untracked files present ({len(status.untracked_files)})")
    if mismatches:
        return _result(
            claim, ClaimVerdict.MISMATCH, EvidenceClass.WORKTREE_STATE, Confidence.HIGH,
            expected=expected_block, observed=observed, source="git status --porcelain",
            message="; ".join(mismatches) + ".",
        )
    return _result(
        claim, ClaimVerdict.MATCH, EvidenceClass.WORKTREE_STATE, Confidence.HIGH,
        expected=expected_block, observed=observed, source="git status --porcelain",
        message="Working tree matches expected cleanliness.",
    )


def _check_active_lane(claim, *, request, git, github, fs) -> ClaimResult:
    """Policy check over the input contract (D5). No external evidence.

    Same-repository targets pass. Cross-repository *evidence* references are
    permitted. A cross-repository *mutation* target under an EVIDENCE_ONLY
    policy is a lane conflict.
    """
    lane = request.active_lane
    target_repo = claim.target_repository or claim.repository
    action = (claim.action or "evidence").lower()
    expected_block = {
        "active_repository": lane.active_repository,
        "target_repository": target_repo,
        "action": action,
        "cross_repo_policy": lane.cross_repo_policy.value,
    }

    if not target_repo:
        return _result(
            claim, ClaimVerdict.INSUFFICIENT_EVIDENCE,
            EvidenceClass.INSUFFICIENT_EVIDENCE, Confidence.LOW,
            expected=expected_block,
            message="active_lane requires 'target_repository' (or 'repository').",
        )

    same_repo = target_repo == lane.active_repository
    observed = dict(expected_block)

    if same_repo:
        return _result(
            claim, ClaimVerdict.MATCH, EvidenceClass.INPUT_CONTRACT, Confidence.HIGH,
            expected=expected_block, observed=observed, source="active-lane contract",
            message="Target repository matches the active lane.",
        )

    # Cross-repo from here on.
    if action == "mutation" and lane.cross_repo_policy is CrossRepoPolicy.EVIDENCE_ONLY:
        observed["classification"] = "OUT_OF_LANE_MUTATION"
        return _result(
            claim, ClaimVerdict.MISMATCH, EvidenceClass.INPUT_CONTRACT, Confidence.HIGH,
            expected=expected_block, observed=observed, source="active-lane contract",
            message=(
                f"Cross-repo mutation target {target_repo} conflicts with "
                f"active_repository {lane.active_repository} under EVIDENCE_ONLY policy."
            ),
        )

    # Cross-repo evidence reference: permitted (only evidence reaches here, since
    # v0.1 defines a single policy, EVIDENCE_ONLY, which blocks cross-repo mutation).
    observed["classification"] = "CROSS_REPO_EVIDENCE"
    return _result(
        claim, ClaimVerdict.MATCH, EvidenceClass.INPUT_CONTRACT, Confidence.HIGH,
        expected=expected_block, observed=observed, source="active-lane contract",
        message=f"Cross-repo evidence reference to {target_repo} permitted.",
    )


def _blocked(
    claim: GroundingClaim,
    evidence_class: EvidenceClass,
    reason: str,
    *,
    expected: Dict[str, Any] | None = None,
) -> ClaimResult:
    return _result(
        claim, ClaimVerdict.BLOCKED, evidence_class, Confidence.LOW,
        expected=expected or {}, observed={"error": reason},
        message=f"Evidence source unavailable: {reason}",
    )
