"""Anti-behavior tests: prove the package has no mutation surface (D1).

These checks are scoped to ``tools/grounding_agent/`` (not a brittle whole-repo
grep) and assert, structurally and via AST, that the package cannot commit,
push, checkout, edit/merge PRs, issue HTTP writes, or emit remediation fields.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tools.grounding_agent.adapters.git_repo import (
    _READ_ONLY_SUBCOMMANDS,
    GitRepoAdapter,
)
from tools.grounding_agent.adapters.github_api import GitHubAdapter

PACKAGE_DIR = Path(__file__).resolve().parents[2] / "tools" / "grounding_agent"

# git subcommands that mutate local or remote state. merge-base is intentionally
# NOT here (distinct token from "merge") and is a read-only ancestry query.
FORBIDDEN_GIT_SUBCOMMANDS = {
    "commit", "push", "checkout", "switch", "reset", "rebase", "merge",
    "cherry-pick", "am", "apply", "clean", "gc", "fetch", "pull", "clone",
    "mv", "rm", "stash", "update-ref", "update-index", "symbolic-ref",
    "worktree", "notes", "restore", "tag", "branch", "remote", "add",
}

FORBIDDEN_HTTP_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

FORBIDDEN_RESULT_FIELDS = {
    "recommended_fix", "next_action", "suggested_branch", "patch", "reasoning",
    "fix", "remediation",
}


def _package_py_files():
    return sorted(PACKAGE_DIR.rglob("*.py"))


def _parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


# --- Structural facts about the adapters ---------------------------------

def test_git_allowlist_is_read_only():
    assert _READ_ONLY_SUBCOMMANDS.isdisjoint(FORBIDDEN_GIT_SUBCOMMANDS)


def test_git_adapter_exposes_no_generic_runner():
    # No public run/exec surface; only named read methods.
    public = [n for n in dir(GitRepoAdapter) if not n.startswith("_")]
    for name in public:
        assert "run" not in name.lower()
        assert "exec" not in name.lower()
    assert not hasattr(GitRepoAdapter, "run_git")


def test_github_adapter_has_no_write_methods():
    public = [n for n in dir(GitHubAdapter) if not n.startswith("_")]
    for name in public:
        for verb in ("post", "patch", "put", "delete", "create", "update", "edit", "merge", "close"):
            assert verb not in name.lower(), f"suspicious GitHub method: {name}"


# --- AST scans across the package ----------------------------------------

def test_no_shell_true_and_no_literal_git_mutation():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            # shell=True is forbidden anywhere.
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    raise AssertionError(f"shell=True found in {path}")
            # A literal argv array beginning with 'git' must not name a mutating subcommand.
            if node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
                elts = node.args[0].elts
                strings = [e.value for e in elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                if strings and strings[0] == "git":
                    for token in strings[1:]:
                        assert token not in FORBIDDEN_GIT_SUBCOMMANDS, (
                            f"literal git mutation '{token}' in {path}"
                        )
                        # stop at first non-flag subcommand
                        if not token.startswith("-") and token not in ("-C",):
                            break
                # Reject any literal 'gh' PR write invocation.
                if strings[:1] == ["gh"]:
                    joined = " ".join(strings)
                    for bad in ("pr edit", "pr merge", "pr close", "pr comment", "pr review", "api -X"):
                        assert bad not in joined, f"gh mutation '{bad}' in {path}"


def test_no_http_write_methods():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg == "method" and isinstance(kw.value, ast.Constant):
                    assert kw.value.value not in FORBIDDEN_HTTP_METHODS, (
                        f"HTTP {kw.value.value} in {path}"
                    )


def test_no_write_mode_file_open_outside_cli():
    """No evidence-gathering module opens a file for writing.

    cli.py is permitted exactly one write path: emitting the JSON report to a
    user-specified --output. Everything else must be read-only.
    """
    for path in _package_py_files():
        if path.name == "cli.py":
            continue
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                mode = None
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = kw.value.value
                if mode:
                    assert not any(c in mode for c in ("w", "a", "x", "+")), (
                        f"write-mode open in {path}: mode={mode}"
                    )


def test_no_forbidden_result_fields_in_dict_literals():
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key in node.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        assert key.value not in FORBIDDEN_RESULT_FIELDS, (
                            f"forbidden field '{key.value}' in dict literal in {path}"
                        )


def test_no_hardcoded_program_name_classifier():
    """GA2-011 — the lane/provenance logic is structural, not a keyword classifier.

    Prove no known program/workstream name is hardcoded as a string literal in
    the evaluator modules (which would be an NLP-style ``if "SGAQ" in ...``
    classifier, forbidden by D9). Lane comparison must be structural.
    """
    denylisted_program_names = {
        "SGAQ", "RMOS", "Vectorizer", "vectorizer-sandbox", "Dependabot",
        "Reconciliation", "Agent Program", "Queue Agent", "Supervisor",
    }
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value not in denylisted_program_names, (
                    f"hardcoded program-name literal {node.value!r} in {path} "
                    "(lane checks must be structural, not keyword-based)"
                )


def test_subprocess_only_imported_in_git_adapter():
    importers = []
    for path in _package_py_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "subprocess":
                        importers.append(path.name)
            elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
                importers.append(path.name)
    assert importers == ["git_repo.py"] or set(importers) == {"git_repo.py"}, importers


# --- Report-level: no remediation output ---------------------------------

def test_mismatch_report_contains_no_remediation_field():
    from tools.grounding_agent.engine import ground
    from tools.grounding_agent.models import (
        ActiveLane,
        GroundingClaim,
        GroundingRequest,
    )
    from ._fakes import FakeFS, FakeGit, FakeGitHub

    request = GroundingRequest(
        active_lane=ActiveLane.from_dict({
            "project": "p", "active_repository": "HanzoRazer/luthiers-toolbox",
            "active_program": "prog", "active_order": "ord", "active_state": "IMPLEMENTATION",
            "cross_repo_policy": "EVIDENCE_ONLY",
        }),
        claims=[GroundingClaim.from_dict({
            "claim_id": "C-1", "type": "pr_state", "repository": "HanzoRazer/luthiers-toolbox",
            "pr_number": 1, "expected": {"merged": True}, "material": True,
        })],
    )
    pr = {"number": 1, "state": "open", "draft": True, "merged": False, "head": {"sha": "x"}, "base": {"ref": "main"}}
    report = ground(request, git=FakeGit(), github=FakeGitHub(prs={("HanzoRazer/luthiers-toolbox", 1): pr}), fs=FakeFS())

    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k not in FORBIDDEN_RESULT_FIELDS, f"forbidden field in report: {k}"
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(report.to_dict())
