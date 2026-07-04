"""Unit tests for CBSP21 manifest discovery + selection.

These lock in the footgun fix: per-PR manifests under .cbsp21/patches/ are
discovered alongside the legacy single file, and the gate selects exactly the
manifest that covers the current diff (never a stale accumulator).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cbsp21_manifest_discovery import (  # noqa: E402
    discover_manifest_paths,
    is_cbsp21_internal,
    load_candidates,
    select_manifest,
)


def _scope_matcher(manifest):
    expected = set(manifest.get("scope", {}).get("files_expected_to_change", []))

    def is_declared(f: str) -> bool:
        return f in expected

    return is_declared


def _write(path: Path, patch_id: str, files: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "cbsp21_patch_input_v1",
                "patch_id": patch_id,
                "scope": {"files_expected_to_change": files, "paths_in_scope": files},
                "files": [{"path": f} for f in files],
            }
        ),
        encoding="utf-8",
    )


def test_is_cbsp21_internal_covers_patches_and_legacy():
    assert is_cbsp21_internal(".cbsp21/patch_input.json")
    assert is_cbsp21_internal(".cbsp21/patches/foo.json")
    assert is_cbsp21_internal(".cbsp21\\patches\\foo.json")  # windows sep
    assert not is_cbsp21_internal("services/api/app/x.py")


def test_discover_finds_patches_then_legacy(tmp_path: Path):
    _write(tmp_path / ".cbsp21" / "patches" / "b.json", "B", ["b.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "a.json", "A", ["a.py"])
    _write(tmp_path / ".cbsp21" / "patch_input.json", "LEGACY", ["legacy.py"])

    paths = [p.name for p in discover_manifest_paths(tmp_path)]
    # patches sorted first, legacy last
    assert paths == ["a.json", "b.json", "patch_input.json"]


def test_discover_handles_missing_dir(tmp_path: Path):
    assert discover_manifest_paths(tmp_path) == []


def test_selects_manifest_that_covers_the_diff(tmp_path: Path):
    _write(tmp_path / ".cbsp21" / "patches" / "mine.json", "MINE", ["feature.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "stale.json", "STALE", ["other.py"])

    candidates = load_candidates(tmp_path)
    path, manifest = select_manifest(candidates, ["feature.py"], _scope_matcher)
    assert manifest["patch_id"] == "MINE"


def test_stale_legacy_does_not_shadow_current_pr(tmp_path: Path):
    # Legacy file left over from a previously-merged PR declares unrelated files.
    _write(tmp_path / ".cbsp21" / "patch_input.json", "OLD_MERGED", ["old.py"])
    _write(tmp_path / ".cbsp21" / "patches" / "current.json", "CURRENT", ["new.py"])

    candidates = load_candidates(tmp_path)
    _path, manifest = select_manifest(candidates, ["new.py"], _scope_matcher)
    assert manifest["patch_id"] == "CURRENT"


def test_tie_break_prefers_more_specific_manifest(tmp_path: Path):
    # Both cover the changed file; the tighter manifest (fewer declared) wins.
    _write(
        tmp_path / ".cbsp21" / "patches" / "broad.json",
        "BROAD",
        ["x.py", "a.py", "b.py", "c.py"],
    )
    _write(tmp_path / ".cbsp21" / "patches" / "tight.json", "TIGHT", ["x.py"])

    candidates = load_candidates(tmp_path)
    _path, manifest = select_manifest(candidates, ["x.py"], _scope_matcher)
    assert manifest["patch_id"] == "TIGHT"


def test_no_candidates_returns_none():
    assert select_manifest([], ["x.py"], _scope_matcher) is None


def test_invalid_json_fails_loudly(tmp_path: Path):
    bad = tmp_path / ".cbsp21" / "patches" / "bad.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("{ not json", encoding="utf-8")

    with pytest.raises(ValueError, match="bad.json"):
        load_candidates(tmp_path)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
