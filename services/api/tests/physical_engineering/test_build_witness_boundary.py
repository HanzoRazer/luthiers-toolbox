"""Round-4 trust boundary: creation ownership, the evidence seal and its
ledger anchor, file placement, prohibited claims anywhere, and the derived
observation boundary.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest
from app.physical_engineering.build_witness import create as create_module
from app.physical_engineering.build_witness.analyze import analyze_package
from app.physical_engineering.build_witness.package import (
    PackageError,
    create_package,
    ingest_package,
    verify_package,
)
from app.physical_engineering.build_witness.report import render_package
from app.physical_engineering.build_witness.repository import WitnessRepository

from .pem_build_witness_fixture import PNG, write_valid, write_wav

TRIAL = "raw/audio/fixed-tap__trial-1.wav"
DERIVED = "derived/observations.json"
REPORT = "reports/WITNESS-REPORT.md"


def _codes(result: dict) -> set[str]:
    return {item["code"] for item in result["findings"]}


def _not_verified(result: dict) -> None:
    assert "INTEGRITY_VERIFIED" not in result["states"]
    assert result["capture_complete"] is False


def _leftovers(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if ".staging-" in p.name or p.name.endswith(".reservation"))


def _sealed(tmp_path: Path, name: str = "pkg") -> Path:
    package = tmp_path / name
    write_valid(package)
    ingest_package(package)
    assert verify_package(package)["exit_code"] == 0
    return package


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --- 1. destination reservation ---------------------------------------------


def test_two_creators_paused_at_the_former_race_point_yield_one_package(tmp_path: Path, monkeypatch) -> None:
    """Both callers pass the existence check before either reserves."""
    dest = tmp_path / "out" / "witness"
    dest.parent.mkdir()
    barrier = threading.Barrier(2, timeout=30)
    monkeypatch.setattr(create_module, "_after_destination_check", barrier.wait)
    results: dict[str, object] = {}

    def creator(name: str, token: str) -> None:
        try:
            results[name] = create_package(
                dest, "acoustic_guitar", WitnessRepository(tmp_path / f"ledger-{name}"), factory=lambda: token * 32
            )
        except PackageError as exc:
            results[name] = exc

    threads = [threading.Thread(target=creator, args=(n, t)) for n, t in (("a", "a"), ("b", "b"))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    winners = [value for value in results.values() if isinstance(value, str)]
    losers = [value for value in results.values() if isinstance(value, PackageError)]
    assert len(winners) == 1 and len(losers) == 1
    assert "collision" in str(losers[0])
    record = _load(dest / "BUILD-RECORD.json")
    protocol = _load(dest / "TEST-PROTOCOL.json")
    assert record["witness_id"] == winners[0]
    assert protocol["session_id"] == record["session_id"]  # every file from one creator
    assert _leftovers(dest.parent) == []


def test_a_held_reservation_refuses_the_second_creator(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "out" / "witness"
    dest.parent.mkdir()
    holding, release = threading.Event(), threading.Event()

    def hold() -> None:
        holding.set()
        assert release.wait(30)

    monkeypatch.setattr(create_module, "_after_reservation", hold)
    first: dict[str, object] = {}
    thread = threading.Thread(
        target=lambda: first.setdefault("id", create_package(dest, "acoustic_guitar", WitnessRepository(tmp_path / "l1")))
    )
    thread.start()
    assert holding.wait(30)
    monkeypatch.setattr(create_module, "_after_reservation", lambda: None)
    with pytest.raises(PackageError, match="collision"):
        create_package(dest, "acoustic_guitar", WitnessRepository(tmp_path / "l2"))
    release.set()
    thread.join()
    assert _load(dest / "BUILD-RECORD.json")["witness_id"] == first["id"]
    assert _leftovers(dest.parent) == []


def test_a_creator_arriving_after_publication_burns_no_ids(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "out" / "witness"
    dest.parent.mkdir()
    passed, done = threading.Event(), threading.Event()

    def late() -> None:
        if threading.current_thread().name == "late":
            passed.set()
            assert done.wait(30)

    monkeypatch.setattr(create_module, "_after_destination_check", late)
    errors: list[PackageError] = []

    def run_late() -> None:
        try:
            create_package(dest, "acoustic_guitar", WitnessRepository(tmp_path / "late-ledger"), factory=lambda: "c" * 32)
        except PackageError as exc:
            errors.append(exc)

    thread = threading.Thread(target=run_late, name="late")
    thread.start()
    assert passed.wait(30)
    create_package(dest, "acoustic_guitar", WitnessRepository(tmp_path / "first-ledger"))
    done.set()
    thread.join()
    assert len(errors) == 1 and "collision" in str(errors[0])
    assert not (tmp_path / "late-ledger" / "burned").exists()
    assert _leftovers(dest.parent) == []


def test_an_interrupted_creator_leaves_nothing_publishable(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "out" / "witness"
    dest.parent.mkdir()

    def interrupt(staging: Path) -> None:
        assert (staging / "BUILD-RECORD.json").is_file()
        raise KeyboardInterrupt

    monkeypatch.setattr(create_module, "_before_publish", interrupt)
    with pytest.raises(KeyboardInterrupt):
        create_package(dest, "acoustic_guitar", WitnessRepository(tmp_path / "ledger"))
    assert not dest.exists()
    assert _leftovers(dest.parent) == []


def test_a_stale_reservation_fails_closed_with_recovery_instructions(tmp_path: Path) -> None:
    dest = tmp_path / "out" / "witness"
    dest.parent.mkdir()
    stale = create_module.reservation_path(dest)
    stale.mkdir()
    with pytest.raises(PackageError) as caught:
        create_package(dest, "acoustic_guitar", WitnessRepository(tmp_path / "ledger"))
    message = str(caught.value)
    assert str(stale) in message and "remove" in message
    assert stale.is_dir()  # not taken over
    assert not dest.exists()
    stale.rmdir()
    assert create_package(dest, "acoustic_guitar", WitnessRepository(tmp_path / "ledger2"))


# --- B1. prohibited claims anywhere -----------------------------------------


@pytest.mark.parametrize(
    "spelling",
    ["intrinsic_moe", "Intrinsic-MOE", "INTRINSIC MOE", "production_ready", "SCIENTIFICALLY_VALIDATED"],
)
def test_a_prohibited_claim_in_a_measurement_row_is_exit_4(tmp_path: Path, spelling: str) -> None:
    package = tmp_path / "csv"
    write_valid(package)
    path = package / "MEASUREMENTS.csv"
    path.write_text(path.read_text(encoding="utf-8").replace("lower_bout_width", spelling, 1), encoding="utf-8")
    with pytest.raises(PackageError) as caught:
        ingest_package(package)
    assert caught.value.code == 4
    result = verify_package(package)
    assert result["exit_code"] == 4
    assert "INTEGRITY_VERIFIED" not in result["states"]


def test_a_prohibited_value_in_a_record_or_a_raw_json_file_is_exit_4(tmp_path: Path) -> None:
    package = tmp_path / "value"
    write_valid(package)
    record = _load(package / "BUILD-RECORD.json")
    record["uncertainty_notes"] = ["Production-Ready"]
    (package / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    assert verify_package(package)["exit_code"] == 4
    other = tmp_path / "sensor"
    write_valid(other)
    (other / "raw" / "sensors").mkdir(parents=True, exist_ok=True)
    (other / "raw" / "sensors" / "log.json").write_text(json.dumps({"reading": {"species_inference": "x"}}), encoding="utf-8")
    assert verify_package(other)["exit_code"] == 4


def test_prose_that_mentions_a_word_is_not_a_claim(tmp_path: Path) -> None:
    package = tmp_path / "prose"
    write_valid(package)
    record = _load(package / "BUILD-RECORD.json")
    record["uncertainty_notes"] = ["not production ready; intrinsic moe is not estimated here"]
    (package / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    ingest_package(package)
    assert verify_package(package)["exit_code"] == 0


def test_a_prohibited_claim_in_derived_observations_is_exit_4_without_integrity(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    (package / "derived").mkdir(exist_ok=True)
    (package / DERIVED).write_text(json.dumps({"intrinsic_moe": "11.2 GPa", "observations": []}), encoding="utf-8")
    result = verify_package(package)
    assert result["exit_code"] == 4
    assert "INTEGRITY_VERIFIED" not in result["states"]
    with pytest.raises(PackageError) as caught:
        render_package(package)
    assert caught.value.code == 4


# --- B2. one seal per witness, anchored in the ledger ------------------------


def test_deleting_the_manifest_does_not_allow_a_reseal(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    write_wav(package / TRIAL, amplitude=0.9)
    with pytest.raises(PackageError) as replaced:
        ingest_package(package, replace=True)
    assert replaced.value.code == 2
    (package / "WITNESS-MANIFEST.json").unlink()
    (package / "SHA256SUMS").unlink()
    with pytest.raises(PackageError, match="already sealed with different bytes") as resealed:
        ingest_package(package)
    assert resealed.value.code == 2
    _not_verified(verify_package(package))


def test_a_reseal_through_another_ledger_is_detected(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    write_wav(package / TRIAL, amplitude=0.9)
    (package / "WITNESS-MANIFEST.json").unlink()
    (package / "SHA256SUMS").unlink()
    ingest_package(package, repository=WitnessRepository(tmp_path / "elsewhere"))
    result = verify_package(package)
    assert result["exit_code"] == 2
    assert "seal_mismatch" in _codes(result)
    _not_verified(result)


def test_replace_refuses_changed_evidence_even_with_a_fresh_ledger(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    write_wav(package / TRIAL, amplitude=0.9)
    with pytest.raises(PackageError, match="stays immutable") as caught:
        ingest_package(package, replace=True, repository=WitnessRepository(tmp_path / "fresh-ledger"))
    assert caught.value.code == 2


def test_reingesting_identical_evidence_is_idempotent(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    before = (package / "WITNESS-MANIFEST.json").read_bytes()
    ingest_package(package, replace=True)
    assert (package / "WITNESS-MANIFEST.json").read_bytes() == before
    assert verify_package(package)["exit_code"] == 0


@pytest.mark.parametrize("directory", ["derived/audio", "reports"])
def test_recordings_outside_raw_cannot_be_sealed(tmp_path: Path, directory: str) -> None:
    package = tmp_path / "moved"
    write_valid(package)
    target = f"{directory}/fixed-tap__trial-1.wav"
    (package / directory).mkdir(parents=True, exist_ok=True)
    (package / TRIAL).rename(package / target)
    for name in ("TEST-PROTOCOL.json", "MEASUREMENTS.csv"):
        path = package / name
        path.write_text(path.read_text(encoding="utf-8").replace(TRIAL, target), encoding="utf-8")
    with pytest.raises(PackageError, match="outside the evidence layout") as caught:
        ingest_package(package)
    assert caught.value.code == 2
    result = verify_package(package)
    assert {"misplaced_file", "misplaced_evidence"} <= _codes(result)


def test_recordings_must_be_under_raw_audio(tmp_path: Path) -> None:
    package = tmp_path / "sensors"
    write_valid(package)
    target = "raw/sensors/fixed-tap__trial-1.wav"
    (package / "raw/sensors").mkdir(parents=True, exist_ok=True)
    (package / TRIAL).rename(package / target)
    for name in ("TEST-PROTOCOL.json", "MEASUREMENTS.csv"):
        path = package / name
        path.write_text(path.read_text(encoding="utf-8").replace(TRIAL, target), encoding="utf-8")
    result = verify_package(package)
    assert any(
        item["code"] == "misplaced_evidence" and "raw/audio/" in item["message"] for item in result["findings"]
    ), result["findings"]


def test_photographs_outside_raw_images_are_refused(tmp_path: Path) -> None:
    package = tmp_path / "photo"
    write_valid(package)
    (package / "raw" / "placement.png").write_bytes((package / "raw/images/placement.png").read_bytes())
    (package / "raw/images/placement.png").unlink()
    record = _load(package / "BUILD-RECORD.json")
    record["photograph_refs"] = ["raw/images/build-id.png", "raw/placement.png"]
    (package / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    ingest_package(package)
    result = verify_package(package)
    assert "misplaced_evidence" in _codes(result)
    assert result["capture_complete"] is False


def test_an_unrecognized_file_anywhere_is_refused(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    (package / "notes.txt").write_text("extra", encoding="utf-8")
    result = verify_package(package)
    assert result["exit_code"] == 2 and "misplaced_file" in _codes(result)
    _not_verified(result)
    (package / "notes.txt").unlink()
    (package / "derived").mkdir(exist_ok=True)
    (package / "derived" / "plot.png").write_bytes(PNG)
    assert "misplaced_file" in _codes(verify_package(package))


def test_a_duplicate_manifest_entry_is_an_integrity_failure(tmp_path: Path) -> None:
    package = _sealed(tmp_path)
    manifest = _load(package / "WITNESS-MANIFEST.json")
    bogus = dict(manifest["files"][0], sha256="0" * 64, byte_length=1)
    manifest["files"].insert(0, bogus)
    (package / "WITNESS-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    result = verify_package(package)
    assert "duplicate_entry" in _codes(result)
    _not_verified(result)


# --- S2, S3: photographs and recordings --------------------------------------


def test_one_image_cannot_fill_two_photograph_slots(tmp_path: Path) -> None:
    package = tmp_path / "twice"
    write_valid(package)
    (package / "raw/images/placement.png").write_bytes((package / "raw/images/build-id.png").read_bytes())
    result = verify_package(package)
    assert "missing_photograph" in _codes(result)
    case = tmp_path / "case"
    write_valid(case)
    record = _load(case / "BUILD-RECORD.json")
    record["photograph_refs"] = ["raw/images/build-id.png", "raw/images/BUILD-ID.png"]
    (case / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    messages = [item["message"] for item in verify_package(case)["findings"] if item["code"] == "missing_photograph"]
    assert any("listed twice" in message for message in messages) or not (case / "raw/images/BUILD-ID.png").exists()


def test_a_truncated_recording_is_malformed(tmp_path: Path) -> None:
    package = tmp_path / "short"
    write_valid(package)
    path = package / TRIAL
    path.write_bytes(path.read_bytes()[:100])
    result = verify_package(package)
    assert "truncated_audio" in _codes(result)
    assert result["capture_complete"] is False


# --- 2. derived observations --------------------------------------------------


def _analyzed(tmp_path: Path) -> Path:
    package = _sealed(tmp_path)
    analyze_package(package)
    assert verify_package(package)["exit_code"] == 0
    return package


def _mutate_rows(payload: dict) -> None:
    payload["observations"][0] = "not an object"


def _wrong_type(payload: dict) -> None:
    payload["observations"][0]["value"] = 1.5


def _ghost_ref(payload: dict) -> None:
    payload["observations"][0]["raw_evidence_ref"] = "raw/audio/ghost.wav"
    payload["observations"][0]["derived_from"] = ["raw/audio/ghost.wav"]


def _altered_value(payload: dict) -> None:
    row = next(item for item in payload["observations"] if item["quantity"] == "peak_amplitude_ratio")
    row["value"] = "0.999999"


@pytest.mark.parametrize(
    ("name", "write"),
    [
        ("malformed-json", lambda path, payload: path.write_text("{", encoding="utf-8")),
        ("invalid-utf8", lambda path, payload: path.write_bytes(b"\xff\xfe{}")),
        ("top-level-list", lambda path, payload: path.write_text("[]", encoding="utf-8")),
        ("missing-observations", lambda path, payload: path.write_text(json.dumps({k: v for k, v in payload.items() if k != "observations"}), encoding="utf-8")),
        ("non-object-row", lambda path, payload: (_mutate_rows(payload), path.write_text(json.dumps(payload), encoding="utf-8"))),
        ("wrong-type", lambda path, payload: (_wrong_type(payload), path.write_text(json.dumps(payload), encoding="utf-8"))),
        ("nonexistent-ref", lambda path, payload: (_ghost_ref(payload), path.write_text(json.dumps(payload), encoding="utf-8"))),
        ("altered-value", lambda path, payload: (_altered_value(payload), path.write_text(json.dumps(payload), encoding="utf-8"))),
    ],
)
def test_untrusted_derived_observations_fail_closed(tmp_path: Path, name: str, write) -> None:
    package = _analyzed(tmp_path)
    path = package / DERIVED
    write(path, _load(path))
    result = verify_package(package)
    assert result["exit_code"] == 2, result["findings"]
    assert "derived_invalid" in _codes(result)
    _not_verified(result)
    with pytest.raises(PackageError) as caught:
        render_package(package)
    assert caught.value.code == 2
    assert not (package / REPORT).exists()


def test_derived_rows_may_cite_only_the_inputs(tmp_path: Path) -> None:
    package = _analyzed(tmp_path)
    payload = _load(package / DERIVED)
    _ghost_ref(payload)
    (package / DERIVED).write_text(json.dumps(payload), encoding="utf-8")
    result = verify_package(package)
    assert any("cites evidence that is not an input" in item["message"] for item in result["findings"])


def test_derived_observations_from_another_seal_are_refused(tmp_path: Path) -> None:
    package = _analyzed(tmp_path)
    payload = _load(package / DERIVED)
    payload["evidence_manifest_sha256"] = "0" * 64
    (package / DERIVED).write_text(json.dumps(payload), encoding="utf-8")
    result = verify_package(package)
    assert any("different evidence seal" in item["message"] for item in result["findings"])


def test_a_valid_derived_document_renders_and_the_seal_is_untouched(tmp_path: Path) -> None:
    package = _analyzed(tmp_path)
    manifest = (package / "WITNESS-MANIFEST.json").read_bytes()
    text = render_package(package)
    assert "Recomputed from the sealed audio" in text
    assert "peak_amplitude_ratio" in text
    assert (package / "WITNESS-MANIFEST.json").read_bytes() == manifest
    assert verify_package(package)["exit_code"] == 0  # the report is a recognized product


# --- S5. the report shows only what the verifier accepted --------------------


def test_the_report_does_not_list_rows_from_a_rejected_csv(tmp_path: Path) -> None:
    package = tmp_path / "wide"
    write_valid(package)
    path = package / "MEASUREMENTS.csv"
    path.write_text(path.read_text(encoding="utf-8") + ",".join(["x"] * 19) + "\n", encoding="utf-8")
    ingest_package(package)
    result = verify_package(package)
    assert result["exit_code"] == 1 and result["integrity_ok"]
    text = render_package(package)
    assert "MEASUREMENTS.csv was rejected by the verifier" in text
    assert "instrument_mass" not in text
