"""
Tests for Runtime Semantic Consumption Ledger (Dev Order 7O)

Tests cover:
  - Ledger entry creation from 7N reports
  - Linear chain lineage
  - Deterministic hashing
  - Drift type mapping
  - Escalation thresholds
  - Replay continuity
  - Replay integrity validation
  - Invariant enforcement
  - REST endpoints

7O invariants tested:
  - immutable = true (always)
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.cam.runtime_semantic_consumption import (
    RuntimeSemanticConsumer,
    ConsumptionDisciplineReport,
    TermConsumptionMismatch,
    ProhibitedAuthorityClaim,
    RuntimeReinterpretationRisk,
    register_runtime_semantic_consumer,
    clear_runtime_semantic_consumers_for_tests,
    _seed_initial_consumers,
)
from app.cam.runtime_consumption_policy import (
    generate_consumption_discipline_report,
    clear_reports_for_tests,
)
from app.cam.runtime_semantic_consumption_ledger import (
    RuntimeSemanticConsumptionLedgerEntry,
    RUNTIME_DRIFT_TYPES,
    get_ledger_entry,
    list_ledger_entries,
    list_ledger_entries_for_consumer,
    get_latest_ledger_entry_for_consumer,
    clear_ledger_for_tests,
    create_ledger_entry_from_report,
    map_drift_types_from_report,
    compute_ledger_entry_hash,
)
from app.cam.runtime_drift_escalation_engine import (
    RuntimeDriftEscalationEvaluation,
    evaluate_runtime_drift_escalation,
    list_escalation_evaluations,
    clear_escalations_for_tests,
    analyze_drift_patterns,
    classify_escalation_severity,
)
from app.cam.runtime_semantic_replay import (
    RuntimeSemanticReplayResult,
    replay_runtime_semantic_lineage,
    clear_replays_for_tests,
    verify_parent_hash_continuity,
    verify_invariants,
    detect_drift_progression,
)


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_all_registries():
    """Reset all registries before each test."""
    clear_runtime_semantic_consumers_for_tests()
    clear_reports_for_tests()
    clear_ledger_for_tests()
    clear_escalations_for_tests()
    clear_replays_for_tests()
    _seed_initial_consumers()
    yield


@pytest.fixture
def sample_report():
    """Generate a sample 7N report for testing."""
    return generate_consumption_discipline_report("cam_runtime")


# -----------------------------------------------------------------------------
# Ledger Entry Model Tests
# -----------------------------------------------------------------------------

class TestRuntimeSemanticConsumptionLedgerEntry:
    """Tests for ledger entry model."""

    def test_ledger_entry_creation(self, sample_report):
        """Can create ledger entry from report."""
        entry = create_ledger_entry_from_report(sample_report)
        assert entry.consumer_id == "cam_runtime"
        assert entry.immutable is True
        assert entry.execution_authorized is False
        assert entry.machine_output_allowed is False

    def test_immutable_invariant_enforced(self):
        """Cannot set immutable to False."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeSemanticConsumptionLedgerEntry(
                ledger_entry_id="test",
                consumer_id="test",
                parent_ledger_hashes=[],
                consumption_report_hash="abc",
                ontology_alignment_score=1.0,
                ontology_consumption_valid=True,
                deterministic_ledger_hash="def",
                immutable=False,
            )
        assert "7O invariant violation" in str(exc_info.value)

    def test_execution_authorized_invariant(self):
        """Cannot set execution_authorized to True."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeSemanticConsumptionLedgerEntry(
                ledger_entry_id="test",
                consumer_id="test",
                parent_ledger_hashes=[],
                consumption_report_hash="abc",
                ontology_alignment_score=1.0,
                ontology_consumption_valid=True,
                deterministic_ledger_hash="def",
                execution_authorized=True,
            )
        assert "7O invariant violation" in str(exc_info.value)

    def test_machine_output_invariant(self):
        """Cannot set machine_output_allowed to True."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeSemanticConsumptionLedgerEntry(
                ledger_entry_id="test",
                consumer_id="test",
                parent_ledger_hashes=[],
                consumption_report_hash="abc",
                ontology_alignment_score=1.0,
                ontology_consumption_valid=True,
                deterministic_ledger_hash="def",
                machine_output_allowed=True,
            )
        assert "7O invariant violation" in str(exc_info.value)


# -----------------------------------------------------------------------------
# Ledger Index Tests
# -----------------------------------------------------------------------------

class TestLedgerIndex:
    """Tests for ledger indexing."""

    def test_store_and_retrieve_entry(self, sample_report):
        """Can store and retrieve ledger entry."""
        entry = create_ledger_entry_from_report(sample_report)
        retrieved = get_ledger_entry(entry.ledger_entry_id)
        assert retrieved is not None
        assert retrieved.ledger_entry_id == entry.ledger_entry_id

    def test_list_ledger_entries(self, sample_report):
        """Can list all ledger entries."""
        create_ledger_entry_from_report(sample_report)
        entries = list_ledger_entries()
        assert len(entries) >= 1

    def test_list_entries_for_consumer(self, sample_report):
        """Can list entries for specific consumer."""
        create_ledger_entry_from_report(sample_report)
        entries = list_ledger_entries_for_consumer("cam_runtime")
        assert len(entries) >= 1
        assert all(e.consumer_id == "cam_runtime" for e in entries)

    def test_get_latest_entry_for_consumer(self, sample_report):
        """Can get latest entry for consumer."""
        entry1 = create_ledger_entry_from_report(sample_report)
        entry2 = create_ledger_entry_from_report(sample_report)
        latest = get_latest_ledger_entry_for_consumer("cam_runtime")
        assert latest.ledger_entry_id == entry2.ledger_entry_id


# -----------------------------------------------------------------------------
# Linear Chain Tests
# -----------------------------------------------------------------------------

class TestLinearChain:
    """Tests for linear chain lineage."""

    def test_first_entry_empty_parents(self, sample_report):
        """First entry has empty parent_ledger_hashes."""
        entry = create_ledger_entry_from_report(sample_report)
        assert entry.parent_ledger_hashes == []

    def test_second_entry_links_to_first(self, sample_report):
        """Second entry links to first via parent hash."""
        entry1 = create_ledger_entry_from_report(sample_report)
        entry2 = create_ledger_entry_from_report(sample_report)
        assert entry1.deterministic_ledger_hash in entry2.parent_ledger_hashes

    def test_chain_continuity(self, sample_report):
        """Chain maintains continuity across multiple entries."""
        entry1 = create_ledger_entry_from_report(sample_report)
        entry2 = create_ledger_entry_from_report(sample_report)
        entry3 = create_ledger_entry_from_report(sample_report)

        assert entry1.parent_ledger_hashes == []
        assert entry1.deterministic_ledger_hash in entry2.parent_ledger_hashes
        assert entry2.deterministic_ledger_hash in entry3.parent_ledger_hashes


# -----------------------------------------------------------------------------
# Deterministic Hash Tests
# -----------------------------------------------------------------------------

class TestDeterministicHash:
    """Tests for deterministic hashing."""

    def test_same_input_same_hash(self):
        """Same input produces same hash."""
        hash1 = compute_ledger_entry_hash(
            consumer_id="test",
            parent_ledger_hashes=[],
            consumption_report_hash="abc",
            detected_drift_types=["a", "b"],
            ontology_consumption_valid=True,
            ontology_alignment_score=1.0,
            escalation_recommended=False,
            escalation_reason_codes=[],
            reinterpretation_risk_count=0,
            authority_violation_count=0,
        )
        hash2 = compute_ledger_entry_hash(
            consumer_id="test",
            parent_ledger_hashes=[],
            consumption_report_hash="abc",
            detected_drift_types=["a", "b"],
            ontology_consumption_valid=True,
            ontology_alignment_score=1.0,
            escalation_recommended=False,
            escalation_reason_codes=[],
            reinterpretation_risk_count=0,
            authority_violation_count=0,
        )
        assert hash1 == hash2

    def test_different_consumer_different_hash(self):
        """Different consumer produces different hash."""
        hash1 = compute_ledger_entry_hash(
            consumer_id="test1",
            parent_ledger_hashes=[],
            consumption_report_hash="abc",
            detected_drift_types=[],
            ontology_consumption_valid=True,
            ontology_alignment_score=1.0,
            escalation_recommended=False,
            escalation_reason_codes=[],
            reinterpretation_risk_count=0,
            authority_violation_count=0,
        )
        hash2 = compute_ledger_entry_hash(
            consumer_id="test2",
            parent_ledger_hashes=[],
            consumption_report_hash="abc",
            detected_drift_types=[],
            ontology_consumption_valid=True,
            ontology_alignment_score=1.0,
            escalation_recommended=False,
            escalation_reason_codes=[],
            reinterpretation_risk_count=0,
            authority_violation_count=0,
        )
        assert hash1 != hash2


# -----------------------------------------------------------------------------
# Drift Type Mapping Tests
# -----------------------------------------------------------------------------

class TestDriftTypeMapping:
    """Tests for drift type mapping from 7N reports."""

    def test_canonical_drift_types_defined(self):
        """Canonical drift types are defined."""
        assert "missing_term_dependency" in RUNTIME_DRIFT_TYPES
        assert "domain_reinterpretation" in RUNTIME_DRIFT_TYPES
        assert "lifecycle_reinterpretation" in RUNTIME_DRIFT_TYPES
        assert "authority_claim_attempt" in RUNTIME_DRIFT_TYPES
        assert "execution_semantic_leakage" in RUNTIME_DRIFT_TYPES
        assert "machine_output_semantic_leakage" in RUNTIME_DRIFT_TYPES
        assert "ontology_mutation_attempt" in RUNTIME_DRIFT_TYPES

    def test_missing_terms_maps_to_drift(self):
        """Missing terms map to missing_term_dependency."""
        report = ConsumptionDisciplineReport(
            report_id="test",
            consumer_id="test",
            consumed_terms=["missing"],
            missing_terms=["missing"],
            term_mismatches=[],
            prohibited_authority_claims=[],
            runtime_reinterpretation_risks=[],
            consumption_alignment_score=0.85,
            discipline_valid=False,
            deterministic_report_hash="abc",
        )
        drift_types = map_drift_types_from_report(report)
        assert "missing_term_dependency" in drift_types


# -----------------------------------------------------------------------------
# Escalation Engine Tests
# -----------------------------------------------------------------------------

class TestEscalationEngine:
    """Tests for drift escalation engine."""

    def test_evaluate_escalation(self, sample_report):
        """Can evaluate escalation for consumer."""
        create_ledger_entry_from_report(sample_report)
        evaluation = evaluate_runtime_drift_escalation("cam_runtime")
        assert evaluation.consumer_id == "cam_runtime"
        assert evaluation.execution_authorized is False
        assert evaluation.machine_output_allowed is False

    def test_no_entries_no_escalation(self):
        """Consumer with no entries has no escalation."""
        evaluation = evaluate_runtime_drift_escalation("cam_runtime")
        assert evaluation.ledger_entries_evaluated == 0
        assert evaluation.escalation_severity == "none"

    def test_single_drift_low_severity(self, sample_report):
        """Single drift occurrence is low severity."""
        # Seeded consumers should have valid reports with no drift
        create_ledger_entry_from_report(sample_report)
        evaluation = evaluate_runtime_drift_escalation("cam_runtime")
        # cam_runtime consumes valid terms, so severity should be none or low
        assert evaluation.escalation_severity in ("none", "low")

    def test_escalation_stored(self, sample_report):
        """Escalation evaluations are stored."""
        create_ledger_entry_from_report(sample_report)
        evaluate_runtime_drift_escalation("cam_runtime")
        evals = list_escalation_evaluations()
        assert len(evals) >= 1


# -----------------------------------------------------------------------------
# Escalation Threshold Tests
# -----------------------------------------------------------------------------

class TestEscalationThresholds:
    """Tests for escalation severity thresholds."""

    def test_classify_no_entries_none(self):
        """No entries = none severity."""
        severity = classify_escalation_severity(
            entries=[],
            repeated_drift_patterns=[],
            repeated_authority_violations=[],
            drift_counts={},
        )
        assert severity == "none"

    def test_repeated_authority_is_critical(self):
        """Repeated authority violations = critical."""
        severity = classify_escalation_severity(
            entries=[],
            repeated_drift_patterns=[],
            repeated_authority_violations=["authority_claim_attempt"],
            drift_counts={},
        )
        assert severity == "critical"


# -----------------------------------------------------------------------------
# Replay Tests
# -----------------------------------------------------------------------------

class TestReplay:
    """Tests for runtime semantic replay."""

    def test_replay_empty_chain(self):
        """Replay works for consumer with no entries."""
        result = replay_runtime_semantic_lineage("cam_runtime")
        assert result.replay_entry_count == 0
        assert result.replay_integrity_valid is True
        assert result.immutable is True

    def test_replay_single_entry(self, sample_report):
        """Replay works for single entry."""
        create_ledger_entry_from_report(sample_report)
        result = replay_runtime_semantic_lineage("cam_runtime")
        assert result.replay_entry_count == 1
        assert result.replay_integrity_valid is True

    def test_replay_chain_integrity(self, sample_report):
        """Replay validates chain integrity."""
        create_ledger_entry_from_report(sample_report)
        create_ledger_entry_from_report(sample_report)
        create_ledger_entry_from_report(sample_report)
        result = replay_runtime_semantic_lineage("cam_runtime")
        assert result.replay_entry_count == 3
        assert result.replay_integrity_valid is True
        assert len(result.broken_links) == 0

    def test_verify_parent_hash_continuity(self, sample_report):
        """Parent hash continuity verification works."""
        entry1 = create_ledger_entry_from_report(sample_report)
        entry2 = create_ledger_entry_from_report(sample_report)
        entries = [entry1, entry2]
        valid, broken = verify_parent_hash_continuity(entries)
        assert valid is True
        assert broken == []


# -----------------------------------------------------------------------------
# Replay Invariant Tests
# -----------------------------------------------------------------------------

class TestReplayInvariants:
    """Tests for replay invariant verification."""

    def test_verify_invariants_valid(self, sample_report):
        """Valid entries pass invariant verification."""
        create_ledger_entry_from_report(sample_report)
        entries = list_ledger_entries_for_consumer("cam_runtime")
        valid, violations = verify_invariants(entries)
        assert valid is True
        assert violations == []

    def test_replay_result_immutable(self):
        """Replay result is immutable."""
        result = replay_runtime_semantic_lineage("cam_runtime")
        assert result.immutable is True


# -----------------------------------------------------------------------------
# Router Endpoint Tests
# -----------------------------------------------------------------------------

class TestLedgerEndpoints:
    """Tests for REST endpoints."""

    def test_get_policy(self):
        """GET /api/cam/runtime-ledger/policy returns policy."""
        response = client.get("/api/cam/runtime-ledger/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["dev_order"] == "7O"
        assert data["execution_authorized"] is False

    def test_list_entries(self):
        """GET /api/cam/runtime-ledger/entries returns entries."""
        # Generate some data first
        report = generate_consumption_discipline_report("cam_runtime")
        create_ledger_entry_from_report(report)

        response = client.get("/api/cam/runtime-ledger/entries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_entry(self):
        """GET /api/cam/runtime-ledger/entries/{id} returns entry."""
        report = generate_consumption_discipline_report("cam_runtime")
        entry = create_ledger_entry_from_report(report)

        response = client.get(
            f"/api/cam/runtime-ledger/entries/{entry.ledger_entry_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ledger_entry_id"] == entry.ledger_entry_id

    def test_get_entry_not_found(self):
        """GET returns 404 for unknown entry."""
        response = client.get("/api/cam/runtime-ledger/entries/nonexistent")
        assert response.status_code == 404

    def test_get_consumer_lineage(self):
        """GET /api/cam/runtime-ledger/consumer/{id} returns lineage."""
        report = generate_consumption_discipline_report("cam_runtime")
        create_ledger_entry_from_report(report)

        response = client.get("/api/cam/runtime-ledger/consumer/cam_runtime")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_record_ledger_entry(self):
        """POST /api/cam/runtime-ledger/record creates entry."""
        # Generate a report first
        generate_consumption_discipline_report("cam_runtime")

        response = client.post(
            "/api/cam/runtime-ledger/record",
            json={"consumer_id": "cam_runtime"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["consumer_id"] == "cam_runtime"

    def test_evaluate_escalation(self):
        """POST /api/cam/runtime-ledger/escalation/{id} evaluates."""
        report = generate_consumption_discipline_report("cam_runtime")
        create_ledger_entry_from_report(report)

        response = client.post(
            "/api/cam/runtime-ledger/escalation/cam_runtime"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["consumer_id"] == "cam_runtime"
        assert data["execution_authorized"] is False

    def test_replay_lineage(self):
        """POST /api/cam/runtime-ledger/replay/{id} replays."""
        report = generate_consumption_discipline_report("cam_runtime")
        create_ledger_entry_from_report(report)

        response = client.post(
            "/api/cam/runtime-ledger/replay/cam_runtime"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["consumer_id"] == "cam_runtime"
        assert data["immutable"] is True

    def test_get_ci_summary(self):
        """GET /api/cam/runtime-ledger/ci returns CI summary."""
        response = client.get("/api/cam/runtime-ledger/ci")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["pass", "warn", "fail"]
        assert data["execution_authorized"] is False


# -----------------------------------------------------------------------------
# Progression Detection Tests
# -----------------------------------------------------------------------------

class TestProgressionDetection:
    """Tests for drift and escalation progression detection."""

    def test_no_progression_single_entry(self, sample_report):
        """Single entry has no progression."""
        entry = create_ledger_entry_from_report(sample_report)
        detected = detect_drift_progression([entry])
        assert detected is False

    def test_drift_progression_detected(self):
        """Drift progression is detected when drift increases."""
        entry1 = RuntimeSemanticConsumptionLedgerEntry(
            ledger_entry_id="e1",
            consumer_id="test",
            parent_ledger_hashes=[],
            consumption_report_hash="h1",
            ontology_alignment_score=1.0,
            ontology_consumption_valid=True,
            detected_drift_types=[],
            deterministic_ledger_hash="hash1",
        )
        entry2 = RuntimeSemanticConsumptionLedgerEntry(
            ledger_entry_id="e2",
            consumer_id="test",
            parent_ledger_hashes=["hash1"],
            consumption_report_hash="h2",
            ontology_alignment_score=0.9,
            ontology_consumption_valid=True,
            detected_drift_types=["missing_term_dependency"],
            deterministic_ledger_hash="hash2",
        )
        detected = detect_drift_progression([entry1, entry2])
        assert detected is True
