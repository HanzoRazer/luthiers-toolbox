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
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


MANIFEST_PATH = Path(".cbsp21") / "patch_input.json"


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


def _read_manifest() -> Dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(str(MANIFEST_PATH))
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid JSON in {MANIFEST_PATH}: {e}")


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
    args = ap.parse_args()

    try:
        manifest = _read_manifest()
    except FileNotFoundError:
        return _fail("Missing .cbsp21/patch_input.json (required by CBSP21).")
    except Exception as e:
        return _fail(str(e))

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

    try:
        changed = _git_changed_files(args.base, args.head)
    except Exception as e:
        return _fail(f"Could not compute git diff changed files: {e}")

    # Ignore the manifest itself and common noise.
    ignore_prefixes = (".git/",)
    ignore_exact = {".cbsp21/patch_input.json"}

    undeclared: List[str] = []
    for f in changed:
        if f in ignore_exact:
            continue
        if f.startswith(ignore_prefixes):
            continue
        # Must be explicitly listed OR fall under declared scope paths.
        if f not in expected_files and not _in_scope(f, paths_in_scope):
            undeclared.append(f)

    if undeclared:
        lines = "\n".join([f"  - {x}" for x in undeclared[:50]])
        return _fail(
            "Changed files not declared in patch_input scope (add to files_expected_to_change or paths_in_scope):\n"
            + lines
        )

    _ok("PASS")
    _ok(f"base={args.base} head={args.head} changed_files={len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
