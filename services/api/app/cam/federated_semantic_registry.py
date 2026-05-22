"""
Federated Semantic Registry

CAM Dev Order 7X: Federation indexes and drift summaries.

Provides:
  - In-memory federation indexes
  - Registration helpers
  - Validation helpers
  - CI drift reporting
  - Authority boundary validation

7X invariants:
  - Registry is observational only
  - No execution authorization
  - No machine output
  - No ontology mutation

Core principle:
  Registry coordinates semantic references.
  It does not centralize authority or mutate schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from .federated_semantic_reference import (
    FederatedDomainType,
    FederatedSemanticReference,
    detect_authority_override,
    validate_federated_semantic_reference,
)
from .cross_domain_continuity import (
    CrossDomainContinuityRecord,
    detect_fragmented_federation,
    validate_cross_domain_continuity,
)
from .federated_review_package import (
    FederatedReviewPackage,
    validate_federated_review_package,
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory indexes
# ─────────────────────────────────────────────────────────────────────────────

FEDERATED_SEMANTIC_REFERENCE_INDEX: Dict[str, FederatedSemanticReference] = {}
CROSS_DOMAIN_CONTINUITY_INDEX: Dict[str, CrossDomainContinuityRecord] = {}
FEDERATED_REVIEW_PACKAGE_INDEX: Dict[str, FederatedReviewPackage] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Registration helpers
# ─────────────────────────────────────────────────────────────────────────────

def register_federated_semantic_reference(
    ref: FederatedSemanticReference,
    *,
    reject_on_authority_override: bool = True,
    force_register: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Register a federated semantic reference.

    Args:
        ref: The reference to register
        reject_on_authority_override: If True, reject refs with authority override
        force_register: If True, skip validation (for testing CI detection)

    Returns:
        (success, error_message)
    """
    # Force registration bypasses validation (for testing)
    if force_register:
        ref.deterministic_federation_hash = ref.compute_hash()
        FEDERATED_SEMANTIC_REFERENCE_INDEX[ref.federation_ref_id] = ref
        return True, None

    # Validate reference
    is_valid, issues = validate_federated_semantic_reference(ref)

    # Check for authority override
    if reject_on_authority_override and detect_authority_override(ref):
        return False, "Authority override detected — registration rejected"

    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    # Recompute hash before registration
    ref.deterministic_federation_hash = ref.compute_hash()

    FEDERATED_SEMANTIC_REFERENCE_INDEX[ref.federation_ref_id] = ref
    return True, None


def register_cross_domain_continuity(
    record: CrossDomainContinuityRecord,
) -> Tuple[bool, Optional[str]]:
    """
    Register a cross-domain continuity record.

    Returns:
        (success, error_message)
    """
    is_valid, issues = validate_cross_domain_continuity(record)

    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    # Recompute hash before registration
    record.deterministic_continuity_hash = record.compute_hash()

    CROSS_DOMAIN_CONTINUITY_INDEX[record.continuity_record_id] = record
    return True, None


def register_federated_review_package(
    package: FederatedReviewPackage,
) -> Tuple[bool, Optional[str]]:
    """
    Register a federated review package.

    Returns:
        (success, error_message)
    """
    is_valid, issues = validate_federated_review_package(package)

    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    # Recompute hash before registration
    package.deterministic_package_hash = package.compute_hash()

    FEDERATED_REVIEW_PACKAGE_INDEX[package.package_id] = package
    return True, None


# ─────────────────────────────────────────────────────────────────────────────
# Get helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_federated_semantic_reference(
    ref_id: str,
) -> Optional[FederatedSemanticReference]:
    """Get a federated semantic reference by ID."""
    return FEDERATED_SEMANTIC_REFERENCE_INDEX.get(ref_id)


def get_cross_domain_continuity(
    record_id: str,
) -> Optional[CrossDomainContinuityRecord]:
    """Get a cross-domain continuity record by ID."""
    return CROSS_DOMAIN_CONTINUITY_INDEX.get(record_id)


def get_federated_review_package(
    package_id: str,
) -> Optional[FederatedReviewPackage]:
    """Get a federated review package by ID."""
    return FEDERATED_REVIEW_PACKAGE_INDEX.get(package_id)


# ─────────────────────────────────────────────────────────────────────────────
# List helpers
# ─────────────────────────────────────────────────────────────────────────────

def list_federated_semantic_references() -> List[FederatedSemanticReference]:
    """List all federated semantic references."""
    return list(FEDERATED_SEMANTIC_REFERENCE_INDEX.values())


def list_cross_domain_continuity_records() -> List[CrossDomainContinuityRecord]:
    """List all cross-domain continuity records."""
    return list(CROSS_DOMAIN_CONTINUITY_INDEX.values())


def list_federated_review_packages() -> List[FederatedReviewPackage]:
    """List all federated review packages."""
    return list(FEDERATED_REVIEW_PACKAGE_INDEX.values())


def list_references_by_domain(
    domain: FederatedDomainType,
) -> List[FederatedSemanticReference]:
    """List federation references involving a specific domain."""
    return [
        ref for ref in FEDERATED_SEMANTIC_REFERENCE_INDEX.values()
        if ref.source_domain == domain or ref.target_domain == domain
    ]


def list_continuity_by_domain(
    domain: FederatedDomainType,
) -> List[CrossDomainContinuityRecord]:
    """List continuity records involving a specific domain."""
    return [
        record for record in CROSS_DOMAIN_CONTINUITY_INDEX.values()
        if domain in record.participating_domains
    ]


def list_packages_by_domain(
    domain: FederatedDomainType,
) -> List[FederatedReviewPackage]:
    """List packages involving a specific domain."""
    return [
        package for package in FEDERATED_REVIEW_PACKAGE_INDEX.values()
        if domain in package.participating_domains
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Validation helpers
# ─────────────────────────────────────────────────────────────────────────────

def validate_federation_boundaries() -> Tuple[bool, List[str]]:
    """
    Validate all federation boundaries are preserved.

    Returns:
        (all_valid, issues)
    """
    issues: List[str] = []

    for ref_id, ref in FEDERATED_SEMANTIC_REFERENCE_INDEX.items():
        if not ref.preserves_authority_boundary:
            issues.append(f"Ref {ref_id} does not preserve authority boundary")
        if ref.authority_override_attempted:
            issues.append(f"Ref {ref_id} has authority_override_attempted")
        if ref.ontology_mutation_attempted:
            issues.append(f"Ref {ref_id} has ontology_mutation_attempted")

    return len(issues) == 0, issues


def validate_cross_domain_provenance() -> Tuple[bool, List[str]]:
    """
    Validate cross-domain provenance is preserved.

    Returns:
        (all_valid, issues)
    """
    issues: List[str] = []

    for record_id, record in CROSS_DOMAIN_CONTINUITY_INDEX.items():
        if not record.continuity_integrity_valid:
            issues.append(f"Record {record_id} has invalid continuity integrity")
        if record.fragmented_federation_detected:
            issues.append(f"Record {record_id} has fragmented federation")

    return len(issues) == 0, issues


def validate_authority_boundaries() -> Tuple[bool, List[str]]:
    """
    Validate no authority boundaries are violated.

    Returns:
        (all_valid, issues)
    """
    issues: List[str] = []

    for ref_id, ref in FEDERATED_SEMANTIC_REFERENCE_INDEX.items():
        if detect_authority_override(ref):
            issues.append(f"Ref {ref_id} has authority override")

    return len(issues) == 0, issues


def detect_ontology_override_attempt() -> List[str]:
    """
    Detect any ontology override attempts across all refs.

    Returns:
        List of ref IDs with ontology override attempts
    """
    return [
        ref.federation_ref_id
        for ref in FEDERATED_SEMANTIC_REFERENCE_INDEX.values()
        if ref.ontology_mutation_attempted
    ]


# ─────────────────────────────────────────────────────────────────────────────
# CI/Summary helpers
# ─────────────────────────────────────────────────────────────────────────────

FederationCIStatus = Literal["pass", "warn", "fail"]


def build_cross_domain_summary() -> Dict[str, Any]:
    """
    Build cross-domain federation summary for CI.

    Status:
      - fail: authority override, ontology mutation, execution/machine output, invalid continuity
      - warn: fragmented federation or warnings exist
      - pass: all registered federation state is clean
    """
    total_refs = len(FEDERATED_SEMANTIC_REFERENCE_INDEX)
    total_continuity = len(CROSS_DOMAIN_CONTINUITY_INDEX)
    total_packages = len(FEDERATED_REVIEW_PACKAGE_INDEX)

    authority_override_count = 0
    ontology_mutation_count = 0
    fragmented_count = 0
    invalid_continuity_count = 0
    warning_count = 0
    blocking_issue_count = 0

    # Count issues in refs
    for ref in FEDERATED_SEMANTIC_REFERENCE_INDEX.values():
        if detect_authority_override(ref):
            authority_override_count += 1
        if ref.ontology_mutation_attempted:
            ontology_mutation_count += 1
        warning_count += len(ref.warnings)
        blocking_issue_count += len(ref.blocking_issues)

    # Count issues in continuity records
    for record in CROSS_DOMAIN_CONTINUITY_INDEX.values():
        if detect_fragmented_federation(record):
            fragmented_count += 1
        # Invalid continuity only counts if there are blocking issues
        # (fragmented federation without blocking issues is a warning, not failure)
        if not record.continuity_integrity_valid and record.blocking_issues:
            invalid_continuity_count += 1
        warning_count += len(record.warnings)
        blocking_issue_count += len(record.blocking_issues)

    # Count issues in packages
    for package in FEDERATED_REVIEW_PACKAGE_INDEX.values():
        warning_count += len(package.warnings)
        blocking_issue_count += len(package.blocking_issues)

    # Determine status
    status: FederationCIStatus = "pass"
    summary_parts: List[str] = []

    if authority_override_count > 0:
        status = "fail"
        summary_parts.append(f"{authority_override_count} authority override(s)")

    if ontology_mutation_count > 0:
        status = "fail"
        summary_parts.append(f"{ontology_mutation_count} ontology mutation attempt(s)")

    if invalid_continuity_count > 0:
        status = "fail"
        summary_parts.append(f"{invalid_continuity_count} invalid continuity record(s)")

    if blocking_issue_count > 0:
        status = "fail"
        summary_parts.append(f"{blocking_issue_count} blocking issue(s)")

    if status == "pass":
        if fragmented_count > 0:
            status = "warn"
            summary_parts.append(f"{fragmented_count} fragmented federation(s)")

        if warning_count > 0:
            status = "warn"
            summary_parts.append(f"{warning_count} warning(s)")

    if status == "pass":
        summary_message = "All federation state is clean"
    else:
        summary_message = "; ".join(summary_parts)

    return {
        "total_federation_refs": total_refs,
        "total_continuity_records": total_continuity,
        "total_federated_packages": total_packages,
        "authority_override_count": authority_override_count,
        "ontology_mutation_attempt_count": ontology_mutation_count,
        "fragmented_federation_count": fragmented_count,
        "invalid_continuity_count": invalid_continuity_count,
        "warning_count": warning_count,
        "blocking_issue_count": blocking_issue_count,
        "status": status,
        "summary_message": summary_message,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

def clear_federated_semantic_indexes_for_tests() -> None:
    """Clear all federation indexes for test isolation."""
    FEDERATED_SEMANTIC_REFERENCE_INDEX.clear()
    CROSS_DOMAIN_CONTINUITY_INDEX.clear()
    FEDERATED_REVIEW_PACKAGE_INDEX.clear()


def get_federation_index_counts() -> Dict[str, int]:
    """Get counts of all federation indexes."""
    return {
        "federation_refs": len(FEDERATED_SEMANTIC_REFERENCE_INDEX),
        "continuity_records": len(CROSS_DOMAIN_CONTINUITY_INDEX),
        "federated_packages": len(FEDERATED_REVIEW_PACKAGE_INDEX),
    }
