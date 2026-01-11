"""
Gate tests for ToolBox -> Smart Guitar Safe Export v1

These tests enforce the contract boundary:
- No manufacturing content (G-code, toolpaths, CAM)
- No RMOS authority artifacts
- No secrets
- Content-addressed integrity
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.smart_guitar_export import (
    ExportBuilder,
    validate_bundle,
    validate_manifest,
    create_export_bundle,
    FORBIDDEN_EXTENSIONS,
    SmartGuitarExportManifest,
)


# =============================================================================
# Schema Validation Tests
# =============================================================================


def test_manifest_schema_rejects_missing_required_fields():
    """Manifest must have all required fields."""
    incomplete = {"schema_id": "toolbox_smart_guitar_safe_export"}
    result = validate_manifest(incomplete)
    assert not result.valid
    assert len(result.errors) > 0


def test_manifest_schema_accepts_valid_manifest():
    """Valid manifest passes validation."""
    valid = {
        "schema_id": "toolbox_smart_guitar_safe_export",
        "schema_version": "v1",
        "created_at_utc": "2026-01-10T00:00:00Z",
        "export_id": "test_001",
        "producer": {
            "system": "luthiers-toolbox",
            "repo": "https://github.com/test/repo",
            "commit": "abc123",
        },
        "scope": {
            "domain": "education",
            "safe_for": "smart_guitar",
        },
        "content_policy": {
            "no_manufacturing": True,
            "no_toolpaths": True,
            "no_rmos_authority": True,
            "no_secrets": True,
        },
        "files": [],
        "bundle_sha256": "abc123",
    }
    result = validate_manifest(valid)
    assert result.valid, f"Errors: {result.errors}"


# =============================================================================
# Content Policy Tests
# =============================================================================


def test_manifest_rejects_manufacturing_flag_false():
    """content_policy.no_manufacturing must be true."""
    manifest = {
        "schema_id": "toolbox_smart_guitar_safe_export",
        "schema_version": "v1",
        "created_at_utc": "2026-01-10T00:00:00Z",
        "export_id": "test_001",
        "producer": {"system": "luthiers-toolbox", "repo": "x", "commit": "x"},
        "scope": {"domain": "education", "safe_for": "smart_guitar"},
        "content_policy": {
            "no_manufacturing": False,  # BAD
            "no_toolpaths": True,
            "no_rmos_authority": True,
            "no_secrets": True,
        },
        "files": [],
        "bundle_sha256": "x",
    }
    result = validate_manifest(manifest)
    # Should fail at Pydantic level due to Literal[True]
    assert not result.valid


def test_manifest_rejects_toolpaths_flag_false():
    """content_policy.no_toolpaths must be true."""
    manifest = {
        "schema_id": "toolbox_smart_guitar_safe_export",
        "schema_version": "v1",
        "created_at_utc": "2026-01-10T00:00:00Z",
        "export_id": "test_001",
        "producer": {"system": "luthiers-toolbox", "repo": "x", "commit": "x"},
        "scope": {"domain": "education", "safe_for": "smart_guitar"},
        "content_policy": {
            "no_manufacturing": True,
            "no_toolpaths": False,  # BAD
            "no_rmos_authority": True,
            "no_secrets": True,
        },
        "files": [],
        "bundle_sha256": "x",
    }
    result = validate_manifest(manifest)
    assert not result.valid


# =============================================================================
# Forbidden Extension Tests
# =============================================================================


def test_manifest_rejects_gcode_extension():
    """Files with .nc extension are forbidden."""
    manifest = {
        "schema_id": "toolbox_smart_guitar_safe_export",
        "schema_version": "v1",
        "created_at_utc": "2026-01-10T00:00:00Z",
        "export_id": "test_001",
        "producer": {"system": "luthiers-toolbox", "repo": "x", "commit": "x"},
        "scope": {"domain": "education", "safe_for": "smart_guitar"},
        "content_policy": {
            "no_manufacturing": True,
            "no_toolpaths": True,
            "no_rmos_authority": True,
            "no_secrets": True,
        },
        "files": [
            {
                "relpath": "assets/toolpath.nc",  # FORBIDDEN
                "sha256": "abc123",
                "bytes": 100,
                "mime": "text/plain",
                "kind": "unknown",
            }
        ],
        "bundle_sha256": "x",
    }
    result = validate_manifest(manifest)
    assert not result.valid
    assert any(".nc" in e for e in result.errors)


def test_manifest_rejects_dxf_extension():
    """Files with .dxf extension are forbidden."""
    manifest = {
        "schema_id": "toolbox_smart_guitar_safe_export",
        "schema_version": "v1",
        "created_at_utc": "2026-01-10T00:00:00Z",
        "export_id": "test_001",
        "producer": {"system": "luthiers-toolbox", "repo": "x", "commit": "x"},
        "scope": {"domain": "education", "safe_for": "smart_guitar"},
        "content_policy": {
            "no_manufacturing": True,
            "no_toolpaths": True,
            "no_rmos_authority": True,
            "no_secrets": True,
        },
        "files": [
            {
                "relpath": "assets/design.dxf",  # FORBIDDEN
                "sha256": "abc123",
                "bytes": 100,
                "mime": "application/dxf",
                "kind": "unknown",
            }
        ],
        "bundle_sha256": "x",
    }
    result = validate_manifest(manifest)
    assert not result.valid
    assert any(".dxf" in e for e in result.errors)


@pytest.mark.parametrize("ext", list(FORBIDDEN_EXTENSIONS)[:5])
def test_forbidden_extensions_rejected(ext):
    """All forbidden extensions should be rejected."""
    manifest = {
        "schema_id": "toolbox_smart_guitar_safe_export",
        "schema_version": "v1",
        "created_at_utc": "2026-01-10T00:00:00Z",
        "export_id": "test_001",
        "producer": {"system": "luthiers-toolbox", "repo": "x", "commit": "x"},
        "scope": {"domain": "education", "safe_for": "smart_guitar"},
        "content_policy": {
            "no_manufacturing": True,
            "no_toolpaths": True,
            "no_rmos_authority": True,
            "no_secrets": True,
        },
        "files": [
            {
                "relpath": f"assets/file{ext}",
                "sha256": "abc123",
                "bytes": 100,
                "mime": "application/octet-stream",
                "kind": "unknown",
            }
        ],
        "bundle_sha256": "x",
    }
    result = validate_manifest(manifest)
    assert not result.valid, f"Extension {ext} should be forbidden"


# =============================================================================
# Builder Tests
# =============================================================================


def test_builder_creates_valid_bundle():
    """ExportBuilder creates a valid bundle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = ExportBuilder(domain="education")
        builder.add_topic("setup", "Setup Guide", tags=["beginner"])
        builder.add_lesson(
            "lesson_001",
            "Clean Fretting",
            "beginner",
            "# Clean Fretting\n\nPress firmly behind the fret.",
        )
        builder.add_drill(
            "drill_001",
            "Alternate Picking",
            tempo_min=60,
            tempo_max=120,
            metrics=["timing", "consistency"],
        )

        bundle_path = builder.build(tmpdir)

        assert bundle_path.exists()
        assert (bundle_path / "manifest.json").exists()
        assert (bundle_path / "index" / "topics.json").exists()
        assert (bundle_path / "index" / "lessons.json").exists()
        assert (bundle_path / "index" / "drills.json").exists()

        # Validate the bundle
        result = validate_bundle(bundle_path)
        assert result.valid, f"Errors: {result.errors}"


def test_builder_rejects_forbidden_file():
    """ExportBuilder rejects forbidden file extensions."""
    builder = ExportBuilder(domain="education")

    with pytest.raises(ValueError, match="Forbidden extension"):
        builder.add_file("toolpath.nc", b"G0 X0 Y0")


def test_create_export_bundle_validates_output():
    """create_export_bundle validates the bundle by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_path = create_export_bundle(
            tmpdir,
            domain="practice",
            topics=[{"id": "warmup", "title": "Warmup", "tags": ["daily"]}],
            lessons=[{
                "id": "lesson_001",
                "title": "Finger Stretches",
                "level": "beginner",
                "content_md": "# Finger Stretches\n\nStretch before playing.",
            }],
        )

        assert bundle_path.exists()
        result = validate_bundle(bundle_path)
        assert result.valid


# =============================================================================
# Bundle Validation Tests
# =============================================================================


def test_validate_bundle_detects_missing_file():
    """validate_bundle detects missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_path = Path(tmpdir) / "test_bundle"
        bundle_path.mkdir()

        manifest = {
            "schema_id": "toolbox_smart_guitar_safe_export",
            "schema_version": "v1",
            "created_at_utc": "2026-01-10T00:00:00Z",
            "export_id": "test_001",
            "producer": {"system": "luthiers-toolbox", "repo": "x", "commit": "x"},
            "scope": {"domain": "education", "safe_for": "smart_guitar"},
            "content_policy": {
                "no_manufacturing": True,
                "no_toolpaths": True,
                "no_rmos_authority": True,
                "no_secrets": True,
            },
            "files": [
                {
                    "relpath": "assets/missing.md",  # File doesn't exist
                    "sha256": "abc123",
                    "bytes": 100,
                    "mime": "text/markdown",
                    "kind": "lesson_md",
                }
            ],
            "bundle_sha256": "x",
        }

        (bundle_path / "manifest.json").write_text(json.dumps(manifest))

        result = validate_bundle(bundle_path)
        assert not result.valid
        assert any("not found" in e.lower() for e in result.errors)


def test_validate_bundle_detects_sha256_mismatch():
    """validate_bundle detects SHA256 mismatches."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_path = Path(tmpdir) / "test_bundle"
        bundle_path.mkdir()
        (bundle_path / "assets").mkdir()

        # Write a file
        content = b"Hello, World!"
        (bundle_path / "assets" / "hello.md").write_bytes(content)

        # Manifest with wrong SHA256
        manifest = {
            "schema_id": "toolbox_smart_guitar_safe_export",
            "schema_version": "v1",
            "created_at_utc": "2026-01-10T00:00:00Z",
            "export_id": "test_001",
            "producer": {"system": "luthiers-toolbox", "repo": "x", "commit": "x"},
            "scope": {"domain": "education", "safe_for": "smart_guitar"},
            "content_policy": {
                "no_manufacturing": True,
                "no_toolpaths": True,
                "no_rmos_authority": True,
                "no_secrets": True,
            },
            "files": [
                {
                    "relpath": "assets/hello.md",
                    "sha256": "wrong_hash",  # BAD
                    "bytes": len(content),
                    "mime": "text/markdown",
                    "kind": "lesson_md",
                }
            ],
            "bundle_sha256": "x",
        }

        (bundle_path / "manifest.json").write_text(json.dumps(manifest))

        result = validate_bundle(bundle_path)
        assert not result.valid
        assert any("sha256 mismatch" in e.lower() for e in result.errors)


# =============================================================================
# Integration Test
# =============================================================================


def test_full_export_workflow():
    """End-to-end test of export creation and validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Build a complete bundle
        bundle_path = create_export_bundle(
            tmpdir,
            domain="coaching",
            export_id="integration_test_001",
            topics=[
                {"id": "technique", "title": "Technique", "tags": ["core"]},
                {"id": "theory", "title": "Music Theory", "tags": ["knowledge"]},
            ],
            lessons=[
                {
                    "id": "lesson_fretting",
                    "title": "Clean Fretting Technique",
                    "level": "beginner",
                    "content_md": "# Clean Fretting\n\n1. Place finger behind fret\n2. Apply firm pressure\n3. Check for buzz",
                    "topic_ids": ["technique"],
                },
                {
                    "id": "lesson_scales",
                    "title": "Major Scale Patterns",
                    "level": "intermediate",
                    "content_md": "# Major Scale\n\nThe major scale is the foundation of Western music.",
                    "topic_ids": ["theory"],
                },
            ],
            drills=[
                {
                    "id": "drill_chromatic",
                    "title": "Chromatic Exercise",
                    "tempo_bpm": {"min": 40, "max": 200, "step": 10},
                    "metrics": ["timing", "accuracy", "string_noise"],
                },
            ],
        )

        # Validate
        result = validate_bundle(bundle_path)
        assert result.valid, f"Errors: {result.errors}"
        assert result.manifest is not None

        # Check manifest content
        manifest = result.manifest
        assert manifest.export_id == "integration_test_001"
        assert manifest.scope.domain.value == "coaching"
        assert manifest.content_policy.no_manufacturing is True
        assert manifest.content_policy.no_toolpaths is True
        assert manifest.content_policy.no_rmos_authority is True
        assert manifest.content_policy.no_secrets is True

        # Check files exist
        assert len(manifest.files) >= 5  # 3 index + 2 lessons + provenance
