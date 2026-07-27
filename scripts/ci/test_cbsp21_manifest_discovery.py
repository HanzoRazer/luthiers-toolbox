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


def test_no_coverage_does_not_raise_ambiguity(tmp_path: Path):
    # Two manifests, neither covers the diff -> no meaningful selection, no raise.
    _write(tmp_path / ".cbsp21" / "patches" / "a.json", "A", scope_files=["a.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "b.json", "B", scope_files=["b.py"])
    candidates, _ = load_candidates(tmp_path)
    selected = select_manifest(candidates, ["unrelated.py"])  # covered==0 for both
    assert selected is not None  # returns the deterministic top; downstream coverage fails


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
