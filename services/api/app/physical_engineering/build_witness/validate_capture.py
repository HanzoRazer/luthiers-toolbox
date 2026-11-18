"""Trial, environment, and measurement-row checks."""

from __future__ import annotations

import wave
from datetime import datetime
from pathlib import Path

from app.physical_engineering.build_witness.findings import Finding, finding
from app.physical_engineering.build_witness.ids import is_identifier
from app.physical_engineering.build_witness.paths import normalize_relative
from app.physical_engineering.build_witness.validate_support import DECIMAL_TEXT, parse_time, path_exists
from app.physical_engineering.build_witness.vocabulary import (
    CALIBRATION_UNVERIFIED_STATUS,
    CALIBRATION_VERIFIED,
    DIRECT_SOURCES,
    MEASUREMENT_SOURCES,
)

def _check_trial_groups(package: Path, protocol: dict, findings: list[Finding]) -> None:
    trials = protocol.get("trials")
    if not isinstance(trials, list):
        findings.append(finding("malformed", "trial_count", "trials missing"))
        return
    background = protocol.get("background_file")
    if not isinstance(background, str):
        findings.append(finding("malformed", "background_missing", "background capture is required"))
    else:
        _check_wav(package, background, protocol, findings)
    groups: dict[tuple, int] = {}
    for trial in trials:
        if not isinstance(trial, dict) or not isinstance(trial.get("file"), str):
            findings.append(finding("malformed", "trial_count", "trial is malformed"))
            continue
        _check_wav(package, trial["file"], protocol, findings)
        key = (
            trial.get("protocol_id"),
            trial.get("excitation_method"),
            trial.get("excitation_position"),
            trial.get("microphone_position"),
            trial.get("support_condition"),
            trial.get("string_state"),
        )
        groups[key] = groups.get(key, 0) + 1
    if not groups or any(count < 3 for count in groups.values()):
        findings.append(finding("malformed", "trial_count", "each configuration needs three trials"))


def _check_wav(package: Path, relative: str, protocol: dict, findings: list[Finding]) -> None:
    try:
        path = package / normalize_relative(relative)
    except Exception:
        findings.append(finding("integrity", "unsafe_path", relative))
        return
    if path.is_symlink() or not path.is_file():
        findings.append(finding("malformed", "unreadable_audio", relative))
        return
    try:
        with wave.open(str(path), "rb") as handle:
            frames = handle.getnframes()
            channels = handle.getnchannels()
            rate = handle.getframerate()
            width = handle.getsampwidth()
    except (wave.Error, EOFError):
        findings.append(finding("malformed", "unreadable_audio", relative))
        return
    if frames <= 0:
        findings.append(finding("malformed", "empty_audio", relative))
    if rate != protocol.get("sample_rate_hz"):
        findings.append(finding("malformed", "sample_rate_mismatch", relative))
    if channels != protocol.get("channels"):
        findings.append(finding("malformed", "channel_mismatch", relative))
    if width * 8 != protocol.get("bit_depth"):
        findings.append(finding("malformed", "bit_depth_mismatch", relative))


def _check_audio_rows(protocol: dict, measurements: list[dict[str, str]], findings: list[Finding]) -> None:
    expected = [trial.get("file") for trial in protocol.get("trials") or [] if isinstance(trial, dict)]
    if isinstance(protocol.get("background_file"), str):
        expected.append(protocol["background_file"])
    refs = {
        row.get("raw_evidence_ref")
        for row in measurements
        if row.get("measurement_source") == "DIRECT_AUDIO_CAPTURE"
    }
    for relative in expected:
        if relative not in refs:
            findings.append(finding("malformed", "missing_policy", "audio measurement row " + str(relative)))


def _check_equipment(equipment: dict, build: dict, findings: list[Finding]) -> None:
    if equipment.get("schema_id") != "pem_equipment":
        findings.append(finding("malformed", "schema_version", "equipment schema_id"))
    test_date = build.get("test_date") if isinstance(build, dict) else None
    observed = parse_time(test_date, findings) if isinstance(test_date, str) else None
    instruments = equipment.get("instruments")
    if not isinstance(instruments, list):
        findings.append(finding("malformed", "missing_policy", "instruments"))
        return
    for instrument in instruments:
        if isinstance(instrument, dict):
            _calibration_date(instrument.get("calibration_date"), observed, findings)


def _calibration_date(value: object, observed: datetime | None, findings: list[Finding]) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str):
        findings.append(finding("malformed", "calibration_date", "calibration date"))
        return
    try:
        stamped = datetime.fromisoformat(value)
    except ValueError:
        findings.append(finding("malformed", "calibration_date", "calibration date"))
        return
    if stamped.year < 1990 or stamped.year > 2100:
        findings.append(finding("malformed", "calibration_date", "calibration date"))
        return
    if observed is not None and stamped.date() > observed.date():
        findings.append(finding("malformed", "calibration_date", "calibration date is after the test"))


def _check_environment(rows: list[dict[str, str]], findings: list[Finding]) -> None:
    _required_phases(rows, "air_temperature", "degC", "incomplete_temperature", findings)
    _required_phases(rows, "relative_humidity", "percent", "incomplete_humidity", findings)
    moisture = [row for row in rows if row.get("quantity") == "wood_moisture"]
    if not moisture:
        findings.append(finding("malformed", "moisture_reason_missing", "moisture reading needs a value or a reason"))
        return
    for row in moisture:
        _environment_row(row, "percent", findings)
        if not row.get("value") and not row.get("missing_reason"):
            findings.append(finding("malformed", "moisture_reason_missing", "moisture reason is required"))


def _required_phases(rows: list[dict[str, str]], quantity: str, unit: str, code: str, findings: list[Finding]) -> None:
    phases = {row.get("phase") for row in rows if row.get("quantity") == quantity and row.get("value")}
    if not {"before", "after"} <= phases:
        findings.append(finding("malformed", code, quantity))
    for row in rows:
        if row.get("quantity") == quantity:
            _environment_row(row, unit, findings)


def _environment_row(row: dict[str, str], unit: str, findings: list[Finding]) -> None:
    if row.get("value") and row.get("unit") != unit:
        findings.append(finding("malformed", "unit_rejected", row.get("quantity") or "unit"))
    if row.get("value") and DECIMAL_TEXT.fullmatch(row["value"]) is None:
        findings.append(finding("malformed", "unit_rejected", "value is not a decimal string"))
    if row.get("timestamp"):
        parse_time(row["timestamp"], findings)


def _check_measurements(package: Path, rows: list[dict[str, str]], findings: list[Finding]) -> None:
    mass = 0
    dimension = 0
    for row in rows:
        _one_measurement(package, row, findings)
        if (
            row.get("quantity") == "instrument_mass"
            and row.get("measurement_source") == "DIRECT_MASS_MEASUREMENT"
            and row.get("unit") == "g"
            and row.get("estimated") != "true"
            and row.get("value")
            and DECIMAL_TEXT.fullmatch(row["value"])
        ):
            mass += 1
        if (
            row.get("measurement_source") == "DIRECT_DIMENSION_MEASUREMENT"
            and row.get("unit") == "mm"
            and row.get("estimated") != "true"
            and row.get("value")
            and DECIMAL_TEXT.fullmatch(row["value"])
        ):
            dimension += 1
    if mass < 1:
        findings.append(finding("malformed", "missing_mass", "instrument mass is required"))
    if dimension < 1:
        findings.append(finding("malformed", "missing_dimension", "a direct dimension is required"))


def _one_measurement(package: Path, row: dict[str, str], findings: list[Finding]) -> None:
    source = row.get("measurement_source")
    if not is_identifier(row.get("observation_id")):
        findings.append(finding("malformed", "schema_version", "observation_id"))
    if source not in MEASUREMENT_SOURCES:
        findings.append(finding("malformed", "schema_version", "measurement source"))
        return
    if source == "DECLARED_BUILD_PROPERTY" and row.get("value"):
        findings.append(finding("malformed", "declared_as_measurement", row.get("quantity") or "declared"))
    if source in DIRECT_SOURCES and row.get("estimated") == "true":
        findings.append(finding("malformed", "estimate_as_direct", row.get("quantity") or "estimate"))
    if source == "IMPORTED_MEASUREMENT" and not row.get("raw_evidence_ref"):
        findings.append(finding("malformed", "imported_source_missing", row.get("quantity") or "imported"))
    if source == "DERIVED_FROM_CAPTURE":
        for key in ("derived_from", "algorithm_id", "algorithm_version", "algorithm_parameters"):
            if not row.get(key):
                findings.append(finding("malformed", "derived_provenance_missing", key))
    if row.get("observed_at"):
        parse_time(row["observed_at"], findings)
    ref = row.get("raw_evidence_ref")
    if ref and not path_exists(package, ref):
        findings.append(finding("malformed", "missing_policy", "evidence ref missing"))
    status = row.get("calibration_status")
    if status and status not in {CALIBRATION_VERIFIED, CALIBRATION_UNVERIFIED_STATUS}:
        findings.append(finding("malformed", "schema_version", "calibration status"))


def _calibration_unverified(docs: dict) -> bool:
    statuses = [str(docs["equipment"].get("calibration_status") or "")]
    for instrument in docs["equipment"].get("instruments") or []:
        if isinstance(instrument, dict):
            statuses.append(str(instrument.get("calibration_status") or ""))
    for row in docs["environment"] + docs["measurements"]:
        statuses.append(str(row.get("calibration_status") or ""))
    return any(item != CALIBRATION_VERIFIED for item in statuses)


