"""Smoke tests for acoustics import endpoint (proxied to real router_import)."""

import hashlib
import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def _make_minimal_viewer_pack() -> bytes:
    """Create a minimal valid viewer_pack ZIP for testing."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Dummy audio file for the manifest
        dummy_audio = b"RIFF" + b" " * 100  # Minimal WAV-ish content
        audio_sha256 = hashlib.sha256(dummy_audio).hexdigest()  # Real SHA256

        # manifest.json - minimal valid TapToneBundleManifestV1
        manifest = {
            "manifest_version": "TapToneBundleManifestV1",
            "bundle_id": "test_bundle_001",
            "bundle_sha256": "0" * 64,  # Bundle hash (not verified by import)
            "capture_started_at_utc": "2024-01-01T00:00:00Z",
            "capture_finished_at_utc": "2024-01-01T00:01:00Z",
            "tool_id": "tap_tone_pi",
            "event_type": "tap_tone.capture",
            "mode": "acoustics",
            "units": "mm",
            "files": [
                {
                    "relpath": "audio/tap_001.wav",
                    "sha256": audio_sha256,
                    "bytes": len(dummy_audio),
                    "mime": "audio/wav",
                    "kind": "audio_raw",
                }
            ],
        }
        zf.writestr("manifest.json", json.dumps(manifest))

        # validation_report.json - passed=true
        report = {
            "schema_id": "validation_report_v1",
            "passed": True,
            "errors": [],
            "warnings": [],
        }
        zf.writestr("validation_report.json", json.dumps(report))

        # attachments/ directory with the audio file
        zf.writestr("attachments/audio/tap_001.wav", dummy_audio)

    buf.seek(0)
    return buf.read()


def _make_invalid_zip() -> bytes:
    """Create an invalid ZIP (not actually a ZIP file)."""
    return b"this is not a zip file"


def _make_zip_without_validation_report() -> bytes:
    """Create a ZIP without validation_report.json."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Minimal manifest (will fail validation anyway after hitting 422 for missing report)
        manifest = {
            "manifest_version": "TapToneBundleManifestV1",
            "bundle_id": "test_bundle_002",
            "bundle_sha256": "0" * 64,
            "capture_started_at_utc": "2024-01-01T00:00:00Z",
            "capture_finished_at_utc": "2024-01-01T00:01:00Z",
            "tool_id": "tap_tone_pi",
            "event_type": "tap_tone.capture",
            "mode": "acoustics",
            "units": "mm",
            "files": [{"relpath": "a.wav", "sha256": "a" * 64, "bytes": 10, "mime": "audio/wav", "kind": "audio_raw"}],
        }
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("attachments/.gitkeep", "")
    buf.seek(0)
    return buf.read()


def _make_zip_with_failed_validation() -> bytes:
    """Create a ZIP with validation_report.json where passed=false."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            "manifest_version": "TapToneBundleManifestV1",
            "bundle_id": "test_bundle_003",
            "bundle_sha256": "0" * 64,
            "capture_started_at_utc": "2024-01-01T00:00:00Z",
            "capture_finished_at_utc": "2024-01-01T00:01:00Z",
            "tool_id": "tap_tone_pi",
            "event_type": "tap_tone.capture",
            "mode": "acoustics",
            "units": "mm",
            "files": [{"relpath": "a.wav", "sha256": "a" * 64, "bytes": 10, "mime": "audio/wav", "kind": "audio_raw"}],
        }
        zf.writestr("manifest.json", json.dumps(manifest))

        report = {
            "schema_id": "validation_report_v1",
            "passed": False,
            "errors": [{"message": "Test error"}],
            "warnings": [],
        }
        zf.writestr("validation_report.json", json.dumps(report))
        zf.writestr("attachments/.gitkeep", "")
    buf.seek(0)
    return buf.read()


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_import_zip_endpoint_exists(client):
    """POST /api/rmos/acoustics/import-zip endpoint exists."""
    # Empty file should return 422 (validation error), not 404
    response = client.post("/api/rmos/acoustics/import-zip", files={})
    assert response.status_code != 404


def test_rebuild_attachment_index_endpoint_exists(client):
    """POST /api/rmos/acoustics/index/rebuild_attachment_meta endpoint exists."""
    response = client.post("/api/rmos/acoustics/index/rebuild_attachment_meta")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "entries_indexed" in data


# =============================================================================
# Import ZIP - Valid Cases
# =============================================================================

def test_import_zip_valid_pack_returns_200(client):
    """POST /api/rmos/acoustics/import-zip with valid pack returns 200."""
    zip_data = _make_minimal_viewer_pack()
    response = client.post(
        "/api/rmos/acoustics/import-zip",
        files={"file": ("test.zip", zip_data, "application/zip")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "run_id" in data


def test_import_zip_returns_run_id(client):
    """POST /api/rmos/acoustics/import-zip returns run_id."""
    zip_data = _make_minimal_viewer_pack()
    response = client.post(
        "/api/rmos/acoustics/import-zip",
        files={"file": ("test.zip", zip_data, "application/zip")},
    )
    data = response.json()
    assert "run_id" in data
    assert data["run_id"] is not None


def test_import_zip_accepts_session_id(client):
    """POST /api/rmos/acoustics/import-zip accepts session_id form field."""
    zip_data = _make_minimal_viewer_pack()
    response = client.post(
        "/api/rmos/acoustics/import-zip",
        files={"file": ("test.zip", zip_data, "application/zip")},
        data={"session_id": "test_session_123"},
    )
    assert response.status_code == 200


def test_import_zip_accepts_batch_label(client):
    """POST /api/rmos/acoustics/import-zip accepts batch_label form field."""
    zip_data = _make_minimal_viewer_pack()
    response = client.post(
        "/api/rmos/acoustics/import-zip",
        files={"file": ("test.zip", zip_data, "application/zip")},
        data={"batch_label": "guitar_001"},
    )
    assert response.status_code == 200


# =============================================================================
# Import ZIP - Error Cases
# =============================================================================

def test_import_zip_invalid_zip_returns_400(client):
    """POST /api/rmos/acoustics/import-zip with invalid ZIP returns 400."""
    invalid_data = _make_invalid_zip()
    response = client.post(
        "/api/rmos/acoustics/import-zip",
        files={"file": ("test.zip", invalid_data, "application/zip")},
    )
    assert response.status_code == 400


def test_import_zip_missing_validation_report_returns_422(client, monkeypatch):
    """POST /api/rmos/acoustics/import-zip without validation_report returns 422."""
    # Ensure allow_missing is False (default)
    monkeypatch.delenv("ACOUSTICS_ALLOW_MISSING_VALIDATION_REPORT", raising=False)

    zip_data = _make_zip_without_validation_report()
    response = client.post(
        "/api/rmos/acoustics/import-zip",
        files={"file": ("test.zip", zip_data, "application/zip")},
    )
    assert response.status_code == 422
    data = response.json()
    assert "validation" in str(data).lower() or "missing" in str(data).lower()


def test_import_zip_failed_validation_returns_422(client):
    """POST /api/rmos/acoustics/import-zip with passed=false returns 422."""
    zip_data = _make_zip_with_failed_validation()
    response = client.post(
        "/api/rmos/acoustics/import-zip",
        files={"file": ("test.zip", zip_data, "application/zip")},
    )
    assert response.status_code == 422


# =============================================================================
# Rebuild Index
# =============================================================================

def test_rebuild_attachment_index_returns_ok(client):
    """POST /api/rmos/acoustics/index/rebuild_attachment_meta returns ok."""
    response = client.post("/api/rmos/acoustics/index/rebuild_attachment_meta")
    data = response.json()
    assert data["ok"] is True


def test_rebuild_attachment_index_returns_count(client):
    """POST /api/rmos/acoustics/index/rebuild_attachment_meta returns entries_indexed."""
    response = client.post("/api/rmos/acoustics/index/rebuild_attachment_meta")
    data = response.json()
    assert "entries_indexed" in data
    assert isinstance(data["entries_indexed"], int)
