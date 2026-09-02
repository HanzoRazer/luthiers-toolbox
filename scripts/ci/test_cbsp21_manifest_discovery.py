"""Unit tests for CBSP21 manifest discovery + selection.

These lock in the footgun fix and the post-review hardening:
- per-PR manifests under .cbsp21/patches/ are discovered alongside the legacy file,
- selection uses ONE shared matcher (default_declared_matcher) so both gates agree,
- a genuinely ambiguous match fails loudly instead of resolving by filename,
- a malformed sibling manifest is skipped (with report), not fatal to other PRs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cbsp21_manifest_discovery import (  # noqa: E402
    AmbiguousManifestSelection,
    default_declared_matcher,
    discover_manifest_paths,
    is_cbsp21_internal,
    load_candidates,
    near_miss_candidates,
    owned_candidates,
    select_manifest,
)


def _write(path: Path, patch_id: str, *, files=None, scope_files=None, scope_paths=None):
    """Write a manifest declaring work via any combination of the three forms."""
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "cbsp21_patch_input_v1", "patch_id": patch_id}
    if files is not None:
        manifest["files"] = [{"path": f} for f in files]
    if scope_files is not None or scope_paths is not None:
        manifest["scope"] = {
            "files_expected_to_change": scope_files or [],
            "paths_in_scope": scope_paths or [],
        }
    path.write_text(json.dumps(manifest), encoding="utf-8")


# --------------------------------------------------------------------------- #
# discovery
# --------------------------------------------------------------------------- #

def test_is_cbsp21_internal_covers_patches_and_legacy():
    assert is_cbsp21_internal(".cbsp21/patch_input.json")
    assert is_cbsp21_internal(".cbsp21/patches/foo.json")
    assert is_cbsp21_internal(".cbsp21\\patches\\foo.json")  # windows sep
    assert not is_cbsp21_internal("services/api/app/x.py")


def test_discover_finds_patches_then_legacy(tmp_path: Path):
    _write(tmp_path / ".cbsp21" / "patches" / "b.json", "B", scope_files=["b.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "a.json", "A", scope_files=["a.py"])
    _write(tmp_path / ".cbsp21" / "patch_input.json", "LEGACY", scope_files=["legacy.py"])

    paths = [p.name for p in discover_manifest_paths(tmp_path)]
    assert paths == ["a.json", "b.json", "patch_input.json"]  # patches sorted, legacy last


def test_discover_handles_missing_dir(tmp_path: Path):
    assert discover_manifest_paths(tmp_path) == []


# --------------------------------------------------------------------------- #
# unified matcher — both files[] and scope.* count as "declared"
# --------------------------------------------------------------------------- #

def test_default_matcher_unions_files_and_scope():
    m_files = default_declared_matcher({"files": [{"path": "a.py", "scan_targets": ["b.py"]}]})
    assert m_files("a.py") and m_files("b.py") and not m_files("c.py")

    m_scope = default_declared_matcher(
        {"scope": {"files_expected_to_change": ["a.py"], "paths_in_scope": ["src/"]}}
    )
    assert m_scope("a.py") and m_scope("src/deep/x.py") and not m_scope("other/x.py")


# --------------------------------------------------------------------------- #
# selection — the happy paths
# --------------------------------------------------------------------------- #

def test_selects_manifest_that_covers_the_diff(tmp_path: Path):
    _write(tmp_path / ".cbsp21" / "patches" / "mine.json", "MINE", scope_files=["feature.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "stale.json", "STALE", scope_files=["other.py"])

    candidates, malformed = load_candidates(tmp_path)
    assert malformed == []
    _path, manifest = select_manifest(candidates, ["feature.py"])
    assert manifest["patch_id"] == "MINE"


def test_stale_legacy_does_not_shadow_current_pr(tmp_path: Path):
    _write(tmp_path / ".cbsp21" / "patch_input.json", "OLD_MERGED", scope_files=["old.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "current.json", "CURRENT", scope_files=["new.py"])

    candidates, _ = load_candidates(tmp_path)
    _path, manifest = select_manifest(candidates, ["new.py"])
    assert manifest["patch_id"] == "CURRENT"


def test_tie_break_prefers_more_specific_manifest(tmp_path: Path):
    # Both cover x.py; the tighter manifest (fewer declared tokens) wins — no tie.
    _write(tmp_path / ".cbsp21" / "patches" / "broad.json", "BROAD",
           scope_files=["x.py", "a.py", "b.py", "c.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "tight.json", "TIGHT", scope_files=["x.py"])

    candidates, _ = load_candidates(tmp_path)
    _path, manifest = select_manifest(candidates, ["x.py"])
    assert manifest["patch_id"] == "TIGHT"


def test_no_candidates_returns_none():
    assert select_manifest([], ["x.py"]) is None


# --------------------------------------------------------------------------- #
# selection — zero-overlap vs partial vs empty (CBSP21-DIAG-001 / BR-046)
# --------------------------------------------------------------------------- #

def test_zero_overlap_returns_no_applicable_manifest(tmp_path: Path):
    """BR-046 characterization: changed files + zero overlap → no selection.

    Previously select_manifest returned a deterministic unrelated historical
    winner (covered==0), and the coverage gate printed that stale path at 0.0%.
    Auto-discovery must return None so callers can report "no applicable
    manifest" instead of attributing the failure to an unrelated patch.
    """
    _write(tmp_path / ".cbsp21" / "patches" / "a.json", "A", scope_files=["a.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "b.json", "B", scope_files=["b.py"])
    _write(
        tmp_path / ".cbsp21" / "patches" / "audit-n1-refuted.json",
        "AUDIT_N1",
        scope_files=["docs/unrelated/historical.md"],
    )
    candidates, _ = load_candidates(tmp_path)
    selected = select_manifest(candidates, ["CBSP21_NEGATIVE_TEST_ARTIFACT.md"])
    assert selected is None, (
        "zero-overlap auto-discovery must not select an unrelated historical "
        f"manifest; got {selected[0] if selected else None}"
    )


def test_zero_overlap_does_not_raise_ambiguity(tmp_path: Path):
    """Zero overlap among many stale manifests is absence, not AmbiguousManifestSelection."""
    _write(tmp_path / ".cbsp21" / "patches" / "a.json", "A", scope_files=["a.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "b.json", "B", scope_files=["b.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "c.json", "C", scope_files=["c.py"])
    candidates, _ = load_candidates(tmp_path)
    selected = select_manifest(candidates, ["unrelated.py"])
    assert selected is None


def test_partial_overlap_selects_applicable_manifest(tmp_path: Path):
    """Changed A/B/C with a manifest declaring A/B is FOUND_INCOMPLETE, not NOT_FOUND."""
    _write(
        tmp_path / ".cbsp21" / "patches" / "partial.json",
        "PARTIAL",
        scope_files=["a.py", "b.py"],
    )
    _write(
        tmp_path / ".cbsp21" / "patches" / "stale.json",
        "STALE",
        scope_files=["other.py"],
    )
    candidates, _ = load_candidates(tmp_path)
    selected = select_manifest(candidates, ["a.py", "b.py", "c.py"])
    assert selected is not None
    assert selected[1]["patch_id"] == "PARTIAL"


def test_empty_diff_preserves_deterministic_selection(tmp_path: Path):
    """Empty changed_files is not 'no applicable manifest' (CBSP21-DIAG-001 ruling 3A)."""
    _write(tmp_path / ".cbsp21" / "patches" / "a.json", "A", scope_files=["a.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "b.json", "B", scope_files=["b.py"])
    candidates, _ = load_candidates(tmp_path)
    selected = select_manifest(candidates, [])
    assert selected is not None
    # Deterministic among zero-coverage: lexicographically smallest path.
    assert selected[0].name == "a.json"


# --------------------------------------------------------------------------- #
# selection — ambiguity guard (the review's "surprising winner" concern)
# --------------------------------------------------------------------------- #

def test_overlapping_paths_in_scope_ties_raise(tmp_path: Path):
    # Two manifests with identical broad scope both cover the file equally.
    _write(tmp_path / ".cbsp21" / "patches" / "one.json", "ONE", scope_paths=["scripts/ci/"])
    _write(tmp_path / ".cbsp21" / "patches" / "two.json", "TWO", scope_paths=["scripts/ci/"])
    candidates, _ = load_candidates(tmp_path)
    with pytest.raises(AmbiguousManifestSelection, match="equally plausible"):
        select_manifest(candidates, ["scripts/ci/x.py"])


def test_files_only_vs_scope_only_same_file_is_ambiguous(tmp_path: Path):
    # Same file claimed by two manifests through different declaration forms,
    # with equal specificity -> genuinely ambiguous -> raise (not filename order).
    _write(tmp_path / ".cbsp21" / "patches" / "viafiles.json", "VIAFILES", files=["shared.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "viascope.json", "VIASCOPE",
           scope_files=["shared.py"])
    candidates, _ = load_candidates(tmp_path)
    with pytest.raises(AmbiguousManifestSelection):
        select_manifest(candidates, ["shared.py"])


# --------------------------------------------------------------------------- #
# malformed siblings — skipped, not fatal to unrelated PRs
# --------------------------------------------------------------------------- #

def test_malformed_sibling_is_skipped_not_fatal(tmp_path: Path):
    bad = tmp_path / ".cbsp21" / "patches" / "bad.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("{ not json", encoding="utf-8")
    _write(tmp_path / ".cbsp21" / "patches" / "good.json", "GOOD", scope_files=["mine.py"])

    candidates, malformed = load_candidates(tmp_path)
    # bad one reported, good one still usable
    assert [p.name for p, _ in malformed] == ["bad.json"]
    _path, manifest = select_manifest(candidates, ["mine.py"])
    assert manifest["patch_id"] == "GOOD"


def test_only_malformed_yields_no_candidates(tmp_path: Path):
    bad = tmp_path / ".cbsp21" / "patches" / "bad.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("{ nope", encoding="utf-8")
    candidates, malformed = load_candidates(tmp_path)
    assert candidates == [] and len(malformed) == 1  # gate then fails "no valid manifest"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))


# --------------------------------------------------------------------------- #
# specificity — directory prefixes must not outrank explicit file declarations
# --------------------------------------------------------------------------- #

def test_directory_prefix_does_not_outrank_explicit_per_pr_manifest(tmp_path: Path):
    """Regression: a broad prefix manifest used to hijack multi-file PRs.

    Reproduces the real failure on PR #235. `fence-docs-witness-cired004.json`
    declares paths_in_scope ["docs/handoffs/", ".cbsp21/"] and one file, totalling
    4 tokens. A per-PR manifest naming its five rescued handoffs explicitly totalled
    6 tokens. Both covered all five changed files, so the tie-break on "fewest
    tokens" picked the BROAD manifest, which then failed coverage because its
    files[] did not list those five documents. The PR could not be made to pass by
    declaring its work correctly -- covering five files needs at least five tokens.
    """
    _write(
        tmp_path / ".cbsp21" / "patches" / "broad-accumulator.json", "BROAD",
        scope_paths=["docs/handoffs/", ".cbsp21/"],
        files=["docs/handoffs/SOMETHING_ELSE.md"],
    )
    rescued = [
        "docs/handoffs/A.md", "docs/handoffs/B.md", "docs/handoffs/C.md",
        "docs/handoffs/D.md", "docs/handoffs/E.md",
    ]
    _write(tmp_path / ".cbsp21" / "patches" / "per-pr.json", "PERPR", files=rescued)

    candidates, _ = load_candidates(tmp_path)
    _path, manifest = select_manifest(candidates, rescued)
    assert manifest["patch_id"] == "PERPR", (
        "the per-PR manifest that names its files must win over a directory-prefix "
        "accumulator that merely contains them"
    )


def test_prefix_manifest_still_wins_when_it_alone_covers_the_diff(tmp_path: Path):
    """The weighting must only affect tie-breaks, never coverage ranking.

    A prefix manifest is still the correct answer when nothing else covers the diff;
    otherwise this change would strand every PR that legitimately declares by prefix.
    """
    _write(tmp_path / ".cbsp21" / "patches" / "prefix.json", "PREFIX",
           scope_paths=["services/api/app/ibg_repository/"])
    _write(tmp_path / ".cbsp21" / "patches" / "elsewhere.json", "ELSEWHERE",
           files=["totally/unrelated.py"])

    candidates, _ = load_candidates(tmp_path)
    _path, manifest = select_manifest(
        candidates, ["services/api/app/ibg_repository/x.py",
                     "services/api/app/ibg_repository/y.py"])
    assert manifest["patch_id"] == "PREFIX"


# ---------------------------------------------------------------------------
# CBSP21-NOBORROW-001 — ownership predicate
#
# The defect: a PR touching only package.json + package-lock.json scored a
# GENUINE 100% against dep-sec-pr281-types-node.json, a manifest authored for a
# different PR that legitimately declares those two files. Coverage was never
# coincidental, so no file-set rule can catch it. Ownership is about authorship.
# ---------------------------------------------------------------------------


def _cand(path: str, files: list) -> tuple:
    return (Path(path), {"files": [{"path": f} for f in files]})


def test_noborrow_diff_without_own_manifest_owns_nothing():
    """The #344 reproduction. Must yield zero owned candidates.

    The foreign manifest declares BOTH changed files -- full coverage -- and is
    still not owned, which is the entire point of the predicate.
    """
    foreign = _cand(
        ".cbsp21/patches/dep-sec-pr281-types-node.json",
        ["packages/client/package.json", "packages/client/package-lock.json"],
    )
    changed = ["packages/client/package.json", "packages/client/package-lock.json"]
    assert owned_candidates([foreign], changed) == []


def test_noborrow_diff_that_brought_its_manifest_owns_it():
    mine = _cand(".cbsp21/patches/axios-1200-bump.json", ["packages/client/package.json"])
    changed = ["packages/client/package.json", ".cbsp21/patches/axios-1200-bump.json"]
    assert len(owned_candidates([mine], changed)) == 1


def test_noborrow_selects_only_the_brought_manifest_among_many():
    """A foreign manifest with BETTER coverage must still lose to ownership."""
    foreign = _cand(
        ".cbsp21/patches/other.json",
        ["packages/client/package.json", "packages/client/package-lock.json"],
    )
    mine = _cand(".cbsp21/patches/mine.json", ["packages/client/package.json"])
    changed = [
        "packages/client/package.json",
        "packages/client/package-lock.json",
        ".cbsp21/patches/mine.json",
    ]
    owned = owned_candidates([foreign, mine], changed)
    # Normalise: Path stringifies with backslashes on Windows.
    assert [str(p).replace("\\", "/") for p, _ in owned] == [
        ".cbsp21/patches/mine.json"
    ]


def test_noborrow_path_separators_normalise():
    """Windows git output uses backslashes; ownership must not depend on that."""
    mine = _cand(".cbsp21/patches/mine.json", ["a.py"])
    assert len(owned_candidates([mine], ["a.py", ".cbsp21\patches\mine.json"])) == 1


def test_noborrow_ignores_blank_entries_in_the_diff():
    mine = _cand(".cbsp21/patches/mine.json", ["a.py"])
    assert owned_candidates([mine], ["", "   ", "a.py"]) == []


# ---------------------------------------------------------------------------
# CBSP21-NOBORROW-001, second increment.
#
# Invariant, stated mechanically to remove any "added vs modified" edge case:
#
#   A manifest already present on the base branch is ineligible to satisfy the
#   current PR unless the current PR modifies that manifest.
#
# Since the diff lists a manifest only when the PR adds OR modifies it, "appears
# in the diff" expresses that invariant exactly, with no need to distinguish the
# two cases.
# ---------------------------------------------------------------------------


def test_base_branch_manifest_is_ineligible_unless_this_pr_modifies_it():
    """The invariant, stated directly.

    `historical` is on the base branch and fully covers the diff. It is
    ineligible because this PR did not touch it. The moment the PR modifies it,
    it becomes eligible -- same manifest, same coverage, different provenance.
    """
    historical = _cand(".cbsp21/patches/older-pr.json", ["src/thing.py"])
    diff_without = ["src/thing.py"]
    diff_with = ["src/thing.py", ".cbsp21/patches/older-pr.json"]

    assert owned_candidates([historical], diff_without) == []
    assert len(owned_candidates([historical], diff_with)) == 1


def test_non_dependency_borrow_is_closed_too():
    """The defect is repository-wide, not Dependabot-specific.

    Reproduced on main before this fix: a diff touching only
    services/api/app/rmos/manufacturing_authority_registry.json borrowed
    .cbsp21/patches/rmos-vcarve-converge-001.json and scored 100%. Dependency
    PRs were where it was observed, not the boundary of where it works.
    """
    rmos_historical = _cand(
        ".cbsp21/patches/rmos-vcarve-converge-001.json",
        ["services/api/app/rmos/manufacturing_authority_registry.json"],
    )
    changed = ["services/api/app/rmos/manufacturing_authority_registry.json"]
    assert owned_candidates([rmos_historical], changed) == []


def test_many_historical_manifests_covering_the_same_files_all_lose():
    """Only the brought manifest qualifies, however many others cover the diff.

    Guards the ranking-shaped intuition that a "best" historical manifest might
    still win. Ownership is not a tie-break applied after ranking; it filters
    before ranking runs.
    """
    shared = ["packages/client/package.json", "packages/client/package-lock.json"]
    historicals = [
        _cand(f".cbsp21/patches/historical-{i}.json", shared) for i in range(5)
    ]
    assert owned_candidates(historicals, shared) == []

    mine = _cand(".cbsp21/patches/mine.json", shared)
    owned = owned_candidates(historicals + [mine], shared + [".cbsp21/patches/mine.json"])
    assert [str(p).replace("\\", "/") for p, _ in owned] == [".cbsp21/patches/mine.json"]


def test_historical_manifest_still_valid_for_its_own_original_pr():
    """Tightening the selector must not retroactively invalidate old evidence.

    Replays the diff of the PR that authored the manifest -- which included the
    manifest itself -- and confirms it is still owned. Historical manifests
    remain valid for the change they describe.
    """
    original = _cand(
        ".cbsp21/patches/dep-sec-pr281-types-node.json",
        ["packages/client/package.json", "packages/client/package-lock.json"],
    )
    original_diff = [
        "packages/client/package.json",
        "packages/client/package-lock.json",
        ".cbsp21/patches/dep-sec-pr281-types-node.json",
    ]
    assert len(owned_candidates([original], original_diff)) == 1


def test_non_dependency_pr_with_its_own_manifest_is_unaffected():
    """Ordinary governed work keeps passing; the rule is change-based, not author- or type-based."""
    mine = _cand(
        ".cbsp21/patches/some-feature.json",
        ["services/api/app/feature.py", "services/api/tests/test_feature.py"],
    )
    changed = [
        "services/api/app/feature.py",
        "services/api/tests/test_feature.py",
        ".cbsp21/patches/some-feature.json",
    ]
    assert len(owned_candidates([mine], changed)) == 1


def test_near_miss_lists_what_would_have_been_borrowed():
    """The actionable subset when ownership fails, ranked by temptation."""
    shared = ["packages/client/package.json", "packages/client/package-lock.json"]
    a = _cand(".cbsp21/patches/covers-both.json", shared)
    b = _cand(".cbsp21/patches/covers-one.json", [shared[0]])
    c = _cand(".cbsp21/patches/covers-none.json", ["unrelated/x.py"])

    near = near_miss_candidates([c, b, a], shared)
    assert [(str(p).replace("\\", "/"), n) for p, n in near] == [
        (".cbsp21/patches/covers-both.json", 2),
        (".cbsp21/patches/covers-one.json", 1),
    ]


def test_near_miss_excludes_cbsp21_internals_from_the_count():
    """A manifest must not look like a near miss by declaring itself.

    Same exclusion selection uses -- otherwise every manifest would appear to
    cover any diff that contains a manifest.
    """
    m = _cand(".cbsp21/patches/self.json", [".cbsp21/patches/self.json"])
    assert near_miss_candidates([m], [".cbsp21/patches/self.json"]) == []


def test_near_miss_is_empty_when_diff_is_all_internal():
    m = _cand(".cbsp21/patches/x.json", ["src/a.py"])
    assert near_miss_candidates([m], [".cbsp21/patches/x.json"]) == []
