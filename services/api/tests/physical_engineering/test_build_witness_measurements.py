"""Environment, trial, and derived-observation tests."""

from __future__ import annotations

import json
from pathlib import Path

from app.physical_engineering.build_witness.analyze import analyze_package
from app.physical_engineering.build_witness.package import PackageError, ingest_package, verify_package
from app.physical_engineering.build_witness.paths import sha256_file
from .pem_build_witness_fixture import write_valid, write_wav


def _package(tmp_path: Path, **kwargs: object) -> Path:
    package = tmp_path / "pkg"
    write_valid(package, **kwargs)
    return package


def test_missing_temperature_or_humidity_fails(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _drop_environment(package, "air_temperature")
    ingest_package(package)
    assert any(item["code"] == "incomplete_temperature" for item in verify_package(package)["findings"])
    package = _package(tmp_path / "humidity")
    _drop_environment(package, "relative_humidity")
    ingest_package(package)
    assert any(item["code"] == "incomplete_humidity" for item in verify_package(package)["findings"])


def test_missing_moisture_needs_a_reason_and_units_are_not_converted(tmp_path: Path) -> None:
    package = _package(tmp_path)
    kept = [line for line in (package / "ENVIRONMENT.csv").read_text(encoding="utf-8").splitlines() if "wood_moisture" not in line]
    (package / "ENVIRONMENT.csv").write_text("\n".join(kept) + "\n", encoding="utf-8")
    ingest_package(package)
    assert any(item["code"] == "moisture_reason_missing" for item in verify_package(package)["findings"])
    package = _package(tmp_path / "fahrenheit")
    text = (package / "ENVIRONMENT.csv").read_text(encoding="utf-8").replace(",degC,", ",degF,")
    (package / "ENVIRONMENT.csv").write_text(text, encoding="utf-8")
    ingest_package(package)
    before = (package / "ENVIRONMENT.csv").read_bytes()
    result = verify_package(package)
    assert result["exit_code"] == 1
    assert any(item["code"] == "unit_rejected" for item in result["findings"])
    assert (package / "ENVIRONMENT.csv").read_bytes() == before


def test_unknown_calibration_is_a_state_and_a_future_date_fails(tmp_path: Path) -> None:
    package = _package(tmp_path)
    ingest_package(package)
    result = verify_package(package)
    assert result["exit_code"] == 0
    assert "CALIBRATION_UNVERIFIED" in result["states"]
    fresh = _package(tmp_path / "dated")
    equipment = json.loads((fresh / "EQUIPMENT.json").read_text(encoding="utf-8"))
    equipment["instruments"][0]["calibration_date"] = "2099-01-01"
    (fresh / "EQUIPMENT.json").write_text(json.dumps(equipment), encoding="utf-8")
    text = (fresh / "ENVIRONMENT.csv").read_text(encoding="utf-8").replace(
        "2026-11-18T17:50:00+00:00", "1890-01-01T00:00:00+00:00", 1
    )
    (fresh / "ENVIRONMENT.csv").write_text(text, encoding="utf-8")
    ingest_package(fresh)
    codes = {item["code"] for item in verify_package(fresh)["findings"]}
    assert "calibration_date" in codes
    assert "timestamp" in codes


def test_trial_rules(tmp_path: Path) -> None:
    three = _package(tmp_path)
    ingest_package(three)
    assert verify_package(three)["exit_code"] == 0
    two = tmp_path / "two"
    write_valid(two, trials=2)
    ingest_package(two)
    assert any(item["code"] == "trial_count" for item in verify_package(two)["findings"])
    mixed = _package(tmp_path / "mixed")
    _edit_trial(mixed, "protocol_id", "other_tap")
    ingest_package(mixed)
    assert any(item["code"] == "trial_count" for item in verify_package(mixed)["findings"])
    moved = _package(tmp_path / "moved")
    _edit_trial(moved, "microphone_position", "lower_bout")
    ingest_package(moved)
    assert any(item["code"] == "trial_count" for item in verify_package(moved)["findings"])
    quiet = tmp_path / "quiet"
    write_valid(quiet, background=False)
    ingest_package(quiet)
    assert any(item["code"] == "background_missing" for item in verify_package(quiet)["findings"])


def test_audio_header_and_clipping(tmp_path: Path) -> None:
    empty = _package(tmp_path / "empty")
    write_wav(empty / "raw" / "audio" / "fixed-tap__trial-1.wav", amplitude=0.4, frames=0)
    ingest_package(empty)
    assert any(item["code"] == "empty_audio" for item in verify_package(empty)["findings"])
    broken = _package(tmp_path / "broken")
    (broken / "raw" / "audio" / "fixed-tap__trial-1.wav").write_bytes(b"not-a-wav")
    ingest_package(broken)
    assert any(item["code"] == "unreadable_audio" for item in verify_package(broken)["findings"])
    rate = _package(tmp_path / "rate")
    write_wav(rate / "raw" / "audio" / "fixed-tap__trial-1.wav", amplitude=0.4, rate=16000)
    ingest_package(rate)
    assert any(item["code"] == "sample_rate_mismatch" for item in verify_package(rate)["findings"])
    stereo = _package(tmp_path / "stereo")
    write_wav(stereo / "raw" / "audio" / "fixed-tap__trial-1.wav", amplitude=0.4, channels=2)
    ingest_package(stereo)
    assert any(item["code"] == "channel_mismatch" for item in verify_package(stereo)["findings"])
    clipped = _package(tmp_path / "clipped")
    write_wav(clipped / "raw" / "audio" / "fixed-tap__trial-1.wav", amplitude=1.0)
    ingest_package(clipped)
    observations = analyze_package(clipped)
    assert any(row["value"] == "clipping" for row in observations["observations"])


def test_derived_observations_are_reproducible_and_do_not_replace_raw(tmp_path: Path) -> None:
    package = _package(tmp_path)
    ingest_package(package)
    raw = package / "raw" / "audio" / "fixed-tap__trial-1.wav"
    before = sha256_file(raw)
    measurements = (package / "MEASUREMENTS.csv").read_bytes()
    first = analyze_package(package)
    assert sha256_file(raw) == before
    assert (package / "MEASUREMENTS.csv").read_bytes() == measurements
    assert first["algorithm_id"] == "pem_descriptive_v1"
    assert first["algorithm_version"] == "1"
    assert first["inputs"]
    for row in first["observations"]:
        assert row["raw_evidence_ref"] in first["inputs"]
        assert row["measurement_source"] == "DERIVED_FROM_CAPTURE"
    text = (package / "derived" / "observations.json").read_bytes()
    second = analyze_package(package)
    assert second == first
    assert (package / "derived" / "observations.json").read_bytes() == text
    assert verify_package(package)["exit_code"] == 0


def test_estimates_and_prohibited_derivations_are_refused(tmp_path: Path) -> None:
    package = _package(tmp_path)
    text = (package / "MEASUREMENTS.csv").read_text(encoding="utf-8").replace(
        "DIRECT_MASS_MEASUREMENT", "DIRECT_MASS_MEASUREMENT", 1
    )
    lines = text.splitlines()
    lines[1] = lines[1].replace(",false", ",true")
    (package / "MEASUREMENTS.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    ingest_package(package)
    assert any(item["code"] == "estimate_as_direct" for item in verify_package(package)["findings"])
    sealed = _package(tmp_path / "sealed")
    ingest_package(sealed)
    for kwargs in (
        {"derive": ["moe"]},
        {"infer_species": True},
        {"compare_reference": True},
    ):
        try:
            analyze_package(sealed, **kwargs)
        except PackageError as exc:
            assert exc.code == 4
        else:
            raise AssertionError(kwargs)


def _drop_environment(package: Path, quantity: str) -> None:
    lines = (package / "ENVIRONMENT.csv").read_text(encoding="utf-8").splitlines()
    kept = [lines[0]] + [line for line in lines[1:] if f",{quantity}," not in line]
    (package / "ENVIRONMENT.csv").write_text("\n".join(kept) + "\n", encoding="utf-8")


def _edit_trial(package: Path, key: str, value: str) -> None:
    protocol = json.loads((package / "TEST-PROTOCOL.json").read_text(encoding="utf-8"))
    protocol["trials"][0][key] = value
    (package / "TEST-PROTOCOL.json").write_text(json.dumps(protocol), encoding="utf-8")


def _rewrite_audio(package: Path, *, width: int = 2, channels: int = 1) -> None:
    protocol = json.loads((package / "TEST-PROTOCOL.json").read_text(encoding="utf-8"))
    for index, trial in enumerate(protocol["trials"]):
        write_wav(package / trial["file"], amplitude=0.40 + index * 0.05, width=width, channels=channels)
    write_wav(package / protocol["background_file"], amplitude=0.01, width=width, channels=channels)
    protocol["bit_depth"] = width * 8
    protocol["channels"] = channels
    (package / "TEST-PROTOCOL.json").write_text(json.dumps(protocol), encoding="utf-8")


def test_every_accepted_pcm_width_is_decoded_at_its_own_scale(tmp_path: Path) -> None:
    for width in (1, 2, 3, 4):
        package = _package(tmp_path / f"w{width}")
        _rewrite_audio(package, width=width)
        ingest_package(package)
        assert verify_package(package)["exit_code"] == 0
        result = analyze_package(package)
        assert result["algorithm_parameters"]["full_scale"] == (1 << (8 * width - 1)) - 1
        rows = {
            row["quantity"]: row["value"]
            for row in result["observations"]
            if row["raw_evidence_ref"].endswith("trial-1.wav")
        }
        assert rows["dominant_frequency_hz"] == "125.000000", width
        assert abs(float(rows["peak_amplitude_ratio"]) - 0.40) < 0.01, width


def test_multichannel_capture_verifies_but_analysis_refuses_it(tmp_path: Path) -> None:
    package = _package(tmp_path)
    _rewrite_audio(package, channels=2)
    ingest_package(package)
    assert verify_package(package)["exit_code"] == 0
    try:
        analyze_package(package)
    except PackageError as exc:
        assert exc.code == 1
        assert "mono" in str(exc)
    else:
        raise AssertionError("a stereo capture was analyzed from one channel")
    assert not (package / "derived" / "observations.json").exists()


def test_trials_must_match_the_protocol_settings(tmp_path: Path) -> None:
    package = _package(tmp_path)
    protocol = json.loads((package / "TEST-PROTOCOL.json").read_text(encoding="utf-8"))
    for trial in protocol["trials"]:
        trial["microphone_position"] = "lower_bout_50cm"
    (package / "TEST-PROTOCOL.json").write_text(json.dumps(protocol), encoding="utf-8")
    ingest_package(package)
    result = verify_package(package)
    assert result["exit_code"] == 1
    assert any(item["code"] == "trial_protocol_mismatch" for item in result["findings"])


def test_trial_count_must_match_the_trials_listed(tmp_path: Path) -> None:
    package = _package(tmp_path)
    protocol = json.loads((package / "TEST-PROTOCOL.json").read_text(encoding="utf-8"))
    protocol["trial_count"] = 7
    (package / "TEST-PROTOCOL.json").write_text(json.dumps(protocol), encoding="utf-8")
    ingest_package(package)
    assert verify_package(package)["exit_code"] == 1


def test_one_recording_cannot_count_as_several_trials(tmp_path: Path) -> None:
    reused = _package(tmp_path / "reused")
    protocol = json.loads((reused / "TEST-PROTOCOL.json").read_text(encoding="utf-8"))
    for trial in protocol["trials"]:
        trial["file"] = protocol["trials"][0]["file"]
    (reused / "TEST-PROTOCOL.json").write_text(json.dumps(protocol), encoding="utf-8")
    ingest_package(reused)
    assert any(item["code"] == "duplicate_audio" for item in verify_package(reused)["findings"])
    copied = _package(tmp_path / "copied")
    first = copied / "raw" / "audio" / "fixed-tap__trial-1.wav"
    (copied / "raw" / "audio" / "fixed-tap__trial-2.wav").write_bytes(first.read_bytes())
    ingest_package(copied)
    assert any(item["code"] == "duplicate_audio" for item in verify_package(copied)["findings"])
