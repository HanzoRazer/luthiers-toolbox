"""Ingest and verify an external witness package.

The evidence seal (WITNESS-MANIFEST.json + SHA256SUMS) covers the root
records and ``raw/``. Ingest anchors the manifest digest in the ledger before
writing it; a witness is never resealed with different bytes. Generated
products (``derived/observations.json``, ``reports/WITNESS-REPORT.md``) sit
outside the seal; see layout.py and derived_check.py.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from app.physical_engineering.build_witness.create import (  # noqa: F401 - re-export
    create_package,
    reservation_path,
)
from app.physical_engineering.build_witness.derived_check import check_derived
from app.physical_engineering.build_witness.findings import (
    Finding,
    PackageError,
    exit_code,
    finding,
)
from app.physical_engineering.build_witness.layout import misplaced_files, sealed_files
from app.physical_engineering.build_witness.paths import (
    MANIFEST_NAME,
    SUMS_NAME,
    PathPolicyError,
    evidence_files,
    media_type,
    normalize_relative,
    sha256_file,
)
from app.physical_engineering.build_witness.repository import (
    LedgerError,
    WitnessRepository,
)
from app.physical_engineering.build_witness.schema_check import (
    WITNESS_MANIFEST,
    schema_findings,
)
from app.physical_engineering.build_witness.validate import (
    load_package_docs,
    stored_states,
)
from app.physical_engineering.build_witness.vocabulary import (
    BUILD_RESPONSE_OBSERVED,
    CALIBRATION_UNVERIFIED,
    CAPTURE_COMPLETE,
    CAPTURE_INCOMPLETE,
    INTEGRITY_VERIFIED,
    METHOD_REVIEW_PENDING,
)

__all__ = ["PackageError", "create_package", "default_ledger", "ingest_package", "verify_package"]

LEDGER_DIR_NAME = "pem-witness-ledger"


def default_ledger(package: Path) -> WitnessRepository:
    """The ledger ``create`` uses by default: a sibling of the package."""
    return WitnessRepository(Path(package).parent / LEDGER_DIR_NAME)


def ingest_package(package: Path, *, replace: bool = False, repository: WitnessRepository | None = None) -> dict:
    """Seal the evidence once.

    ``replace`` re-runs ingest on an already sealed package; it succeeds only
    if the manifest it would write is byte-identical to the one sealed. The
    first manifest digest is anchored in the ledger before it is written.
    """
    package = Path(package)
    repository = repository or default_ledger(package)
    try:
        files = evidence_files(package)
    except PathPolicyError as exc:
        raise PackageError(exc.args[0], 2) from exc
    except OSError as exc:
        raise PackageError(str(exc), 3) from exc
    misplaced = misplaced_files(files)
    if misplaced:
        raise PackageError("files outside the evidence layout: " + ", ".join(misplaced), 2)
    manifest_path = package / MANIFEST_NAME
    if manifest_path.exists() and not replace:
        raise PackageError("manifest already exists; the evidence is sealed")
    docs, findings = load_package_docs(package)
    if any(item.severity == "authority" for item in findings):
        raise PackageError("prohibited authority claim", 4)
    payload = _manifest_payload(package, sealed_files(files), docs, findings)
    problems = schema_findings(WITNESS_MANIFEST, payload, MANIFEST_NAME)
    if problems:
        raise PackageError("refusing to write a manifest that breaks its schema: " + problems[0].message)
    body = json.dumps(payload, indent=2) + "\n"
    if manifest_path.exists() and manifest_path.read_bytes() != body.encode("utf-8"):
        raise PackageError(
            "the evidence is sealed and would seal differently now; the original package stays immutable. "
            "A correction needs a new witness that supersedes this one",
            2,
        )
    try:
        repository.seal(payload["witness_id"], hashlib.sha256(body.encode("utf-8")).hexdigest())
    except LedgerError as exc:
        raise PackageError(str(exc), 2) from exc
    _publish_manifest(package, payload, body)
    return payload


def verify_package(package: Path, *, repository: WitnessRepository | None = None) -> dict:
    package = Path(package)
    findings: list[Finding] = []
    docs: dict = {}
    manifest_checked = False
    try:
        if package.is_symlink():
            findings.append(finding("integrity", "symlink_directory", "package root is a symlink"))
        elif not package.is_dir():
            findings.append(finding("io", "not_a_directory", "package path is not a directory"))
        else:
            manifest_checked = _verify_contents(package, repository or default_ledger(package), docs, findings)
    except PathPolicyError as exc:
        findings.append(finding("integrity", exc.code, str(exc)))
    except OSError as exc:
        findings.append(finding("io", "os_error", str(exc)))
    except Exception as exc:  # noqa: BLE001 - a verifier must not crash on package contents
        # Fail closed: an input the checks did not anticipate is "could not
        # be checked" (exit 3), never a pass and never a traceback.
        findings.append(finding("io", "verifier_error", f"{type(exc).__name__}: {exc}"))
    code = exit_code(findings)
    # INTEGRITY_VERIFIED requires a manifest that was present, well formed,
    # bound to this record and the ledger, and matched every file.
    integrity_ok = manifest_checked and not any(item.severity in {"integrity", "io"} for item in findings)
    states = _output_states(code, integrity_ok, _calibration_unverified(docs))
    record = docs.get("build")
    witness_id = record.get("witness_id") if isinstance(record, dict) else None
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


def _verify_contents(package: Path, repository: WitnessRepository, docs: dict, findings: list[Finding]) -> bool:
    files = evidence_files(package)
    for relative in misplaced_files(files):
        findings.append(finding("integrity", "misplaced_file", "file outside the evidence layout: " + relative))
    loaded_docs, loaded = load_package_docs(package)
    docs.update(loaded_docs)
    findings.extend(loaded)
    manifest_findings, listed = _check_manifest(package, sealed_files(files), docs)
    findings.extend(manifest_findings)
    manifest_checked = not manifest_findings
    if manifest_checked:
        findings.extend(_check_references(docs.get("evidence_refs") or set(), listed))
        findings.extend(_check_ledger(package, repository, docs))
    evidence_ok = manifest_checked and not any(item.severity != "warning" for item in findings)
    _, derived_findings = check_derived(package, docs, listed, evidence_ok)
    findings.extend(derived_findings)
    return manifest_checked


def trusted_derived(package: Path, docs: dict) -> dict | None:
    """The derived document after every derived check, or PackageError."""
    _, listed = _check_manifest(package, sealed_files(evidence_files(package)), docs)
    payload, findings = check_derived(package, docs, listed, evidence_ok=True)
    if findings:
        raise PackageError(findings[0].message, 2)
    return payload


def _check_references(refs: set[str], listed: dict[str, dict]) -> list[Finding]:
    """Every evidence file a record points to must be sealed by name."""
    found = []
    for ref in sorted(refs):
        try:
            relative = normalize_relative(ref)
        except PathPolicyError:
            continue  # reported by the record checks
        if relative not in listed:
            found.append(finding("integrity", "unsealed_reference", "referenced evidence is not in the manifest: " + ref))
    return found


def _check_ledger(package: Path, repository: WitnessRepository, docs: dict) -> list[Finding]:
    witness_id = (docs.get("build") or {}).get("witness_id")
    if not repository.root.is_dir():
        return [finding("warning", "ledger_unavailable", f"no ledger at {repository.root}; the first seal was not compared")]
    if not isinstance(witness_id, str):
        return []
    anchored = repository.sealed_digest(witness_id)
    if anchored is None:
        return [finding("integrity", "seal_not_anchored", "the ledger has no seal for this witness")]
    if anchored != sha256_file(package / MANIFEST_NAME):
        return [finding("integrity", "seal_mismatch", "the manifest is not the one first sealed for this witness")]
    return []


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


def _check_manifest(package: Path, files: list[str], docs: dict) -> tuple[list[Finding], dict[str, dict]]:
    path = package / MANIFEST_NAME
    sums = package / SUMS_NAME
    if not path.is_file() or not sums.is_file():
        return [finding("malformed", "missing_manifest", "manifest or SHA256SUMS is absent")], {}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        sums_text = sums.read_text(encoding="utf-8")
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
        return [finding("malformed", "schema_version", "manifest is not UTF-8 JSON")], {}
    if not isinstance(manifest, dict):
        return [finding("malformed", "schema_version", "manifest is not an object")], {}
    findings = _check_manifest_metadata(manifest, docs)
    inventory, listed = _compare_inventory(package, files, manifest, sums_text)
    findings.extend(inventory)
    return findings, listed


def _check_manifest_metadata(manifest: dict, docs: dict) -> list[Finding]:
    """Apply the published manifest schema and bind the manifest to the record.

    A manifest that does not follow its own schema, or names a different
    witness than BUILD-RECORD.json, does not establish integrity.
    """
    findings = schema_findings(WITNESS_MANIFEST, manifest, MANIFEST_NAME, severity="integrity", code="manifest_schema")
    record = docs.get("build") if isinstance(docs.get("build"), dict) else {}
    if manifest.get("witness_id") != record.get("witness_id"):
        findings.append(finding("integrity", "identity_mismatch", "manifest witness_id does not match BUILD-RECORD.json"))
    return findings


def _compare_inventory(package: Path, files: list[str], manifest: dict, sums_text: str) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    entries = manifest.get("files")
    if not isinstance(entries, list):
        return [finding("malformed", "schema_version", "manifest files must be a list")], {}
    listed: dict[str, dict] = {}
    folded: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            findings.append(finding("integrity", "digest_mismatch", "manifest entry is not an object"))
            continue
        try:
            relative = normalize_relative(entry.get("path"))
        except PathPolicyError as exc:
            findings.append(finding("integrity", exc.code, str(exc)))
            continue
        if relative.casefold() in folded:
            # A later entry must not silently replace an earlier one.
            findings.append(finding("integrity", "duplicate_entry", "manifest lists a path twice: " + relative))
            continue
        folded.add(relative.casefold())
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
    return findings, listed


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


def _publish_manifest(package: Path, payload: dict, body: str) -> None:
    lines = [f"{item['sha256']}  {item['path']}" for item in payload["files"]]
    _atomic_write(package / SUMS_NAME, "\n".join(lines) + "\n")
    _atomic_write(package / MANIFEST_NAME, body)


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(text.encode("utf-8"))
    os.replace(temporary, path)
