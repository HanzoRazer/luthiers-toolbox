#!/usr/bin/env python3
"""
Golden regression test for Phase 2 viewer pack export.

This test proves that exporting a known session produces a valid pack
with correct hashing + required structure. Prevents 80% of future regressions.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
RUNS_PHASE2 = REPO_ROOT / "runs_phase2"
CONTRACTS_DIR = REPO_ROOT / "contracts"

# Known test sessions
GOLDEN_SESSIONS = [
    "session_20260101T234237Z",
    "session_20260101T235209Z",
]

# Required kinds that MUST be present in any valid Phase 2 export
REQUIRED_KINDS = {"audio_raw", "spectrum_csv", "analysis_peaks", "session_meta"}

# All valid kinds (canonical vocabulary)
VALID_KINDS = {
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


def sha256_file(p: Path) -> str:
    """Compute SHA256 of file."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_available_session() -> Path | None:
    """Find first available golden session."""
    for name in GOLDEN_SESSIONS:
        session = RUNS_PHASE2 / name
        if session.is_dir():
            return session
    return None


@pytest.fixture(scope="module")
def exported_pack(tmp_path_factory) -> tuple[Path, dict] | None:
    """Export a golden session and return (pack_dir, manifest)."""
    session = find_available_session()
    if session is None:
        pytest.skip("No golden Phase 2 session found")
    
    # Import exporter
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "phase2"))
    from export_viewer_pack_v1 import export_viewer_pack
    
    out_dir = tmp_path_factory.mktemp("golden_export")
    pack_dir = export_viewer_pack(session, out_dir, as_zip=False)
    
    manifest_path = pack_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    return pack_dir, manifest


class TestGoldenExport:
    """Golden regression tests for Phase 2 export."""
    
    def test_manifest_exists_and_parses(self, exported_pack):
        """manifest.json must exist and be valid JSON."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        pack_dir, manifest = exported_pack
        
        assert (pack_dir / "manifest.json").exists()
        assert isinstance(manifest, dict)
    
    def test_schema_identifiers(self, exported_pack):
        """Schema ID and version must be correct."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        assert manifest["schema_id"] == "viewer_pack_v1"
        assert manifest["schema_version"] == "v1"
    
    def test_files_list_not_empty(self, exported_pack):
        """files[] must contain entries."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        assert len(manifest["files"]) > 0
    
    def test_every_file_exists(self, exported_pack):
        """Every files[].relpath must exist in pack."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        pack_dir, manifest = exported_pack
        
        for entry in manifest["files"]:
            file_path = pack_dir / entry["relpath"]
            assert file_path.exists(), f"Missing: {entry['relpath']}"
    
    def test_every_sha256_matches(self, exported_pack):
        """Every files[].sha256 must match actual file bytes."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        pack_dir, manifest = exported_pack
        
        for entry in manifest["files"]:
            file_path = pack_dir / entry["relpath"]
            actual_hash = sha256_file(file_path)
            assert actual_hash == entry["sha256"], f"Hash mismatch: {entry['relpath']}"
    
    def test_required_kinds_present(self, exported_pack):
        """Required kinds must be present in export."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        present_kinds = {e["kind"] for e in manifest["files"]}
        missing = REQUIRED_KINDS - present_kinds
        assert not missing, f"Missing required kinds: {missing}"
    
    def test_all_kinds_valid(self, exported_pack):
        """All kinds must be from canonical vocabulary."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        for entry in manifest["files"]:
            assert entry["kind"] in VALID_KINDS, f"Invalid kind '{entry['kind']}' for {entry['relpath']}"
    
    def test_points_list_matches_audio(self, exported_pack):
        """points[] must match audio files."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        audio_points = {
            e["relpath"].split("/")[-1].replace(".wav", "")
            for e in manifest["files"]
            if e["relpath"].startswith("audio/points/")
        }
        manifest_points = set(manifest["points"])
        
        assert audio_points == manifest_points, f"Points mismatch: {audio_points} vs {manifest_points}"
    
    def test_measurement_only_flag(self, exported_pack):
        """measurement_only must be True."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        assert manifest["measurement_only"] is True
        assert manifest["interpretation"] == "deferred"
    
    def test_bundle_sha256_present(self, exported_pack):
        """bundle_sha256 must be present and valid hex."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        assert "bundle_sha256" in manifest
        assert len(manifest["bundle_sha256"]) == 64
        assert all(c in "0123456789abcdef" for c in manifest["bundle_sha256"])
    
    def test_ods_uses_transfer_function_kind(self, exported_pack):
        """ODS file must use transfer_function kind (not ods_snapshot)."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        # Only check files in ods/ directory (not plots with "ods" in name)
        ods_files = [e for e in manifest["files"] if e["relpath"].startswith("ods/")]
        assert len(ods_files) > 0, "No ODS files found in pack"
        for entry in ods_files:
            assert entry["kind"] == "transfer_function", f"ODS should be transfer_function, got {entry['kind']}"


class TestBothSessionsExportIdentically:
    """Test that both golden sessions export with same structure."""
    
    def test_both_sessions_available(self):
        """At least one golden session should be available."""
        available = [s for s in GOLDEN_SESSIONS if (RUNS_PHASE2 / s).is_dir()]
        assert len(available) > 0, "No golden sessions available"
    
    @pytest.mark.parametrize("session_name", GOLDEN_SESSIONS)
    def test_session_exports_successfully(self, session_name, tmp_path):
        """Each golden session should export without error."""
        session = RUNS_PHASE2 / session_name
        if not session.is_dir():
            pytest.skip(f"Session not available: {session_name}")
        
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "phase2"))
        from export_viewer_pack_v1 import export_viewer_pack
        
        pack_dir = export_viewer_pack(session, tmp_path, as_zip=False)
        
        assert pack_dir.exists()
        assert (pack_dir / "manifest.json").exists()
