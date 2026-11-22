"""Path and byte checks for an external witness package.

Symlinks are not followed. Hard-linked evidence is refused. Manifest paths
must be relative and case-unique.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

MANIFEST_NAME = "WITNESS-MANIFEST.json"
SUMS_NAME = "SHA256SUMS"
SKIP_NAMES = frozenset({MANIFEST_NAME, SUMS_NAME})

MEDIA_TYPES = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".md": "text/markdown",
    ".png": "image/png",
    ".txt": "text/plain",
    ".wav": "audio/wav",
}


class PathPolicyError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def normalize_relative(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise PathPolicyError("unsafe_path", "path is empty")
    if value != value.strip() or "\\" in value or "\x00" in value or ":" in value:
        raise PathPolicyError("unsafe_path", "path contains an unsafe character")
    if value.startswith("/") or value.startswith("~"):
        raise PathPolicyError("unsafe_path", "absolute paths are refused")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PathPolicyError("unsafe_path", "traversal paths are refused")
    return "/".join(parts)


def media_type(relative: str) -> str:
    return MEDIA_TYPES.get(Path(relative).suffix.lower(), "application/octet-stream")


def assert_regular_file(root: Path, relative: str) -> Path:
    current = root
    for part in normalize_relative(relative).split("/"):
        current = current / part
        if current.is_symlink():
            kind = "symlink_directory" if current.is_dir() else "symlink_file"
            raise PathPolicyError(kind, f"symlink refused: {relative}")
    if not current.is_file():
        raise PathPolicyError("missing_file", f"not a regular file: {relative}")
    if current.stat().st_nlink != 1:
        raise PathPolicyError("hard_link", f"hard link refused: {relative}")
    return current


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_files(root: Path) -> list[str]:
    """Inventory regular files. Symlinks and hard links raise."""
    if root.is_symlink():
        raise PathPolicyError("symlink_directory", "package root is a symlink")
    if not root.is_dir():
        raise PathPolicyError("not_a_directory", "package path is not a directory")
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        for name in list(dirnames):
            child = current / name
            if child.is_symlink():
                raise PathPolicyError("symlink_directory", f"symlink directory refused: {name}")
        for name in filenames:
            path = current / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise PathPolicyError("symlink_file", f"symlink file refused: {relative}")
            if not path.is_file():
                raise PathPolicyError("missing_file", f"not a regular file: {relative}")
            if path.stat().st_nlink != 1:
                raise PathPolicyError("hard_link", f"hard link refused: {relative}")
            found.append(relative)
    folded = [item.casefold() for item in found]
    if len(folded) != len(set(folded)):
        raise PathPolicyError("case_collision", "case-insensitive filename collision")
    return sorted(found)


def evidence_files(root: Path) -> list[str]:
    return [item for item in relative_files(root) if item not in SKIP_NAMES]
