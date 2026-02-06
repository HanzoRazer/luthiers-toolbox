"""
Test viewer_pack_v1 export contract.

Validates that the exporter produces packs matching the schema contract.
"""
from __future__ import annotations

import json
import hashlib
import tempfile
from pathlib import Path

import pytest

# Skip if jsonschema not available
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    jsonschema = None  # type: ignore


REPO_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = REPO_ROOT / "contracts"
RUNS_PHASE2 = REPO_ROOT / "runs_phase2"


def load_schema() -> dict:
    """Load viewer_pack_v1 schema."""
    path = CONTRACTS_DIR / "viewer_pack_v1.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def find_test_session() -> Path | None:
    """Find a Phase 2 session for testing."""
    if not RUNS_PHASE2.is_dir():
        return None
    sessions = sorted(RUNS_PHASE2.glob("session_*"))
    return sessions[0] if sessions else None


@pytest.fixture(scope="module")
def exported_pack(tmp_path_factory) -> tuple[Path, dict] | None:
    """Export a test session and return (zip_path, manifest)."""
    session = find_test_session()
    if session is None:
        pytest.skip("No Phase 2 session found for testing")
    
    # Import here to avoid import errors if deps missing
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from export.viewer_pack_v1_export import export_viewer_pack
    
    out_dir = tmp_path_factory.mktemp("viewer_packs")
    out_path = out_dir / f"{session.name}.zip"
    
    result = export_viewer_pack(session, out_path, keep_unzipped=True)
    return out_path, result.manifest


class TestExportContract:
    """Test that exported packs match the schema contract."""
    
    def test_manifest_exists(self, exported_pack):
        """manifest.json must exist in pack."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        zip_path, manifest = exported_pack
        assert "schema_version" in manifest
        assert manifest["schema_version"] == "v1"
    
    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_manifest_validates_against_schema(self, exported_pack):
        """Manifest must validate against viewer_pack_v1.schema.json."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        schema = load_schema()
        jsonschema.validate(instance=manifest, schema=schema)
    
    def test_meta_grid_exists(self, exported_pack):
        """meta/grid.json must be present for phase2."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        zip_path, manifest = exported_pack
        relpaths = [f["relpath"] for f in manifest["files"]]
        assert "meta/grid.json" in relpaths
    
    def test_at_least_one_audio_point(self, exported_pack):
        """At least one audio/points/*.wav must exist."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        audio_files = [f for f in manifest["files"] if f["relpath"].startswith("audio/points/")]
        assert len(audio_files) > 0, "No audio point files found"
    
    def test_file_hashes_match(self, exported_pack):
        """Every manifest.files[].sha256 must match actual file bytes."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        zip_path, manifest = exported_pack
        
        # Unzipped dir is alongside zip
        unzipped = zip_path.with_suffix("")
        assert unzipped.is_dir(), "Unzipped pack not found"
        
        for entry in manifest["files"]:
            file_path = unzipped / entry["relpath"]
            assert file_path.exists(), f"Missing file: {entry['relpath']}"
            
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            assert actual_hash == entry["sha256"], f"Hash mismatch: {entry['relpath']}"
    
    def test_contents_flags_match_presence(self, exported_pack):
        """contents.* flags must match actual file presence."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        relpaths = {f["relpath"] for f in manifest["files"]}
        contents = manifest["contents"]
        
        # audio flag
        has_audio = any(p.startswith("audio/") for p in relpaths)
        assert contents["audio"] == has_audio, "audio flag mismatch"
        
        # spectra flag
        has_spectra = any(p.startswith("spectra/") for p in relpaths)
        assert contents["spectra"] == has_spectra, "spectra flag mismatch"
        
        # ods flag
        has_ods = any("ods_snapshot" in p for p in relpaths)
        assert contents["ods"] == has_ods, "ods flag mismatch"
        
        # wolf flag
        has_wolf = any("wolf_candidates" in p for p in relpaths)
        assert contents["wolf"] == has_wolf, "wolf flag mismatch"
        
        # plots flag
        has_plots = any(p.startswith("plots/") for p in relpaths)
        assert contents["plots"] == has_plots, "plots flag mismatch"
    
    def test_points_list_populated(self, exported_pack):
        """points[] array must list all exported point IDs."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        assert "points" in manifest
        assert isinstance(manifest["points"], list)
        assert len(manifest["points"]) > 0
        
        # Each point should have corresponding audio file
        for pid in manifest["points"]:
            expected = f"audio/points/{pid}.wav"
            relpaths = [f["relpath"] for f in manifest["files"]]
            assert expected in relpaths, f"Missing audio for point {pid}"
    
    def test_measurement_only_flag(self, exported_pack):
        """measurement_only must be True."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        assert manifest["measurement_only"] is True
        assert manifest["interpretation"] == "deferred"


class TestKindAssignments:
    """Test that file kinds are correctly assigned."""
    
    def test_audio_files_have_audio_raw_kind(self, exported_pack):
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        for f in manifest["files"]:
            if f["relpath"].startswith("audio/points/") and f["relpath"].endswith(".wav"):
                assert f["kind"] == "audio_raw", f"Wrong kind for {f['relpath']}"
    
    def test_spectrum_csv_kind(self, exported_pack):
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        for f in manifest["files"]:
            if f["relpath"].endswith("spectrum.csv"):
                assert f["kind"] == "spectrum_csv", f"Wrong kind for {f['relpath']}"
    
    def test_ods_uses_transfer_function_kind(self, exported_pack):
        """ODS files should use transfer_function kind."""
        if exported_pack is None:
            pytest.skip("No exported pack")
        _, manifest = exported_pack
        
        for f in manifest["files"]:
            if f["relpath"].startswith("ods/"):
                assert f["kind"] == "transfer_function", f"Wrong kind for {f['relpath']}"
