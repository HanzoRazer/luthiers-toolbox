"""
Viewer Pack Loader — The ONLY interface to tap_tone_pi data.

This module loads viewer_pack_v1.json files. It does NOT import tap_tone_pi.
The viewer_pack is a contract, not a code dependency.
"""
import json
from pathlib import Path
from typing import Union, BinaryIO
import zipfile

from .schemas import ViewerPackV1


# Type alias for clarity
ViewerPack = ViewerPackV1


def load_viewer_pack(source: Union[str, Path, BinaryIO]) -> ViewerPack:
    """
    Load a viewer_pack_v1 from file path, ZIP, or file-like object.

    Args:
        source: Path to .json file, .zip archive, or file-like object

    Returns:
        Validated ViewerPackV1 instance

    Raises:
        ValueError: If schema version doesn't match
        ValidationError: If data doesn't conform to schema
    """
    if isinstance(source, (str, Path)):
        path = Path(source)

        if path.suffix == ".zip":
            return _load_from_zip(path)
        else:
            return _load_from_json(path)
    else:
        # File-like object
        data = json.load(source)
        return _validate_and_parse(data)


def _load_from_json(path: Path) -> ViewerPack:
    """Load from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _validate_and_parse(data)


def _load_from_zip(path: Path) -> ViewerPack:
    """Load from a ZIP archive containing viewer_pack.json."""
    with zipfile.ZipFile(path, "r") as zf:
        # Look for the manifest
        manifest_names = ["viewer_pack.json", "manifest.json", "pack.json"]

        for name in manifest_names:
            if name in zf.namelist():
                with zf.open(name) as f:
                    data = json.load(f)
                    return _validate_and_parse(data)

        raise ValueError(
            f"No viewer pack manifest found in {path}. "
            f"Expected one of: {manifest_names}"
        )


def _validate_and_parse(data: dict) -> ViewerPack:
    """Validate schema version and parse data."""
    schema_version = data.get("schema_version", "unknown")

    if schema_version != "viewer_pack_v1":
        raise ValueError(
            f"Unsupported viewer pack schema: {schema_version}. "
            f"Expected: viewer_pack_v1"
        )

    # Check the contract assertions
    if data.get("interpretation") != "deferred":
        raise ValueError(
            "viewer_pack must have interpretation='deferred'. "
            "tap_tone_pi should not interpret, only measure."
        )

    return ViewerPackV1(**data)


def viewer_pack_from_dict(data: dict) -> ViewerPack:
    """
    Create ViewerPack from dictionary (e.g., from API request body).

    Use this when receiving viewer_pack data via HTTP rather than file.
    """
    return _validate_and_parse(data)
