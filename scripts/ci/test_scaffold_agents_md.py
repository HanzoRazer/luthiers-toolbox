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

import ast
import json
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


# --------------------------------------------------------------------------- #
# AGENT-PROCESS-SAFETY-002
#
# Lives in this file because core_ci.yml pins test_scaffold_agents_md.py by
# name. Nothing collects scripts/ci/ wholesale, so a new file would not run.
# These tests read the adopted instructions. They never execute a kill.
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_INSTRUCTIONS = REPO_ROOT / "AGENTS.md"
CLAUDE_INSTRUCTIONS = REPO_ROOT / "CLAUDE.md"
MANIFEST = REPO_ROOT / ".cbsp21" / "patches" / "agent-process-safety-002.json"

# Command strings only. APS-011 and APS-012 must reject them without running them.
PROHIBITED_COMMANDS = (
    "taskkill /F /IM python.exe",
    "taskkill /F /IM node.exe",
    "pkill -f python",
    "killall python",
)

# A raw PID kill is not a permitted example. Ownership fields are required.
RAW_PID_COMMAND = "taskkill /PID 4242 /F"


def _section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        raise AssertionError(f"missing heading: {heading}")
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return " ".join(body).lower()


def _canonical() -> str:
    return _section(
        CANONICAL_INSTRUCTIONS.read_text(encoding="utf-8"),
        "## Process termination safety",
    )


def _name_or_wildcard_termination(command: str) -> bool:
    """Classify a command string. Does not run it."""
    text = " ".join(command.lower().split())
    if "taskkill" in text and "/im" in text:
        return True
    head = text.split(" ", 1)[0]
    return head in {"pkill", "killall"}


def _ownership_allows(spec: dict) -> bool:
    pid = spec.get("pid")
    return (
        isinstance(pid, int)
        and not isinstance(pid, bool)
        and pid > 0
        and spec.get("started_by_current_task") is True
        and bool(spec.get("expected_command"))
        and bool(spec.get("expected_parent_or_session"))
    )


def test_aps001_canonical_instruction_is_agents_md() -> None:
    assert CANONICAL_INSTRUCTIONS.is_file()
    claude = CLAUDE_INSTRUCTIONS.read_text(encoding="utf-8").lower()
    assert "process termination safety" in claude
    assert "agents.md" in claude
    assert "canonical text" in claude


def test_aps002_policy_requires_an_exact_pid() -> None:
    assert "process id" in _canonical() or "pid" in _canonical()


def test_aps003_policy_requires_the_task_started_the_process() -> None:
    text = _canonical()
    assert "started" in text
    assert "current task" in text


def test_aps004_policy_requires_command_identity() -> None:
    assert "command identity" in _canonical()


def test_aps005_policy_requires_parent_or_session() -> None:
    text = _canonical()
    assert "parent" in text
    assert "session" in text


def test_aps006_policy_prohibits_executable_name_termination() -> None:
    text = _canonical()
    assert "executable name" in text
    assert "taskkill /im" in text


def test_aps007_policy_prohibits_wildcard_and_interpreter_wide_termination() -> None:
    text = _canonical()
    assert "wildcard" in text
    assert "interpreter" in text
    assert "pkill" in text
    assert "killall" in text


def test_aps008_policy_stops_and_reports_when_ownership_is_uncertain() -> None:
    text = _canonical()
    assert "stop and report" in text
    assert "ownership" in text


def test_aps009_policy_prefers_the_managed_execution_session() -> None:
    text = _canonical()
    assert "execution tool" in text
    assert "managed execution session" in text


def test_aps010_a_timeout_does_not_expand_termination_authority() -> None:
    text = _canonical()
    assert "timeout" in text
    assert "stalled test" in text
    assert "does not expand" in text


def test_aps011_taskkill_by_image_name_is_rejected_without_execution() -> None:
    for command in PROHIBITED_COMMANDS:
        if "taskkill" in command.lower():
            assert _name_or_wildcard_termination(command)


def test_aps012_pkill_and_killall_are_rejected_without_execution() -> None:
    assert _name_or_wildcard_termination("pkill -f python")
    assert _name_or_wildcard_termination("killall python")
    assert _name_or_wildcard_termination("pkill python")


def test_aps011_012_this_module_does_not_execute_prohibited_commands() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name not in {"run", "check_call", "check_output", "Popen"}:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                assert not _name_or_wildcard_termination(arg.value)


def test_aps_raw_pid_termination_is_not_treated_as_safe() -> None:
    assert not _name_or_wildcard_termination(RAW_PID_COMMAND)
    assert not _ownership_allows({"pid": 4242})
    assert _ownership_allows(
        {
            "pid": 4242,
            "expected_command": "python -m pytest tests/example.py",
            "expected_parent_or_session": "agent-session",
            "started_by_current_task": True,
        }
    )


def test_aps013_014_no_agent_process_utility_to_extend() -> None:
    """No agent-owned terminator exists, so no child process is created or killed."""
    roots = [REPO_ROOT / "scripts", REPO_ROOT / ".cursor"]
    for root in roots:
        for path in root.rglob("*.py"):
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            assert "def terminate_owned_process" not in text


def test_aps016_manifest_declares_no_production_paths() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    declared = set(manifest["scope"]["files_expected_to_change"])
    declared.update(entry["path"] for entry in manifest["files"])
    forbidden = (
        "services/api/app/",
        "packages/client/",
        "services/photo-vectorizer/",
    )
    for path in declared:
        for prefix in forbidden:
            assert not path.startswith(prefix), path
    assert manifest["behavior_change"] == "none"
