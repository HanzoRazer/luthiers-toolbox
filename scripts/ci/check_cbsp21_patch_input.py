#!/usr/bin/env python3
"""CBSP21 Patch Input Gate

Enforces a lightweight, repo-native "patch intent" manifest so reviewers (and bots)
don't miss subtle diffs or incorrectly label changes as "redundant".

What it checks:
1) .cbsp21/patch_input.json exists
2) Required fields are present and sane
3) Files changed in git diff are declared in files_expected_to_change (or paths_in_scope)
4) If behavior_change != "none", diff_articulation.why_not_redundant must be non-empty

Designed to be safe in CI and usable locally.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

# scripts/ci is on sys.path[0] when invoked as `python scripts/ci/check_...py`.
from cbsp21_manifest_discovery import (
    is_cbsp21_internal,
    load_candidates,
    load_manifest,
    select_manifest,
)


def _fail(msg: str) -> int:
    print(f"CBSP21 PATCH INPUT GATE: FAIL: {msg}")
    return 1


def _ok(msg: str) -> None:
    print(f"CBSP21 PATCH INPUT GATE: {msg}")


def _run(cmd: List[str]) -> Tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout.strip()


def _git_changed_files(base: str, head: str) -> List[str]:
    rc, out = _run(["git", "diff", "--name-only", f"{base}...{head}"])
    if rc != 0:
        raise RuntimeError(out)
    files = [line.strip() for line in out.splitlines() if line.strip()]
    # Ignore deletions? keep them — reviewers still need to know.
    return files


def _get(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _as_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    return [str(x)]


def _in_scope(file_path: str, paths_in_scope: List[str]) -> bool:
    # Treat scope entries as directory prefixes.
    for p in paths_in_scope:
        p = p.strip()
        if not p:
            continue
        # Normalize to posix-ish.
        if file_path.startswith(p.rstrip("/") + "/") or file_path == p.rstrip("/"):
            return True
    return False


def _declared_matcher(manifest: Dict[str, Any]) -> Callable[[str], bool]:
    """Whether a changed file is declared by this manifest's scope."""
    expected = set(_as_list(_get(manifest, "scope.files_expected_to_change")))
    paths_in_scope = _as_list(_get(manifest, "scope.paths_in_scope"))

    def is_declared(file_path: str) -> bool:
        return file_path in expected or _in_scope(file_path, paths_in_scope)

    return is_declared


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        default=os.getenv("CBSP21_BASE_REF") or os.getenv("GITHUB_BASE_REF") or "HEAD~1",
        help="git base ref (default: env CBSP21_BASE_REF / GITHUB_BASE_REF / HEAD~1)",
    )
    ap.add_argument(
        "--head",
        default=os.getenv("CBSP21_HEAD_REF") or os.getenv("GITHUB_SHA") or "HEAD",
        help="git head ref (default: env CBSP21_HEAD_REF / GITHUB_SHA / HEAD)",
    )
    ap.add_argument(
        "--manifest",
        default=None,
        help=(
            "Optional explicit manifest path. Default: auto-discover "
            ".cbsp21/patches/*.json (+ legacy .cbsp21/patch_input.json) and "
            "select the one that best covers the diff."
        ),
    )
    args = ap.parse_args()

    # Compute the diff first — the manifest is selected to match it.
    try:
        changed = _git_changed_files(args.base, args.head)
    except Exception as e:
        return _fail(f"Could not compute git diff changed files: {e}")

    try:
        if args.manifest:
            candidates = [(Path(args.manifest), load_manifest(args.manifest))]
        else:
            candidates = load_candidates()
    except FileNotFoundError:
        return _fail(f"Missing manifest: {args.manifest}")
    except Exception as e:
        return _fail(str(e))

    if not candidates:
        return _fail(
            "No CBSP21 manifest found. Add one under .cbsp21/patches/<patch-id>.json "
            "(preferred) or .cbsp21/patch_input.json (legacy)."
        )

    selected = select_manifest(candidates, changed, _declared_matcher)
    if selected is None:  # unreachable given the guard above, defensive
        return _fail("No CBSP21 manifest could be selected for this diff.")
    manifest_path, manifest = selected

    # Required top-level fields
    required = [
        "schema_version",
        "patch_id",
        "title",
        "intent",
        "change_type",
        "behavior_change",
        "risk_level",
        "scope.paths_in_scope",
        "scope.files_expected_to_change",
        "diff_articulation.what_changed",
        "diff_articulation.why_not_redundant",
        "verification.commands_run",
    ]
    for key in required:
        v = _get(manifest, key)
        if v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, list) and len(v) == 0):
            return _fail(f"Manifest missing/empty required field: {key}")

    behavior_change = str(_get(manifest, "behavior_change") or "").strip().lower()
    why_not = str(_get(manifest, "diff_articulation.why_not_redundant") or "").strip()
    if behavior_change != "none" and len(why_not) < 20:
        return _fail(
            "behavior_change is not 'none' but diff_articulation.why_not_redundant is too short. "
            "Explain the non-redundant delta (functions/fields/edges)."
        )

    paths_in_scope = _as_list(_get(manifest, "scope.paths_in_scope"))
    expected_files = set(_as_list(_get(manifest, "scope.files_expected_to_change")))

    # Ignore all .cbsp21/ manifests (legacy + patches) and git internals — a PR
    # never has to declare its own manifest file as in-scope work.
    ignore_prefixes = (".git/",)

    undeclared: List[str] = []
    for f in changed:
        if is_cbsp21_internal(f):
            continue
        if f.startswith(ignore_prefixes):
            continue
        # Must be explicitly listed OR fall under declared scope paths.
        if f not in expected_files and not _in_scope(f, paths_in_scope):
            undeclared.append(f)

    if undeclared:
        lines = "\n".join([f"  - {x}" for x in undeclared[:50]])
        return _fail(
            f"Changed files not declared in the selected manifest ({manifest_path}) "
            "scope (add to files_expected_to_change or paths_in_scope):\n" + lines
        )

    _ok("PASS")
    _ok(
        f"manifest={manifest_path} base={args.base} head={args.head} "
        f"changed_files={len(changed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
