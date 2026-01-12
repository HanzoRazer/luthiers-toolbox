"""
Export History Store for Luthier's Tool Box API
Manages persistent storage of all DXF/SVG exports with metadata

Migrated from legacy ./server/history_store.py
"""
from __future__ import annotations
import uuid
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


def _get_exports_root() -> str:
    """Get root directory for export history storage"""
    return os.environ.get("EXPORTS_ROOT", "./exports/logs")


def get_units() -> str:
    """Get default units for exports"""
    return os.environ.get("UNITS", "in")


def get_version() -> str:
    """Get ToolBox version string"""
    return os.environ.get("TOOLBOX_VERSION", "ToolBox MVP")


def get_git_sha() -> str:
    """Get Git SHA for DXF comment stamping"""
    return os.environ.get("GIT_SHA", "unknown")


def _utc_ts() -> str:
    """Generate UTC timestamp in ISO 8601 format"""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ensure_dir(p: Path):
    """Create directory if it doesn't exist"""
    p.mkdir(parents=True, exist_ok=True)


def _get_root() -> Path:
    """Get the exports root path (refreshed on each call)"""
    return Path(_get_exports_root())


def start_entry(kind: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new export history entry

    Args:
        kind: Export type ('polyline', 'biarc', etc.)
        meta: Additional metadata to store

    Returns:
        Entry dict with id, dir path, and metadata
    """
    root = _get_root()

    day = time.strftime("%Y-%m-%d", time.gmtime())
    entry_id = str(uuid.uuid4())
    entry_dir = root / day / entry_id
    _ensure_dir(entry_dir)

    meta_out = {
        "id": entry_id,
        "kind": kind,
        "created_utc": _utc_ts(),
        **meta
    }

    (entry_dir / "meta.json").write_text(json.dumps(meta_out, indent=2))

    return {
        "id": entry_id,
        "dir": str(entry_dir),
        "meta": meta_out
    }


def write_file(entry: Dict[str, Any], name: str, data: bytes):
    """Write binary file to export entry directory"""
    Path(entry["dir"]).mkdir(parents=True, exist_ok=True)
    (Path(entry["dir"]) / name).write_bytes(data)


def write_text(entry: Dict[str, Any], name: str, text: str):
    """Write text file to export entry directory"""
    write_file(entry, name, text.encode("utf-8"))


def finalize(entry: Dict[str, Any], extra_meta: Optional[Dict[str, Any]] = None):
    """Finalize export entry by updating metadata"""
    entry_dir = Path(entry["dir"])
    meta_path = entry_dir / "meta.json"
    meta = json.loads(meta_path.read_text())

    if extra_meta:
        meta.update(extra_meta)

    meta_path.write_text(json.dumps(meta, indent=2))


def list_entries(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent export entries sorted by creation time"""
    root = _get_root()

    if not root.exists():
        return []

    days = sorted([p for p in root.iterdir() if p.is_dir()], reverse=True)
    items: List[Dict[str, Any]] = []

    for day in days:
        for entry in sorted(day.iterdir(), reverse=True):
            if (entry / "meta.json").exists():
                try:
                    meta = json.loads((entry / "meta.json").read_text())
                except Exception:
                    meta = {
                        "id": entry.name,
                        "created_utc": "",
                        "kind": "unknown"
                    }

                meta["_path"] = str(entry)
                items.append(meta)

                if len(items) >= limit:
                    return items

    return items


def read_meta(entry_id: str) -> Dict[str, Any]:
    """Read metadata for a specific export entry"""
    root = _get_root()

    if not root.exists():
        raise FileNotFoundError("No history root")

    for day in root.iterdir():
        p = day / entry_id / "meta.json"
        if p.exists():
            return json.loads(p.read_text())

    raise FileNotFoundError(entry_id)


def file_bytes(entry_id: str, filename: str) -> bytes:
    """Read file from a specific export entry"""
    root = _get_root()

    if not root.exists():
        raise FileNotFoundError("No history root")

    for day in root.iterdir():
        p = day / entry_id / filename
        if p.exists():
            return p.read_bytes()

    raise FileNotFoundError(f"{entry_id}/{filename}")
