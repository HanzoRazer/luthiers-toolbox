"""Descriptive measurements of a verified build-response capture.

The calculations name their algorithm and inputs. They do not estimate
wood stiffness, damping, species, or a manufacturing result.
"""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
import math
import os
import struct
import wave
from datetime import datetime
from pathlib import Path

from app.physical_engineering.build_witness.package import PackageError, ingest_package, verify_package
from app.physical_engineering.build_witness.vocabulary import (
    ALGORITHM_ID,
    ALGORITHM_VERSION,
    ALLOWED_DERIVATIONS,
    FFT_SIZE,
    REFUSED_DERIVATIONS,
)

_FULL_SCALE = Decimal(32767)


def analyze_package(
    package: Path,
    *,
    compare_reference: bool = False,
    infer_species: bool = False,
    derive: list[str] | None = None,
) -> dict:
    if compare_reference or infer_species:
        raise PackageError("reference comparison and species inference are blocked", 4)
    requested = derive or sorted(ALLOWED_DERIVATIONS)
    for name in requested:
        if name in REFUSED_DERIVATIONS or name not in ALLOWED_DERIVATIONS:
            raise PackageError("derivation is not allowed: " + name, 4)
    verified = verify_package(package)
    if verified["exit_code"] != 0:
        raise PackageError("analysis requires an integrity-verified package", verified["exit_code"])
    payload = _observations(Path(package), verified["witness_id"], requested)
    destination = Path(package) / "derived" / "observations.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    _atomic(destination, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    ingest_package(package, replace=True)
    return payload


def _observations(package: Path, witness_id: str, requested: list[str]) -> dict:
    protocol = json.loads((package / "TEST-PROTOCOL.json").read_text(encoding="utf-8"))
    build = json.loads((package / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    millis = int(datetime.fromisoformat(build["test_date"]).timestamp() * 1000)
    trials = [_load(package / trial["file"]) for trial in protocol["trials"]]
    background = _load(package / protocol["background_file"])
    inputs = [trial["file"] for trial in protocol["trials"]] + [protocol["background_file"]]
    rows: list[dict] = []
    for index, audio in enumerate(trials):
        rows.extend(_trial_rows(witness_id, millis, inputs[index], audio, requested))
    rows.extend(_trial_rows(witness_id, millis, protocol["background_file"], background, {"noise_floor", "capture_duration"} & set(requested)))
    rows.extend(_across(witness_id, millis, inputs, trials, background, requested))
    rows.sort(key=lambda item: (item["quantity"], item["raw_evidence_ref"]))
    return {
        "algorithm_id": ALGORITHM_ID,
        "algorithm_parameters": {"fft_size": FFT_SIZE, "full_scale": 32767, "window": "rectangular"},
        "algorithm_version": ALGORITHM_VERSION,
        "implementation": "python-stdlib-wave",
        "inputs": inputs,
        "observations": rows,
        "schema_id": "pem_derived_observations",
        "schema_version": "1",
        "witness_id": witness_id,
    }


def _trial_rows(witness_id: str, millis: int, relative: str, audio: dict, requested: set[str] | list[str]) -> list[dict]:
    rows = []
    wanted = set(requested)
    peak, rms, clipped = _levels(audio["samples"])
    if "capture_duration" in wanted:
        rows.append(_row(witness_id, millis, "capture_duration_s", _duration(audio), "s", relative))
    if "peak_amplitude" in wanted:
        rows.append(_row(witness_id, millis, "peak_amplitude_ratio", peak, "dimensionless", relative))
    if "rms_level" in wanted:
        rows.append(_row(witness_id, millis, "rms_amplitude_ratio", rms, "dimensionless", relative))
    if "noise_floor" in wanted and "background" in Path(relative).name:
        rows.append(_row(witness_id, millis, "noise_floor_rms_ratio", rms, "dimensionless", relative))
    if "peak_frequencies" in wanted or "dominant_spectral_peaks" in wanted:
        frequency = _dominant_hz(audio["samples"], audio["rate"])
        if frequency is None:
            rows.append(_warning(witness_id, millis, "frequency_unsupported", relative))
        else:
            rows.append(_row(witness_id, millis, "dominant_frequency_hz", frequency, "Hz", relative))
    if "envelope_decay" in wanted:
        decay = _envelope(audio["samples"])
        if decay is None:
            rows.append(_warning(witness_id, millis, "envelope_unsupported", relative))
        else:
            rows.append(_row(witness_id, millis, "envelope_level_ratio", decay, "dimensionless", relative))
    if "capture_warnings" in wanted and clipped:
        rows.append(_warning(witness_id, millis, "clipping", relative))
    return rows


def _across(witness_id, millis, inputs, trials, background, requested) -> list[dict]:
    rows = []
    wanted = set(requested)
    peaks = [_levels(audio["samples"])[0] for audio in trials]
    if "trial_differences" in wanted and peaks:
        rows.append(
            _row(
                witness_id,
                millis,
                "trial_peak_difference",
                _subtract(_decimal_max(peaks), _decimal_min(peaks)),
                "dimensionless",
                inputs[0],
            )
        )
    if "repeatability" in wanted:
        frequencies = [item for item in (_dominant_hz(audio["samples"], audio["rate"]) for audio in trials) if item]
        if len(frequencies) == len(trials):
            rows.append(
                _row(
                    witness_id,
                    millis,
                    "trial_frequency_difference_hz",
                    _subtract(_decimal_max(frequencies), _decimal_min(frequencies)),
                    "Hz",
                    inputs[0],
                )
            )
    if "capture_warnings" in wanted:
        signal = _levels(trials[0]["samples"])[1]
        noise = _levels(background["samples"])[1]
        if Decimal(signal) < Decimal("0.01"):
            rows.append(_warning(witness_id, millis, "insufficient_signal", inputs[0]))
        if Decimal(noise) * 2 > Decimal(signal):
            rows.append(_warning(witness_id, millis, "excessive_background", inputs[0]))
    return rows


def _row(witness_id: str, millis: int, quantity: str, value: str, unit: str, source: str) -> dict:
    return {
        "algorithm_id": ALGORITHM_ID,
        "algorithm_version": ALGORITHM_VERSION,
        "derived_from": [source],
        "measurement_source": "DERIVED_FROM_CAPTURE",
        "observation_id": _observation_id(witness_id, quantity, source, millis),
        "quantity": quantity,
        "raw_evidence_ref": source,
        "unit": unit,
        "value": value,
        "witness_id": witness_id,
    }


def _warning(witness_id: str, millis: int, code: str, source: str) -> dict:
    row = _row(witness_id, millis, "capture_warning", code, "none", source)
    row["observation_id"] = _observation_id(witness_id, "capture_warning:" + code, source, millis)
    return row


def _observation_id(witness_id: str, quantity: str, source: str, millis: int) -> str:
    digest = hashlib.sha256(f"{witness_id}|{quantity}|{source}".encode("utf-8")).hexdigest()[:32]
    return f"pem_observation_{millis}_{digest}"


def _load(path: Path) -> dict:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        raw = handle.readframes(handle.getnframes())
        rate = handle.getframerate()
        frames = handle.getnframes()
    samples = [struct.unpack_from("<h", raw, index * channels * 2)[0] for index in range(frames)]
    return {"rate": rate, "samples": samples}


def _levels(samples: list[int]) -> tuple[str, str, bool]:
    peak = max(abs(sample) for sample in samples)
    square = sum(Decimal(sample) * Decimal(sample) for sample in samples) / Decimal(len(samples))
    rms = square.sqrt() / _FULL_SCALE
    clipped = any(sample >= 32767 or sample <= -32768 for sample in samples)
    return (_quantize(Decimal(peak) / _FULL_SCALE), _quantize(rms), clipped)


def _duration(audio: dict) -> str:
    return _quantize(Decimal(len(audio["samples"])) / Decimal(audio["rate"]))


def _dominant_hz(samples: list[int], rate: int) -> str | None:
    if len(samples) < FFT_SIZE:
        return None
    window = samples[:FFT_SIZE]
    best_k = 1
    best = -1.0
    for bin_index in range(1, FFT_SIZE // 2):
        power = _bin_power(window, bin_index)
        if power > best:
            best = power
            best_k = bin_index
    return _quantize(Decimal(best_k * rate) / Decimal(FFT_SIZE))


def _bin_power(window: list[int], bin_index: int) -> float:
    real = 0.0
    imag = 0.0
    for index, sample in enumerate(window):
        angle = -2.0 * math.pi * bin_index * index / FFT_SIZE
        real += sample * math.cos(angle)
        imag += sample * math.sin(angle)
    return real * real + imag * imag


def _envelope(samples: list[int]) -> str | None:
    half = len(samples) // 2
    if half < 2:
        return None
    first = _levels(samples[:half])[1]
    second = _levels(samples[half:])[1]
    if Decimal(first) == 0:
        return None
    return _quantize(Decimal(second) / Decimal(first))


def _subtract(left: str, right: str) -> str:
    return _quantize(Decimal(left) - Decimal(right))


def _decimal_max(values: list[str]) -> str:
    return _quantize(max(Decimal(value) for value in values))


def _decimal_min(values: list[str]) -> str:
    return _quantize(min(Decimal(value) for value in values))


def _quantize(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000001")), "f")


def _atomic(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)
