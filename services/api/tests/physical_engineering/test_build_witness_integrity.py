"""Digest, path, and cross-process integrity tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

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


def test_case_insensitive_filename_collision_fails(tmp_path: Path) -> None:
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
