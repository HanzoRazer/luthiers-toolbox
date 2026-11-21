"""Synthetic build-response packages for tests.

The audio is generated here. It is not a recording of an instrument.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import struct
import wave
from pathlib import Path

from app.physical_engineering.build_witness.ids import new_id
from app.physical_engineering.build_witness.templates import dump_json
from app.physical_engineering.build_witness.validate import stored_states
from app.physical_engineering.build_witness.vocabulary import (
    CALIBRATION_UNVERIFIED_STATUS,
    MATERIAL_IDENTITY_STATEMENT,
    NON_AUTHORITY_STATEMENT,
)

CLOCK = datetime(2026, 11, 18, 18, 0, tzinfo=timezone.utc)
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


class Factory:
    def __init__(self) -> None:
        self.n = 0

    def __call__(self) -> str:
        self.n += 1
        return f"{self.n:032x}"


def clock() -> datetime:
    return CLOCK


def write_wav(
    path: Path,
    *,
    amplitude: float,
    frames: int = 2048,
    rate: int = 8000,
    channels: int = 1,
    width: int = 2,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    full = (1 << (8 * width - 1)) - 1
    payload = bytearray()
    for index in range(frames):
        sample = int(round(amplitude * full * math.sin(2 * math.pi * 125 * index / rate)))
        sample = max(-full, min(full, sample))
        if width == 1:
            frame = struct.pack("<B", sample + 128)
        else:
            frame = sample.to_bytes(width, "little", signed=True)
        payload.extend(frame * channels)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(width)
        handle.setframerate(rate)
        handle.writeframes(payload)


def write_valid(root: Path, *, trials: int = 3, background: bool = True) -> dict[str, str]:
    factory = Factory()
    witness_id = new_id("witness", clock, factory)
    build_id = new_id("build", clock, factory)
    session_id = new_id("session", clock, factory)
    root.mkdir(parents=True, exist_ok=True)
    (root / "raw" / "audio").mkdir(parents=True, exist_ok=True)
    (root / "raw" / "images").mkdir(parents=True, exist_ok=True)
    names = [f"raw/audio/fixed-tap__trial-{index}.wav" for index in range(1, trials + 1)]
    for index, relative in enumerate(names):
        write_wav(root / relative, amplitude=0.40 + (index * 0.05))
    background_name = "raw/audio/fixed-tap__background.wav"
    if background:
        write_wav(root / background_name, amplitude=0.01)
    (root / "raw" / "images" / "build-id.png").write_bytes(PNG)
    (root / "raw" / "images" / "placement.png").write_bytes(PNG)
    record = _record(witness_id, build_id, session_id)
    dump_json(root / "BUILD-RECORD.json", record)
    dump_json(root / "TEST-PROTOCOL.json", _protocol(session_id, names, background_name if background else None))
    dump_json(root / "EQUIPMENT.json", _equipment())
    _write_environment(root)
    _write_measurements(root, factory, witness_id, session_id, names, background_name if background else None)
    (root / "READ-ME-FIRST.txt").write_text(NON_AUTHORITY_STATEMENT + "\n", encoding="utf-8")
    return {"witness_id": witness_id, "build_id": build_id, "session_id": session_id}


def _record(witness_id: str, build_id: str, session_id: str) -> dict:
    return {
        "schema_id": "pem_build_record",
        "schema_version": "1",
        "witness_id": witness_id,
        "build_id": build_id,
        "session_id": session_id,
        "witness_class": "BUILD_RESPONSE_WITNESS",
        "authority_boundary_id": "PEM-BUILD-WITNESS-001",
        "literature_reconciliation_status": "BLOCKED_BEFORE_PREFLIGHT",
        "record_kind": "SYNTHETIC_FIXTURE",
        "instrument_type": "acoustic_guitar",
        "builder": None,
        "builder_unknown_reason": "synthetic fixture has no builder",
        "build_completion_state": "completed_instrument",
        "specimen_role": "working_instrument",
        "test_date": "2026-11-18T18:00:00+00:00",
        "test_location": "synthetic-bench",
        "test_location_unknown_reason": None,
        "scale_length_mm": "648",
        "scale_length_unknown_reason": None,
        "body_style": "dreadnought",
        "top": _declared("Adirondack"),
        "back_side": _declared("synthetic-back"),
        "neck": {
            "botanical_name": None,
            "evidence_ref": None,
            "identity_basis": None,
            "identity_status": "UNDECLARED",
            "trade_name": None,
            "unknown_reason": "not identified",
        },
        "bracing": {"declaration": "synthetic x-brace", "unknown_reason": None},
        "finish": {"declaration": "none", "unknown_reason": None},
        "bridge": {"declaration": "synthetic", "unknown_reason": None},
        "saddle": {"declaration": "synthetic", "unknown_reason": None},
        "strings": {
            "approximate_age": "0",
            "condition": "synthetic",
            "gauges": "12-53",
            "material": "phosphor bronze",
            "unknown_reason": None,
        },
        "tuning": "EADGBE",
        "component_ids": [],
        "photograph_refs": ["raw/images/build-id.png", "raw/images/placement.png"],
        "uncertainty_notes": ["synthetic fixture, not a physical instrument"],
        "material_identity_statement": MATERIAL_IDENTITY_STATEMENT,
        "operator_attestation": {
            "attested_at": "2026-11-18T18:05:00+00:00",
            "operator": "synthetic",
            "statement": "synthetic fixture, not a physical instrument",
        },
        "states": stored_states(True, True),
        "supersedes_witness_id": None,
    }


def _declared(trade_name: str) -> dict:
    return {
        "botanical_name": None,
        "evidence_ref": None,
        "identity_basis": None,
        "identity_status": "DECLARED_ONLY",
        "trade_name": trade_name,
        "unknown_reason": None,
    }


def _protocol(session_id: str, trials: list[str], background: str | None) -> dict:
    rows = []
    for index, relative in enumerate(trials, start=1):
        rows.append(
            {
                "excitation_method": "finger_tap",
                "excitation_position": "bridge",
                "file": relative,
                "microphone_position": "soundhole_12cm",
                "protocol_id": "fixed_tap",
                "string_state": "tuned",
                "support_condition": "foam_stands",
                "trial_index": index,
            }
        )
    return {
        "schema_id": "pem_test_protocol",
        "schema_version": "1",
        "protocol_id": "fixed_tap",
        "protocol_version": "1",
        "session_id": session_id,
        "operator": "synthetic",
        "objective": "capture the coupled response of one synthetic fixture",
        "excitation_method": "finger_tap",
        "excitation_position": "bridge",
        "microphone_position": "soundhole_12cm",
        "support_condition": "foam_stands",
        "string_state": "tuned",
        "tuning": "EADGBE",
        "sample_rate_hz": 8000,
        "bit_depth": 16,
        "channels": 1,
        "recording_duration_s": "0.256",
        "preprocessing": "none",
        "trial_count": 3,
        "trials": rows,
        "background_file": background,
        "file_naming_convention": "fixed-tap__trial-{index}.wav",
        "allowed_derivations": [
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
        ],
        "limitations": [NON_AUTHORITY_STATEMENT],
    }


def _equipment() -> dict:
    return {
        "schema_id": "pem_equipment",
        "schema_version": "1",
        "calibration_status": CALIBRATION_UNVERIFIED_STATUS,
        "calibration_unknown_reason": "synthetic fixture has no calibration certificate",
        "instruments": [
            {
                "calibration_date": None,
                "calibration_status": CALIBRATION_UNVERIFIED_STATUS,
                "instrument_id": "synth-mic",
                "kind": "microphone",
            }
        ],
    }


def _write_environment(root: Path) -> None:
    rows = [
        "timestamp,phase,quantity,value,unit,device_id,calibration_status,stabilization_duration_s,operator_note,missing_reason",
        "2026-11-18T17:50:00+00:00,before,air_temperature,22.4,degC,synth-thermo,CALIBRATION_UNVERIFIED,600,,",
        "2026-11-18T18:10:00+00:00,after,air_temperature,22.6,degC,synth-thermo,CALIBRATION_UNVERIFIED,600,,",
        "2026-11-18T17:50:00+00:00,before,relative_humidity,45.0,percent,synth-thermo,CALIBRATION_UNVERIFIED,600,,",
        "2026-11-18T18:10:00+00:00,after,relative_humidity,46.0,percent,synth-thermo,CALIBRATION_UNVERIFIED,600,,",
        "2026-11-18T17:50:00+00:00,before,wood_moisture,,percent,synth-meter,CALIBRATION_UNVERIFIED,600,,meter not available",
    ]
    (root / "ENVIRONMENT.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _write_measurements(root, factory, witness_id, session_id, trials, background) -> None:
    header = (
        "observation_id,witness_id,session_id,quantity,value,unit,measurement_source,"
        "instrument_id,calibration_status,observed_at,raw_evidence_ref,note,missing_reason,"
        "derived_from,algorithm_id,algorithm_version,algorithm_parameters,estimated"
    )
    rows = [header]
    rows.append(_csv(factory, witness_id, session_id, "instrument_mass", "1800.5", "g", "DIRECT_MASS_MEASUREMENT", ""))
    rows.append(_csv(factory, witness_id, session_id, "lower_bout_width", "380.0", "mm", "DIRECT_DIMENSION_MEASUREMENT", ""))
    for relative in trials:
        rows.append(_csv(factory, witness_id, session_id, "audio_capture", "0.256", "s", "DIRECT_AUDIO_CAPTURE", relative))
    if background:
        rows.append(_csv(factory, witness_id, session_id, "audio_capture", "0.256", "s", "DIRECT_AUDIO_CAPTURE", background))
    (root / "MEASUREMENTS.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _csv(factory, witness_id, session_id, quantity, value, unit, source, ref) -> str:
    observation = new_id("observation", clock, factory)
    return (
        f"{observation},{witness_id},{session_id},{quantity},{value},{unit},{source},"
        f"synth-mic,CALIBRATION_UNVERIFIED,2026-11-18T18:00:00+00:00,{ref},,,,,,,"
        "false"
    )
