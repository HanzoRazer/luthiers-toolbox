"""CBSP21-NOBORROW-001-R1 — checker-level end-to-end provenance/coverage tests.

The existing suite (``test_cbsp21_manifest_discovery.py``) unit-tests the
``owned_candidates`` predicate. These tests instead drive the **real gate
scripts** (``check_cbsp21_patch_input.py`` and ``check_cbsp21_gate.py``) against
a synthetic Git base→head state, so the *user-visible* gate behavior is pinned:

* NB-014 — no current-change manifest → explicit **ownership/provenance** failure.
* NB-015 — an owned manifest exists but under-covers → explicit **coverage** failure.
* NB-020 — the PR's own in-diff manifest is the one selected (not a historical
  candidate that also covers the files).

No checker code is exercised in-process; the scripts are invoked exactly as CI
would run them, in a throwaway repository.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

CI_DIR = Path(__file__).resolve().parent
PATCH_INPUT = CI_DIR / "check_cbsp21_patch_input.py"
COVERAGE_GATE = CI_DIR / "check_cbsp21_gate.py"


# --- synthetic repository helpers ----------------------------------------


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True,
        # Explicit: the gates print emoji, and on Windows text=True decodes
        # with cp1252, which raises UnicodeDecodeError and leaves stdout None.
        encoding="utf-8", errors="replace",
    )
    return proc.stdout.strip()


def _write(repo: Path, rel: str, content) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content if isinstance(content, str) else json.dumps(content, indent=2), encoding="utf-8")


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@example.com", "-c", "user.name=Test", "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


def _valid_manifest(patch_id: str, declared: list) -> dict:
    """A schema-complete patch-input manifest declaring ``declared`` paths."""
    return {
        "schema": "cbsp21_patch_input_v1",
        "schema_version": "cbsp21_patch_input_v1",
        "coverage_min": 0.95,
        "patch_id": patch_id,
        "title": f"{patch_id} synthetic",
        "intent": "synthetic test manifest",
        "change_type": "test",
        "behavior_change": "none",
        "risk_level": "low",
        "scope": {
            "paths_in_scope": list(declared),
            "files_expected_to_change": list(declared),
        },
        "diff_articulation": {
            "what_changed": "synthetic change for a checker-level test",
            "why_not_redundant": "synthetic non-redundant rationale exceeding twenty characters",
        },
        "verification": {"commands_run": ["pytest scripts/ci/test_cbsp21_noborrow_checker.py"]},
        "files": [
            {"path": f, "intent": "synthetic", "risk": "low", "behavior_change": "none"}
            for f in declared
        ],
    }


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")


def _run(script: Path, repo: Path, *args: str):
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(repo), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr


def _run_patch_input(repo: Path, base: str, head: str):
    return _run(PATCH_INPUT, repo, "--base", base, "--head", head)


def _run_coverage_gate(repo: Path, changed_files: list):
    return _run(COVERAGE_GATE, repo, "--changed-files", *changed_files)


# --- NB-014: no current-change manifest → provenance failure -------------


def test_nb014_no_owned_manifest_is_provenance_failure(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write(repo, "app.py", "x = 1\n")
    # A historical manifest that fully covers app.py, authored by an earlier PR.
    _write(repo, ".cbsp21/patches/historical.json", _valid_manifest("HISTORICAL", ["app.py"]))
    base = _commit(repo, "base: app + historical manifest")
    _write(repo, "app.py", "x = 2\n")  # current change touches only app.py
    head = _commit(repo, "head: modify app only, bring no manifest")

    rc, out = _run_patch_input(repo, base, head)
    assert rc != 0, out
    # Ownership/provenance diagnostic — not a coverage message.
    assert "no CBSP21 manifest of its own" in out
    assert "authored for other changes" in out
    assert "COVERAGE failure" not in out


def test_nb014_coverage_gate_lockstep(tmp_path):
    # The coverage gate must fail-closed on the same provenance grounds.
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write(repo, "app.py", "x = 1\n")
    _write(repo, ".cbsp21/patches/historical.json", _valid_manifest("HISTORICAL", ["app.py"]))
    _commit(repo, "base")
    rc, out = _run_coverage_gate(repo, ["app.py"])
    assert rc != 0, out
    assert "declares no CBSP21 manifest of its own" in out


# --- NB-015: owned manifest under-covers → coverage failure --------------


def test_nb015_owned_but_undercovering_is_coverage_failure(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write(repo, "app.py", "x = 1\n")
    base = _commit(repo, "base: app only")
    _write(repo, "app.py", "x = 2\n")
    # Owned manifest is in the diff, but it declares a DIFFERENT file.
    _write(repo, ".cbsp21/patches/owned.json", _valid_manifest("OWNED", ["other.py"]))
    head = _commit(repo, "head: modify app, bring manifest that declares the wrong file")

    rc, out = _run_patch_input(repo, base, head)
    assert rc != 0, out
    # Coverage diagnostic — explicitly NOT an ownership failure.
    assert "COVERAGE failure" in out
    assert "no CBSP21 manifest of its own" not in out


# --- NB-020: PR's own in-diff manifest is selected -----------------------


def test_nb020_own_manifest_selected_over_historical(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write(repo, "app.py", "x = 1\n")
    # A historical manifest that also fully covers app.py (perfect borrow bait).
    _write(repo, ".cbsp21/patches/historical.json", _valid_manifest("HISTORICAL", ["app.py"]))
    base = _commit(repo, "base: app + historical manifest")
    _write(repo, "app.py", "x = 2\n")
    _write(repo, ".cbsp21/patches/owned.json", _valid_manifest("OWNED", ["app.py"]))
    head = _commit(repo, "head: modify app, bring own manifest covering it")

    rc, out = _run_patch_input(repo, base, head)
    assert rc == 0, out
    assert "PASS" in out
    # Selected because it is in the diff — not the historical candidate.
    assert "owned.json" in out
    assert "historical.json" not in out
