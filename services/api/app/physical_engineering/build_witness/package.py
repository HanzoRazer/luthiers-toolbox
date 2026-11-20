"""Create, ingest, and verify an external witness package."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from app.physical_engineering.build_witness import templates
from app.physical_engineering.build_witness.findings import Finding, exit_code, finding
from app.physical_engineering.build_witness.ids import new_id
from app.physical_engineering.build_witness.paths import (
    MANIFEST_NAME,
    SUMS_NAME,
    PathPolicyError,
    evidence_files,
    media_type,
    normalize_relative,
    sha256_file,
)
from app.physical_engineering.build_witness.repository import LedgerError, WitnessRepository
from app.physical_engineering.build_witness.validate import load_package_docs, stored_states
from app.physical_engineering.build_witness.vocabulary import (
    BUILD_RESPONSE_OBSERVED,
    CALIBRATION_UNVERIFIED,
    CAPTURE_COMPLETE,
    CAPTURE_INCOMPLETE,
    INTEGRITY_VERIFIED,
    METHOD_REVIEW_PENDING,
)

_INSTRUMENT = __import__("re").compile(r"^[a-z][a-z0-9_]{0,63}$")


class PackageError(Exception):
    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def create_package(
    dest: Path,
    instrument_type: str,
    repository: WitnessRepository,
    *,
    clock: Callable[[], datetime] | None = None,
    factory: Callable[[], str] | None = None,
    supersedes: str | None = None,
) -> str:
    if not isinstance(instrument_type, str) or _INSTRUMENT.fullmatch(instrument_type) is None:
        raise PackageError("instrument type must be a lowercase token")
    dest = Path(dest)
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise PackageError("destination is not empty")
    if _is_inside(repository.root, dest) or _is_inside(dest, repository.root):
        raise PackageError("the ledger and the package must be different directories")
    witness_id = new_id("witness", clock, factory)
    build_id = new_id("build", clock, factory)
    session_id = new_id("session", clock, factory)
    for identifier in (witness_id, build_id, session_id):
        try:
            repository.burn(identifier)
        except LedgerError as exc:
            raise PackageError(str(exc)) from exc
    record = templates.build_record(witness_id, build_id, session_id, instrument_type)
    record["supersedes_witness_id"] = supersedes
    partial = dest.with_name(dest.name + ".partial")
    if partial.exists():
        raise PackageError("destination collision")
    created_partial = False
    try:
        if dest.exists():
            templates.write_blank_tree(dest, record, templates.test_protocol(session_id), templates.equipment())
        else:
            partial.mkdir()
            created_partial = True
            templates.write_blank_tree(partial, record, templates.test_protocol(session_id), templates.equipment())
            try:
                os.rename(partial, dest)
            except OSError as exc:
                shutil.rmtree(partial)
                created_partial = False
                raise PackageError("destination collision") from exc
            created_partial = False
    except FileExistsError as exc:
        if created_partial and partial.exists():
            shutil.rmtree(partial)
        raise PackageError("destination collision") from exc
    except Exception:
        if created_partial and partial.exists():
            shutil.rmtree(partial)
        raise
    try:
        repository.publish(witness_id, dest, supersedes)
    except LedgerError as exc:
        raise PackageError(str(exc)) from exc
    return witness_id


def ingest_package(package: Path, *, replace: bool = False) -> dict:
    package = Path(package)
    try:
        files = evidence_files(package)
    except PathPolicyError as exc:
        raise PackageError(exc.args[0], 2) from exc
    except OSError as exc:
        raise PackageError(str(exc), 3) from exc
    manifest_path = package / MANIFEST_NAME
    if manifest_path.exists() and not replace:
        raise PackageError("manifest already exists; pass replace to publish a new manifest")
    if replace and manifest_path.is_file():
        _refuse_locked_rewrite(package, files)
    docs, findings = load_package_docs(package)
    if any(item.severity == "authority" for item in findings):
        raise PackageError("prohibited authority claim", 4)
    payload = _manifest_payload(package, files, docs, findings)
    _publish_manifest(package, payload)
    return payload


def verify_package(package: Path) -> dict:
    package = Path(package)
    findings: list[Finding] = []
    docs: dict = {}
    files: list[str] = []
    try:
        if package.is_symlink():
            findings.append(finding("integrity", "symlink_directory", "package root is a symlink"))
        elif not package.is_dir():
            findings.append(finding("io", "not_a_directory", "package path is not a directory"))
        else:
            files = evidence_files(package)
            docs, loaded = load_package_docs(package)
            findings.extend(loaded)
            findings.extend(_check_manifest(package, files))
    except PathPolicyError as exc:
        findings.append(finding("integrity", exc.code, str(exc)))
    except OSError as exc:
        findings.append(finding("io", "os_error", str(exc)))
    code = exit_code(findings)
    integrity_ok = not any(item.severity in {"integrity", "io"} for item in findings)
    states = _output_states(code, integrity_ok, _calibration_unverified(docs))
    witness_id = None
    record = docs.get("build")
    if isinstance(record, dict):
        witness_id = record.get("witness_id")
    return {
        "cam_authorized": False,
        "capture_complete": code == 0,
        "exit_code": code,
        "findings": [item.as_dict() for item in findings],
        "integrity_ok": integrity_ok and code != 4,
        "machine_executable": False,
        "material_property_witness": False,
        "production_ready": False,
        "scientific_approval": False,
        "states": states,
        "witness_id": witness_id,
    }


def _authority_states() -> list[str]:
    return ["REFERENCE_COMPARISON_BLOCKED", "SCIENTIFIC_INTERPRETATION_PENDING"]


def _output_states(code: int, integrity_ok: bool, calibration_unverified: bool) -> list[str]:
    if code == 4:
        return _authority_states()
    states = [METHOD_REVIEW_PENDING, "REFERENCE_COMPARISON_BLOCKED", "SCIENTIFIC_INTERPRETATION_PENDING"]
    if code == 0:
        states.extend([CAPTURE_COMPLETE, BUILD_RESPONSE_OBSERVED, INTEGRITY_VERIFIED])
    elif integrity_ok and code == 1:
        states.extend([CAPTURE_INCOMPLETE, INTEGRITY_VERIFIED])
    else:
        states.append(CAPTURE_INCOMPLETE)
    if calibration_unverified and code in (0, 1):
        states.append(CALIBRATION_UNVERIFIED)
    return sorted(set(states))


def _calibration_unverified(docs: dict) -> bool:
    return bool(docs.get("calibration_unverified", True))


def _check_manifest(package: Path, files: list[str]) -> list[Finding]:
    path = package / MANIFEST_NAME
    sums = package / SUMS_NAME
    if not path.is_file() or not sums.is_file():
        return [finding("malformed", "missing_manifest", "manifest or SHA256SUMS is absent")]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [finding("malformed", "schema_version", "manifest is not JSON")]
    if not isinstance(manifest, dict):
        return [finding("malformed", "schema_version", "manifest is not an object")]
    return _compare_inventory(package, files, manifest, sums.read_text(encoding="utf-8"))


def _compare_inventory(package: Path, files: list[str], manifest: dict, sums_text: str) -> list[Finding]:
    findings: list[Finding] = []
    entries = manifest.get("files")
    if not isinstance(entries, list):
        return [finding("malformed", "schema_version", "manifest files must be a list")]
    listed: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            findings.append(finding("integrity", "digest_mismatch", "manifest entry is not an object"))
            continue
        try:
            relative = normalize_relative(entry.get("path"))
        except PathPolicyError as exc:
            findings.append(finding("integrity", exc.code, str(exc)))
            continue
        listed[relative] = entry
    if sorted(listed) != files:
        extra = sorted(set(files) - set(listed))
        missing = sorted(set(listed) - set(files))
        if extra:
            findings.append(finding("integrity", "unexpected_file", "unmanifested file: " + ", ".join(extra)))
        if missing:
            findings.append(finding("integrity", "missing_file", "manifest path missing: " + ", ".join(missing)))
    expected_lines = []
    for relative in files:
        entry = listed.get(relative)
        if entry is None:
            continue
        path = package / relative
        digest = sha256_file(path)
        size = path.stat().st_size
        expected_lines.append(f"{digest}  {relative}")
        if entry.get("sha256") != digest:
            findings.append(finding("integrity", "digest_mismatch", relative))
        if entry.get("byte_length") != size:
            findings.append(finding("integrity", "length_mismatch", relative))
        if entry.get("media_type") != media_type(relative):
            findings.append(finding("integrity", "digest_mismatch", "media type " + relative))
    sums_lines = [line for line in sums_text.splitlines() if line]
    if sums_lines != expected_lines:
        findings.append(finding("integrity", "digest_mismatch", "SHA256SUMS does not match the files"))
    return findings


def _manifest_payload(package: Path, files: list[str], docs: dict, findings: list[Finding]) -> dict:
    entries = []
    for relative in files:
        path = package / relative
        entries.append(
            {
                "byte_length": path.stat().st_size,
                "media_type": media_type(relative),
                "path": relative,
                "sha256": sha256_file(path),
            }
        )
    record = docs.get("build") if isinstance(docs.get("build"), dict) else {}
    complete = not any(item.severity == "malformed" for item in findings)
    return {
        "authority_boundary_id": "PEM-BUILD-WITNESS-001",
        "files": entries,
        "literature_reconciliation_status": "BLOCKED_BEFORE_PREFLIGHT",
        "schema_id": "pem_build_witness",
        "schema_version": "1",
        "states": stored_states(complete, _calibration_unverified(docs)),
        "witness_class": "BUILD_RESPONSE_WITNESS",
        "witness_id": record.get("witness_id"),
    }


def _publish_manifest(package: Path, payload: dict) -> None:
    body = json.dumps(payload, indent=2) + "\n"
    lines = [f"{item['sha256']}  {item['path']}" for item in payload["files"]]
    _atomic_write(package / SUMS_NAME, "\n".join(lines) + "\n")
    _atomic_write(package / MANIFEST_NAME, body)


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _locked(relative: str) -> bool:
    return not (relative.startswith("derived/") or relative.startswith("reports/"))


def _refuse_locked_rewrite(package: Path, files: list[str]) -> None:
    previous = json.loads((package / MANIFEST_NAME).read_text(encoding="utf-8"))
    old = {item["path"]: item["sha256"] for item in previous.get("files", []) if isinstance(item, dict)}
    for relative in files:
        if not _locked(relative):
            continue
        if relative not in old:
            raise PackageError("replacement cannot add locked evidence; create a new witness", 1)
        if sha256_file(package / relative) != old[relative]:
            raise PackageError("locked evidence bytes changed; the original package stays immutable", 2)
    for relative, digest in old.items():
        if not _locked(relative):
            continue
        if relative not in files or digest != sha256_file(package / relative):
            raise PackageError("locked evidence changed: " + relative, 2)


def _is_inside(parent: Path, child: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True
