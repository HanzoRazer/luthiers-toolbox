#!/usr/bin/env python3
"""
Viewer Pack v1 Validator

Checks:
- manifest.json schema shape (no additionalProperties)
- referenced files exist
- file byte size matches
- sha256 matches manifest

Exit codes:
  0 = valid
  1 = validation failure
  2 = execution error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Any


REQUIRED_KEYS = {
    "schema_version",
    "schema_id",
    "created_at_utc",
    "source_capdir",
    "detected_phase",
    "measurement_only",
    "interpretation",
    "points",
    "contents",
    "files",
    "bundle_sha256",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_pack(pack_dir: Path) -> None:
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.exists():
        raise AssertionError("manifest.json not found")

    manifest: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))

    # --- shape enforcement (additionalProperties: false) ---
    extra_keys = set(manifest.keys()) - REQUIRED_KEYS
    if extra_keys:
        raise AssertionError(f"Unexpected manifest keys: {sorted(extra_keys)}")

    missing = REQUIRED_KEYS - set(manifest.keys())
    if missing:
        raise AssertionError(f"Missing required manifest keys: {sorted(missing)}")

    # --- bundle sha check ---
    manifest_copy = dict(manifest)
    bundle_sha = manifest_copy.pop("bundle_sha256")

    manifest_bytes = json.dumps(manifest_copy, indent=2, sort_keys=True).encode("utf-8")
    computed_bundle_sha = hashlib.sha256(manifest_bytes).hexdigest()

    if computed_bundle_sha != bundle_sha:
        raise AssertionError("bundle_sha256 mismatch")

    # --- file checks ---
    for f in manifest["files"]:
        rel = f["relpath"]
        expected_sha = f["sha256"]
        expected_bytes = f["bytes"]

        fp = pack_dir / rel
        if not fp.exists():
            raise AssertionError(f"Missing file: {rel}")

        actual_bytes = fp.stat().st_size
        if actual_bytes != expected_bytes:
            raise AssertionError(
                f"Size mismatch for {rel}: {actual_bytes} != {expected_bytes}"
            )

        actual_sha = sha256_file(fp)
        if actual_sha != expected_sha:
            raise AssertionError(
                f"SHA mismatch for {rel}: {actual_sha} != {expected_sha}"
            )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pack_dir", help="Path to viewer_pack_v1 directory")
    args = ap.parse_args()

    try:
        validate_pack(Path(args.pack_dir))
        print("[viewer-pack] PASS")
        return 0
    except AssertionError as e:
        print(f"[viewer-pack] FAIL: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[viewer-pack] ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
