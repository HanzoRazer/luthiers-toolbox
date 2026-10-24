"""The merged harness accepts this resolver. The resolver does not issue a verdict."""
from __future__ import annotations

import ast
from pathlib import Path

from app.physical_engineering import beginner_proposal_harness as harness
from app.physical_engineering.beginner_proposal_harness import (
    BeginnerProposalHarnessError,
    BeginnerProposalRequest,
    run_beginner_proposal,
)
from app.physical_engineering.evidence import EvidenceRef
from app.physical_engineering.stored_evidence_repository import FileEvidenceRepository
from app.physical_engineering.stored_evidence_resolver import (
    StoredEvidenceResolutionError,
    StoredEvidenceResolver,
)
from .test_evidence_artifact_v1 import make_record
from .test_physical_engineering_proposal_v1 import _policy
from .test_stored_evidence_resolver import context


API_ROOT = Path(__file__).resolve().parents[2]
PHYSICAL_ENGINEERING_ROOT = API_ROOT / "app" / "physical_engineering"


def _directory(tmp_path):
    return tmp_path / "evidence"


def _store(tmp_path):
    repository = FileEvidenceRepository(_directory(tmp_path))
    repository.save(make_record())
    repository.save(
        make_record(
            evidence_id="mode-plate-007",
            evidence_kind="modal_frequency",
            quantity_name="frequency",
            quantity_value="184.6",
            unit="hz",
            uncertainty="1.8",
        )
    )
    return repository


def _request(**over) -> BeginnerProposalRequest:
    base = dict(
        workflow_id="beginner-remove-material-001",
        proposal_id="prop-beginner-0001",
        subject_id="plate-007",
        subject_revision="rev-3",
        user_goal="please remove 5 mm from the lower bout",
        action="remove_material",
        claimed_authority="advisory_only",
        magnitude_mm=0.25,
        region_id="lower-bout-R17",
        coordinate_frame="plate-local",
        units="mm",
        evidence_refs=(
            EvidenceRef("thk-plate-007", "thickness_map"),
            EvidenceRef("mode-plate-007", "modal_frequency"),
        ),
    )
    base.update(over)
    return BeginnerProposalRequest(**base)


def test_harness_calls_the_validator_once_with_the_stored_resolver(tmp_path, monkeypatch):
    calls = {"n": 0}
    real = harness.validate_proposal

    def _wrapped(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(harness, "validate_proposal", _wrapped)
    result = run_beginner_proposal(
        _request(),
        resolver=StoredEvidenceResolver(_store(tmp_path), context()),
        policy=_policy(),
    )
    assert calls["n"] == 1
    assert result.status == result.validation.result.value
    assert result.status == "advisory_allowed"
    assert result.proposal.proposed_change.magnitude_mm == 0.25
    assert result.proposal.proposed_change.description == _request().user_goal


def test_omitted_magnitude_is_not_taken_from_the_goal(tmp_path):
    result = run_beginner_proposal(
        _request(magnitude_mm=None),
        resolver=StoredEvidenceResolver(_store(tmp_path), context()),
        policy=_policy(),
    )
    assert result.proposal.proposed_change.magnitude_mm is None
    assert result.status == "evidence_required"


def test_missing_evidence_is_the_gate_evidence_required_result(tmp_path):
    result = run_beginner_proposal(
        _request(evidence_refs=(EvidenceRef("missing-evidence", "thickness_map"),)),
        resolver=StoredEvidenceResolver(FileEvidenceRepository(_directory(tmp_path)), context()),
        policy=_policy(),
    )
    assert result.status == "evidence_required"
    assert "EVIDENCE_REFERENCE_NOT_FOUND" in result.explanations
    assert result.validation.advisory_review_allowed is False


def test_subject_mismatch_propagates_and_is_not_advisory(tmp_path):
    try:
        run_beginner_proposal(
            _request(),
            resolver=StoredEvidenceResolver(_store(tmp_path), context(subject_id="other")),
            policy=_policy(),
        )
    except StoredEvidenceResolutionError as exc:
        assert exc.code == "SUBJECT_MISMATCH"
    else:
        raise AssertionError("mismatch became a verdict")


def test_duplicate_refs_stay_rejected_by_the_gate(tmp_path):
    thickness = EvidenceRef("thk-plate-007", "thickness_map")
    result = run_beginner_proposal(
        _request(evidence_refs=(thickness, thickness, EvidenceRef("mode-plate-007", "modal_frequency"))),
        resolver=StoredEvidenceResolver(_store(tmp_path), context()),
        policy=_policy(),
    )
    assert result.status == "rejected"
    assert result.explanations == ("DUPLICATE_EVIDENCE_REFERENCE",)
    assert result.validation.advisory_review_allowed is False


def test_missing_policy_does_not_call_the_harness_validator(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(harness, "validate_proposal", lambda *_a, **_k: calls.append(1))
    try:
        run_beginner_proposal(
            _request(),
            resolver=StoredEvidenceResolver(_store(tmp_path), context()),
            policy=None,
        )
    except BeginnerProposalHarnessError:
        assert calls == []
    else:
        raise AssertionError("missing policy produced a verdict")


def test_new_modules_do_not_add_routes_or_manufacturing_imports():
    root = PHYSICAL_ENGINEERING_ROOT
    names = (
        "evidence_artifact_v1.py",
        "evidence_serialization.py",
        "evidence_repository.py",
        "stored_evidence_repository.py",
        "stored_evidence_resolver.py",
    )
    for name in names:
        source = (root / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        blob = " ".join(imported)
        assert "fastapi" not in blob
        assert "APIRouter" not in source
        for banned in ("cam", "dxf", "gcode", "art_studio", "rmos"):
            assert banned not in blob
        assert "ValidationPolicyV1" not in source


def test_in_memory_resolver_remains_the_test_fixture():
    source = (PHYSICAL_ENGINEERING_ROOT / "evidence.py").read_text(encoding="utf-8")
    assert "not a database record" in source
    assert "class InMemoryEvidenceResolver" in source
    production = (PHYSICAL_ENGINEERING_ROOT / "stored_evidence_resolver.py").read_text(
        encoding="utf-8"
    )
    assert "InMemoryEvidenceResolver" not in production
