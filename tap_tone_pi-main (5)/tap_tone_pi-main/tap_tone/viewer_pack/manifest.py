"""Viewer Pack manifest utilities — shared helpers for ZIP export/validate/diff.

This module keeps ZIP handling consistent across:
- scripts/phase2/export_viewer_pack_v1.py (export)
- scripts/viewer_pack_validate.py (validation)
- scripts/viewer_pack_diff.py (comparison)

All functions are pure where possible; no interpretation logic.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple


MANIFEST_FILENAME = "viewer_pack.json"


@dataclass(frozen=True)
class FileEntry:
    """Immutable representation of a file entry from the manifest."""
    relpath: str
    sha256: str
    bytes: int
    mime: str
    kind: str


@dataclass
class ViewerPackHandle:
    """Container for an opened viewer pack with its manifest and zip handle."""
    manifest: Dict[str, Any]
    zip_handle: zipfile.ZipFile
    path: Path

    def close(self) -> None:
        """Close the underlying zip handle."""
        self.zip_handle.close()

    def __enter__(self) -> "ViewerPackHandle":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def load_viewer_pack(zip_path: str | Path) -> ViewerPackHandle:
    """Open a viewer pack ZIP and parse its manifest.

    Args:
        zip_path: Path to the viewer_pack_*.zip file.

    Returns:
        ViewerPackHandle with parsed manifest and open zip handle.

    Raises:
        FileNotFoundError: If ZIP doesn't exist.
        KeyError: If viewer_pack.json not found in ZIP.
        json.JSONDecodeError: If manifest is invalid JSON.
    """
    path = Path(zip_path)
    if not path.exists():
        raise FileNotFoundError(f"Viewer pack not found: {path}")

    zf = zipfile.ZipFile(path, "r")

    if MANIFEST_FILENAME not in zf.namelist():
        zf.close()
        raise KeyError(f"Manifest '{MANIFEST_FILENAME}' not found in ZIP")

    with zf.open(MANIFEST_FILENAME) as f:
        manifest = json.load(f)

    return ViewerPackHandle(manifest=manifest, zip_handle=zf, path=path)


def canonical_json_bytes(obj: Dict[str, Any], exclude_keys: Optional[set] = None) -> bytes:
    """Serialize object to canonical JSON bytes for hashing.

    Canonical form:
    - Keys sorted
    - No trailing whitespace
    - UTF-8 encoded
    - Compact separators

    Args:
        obj: Dictionary to serialize.
        exclude_keys: Top-level keys to exclude (e.g., {"bundle_sha256"}).

    Returns:
        UTF-8 encoded JSON bytes.
    """
    if exclude_keys:
        obj = {k: v for k, v in obj.items() if k not in exclude_keys}

    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_bundle_sha256(manifest: Dict[str, Any]) -> str:
    """Compute SHA256 hash of manifest (excluding bundle_sha256 field).

    Args:
        manifest: The viewer pack manifest dict.

    Returns:
        Lowercase hex SHA256 hash.
    """
    canonical = canonical_json_bytes(manifest, exclude_keys={"bundle_sha256"})
    return hashlib.sha256(canonical).hexdigest()


def compute_file_sha256(data: bytes) -> str:
    """Compute SHA256 hash of file data.

    Args:
        data: Raw file bytes.

    Returns:
        Lowercase hex SHA256 hash.
    """
    return hashlib.sha256(data).hexdigest()


def iter_files(manifest: Dict[str, Any]) -> Iterator[FileEntry]:
    """Iterate over file entries in the manifest.

    Args:
        manifest: The viewer pack manifest dict.

    Yields:
        FileEntry objects for each file in the manifest.
    """
    for f in manifest.get("files", []):
        yield FileEntry(
            relpath=f["relpath"],
            sha256=f["sha256"],
            bytes=f["bytes"],
            mime=f["mime"],
            kind=f["kind"],
        )


def get_points(manifest: Dict[str, Any]) -> list[str]:
    """Extract point IDs from manifest.

    Args:
        manifest: The viewer pack manifest dict.

    Returns:
        List of point ID strings.
    """
    return list(manifest.get("points", []))


def get_contents_flags(manifest: Dict[str, Any]) -> Dict[str, bool]:
    """Extract contents flags from manifest.

    Args:
        manifest: The viewer pack manifest dict.

    Returns:
        Dict mapping content type to boolean presence flag.
    """
    return dict(manifest.get("contents", {}))


def find_files_by_kind(manifest: Dict[str, Any], kind: str) -> list[FileEntry]:
    """Find all files of a specific kind.

    Args:
        manifest: The viewer pack manifest dict.
        kind: The kind to filter by (e.g., "spectrum_csv").

    Returns:
        List of matching FileEntry objects.
    """
    return [f for f in iter_files(manifest) if f.kind == kind]


def read_file_from_pack(handle: ViewerPackHandle, relpath: str) -> bytes:
    """Read a file from the viewer pack.

    Args:
        handle: Open ViewerPackHandle.
        relpath: Relative path within the ZIP.

    Returns:
        Raw file bytes.

    Raises:
        KeyError: If file not found in ZIP.
    """
    return handle.zip_handle.read(relpath)
