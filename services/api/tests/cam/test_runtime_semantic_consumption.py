"""
Tests for Runtime Semantic Consumption Discipline (Dev Order 7N)

Tests cover:
  - Consumer registration and retrieval
  - Consumption validation against 7M registry
  - Prohibited authority claim detection
  - Reinterpretation risk detection
  - Alignment score calculation
  - Deterministic hash verification
  - CI summary generation
  - REST endpoints

7N invariants tested:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)
  - Consumer invariants (no authority claims)
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.cam.runtime_semantic_consumption import (
    RuntimeSemanticConsumer,
    RuntimeSemanticConsumerSummary,
    ConsumptionDisciplineReport,
    TermConsumptionMismatch,
    ProhibitedAuthorityClaim,
    RuntimeReinterpretationRisk,
    register_runtime_semantic_consumer,
    get_runtime_semantic_consumer,
    list_runtime_semantic_consumers,
    list_consumers_for_domain,
    list_consumer_domains,
    to_consumer_summary,
    clear_runtime_semantic_consumers_for_tests,
    validate_consumed_terms,
    detect_prohibited_authority_claims,
    detect_reinterpretation_risks,
    _seed_initial_consumers,
)
from app.cam.runtime_consumption_policy import (
    ConsumptionPolicyResponse,
    ConsumptionCISummary,
    SEVERITY_PENALTIES,
    calculate_consumption_alignment_score,
    is_discipline_valid,
    compute_consumption_report_hash,
    generate_consumption_discipline_report,
    generate_all_consumer_reports,
    generate_ci_summary,
    list_reports,
    get_latest_report,
    clear_reports_for_tests,
)


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_registries():
    """Reset registries before each test."""
    clear_runtime_semantic_consumers_for_tests()
    clear_reports_for_tests()
    _seed_initial_consumers()
    yield


@pytest.fixture
def test_consumer():
    """Create a test consumer."""
    return RuntimeSemanticConsumer(
        consumer_id="test_consumer",
        consumer_name="Test Consumer",
        consumer_domain="Test",
        consumed_terms=["translator", "intent"],
        consumption_purpose="Testing consumption discipline",
    )


@pytest.fixture
def consumer_with_missing_terms():
    """Consumer that consumes non-existent terms."""
    return RuntimeSemanticConsumer(
        consumer_id="missing_terms_consumer",
        consumer_name="Missing Terms Consumer",
        consumer_domain="Test",
        consumed_terms=["nonexistent_term", "another_fake_term"],
        consumption_purpose="Testing missing term detection",
    )


# -----------------------------------------------------------------------------
# Consumer Model Tests
# -----------------------------------------------------------------------------

class TestRuntimeSemanticConsumer:
    """Tests for RuntimeSemanticConsumer model."""

    def test_consumer_creation(self, test_consumer):
        """Consumer can be created with valid data."""
        assert test_consumer.consumer_id == "test_consumer"
        assert test_consumer.consumer_name == "Test Consumer"
        assert len(test_consumer.consumed_terms) == 2

    def test_consumer_invariants_enforced(self):
        """Consumer invariants are always false."""
        consumer = RuntimeSemanticConsumer(
            consumer_id="invariant_test",
            consumer_name="Invariant Test",
            consumer_domain="Test",
            consumed_terms=[],
            consumption_purpose="Testing invariants",
        )
        assert consumer.declared_semantic_authority is False
        assert consumer.may_register_terms is False
        assert consumer.may_mutate_ontology is False
        assert consumer.may_define_lifecycle is False
        assert consumer.may_execute_runtime is False
        assert consumer.may_generate_machine_output is False

    def test_declared_semantic_authority_rejected(self):
        """Cannot set declared_semantic_authority to True."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeSemanticConsumer(
                consumer_id="bad_consumer",
                consumer_name="Bad Consumer",
                consumer_domain="Test",
                consumed_terms=[],
                consumption_purpose="Testing",
                declared_semantic_authority=True,
            )
        assert "7N invariant violation" in str(exc_info.value)

    def test_may_register_terms_rejected(self):
        """Cannot set may_register_terms to True."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeSemanticConsumer(
                consumer_id="bad_consumer",
                consumer_name="Bad Consumer",
                consumer_domain="Test",
                consumed_terms=[],
                consumption_purpose="Testing",
                may_register_terms=True,
            )
        assert "7N invariant violation" in str(exc_info.value)

    def test_may_mutate_ontology_rejected(self):
        """Cannot set may_mutate_ontology to True."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeSemanticConsumer(
                consumer_id="bad_consumer",
                consumer_name="Bad Consumer",
                consumer_domain="Test",
                consumed_terms=[],
                consumption_purpose="Testing",
                may_mutate_ontology=True,
            )
        assert "7N invariant violation" in str(exc_info.value)

    def test_may_execute_runtime_rejected(self):
        """Cannot set may_execute_runtime to True."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeSemanticConsumer(
                consumer_id="bad_consumer",
                consumer_name="Bad Consumer",
                consumer_domain="Test",
                consumed_terms=[],
                consumption_purpose="Testing",
                may_execute_runtime=True,
            )
        assert "7N invariant violation" in str(exc_info.value)


# -----------------------------------------------------------------------------
# Consumer Registry Tests
# -----------------------------------------------------------------------------

class TestConsumerRegistry:
    """Tests for consumer registration and retrieval."""

    def test_initial_consumers_seeded(self):
        """Initial 5 consumers are seeded at module load."""
        consumers = list_runtime_semantic_consumers()
        assert len(consumers) >= 5

        consumer_ids = {c.consumer_id for c in consumers}
        assert "cam_runtime" in consumer_ids
        assert "translator_runtime" in consumer_ids
        assert "morphology_runtime" in consumer_ids
        assert "execution_scheduler" in consumer_ids
        assert "validation_runtime" in consumer_ids

    def test_register_consumer(self, test_consumer):
        """Can register a new consumer."""
        register_runtime_semantic_consumer(test_consumer)
        retrieved = get_runtime_semantic_consumer("test_consumer")
        assert retrieved is not None
        assert retrieved.consumer_id == "test_consumer"

    def test_register_duplicate_rejected(self, test_consumer):
        """Cannot register consumer with duplicate ID."""
        register_runtime_semantic_consumer(test_consumer)
        with pytest.raises(ValueError) as exc_info:
            register_runtime_semantic_consumer(test_consumer)
        assert "already registered" in str(exc_info.value)

    def test_get_nonexistent_consumer(self):
        """Getting nonexistent consumer returns None."""
        result = get_runtime_semantic_consumer("nonexistent")
        assert result is None

    def test_list_consumers_for_domain(self):
        """Can list consumers for a specific domain."""
        cam_consumers = list_consumers_for_domain("CAM")
        assert len(cam_consumers) >= 1
        assert all(c.consumer_domain == "CAM" for c in cam_consumers)

    def test_list_consumer_domains(self):
        """Can list all consumer domains."""
        domains = list_consumer_domains()
        assert "CAM" in domains
        assert "MRP" in domains
        assert "Governance" in domains

    def test_to_consumer_summary(self, test_consumer):
        """Can convert consumer to summary."""
        register_runtime_semantic_consumer(test_consumer)
        summary = to_consumer_summary(test_consumer)
        assert isinstance(summary, RuntimeSemanticConsumerSummary)
        assert summary.consumer_id == "test_consumer"
        assert summary.consumed_term_count == 2


# -----------------------------------------------------------------------------
# Validation Tests
# -----------------------------------------------------------------------------

class TestConsumptionValidation:
    """Tests for consumption validation."""

    def test_validate_valid_terms(self):
        """Consumer with valid terms passes validation."""
        consumer = get_runtime_semantic_consumer("cam_runtime")
        missing, mismatches = validate_consumed_terms(consumer)
        # CAM runtime consumes translator, intent, etc. which exist in 7M
        assert len(missing) == 0

    def test_validate_missing_terms(self, consumer_with_missing_terms):
        """Consumer with missing terms detected."""
        register_runtime_semantic_consumer(consumer_with_missing_terms)
        missing, mismatches = validate_consumed_terms(consumer_with_missing_terms)
        assert len(missing) == 2
        assert "nonexistent_term" in missing
        assert "another_fake_term" in missing
        assert len(mismatches) == 2

    def test_detect_prohibited_claims(self):
        """Prohibited authority claims detection works."""
        consumer = get_runtime_semantic_consumer("cam_runtime")
        # Seeded consumers have no prohibited claims
        claims = detect_prohibited_authority_claims(consumer)
        assert len(claims) == 0

    def test_detect_reinterpretation_risks(self):
        """Reinterpretation risk detection works."""
        consumer = get_runtime_semantic_consumer("cam_runtime")
        risks = detect_reinterpretation_risks(consumer)
        # May or may not have risks depending on term names
        assert isinstance(risks, list)


# -----------------------------------------------------------------------------
# Alignment Score Tests
# -----------------------------------------------------------------------------

class TestAlignmentScore:
    """Tests for alignment score calculation."""

    def test_perfect_score(self):
        """No violations gives perfect score."""
        score = calculate_consumption_alignment_score(
            missing_terms=[],
            mismatches=[],
            prohibited_claims=[],
            reinterpretation_risks=[],
        )
        assert score == 1.0

    def test_missing_terms_penalty(self):
        """Missing terms reduce score."""
        score = calculate_consumption_alignment_score(
            missing_terms=["term1", "term2"],
            mismatches=[],
            prohibited_claims=[],
            reinterpretation_risks=[],
        )
        # 2 missing terms * 15 (high) = 30 penalty
        # (100 - 30) / 100 = 0.7
        assert score == 0.7

    def test_prohibited_claims_severe_penalty(self):
        """Prohibited claims cause severe penalty."""
        claims = [
            ProhibitedAuthorityClaim(
                consumer_id="test",
                operation="mutate_ontology",
                description="Test",
                severity="critical",
            )
        ]
        score = calculate_consumption_alignment_score(
            missing_terms=[],
            mismatches=[],
            prohibited_claims=claims,
            reinterpretation_risks=[],
        )
        # 1 critical = 30 penalty
        assert score == 0.7

    def test_severity_penalties_match_spec(self):
        """Severity penalties match specification."""
        assert SEVERITY_PENALTIES["low"] == 2
        assert SEVERITY_PENALTIES["medium"] == 5
        assert SEVERITY_PENALTIES["high"] == 15
        assert SEVERITY_PENALTIES["critical"] == 30


# -----------------------------------------------------------------------------
# Discipline Validity Tests
# -----------------------------------------------------------------------------

class TestDisciplineValidity:
    """Tests for discipline validity determination."""

    def test_valid_discipline(self):
        """No violations means valid discipline."""
        valid = is_discipline_valid(
            missing_terms=[],
            prohibited_claims=[],
            mismatches=[],
        )
        assert valid is True

    def test_missing_terms_invalid(self):
        """Missing terms make discipline invalid."""
        valid = is_discipline_valid(
            missing_terms=["missing"],
            prohibited_claims=[],
            mismatches=[],
        )
        assert valid is False

    def test_prohibited_claims_invalid(self):
        """Prohibited claims make discipline invalid."""
        claims = [
            ProhibitedAuthorityClaim(
                consumer_id="test",
                operation="register_term",
                description="Test",
                severity="critical",
            )
        ]
        valid = is_discipline_valid(
            missing_terms=[],
            prohibited_claims=claims,
            mismatches=[],
        )
        assert valid is False


# -----------------------------------------------------------------------------
# Report Tests
# -----------------------------------------------------------------------------

class TestConsumptionReports:
    """Tests for consumption discipline reports."""

    def test_generate_report(self):
        """Can generate consumption discipline report."""
        report = generate_consumption_discipline_report("cam_runtime")
        assert isinstance(report, ConsumptionDisciplineReport)
        assert report.consumer_id == "cam_runtime"
        assert report.execution_authorized is False
        assert report.machine_output_allowed is False

    def test_report_invariants_enforced(self):
        """Report invariants are always false."""
        report = generate_consumption_discipline_report("cam_runtime")
        assert report.execution_authorized is False
        assert report.machine_output_allowed is False

    def test_generate_report_nonexistent_consumer(self):
        """Generating report for nonexistent consumer raises error."""
        with pytest.raises(ValueError) as exc_info:
            generate_consumption_discipline_report("nonexistent")
        assert "not found" in str(exc_info.value)

    def test_generate_all_reports(self):
        """Can generate reports for all consumers."""
        reports = generate_all_consumer_reports()
        assert len(reports) >= 5  # At least the 5 seeded consumers

    def test_report_stored(self):
        """Generated reports are stored."""
        generate_consumption_discipline_report("cam_runtime")
        reports = list_reports()
        assert len(reports) >= 1

    def test_get_latest_report(self):
        """Can get latest report."""
        generate_consumption_discipline_report("cam_runtime")
        generate_consumption_discipline_report("translator_runtime")
        latest = get_latest_report()
        assert latest is not None


# -----------------------------------------------------------------------------
# Deterministic Hash Tests
# -----------------------------------------------------------------------------

class TestDeterministicHash:
    """Tests for deterministic hash computation."""

    def test_same_input_same_hash(self):
        """Same input produces same hash."""
        hash1 = compute_consumption_report_hash(
            consumer_id="test",
            consumed_terms=["a", "b"],
            missing_terms=[],
            mismatches=[],
            prohibited_claims=[],
            reinterpretation_risks=[],
            alignment_score=1.0,
            discipline_valid=True,
        )
        hash2 = compute_consumption_report_hash(
            consumer_id="test",
            consumed_terms=["a", "b"],
            missing_terms=[],
            mismatches=[],
            prohibited_claims=[],
            reinterpretation_risks=[],
            alignment_score=1.0,
            discipline_valid=True,
        )
        assert hash1 == hash2

    def test_different_consumer_different_hash(self):
        """Different consumer ID produces different hash."""
        hash1 = compute_consumption_report_hash(
            consumer_id="test1",
            consumed_terms=[],
            missing_terms=[],
            mismatches=[],
            prohibited_claims=[],
            reinterpretation_risks=[],
            alignment_score=1.0,
            discipline_valid=True,
        )
        hash2 = compute_consumption_report_hash(
            consumer_id="test2",
            consumed_terms=[],
            missing_terms=[],
            mismatches=[],
            prohibited_claims=[],
            reinterpretation_risks=[],
            alignment_score=1.0,
            discipline_valid=True,
        )
        assert hash1 != hash2

    def test_term_order_irrelevant(self):
        """Term order doesn't affect hash (sorted internally)."""
        hash1 = compute_consumption_report_hash(
            consumer_id="test",
            consumed_terms=["a", "b", "c"],
            missing_terms=[],
            mismatches=[],
            prohibited_claims=[],
            reinterpretation_risks=[],
            alignment_score=1.0,
            discipline_valid=True,
        )
        hash2 = compute_consumption_report_hash(
            consumer_id="test",
            consumed_terms=["c", "a", "b"],
            missing_terms=[],
            mismatches=[],
            prohibited_claims=[],
            reinterpretation_risks=[],
            alignment_score=1.0,
            discipline_valid=True,
        )
        assert hash1 == hash2


# -----------------------------------------------------------------------------
# CI Summary Tests
# -----------------------------------------------------------------------------

class TestCISummary:
    """Tests for CI summary generation."""

    def test_ci_summary_pass(self):
        """All valid consumers produces pass status."""
        reports = [
            ConsumptionDisciplineReport(
                report_id="test1",
                consumer_id="test1",
                consumed_terms=["translator"],
                missing_terms=[],
                term_mismatches=[],
                prohibited_authority_claims=[],
                runtime_reinterpretation_risks=[],
                consumption_alignment_score=1.0,
                discipline_valid=True,
                deterministic_report_hash="abc",
            )
        ]
        summary = generate_ci_summary(reports)
        assert summary.status == "pass"
        assert summary.consumers_valid == 1
        assert summary.consumers_invalid == 0

    def test_ci_summary_fail(self):
        """Invalid consumer produces fail status."""
        reports = [
            ConsumptionDisciplineReport(
                report_id="test1",
                consumer_id="test1",
                consumed_terms=["missing_term"],
                missing_terms=["missing_term"],
                term_mismatches=[],
                prohibited_authority_claims=[],
                runtime_reinterpretation_risks=[],
                consumption_alignment_score=0.85,
                discipline_valid=False,
                deterministic_report_hash="abc",
            )
        ]
        summary = generate_ci_summary(reports)
        assert summary.status == "fail"
        assert summary.consumers_invalid == 1

    def test_ci_summary_warn(self):
        """Risks only produces warn status."""
        reports = [
            ConsumptionDisciplineReport(
                report_id="test1",
                consumer_id="test1",
                consumed_terms=["translator"],
                missing_terms=[],
                term_mismatches=[],
                prohibited_authority_claims=[],
                runtime_reinterpretation_risks=[
                    RuntimeReinterpretationRisk(
                        consumer_id="test1",
                        term="translator",
                        risk_type="shadow_definition",
                        description="Test risk",
                        severity="low",
                    )
                ],
                consumption_alignment_score=0.98,
                discipline_valid=True,
                deterministic_report_hash="abc",
            )
        ]
        summary = generate_ci_summary(reports)
        assert summary.status == "warn"

    def test_ci_summary_invariants(self):
        """CI summary has correct invariants."""
        summary = generate_ci_summary([])
        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False


# -----------------------------------------------------------------------------
# Policy Tests
# -----------------------------------------------------------------------------

class TestConsumptionPolicy:
    """Tests for consumption policy."""

    def test_policy_invariants(self):
        """Policy has correct invariants."""
        policy = ConsumptionPolicyResponse()
        assert policy.immutable is True
        assert policy.ontology_authoritative is True
        assert policy.execution_authorized is False
        assert policy.machine_output_allowed is False
        assert policy.mutation_allowed is False
        assert policy.runtime_may_own_ontology is False

    def test_policy_guardrail(self):
        """Policy has correct guardrail."""
        policy = ConsumptionPolicyResponse()
        assert "runtimes consume ontology without owning ontology" in policy.guardrail

    def test_prohibited_operations_listed(self):
        """Policy lists all prohibited operations."""
        policy = ConsumptionPolicyResponse()
        assert "register_term" in policy.prohibited_operations
        assert "mutate_ontology" in policy.prohibited_operations
        assert "execute_runtime" in policy.prohibited_operations
        assert "generate_machine_output" in policy.prohibited_operations


# -----------------------------------------------------------------------------
# REST Endpoint Tests
# -----------------------------------------------------------------------------

class TestConsumptionEndpoints:
    """Tests for REST endpoints."""

    def test_get_policy(self):
        """GET /api/cam/consumption/policy returns policy."""
        response = client.get("/api/cam/consumption/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["dev_order"] == "7N"
        assert data["execution_authorized"] is False

    def test_list_consumers(self):
        """GET /api/cam/consumption/consumers returns consumers."""
        response = client.get("/api/cam/consumption/consumers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5

    def test_get_consumer(self):
        """GET /api/cam/consumption/consumers/{id} returns consumer."""
        response = client.get("/api/cam/consumption/consumers/cam_runtime")
        assert response.status_code == 200
        data = response.json()
        assert data["consumer_id"] == "cam_runtime"

    def test_get_consumer_not_found(self):
        """GET /api/cam/consumption/consumers/{id} returns 404 for unknown."""
        response = client.get("/api/cam/consumption/consumers/nonexistent")
        assert response.status_code == 404

    def test_list_consumer_domains(self):
        """GET /api/cam/consumption/consumers/domains returns domains."""
        response = client.get("/api/cam/consumption/consumers/domains")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert len(data["domains"]) >= 1

    def test_validate_consumer(self):
        """POST /api/cam/consumption/validate validates consumer."""
        response = client.post(
            "/api/cam/consumption/validate",
            json={"consumer_id": "cam_runtime"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["consumer_id"] == "cam_runtime"
        assert "consumption_alignment_score" in data

    def test_validate_consumer_not_found(self):
        """POST /api/cam/consumption/validate returns 404 for unknown."""
        response = client.post(
            "/api/cam/consumption/validate",
            json={"consumer_id": "nonexistent"}
        )
        assert response.status_code == 404

    def test_validate_all_consumers(self):
        """POST /api/cam/consumption/validate/all validates all."""
        response = client.post("/api/cam/consumption/validate/all")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert "ci_summary" in data
        assert len(data["reports"]) >= 5

    def test_list_reports(self):
        """GET /api/cam/consumption/reports returns reports."""
        # Generate some reports first
        client.post("/api/cam/consumption/validate/all")
        response = client.get("/api/cam/consumption/reports")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_ci_summary(self):
        """GET /api/cam/consumption/ci returns CI summary."""
        response = client.get("/api/cam/consumption/ci")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["pass", "warn", "fail"]
        assert data["execution_authorized"] is False
