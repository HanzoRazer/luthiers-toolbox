#!/usr/bin/env python3
"""
emit_manifest.py — Generate provenance manifest for measurement artifacts.

Usage:
    python modes/_shared/emit_manifest.py --out manifest.json \
        --artifact load_series.json --artifact pairs.csv \
        --rig fixture=3-point --rig span_mm=400 --rig operator=Ross \
        --notes "Checkpoint run"

Output: JSON manifest with SHA-256 hashes for all artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List


def _sha256(p: Path) -> str:
    """Compute SHA-256 hash of file."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    out_path: str,
    *,
    rig: Dict[str, Any],
    artifacts: List[str],
    notes: str = "",
) -> str:
    """
    Write a measurement manifest JSON file.

    Args:
        out_path: Destination path for manifest.json
        rig: Dict of rig configuration (fixture, span, operator, etc.)
        artifacts: List of artifact file paths to hash
        notes: Optional operator notes

    Returns:
        Path to written manifest file.
    """
    items = []
    for a in artifacts:
        q = Path(a)
        items.append({
            "path": q.as_posix(),
            "exists": q.exists(),
            "bytes": q.stat().st_size if q.exists() else 0,
            "sha256": _sha256(q) if q.exists() and q.is_file() else None,
        })

    manifest = {
        "artifact_type": "measurement_manifest",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rig": rig,
        "notes": notes,
        "artifacts": items,
    }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return out_path


def _parse_kv(pairs: List[str]) -> Dict[str, Any]:
    """Parse key=value pairs into a dict with type coercion."""
    out: Dict[str, Any] = {}
    for s in pairs:
        if "=" not in s:
            raise ValueError(f"Bad key=value: {s}")
        k, v = s.split("=", 1)
        v = v.strip()
        # Type coercion
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        else:
            try:
                out[k] = int(v)
            except ValueError:
                try:
                    out[k] = float(v)
                except ValueError:
                    out[k] = v
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Emit provenance manifest for measurement artifacts."
    )
    ap.add_argument("--out", required=True, help="Output manifest path")
    ap.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Artifact file path (repeatable)",
    )
    ap.add_argument(
        "--rig",
        nargs="*",
        default=[],
        help="Rig config as key=value pairs",
    )
    ap.add_argument("--notes", default="", help="Operator notes")
    args = ap.parse_args()

    rig = _parse_kv(args.rig) if args.rig else {}
    out = write_manifest(args.out, rig=rig, artifacts=args.artifact, notes=args.notes)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
