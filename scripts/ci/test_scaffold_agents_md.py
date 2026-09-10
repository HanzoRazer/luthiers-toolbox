"""SCAFFOLD-DIST-001 — self-test for scripts/scaffold_agents_md.py.

Every defect this scaffolder has had was an ENVIRONMENT-COUPLING bug: a worktree
directory name, a case-insensitive filesystem, a non-TTY stdin, an undetectable
default branch. None was visible by reading the code; each appeared only when the
tool met a real repository.

So these tests build **real temp git repos** and drive the real CLI as a
subprocess, asserting on OUTPUT -- files written, file contents, exit codes --
never on internal calls. Mocking the environment would test the model of the
environment, and a wrong model of it is the entire defect history.

Placed in scripts/ci/ rather than tests/ deliberately: repo-root tests/ is
collected by no workflow (each reference names an individual file or one
subdirectory), so a self-test for distribution-correctness placed there would
exist and never run -- the same hollow-guarantee shape the tool is hardened
against. See core_ci.yml for the named step that pins this file.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCAFFOLDER = Path(__file__).resolve().parents[2] / "scripts" / "scaffold_agents_md.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=repo, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _make_repo(root: Path, *, name: str = "repo", remote: str | None = None,
               branch: str = "main", origin_head: bool = True) -> Path:
    """A real git repo with one commit, and optionally a fake origin."""
    repo = root / name
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", branch)
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-qm", "init")
    if remote:
        _git(repo, "remote", "add", "origin", remote)
        if origin_head:
            # Simulate a resolvable origin/HEAD without a real network remote.
            _git(repo, "update-ref", f"refs/remotes/origin/{branch}", "HEAD")
            _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD",
                 f"refs/remotes/origin/{branch}")
    return repo


def _run_scaffolder(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    """Invoke the real CLI with stdin closed -- the agent-session condition."""
    return subprocess.run(
        [sys.executable, str(SCAFFOLDER), str(repo), *extra],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        stdin=subprocess.DEVNULL, timeout=60,
    )


# --------------------------------------------------------------------------- #
# 1. Worktree repo-name (defect #3)
# --------------------------------------------------------------------------- #

def test_heading_uses_remote_name_not_directory_name(tmp_path: Path) -> None:
    """A worktree directory is named for the task, not the repository.

    This produced a real wrong file: run from a worktree at C:/tmp/ltb-sprints,
    the heading read "Agent instructions - ltb-sprints".
    """
    repo = _make_repo(tmp_path, name="ltb-sprints",
                      remote="https://example.com/org/luthiers-toolbox.git")
    assert _run_scaffolder(repo).returncode == 0
    heading = (repo / "AGENTS.md").read_text(encoding="utf-8").splitlines()[0]
    assert heading == "# Agent instructions — luthiers-toolbox"
    assert "ltb-sprints" not in heading


# --------------------------------------------------------------------------- #
# 2. Case-folded PR-template discovery (defects #2 and #4)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("where", [".github", "", "docs"])
@pytest.mark.parametrize("casing", ["PULL_REQUEST_TEMPLATE.md", "pull_request_template.md"])
def test_existing_template_is_found_in_any_casing_or_location(
    tmp_path: Path, where: str, casing: str
) -> None:
    """Skip an existing template whatever its casing or directory.

    The original exact-path check appeared to work on a case-insensitive
    filesystem while matching a differently-cased file, and on Linux would have
    written a SECOND template beside the existing one.
    """
    repo = _make_repo(tmp_path, name=f"r{len(where)}{len(casing)}",
                      remote="https://example.com/o/r.git")
    target_dir = repo / where if where else repo
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / casing).write_text("existing\n", encoding="utf-8")

    result = _run_scaffolder(repo)
    assert result.returncode == 0
    assert "already exists" in result.stdout
    assert (target_dir / casing).read_text(encoding="utf-8") == "existing\n"
    # No second template anywhere.
    found = [p for d in (repo, repo / ".github", repo / "docs") if d.is_dir()
             for p in d.iterdir()
             if p.is_file() and p.name.casefold() == "pull_request_template.md"]
    assert len(found) == 1, f"a second template was written: {found}"


# --------------------------------------------------------------------------- #
# 3. Non-TTY --force (defect #1)
# --------------------------------------------------------------------------- #

def test_force_without_yes_refuses_headlessly_and_writes_nothing(tmp_path: Path) -> None:
    """The original crashed with EOFError AFTER writing the first file.

    A half-completed overwrite is worse than a refusal, so the guard must fire
    before anything is written -- asserted by content, not just exit code.
    """
    repo = _make_repo(tmp_path, name="r3a", remote="https://example.com/o/r3a.git")
    (repo / "AGENTS.md").write_text("ORIGINAL\n", encoding="utf-8")

    result = _run_scaffolder(repo, "--force")
    assert result.returncode != 0
    assert "EOFError" not in result.stderr and "Traceback" not in result.stderr
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == "ORIGINAL\n"


def test_force_with_yes_overwrites_headlessly(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, name="r3b", remote="https://example.com/o/r3b.git")
    (repo / "AGENTS.md").write_text("ORIGINAL\n", encoding="utf-8")

    result = _run_scaffolder(repo, "--force", "--yes")
    assert result.returncode == 0
    body = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "ORIGINAL" not in body
    assert body.startswith("# Agent instructions — r3b")


# --------------------------------------------------------------------------- #
# 4. Flag 1 — an undetectable default must never be written silently
# --------------------------------------------------------------------------- #

def test_undetectable_default_branch_refuses_headlessly(tmp_path: Path) -> None:
    """THE POISON-PILL GUARD.

    Repo on 'develop', no origin/HEAD, no local main/master. Writing here would
    put "branch from main" into a canonical file naming a branch that is not this
    repo's default -- and replicate that across every repo scaffolded the same
    way. It must refuse, and it must write nothing.
    """
    repo = _make_repo(tmp_path, name="r4", branch="develop", remote=None)

    result = _run_scaffolder(repo)
    assert result.returncode != 0, "wrote on a guessed default branch"
    assert not (repo / "AGENTS.md").exists(), "wrote a file it could not name correctly"
    assert "could not detect the default branch" in result.stderr
    assert "--default-branch" in result.stderr


def test_default_branch_override_is_used_throughout(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, name="r4b", branch="develop", remote=None)

    result = _run_scaffolder(repo, "--default-branch", "develop")
    assert result.returncode == 0
    body = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Branch from current `develop`. Always." in body
    assert "origin/develop" in body
    # The self-check must assert against develop, not a stray 'main'.
    assert "git merge-base HEAD origin/develop" in body
    assert "origin/main" not in body


# --------------------------------------------------------------------------- #
# 5. Happy path, and the never-overwrite default
# --------------------------------------------------------------------------- #

def test_happy_path_writes_both_with_todo_blocks_unfilled(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, name="r5", remote="https://example.com/o/r5.git")

    result = _run_scaffolder(repo)
    assert result.returncode == 0
    agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert (repo / ".github" / "pull_request_template.md").exists()

    # The scaffolder must NOT invent these two -- they are the human's to write.
    assert "<!-- INCIDENTS" in agents
    assert "<!-- VERIFICATION GATES" in agents
    assert "NOT DONE" in result.stdout


def test_second_run_does_not_clobber(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, name="r5b", remote="https://example.com/o/r5b.git")
    assert _run_scaffolder(repo).returncode == 0
    (repo / "AGENTS.md").write_text("HAND EDITED\n", encoding="utf-8")

    result = _run_scaffolder(repo)
    assert result.returncode == 0
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == "HAND EDITED\n"
    assert "SKIP" in result.stdout


def test_refuses_a_non_git_directory(tmp_path: Path) -> None:
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    result = _run_scaffolder(plain)
    assert result.returncode == 2
    assert not (plain / "AGENTS.md").exists()
