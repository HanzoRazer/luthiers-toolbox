"""Filesystem adapter tests."""

from __future__ import annotations

from tools.grounding_agent.adapters.filesystem import FileSystemAdapter


def test_local_path_exists(tmp_path):
    adapter = FileSystemAdapter()
    present = tmp_path / "present.txt"
    present.write_text("x")
    assert adapter.local_path_exists(str(present)) is True
    assert adapter.local_path_exists(str(tmp_path / "missing.txt")) is False


def test_repo_path_exists(tmp_path):
    adapter = FileSystemAdapter()
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "f.py").write_text("x")
    assert adapter.repo_path_exists(str(tmp_path), "sub/f.py") is True
    assert adapter.repo_path_exists(str(tmp_path), "sub/nope.py") is False
