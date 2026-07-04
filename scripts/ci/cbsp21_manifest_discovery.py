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

Two design guarantees added after review
-----------------------------------------
1. **Both gates select identically.** Selection uses ONE shared matcher
   (``default_declared_matcher``, the union of ``files[]`` and ``scope.*``), so
   the coverage gate and the patch-input gate can never validate against
   different manifests for the same diff. Each gate still applies its own
   *validation* rules afterwards.
2. **Genuine ambiguity fails loudly.** If two manifests are truly
   indistinguishable for a diff (same coverage AND same specificity), selection
   raises ``AmbiguousManifestSelection`` rather than silently picking by
   filename. A malformed *non-selected* manifest is skipped with a warning (via
   ``load_candidates``) so one bad file in the shared directory cannot fail every
   other PR — but the PR whose OWN manifest is broken still fails, because no
   valid manifest will cover its diff.

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
Malformed = Tuple[Path, str]
# A matcher decides whether one changed file is declared by a given manifest.
DeclaredMatcher = Callable[[Manifest], Callable[[str], bool]]


class AmbiguousManifestSelection(Exception):
    """Raised when >1 manifest is equally plausible for a diff.

    Deliberately fails the gate: silently resolving by filename would make CI
    depend on manifest naming conventions. The author should make one manifest's
    scope specific to its PR.
    """


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip()


def _as_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


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


def load_candidates(root: Path | str = ".") -> Tuple[List[Candidate], List[Malformed]]:
    """Discover and parse every candidate manifest.

    Returns ``(candidates, malformed)``. Malformed manifests (invalid JSON) are
    collected — NOT raised — so one bad sibling file cannot fail an unrelated
    PR's gate. Callers should surface ``malformed`` as a warning; the PR whose
    own manifest is the broken one still fails downstream because no valid
    manifest will cover its diff.
    """
    candidates: List[Candidate] = []
    malformed: List[Malformed] = []
    for path in discover_manifest_paths(root):
        try:
            candidates.append((path, load_manifest(path)))
        except Exception as exc:  # noqa: BLE001 — capture, don't abort discovery
            malformed.append((path, str(exc)))
    return candidates, malformed


def default_declared_matcher(manifest: Manifest) -> Callable[[str], bool]:
    """The shared selection matcher: union of ``files[]`` and ``scope.*``.

    A changed file is "declared" by this manifest if it is named in
    ``files[].path``/``files[].scan_targets`` or ``scope.files_expected_to_change``
    (exact), or falls under a ``scope.paths_in_scope`` prefix. Using one matcher
    for BOTH gates guarantees they select the same manifest for a given diff.
    """
    exact: set[str] = set()
    prefixes: List[str] = []

    scope = manifest.get("scope")
    if isinstance(scope, dict):
        exact.update(_norm(v) for v in _as_list(scope.get("files_expected_to_change")))
        prefixes.extend(_norm(p) for p in _as_list(scope.get("paths_in_scope")))

    files = manifest.get("files")
    if isinstance(files, list):
        for entry in files:
            if isinstance(entry, dict):
                if entry.get("path"):
                    exact.add(_norm(str(entry["path"])))
                exact.update(_norm(t) for t in _as_list(entry.get("scan_targets")))

    def is_declared(file_path: str) -> bool:
        f = _norm(file_path)
        if f in exact:
            return True
        for p in prefixes:
            p = p.rstrip("/")
            if p and (f == p or f.startswith(p + "/")):
                return True
        return False

    return is_declared


def _declared_size(manifest: Manifest) -> int:
    """Rough specificity measure across all declaration fields (for tie-breaks).

    Smaller = more specific = preferred, so a tight per-PR manifest beats a broad
    accumulator when both cover the same number of changed files.
    """
    tokens: set[str] = set()
    scope = manifest.get("scope")
    if isinstance(scope, dict):
        for key in ("files_expected_to_change", "paths_in_scope"):
            tokens.update(_as_list(scope.get(key)))
    files = manifest.get("files")
    if isinstance(files, list):
        for entry in files:
            if isinstance(entry, dict):
                if entry.get("path"):
                    tokens.add(str(entry["path"]))
                tokens.update(_as_list(entry.get("scan_targets")))
    return len(tokens)


def select_manifest(
    candidates: List[Candidate],
    changed_files: List[str],
    declared_matcher: Optional[DeclaredMatcher] = None,
) -> Optional[Candidate]:
    """Pick the candidate that best covers the current diff.

    Ranking (deterministic):
      1. most changed files covered (excluding ``.cbsp21/`` internals from the
         signal),
      2. then fewest declared tokens (most specific),
      3. then lexicographically smallest path (stable ordering only).

    Selection uses ``default_declared_matcher`` unless a matcher is injected
    (tests). Both production gates use the default, so they always agree.

    Raises:
        AmbiguousManifestSelection: if >1 manifest ties on (coverage>0,
            specificity) — a real ambiguity that naming order must not resolve.

    Returns None only when there are no candidates at all.
    """
    if not candidates:
        return None

    matcher_factory = declared_matcher or default_declared_matcher
    signal = [f for f in changed_files if not is_cbsp21_internal(f)]

    scored: List[Tuple[int, int, str, Candidate]] = []
    for path, manifest in candidates:
        matcher = matcher_factory(manifest)
        covered = sum(1 for f in signal if matcher(_norm(f)))
        scored.append((covered, _declared_size(manifest), str(path), (path, manifest)))

    scored.sort(key=lambda s: (-s[0], s[1], s[2]))
    top = scored[0]

    # Only a tie among manifests that actually cover the diff is ambiguous;
    # when nothing covers it (covered == 0) there is no meaningful selection to
    # get wrong, so fall through and let downstream coverage checks fail.
    if top[0] > 0:
        ties = [s for s in scored if s[0] == top[0] and s[1] == top[1]]
        if len(ties) > 1:
            raise AmbiguousManifestSelection(
                f"{len(ties)} manifests are equally plausible for this diff "
                f"(covered={top[0]} files, specificity={top[1]}): "
                + ", ".join(s[2] for s in ties)
                + ". Make one manifest's scope specific to its PR."
            )

    return top[3]
