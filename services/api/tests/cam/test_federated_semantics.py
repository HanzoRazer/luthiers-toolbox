"""
Federated Semantics Tests

CAM Dev Order 7X: Cross-domain semantic federation tests.

Test coverage:
  - Federation reference model/invariants
  - Cross-domain continuity model/invariants
  - Federated review package model/invariants
  - Hash determinism
  - Authority override detection
  - Fragmented federation detection
  - Registry operations
  - CI summary
  - Router endpoints

Minimum: 90 tests
"""

import pytest
from fastapi.testclient import TestClient

from app.cam.federated_semantic_reference import (
    FederatedSemanticReference,
    create_federated_semantic_reference,
    validate_federated_semantic_reference,
    detect_authority_override,
    detect_semantic_overlap,
    is_cross_domain_reference,
    is_valid_federation_reference,
    build_federation_hash,
    add_provenance_ref,
    add_warning,
    add_blocking_issue,
    mark_authority_override_attempted,
    mark_ontology_mutation_attempted,
    get_reference_summary,
)
from app.cam.cross_domain_continuity import (
    CrossDomainContinuityRecord,
    create_cross_domain_continuity_record,
    validate_cross_domain_continuity,
    detect_fragmented_federation,
    is_continuity_valid,
    build_cross_domain_continuity_hash,
    add_participating_domain,
    add_continuity_ref,
    add_replay_session_ref,
    add_federation_ref,
    mark_fragmented_federation,
    mark_missing_refs,
    get_continuity_summary,
)
from app.cam.federated_review_package import (
    FederatedReviewPackage,
    create_federated_review_package,
    validate_federated_review_package,
    is_package_valid_for_review,
    build_federated_package_hash,
    add_federation_ref as add_package_federation_ref,
    add_continuity_record,
    add_replay_package_ref,
    add_participating_domain as add_package_domain,
    update_review_summary,
    get_package_summary,
)
from app.cam.federated_semantic_registry import (
    register_federated_semantic_reference,
    register_cross_domain_continuity,
    register_federated_review_package,
    get_federated_semantic_reference,
    get_cross_domain_continuity,
    get_federated_review_package,
    list_federated_semantic_references,
    list_cross_domain_continuity_records,
    list_federated_review_packages,
    list_references_by_domain,
    list_continuity_by_domain,
    list_packages_by_domain,
    validate_federation_boundaries,
    validate_cross_domain_provenance,
    validate_authority_boundaries,
    detect_ontology_override_attempt,
    build_cross_domain_summary,
    clear_federated_semantic_indexes_for_tests,
    get_federation_index_counts,
)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all indexes before each test."""
    clear_federated_semantic_indexes_for_tests()
    yield
    clear_federated_semantic_indexes_for_tests()


# ─────────────────────────────────────────────────────────────────────────────
# Federation Reference Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFederatedSemanticReference:
    """Tests for FederatedSemanticReference model."""

    def test_create_valid_reference(self):
        """Create a valid federation reference."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:strategy-123",
            target_ref_id="geometry:body-456",
        )
        assert ref.source_domain == "cam"
        assert ref.target_domain == "geometry"
        assert ref.relationship_type == "references"
        assert ref.preserves_authority_boundary is True
        assert ref.authority_override_attempted is False
        assert ref.ontology_mutation_attempted is False
        assert ref.execution_authorized is False
        assert ref.machine_output_allowed is False

    def test_create_reference_with_provenance(self):
        """Create reference with provenance refs."""
        ref = create_federated_semantic_reference(
            source_domain="acoustics",
            target_domain="topology",
            relationship_type="observes",
            source_ref_id="acoustics:obs-123",
            target_ref_id="topology:variant-456",
            provenance_refs=["prov:a", "prov:b"],
        )
        assert ref.provenance_refs == ["prov:a", "prov:b"]

    def test_same_domain_warning(self):
        """Same-domain with cross-domain relationship type warns."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="cam",
            relationship_type="shares_provenance_with",
            source_ref_id="cam:a",
            target_ref_id="cam:b",
        )
        assert len(ref.warnings) == 1
        assert "Same-domain" in ref.warnings[0]

    def test_execution_authorized_rejected(self):
        """execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            FederatedSemanticReference(
                source_domain="cam",
                target_domain="geometry",
                relationship_type="references",
                source_ref_id="a",
                target_ref_id="b",
                execution_authorized=True,
            )

    def test_machine_output_rejected(self):
        """machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            FederatedSemanticReference(
                source_domain="cam",
                target_domain="geometry",
                relationship_type="references",
                source_ref_id="a",
                target_ref_id="b",
                machine_output_allowed=True,
            )

    def test_hash_determinism(self):
        """Same semantic state produces same hash."""
        ref1 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:a",
            target_ref_id="geo:b",
        )
        ref2 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:a",
            target_ref_id="geo:b",
        )
        assert ref1.deterministic_federation_hash == ref2.deterministic_federation_hash

    def test_hash_changes_with_state(self):
        """Hash changes when semantic state changes."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:a",
            target_ref_id="geo:b",
        )
        hash1 = ref.deterministic_federation_hash
        add_blocking_issue(ref, "test issue")
        hash2 = ref.deterministic_federation_hash
        assert hash1 != hash2

    def test_is_cross_domain_reference(self):
        """Detect cross-domain reference."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        assert is_cross_domain_reference(ref) is True

    def test_is_not_cross_domain_reference(self):
        """Same domain is not cross-domain."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="cam",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        assert is_cross_domain_reference(ref) is False


class TestFederationReferenceValidation:
    """Tests for federation reference validation."""

    def test_validate_valid_reference(self):
        """Valid reference passes validation."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        is_valid, issues = validate_federated_semantic_reference(ref)
        assert is_valid is True
        assert issues == []

    def test_validate_missing_source_ref(self):
        """Missing source_ref_id fails validation."""
        ref = FederatedSemanticReference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="",
            target_ref_id="b",
        )
        is_valid, issues = validate_federated_semantic_reference(ref)
        assert is_valid is False
        assert "source_ref_id is required" in issues

    def test_validate_missing_target_ref(self):
        """Missing target_ref_id fails validation."""
        ref = FederatedSemanticReference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="",
        )
        is_valid, issues = validate_federated_semantic_reference(ref)
        assert is_valid is False
        assert "target_ref_id is required" in issues

    def test_validate_authority_override_attempted(self):
        """authority_override_attempted fails validation."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        ref.authority_override_attempted = True
        ref.deterministic_federation_hash = ref.compute_hash()
        is_valid, issues = validate_federated_semantic_reference(ref)
        assert is_valid is False
        assert "authority_override_attempted indicates invalid federation" in issues

    def test_validate_boundary_violation(self):
        """preserves_authority_boundary=False fails validation."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        ref.preserves_authority_boundary = False
        ref.deterministic_federation_hash = ref.compute_hash()
        is_valid, issues = validate_federated_semantic_reference(ref)
        assert is_valid is False
        assert "preserves_authority_boundary is False — boundary violation" in issues


class TestAuthorityOverrideDetection:
    """Tests for authority override detection."""

    def test_detect_no_override(self):
        """Clean reference has no override."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        assert detect_authority_override(ref) is False

    def test_detect_boundary_not_preserved(self):
        """preserves_authority_boundary=False is override."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        ref.preserves_authority_boundary = False
        assert detect_authority_override(ref) is True

    def test_detect_authority_override_flag(self):
        """authority_override_attempted=True is override."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        mark_authority_override_attempted(ref)
        assert detect_authority_override(ref) is True

    def test_detect_ontology_mutation(self):
        """ontology_mutation_attempted=True is override."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        mark_ontology_mutation_attempted(ref)
        assert detect_authority_override(ref) is True

    def test_mark_authority_override(self):
        """mark_authority_override_attempted adds blocking issue."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        mark_authority_override_attempted(ref)
        assert ref.authority_override_attempted is True
        assert "Authority override attempted" in ref.blocking_issues

    def test_mark_ontology_mutation(self):
        """mark_ontology_mutation_attempted adds blocking issue."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        mark_ontology_mutation_attempted(ref)
        assert ref.ontology_mutation_attempted is True
        assert "Ontology mutation attempted" in ref.blocking_issues


class TestSemanticOverlapDetection:
    """Tests for semantic overlap detection."""

    def test_detect_overlap(self):
        """Two refs targeting same entity from different sources overlap."""
        ref1 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:a",
            target_ref_id="geo:shared",
        )
        ref2 = create_federated_semantic_reference(
            source_domain="acoustics",
            target_domain="geometry",
            relationship_type="observes",
            source_ref_id="acou:b",
            target_ref_id="geo:shared",
        )
        assert detect_semantic_overlap(ref1, ref2) is True

    def test_no_overlap_different_targets(self):
        """Different targets don't overlap."""
        ref1 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:a",
            target_ref_id="geo:x",
        )
        ref2 = create_federated_semantic_reference(
            source_domain="acoustics",
            target_domain="geometry",
            relationship_type="observes",
            source_ref_id="acou:b",
            target_ref_id="geo:y",
        )
        assert detect_semantic_overlap(ref1, ref2) is False

    def test_no_overlap_same_source(self):
        """Same source domain doesn't count as overlap."""
        ref1 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:a",
            target_ref_id="geo:shared",
        )
        ref2 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:b",
            target_ref_id="geo:shared",
        )
        assert detect_semantic_overlap(ref1, ref2) is False


# ─────────────────────────────────────────────────────────────────────────────
# Cross-Domain Continuity Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCrossDomainContinuity:
    """Tests for CrossDomainContinuityRecord model."""

    def test_create_valid_record(self):
        """Create a valid continuity record."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["cont:a"],
        )
        assert record.participating_domains == ["cam", "geometry"]
        assert record.continuity_refs == ["cont:a"]
        assert record.continuity_integrity_valid is True
        assert record.fragmented_federation_detected is False
        assert record.execution_authorized is False
        assert record.machine_output_allowed is False

    def test_create_with_replay_refs(self):
        """Create with replay session refs."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "topology"],
            replay_session_refs=["mrs-123", "mrs-456"],
        )
        assert record.replay_session_refs == ["mrs-123", "mrs-456"]

    def test_single_domain_warning(self):
        """Single domain warns about cross-domain semantics."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam"],
            continuity_refs=["cont:a"],
        )
        assert len(record.warnings) == 1
        assert "fewer than 2" in record.warnings[0]

    def test_execution_authorized_rejected(self):
        """execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            CrossDomainContinuityRecord(
                participating_domains=["cam", "geometry"],
                continuity_refs=["a"],
                execution_authorized=True,
            )

    def test_machine_output_rejected(self):
        """machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            CrossDomainContinuityRecord(
                participating_domains=["cam", "geometry"],
                continuity_refs=["a"],
                machine_output_allowed=True,
            )

    def test_hash_determinism(self):
        """Same semantic state produces same hash."""
        record1 = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["cont:a"],
        )
        record2 = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["cont:a"],
        )
        assert record1.deterministic_continuity_hash == record2.deterministic_continuity_hash

    def test_hash_changes_with_fragmentation(self):
        """Hash changes when fragmentation detected."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["cont:a"],
        )
        hash1 = record.deterministic_continuity_hash
        mark_fragmented_federation(record)
        hash2 = record.deterministic_continuity_hash
        assert hash1 != hash2


class TestContinuityValidation:
    """Tests for continuity record validation."""

    def test_validate_valid_record(self):
        """Valid record passes validation."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["cont:a"],
        )
        is_valid, issues = validate_cross_domain_continuity(record)
        assert is_valid is True
        assert issues == []

    def test_validate_no_domains(self):
        """No domains fails validation."""
        record = CrossDomainContinuityRecord(
            participating_domains=[],
            continuity_refs=["a"],
        )
        is_valid, issues = validate_cross_domain_continuity(record)
        assert is_valid is False
        assert "No participating domains specified" in issues

    def test_validate_no_refs(self):
        """No continuity or replay refs fails validation."""
        record = CrossDomainContinuityRecord(
            participating_domains=["cam", "geometry"],
        )
        is_valid, issues = validate_cross_domain_continuity(record)
        assert is_valid is False
        assert "Record has no continuity refs or replay session refs" in issues

    def test_validate_blocking_issues_but_valid(self):
        """Blocking issues with valid integrity fails."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        record.blocking_issues.append("test")
        is_valid, issues = validate_cross_domain_continuity(record)
        assert is_valid is False
        assert "Record has blocking issues but is marked valid" in issues


class TestFragmentedFederationDetection:
    """Tests for fragmented federation detection."""

    def test_no_fragmentation(self):
        """Clean record has no fragmentation."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        assert detect_fragmented_federation(record) is False

    def test_fragmented_flag(self):
        """fragmented_federation_detected=True is fragmented."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        mark_fragmented_federation(record)
        assert detect_fragmented_federation(record) is True

    def test_missing_refs(self):
        """missing_refs_detected=True is fragmented."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        mark_missing_refs(record)
        assert detect_fragmented_federation(record) is True

    def test_invalid_integrity_multi_domain(self):
        """Invalid integrity with multiple domains is fragmented."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry", "acoustics"],
            continuity_refs=["a"],
        )
        record.continuity_integrity_valid = False
        assert detect_fragmented_federation(record) is True


# ─────────────────────────────────────────────────────────────────────────────
# Federated Review Package Model Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFederatedReviewPackage:
    """Tests for FederatedReviewPackage model."""

    def test_create_valid_package(self):
        """Create a valid federated review package."""
        package = create_federated_review_package(
            participating_domains=["cam", "geometry"],
            federation_ref_ids=["fsr-123"],
        )
        assert package.participating_domains == ["cam", "geometry"]
        assert package.federation_ref_ids == ["fsr-123"]
        assert package.immutable is True
        assert package.execution_authorized is False
        assert package.machine_output_allowed is False

    def test_create_with_continuity_records(self):
        """Create with continuity record IDs."""
        package = create_federated_review_package(
            participating_domains=["cam", "topology"],
            continuity_record_ids=["cdcr-123"],
        )
        assert package.continuity_record_ids == ["cdcr-123"]

    def test_empty_package_warning(self):
        """Package with no refs warns."""
        package = create_federated_review_package(
            participating_domains=["cam", "geometry"],
        )
        assert len(package.warnings) == 1
        assert "no federation refs or continuity records" in package.warnings[0]

    def test_immutable_false_rejected(self):
        """immutable=False raises ValueError."""
        with pytest.raises(ValueError, match="immutable must be True"):
            FederatedReviewPackage(
                participating_domains=["cam"],
                federation_ref_ids=["a"],
                immutable=False,
            )

    def test_execution_authorized_rejected(self):
        """execution_authorized=True raises ValueError."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            FederatedReviewPackage(
                participating_domains=["cam"],
                federation_ref_ids=["a"],
                execution_authorized=True,
            )

    def test_machine_output_rejected(self):
        """machine_output_allowed=True raises ValueError."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            FederatedReviewPackage(
                participating_domains=["cam"],
                federation_ref_ids=["a"],
                machine_output_allowed=True,
            )

    def test_hash_determinism(self):
        """Same semantic state produces same hash."""
        package1 = create_federated_review_package(
            participating_domains=["cam", "geometry"],
            federation_ref_ids=["fsr-123"],
        )
        package2 = create_federated_review_package(
            participating_domains=["cam", "geometry"],
            federation_ref_ids=["fsr-123"],
        )
        assert package1.deterministic_package_hash == package2.deterministic_package_hash


class TestPackageValidation:
    """Tests for package validation."""

    def test_validate_valid_package(self):
        """Valid package passes validation."""
        package = create_federated_review_package(
            participating_domains=["cam", "geometry"],
            federation_ref_ids=["fsr-123"],
        )
        is_valid, issues = validate_federated_review_package(package)
        assert is_valid is True
        assert issues == []

    def test_validate_no_domains(self):
        """No domains fails validation."""
        package = FederatedReviewPackage(
            participating_domains=[],
            federation_ref_ids=["a"],
        )
        is_valid, issues = validate_federated_review_package(package)
        assert is_valid is False
        assert "No participating domains specified" in issues

    def test_validate_no_refs(self):
        """No federation refs or continuity records fails."""
        package = FederatedReviewPackage(
            participating_domains=["cam"],
        )
        is_valid, issues = validate_federated_review_package(package)
        assert is_valid is False
        assert "Package has no federation refs or continuity records" in issues


# ─────────────────────────────────────────────────────────────────────────────
# Registry Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFederatedSemanticRegistry:
    """Tests for federated semantic registry."""

    def test_register_valid_reference(self):
        """Register a valid reference."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        success, error = register_federated_semantic_reference(ref)
        assert success is True
        assert error is None

    def test_register_rejects_authority_override(self):
        """Registration rejects authority override by default."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        ref.preserves_authority_boundary = False
        success, error = register_federated_semantic_reference(ref)
        assert success is False
        assert "Authority override detected" in error

    def test_get_registered_reference(self):
        """Get a registered reference."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        register_federated_semantic_reference(ref)
        retrieved = get_federated_semantic_reference(ref.federation_ref_id)
        assert retrieved is not None
        assert retrieved.federation_ref_id == ref.federation_ref_id

    def test_get_nonexistent_reference(self):
        """Get nonexistent reference returns None."""
        retrieved = get_federated_semantic_reference("nonexistent")
        assert retrieved is None

    def test_list_references(self):
        """List all references."""
        ref1 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        ref2 = create_federated_semantic_reference(
            source_domain="acoustics",
            target_domain="topology",
            relationship_type="observes",
            source_ref_id="c",
            target_ref_id="d",
        )
        register_federated_semantic_reference(ref1)
        register_federated_semantic_reference(ref2)
        refs = list_federated_semantic_references()
        assert len(refs) == 2

    def test_list_references_by_domain(self):
        """List references by domain."""
        ref1 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        ref2 = create_federated_semantic_reference(
            source_domain="acoustics",
            target_domain="topology",
            relationship_type="observes",
            source_ref_id="c",
            target_ref_id="d",
        )
        register_federated_semantic_reference(ref1)
        register_federated_semantic_reference(ref2)
        cam_refs = list_references_by_domain("cam")
        assert len(cam_refs) == 1
        assert cam_refs[0].source_domain == "cam"


class TestContinuityRegistry:
    """Tests for continuity record registry."""

    def test_register_valid_record(self):
        """Register a valid continuity record."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        success, error = register_cross_domain_continuity(record)
        assert success is True
        assert error is None

    def test_register_invalid_record(self):
        """Registration rejects invalid record."""
        record = CrossDomainContinuityRecord(
            participating_domains=[],
            continuity_refs=["a"],
        )
        success, error = register_cross_domain_continuity(record)
        assert success is False
        assert "Validation failed" in error

    def test_get_registered_record(self):
        """Get a registered continuity record."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        register_cross_domain_continuity(record)
        retrieved = get_cross_domain_continuity(record.continuity_record_id)
        assert retrieved is not None

    def test_list_continuity_by_domain(self):
        """List continuity records by domain."""
        record1 = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        record2 = create_cross_domain_continuity_record(
            participating_domains=["acoustics", "topology"],
            continuity_refs=["b"],
        )
        register_cross_domain_continuity(record1)
        register_cross_domain_continuity(record2)
        cam_records = list_continuity_by_domain("cam")
        assert len(cam_records) == 1


class TestPackageRegistry:
    """Tests for package registry."""

    def test_register_valid_package(self):
        """Register a valid package."""
        package = create_federated_review_package(
            participating_domains=["cam", "geometry"],
            federation_ref_ids=["fsr-123"],
        )
        success, error = register_federated_review_package(package)
        assert success is True
        assert error is None

    def test_register_invalid_package(self):
        """Registration rejects invalid package."""
        package = FederatedReviewPackage(
            participating_domains=[],
            federation_ref_ids=["a"],
        )
        success, error = register_federated_review_package(package)
        assert success is False
        assert "Validation failed" in error

    def test_get_registered_package(self):
        """Get a registered package."""
        package = create_federated_review_package(
            participating_domains=["cam", "geometry"],
            federation_ref_ids=["fsr-123"],
        )
        register_federated_review_package(package)
        retrieved = get_federated_review_package(package.package_id)
        assert retrieved is not None

    def test_list_packages_by_domain(self):
        """List packages by domain."""
        package1 = create_federated_review_package(
            participating_domains=["cam", "geometry"],
            federation_ref_ids=["a"],
        )
        package2 = create_federated_review_package(
            participating_domains=["acoustics"],
            federation_ref_ids=["b"],
        )
        register_federated_review_package(package1)
        register_federated_review_package(package2)
        cam_packages = list_packages_by_domain("cam")
        assert len(cam_packages) == 1


# ─────────────────────────────────────────────────────────────────────────────
# CI Summary Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCISummary:
    """Tests for CI summary."""

    def test_empty_indexes_pass(self):
        """Empty indexes produce pass status."""
        summary = build_cross_domain_summary()
        assert summary["status"] == "pass"
        assert summary["total_federation_refs"] == 0

    def test_clean_refs_pass(self):
        """Clean refs produce pass status."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        register_federated_semantic_reference(ref)
        summary = build_cross_domain_summary()
        assert summary["status"] == "pass"
        assert summary["total_federation_refs"] == 1

    def test_authority_override_fail(self):
        """Authority override produces fail status."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        mark_authority_override_attempted(ref)
        register_federated_semantic_reference(ref, force_register=True)
        summary = build_cross_domain_summary()
        assert summary["status"] == "fail"
        assert summary["authority_override_count"] == 1

    def test_ontology_mutation_fail(self):
        """Ontology mutation produces fail status."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        mark_ontology_mutation_attempted(ref)
        register_federated_semantic_reference(ref, force_register=True)
        summary = build_cross_domain_summary()
        assert summary["status"] == "fail"
        assert summary["ontology_mutation_attempt_count"] == 1

    def test_fragmented_federation_warn(self):
        """Fragmented federation produces warn status."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        mark_fragmented_federation(record)
        # Can't register with validation, so we do it manually
        from app.cam.federated_semantic_registry import CROSS_DOMAIN_CONTINUITY_INDEX
        CROSS_DOMAIN_CONTINUITY_INDEX[record.continuity_record_id] = record
        summary = build_cross_domain_summary()
        assert summary["status"] == "warn"
        assert summary["fragmented_federation_count"] == 1

    def test_warning_count(self):
        """Warnings produce warn status."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="cam",
            relationship_type="shares_provenance_with",
            source_ref_id="a",
            target_ref_id="b",
        )
        register_federated_semantic_reference(ref)
        summary = build_cross_domain_summary()
        assert summary["status"] == "warn"
        assert summary["warning_count"] >= 1

    def test_summary_message(self):
        """Summary message describes issues."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        mark_authority_override_attempted(ref)
        register_federated_semantic_reference(ref, force_register=True)
        summary = build_cross_domain_summary()
        assert "authority override" in summary["summary_message"]


class TestValidationHelpers:
    """Tests for validation helper functions."""

    def test_validate_federation_boundaries_clean(self):
        """Clean refs pass boundary validation."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        register_federated_semantic_reference(ref)
        is_valid, issues = validate_federation_boundaries()
        assert is_valid is True
        assert issues == []

    def test_validate_federation_boundaries_violation(self):
        """Boundary violation fails validation."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        ref.preserves_authority_boundary = False
        from app.cam.federated_semantic_registry import FEDERATED_SEMANTIC_REFERENCE_INDEX
        FEDERATED_SEMANTIC_REFERENCE_INDEX[ref.federation_ref_id] = ref
        is_valid, issues = validate_federation_boundaries()
        assert is_valid is False
        assert any("does not preserve authority boundary" in i for i in issues)

    def test_validate_authority_boundaries(self):
        """Authority boundary validation works."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        register_federated_semantic_reference(ref)
        is_valid, issues = validate_authority_boundaries()
        assert is_valid is True

    def test_detect_ontology_override_attempt(self):
        """Detect ontology override attempts."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        mark_ontology_mutation_attempted(ref)
        from app.cam.federated_semantic_registry import FEDERATED_SEMANTIC_REFERENCE_INDEX
        FEDERATED_SEMANTIC_REFERENCE_INDEX[ref.federation_ref_id] = ref
        overrides = detect_ontology_override_attempt()
        assert ref.federation_ref_id in overrides


class TestIndexHelpers:
    """Tests for index helper functions."""

    def test_validate_cross_domain_provenance_clean(self):
        """Clean continuity records pass provenance validation."""
        record = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["a"],
        )
        register_cross_domain_continuity(record)
        is_valid, issues = validate_cross_domain_provenance()
        assert is_valid is True
        assert issues == []

    def test_clear_indexes(self):
        """Clear indexes removes all entries."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        register_federated_semantic_reference(ref)
        assert len(list_federated_semantic_references()) == 1
        clear_federated_semantic_indexes_for_tests()
        assert len(list_federated_semantic_references()) == 0

    def test_get_index_counts(self):
        """Get index counts returns correct values."""
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="a",
            target_ref_id="b",
        )
        register_federated_semantic_reference(ref)
        counts = get_federation_index_counts()
        assert counts["federation_refs"] == 1
        assert counts["continuity_records"] == 0
        assert counts["federated_packages"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Router Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFederatedSemanticsRouter:
    """Tests for federated semantics router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)

    def test_create_federation_reference(self, client):
        """POST /api/cam/federation/references creates reference."""
        response = client.post(
            "/api/cam/federation/references",
            json={
                "source_domain": "cam",
                "target_domain": "geometry",
                "relationship_type": "references",
                "source_ref_id": "cam:test-123",
                "target_ref_id": "geo:body-456",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_domain"] == "cam"
        assert data["target_domain"] == "geometry"
        assert data["preserves_authority_boundary"] is True

    def test_get_federation_reference(self, client):
        """GET /api/cam/federation/references/{ref_id} returns reference."""
        # First create
        create_response = client.post(
            "/api/cam/federation/references",
            json={
                "source_domain": "cam",
                "target_domain": "geometry",
                "relationship_type": "references",
                "source_ref_id": "a",
                "target_ref_id": "b",
            },
        )
        ref_id = create_response.json()["federation_ref_id"]

        # Then get
        response = client.get(f"/api/cam/federation/references/{ref_id}")
        assert response.status_code == 200
        assert response.json()["federation_ref_id"] == ref_id

    def test_get_nonexistent_reference(self, client):
        """GET /api/cam/federation/references/{ref_id} returns 404."""
        response = client.get("/api/cam/federation/references/nonexistent")
        assert response.status_code == 404

    def test_list_federation_references(self, client):
        """GET /api/cam/federation/references returns list."""
        client.post(
            "/api/cam/federation/references",
            json={
                "source_domain": "cam",
                "target_domain": "geometry",
                "relationship_type": "references",
                "source_ref_id": "a",
                "target_ref_id": "b",
            },
        )
        response = client.get("/api/cam/federation/references")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_create_continuity_record(self, client):
        """POST /api/cam/federation/continuity creates record."""
        response = client.post(
            "/api/cam/federation/continuity",
            json={
                "participating_domains": ["cam", "geometry"],
                "continuity_refs": ["cont:a"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["participating_domains"] == ["cam", "geometry"]
        assert data["continuity_integrity_valid"] is True

    def test_get_continuity_record(self, client):
        """GET /api/cam/federation/continuity/{record_id} returns record."""
        create_response = client.post(
            "/api/cam/federation/continuity",
            json={
                "participating_domains": ["cam", "geometry"],
                "continuity_refs": ["a"],
            },
        )
        record_id = create_response.json()["continuity_record_id"]

        response = client.get(f"/api/cam/federation/continuity/{record_id}")
        assert response.status_code == 200

    def test_list_continuity_records(self, client):
        """GET /api/cam/federation/continuity returns list."""
        client.post(
            "/api/cam/federation/continuity",
            json={
                "participating_domains": ["cam", "geometry"],
                "continuity_refs": ["a"],
            },
        )
        response = client.get("/api/cam/federation/continuity")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_create_federated_package(self, client):
        """POST /api/cam/federation/package creates package."""
        response = client.post(
            "/api/cam/federation/package",
            json={
                "participating_domains": ["cam", "geometry"],
                "federation_ref_ids": ["fsr-123"],
                "review_summary": "Test package",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["immutable"] is True
        assert data["review_summary"] == "Test package"

    def test_get_federated_package(self, client):
        """GET /api/cam/federation/package/{package_id} returns package."""
        create_response = client.post(
            "/api/cam/federation/package",
            json={
                "participating_domains": ["cam"],
                "federation_ref_ids": ["a"],
            },
        )
        package_id = create_response.json()["package_id"]

        response = client.get(f"/api/cam/federation/package/{package_id}")
        assert response.status_code == 200

    def test_list_federated_packages(self, client):
        """GET /api/cam/federation/packages returns list."""
        client.post(
            "/api/cam/federation/package",
            json={
                "participating_domains": ["cam"],
                "federation_ref_ids": ["a"],
            },
        )
        response = client.get("/api/cam/federation/packages")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_ci_summary(self, client):
        """GET /api/cam/federation/ci returns summary."""
        response = client.get("/api/cam/federation/ci")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "summary_message" in data
        assert data["status"] in ["pass", "warn", "fail"]


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFederationIntegration:
    """Integration tests for federation workflow."""

    def test_full_federation_workflow(self):
        """Complete federation workflow: ref → continuity → package."""
        # Create federation references
        ref1 = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id="cam:strategy-123",
            target_ref_id="geo:body-456",
        )
        ref2 = create_federated_semantic_reference(
            source_domain="acoustics",
            target_domain="geometry",
            relationship_type="observes",
            source_ref_id="acou:obs-789",
            target_ref_id="geo:body-456",
        )
        register_federated_semantic_reference(ref1)
        register_federated_semantic_reference(ref2)

        # Create continuity record linking refs
        continuity = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry", "acoustics"],
            federation_ref_ids=[ref1.federation_ref_id, ref2.federation_ref_id],
            continuity_refs=["cont:session-abc"],
        )
        register_cross_domain_continuity(continuity)

        # Create federated package
        package = create_federated_review_package(
            participating_domains=["cam", "geometry", "acoustics"],
            federation_ref_ids=[ref1.federation_ref_id, ref2.federation_ref_id],
            continuity_record_ids=[continuity.continuity_record_id],
            review_summary="Cross-domain body analysis",
        )
        register_federated_review_package(package)

        # Verify CI summary
        summary = build_cross_domain_summary()
        assert summary["status"] == "pass"
        assert summary["total_federation_refs"] == 2
        assert summary["total_continuity_records"] == 1
        assert summary["total_federated_packages"] == 1

    def test_federation_with_replay_session(self):
        """Federation integrates with replay session."""
        from app.cam.manufacturing_replay_session import create_replay_session

        # Create replay session with federation refs
        session = create_replay_session(
            workspace_id="ws-123",
            observation_ids=["obs-1", "obs-2"],
        )
        # The 7X field should exist
        assert hasattr(session, "federation_ref_ids")
        assert session.federation_ref_ids == []

        # Create federation ref and link
        ref = create_federated_semantic_reference(
            source_domain="cam",
            target_domain="geometry",
            relationship_type="references",
            source_ref_id=f"cam:{session.replay_session_id}",
            target_ref_id="geo:body-123",
        )
        register_federated_semantic_reference(ref)

        # Link ref to session
        session.federation_ref_ids.append(ref.federation_ref_id)
        assert len(session.federation_ref_ids) == 1

    def test_federation_with_review_package(self):
        """Federation integrates with replay safe review package."""
        from app.cam.replay_safe_review_package import create_replay_safe_review_package

        # Create review package with continuity refs
        package = create_replay_safe_review_package(
            replay_session_id="mrs-123",
            observation_ids=["obs-1"],
        )
        # The 7X field should exist
        assert hasattr(package, "cross_domain_continuity_refs")
        assert package.cross_domain_continuity_refs == []

        # Create continuity record and link
        continuity = create_cross_domain_continuity_record(
            participating_domains=["cam", "geometry"],
            continuity_refs=["cont:a"],
        )
        register_cross_domain_continuity(continuity)

        # Link continuity to package
        package.cross_domain_continuity_refs.append(continuity.continuity_record_id)
        assert len(package.cross_domain_continuity_refs) == 1
