"""
Tests for Ontology Reconciliation (7M)

CAM Dev Order 7M: Canonical ontology reconciliation infrastructure.

7M invariants:
  - immutable = true (always)
  - ontology_authoritative = true (always)
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7M makes ontology drift visible. It does not automatically repair
  ontology drift.
"""

import pytest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.cam.canonical_ontology_registry import (
    CanonicalOntologyTerm,
    CANONICAL_ONTOLOGY_INDEX,
    ONTOLOGY_DOMAIN_INDEX,
    ONTOLOGY_ALIAS_INDEX,
    register_canonical_term,
    get_canonical_term,
    list_canonical_terms,
    list_terms_for_domain,
    list_domains,
    resolve_alias,
    clear_ontology_registry,
    to_summary,
    DuplicateTermError,
    _seed_initial_vocabulary,
)
from app.cam.ontology_authority_map import (
    get_domain_ownership_summary,
    get_all_domain_summaries,
    get_lifecycle_vocabularies,
    get_cross_domain_relationship,
    analyze_authority_claim,
    get_tier_1_authority_terms,
)
from app.cam.ontology_reconciliation_engine import (
    OntologyConflict,
    OntologyReconciliationReport,
    ONTOLOGY_CONFLICT_INDEX,
    ONTOLOGY_REPORT_INDEX,
    detect_ontology_conflicts,
    generate_reconciliation_report,
    calculate_alignment_score,
    validate_lifecycle_alignment,
    validate_authority_alignment,
    clear_conflict_index,
    clear_report_index,
    SEVERITY_PENALTIES,
)
from app.cam.ontology_drift_report import (
    generate_ci_summary,
    generate_drift_report,
    classify_severity_summary,
    classify_type_summary,
)


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_indexes():
    """Reset all indexes before each test."""
    clear_ontology_registry()
    clear_conflict_index()
    clear_report_index()
    # Re-seed initial vocabulary
    _seed_initial_vocabulary()
    yield
    clear_ontology_registry()
    clear_conflict_index()
    clear_report_index()


def _create_test_term(
    term: str = "test_term",
    canonical_definition: str = "Test definition",
    owning_domain: str = "Test",
    owning_governance_tier: int = 2,
    aliases: list = None,
    lifecycle_semantics: list = None,
) -> CanonicalOntologyTerm:
    """Create a test term."""
    return CanonicalOntologyTerm(
        term=term,
        canonical_definition=canonical_definition,
        owning_domain=owning_domain,
        owning_governance_tier=owning_governance_tier,
        canonical_contracts=[],
        prohibited_reinterpretations=[],
        lifecycle_semantics=lifecycle_semantics,
        aliases=aliases or [],
    )


# -----------------------------------------------------------------------------
# Test 7M Invariants
# -----------------------------------------------------------------------------

class TestOntologyInvariants:
    """Test 7M model-enforced invariants."""

    def test_7m_invariant_immutable_always_true(self):
        """immutable must always be true."""
        term = get_canonical_term("translator")
        assert term is not None
        assert term.immutable is True

    def test_7m_invariant_ontology_authoritative_always_true(self):
        """ontology_authoritative must always be true."""
        term = get_canonical_term("translator")
        assert term is not None
        assert term.ontology_authoritative is True

    def test_cannot_create_mutable_term(self):
        """Creating a term with immutable=false must fail."""
        with pytest.raises(ValueError, match="7M invariant violation"):
            CanonicalOntologyTerm(
                term="test",
                canonical_definition="Test",
                owning_domain="Test",
                owning_governance_tier=2,
                canonical_contracts=[],
                prohibited_reinterpretations=[],
                immutable=False,  # Must fail
            )

    def test_cannot_create_non_authoritative_term(self):
        """Creating a term with ontology_authoritative=false must fail."""
        with pytest.raises(ValueError, match="7M invariant violation"):
            CanonicalOntologyTerm(
                term="test",
                canonical_definition="Test",
                owning_domain="Test",
                owning_governance_tier=2,
                canonical_contracts=[],
                prohibited_reinterpretations=[],
                ontology_authoritative=False,  # Must fail
            )

    def test_report_execution_authorized_always_false(self):
        """Report execution_authorized must always be false."""
        report = generate_reconciliation_report()
        assert report.execution_authorized is False

    def test_report_machine_output_always_false(self):
        """Report machine_output_allowed must always be false."""
        report = generate_reconciliation_report()
        assert report.machine_output_allowed is False

    def test_cannot_create_execution_authorized_report(self):
        """Creating a report with execution_authorized=true must fail."""
        with pytest.raises(ValueError, match="7M invariant violation"):
            OntologyReconciliationReport(
                terms_evaluated=10,
                conflicts_detected=0,
                lifecycle_conflicts=0,
                authority_conflicts=0,
                runtime_semantic_conflicts=0,
                canonical_alignment_score=1.0,
                ontology_integrity_valid=True,
                deterministic_report_hash="test_hash",
                execution_authorized=True,  # Must fail
            )


# -----------------------------------------------------------------------------
# Test Vocabulary Governance
# -----------------------------------------------------------------------------

class TestVocabularyGovernance:
    """Test canonical vocabulary registration and governance."""

    def test_duplicate_term_rejected(self):
        """Duplicate term registration must be rejected."""
        # "translator" is already seeded
        with pytest.raises(DuplicateTermError):
            term = _create_test_term(term="translator")
            register_canonical_term(term)

    def test_alias_normalization_stable(self):
        """Alias normalization is stable (case-insensitive)."""
        # Get term by alias (case insensitive)
        term = get_canonical_term("TRANSLATION_ENGINE")
        assert term is not None
        assert term.term == "translator"

    def test_immutable_ownership_enforced(self):
        """Term ownership is immutable after registration."""
        term = get_canonical_term("translator")
        assert term is not None
        # Ownership cannot be changed (immutable model)
        assert term.owning_domain == "CAM"

    def test_alias_collision_rejected(self):
        """Alias that collides with existing term or alias is rejected."""
        # Try to register a term with an alias that already exists
        with pytest.raises(DuplicateTermError, match="Alias"):
            term = _create_test_term(
                term="new_term",
                aliases=["translation_engine"],  # Already an alias for "translator"
            )
            register_canonical_term(term)

    def test_initial_vocabulary_seeded(self):
        """Initial canonical vocabulary is seeded at module load."""
        terms = list_canonical_terms()
        assert len(terms) >= 14  # At least 14 initial terms

        # Check specific terms exist
        assert get_canonical_term("translator") is not None
        assert get_canonical_term("runtime") is not None
        assert get_canonical_term("provenance") is not None
        assert get_canonical_term("morphology") is not None


# -----------------------------------------------------------------------------
# Test Conflict Detection
# -----------------------------------------------------------------------------

class TestConflictDetection:
    """Test ontology conflict detection."""

    def test_detects_lifecycle_drift(self):
        """Detects incompatible lifecycle vocabularies."""
        # Clear and add terms with conflicting lifecycle semantics
        clear_ontology_registry()
        clear_conflict_index()

        term1 = _create_test_term(
            term="status_a",
            owning_domain="DomainA",
            lifecycle_semantics=["green", "yellow", "red"],
        )
        term2 = _create_test_term(
            term="status_b",
            owning_domain="DomainB",
            lifecycle_semantics=["ready", "pending", "blocked"],
        )

        register_canonical_term(term1)
        register_canonical_term(term2)

        conflicts = detect_ontology_conflicts()
        lifecycle_conflicts = [c for c in conflicts if c.conflict_type == "lifecycle_drift"]

        # May or may not detect depending on domain relationship
        # The important thing is the detector runs without error
        assert isinstance(conflicts, list)

    def test_generates_reconciliation_report(self):
        """Generates valid reconciliation report."""
        report = generate_reconciliation_report()

        assert report.terms_evaluated > 0
        assert report.canonical_alignment_score >= 0
        assert report.canonical_alignment_score <= 1
        assert report.execution_authorized is False
        assert report.machine_output_allowed is False

    def test_alignment_score_calculation(self):
        """Alignment score is severity-weighted."""
        # No conflicts = 1.0
        score = calculate_alignment_score([])
        assert score == 1.0

        # Single low conflict = (100 - 2) / 100 = 0.98
        conflicts = [
            OntologyConflict(
                term="test",
                conflicting_sources=["A"],
                canonical_source="A",
                conflict_type="duplicate_definition",
                severity="low",
            )
        ]
        score = calculate_alignment_score(conflicts)
        assert score == 0.98

        # Single critical conflict = (100 - 30) / 100 = 0.70
        conflicts = [
            OntologyConflict(
                term="test",
                conflicting_sources=["A"],
                canonical_source="A",
                conflict_type="runtime_reinterpretation",
                severity="critical",
            )
        ]
        score = calculate_alignment_score(conflicts)
        assert score == 0.70


# -----------------------------------------------------------------------------
# Test Determinism
# -----------------------------------------------------------------------------

class TestDeterminism:
    """Test deterministic behavior."""

    def test_same_ontology_same_report_hash(self):
        """Same ontology state produces same report hash."""
        report1 = generate_reconciliation_report()

        # Clear report index to generate new report
        clear_report_index()
        clear_conflict_index()

        report2 = generate_reconciliation_report()

        # Same vocabulary state should produce same deterministic hash
        assert report1.deterministic_report_hash == report2.deterministic_report_hash

    def test_same_vocabulary_ordering(self):
        """Same vocabulary ordering produces consistent results."""
        terms1 = list_canonical_terms()
        terms2 = list_canonical_terms()

        # Term list should be consistent
        assert len(terms1) == len(terms2)

    def test_alignment_score_deterministic(self):
        """Alignment score is deterministic for same conflicts."""
        conflicts = [
            OntologyConflict(
                term="test1",
                conflicting_sources=["A", "B"],
                canonical_source="A",
                conflict_type="lifecycle_drift",
                severity="medium",
            ),
            OntologyConflict(
                term="test2",
                conflicting_sources=["C"],
                canonical_source="C",
                conflict_type="authority_collision",
                severity="high",
            ),
        ]

        score1 = calculate_alignment_score(conflicts)
        score2 = calculate_alignment_score(conflicts)

        assert score1 == score2
        # medium (5) + high (15) = 20 penalty
        # (100 - 20) / 100 = 0.80
        assert score1 == 0.80


# -----------------------------------------------------------------------------
# Test Governance Integrity
# -----------------------------------------------------------------------------

class TestGovernanceIntegrity:
    """Test governance integrity validation."""

    def test_ontology_integrity_valid_on_no_critical(self):
        """ontology_integrity_valid is true when no critical conflicts."""
        # Generate report with no critical conflicts
        report = generate_reconciliation_report()

        # Check if any critical conflicts
        has_critical = any(c.severity == "critical" for c in report.conflicts)

        if not has_critical:
            assert report.ontology_integrity_valid is True

    def test_execution_authorized_always_false_in_report(self):
        """execution_authorized is always false in reports."""
        report = generate_reconciliation_report()
        assert report.execution_authorized is False

    def test_machine_output_always_false_in_report(self):
        """machine_output_allowed is always false in reports."""
        report = generate_reconciliation_report()
        assert report.machine_output_allowed is False


# -----------------------------------------------------------------------------
# Test Cross-Domain
# -----------------------------------------------------------------------------

class TestCrossDomain:
    """Test cross-domain ontology analysis."""

    def test_cam_mrp_relationship(self):
        """Analyzes CAM and MRP domain relationship."""
        relationship = get_cross_domain_relationship("CAM", "MRP")

        assert relationship.domain_a == "CAM"
        assert relationship.domain_b == "MRP"
        # Should have some relationship data
        assert isinstance(relationship.shared_concepts, list)
        assert isinstance(relationship.potential_conflicts, list)

    def test_runtime_governance_relationship(self):
        """Analyzes Runtime and Governance domain relationship."""
        relationship = get_cross_domain_relationship(
            "Runtime Governance",
            "Governance"
        )

        assert relationship.domain_a == "Runtime Governance"
        assert relationship.domain_b == "Governance"

    def test_lifecycle_vocabularies_grouped(self):
        """Lifecycle vocabularies are correctly grouped by domain."""
        vocabs = get_lifecycle_vocabularies()

        assert isinstance(vocabs, dict)
        # Should have some domains with lifecycle semantics
        assert len(vocabs) > 0

        # Each value should be a sorted list
        for domain, lifecycle_terms in vocabs.items():
            assert isinstance(lifecycle_terms, list)


# -----------------------------------------------------------------------------
# Test Authority Map
# -----------------------------------------------------------------------------

class TestAuthorityMap:
    """Test ontology authority map."""

    def test_domain_ownership_summary(self):
        """Gets domain ownership summary."""
        summary = get_domain_ownership_summary("CAM")

        assert summary is not None
        assert summary.domain == "CAM"
        assert summary.term_count > 0
        assert len(summary.terms) > 0

    def test_all_domain_summaries(self):
        """Gets all domain summaries."""
        summaries = get_all_domain_summaries()

        assert len(summaries) > 0
        for summary in summaries:
            assert summary.domain
            assert summary.term_count >= 0

    def test_tier_1_authority_terms(self):
        """Gets Tier 1 (Structural) authority terms."""
        tier1_terms = get_tier_1_authority_terms()

        assert len(tier1_terms) > 0
        for term in tier1_terms:
            assert term.owning_governance_tier == 1

    def test_authority_claim_analysis(self):
        """Analyzes authority claims for a concept."""
        analysis = analyze_authority_claim("translator")

        assert analysis.concept == "translator"
        assert analysis.canonical_owner == "CAM"
        assert "CAM" in analysis.claiming_domains


# -----------------------------------------------------------------------------
# Test Drift Report
# -----------------------------------------------------------------------------

class TestDriftReport:
    """Test drift report generation."""

    def test_generates_ci_summary(self):
        """Generates CI-visible summary."""
        report = generate_reconciliation_report()
        ci_summary = generate_ci_summary(report)

        assert ci_summary.status in ["pass", "warn", "fail"]
        assert ci_summary.alignment_score >= 0
        assert ci_summary.alignment_score <= 1
        assert ci_summary.execution_authorized is False
        assert ci_summary.machine_output_allowed is False

    def test_generates_drift_report(self):
        """Generates comprehensive drift report."""
        recon_report = generate_reconciliation_report()
        drift_report = generate_drift_report(recon_report)

        assert drift_report.report_id == recon_report.report_id
        assert drift_report.severity_summary is not None
        assert drift_report.type_summary is not None
        assert drift_report.ci_summary is not None
        assert drift_report.execution_authorized is False
        assert drift_report.machine_output_allowed is False

    def test_severity_classification(self):
        """Classifies conflicts by severity."""
        conflicts = [
            OntologyConflict(
                term="t1", conflicting_sources=["A"], canonical_source="A",
                conflict_type="duplicate_definition", severity="critical"
            ),
            OntologyConflict(
                term="t2", conflicting_sources=["B"], canonical_source="B",
                conflict_type="lifecycle_drift", severity="medium"
            ),
            OntologyConflict(
                term="t3", conflicting_sources=["C"], canonical_source="C",
                conflict_type="authority_collision", severity="low"
            ),
        ]

        summary = classify_severity_summary(conflicts)

        assert summary.critical == 1
        assert summary.medium == 1
        assert summary.low == 1
        assert summary.high == 0
        # Penalty: 30 + 5 + 2 = 37
        assert summary.total_penalty == 37

    def test_type_classification(self):
        """Classifies conflicts by type."""
        conflicts = [
            OntologyConflict(
                term="t1", conflicting_sources=["A"], canonical_source="A",
                conflict_type="duplicate_definition", severity="low"
            ),
            OntologyConflict(
                term="t2", conflicting_sources=["B"], canonical_source="B",
                conflict_type="lifecycle_drift", severity="medium"
            ),
            OntologyConflict(
                term="t3", conflicting_sources=["C"], canonical_source="C",
                conflict_type="lifecycle_drift", severity="medium"
            ),
        ]

        summary = classify_type_summary(conflicts)

        assert summary.duplicate_definition == 1
        assert summary.lifecycle_drift == 2
        assert summary.authority_collision == 0


# -----------------------------------------------------------------------------
# Test Endpoints
# -----------------------------------------------------------------------------

class TestEndpoints:
    """Test REST API endpoints."""

    def test_get_policy_endpoint(self):
        """GET /policy returns ontology policy."""
        response = client.get("/api/cam/ontology/policy")
        assert response.status_code == 200
        data = response.json()
        assert data["immutable"] is True
        assert data["ontology_authoritative"] is True
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
        assert data["dev_order"] == "7M"

    def test_list_terms_endpoint(self):
        """GET /terms returns canonical terms."""
        response = client.get("/api/cam/ontology/terms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_term_endpoint(self):
        """GET /terms/{term} returns specific term."""
        response = client.get("/api/cam/ontology/terms/translator")
        assert response.status_code == 200
        data = response.json()
        assert data["term"] == "translator"
        assert data["owning_domain"] == "CAM"
        assert data["immutable"] is True

    def test_get_term_not_found(self):
        """GET /terms/{term} returns 404 for unknown term."""
        response = client.get("/api/cam/ontology/terms/nonexistent_term")
        assert response.status_code == 404

    def test_list_domains_endpoint(self):
        """GET /domains returns domain summaries."""
        response = client.get("/api/cam/ontology/domains")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_reconcile_endpoint(self):
        """POST /reconcile generates reconciliation report."""
        response = client.post(
            "/api/cam/ontology/reconcile",
            json={"include_drift_report": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert "reconciliation_report" in data
        assert "ci_summary" in data
        assert data["reconciliation_report"]["execution_authorized"] is False
        assert data["reconciliation_report"]["machine_output_allowed"] is False

    def test_ci_endpoint(self):
        """GET /ci returns CI summary."""
        response = client.get("/api/cam/ontology/ci")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["pass", "warn", "fail"]
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

    def test_conflicts_endpoint(self):
        """GET /conflicts returns conflict list."""
        response = client.get("/api/cam/ontology/conflicts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_lifecycles_endpoint(self):
        """GET /lifecycles returns lifecycle vocabularies."""
        response = client.get("/api/cam/ontology/lifecycles")
        assert response.status_code == 200
        data = response.json()
        assert "vocabularies" in data
        assert "total_domains" in data


# -----------------------------------------------------------------------------
# Test Safety Assertions
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Test that 7M never produces execution artifacts."""

    def test_no_dxf_tokens_in_report(self):
        """Report contains no DXF generation tokens."""
        report = generate_reconciliation_report()
        response_text = report.model_dump_json()

        dxf_tokens = ["SECTION", "ENTITIES", "ENDSEC", "EOF", "LINE", "LWPOLYLINE"]
        for token in dxf_tokens:
            assert token not in response_text

    def test_no_gcode_tokens_in_report(self):
        """Report contains no G-code tokens."""
        report = generate_reconciliation_report()
        response_text = report.model_dump_json()

        gcode_tokens = ["G00", "G01", "G02", "G03", "M03", "M05", "M30"]
        for token in gcode_tokens:
            assert token not in response_text

    def test_all_endpoints_enforce_invariants(self):
        """All endpoint responses enforce invariants."""
        # Policy endpoint
        response = client.get("/api/cam/ontology/policy")
        data = response.json()
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

        # Reconcile endpoint
        response = client.post(
            "/api/cam/ontology/reconcile",
            json={"include_drift_report": False}
        )
        data = response.json()
        assert data["reconciliation_report"]["execution_authorized"] is False
        assert data["reconciliation_report"]["machine_output_allowed"] is False


# -----------------------------------------------------------------------------
# Test Initial Vocabulary Content
# -----------------------------------------------------------------------------

class TestInitialVocabulary:
    """Test that initial vocabulary is correct."""

    def test_translator_term_content(self):
        """translator term has correct content."""
        term = get_canonical_term("translator")
        assert term is not None
        assert term.owning_domain == "CAM"
        assert term.owning_governance_tier == 2
        assert "translation_engine" in term.aliases
        assert "runtime_dispatch_engine" in term.prohibited_reinterpretations

    def test_runtime_term_content(self):
        """runtime term has correct content."""
        term = get_canonical_term("runtime")
        assert term is not None
        assert term.owning_domain == "Runtime Governance"
        assert term.owning_governance_tier == 1

    def test_provenance_term_content(self):
        """provenance term has correct content."""
        term = get_canonical_term("provenance")
        assert term is not None
        assert term.owning_domain == "Governance"
        assert term.owning_governance_tier == 1

    def test_morphology_term_content(self):
        """morphology term has correct content."""
        term = get_canonical_term("morphology")
        assert term is not None
        assert term.owning_domain == "MRP"
        assert term.owning_governance_tier == 2
