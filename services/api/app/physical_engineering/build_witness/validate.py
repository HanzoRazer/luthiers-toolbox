"""Record, environment, trial, and authority checks.

Malformed findings mean the capture is incomplete or the contract was not
followed. Authority findings are a separate exit. Nothing here converts a
unit or fills in a missing room condition.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image

from app.physical_engineering.build_witness.findings import Finding, finding
from app.physical_engineering.build_witness.ids import is_identifier
from app.physical_engineering.build_witness.paths import MANIFEST_NAME
from app.physical_engineering.build_witness.templates import ENVIRONMENT_FIELDS, MEASUREMENT_FIELDS
from app.physical_engineering.build_witness.validate_capture import (
    _calibration_unverified,
    _check_audio_rows,
    _check_environment,
    _check_equipment,
    _check_measurements,
    _check_trial_groups,
)
from app.physical_engineering.build_witness.validate_support import DECIMAL_TEXT as _DECIMAL
from app.physical_engineering.build_witness.validate_support import parse_time as _parse_time
from app.physical_engineering.build_witness.validate_support import path_exists as _exists
from app.physical_engineering.build_witness.vocabulary import (
    AUTHORITY_BOUNDARY_ID,
    BUILD_RESPONSE_OBSERVED,
    CALIBRATION_UNVERIFIED,
    CAPTURE_COMPLETE,
    CAPTURE_INCOMPLETE,
    IDENTITY_STATUSES,
    INTEGRITY_VERIFIED,
    LITERATURE_STATUS,
    MATERIAL_IDENTITY_STATEMENT,
    METHOD_REVIEW_PENDING,
    PROHIBITED_KEYS,
    PROHIBITED_STATES,
    REFERENCE_COMPARISON_BLOCKED,
    SCIENTIFIC_INTERPRETATION_PENDING,
    WITNESS_CLASS,
)


def stored_states(complete: bool, calibration_unverified: bool) -> list[str]:
    states = [
        CAPTURE_COMPLETE if complete else CAPTURE_INCOMPLETE,
        METHOD_REVIEW_PENDING,
        REFERENCE_COMPARISON_BLOCKED,
        SCIENTIFIC_INTERPRETATION_PENDING,
    ]
    if calibration_unverified:
        states.append(CALIBRATION_UNVERIFIED)
    if complete:
        states.append(BUILD_RESPONSE_OBSERVED)
    return sorted(states)


def load_package_docs(package: Path) -> tuple[dict, list[Finding]]:
    findings: list[Finding] = []
    build = _read_json(package / "BUILD-RECORD.json", findings)
    protocol = _read_json(package / "TEST-PROTOCOL.json", findings)
    equipment = _read_json(package / "EQUIPMENT.json", findings)
    environment = _read_csv(package / "ENVIRONMENT.csv", ENVIRONMENT_FIELDS, findings)
    measurements = _read_csv(package / "MEASUREMENTS.csv", MEASUREMENT_FIELDS, findings)
    manifest = _read_optional_json(package / MANIFEST_NAME, findings)
    for document in (build, protocol, equipment, manifest):
        if isinstance(document, dict):
            _walk_authority(document, findings)
    docs = {
        "build": build if isinstance(build, dict) else {},
        "protocol": protocol if isinstance(protocol, dict) else {},
        "equipment": equipment if isinstance(equipment, dict) else {},
        "environment": environment,
        "measurements": measurements,
        "manifest": manifest if isinstance(manifest, dict) else {},
    }
    if isinstance(build, dict):
        _check_build(package, build, findings)
    if isinstance(protocol, dict):
        _check_protocol(package, protocol, measurements, findings)
    if isinstance(build, dict):
        _check_identity(build, docs["protocol"], measurements, findings)
    if isinstance(equipment, dict):
        _check_equipment(equipment, docs["build"], findings)
    _check_environment(environment, findings)
    _check_measurements(package, measurements, findings)
    docs["calibration_unverified"] = _calibration_unverified(docs)
    if isinstance(manifest, dict) and manifest:
        complete = not any(item.severity == "malformed" for item in findings)
        expected = stored_states(complete, docs["calibration_unverified"])
        if manifest.get("states") != expected:
            findings.append(finding("malformed", "state_mismatch", "manifest states do not match the records"))
    return docs, findings


def _read_json(path: Path, findings: list[Finding]) -> dict | None:
    if not path.is_file():
        findings.append(finding("malformed", "missing_policy", path.name + " is absent"))
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        findings.append(finding("malformed", "schema_version", path.name + " is not UTF-8 JSON"))
        return None
    if not isinstance(payload, dict):
        findings.append(finding("malformed", "schema_version", path.name + " is not an object"))
        return None
    if payload.get("schema_version") != "1":
        findings.append(finding("malformed", "schema_version", path.name + " schema_version is not 1"))
    return payload


def _read_optional_json(path: Path, findings: list[Finding]) -> dict | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        findings.append(finding("malformed", "schema_version", path.name + " is not UTF-8 JSON"))
        return None
    return payload if isinstance(payload, dict) else None


def _read_csv(path: Path, fields: tuple[str, ...], findings: list[Finding]) -> list[dict[str, str]]:
    """Rows of a CSV record, or no rows if the document breaks its contract.

    Policy: UTF-8, strict quoting, a header equal to ``fields`` in order, and
    every data row exactly as wide as the header. Completely empty lines are
    skipped. Any other deviation rejects the whole document, so later checks
    never evaluate a repaired copy that differs from the submitted bytes.
    """
    if not path.is_file():
        findings.append(finding("malformed", "missing_policy", path.name + " is absent"))
        return []
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            table = list(csv.reader(handle, strict=True))
    except OSError:
        findings.append(finding("io", "os_error", path.name))
        return []
    except UnicodeDecodeError:
        findings.append(finding("malformed", "csv_malformed", path.name + " is not UTF-8"))
        return []
    except csv.Error as exc:
        findings.append(finding("malformed", "csv_malformed", f"{path.name}: {exc}"))
        return []
    if not table:
        findings.append(finding("malformed", "csv_header", path.name + " has no header"))
        return []
    header, body = table[0], table[1:]
    if tuple(header) != fields:
        findings.append(finding("malformed", "csv_header", f"{path.name}: {_header_problem(header, fields)}"))
        return []
    bad_lines = [index for index, row in enumerate(body, start=2) if row and len(row) != len(header)]
    if bad_lines:
        listed = ", ".join(str(index) for index in bad_lines[:10])
        findings.append(
            finding("malformed", "csv_row_width", f"{path.name}: rows {listed} do not have {len(header)} fields")
        )
        return []
    return [dict(zip(header, row)) for row in body if row]


def _header_problem(header: list[str], fields: tuple[str, ...]) -> str:
    blank = [index + 1 for index, name in enumerate(header) if not name.strip()]
    duplicated = sorted({name for name in header if name and header.count(name) > 1})
    missing = [name for name in fields if name not in header]
    unknown = [name for name in header if name and name not in fields]
    parts = []
    if blank:
        parts.append("blank column " + ", ".join(str(index) for index in blank))
    if duplicated:
        parts.append("duplicated " + ", ".join(duplicated))
    if missing:
        parts.append("missing " + ", ".join(missing))
    if unknown:
        parts.append("unknown " + ", ".join(unknown))
    return "; ".join(parts) or "columns are out of order"


def _walk_authority(value: object, findings: list[Finding]) -> None:
    if isinstance(value, dict):
        _walk_dict(value, findings)
    elif isinstance(value, list):
        for item in value:
            _walk_authority(item, findings)


def _walk_dict(value: dict, findings: list[Finding]) -> None:
    for key, item in value.items():
        if isinstance(key, str) and key in PROHIBITED_KEYS:
            findings.append(finding("authority", "prohibited_key", key))
        if key == "witness_class":
            _witness_class(item, findings)
        if key == "literature_reconciliation_status" and item != LITERATURE_STATUS:
            findings.append(finding("authority", "prohibited_literature_status", "literature comparison is blocked"))
        if key == "states" and isinstance(item, list):
            _states(item, findings)
        _walk_authority(item, findings)


def _witness_class(item: object, findings: list[Finding]) -> None:
    if item == WITNESS_CLASS:
        return
    if isinstance(item, str) and item in PROHIBITED_STATES:
        findings.append(finding("authority", "prohibited_witness_class", str(item)))
        return
    findings.append(finding("malformed", "schema_version", "witness class is not BUILD_RESPONSE_WITNESS"))


def _states(items: list, findings: list[Finding]) -> None:
    for item in items:
        if not isinstance(item, str):
            findings.append(finding("malformed", "schema_version", "state is not a string"))
        elif item in PROHIBITED_STATES:
            findings.append(finding("authority", "prohibited_state", str(item)))
        elif item == INTEGRITY_VERIFIED:
            findings.append(finding("malformed", "self_certified_integrity", "integrity cannot be self-certified"))
        elif item not in {
            BUILD_RESPONSE_OBSERVED,
            CALIBRATION_UNVERIFIED,
            CAPTURE_COMPLETE,
            CAPTURE_INCOMPLETE,
            METHOD_REVIEW_PENDING,
            REFERENCE_COMPARISON_BLOCKED,
            SCIENTIFIC_INTERPRETATION_PENDING,
        }:
            findings.append(finding("malformed", "schema_version", "unknown state"))


def _check_build(package: Path, record: dict, findings: list[Finding]) -> None:
    if record.get("schema_id") != "pem_build_record":
        findings.append(finding("malformed", "schema_version", "build record schema_id"))
    if record.get("authority_boundary_id") != AUTHORITY_BOUNDARY_ID:
        findings.append(finding("malformed", "missing_policy", "authority boundary id"))
    if record.get("material_identity_statement") != MATERIAL_IDENTITY_STATEMENT:
        findings.append(finding("malformed", "missing_policy", "material identity statement"))
    if not isinstance(record.get("record_kind"), str) or record["record_kind"] not in {"PHYSICAL_CAPTURE", "SYNTHETIC_FIXTURE"}:
        findings.append(finding("malformed", "schema_version", "record_kind"))
    for key in ("witness_id", "build_id", "session_id"):
        if not is_identifier(record.get(key)):
            findings.append(finding("malformed", "schema_version", key))
    _optional_text(record, "builder", "builder_unknown_reason", findings)
    _optional_text(record, "test_location", "test_location_unknown_reason", findings)
    _scale(record, findings)
    _role(record, findings)
    _materials(package, record, findings)
    _attestation(record, findings)
    _photos(package, record, findings)
    for key in ("body_style", "tuning", "build_completion_state", "specimen_role", "test_date"):
        if not isinstance(record.get(key), str) or not record.get(key):
            findings.append(finding("malformed", "missing_policy", key))
    if isinstance(record.get("test_date"), str):
        _parse_time(record["test_date"], findings)
    strings = record.get("strings")
    if not isinstance(strings, dict):
        findings.append(finding("malformed", "missing_policy", "strings"))
    elif not strings.get("condition") and not strings.get("unknown_reason"):
        findings.append(finding("malformed", "missing_policy", "strings"))


def _optional_text(record: dict, key: str, reason_key: str, findings: list[Finding]) -> None:
    if record.get(key):
        return
    if not record.get(reason_key):
        findings.append(finding("malformed", "missing_policy", key))


def _scale(record: dict, findings: list[Finding]) -> None:
    value = record.get("scale_length_mm")
    if value is None:
        if not record.get("scale_length_unknown_reason"):
            findings.append(finding("malformed", "missing_dimension", "scale length"))
        else:
            findings.append(finding("malformed", "missing_dimension", "scale length"))
        return
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        findings.append(finding("malformed", "unit_rejected", "scale_length_mm"))


def _role(record: dict, findings: list[Finding]) -> None:
    if (
        record.get("build_completion_state") == "completed_instrument"
        and record.get("specimen_role") == "controlled_material_coupon"
    ):
        findings.append(finding("malformed", "coupon_conflict", "a completed instrument is not a material coupon"))


def _materials(package: Path, record: dict, findings: list[Finding]) -> None:
    for key in ("top", "back_side", "neck"):
        material = record.get(key)
        if not isinstance(material, dict):
            findings.append(finding("malformed", "missing_policy", key))
            continue
        _one_material(package, material, findings)


def _one_material(package: Path, material: dict, findings: list[Finding]) -> None:
    status = material.get("identity_status")
    if not isinstance(status, str) or status not in IDENTITY_STATUSES:
        findings.append(finding("malformed", "schema_version", "identity_status"))
        return
    if status == "UNDECLARED" and not material.get("unknown_reason"):
        findings.append(finding("malformed", "missing_policy", "unknown material reason"))
    if status != "VERIFIED":
        return
    if material.get("identity_basis") != "independent_identification" or not material.get("botanical_name"):
        findings.append(finding("authority", "prohibited_witness_class", "botanical identity is not verified"))
        return
    ref = material.get("evidence_ref")
    if not isinstance(ref, str) or not _exists(package, ref):
        findings.append(finding("authority", "prohibited_witness_class", "verified identity needs an evidence file"))


def _attestation(record: dict, findings: list[Finding]) -> None:
    attestation = record.get("operator_attestation")
    if not isinstance(attestation, dict):
        findings.append(finding("malformed", "missing_attestation", "operator attestation is absent"))
        return
    for key in ("operator", "attested_at", "statement"):
        if not isinstance(attestation.get(key), str) or not attestation.get(key):
            findings.append(finding("malformed", "missing_attestation", key))
    if isinstance(attestation.get("attested_at"), str):
        _parse_time(attestation["attested_at"], findings)


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _photos(package: Path, record: dict, findings: list[Finding]) -> None:
    refs = record.get("photograph_refs")
    if not isinstance(refs, list) or len(refs) < 2:
        findings.append(finding("malformed", "missing_photograph", "build and placement photographs are required"))
        return
    seen: set[str] = set()
    for ref in refs:
        if not isinstance(ref, str) or not ref.endswith(".png") or not _exists(package, ref):
            findings.append(finding("malformed", "missing_photograph", "photograph missing"))
            continue
        if ref in seen:
            findings.append(finding("malformed", "missing_photograph", "photograph listed twice: " + ref))
            continue
        seen.add(ref)
        if not _is_png(package / ref):
            findings.append(finding("malformed", "invalid_photograph", "not a PNG image: " + ref))


def _is_png(path: Path) -> bool:
    """A complete PNG that decodes: every chunk CRC, IHDR through IEND, and
    all pixel data. A signature and header alone are not an image.

    This checks the file is an image, not what it shows. Content review of a
    photograph is an operator task.
    """
    with path.open("rb") as handle:
        if handle.read(8) != _PNG_SIGNATURE:
            return False
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                return False
            image.verify()  # chunk structure and CRCs through IEND
        with Image.open(path) as image:
            image.load()  # decompress every scanline
            width, height = image.size
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        return False
    return width > 0 and height > 0


def _check_identity(
    build: dict,
    protocol: dict,
    measurements: list[dict[str, str]],
    findings: list[Finding],
) -> None:
    """Bind the records that carry identifiers to this build.

    Enforced: TEST-PROTOCOL.json ``session_id``, and ``witness_id`` plus
    ``session_id`` on every MEASUREMENTS.csv row (required, nonblank, equal to
    BUILD-RECORD.json). The manifest's ``witness_id`` is checked in package.py.
    EQUIPMENT.json and ENVIRONMENT.csv carry no identifiers in schema version
    1; they are bound only by sitting in a package whose manifest digests them.
    """
    witness_id = build.get("witness_id")
    session_id = build.get("session_id")
    if protocol and protocol.get("session_id") != session_id:
        findings.append(finding("malformed", "identity_mismatch", "TEST-PROTOCOL.json session_id does not match the build record"))
    for line, row in enumerate(measurements, start=2):
        if not row.get("witness_id") or not row.get("session_id"):
            findings.append(
                finding("malformed", "identity_missing", f"MEASUREMENTS.csv row {line} has no witness_id or session_id")
            )
            return
        if row["witness_id"] != witness_id or row["session_id"] != session_id:
            findings.append(
                finding("malformed", "identity_mismatch", f"MEASUREMENTS.csv row {line} names a different witness or session")
            )
            return


def _check_protocol(package: Path, protocol: dict, measurements: list[dict[str, str]], findings: list[Finding]) -> None:
    if protocol.get("schema_id") != "pem_test_protocol":
        findings.append(finding("malformed", "schema_version", "protocol schema_id"))
    if protocol.get("preprocessing") != "none":
        findings.append(finding("malformed", "schema_version", "preprocessing must be none"))
    if not isinstance(protocol.get("trial_count"), int) or protocol.get("trial_count") < 3:
        findings.append(finding("malformed", "trial_count", "trial_count must be at least 3"))
    for key in (
        "excitation_method",
        "excitation_position",
        "microphone_position",
        "objective",
        "operator",
        "protocol_id",
        "string_state",
        "support_condition",
        "tuning",
    ):
        if not isinstance(protocol.get(key), str) or not protocol.get(key):
            findings.append(finding("malformed", "missing_policy", key))
    _check_trial_groups(package, protocol, findings)
    _check_audio_rows(protocol, measurements, findings)


