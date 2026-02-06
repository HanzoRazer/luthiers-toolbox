#!/usr/bin/env python3
"""
Pytest wrapper for validate_viewer_pack_v1.py CLI.

Runs validator against both golden sessions; fails fast if validation breaks.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / "runs_phase2"
VALIDATOR = ROOT / "scripts" / "phase2" / "validate_viewer_pack_v1.py"
EXPORTER = ROOT / "scripts" / "phase2" / "export_viewer_pack_v1.py"


def golden_sessions():
    """Yield session directories that exist."""
    for name in ["session_20260101T234237Z", "session_20260101T235209Z"]:
        p = SESSIONS_DIR / name
        if p.is_dir():
            yield pytest.param(p, id=name)


@pytest.fixture(scope="module")
def exported_packs(tmp_path_factory) -> dict[str, Path]:
    """Export both sessions to temp dir, return {session_name: pack_dir}."""
    out_dir = tmp_path_factory.mktemp("viewer_packs")
    packs = {}

    for session_dir in SESSIONS_DIR.iterdir():
        if not session_dir.is_dir() or not session_dir.name.startswith("session_"):
            continue
        
        pack_name = f"{session_dir.name}__viewer_pack_v1"
        pack_dir = out_dir / pack_name
        
        result = subprocess.run(
            [sys.executable, str(EXPORTER), "--session-dir", str(session_dir), "--out", str(out_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.fail(f"Export failed for {session_dir.name}:\n{result.stderr}")
        
        # Find the actual pack dir (exporter creates viewer_pack_v1/)
        actual_pack = out_dir / "viewer_pack_v1"
        if actual_pack.is_dir():
            packs[session_dir.name] = actual_pack
            # Rename so next export doesn't overwrite
            renamed = out_dir / pack_name
            actual_pack.rename(renamed)
            packs[session_dir.name] = renamed

    return packs


class TestValidatorCLI:
    """Run the validator CLI against exported packs."""

    @pytest.mark.parametrize("session_dir", golden_sessions())
    def test_validator_passes_dir(self, session_dir: Path, exported_packs: dict[str, Path]):
        """Validator CLI returns 0 for directory pack."""
        pack_dir = exported_packs.get(session_dir.name)
        if pack_dir is None:
            pytest.skip(f"Pack not exported for {session_dir.name}")

        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--pack", str(pack_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Validator failed:\n{result.stderr}\n{result.stdout}"
        assert "OK" in result.stdout

    @pytest.mark.parametrize("session_dir", golden_sessions())
    def test_validator_passes_zip(self, session_dir: Path, exported_packs: dict[str, Path], tmp_path):
        """Validator CLI returns 0 for zip pack."""
        pack_dir = exported_packs.get(session_dir.name)
        if pack_dir is None:
            pytest.skip(f"Pack not exported for {session_dir.name}")

        # Re-export with --zip
        zip_out = tmp_path / "zips"
        zip_out.mkdir()
        
        # Find original session dir
        result = subprocess.run(
            [sys.executable, str(EXPORTER), "--session-dir", str(session_dir), "--out", str(zip_out), "--zip"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.fail(f"Zip export failed:\n{result.stderr}")

        # Find the zip file
        zips = list(zip_out.glob("*.zip"))
        assert len(zips) == 1, f"Expected 1 zip, got {zips}"
        
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--pack", str(zips[0])],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Validator failed on zip:\n{result.stderr}\n{result.stdout}"
        assert "OK" in result.stdout


class TestValidatorRejectsCorruption:
    """Validator should fail on corrupted packs."""

    def test_rejects_missing_manifest(self, tmp_path):
        """Validator returns non-zero when manifest.json is missing."""
        empty_dir = tmp_path / "empty_pack"
        empty_dir.mkdir()
        
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--pack", str(empty_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "FAIL" in result.stderr

    def test_rejects_invalid_schema_version(self, exported_packs: dict[str, Path], tmp_path):
        """Validator rejects manifest with wrong schema_version."""
        if not exported_packs:
            pytest.skip("No packs exported")
        
        # Copy first pack
        import shutil
        import json
        
        src = next(iter(exported_packs.values()))
        dst = tmp_path / "bad_version"
        shutil.copytree(src, dst)
        
        # Corrupt schema_version
        manifest_path = dst / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["schema_version"] = "v999"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--pack", str(dst)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "schema_version" in result.stderr

    def test_rejects_extra_manifest_key(self, exported_packs: dict[str, Path], tmp_path):
        """Validator rejects manifest with unexpected keys (additionalProperties: false)."""
        if not exported_packs:
            pytest.skip("No packs exported")
        
        import shutil
        import json
        
        src = next(iter(exported_packs.values()))
        dst = tmp_path / "extra_key"
        shutil.copytree(src, dst)
        
        manifest_path = dst / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["unexpected_field"] = "should_fail"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--pack", str(dst)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "unexpected" in result.stderr.lower()

    def test_rejects_sha256_mismatch(self, exported_packs: dict[str, Path], tmp_path):
        """Validator rejects when file sha256 doesn't match."""
        if not exported_packs:
            pytest.skip("No packs exported")
        
        import shutil
        
        src = next(iter(exported_packs.values()))
        dst = tmp_path / "bad_sha"
        shutil.copytree(src, dst)
        
        # Corrupt a file
        readme = dst / "README.txt"
        if readme.exists():
            readme.write_text("corrupted content!")
        
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--pack", str(dst)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "sha256 mismatch" in result.stderr or "FAIL" in result.stderr
