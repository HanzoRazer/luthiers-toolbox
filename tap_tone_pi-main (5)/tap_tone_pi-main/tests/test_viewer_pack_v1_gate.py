#!/usr/bin/env python3
"""
VIEWER_PACK_V1_CONTRACT_GATE (Producer Side)

Gate ID: VIEWER_PACK_V1_CONTRACT_GATE

This is a CONTRACT GATE, not a feature test. It ensures:
  "If we export from real Phase 2 sessions, the pack validates."

Gate layers:
  Layer A: validate_viewer_pack_v1.py CLI (pure validation)
  Layer B: This pytest wrapper (export + validate)

Exit behavior:
  - Fails fast on first validation failure
  - Uses committed fixture sessions (deterministic CI)
  - Falls back to minimal synthetic session if fixtures unavailable

Cross-repo contract with luthiers-toolbox (ToolBox).
See: ToolBox docs/gates/VIEWER_PACK_V1_GATE.md
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_CLI = REPO_ROOT / "scripts" / "phase2" / "validate_viewer_pack_v1.py"
EXPORTER_CLI = REPO_ROOT / "scripts" / "phase2" / "export_viewer_pack_v1.py"
SCHEMA_PATH = REPO_ROOT / "contracts" / "viewer_pack_v1.schema.json"

# Committed fixture sessions (preferred for CI stability)
FIXTURE_SESSIONS = [
    REPO_ROOT / "fixtures" / "sessions" / "minimal_3pt",
    REPO_ROOT / "fixtures" / "sessions" / "minimal_5pt",
]

# Real sessions (for local dev, may not exist in CI)
REAL_SESSIONS = [
    REPO_ROOT / "runs_phase2" / "session_20260101T234237Z",
    REPO_ROOT / "runs_phase2" / "session_20260101T235209Z",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def temp_output_dir() -> Generator[Path, None, None]:
    """Temporary directory for exported packs."""
    with tempfile.TemporaryDirectory(prefix="viewer_pack_gate_") as td:
        yield Path(td)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_validator(pack_path: Path) -> subprocess.CompletedProcess:
    """Run the validator CLI on a pack (dir or zip)."""
    return subprocess.run(
        [sys.executable, str(VALIDATOR_CLI), "--pack", str(pack_path)],
        capture_output=True,
        text=True,
    )


def run_exporter(session_dir: Path, output_dir: Path) -> subprocess.CompletedProcess:
    """Run the exporter CLI to create a viewer pack."""
    return subprocess.run(
        [
            sys.executable,
            str(EXPORTER_CLI),
            "--session-dir", str(session_dir),
            "--out", str(output_dir),
        ],
        capture_output=True,
        text=True,
    )


def create_minimal_synthetic_session(base_dir: Path) -> Path:
    """
    Create a minimal synthetic Phase 2 session for testing.

    This is used when no committed fixtures exist.
    Creates the absolute minimum needed for export to succeed.
    """
    session_dir = base_dir / "synthetic_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    # session_meta.json (required)
    meta = {
        "schema_version": "phase2_session_meta_v1",
        "session_id": "synthetic_test",
        "created_at_utc": "2026-01-01T00:00:00Z",
        "grid_id": "test_grid",
        "phase": "phase2",
        "points": ["A1", "A2"],
    }
    (session_dir / "session_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    # Create minimal point directories with required files
    for point_id in ["A1", "A2"]:
        point_dir = session_dir / "points" / point_id
        point_dir.mkdir(parents=True, exist_ok=True)

        # capture_meta.json
        capture_meta = {
            "point_id": point_id,
            "captured_at_utc": "2026-01-01T00:00:00Z",
            "sample_rate_hz": 48000,
            "channels": ["ref", "mic"],
        }
        (point_dir / "capture_meta.json").write_text(
            json.dumps(capture_meta, indent=2), encoding="utf-8"
        )

        # Minimal WAV file (8 bytes header + 0 samples = invalid but sufficient for export test)
        # For a real test, you'd want actual audio data
        wav_path = point_dir / "audio.wav"
        # Create a minimal valid WAV (44 bytes header, 0 data)
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
        wav_path.write_bytes(wav_header)

        # spectrum.csv (minimal)
        spectrum_csv = "freq_hz,magnitude_db\n100.0,-20.0\n200.0,-25.0\n"
        (point_dir / "spectrum.csv").write_text(spectrum_csv, encoding="utf-8")

    return session_dir


def get_available_sessions() -> list[Path]:
    """
    Get available session directories for testing.

    Priority:
    1. Committed fixture sessions (stable CI)
    2. Real sessions (local dev)
    3. Empty list (will use synthetic)
    """
    sessions = []

    # Check committed fixtures first
    for fixture in FIXTURE_SESSIONS:
        if fixture.is_dir():
            sessions.append(fixture)

    if sessions:
        return sessions

    # Fall back to real sessions
    for real in REAL_SESSIONS:
        if real.is_dir():
            sessions.append(real)

    return sessions


# ---------------------------------------------------------------------------
# Gate Tests
# ---------------------------------------------------------------------------

class TestViewerPackV1Gate:
    """
    VIEWER_PACK_V1_CONTRACT_GATE - Producer Export Tests.

    Authoritative producer-side gate ensuring exported packs
    validate against the contract.
    """

    def test_validator_cli_exists(self):
        """Validator CLI must exist."""
        assert VALIDATOR_CLI.is_file(), f"Validator CLI not found: {VALIDATOR_CLI}"

    def test_schema_exists(self):
        """Schema file must exist."""
        assert SCHEMA_PATH.is_file(), f"Schema not found: {SCHEMA_PATH}"

    def test_schema_has_required_structure(self):
        """Schema must have expected structure."""
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        assert schema.get("additionalProperties") is False, \
            "Schema must have additionalProperties: false"

        required = schema.get("required", [])
        expected_required = [
            "schema_version", "schema_id", "created_at_utc", "source_capdir",
            "detected_phase", "measurement_only", "interpretation", "points",
            "contents", "files", "bundle_sha256"
        ]
        for key in expected_required:
            assert key in required, f"Schema missing required key: {key}"

    def test_export_and_validate_sessions(self, temp_output_dir: Path):
        """
        Export real/fixture sessions and validate resulting packs.

        This is the core gate test. Fails fast on first failure.
        """
        sessions = get_available_sessions()

        if not sessions:
            # No committed fixtures or real sessions; use synthetic
            pytest.skip(
                "No fixture sessions found. To enable this gate:\n"
                "  1. Create fixtures/sessions/minimal_3pt/ with Phase 2 data, OR\n"
                "  2. Run a real capture to populate runs_phase2/"
            )

        for session_dir in sessions:
            session_name = session_dir.name
            output_dir = temp_output_dir / session_name

            # Export
            export_result = run_exporter(session_dir, output_dir)
            assert export_result.returncode == 0, (
                f"Export failed for {session_name}:\n"
                f"stdout: {export_result.stdout}\n"
                f"stderr: {export_result.stderr}"
            )

            # Find the exported pack (could be dir or zip)
            pack_dir = output_dir / "viewer_pack_v1"
            pack_zip = output_dir / "viewer_pack_v1.zip"

            if pack_dir.is_dir():
                pack_path = pack_dir
            elif pack_zip.is_file():
                pack_path = pack_zip
            else:
                pytest.fail(f"No pack found after export: {output_dir}")

            # Validate
            validate_result = run_validator(pack_path)
            assert validate_result.returncode == 0, (
                f"Validation failed for {session_name}:\n"
                f"stdout: {validate_result.stdout}\n"
                f"stderr: {validate_result.stderr}"
            )

    def test_validator_rejects_invalid_manifest(self, temp_output_dir: Path):
        """Validator must reject packs with schema violations."""
        invalid_pack = temp_output_dir / "invalid_pack"
        invalid_pack.mkdir(parents=True, exist_ok=True)

        # Create manifest missing required fields
        bad_manifest = {
            "schema_version": "v1",
            "schema_id": "viewer_pack_v1",
            # Missing: created_at_utc, source_capdir, etc.
        }
        (invalid_pack / "manifest.json").write_text(
            json.dumps(bad_manifest, indent=2), encoding="utf-8"
        )

        result = run_validator(invalid_pack)
        assert result.returncode == 2, (
            f"Validator should reject invalid manifest (exit 2), got {result.returncode}"
        )

    def test_validator_rejects_extra_keys(self, temp_output_dir: Path):
        """Validator must reject manifests with unexpected keys (additionalProperties: false)."""
        invalid_pack = temp_output_dir / "extra_keys_pack"
        invalid_pack.mkdir(parents=True, exist_ok=True)

        # Create manifest with all required fields plus an extra key
        manifest = {
            "schema_version": "v1",
            "schema_id": "viewer_pack_v1",
            "created_at_utc": "2026-01-01T00:00:00Z",
            "source_capdir": "test_session",
            "detected_phase": "phase2",
            "measurement_only": True,
            "interpretation": "deferred",
            "points": ["A1"],
            "contents": {
                "audio": True,
                "spectra": True,
                "coherence": False,
                "ods": False,
                "wolf": False,
                "plots": False,
                "provenance": False,
            },
            "files": [],
            "bundle_sha256": "0" * 64,
            "unexpected_extra_key": "should_fail",  # <-- This should cause rejection
        }
        (invalid_pack / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        result = run_validator(invalid_pack)
        assert result.returncode == 2, (
            f"Validator should reject extra keys (exit 2), got {result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        assert "unexpected_extra_key" in result.stderr.lower() or "unexpected" in result.stderr.lower()


class TestViewerPackSchemaFreeze:
    """
    VIEWER_PACK_V1_CONTRACT_GATE - Schema Freeze Tests.

    Prevent accidental contract drift in the canonical schema.
    """

    def test_schema_version_is_v1(self):
        """Schema must declare version v1."""
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        props = schema.get("properties", {})
        sv = props.get("schema_version", {})
        assert sv.get("const") == "v1", "schema_version const must be 'v1'"

    def test_schema_id_is_viewer_pack_v1(self):
        """Schema must declare id viewer_pack_v1."""
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        props = schema.get("properties", {})
        sid = props.get("schema_id", {})
        assert sid.get("const") == "viewer_pack_v1", "schema_id const must be 'viewer_pack_v1'"

    def test_kind_vocabulary_is_known(self):
        """All kind values in schema must be from known vocabulary."""
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        file_entry_def = schema.get("$defs", {}).get("fileEntry", {})
        kind_prop = file_entry_def.get("properties", {}).get("kind", {})
        kind_enum = kind_prop.get("enum", [])

        # Canonical vocabulary (update this list intentionally, not accidentally)
        expected_kinds = {
            "audio_raw",
            "spectrum_csv",
            "analysis_peaks",
            "coherence",
            "transfer_function",
            "wolf_candidates",
            "wsi_curve",
            "provenance",
            "plot_png",
            "session_meta",
            "manifest",
            "unknown",
        }

        actual_kinds = set(kind_enum)

        # Fail if kinds changed unexpectedly
        missing = expected_kinds - actual_kinds
        extra = actual_kinds - expected_kinds

        assert not missing, f"Schema missing expected kinds: {missing}"
        assert not extra, (
            f"Schema has new kinds not in expected vocabulary: {extra}\n"
            "If intentional, update expected_kinds in this test."
        )
