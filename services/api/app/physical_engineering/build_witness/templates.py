"""Blank witness templates.

The blanks record that capture has not happened. They do not invent
measurements, environment, or audio.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.physical_engineering.build_witness.vocabulary import (
    AUTHORITY_BOUNDARY_ID,
    CALIBRATION_UNVERIFIED,
    CALIBRATION_UNVERIFIED_STATUS,
    CAPTURE_INCOMPLETE,
    LITERATURE_STATUS,
    MATERIAL_IDENTITY_STATEMENT,
    METHOD_REVIEW_PENDING,
    NON_AUTHORITY_STATEMENT,
    REFERENCE_COMPARISON_BLOCKED,
    SCIENTIFIC_INTERPRETATION_PENDING,
    WITNESS_CLASS,
)

_BLANK_STATES = [
    CALIBRATION_UNVERIFIED,
    CAPTURE_INCOMPLETE,
    METHOD_REVIEW_PENDING,
    REFERENCE_COMPARISON_BLOCKED,
    SCIENTIFIC_INTERPRETATION_PENDING,
]


def dump_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _material() -> dict:
    return {
        "botanical_name": None,
        "evidence_ref": None,
        "identity_basis": None,
        "identity_status": "UNDECLARED",
        "trade_name": None,
        "unknown_reason": "not_recorded",
    }


def _declaration() -> dict:
    return {"declaration": None, "unknown_reason": "not_recorded"}


def build_record(witness_id: str, build_id: str, session_id: str, instrument_type: str) -> dict:
    return {
        "schema_id": "pem_build_record",
        "schema_version": "1",
        "witness_id": witness_id,
        "build_id": build_id,
        "session_id": session_id,
        "witness_class": WITNESS_CLASS,
        "authority_boundary_id": AUTHORITY_BOUNDARY_ID,
        "literature_reconciliation_status": LITERATURE_STATUS,
        "record_kind": "PHYSICAL_CAPTURE",
        "instrument_type": instrument_type,
        "builder": None,
        "builder_unknown_reason": "not_recorded",
        "build_completion_state": None,
        "specimen_role": None,
        "test_date": None,
        "test_location": None,
        "test_location_unknown_reason": "not_recorded",
        "scale_length_mm": None,
        "scale_length_unknown_reason": "not_recorded",
        "body_style": None,
        "top": _material(),
        "back_side": _material(),
        "neck": _material(),
        "bracing": _declaration(),
        "finish": _declaration(),
        "bridge": _declaration(),
        "saddle": _declaration(),
        "strings": {
            "approximate_age": None,
            "condition": None,
            "gauges": None,
            "material": None,
            "unknown_reason": "not_recorded",
        },
        "tuning": None,
        "component_ids": [],
        "photograph_refs": [],
        "uncertainty_notes": ["required measurements have not been captured"],
        "material_identity_statement": MATERIAL_IDENTITY_STATEMENT,
        "operator_attestation": None,
        "states": list(_BLANK_STATES),
        "supersedes_witness_id": None,
    }


def test_protocol(session_id: str) -> dict:
    return {
        "schema_id": "pem_test_protocol",
        "schema_version": "1",
        "protocol_id": None,
        "protocol_version": "1",
        "session_id": session_id,
        "operator": None,
        "objective": "capture the coupled response of one working build",
        "excitation_method": None,
        "excitation_position": None,
        "microphone_position": None,
        "support_condition": None,
        "string_state": None,
        "tuning": None,
        "sample_rate_hz": None,
        "bit_depth": None,
        "channels": None,
        "recording_duration_s": None,
        "preprocessing": "none",
        "trial_count": 3,
        "trials": [],
        "background_file": None,
        "file_naming_convention": "{protocol_id}__trial-{index}.wav and {protocol_id}__background.wav",
        "allowed_derivations": sorted(
            [
                "capture_duration",
                "capture_warnings",
                "dominant_spectral_peaks",
                "envelope_decay",
                "noise_floor",
                "peak_amplitude",
                "peak_frequencies",
                "repeatability",
                "rms_level",
                "trial_differences",
            ]
        ),
        "limitations": [NON_AUTHORITY_STATEMENT],
    }


def equipment() -> dict:
    return {
        "schema_id": "pem_equipment",
        "schema_version": "1",
        "instruments": [],
        "calibration_status": CALIBRATION_UNVERIFIED_STATUS,
        "calibration_unknown_reason": "not_recorded",
    }


def write_blank_tree(root: Path, record: dict, protocol: dict, equipment_doc: dict) -> None:
    for relative in ("raw/audio", "raw/sensors", "raw/images", "derived/plots", "reports"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    dump_json(root / "BUILD-RECORD.json", record)
    dump_json(root / "TEST-PROTOCOL.json", protocol)
    dump_json(root / "EQUIPMENT.json", equipment_doc)
    (root / "ENVIRONMENT.csv").write_text(_ENVIRONMENT_HEADER, encoding="utf-8")
    (root / "MEASUREMENTS.csv").write_text(_MEASUREMENT_HEADER, encoding="utf-8")
    (root / "READ-ME-FIRST.txt").write_text(_README, encoding="utf-8")
    (root / "raw" / "audio" / "NO-CAPTURE.txt").write_text(
        "No audio has been captured. This file is not a measurement.\n",
        encoding="utf-8",
    )
    (root / "raw" / "sensors" / "NO-CAPTURE.txt").write_text(
        "No sensor file has been captured. This file is not a measurement.\n",
        encoding="utf-8",
    )
    (root / "raw" / "images" / "NO-CAPTURE.txt").write_text(
        "No photograph has been captured. This file is not a measurement.\n",
        encoding="utf-8",
    )
    (root / "derived" / "plots" / "NO-PLOTS.txt").write_text(
        "This increment does not generate plots.\n",
        encoding="utf-8",
    )


_ENVIRONMENT_HEADER = (
    "timestamp,phase,quantity,value,unit,device_id,calibration_status,"
    "stabilization_duration_s,operator_note,missing_reason\n"
)

_MEASUREMENT_HEADER = (
    "observation_id,witness_id,session_id,quantity,value,unit,measurement_source,"
    "instrument_id,calibration_status,observed_at,raw_evidence_ref,note,missing_reason,"
    "derived_from,algorithm_id,algorithm_version,algorithm_parameters,estimated\n"
)

_README = (
    "PEM-BUILD-WITNESS-001\n\n"
    "This directory is an external evidence package for one working build.\n"
    "Whole-instrument measurements are a BUILD_RESPONSE_WITNESS.\n"
    "They are not a material-property measurement.\n\n"
    f"{NON_AUTHORITY_STATEMENT}\n\n"
    "Literature comparison is blocked until PEM-LITERATURE-MB-RECONCILE-002R "
    "is recovered and verified. Do not fill unknown measurements with assumed "
    "room conditions or estimated values.\n"
)
