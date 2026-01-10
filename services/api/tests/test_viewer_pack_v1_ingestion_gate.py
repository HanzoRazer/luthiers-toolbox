#!/usr/bin/env python3
"""
VIEWER_PACK_V1_CONTRACT_GATE (Consumer Side)

Gate ID: VIEWER_PACK_V1_CONTRACT_GATE

This is a CONTRACT GATE, not a feature test. It ensures:
  "If ToolBox receives a viewer_pack_v1 zip, it validates."

Gate layers:
  Layer A: validate_viewer_pack_v1.py CLI (vendored from tap_tone_pi)
  Layer B: This pytest wrapper (validate fixture zips)

This is the consumer-side complement to tap_tone_pi's producer-side gate.
Together they ensure: "If a pack exports, it validates; if it validates, ToolBox can render it."

Cross-repo contract with tap_tone_pi.
See: docs/gates/VIEWER_PACK_V1_GATE.md
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]  # services/api/tests -> repo root
VALIDATOR_CLI = REPO_ROOT / "scripts" / "validate" / "validate_viewer_pack_v1.py"
SCHEMA_PATH = REPO_ROOT / "contracts" / "viewer_pack_v1.schema.json"

# Fixture zips for CI
FIXTURE_ZIPS = [
    REPO_ROOT / "services" / "api" / "tests" / "fixtures" / "viewer_packs" / "session_minimal.zip",
]

# Client-side evidence module (for type alignment checks)
EVIDENCE_TYPES_PATH = REPO_ROOT / "packages" / "client" / "src" / "evidence" / "types.ts"


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


def compute_schema_hash(schema_path: Path) -> str:
    """Compute SHA256 hash of schema file for parity checks."""
    content = schema_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def extract_kind_enum_from_schema(schema: Dict[str, Any]) -> set:
    """Extract the 'kind' enum values from the schema."""
    file_entry_def = schema.get("$defs", {}).get("fileEntry", {})
    kind_prop = file_entry_def.get("properties", {}).get("kind", {})
    return set(kind_prop.get("enum", []))


# ---------------------------------------------------------------------------
# Gate Tests
# ---------------------------------------------------------------------------

class TestViewerPackV1IngestionGate:
    """
    VIEWER_PACK_V1_CONTRACT_GATE - Ingestion Tests.

    Consumer-side contract gate ensuring ToolBox can
    validate and ingest packs produced by tap_tone_pi.
    """

    def test_validator_cli_exists(self):
        """Vendored validator CLI must exist."""
        assert VALIDATOR_CLI.is_file(), (
            f"Validator CLI not found: {VALIDATOR_CLI}\n"
            "Vendor from tap_tone_pi: scripts/phase2/validate_viewer_pack_v1.py"
        )

    def test_schema_exists(self):
        """Vendored schema file must exist."""
        assert SCHEMA_PATH.is_file(), (
            f"Schema not found: {SCHEMA_PATH}\n"
            "Vendor from tap_tone_pi: contracts/viewer_pack_v1.schema.json"
        )

    def test_schema_has_required_structure(self):
        """Schema must have expected structure."""
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        # Must have additionalProperties: false
        assert schema.get("additionalProperties") is False, \
            "Schema must have additionalProperties: false"

        # Must have required keys
        required = schema.get("required", [])
        expected_required = [
            "schema_version", "schema_id", "created_at_utc", "source_capdir",
            "detected_phase", "measurement_only", "interpretation", "points",
            "contents", "files", "bundle_sha256"
        ]
        for key in expected_required:
            assert key in required, f"Schema missing required key: {key}"

    def test_validate_fixture_zips(self):
        """
        Validate all committed fixture zips.

        This is the core consumer gate test.
        """
        available_fixtures = [f for f in FIXTURE_ZIPS if f.is_file()]

        if not available_fixtures:
            pytest.skip(
                "No fixture zips found. To enable this gate:\n"
                "  1. Export a minimal pack from tap_tone_pi\n"
                "  2. Commit to services/api/tests/fixtures/viewer_packs/session_minimal.zip"
            )

        for fixture_zip in available_fixtures:
            result = run_validator(fixture_zip)
            assert result.returncode == 0, (
                f"Validation failed for {fixture_zip.name}:\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

    def test_validator_rejects_invalid_pack(self, tmp_path: Path):
        """Validator must reject packs with schema violations."""
        invalid_pack = tmp_path / "invalid_pack"
        invalid_pack.mkdir()

        bad_manifest = {
            "schema_version": "v1",
            "schema_id": "viewer_pack_v1",
            # Missing required fields
        }
        (invalid_pack / "manifest.json").write_text(
            json.dumps(bad_manifest, indent=2), encoding="utf-8"
        )

        result = run_validator(invalid_pack)
        assert result.returncode == 2, (
            f"Validator should reject invalid manifest (exit 2), got {result.returncode}"
        )


class TestViewerPackSchemaParityGate:
    """
    VIEWER_PACK_V1_CONTRACT_GATE - Schema Parity Tests.

    Detect drift between tap_tone_pi and ToolBox vendored schema.
    """

    # Pin this hash to detect vendored schema changes
    # Update intentionally when tap_tone_pi schema changes
    EXPECTED_SCHEMA_HASH = None  # Set after first run

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

    def test_kind_vocabulary_coverage(self):
        """
        ToolBox must support all kinds from the schema.

        Soft policy: unknown kinds fall back to UnknownRenderer.
        This test ensures we know what kinds exist in the contract.
        """
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        schema_kinds = extract_kind_enum_from_schema(schema)

        # Canonical vocabulary from tap_tone_pi schema
        expected_schema_kinds = {
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

        # Check for unexpected drift
        missing = expected_schema_kinds - schema_kinds
        extra = schema_kinds - expected_schema_kinds

        if missing:
            pytest.fail(f"Schema missing expected kinds: {missing}")
        if extra:
            # This is a warning, not a failure (soft policy)
            import warnings
            warnings.warn(
                f"Schema has new kinds not in expected vocabulary: {extra}\n"
                "Update expected_schema_kinds if intentional."
            )

    def test_toolbox_types_cover_schema_kinds(self):
        """
        ToolBox types.ts must handle all schema kinds (or fall back to unknown).

        This is an informational check - soft policy means we don't fail on gaps.
        """
        if not EVIDENCE_TYPES_PATH.is_file():
            pytest.skip("types.ts not found - skipping TS coverage check")

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        schema_kinds = extract_kind_enum_from_schema(schema)

        # Read types.ts and extract EvidenceFileKind values
        types_content = EVIDENCE_TYPES_PATH.read_text(encoding="utf-8")

        # Simple extraction - look for quoted strings in the type definition
        import re
        # Match: | "audio_raw" or "audio_raw" |
        kind_pattern = r'"([a-z_]+)"'
        ts_kinds = set(re.findall(kind_pattern, types_content))

        # Check coverage
        uncovered = schema_kinds - ts_kinds - {"unknown", "manifest"}  # manifest and unknown are special

        if uncovered:
            # Informational only - soft policy
            import warnings
            warnings.warn(
                f"Schema kinds not explicitly in types.ts: {uncovered}\n"
                "These will fall back to 'unknown' renderer."
            )


class TestViewerPackClientIntegration:
    """
    VIEWER_PACK_V1_CONTRACT_GATE - Client Integration Tests.

    Verify the client-side evidence/ module can load valid packs.
    """

    def test_evidence_module_exports_exist(self):
        """Evidence module must export required functions."""
        evidence_dir = REPO_ROOT / "packages" / "client" / "src" / "evidence"
        evidence_index = evidence_dir / "index.ts"
        if not evidence_index.is_file():
            pytest.skip("evidence/index.ts not found")

        # Check that index re-exports from the right modules
        index_content = evidence_index.read_text(encoding="utf-8")
        assert "zip_loader" in index_content, "index.ts should re-export from zip_loader"
        assert "validate" in index_content, "index.ts should re-export from validate"

        # Check that the actual modules export the required functions
        zip_loader = evidence_dir / "zip_loader.ts"
        validate_ts = evidence_dir / "validate.ts"

        if zip_loader.is_file():
            zip_content = zip_loader.read_text(encoding="utf-8")
            assert "loadNormalizedPack" in zip_content, \
                "zip_loader.ts should export loadNormalizedPack"

        if validate_ts.is_file():
            validate_content = validate_ts.read_text(encoding="utf-8")
            assert "validateViewerPackV1" in validate_content, \
                "validate.ts should export validateViewerPackV1"
            assert "detectSchema" in validate_content, \
                "validate.ts should export detectSchema"

    def test_validate_ts_handles_viewer_pack_v1(self):
        """validate.ts must handle viewer_pack_v1 schema."""
        validate_ts = REPO_ROOT / "packages" / "client" / "src" / "evidence" / "validate.ts"
        if not validate_ts.is_file():
            pytest.skip("validate.ts not found")

        content = validate_ts.read_text(encoding="utf-8")

        # Must have viewer_pack_v1 detection
        assert "viewer_pack_v1" in content, \
            "validate.ts must handle viewer_pack_v1 schema"

        # Must have validateViewerPackV1 function
        assert "validateViewerPackV1" in content, \
            "validate.ts must export validateViewerPackV1 function"
