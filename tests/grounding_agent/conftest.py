"""Shared fixtures for Grounding Agent engine tests.

The in-memory fakes live in ``_fakes.py`` so both the engine tests (via these
fixtures) and the historical-fixture test can import them.
"""

from __future__ import annotations

import pytest

from ._fakes import FakeFS, FakeGit, FakeGitHub


@pytest.fixture
def make_git():
    return FakeGit


@pytest.fixture
def make_github():
    return FakeGitHub


@pytest.fixture
def make_fs():
    return FakeFS
