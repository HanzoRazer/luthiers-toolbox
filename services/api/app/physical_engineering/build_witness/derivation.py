"""Descriptive measurements of a build-response capture.

Pure computation over sealed audio. ``observations`` is deterministic, so
the stored derived document can be recomputed and compared byte for byte.
The calculations name their algorithm and inputs. They do not estimate
wood stiffness, damping, species, or a manufacturing result.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import wave
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.physical_engineering.build_witness.findings import PackageError
from app.physical_engineering.build_witness.paths import MANIFEST_NAME, sha256_file
from app.physical_engineering.build_witness.vocabulary import (
    ALGORITHM_ID,
    ALGORITHM_VERSION,
    FFT_SIZE,
)

DERIVED_SCHEMA_ID = "pem_derived_observations"


def observations(package: Path, witness_id: str, requested: list[str]) -> dict:
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
    for row in rows:
        row["session_id"] = build["session_id"]
    rows.sort(key=lambda item: (item["quantity"], item["raw_evidence_ref"]))
    scales = {audio["full_scale"] for audio in trials + [background]}
    if len(scales) != 1:
        raise PackageError("trial and background captures use different sample widths", 1)
    return {
        "algorithm_id": ALGORITHM_ID,
        "algorithm_parameters": {"fft_size": FFT_SIZE, "full_scale": scales.pop(), "window": "rectangular"},
        "algorithm_version": ALGORITHM_VERSION,
        "derivations": sorted(set(requested)),
        "evidence_manifest_sha256": sha256_file(package / MANIFEST_NAME),
        "implementation": "python-stdlib-wave",
        "inputs": [
            {"byte_length": (package / item).stat().st_size, "path": item, "sha256": sha256_file(package / item)}
            for item in inputs
        ],
        "observations": rows,
        "schema_id": DERIVED_SCHEMA_ID,
        "schema_version": "1",
        "session_id": build["session_id"],
        "witness_id": witness_id,
    }


def _trial_rows(witness_id: str, millis: int, relative: str, audio: dict, requested: set[str] | list[str]) -> list[dict]:
    rows = []
    wanted = set(requested)
    peak, rms, clipped = _levels(audio)
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
        decay = _envelope(audio)
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
    peaks = [_levels(audio)[0] for audio in trials]
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
        signal = _levels(trials[0])[1]
        noise = _levels(background)[1]
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
    digest = hashlib.sha256(f"{witness_id}|{quantity}|{source}".encode()).hexdigest()[:32]
    return f"pem_observation_{millis}_{digest}"


def _full_scale(width: int) -> int:
    """Largest positive PCM code for a sample width in bytes."""
    return (1 << (8 * width - 1)) - 1


def _decode(raw: bytes, width: int, frames: int) -> list[int]:
    """Signed integer samples of a mono PCM stream.

    WAV stores 8-bit PCM unsigned with a 128 offset and wider PCM as
    little-endian two's complement.
    """
    if width == 1:
        return [byte - 128 for byte in raw[:frames]]
    if width == 2:
        return list(struct.unpack_from(f"<{frames}h", raw))
    if width == 4:
        return list(struct.unpack_from(f"<{frames}i", raw))
    if width == 3:
        return [int.from_bytes(raw[index : index + 3], "little", signed=True) for index in range(0, frames * 3, 3)]
    raise PackageError(f"analysis does not support {width * 8}-bit PCM", 1)


def _load(path: Path) -> dict:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        frames = handle.getnframes()
        raw = handle.readframes(frames)
    if channels != 1:
        # Choosing one channel or mixing them would change what is measured.
        # Refuse instead of reporting a figure for part of the capture.
        raise PackageError(f"analysis supports mono captures only; {path.name} has {channels} channels", 1)
    if len(raw) < frames * width:
        raise PackageError(f"audio data is shorter than its header declares: {path.name}", 1)
    return {"rate": rate, "samples": _decode(raw, width, frames), "full_scale": _full_scale(width)}


def _levels(audio: dict) -> tuple[str, str, bool]:
    samples = audio["samples"]
    full = audio["full_scale"]
    scale = Decimal(full)
    peak = max(abs(sample) for sample in samples)
    square = sum(Decimal(sample) * Decimal(sample) for sample in samples) / Decimal(len(samples))
    rms = square.sqrt() / scale
    clipped = any(sample >= full or sample <= -full - 1 for sample in samples)
    return (_quantize(Decimal(peak) / scale), _quantize(rms), clipped)


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


def _envelope(audio: dict) -> str | None:
    samples = audio["samples"]
    half = len(samples) // 2
    if half < 2:
        return None
    first = _levels({**audio, "samples": samples[:half]})[1]
    second = _levels({**audio, "samples": samples[half:]})[1]
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
