#!/usr/bin/env python3
"""
Generate a minimal viewer_pack_v1 fixture zip for testing.

This creates a valid, minimal pack that passes validation.
Used for CI fixtures when real exported packs aren't available.

Usage:
    python scripts/validate/generate_minimal_viewer_pack_fixture.py \
        --output services/api/tests/fixtures/viewer_packs/session_minimal.zip
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_minimal_pack() -> dict:
    """
    Generate a minimal valid viewer_pack_v1 manifest and files.

    Returns dict with:
      - manifest: the manifest dict (without bundle_sha256 yet)
      - files: dict of relpath -> bytes
    """
    files: dict[str, bytes] = {}

    # Points to include
    points = ["A1", "A2"]

    # Generate minimal audio files (valid WAV headers)
    for point_id in points:
        relpath = f"audio/points/{point_id}.wav"
        # Minimal valid WAV: 44-byte header, 0 samples
        wav_header = bytes([
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0x24, 0x00, 0x00, 0x00,  # file size - 8 (36 bytes)
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            0x10, 0x00, 0x00, 0x00,  # fmt chunk size (16)
            0x01, 0x00,              # audio format (1 = PCM)
            0x01, 0x00,              # num channels (1)
            0x80, 0xBB, 0x00, 0x00,  # sample rate (48000)
            0x00, 0x77, 0x01, 0x00,  # byte rate
            0x02, 0x00,              # block align
            0x10, 0x00,              # bits per sample (16)
            0x64, 0x61, 0x74, 0x61,  # "data"
            0x00, 0x00, 0x00, 0x00,  # data size (0)
        ])
        files[relpath] = wav_header

    # Generate minimal spectrum CSV files
    for point_id in points:
        relpath = f"spectra/points/{point_id}/spectrum.csv"
        csv_content = "freq_hz,magnitude_db\n100.0,-20.0\n200.0,-25.0\n500.0,-30.0\n"
        files[relpath] = csv_content.encode("utf-8")

    # Generate session meta
    session_meta = {
        "session_id": "minimal_fixture",
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "grid_id": "test_grid_2pt",
        "phase": "phase2",
        "points": points,
    }
    files["meta/session_meta.json"] = json.dumps(session_meta, indent=2).encode("utf-8")

    # Build file entries for manifest
    file_entries = []
    for relpath, data in files.items():
        # Determine kind based on path/extension
        if relpath.endswith(".wav"):
            kind = "audio_raw"
            mime = "audio/wav"
        elif "spectrum" in relpath and relpath.endswith(".csv"):
            kind = "spectrum_csv"
            mime = "text/csv"
        elif relpath.endswith(".json"):
            kind = "session_meta"
            mime = "application/json"
        else:
            kind = "unknown"
            mime = "application/octet-stream"

        file_entries.append({
            "relpath": relpath,
            "sha256": sha256_bytes(data),
            "bytes": len(data),
            "mime": mime,
            "kind": kind,
        })

    # Build manifest (without bundle_sha256)
    manifest = {
        "schema_version": "v1",
        "schema_id": "viewer_pack_v1",
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_capdir": "minimal_fixture_session",
        "detected_phase": "phase2",
        "measurement_only": True,
        "interpretation": "deferred",
        "points": points,
        "contents": {
            "audio": True,
            "spectra": True,
            "coherence": False,
            "ods": False,
            "wolf": False,
            "plots": False,
            "provenance": False,
        },
        "files": file_entries,
    }

    return {"manifest": manifest, "files": files}


def add_bundle_sha256(manifest: dict) -> dict:
    """
    Add bundle_sha256 to manifest using canonical JSON encoding.

    The hash is computed from the manifest JSON bytes WITHOUT bundle_sha256.
    """
    # Canonical JSON: sorted keys, indent=2
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    bundle_hash = sha256_bytes(manifest_bytes)

    manifest["bundle_sha256"] = bundle_hash
    return manifest


def create_zip(output_path: Path, manifest: dict, files: dict[str, bytes]) -> None:
    """Create a viewer_pack_v1 zip file."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write manifest
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
        zf.writestr("manifest.json", manifest_bytes)

        # Write all files
        for relpath, data in files.items():
            zf.writestr(relpath, data)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate minimal viewer_pack_v1 fixture zip.")
    ap.add_argument(
        "--output", "-o",
        default="session_minimal.zip",
        help="Output zip path (default: session_minimal.zip)"
    )
    args = ap.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating minimal viewer_pack_v1 fixture...")

    pack = generate_minimal_pack()
    manifest = add_bundle_sha256(pack["manifest"])
    files = pack["files"]

    create_zip(output_path, manifest, files)

    print(f"Created: {output_path}")
    print(f"  Points: {manifest['points']}")
    print(f"  Files: {len(manifest['files'])}")
    print(f"  bundle_sha256: {manifest['bundle_sha256'][:16]}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
