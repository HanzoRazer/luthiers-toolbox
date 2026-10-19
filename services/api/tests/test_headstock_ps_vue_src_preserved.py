"""Recovered Headstock Suite source (``ps-vue-src/``): kept exactly as delivered.

The folder holds the 2026-03-17 standalone app output recovered on 2026-10-15.
Its README lists a SHA-256 for every recovered file. These tests fail if a file
is edited, added or removed, or if a recovered file is copied into the client.

Hashes are taken over LF-normalized bytes, so a CRLF checkout does not fail them;
the delivered files are LF, so for them this equals the raw bytes.

Pure offline file reads; no application import.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_missing_request_id

REPO_ROOT = Path(__file__).resolve().parents[3]
SUITE = REPO_ROOT / "archive" / "experimental" / "2026-03" / "headstock-suite-refined"
RECOVERED = SUITE / "ps-vue-src"
_HASH_LINE = re.compile(r"^([0-9a-f]{64})  (\S+)$", re.MULTILINE)


def _listed() -> dict[str, str]:
    readme = (RECOVERED / "README.md").read_text(encoding="utf-8")
    return {path: digest for digest, path in _HASH_LINE.findall(readme)}


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_recovered_files_match_their_recorded_hashes():
    listed = _listed()
    assert len(listed) == 14, f"README lists {len(listed)} hashes, expected 14"
    on_disk = {p.relative_to(RECOVERED).as_posix() for p in RECOVERED.rglob("*") if p.is_file()}
    assert on_disk - {"README.md"} == set(listed), "files added to or removed from ps-vue-src/"
    changed = [path for path, digest in listed.items() if _sha256_lf(RECOVERED / path) != digest]
    assert changed == [], f"recovered files edited: {changed}"


def test_no_recovered_file_was_copied_into_the_client():
    client = REPO_ROOT / "packages" / "client" / "src"
    recovered = set(_listed().values())
    copied = [p.relative_to(REPO_ROOT).as_posix() for p in client.rglob("*")
              if p.suffix in {".ts", ".vue", ".css"} and p.is_file() and _sha256_lf(p) in recovered]
    assert copied == [], f"recovered files in packages/client/src: {copied}"
