"""Digest, path, and cross-process integrity tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.physical_engineering.build_witness.package import ingest_package, verify_package
from .pem_build_witness_fixture import write_valid

ROOT = Path(__file__).resolve().parents[4]


def _sealed(tmp_path: Path) -> Path:
    package = tmp_path / "pkg"
    write_valid(package)
    ingest_package(package)
    return package


def test_valid_minimal_package_verifies(tmp_path: Path) -> None:
    result = verify_package(_sealed(tmp_path))
    assert result["exit_code"] == 0
    assert result["integrity_ok"] is True
    assert result["capture_complete"] is True
    assert result["material_property_witness"] is False


def test_missing_required_file_fails(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    (package / "READ-ME-FIRST.txt").unlink()
    result = verify_package(package)
    assert result["exit_code"] == 2
    assert any(item["code"] == "missing_file" for item in result["findings"])


def test_one_byte_audio_mutation_fails(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    audio = package / "raw" / "audio" / "fixed-tap__trial-1.wav"
    blob = bytearray(audio.read_bytes())
    blob[-1] ^= 0x01
    audio.write_bytes(blob)
    assert verify_package(package)["exit_code"] == 2


def test_incorrect_length_and_digest_fail(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    manifest_path = package / "WITNESS-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["byte_length"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any(item["code"] == "length_mismatch" for item in verify_package(package)["findings"])
    manifest["files"][0]["byte_length"] = (package / manifest["files"][0]["path"]).stat().st_size
    manifest["files"][0]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = verify_package(package)
    assert result["exit_code"] == 2
    assert any(item["code"] == "digest_mismatch" for item in result["findings"])


def test_unexpected_file_fails(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    (package / "raw" / "audio" / "extra.wav").write_bytes(b"extra")
    result = verify_package(package)
    assert result["exit_code"] == 2
    assert any(item["code"] == "unexpected_file" for item in result["findings"])


def test_symlink_file_and_directory_fail(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    target = package / "raw" / "audio" / "fixed-tap__trial-1.wav"
    linked = package / "raw" / "audio" / "linked.wav"
    linked.symlink_to(target)
    assert verify_package(package)["exit_code"] == 2
    linked.unlink()
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(package)
    result = verify_package(alias)
    assert result["exit_code"] == 2
    assert any(item["code"] == "symlink_directory" for item in result["findings"])


def test_hard_linked_evidence_fails(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    source = package / "raw" / "audio" / "fixed-tap__trial-1.wav"
    os.link(source, package / "raw" / "audio" / "hard.wav")
    result = verify_package(package)
    assert result["exit_code"] == 2
    assert any(item["code"] == "hard_link" for item in result["findings"])


def test_absolute_and_traversal_paths_fail(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    manifest_path = package / "WITNESS-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"].append({"path": "/etc/passwd", "byte_length": 1, "sha256": "ab", "media_type": "text/plain"})
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    absolute = verify_package(package)
    assert absolute["exit_code"] == 2
    assert any(item["code"] == "unsafe_path" for item in absolute["findings"])
    manifest["files"][-1]["path"] = "../secret.txt"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any(item["code"] == "unsafe_path" for item in verify_package(package)["findings"])


def _case_sensitive(directory: Path) -> bool:
    probe = directory / "Case-Probe"
    probe.write_bytes(b"")
    try:
        return not (directory / "case-probe").exists()
    finally:
        probe.unlink()


def test_case_insensitive_filename_collision_fails(tmp_path: Path) -> None:
    if not _case_sensitive(tmp_path):
        # On NTFS/APFS defaults the second name opens the first file, so no
        # second entry exists to collide. The check is exercised on Linux CI.
        pytest.skip("filesystem is case-insensitive; a colliding pair cannot be created")
    package = _sealed(tmp_path)
    source = package / "raw" / "audio" / "fixed-tap__trial-1.wav"
    (package / "raw" / "audio" / "Fixed-Tap__Trial-1.wav").write_bytes(source.read_bytes())
    result = verify_package(package)
    assert result["exit_code"] == 2
    assert any(item["code"] == "case_collision" for item in result["findings"])


def test_reopen_in_a_new_process(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    first = verify_package(package)
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_build_witness.py"), "--package", str(package), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    second = json.loads(completed.stdout)
    assert second["exit_code"] == first["exit_code"]
    assert second["states"] == first["states"]
    assert second["witness_id"] == first["witness_id"]
    assert second["scientific_approval"] is False


def _edit_manifest(package: Path, change) -> None:
    path = package / "WITNESS-MANIFEST.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    change(manifest)
    path.write_text(json.dumps(manifest), encoding="utf-8")


def test_manifest_metadata_must_follow_its_schema(tmp_path: Path) -> None:
    changes = {
        "schema_version": lambda m: m.update(schema_version="999"),
        "schema_id": lambda m: m.update(schema_id="other"),
        "authority_boundary_id": lambda m: m.update(authority_boundary_id="OTHER"),
        "missing_class": lambda m: m.pop("witness_class"),
        "extra_key": lambda m: m.update(note="added later"),
    }
    for name, change in changes.items():
        package = tmp_path / name
        write_valid(package)
        ingest_package(package)
        _edit_manifest(package, change)
        result = verify_package(package)
        assert result["exit_code"] == 2, name
        assert result["integrity_ok"] is False, name
        assert "INTEGRITY_VERIFIED" not in result["states"], name
        assert any(item["code"] == "manifest_schema" for item in result["findings"]), name


def test_manifest_must_name_the_recorded_witness(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    _edit_manifest(package, lambda m: m.update(witness_id="pem_witness_1_" + "0" * 32))
    result = verify_package(package)
    assert result["exit_code"] == 2
    assert any(item["code"] == "identity_mismatch" for item in result["findings"])


def test_integrity_is_not_claimed_without_a_readable_manifest(tmp_path: Path) -> None:
    unsealed = tmp_path / "unsealed"
    write_valid(unsealed)
    result = verify_package(unsealed)
    assert result["exit_code"] == 1
    assert "INTEGRITY_VERIFIED" not in result["states"]
    corrupt = _sealed(tmp_path / "corrupt")
    (corrupt / "WITNESS-MANIFEST.json").write_text("not json", encoding="utf-8")
    result = verify_package(corrupt)
    assert "INTEGRITY_VERIFIED" not in result["states"]
    assert result["integrity_ok"] is False


def test_replacing_a_malformed_manifest_is_a_package_error(tmp_path: Path) -> None:
    from app.physical_engineering.build_witness.package import PackageError

    package = _sealed(tmp_path)
    _edit_manifest(package, lambda m: m["files"].append({"sha256": "0" * 64}))
    try:
        ingest_package(package, replace=True)
    except PackageError as exc:
        assert exc.code == 2
    else:
        raise AssertionError("a malformed prior manifest was replaced")
