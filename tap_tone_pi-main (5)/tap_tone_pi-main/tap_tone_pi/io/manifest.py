"""Manifest generation utilities.

Provides functions to create measurement manifests with SHA-256 hashes
for artifact integrity verification.

Migration
---------
    # Old import (deprecated)
    from modes._shared.manifest import write_manifest
    
    # New import (v2.0.0+)
    from tap_tone_pi.io.manifest import write_manifest
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from typing import Any, Dict, Iterable


def file_hash(path: str, algo: str = "sha256") -> str:
    """Compute hash of a file.
    
    Args:
        path: Path to file
        algo: Hash algorithm (default: sha256)
    
    Returns:
        Hex digest string
    """
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    out_path: str,
    *,
    rig: Dict[str, Any] | None = None,
    artifacts: Iterable[str] = (),
    notes: str | None = None,
) -> str:
    """Write a measurement manifest with artifact hashes.
    
    Args:
        out_path: Output path for manifest.json
        rig: Rig/fixture configuration dictionary
        artifacts: Iterable of artifact file paths to include
        notes: Optional notes string
    
    Returns:
        Path to written manifest file
    """
    p = pathlib.Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "artifact_type": "manifest",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rig": rig or {},
        "artifacts": [],
        "notes": notes or "",
    }
    
    for a in artifacts:
        a = os.fspath(a)
        entry = {
            "path": a,
            "sha256": file_hash(a),
            "size": os.path.getsize(a),
        }
        data["artifacts"].append(entry)
    
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    return os.fspath(p)
