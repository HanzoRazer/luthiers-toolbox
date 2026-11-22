"""The published schemas are applied when a package is verified.

Each violation must come back as a finding that names the document and the
location, never as a traceback or a pass.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.physical_engineering.build_witness import templates
from app.physical_engineering.build_witness.package import (
    PackageError,
    ingest_package,
    verify_package,
)
from app.physical_engineering.build_witness.report import render_package
from app.physical_engineering.build_witness.schema_check import (
    BUILD_RECORD,
    MEASUREMENT,
    SCHEMA_DIR,
    TEST_PROTOCOL,
    schema_findings,
)
from jsonschema import Draft202012Validator

from .pem_build_witness_fixture import write_valid

WITNESS = "pem_witness_1_" + "a" * 32
BUILD = "pem_build_1_" + "b" * 32
SESSION = "pem_session_1_" + "c" * 32


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _verify_after(package: Path) -> dict:
    """Re-seal the edited package so only the record check can fail."""
    ingest_package(package, replace=True)
    return verify_package(package)


def _schema_messages(result: dict) -> list[str]:
    return [item["message"] for item in result["findings"] if item["code"] == "record_schema"]


def _no_crash(result: dict) -> None:
    assert not any(item["severity"] == "io" for item in result["findings"]), result["findings"]


def test_every_schema_is_valid_draft_2020_12() -> None:
    names = sorted(path.name for path in SCHEMA_DIR.glob("*.schema.json"))
    assert len(names) == 4
    for name in names:
        Draft202012Validator.check_schema(_load(SCHEMA_DIR / name))


def test_valid_fixture_and_blank_templates_satisfy_the_schemas(tmp_path: Path) -> None:
    package = tmp_path / "valid"
    write_valid(package)
    ingest_package(package)
    result = verify_package(package)
    assert result["exit_code"] == 0
    assert result["findings"] == []
    blank = templates.build_record(WITNESS, BUILD, SESSION, "acoustic_guitar")
    assert schema_findings(BUILD_RECORD, blank, "BUILD-RECORD.json") == []
    assert schema_findings(TEST_PROTOCOL, templates.test_protocol(SESSION), "TEST-PROTOCOL.json") == []


@pytest.mark.parametrize(
    ("edit", "pointer", "fragment"),
    [
        (lambda r: r.update(unlisted_field="x"), "BUILD-RECORD.json /:", "Additional properties"),
        (lambda r: r.pop("body_style"), "BUILD-RECORD.json /:", "'body_style' is a required property"),
        (lambda r: r.update(scale_length_mm=648), "BUILD-RECORD.json /scale_length_mm:", "is not of type"),
        (lambda r: r["top"].update(grain="tight"), "BUILD-RECORD.json /top:", "Additional properties"),
        (lambda r: r["strings"].pop("gauges"), "BUILD-RECORD.json /strings:", "'gauges' is a required property"),
        (lambda r: r.update(photograph_refs="raw/images/build-id.png"), "BUILD-RECORD.json /photograph_refs:", "is not of type"),
        (lambda r: r.update(supersedes_witness_id="someone-else"), "BUILD-RECORD.json /supersedes_witness_id:", ""),
    ],
    ids=["unknown", "missing", "wrong-type", "nested-unknown", "nested-missing", "list-as-string", "bad-id"],
)
def test_build_record_schema_violations_are_located_findings(tmp_path: Path, edit, pointer: str, fragment: str) -> None:
    package = tmp_path / "record"
    write_valid(package)
    record = _load(package / "BUILD-RECORD.json")
    edit(record)
    _save(package / "BUILD-RECORD.json", record)
    result = _verify_after(package)
    _no_crash(result)
    assert result["exit_code"] == 1
    messages = _schema_messages(result)
    assert any(message.startswith(pointer) and fragment in message for message in messages), messages


@pytest.mark.parametrize(
    ("edit", "pointer", "fragment"),
    [
        (lambda p: p.update(unlisted_field="x"), "TEST-PROTOCOL.json /:", "Additional properties"),
        (lambda p: p.pop("limitations"), "TEST-PROTOCOL.json /:", "'limitations' is a required property"),
        (lambda p: p.update(trial_count="3"), "TEST-PROTOCOL.json /trial_count:", "is not of type"),
        (lambda p: p.update(bit_depth=12), "TEST-PROTOCOL.json /bit_depth:", "is not one of"),
        (lambda p: p["trials"][0].update(gain_db="6"), "TEST-PROTOCOL.json /trials/0:", "Additional properties"),
        (lambda p: p["trials"][1].update(trial_index="2"), "TEST-PROTOCOL.json /trials/1/trial_index:", "is not of type"),
        (lambda p: p.update(allowed_derivations=["moe"]), "TEST-PROTOCOL.json /allowed_derivations/0:", "is not one of"),
    ],
    ids=["unknown", "missing", "wrong-type", "bad-depth", "trial-unknown", "trial-wrong-type", "derivation"],
)
def test_protocol_schema_violations_are_located_findings(tmp_path: Path, edit, pointer: str, fragment: str) -> None:
    package = tmp_path / "protocol"
    write_valid(package)
    protocol = _load(package / "TEST-PROTOCOL.json")
    edit(protocol)
    _save(package / "TEST-PROTOCOL.json", protocol)
    result = _verify_after(package)
    _no_crash(result)
    assert result["exit_code"] == 1
    messages = _schema_messages(result)
    assert any(message.startswith(pointer) and fragment in message for message in messages), messages


def _edit_measurement_row(package: Path, line: int, column: str, value: str) -> None:
    path = package / "MEASUREMENTS.csv"
    rows = path.read_text(encoding="utf-8").splitlines()
    header = rows[0].split(",")
    cells = rows[line - 1].split(",")
    cells[header.index(column)] = value
    rows[line - 1] = ",".join(cells)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("column", "value", "pointer", "fragment"),
    [
        ("observation_id", "obs-1", "MEASUREMENTS.csv row 3 /observation_id:", "does not match"),
        ("estimated", "yes", "MEASUREMENTS.csv row 3 /estimated:", "is not one of"),
        ("measurement_source", "ESTIMATE", "MEASUREMENTS.csv row 3 /measurement_source:", "is not one of"),
        ("quantity", "", "MEASUREMENTS.csv row 3 /quantity:", "should be non-empty"),
    ],
    ids=["observation-id", "estimated", "source", "blank-quantity"],
)
def test_each_measurement_row_is_checked_against_its_schema(
    tmp_path: Path, column: str, value: str, pointer: str, fragment: str
) -> None:
    package = tmp_path / "rows"
    write_valid(package)
    _edit_measurement_row(package, 3, column, value)
    result = _verify_after(package)
    _no_crash(result)
    assert result["exit_code"] == 1
    messages = _schema_messages(result)
    assert any(message.startswith(pointer) and fragment in message for message in messages), messages


def test_measurement_schema_rejects_unknown_missing_and_mistyped_fields() -> None:
    row = {
        "observation_id": "pem_observation_1_" + "d" * 32,
        "witness_id": WITNESS,
        "session_id": SESSION,
        "quantity": "instrument_mass",
        "value": "1800.5",
        "unit": "g",
        "measurement_source": "DIRECT_MASS_MEASUREMENT",
        "instrument_id": "scale-1",
        "calibration_status": "CALIBRATION_UNVERIFIED",
        "observed_at": "2026-11-18T18:00:00+00:00",
        "raw_evidence_ref": "",
        "note": "",
        "missing_reason": "",
        "derived_from": "",
        "algorithm_id": "",
        "algorithm_version": "",
        "algorithm_parameters": "",
        "estimated": "false",
    }
    assert schema_findings(MEASUREMENT, row, "row") == []
    assert schema_findings(MEASUREMENT, {**row, "extra": ""}, "row")
    assert schema_findings(MEASUREMENT, {k: v for k, v in row.items() if k != "unit"}, "row")
    assert schema_findings(MEASUREMENT, {**row, "value": 1800.5}, "row")


def test_schema_findings_are_bounded_for_a_hostile_document() -> None:
    hostile = {f"field_{index}": index for index in range(500)}
    found = schema_findings(BUILD_RECORD, hostile, "BUILD-RECORD.json")
    assert 0 < len(found) <= 21
    assert all(len(item.message) < 300 for item in found)


def test_ingest_refuses_to_write_a_manifest_that_breaks_its_schema(tmp_path: Path) -> None:
    package = tmp_path / "nowitness"
    write_valid(package)
    record = _load(package / "BUILD-RECORD.json")
    record.pop("witness_id")
    _save(package / "BUILD-RECORD.json", record)
    with pytest.raises(PackageError, match="breaks its schema"):
        ingest_package(package)
    assert not (package / "WITNESS-MANIFEST.json").exists()


def test_scale_length_measured_is_accepted_without_warning(tmp_path: Path) -> None:
    package = tmp_path / "scale"
    write_valid(package)
    ingest_package(package)
    result = verify_package(package)
    assert result["exit_code"] == 0
    assert not [item for item in result["findings"] if item["code"] == "scale_length_unknown"]


def test_unknown_scale_length_with_reason_is_recorded_uncertainty(tmp_path: Path) -> None:
    package = tmp_path / "scale"
    write_valid(package)
    record = _load(package / "BUILD-RECORD.json")
    record.update(scale_length_mm=None, scale_length_unknown_reason="nut replaced; not remeasured")
    _save(package / "BUILD-RECORD.json", record)
    result = _verify_after(package)
    assert result["exit_code"] == 0
    warnings = [item for item in result["findings"] if item["severity"] == "warning"]
    assert [item["code"] for item in warnings] == ["scale_length_unknown"]
    assert "nut replaced" in warnings[0]["message"]
    text = render_package(package)
    assert "## Recorded uncertainty" in text
    assert "scale_length_unknown: scale length not recorded: nut replaced; not remeasured" in text


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_unknown_scale_length_without_reason_is_malformed(tmp_path: Path, reason) -> None:
    package = tmp_path / "scale"
    write_valid(package)
    record = _load(package / "BUILD-RECORD.json")
    record.update(scale_length_mm=None, scale_length_unknown_reason=reason)
    _save(package / "BUILD-RECORD.json", record)
    result = _verify_after(package)
    assert result["exit_code"] == 1
    assert any(item["code"] == "missing_dimension" for item in result["findings"])
    assert not any(item["code"] == "scale_length_unknown" for item in result["findings"])


def test_direct_dimension_is_still_required_when_scale_length_is_known(tmp_path: Path) -> None:
    package = tmp_path / "nodim"
    write_valid(package)
    path = package / "MEASUREMENTS.csv"
    rows = [row for row in path.read_text(encoding="utf-8").splitlines() if "lower_bout_width" not in row]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    result = _verify_after(package)
    assert result["exit_code"] == 1
    assert any(
        item["code"] == "missing_dimension" and "direct dimension" in item["message"] for item in result["findings"]
    )
