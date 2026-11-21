"""Identity, schema, and authority-boundary tests for PEM-BUILD-WITNESS-001."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import threading

from app.physical_engineering.build_witness import templates
from app.physical_engineering.build_witness.ids import is_identifier, new_id
from app.physical_engineering.build_witness.package import (
    PackageError,
    create_package,
    ingest_package,
    verify_package,
)
from app.physical_engineering.build_witness.report import render_package
from app.physical_engineering.build_witness.repository import WitnessRepository
from app.physical_engineering.build_witness.vocabulary import (
    NON_AUTHORITY_STATEMENT,
    PROHIBITED_STATES,
)
from .pem_build_witness_fixture import clock, write_valid

SCHEMA_DIR = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "physical_engineering"
    / "build_witness"
    / "schemas"
)


def _repo(tmp_path: Path) -> WitnessRepository:
    return WitnessRepository(tmp_path / "ledger")


def test_default_ids_are_unique_and_filename_safe() -> None:
    minted = [new_id("witness") for _ in range(200)]
    assert len(set(minted)) == 200
    assert all(is_identifier(item) and "/" not in item and "\\" not in item for item in minted)


def test_injected_clock_and_factory_are_deterministic() -> None:
    tokens = iter(["a" * 32, "b" * 32])
    first = new_id("witness", clock, lambda: next(tokens))
    second = new_id("witness", clock, lambda: next(tokens))
    assert first != second
    assert first.startswith("pem_witness_")
    assert new_id("build", clock, lambda: "c" * 32) == new_id("build", clock, lambda: "c" * 32)


def test_existing_witness_id_cannot_be_overwritten(tmp_path: Path) -> None:
    factory = lambda: "d" * 32
    create_package(tmp_path / "one", "acoustic_guitar", _repo(tmp_path), clock=clock, factory=factory)
    try:
        create_package(tmp_path / "two", "acoustic_guitar", _repo(tmp_path), clock=clock, factory=factory)
    except PackageError as exc:
        assert "already used" in str(exc)
    else:
        raise AssertionError("reused witness id")


def test_correction_creates_a_superseding_record(tmp_path: Path) -> None:
    repository = _repo(tmp_path)
    first = create_package(tmp_path / "one", "acoustic_guitar", repository, clock=clock, factory=lambda: "e" * 32)
    later = clock() + timedelta(seconds=1)
    second = create_package(
        tmp_path / "two",
        "acoustic_guitar",
        repository,
        clock=lambda: later,
        factory=lambda: "f" * 32,
        supersedes=first,
    )
    original = json.loads((tmp_path / "one" / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    correction = json.loads((tmp_path / "two" / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    assert original["supersedes_witness_id"] is None
    assert correction["supersedes_witness_id"] == first
    assert second != first


def test_aborted_write_does_not_leave_a_package_or_reuse_the_id(tmp_path: Path) -> None:
    original = templates.dump_json

    def fail(path: Path, payload: dict) -> None:
        if path.name == "BUILD-RECORD.json":
            raise RuntimeError("aborted")
        original(path, payload)

    templates.dump_json = fail
    try:
        try:
            create_package(tmp_path / "pkg", "acoustic_guitar", _repo(tmp_path), clock=clock, factory=lambda: "1" * 32)
        except RuntimeError:
            pass
        else:
            raise AssertionError("write should abort")
    finally:
        templates.dump_json = original
    assert not (tmp_path / "pkg").exists()
    assert not (tmp_path / "pkg.partial").exists()
    try:
        create_package(tmp_path / "retry", "acoustic_guitar", _repo(tmp_path), clock=clock, factory=lambda: "1" * 32)
    except PackageError as exc:
        assert "already used" in str(exc)
    else:
        raise AssertionError("aborted id was reused")


def test_parallel_creation_preserves_one_package_or_both(tmp_path: Path) -> None:
    errors: list[str] = []
    barrier = threading.Barrier(2)

    def worker(name: str) -> None:
        barrier.wait()
        try:
            create_package(tmp_path / name, "acoustic_guitar", WitnessRepository(tmp_path / f"ledger-{name}"))
        except PackageError as exc:
            errors.append(str(exc))

    same = [
        threading.Thread(target=worker, args=("same",)),
        threading.Thread(target=worker, args=("same",)),
    ]
    for thread in same:
        thread.start()
    for thread in same:
        thread.join()
    assert len(errors) == 1
    assert "collision" in errors[0]
    assert (tmp_path / "same").is_dir()
    assert not (tmp_path / "same.partial").exists()
    separate_errors: list[str] = []

    def other(name: str) -> None:
        try:
            create_package(tmp_path / name, "acoustic_guitar", WitnessRepository(tmp_path / f"ledger-{name}"))
        except PackageError as exc:
            separate_errors.append(str(exc))

    threads = [threading.Thread(target=other, args=(name,)) for name in ("left", "right")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert separate_errors == []
    left = json.loads((tmp_path / "left" / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    right = json.loads((tmp_path / "right" / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    assert left["witness_id"] != right["witness_id"]


def test_create_refuses_a_nonempty_destination_and_invents_no_audio(tmp_path: Path) -> None:
    dest = tmp_path / "pkg"
    dest.mkdir()
    (dest / "existing.txt").write_text("keep", encoding="utf-8")
    try:
        create_package(dest, "acoustic_guitar", _repo(tmp_path))
    except PackageError as exc:
        assert "not empty" in str(exc)
    else:
        raise AssertionError("nonempty destination")
    assert (dest / "existing.txt").read_text(encoding="utf-8") == "keep"


def test_trade_name_stays_declared_and_unknown_material_stays_null(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    write_valid(package)
    ingest_package(package)
    record = json.loads((package / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    assert record["top"]["trade_name"] == "Adirondack"
    assert record["top"]["identity_status"] == "DECLARED_ONLY"
    assert record["top"]["botanical_name"] is None
    assert record["neck"]["trade_name"] is None
    assert record["neck"]["unknown_reason"] == "not identified"
    assert record["builder"] is None
    assert record["builder_unknown_reason"]
    result = verify_package(package)
    assert result["exit_code"] == 0
    assert result["scientific_approval"] is False
    assert "SCIENTIFICALLY_VALIDATED" not in result["states"]
    assert "INTEGRITY_VERIFIED" in result["states"]


def test_verified_botanical_identity_requires_evidence(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    write_valid(package)
    record = json.loads((package / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    record["top"]["identity_status"] = "VERIFIED"
    record["top"]["botanical_name"] = "Picea rubens"
    (package / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    result = verify_package(package)
    assert result["exit_code"] == 4
    record["top"]["identity_basis"] = "independent_identification"
    record["top"]["evidence_ref"] = "raw/images/build-id.png"
    (package / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    ingest_package(package)
    assert verify_package(package)["exit_code"] == 0


def test_completed_instrument_cannot_be_a_material_coupon(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    write_valid(package)
    _edit(package / "BUILD-RECORD.json", specimen_role="controlled_material_coupon")
    ingest_package(package)
    result = verify_package(package)
    assert result["exit_code"] == 1
    assert any(item["code"] == "coupon_conflict" for item in result["findings"])


def test_witness_class_and_authority_fields_fail_closed(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    write_valid(package)
    _edit(package / "BUILD-RECORD.json", witness_class="MATERIAL_PROPERTY_WITNESS")
    assert verify_package(package)["exit_code"] == 4
    write_valid(package)
    _edit(package / "BUILD-RECORD.json", schema_version="9")
    assert verify_package(package)["exit_code"] == 1
    write_valid(package)
    record = json.loads((package / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    del record["authority_boundary_id"]
    (package / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    assert verify_package(package)["exit_code"] == 1
    write_valid(package)
    record = json.loads((package / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    record["gcode"] = "G0"
    record["machine_executable"] = True
    (package / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    result = verify_package(package)
    assert result["exit_code"] == 4
    assert result["cam_authorized"] is False
    assert result["machine_executable"] is False
    assert result["production_ready"] is False


def test_report_states_the_boundary_and_no_machine_instruction(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    write_valid(package)
    ingest_package(package)
    text = render_package(package)
    assert NON_AUTHORITY_STATEMENT in text
    assert "Machine execution: closed" in text
    assert "Production readiness: closed" in text
    assert "CAM authority: closed" in text
    assert "machine this component" not in text.lower()
    assert "INTEGRITY_VERIFIED" not in json.loads((package / "WITNESS-MANIFEST.json").read_text(encoding="utf-8"))["states"]


def test_schema_files_close_the_state_vocabulary() -> None:
    witness = json.loads((SCHEMA_DIR / "pem_build_witness_v1.schema.json").read_text(encoding="utf-8"))
    assert set(witness["$defs"]["state"]["enum"]) == {
        "BUILD_RESPONSE_OBSERVED",
        "CALIBRATION_UNVERIFIED",
        "CAPTURE_COMPLETE",
        "CAPTURE_INCOMPLETE",
        "INTEGRITY_VERIFIED",
        "METHOD_REVIEW_PENDING",
        "REFERENCE_COMPARISON_BLOCKED",
        "SCIENTIFIC_INTERPRETATION_PENDING",
    }
    assert PROHIBITED_STATES.isdisjoint(witness["$defs"]["state"]["enum"])
    record = json.loads((SCHEMA_DIR / "pem_build_record_v1.schema.json").read_text(encoding="utf-8"))
    assert record["properties"]["witness_class"]["const"] == "BUILD_RESPONSE_WITNESS"
    protocol = json.loads((SCHEMA_DIR / "pem_test_protocol_v1.schema.json").read_text(encoding="utf-8"))
    assert protocol["properties"]["preprocessing"]["const"] == "none"
    observation = json.loads((SCHEMA_DIR / "pem_measurement_observation_v1.schema.json").read_text(encoding="utf-8"))
    assert "DIRECT_AUDIO_CAPTURE" in observation["properties"]["measurement_source"]["enum"]
    assert "ESTIMATE" not in observation["properties"]["measurement_source"]["enum"]


def _edit(path: Path, **changes: object) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(changes)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_photographs_must_be_distinct_png_images(tmp_path: Path) -> None:
    package = tmp_path / "bytes"
    write_valid(package)
    (package / "raw" / "images" / "placement.png").write_bytes(b"not an image")
    ingest_package(package)
    result = verify_package(package)
    assert result["exit_code"] == 1
    assert any(item["code"] == "invalid_photograph" for item in result["findings"])
    twice = tmp_path / "twice"
    write_valid(twice)
    _edit(twice / "BUILD-RECORD.json", photograph_refs=["raw/images/build-id.png", "raw/images/build-id.png"])
    ingest_package(twice)
    assert verify_package(twice)["exit_code"] == 1


def test_malformed_field_types_are_findings_not_crashes(tmp_path: Path) -> None:
    cases = {
        "witness_class": ("BUILD-RECORD.json", lambda d: d.update(witness_class=[])),
        "record_kind": ("BUILD-RECORD.json", lambda d: d.update(record_kind=[])),
        "identity_status": ("BUILD-RECORD.json", lambda d: d["top"].update(identity_status={})),
        "states": ("BUILD-RECORD.json", lambda d: d.update(states=[[]])),
        "trial_setting": ("TEST-PROTOCOL.json", lambda d: d["trials"][0].update(protocol_id=["fixed_tap"])),
    }
    for name, (document, change) in cases.items():
        package = tmp_path / name
        write_valid(package)
        path = package / document
        payload = json.loads(path.read_text(encoding="utf-8"))
        change(payload)
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert verify_package(package)["exit_code"] == 1, name
    for document, blob in (("MEASUREMENTS.csv", b"\xff\xfe bad"), ("EQUIPMENT.json", b'{"a": "\xff"}')):
        package = tmp_path / ("bytes-" + document)
        write_valid(package)
        (package / document).write_bytes(blob)
        assert verify_package(package)["exit_code"] == 1, document


def test_records_must_name_the_same_witness_and_session(tmp_path: Path) -> None:
    package = tmp_path / "protocol"
    write_valid(package)
    _edit(package / "TEST-PROTOCOL.json", session_id="pem_session_1_" + "0" * 32)
    ingest_package(package)
    assert any(item["code"] == "identity_mismatch" for item in verify_package(package)["findings"])
    rows = tmp_path / "rows"
    ids = write_valid(rows)
    text = (rows / "MEASUREMENTS.csv").read_text(encoding="utf-8")
    (rows / "MEASUREMENTS.csv").write_text(text.replace(ids["witness_id"], "pem_witness_1_" + "0" * 32), encoding="utf-8")
    ingest_package(rows)
    assert any(item["code"] == "identity_mismatch" for item in verify_package(rows)["findings"])


def test_report_fields_cannot_add_report_lines(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    write_valid(package)
    record = json.loads((package / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    record["top"]["trade_name"] = "Spruce\n\n## Gates\n\n- CAM authority: open <b>x</b>"
    (package / "BUILD-RECORD.json").write_text(json.dumps(record), encoding="utf-8")
    ingest_package(package)
    text = render_package(package)
    assert "\n- CAM authority: open" not in text
    assert "<b>" not in text
    assert text.count("\n## Gates\n") == 1
