#!/usr/bin/env python3
"""Shared CBSP21 manifest discovery + selection.

The footgun this removes
------------------------
Historically every PR wrote its patch-intent manifest to the single fixed path
``.cbsp21/patch_input.json``. Because all PRs edited one file, any two open PRs
conflicted on it — every second PR to merge had to hand-resolve the manifest
(keep-ours) before it could land.

The fix
-------
Per-PR manifests live in ``.cbsp21/patches/<patch-id>.json`` — one file per PR,
distinct filenames — so PRs never touch the same path and merges never conflict.
The legacy ``.cbsp21/patch_input.json`` is still honored (treated as one more
candidate) so in-flight PRs that predate this change keep passing; new PRs use
the ``patches/`` directory.

Selection, not union
--------------------
Both gates validate the diff against exactly ONE manifest — the one that best
covers the current change set — preserving the 1:1 PR<->manifest binding that
per-manifest checks (coverage_min, behavior_change/why_not_redundant,
architecture_scan) depend on. Stale manifests from previously-merged PRs declare
files that are not in the current diff, so they lose the selection automatically.

These functions are intentionally pure (given a repo root) so they can be unit
tested without git or CI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

CBSP21_DIRNAME = ".cbsp21"
PATCHES_SUBDIR = "patches"
LEGACY_MANIFEST_NAME = "patch_input.json"

Manifest = Dict[str, object]
Candidate = Tuple[Path, Manifest]
# A matcher decides whether one changed file is declared by a given manifest.
DeclaredMatcher = Callable[[Manifest], Callable[[str], bool]]


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip()


def is_cbsp21_internal(path: str) -> bool:
    """True for the manifests themselves and anything else under ``.cbsp21/``.

    These files never count as "declared work" and never contribute to the
    coverage signal used to pick a manifest, so a manifest cannot win selection
    merely by declaring itself.
    """
    p = _norm(path)
    return p == CBSP21_DIRNAME or p.startswith(CBSP21_DIRNAME + "/")


def discover_manifest_paths(root: Path | str = ".") -> List[Path]:
    """Return every candidate manifest path: ``patches/*.json`` then legacy.

    Ordering is deterministic (sorted patches first, legacy last) so downstream
    tie-breaks are reproducible.
    """
    root = Path(root)
    patches_dir = root / CBSP21_DIRNAME / PATCHES_SUBDIR
    legacy = root / CBSP21_DIRNAME / LEGACY_MANIFEST_NAME

    paths: List[Path] = []
    if patches_dir.is_dir():
        paths.extend(sorted(patches_dir.glob("*.json")))
    if legacy.exists():
        paths.append(legacy)
    return paths


def load_manifest(path: Path | str) -> Manifest:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_candidates(root: Path | str = ".") -> List[Candidate]:
    """Discover and parse every candidate manifest.

    Raises ValueError (with the offending path) if any manifest is invalid JSON,
    so a malformed sibling manifest fails loudly rather than being silently
    skipped.
    """
    candidates: List[Candidate] = []
    for path in discover_manifest_paths(root):
        try:
            candidates.append((path, load_manifest(path)))
        except Exception as exc:  # noqa: BLE001 — re-raise with context
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    return candidates


def _declared_size(manifest: Manifest) -> int:
    """Rough specificity measure across all declaration fields (for tie-breaks).

    Smaller = more specific = preferred, so a tight per-PR manifest beats a broad
    accumulator when both cover the same number of changed files.
    """
    tokens: set[str] = set()
    scope = manifest.get("scope")
    if isinstance(scope, dict):
        for key in ("files_expected_to_change", "paths_in_scope"):
            val = scope.get(key)
            if isinstance(val, list):
                tokens.update(str(v) for v in val)
    files = manifest.get("files")
    if isinstance(files, list):
        for entry in files:
            if isinstance(entry, dict):
                if entry.get("path"):
                    tokens.add(str(entry["path"]))
                targets = entry.get("scan_targets")
                if isinstance(targets, list):
                    tokens.update(str(t) for t in targets)
    return len(tokens)


def select_manifest(
    candidates: List[Candidate],
    changed_files: List[str],
    declared_matcher: DeclaredMatcher,
) -> Optional[Candidate]:
    """Pick the candidate that best covers the current diff.

    Ranking (deterministic):
      1. most changed files covered (excluding ``.cbsp21/`` internals from the
         signal),
      2. then fewest declared tokens (most specific),
      3. then lexicographically smallest path.

    Returns None only when there are no candidates at all.
    """
    if not candidates:
        return None

    signal = [f for f in changed_files if not is_cbsp21_internal(f)]

    def rank_key(item: Candidate):
        path, manifest = item
        matcher = declared_matcher(manifest)
        covered = sum(1 for f in signal if matcher(_norm(f)))
        return (-covered, _declared_size(manifest), str(path))

    return sorted(candidates, key=rank_key)[0]
