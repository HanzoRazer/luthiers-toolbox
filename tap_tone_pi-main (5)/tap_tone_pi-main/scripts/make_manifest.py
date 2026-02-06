#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a manifest for a capture bundle.")
    ap.add_argument("--capture-dir", required=True)
    ap.add_argument("--out", default=None, help="Output path (default: capture_dir/manifest.json)")
    args = ap.parse_args()

    cap_dir = Path(args.capture_dir).expanduser().resolve()
    if not cap_dir.exists():
        raise SystemExit(f"Capture dir not found: {cap_dir}")

    analysis_path = cap_dir / "analysis.json"
    if not analysis_path.exists():
        raise SystemExit(f"Missing: {analysis_path}")

    analysis = load_json(analysis_path)

    files = []
    for p in sorted(cap_dir.iterdir()):
        if p.is_file():
            files.append({
                "name": p.name,
                "bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })

    manifest = {
        "schema_version": "0.1.0",
        "capture_dir": str(cap_dir),
        "ts_utc": analysis.get("ts_utc"),
        "label": analysis.get("label"),
        "sample_rate": analysis.get("sample_rate"),
        "channels": analysis.get("channels"),
        "dominant_hz": analysis.get("dominant_hz"),
        "confidence": analysis.get("confidence"),
        "files": files,
    }

    out_path = Path(args.out).expanduser().resolve() if args.out else (cap_dir / "manifest.json")
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[OK] Wrote {out_path}")


if __name__ == "__main__":
    main()
