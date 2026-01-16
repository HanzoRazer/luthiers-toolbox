#!/usr/bin/env python3
"""
Generate test fixtures for viewer_pack_v1 testing.

Creates:
- session_with_coherence.zip: Tests dual-axis chart (magnitude + coherence)
- session_unknown_kind.zip: Tests fallback renderer for unknown kinds
"""

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def create_manifest(files: list, source_capdir: str, contents: dict) -> tuple[bytes, str]:
    """Create manifest JSON and compute bundle hash."""
    manifest = {
        "schema_version": "v1",
        "schema_id": "viewer_pack_v1",
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_capdir": source_capdir,
        "detected_phase": "phase2",
        "measurement_only": True,
        "interpretation": "deferred",
        "points": ["A1"],
        "contents": contents,
        "files": files,
    }

    # Compute bundle hash (without bundle_sha256 field)
    manifest_for_hash = dict(sorted(manifest.items()))
    hash_bytes = json.dumps(manifest_for_hash, indent=2).encode("utf-8")
    bundle_sha256 = sha256_bytes(hash_bytes)

    manifest["bundle_sha256"] = bundle_sha256

    final_bytes = json.dumps(manifest, indent=2).encode("utf-8")
    return final_bytes, bundle_sha256


def create_session_with_coherence():
    """Create fixture with coherence data for dual-axis chart testing."""

    # Spectrum CSV with coherence column
    spectrum_csv = b"""freq_hz,H_mag,coherence,phase_deg
50.0,0.00012,0.45,-12.5
100.0,0.00045,0.78,23.1
150.0,0.00089,0.92,45.6
200.0,0.00234,0.95,67.8
250.0,0.00567,0.98,89.2
300.0,0.00891,0.97,112.4
350.0,0.00654,0.94,134.5
400.0,0.00321,0.89,156.7
450.0,0.00156,0.82,178.9
500.0,0.00078,0.71,-170.3
"""

    # Session meta
    session_meta = json.dumps({
        "session_id": "coherence_test_session",
        "instrument": "test_guitar",
        "capture_date": "2026-01-15",
        "notes": "Fixture for testing coherence rendering"
    }, indent=2).encode("utf-8")

    # Dummy audio (WAV header only - 44 bytes)
    audio_wav = bytes([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # chunk size
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # subchunk size
        0x01, 0x00,              # audio format (PCM)
        0x01, 0x00,              # num channels
        0x44, 0xAC, 0x00, 0x00,  # sample rate (44100)
        0x88, 0x58, 0x01, 0x00,  # byte rate
        0x02, 0x00,              # block align
        0x10, 0x00,              # bits per sample
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # data size
    ])

    files_data = {
        "spectra/points/A1/spectrum.csv": spectrum_csv,
        "meta/session_meta.json": session_meta,
        "audio/points/A1.wav": audio_wav,
    }

    file_entries = []
    for relpath, data in files_data.items():
        kind = "spectrum_csv" if "spectrum" in relpath else \
               "session_meta" if "session_meta" in relpath else \
               "audio_raw"
        mime = "text/csv" if kind == "spectrum_csv" else \
               "application/json" if kind == "session_meta" else \
               "audio/wav"

        file_entries.append({
            "relpath": relpath,
            "sha256": sha256_bytes(data),
            "bytes": len(data),
            "mime": mime,
            "kind": kind,
        })

    manifest_bytes, _ = create_manifest(
        files=file_entries,
        source_capdir="coherence_test_session",
        contents={
            "audio": True,
            "spectra": True,
            "coherence": True,
            "ods": False,
            "wolf": False,
            "plots": False,
            "provenance": False,
        }
    )

    # Create ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest_bytes)
        for relpath, data in files_data.items():
            zf.writestr(relpath, data)

    return zip_buffer.getvalue()


def create_session_unknown_kind():
    """Create fixture with unknown kind for fallback renderer testing."""

    # Normal spectrum CSV
    spectrum_csv = b"""freq_hz,H_mag
100.0,0.00045
200.0,0.00089
300.0,0.00123
"""

    # Unknown kind file (simulates future tap_tone_pi feature)
    future_analysis = json.dumps({
        "analysis_type": "future_mode_shape",
        "version": "experimental_v2",
        "data": [1, 2, 3, 4, 5]
    }, indent=2).encode("utf-8")

    # Another unknown kind (binary-ish)
    mystery_data = b"MYSTERY_FORMAT_v1\x00\x01\x02\x03\x04\x05"

    # Session meta
    session_meta = json.dumps({
        "session_id": "unknown_kind_test",
        "notes": "Fixture for testing unknown kind fallback"
    }, indent=2).encode("utf-8")

    files_data = {
        "spectra/points/A1/spectrum.csv": spectrum_csv,
        "analysis/future_mode_shape.json": future_analysis,
        "experimental/mystery.bin": mystery_data,
        "meta/session_meta.json": session_meta,
    }

    file_entries = [
        {
            "relpath": "spectra/points/A1/spectrum.csv",
            "sha256": sha256_bytes(spectrum_csv),
            "bytes": len(spectrum_csv),
            "mime": "text/csv",
            "kind": "spectrum_csv",
        },
        {
            "relpath": "analysis/future_mode_shape.json",
            "sha256": sha256_bytes(future_analysis),
            "bytes": len(future_analysis),
            "mime": "application/json",
            "kind": "future_mode_shape",  # UNKNOWN KIND
        },
        {
            "relpath": "experimental/mystery.bin",
            "sha256": sha256_bytes(mystery_data),
            "bytes": len(mystery_data),
            "mime": "application/octet-stream",
            "kind": "experimental_binary",  # UNKNOWN KIND
        },
        {
            "relpath": "meta/session_meta.json",
            "sha256": sha256_bytes(session_meta),
            "bytes": len(session_meta),
            "mime": "application/json",
            "kind": "session_meta",
        },
    ]

    manifest_bytes, _ = create_manifest(
        files=file_entries,
        source_capdir="unknown_kind_test_session",
        contents={
            "audio": False,
            "spectra": True,
            "coherence": False,
            "ods": False,
            "wolf": False,
            "plots": False,
            "provenance": False,
        }
    )

    # Create ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest_bytes)
        for relpath, data in files_data.items():
            zf.writestr(relpath, data)

    return zip_buffer.getvalue()


def main():
    out_dir = Path(__file__).parent

    # Generate coherence fixture
    coherence_zip = create_session_with_coherence()
    coherence_path = out_dir / "session_with_coherence.zip"
    coherence_path.write_bytes(coherence_zip)
    print(f"Created: {coherence_path} ({len(coherence_zip)} bytes)")

    # Generate unknown kind fixture
    unknown_zip = create_session_unknown_kind()
    unknown_path = out_dir / "session_unknown_kind.zip"
    unknown_path.write_bytes(unknown_zip)
    print(f"Created: {unknown_path} ({len(unknown_zip)} bytes)")


if __name__ == "__main__":
    main()
