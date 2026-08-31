"""TOOLS-GITIGNORE-001 — executable contract for the ``tools/`` custody boundary.

The repository intentionally tracks a set of repository-owned tooling
namespaces under ``tools/`` while keeping generated artifacts and ad-hoc loose
root files ignored. Historically a blanket ``/tools/`` ignore silently dropped
new source files in the tracked packages, forcing ``git add -f``.

These tests pin *both sides* of the intended boundary using Git's own
``git check-ignore`` as the deterministic witness (D5): representative new
paths under the authorized namespaces (and ``tools/README.md``) must be
trackable, while loose root files and generated Python artifacts must remain
ignored. They also assert that existing tracked files stay tracked.

The probe paths are strings only — no fake production files are created.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
)


def _is_ignored(rel_path: str) -> bool:
    """True if Git would ignore ``rel_path`` (via ``git check-ignore -q``).

    Works on path strings whether or not the file exists on disk.
    """
    proc = subprocess.run(
        ["git", "check-ignore", "-q", rel_path],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # returncode 0 => path is ignored; 1 => not ignored.
    if proc.returncode not in (0, 1):
        raise AssertionError(f"git check-ignore errored for {rel_path}: {proc.stderr}")
    return proc.returncode == 0


def _is_tracked(rel_path: str) -> bool:
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel_path],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


# Authorized repository-owned tooling namespaces (established, tracked).
ALLOWED_NAMESPACE_PROBES = [
    "tools/grounding_agent/__probe_boundary__.py",
    "tools/grounding_agent/adapters/__probe_boundary__.py",
    "tools/agent_program/__probe_boundary__.py",
    "tools/codegen/__probe_boundary__.sh",
    "tools/README.md",
]

# Content that must remain ignored: loose root files and generated artifacts.
IGNORED_PROBES = [
    "tools/newscratch.txt",
    "tools/__probe_scratch__.py",
    "tools/grounding_agent/__pycache__/__probe__.pyc",
    "tools/grounding_agent/__probe__.pyc",
]

# Representative files that already exist and must stay tracked.
EXISTING_TRACKED = [
    "tools/grounding_agent/models.py",
    "tools/agent_program/analyze_incidents.py",
    "tools/codegen/generate_ts_sdk.sh",
    "tools/verify_policy.py",
]


@pytest.mark.parametrize("rel_path", ALLOWED_NAMESPACE_PROBES)
def test_new_source_in_authorized_namespaces_is_not_ignored(rel_path):
    """T02/T03/T04/T06 — new source in allowed namespaces is normally trackable."""
    assert not _is_ignored(rel_path), (
        f"{rel_path} is ignored but should be trackable without `git add -f`."
    )


@pytest.mark.parametrize("rel_path", IGNORED_PROBES)
def test_loose_root_and_generated_content_remains_ignored(rel_path):
    """T05 — loose root files and generated Python artifacts stay ignored."""
    assert _is_ignored(rel_path), (
        f"{rel_path} should remain ignored under the tools/ custody boundary."
    )


@pytest.mark.parametrize("rel_path", EXISTING_TRACKED)
def test_existing_tracked_tooling_remains_tracked(rel_path):
    """T01/T07 — the repair does not drop any currently tracked tooling file."""
    assert _is_tracked(rel_path), f"{rel_path} is expected to remain tracked."


def test_authorized_namespaces_are_real_directories():
    """Guards against the probe list drifting away from real tracked namespaces."""
    for ns in ("tools/grounding_agent", "tools/agent_program", "tools/codegen"):
        assert (_REPO_ROOT / ns).is_dir(), f"expected tracked namespace {ns} to exist"
