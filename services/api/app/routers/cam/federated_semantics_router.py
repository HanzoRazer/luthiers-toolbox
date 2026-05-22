"""
Federated Semantics Router

CAM Dev Order 7X: Cross-domain semantic federation endpoints.

Provides:
  - Federation reference CRUD
  - Continuity record CRUD
  - Federated package CRUD
  - CI summary endpoint

7X invariants:
  - All endpoints are observational only
  - No execution authorization
  - No machine output
  - No ontology mutation

Core principle:
  Router coordinates semantic references.
  It does not centralize authority or mutate schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.federated_semantic_reference import (
    FederatedDomainType,
    FederatedSemanticReference,
    SemanticRelationshipType,
    create_federated_semantic_reference,
    get_reference_summary,
)
from app.cam.cross_domain_continuity import (
    CrossDomainContinuityRecord,
    create_cross_domain_continuity_record,
    get_continuity_summary,
)
from app.cam.federated_review_package import (
    FederatedReviewPackage,
    create_federated_review_package,
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
    build_cross_domain_summary,
)


router = APIRouter(prefix="/api/cam/federation", tags=["CAM", "Federation", "Semantics"])


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────────────────────────────────────────

class CreateFederationReferenceRequest(BaseModel):
    """Request to create a federation reference."""
    source_domain: FederatedDomainType
    target_domain: FederatedDomainType
    relationship_type: SemanticRelationshipType
    source_ref_id: str
    target_ref_id: str
    provenance_refs: List[str] = Field(default_factory=list)


class CreateContinuityRecordRequest(BaseModel):
    """Request to create a continuity record."""
    participating_domains: List[FederatedDomainType]
    continuity_refs: List[str] = Field(default_factory=list)
    replay_session_refs: List[str] = Field(default_factory=list)
    provenance_refs: List[str] = Field(default_factory=list)
    federation_ref_ids: List[str] = Field(default_factory=list)


class CreateFederatedPackageRequest(BaseModel):
    """Request to create a federated review package."""
    participating_domains: List[FederatedDomainType]
    federation_ref_ids: List[str] = Field(default_factory=list)
    continuity_record_ids: List[str] = Field(default_factory=list)
    replay_package_refs: List[str] = Field(default_factory=list)
    provenance_refs: List[str] = Field(default_factory=list)
    review_summary: str = ""


class FederationReferenceResponse(BaseModel):
    """Response containing a federation reference."""
    federation_ref_id: str
    source_domain: FederatedDomainType
    target_domain: FederatedDomainType
    relationship_type: SemanticRelationshipType
    source_ref_id: str
    target_ref_id: str
    preserves_authority_boundary: bool
    authority_override_attempted: bool
    ontology_mutation_attempted: bool
    provenance_refs: List[str]
    warnings: List[str]
    blocking_issues: List[str]
    deterministic_federation_hash: str


class ContinuityRecordResponse(BaseModel):
    """Response containing a continuity record."""
    continuity_record_id: str
    participating_domains: List[FederatedDomainType]
    continuity_refs: List[str]
    replay_session_refs: List[str]
    provenance_refs: List[str]
    federation_ref_ids: List[str]
    continuity_integrity_valid: bool
    fragmented_federation_detected: bool
    warnings: List[str]
    blocking_issues: List[str]
    deterministic_continuity_hash: str


class FederatedPackageResponse(BaseModel):
    """Response containing a federated review package."""
    package_id: str
    participating_domains: List[FederatedDomainType]
    federation_ref_ids: List[str]
    continuity_record_ids: List[str]
    replay_package_refs: List[str]
    provenance_refs: List[str]
    review_summary: str
    warnings: List[str]
    blocking_issues: List[str]
    immutable: bool
    deterministic_package_hash: str


class CISummaryResponse(BaseModel):
    """CI summary response."""
    total_federation_refs: int
    total_continuity_records: int
    total_federated_packages: int
    authority_override_count: int
    ontology_mutation_attempt_count: int
    fragmented_federation_count: int
    invalid_continuity_count: int
    warning_count: int
    blocking_issue_count: int
    status: str
    summary_message: str


# ─────────────────────────────────────────────────────────────────────────────
# Federation Reference endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/references", response_model=FederationReferenceResponse)
def create_federation_reference(
    request: CreateFederationReferenceRequest,
) -> FederationReferenceResponse:
    """
    Create a federated semantic reference.

    Links concepts across domain boundaries without collapsing authority.
    """
    ref = create_federated_semantic_reference(
        source_domain=request.source_domain,
        target_domain=request.target_domain,
        relationship_type=request.relationship_type,
        source_ref_id=request.source_ref_id,
        target_ref_id=request.target_ref_id,
        provenance_refs=request.provenance_refs,
    )

    success, error = register_federated_semantic_reference(ref)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return FederationReferenceResponse(
        federation_ref_id=ref.federation_ref_id,
        source_domain=ref.source_domain,
        target_domain=ref.target_domain,
        relationship_type=ref.relationship_type,
        source_ref_id=ref.source_ref_id,
        target_ref_id=ref.target_ref_id,
        preserves_authority_boundary=ref.preserves_authority_boundary,
        authority_override_attempted=ref.authority_override_attempted,
        ontology_mutation_attempted=ref.ontology_mutation_attempted,
        provenance_refs=ref.provenance_refs,
        warnings=ref.warnings,
        blocking_issues=ref.blocking_issues,
        deterministic_federation_hash=ref.deterministic_federation_hash,
    )


@router.get("/references/{ref_id}", response_model=FederationReferenceResponse)
def get_federation_reference(ref_id: str) -> FederationReferenceResponse:
    """Get a federated semantic reference by ID."""
    ref = get_federated_semantic_reference(ref_id)
    if not ref:
        raise HTTPException(status_code=404, detail=f"Reference {ref_id} not found")

    return FederationReferenceResponse(
        federation_ref_id=ref.federation_ref_id,
        source_domain=ref.source_domain,
        target_domain=ref.target_domain,
        relationship_type=ref.relationship_type,
        source_ref_id=ref.source_ref_id,
        target_ref_id=ref.target_ref_id,
        preserves_authority_boundary=ref.preserves_authority_boundary,
        authority_override_attempted=ref.authority_override_attempted,
        ontology_mutation_attempted=ref.ontology_mutation_attempted,
        provenance_refs=ref.provenance_refs,
        warnings=ref.warnings,
        blocking_issues=ref.blocking_issues,
        deterministic_federation_hash=ref.deterministic_federation_hash,
    )


@router.get("/references", response_model=List[Dict[str, Any]])
def list_federation_references() -> List[Dict[str, Any]]:
    """List all federated semantic references (summaries only)."""
    refs = list_federated_semantic_references()
    return [get_reference_summary(ref) for ref in refs]


# ─────────────────────────────────────────────────────────────────────────────
# Continuity Record endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/continuity", response_model=ContinuityRecordResponse)
def create_continuity_record(
    request: CreateContinuityRecordRequest,
) -> ContinuityRecordResponse:
    """
    Create a cross-domain continuity record.

    Links continuity across domain boundaries for replay and provenance.
    """
    record = create_cross_domain_continuity_record(
        participating_domains=request.participating_domains,
        continuity_refs=request.continuity_refs,
        replay_session_refs=request.replay_session_refs,
        provenance_refs=request.provenance_refs,
        federation_ref_ids=request.federation_ref_ids,
    )

    success, error = register_cross_domain_continuity(record)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return ContinuityRecordResponse(
        continuity_record_id=record.continuity_record_id,
        participating_domains=record.participating_domains,
        continuity_refs=record.continuity_refs,
        replay_session_refs=record.replay_session_refs,
        provenance_refs=record.provenance_refs,
        federation_ref_ids=record.federation_ref_ids,
        continuity_integrity_valid=record.continuity_integrity_valid,
        fragmented_federation_detected=record.fragmented_federation_detected,
        warnings=record.warnings,
        blocking_issues=record.blocking_issues,
        deterministic_continuity_hash=record.deterministic_continuity_hash,
    )


@router.get("/continuity/{record_id}", response_model=ContinuityRecordResponse)
def get_continuity_record(record_id: str) -> ContinuityRecordResponse:
    """Get a cross-domain continuity record by ID."""
    record = get_cross_domain_continuity(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")

    return ContinuityRecordResponse(
        continuity_record_id=record.continuity_record_id,
        participating_domains=record.participating_domains,
        continuity_refs=record.continuity_refs,
        replay_session_refs=record.replay_session_refs,
        provenance_refs=record.provenance_refs,
        federation_ref_ids=record.federation_ref_ids,
        continuity_integrity_valid=record.continuity_integrity_valid,
        fragmented_federation_detected=record.fragmented_federation_detected,
        warnings=record.warnings,
        blocking_issues=record.blocking_issues,
        deterministic_continuity_hash=record.deterministic_continuity_hash,
    )


@router.get("/continuity", response_model=List[Dict[str, Any]])
def list_continuity_records() -> List[Dict[str, Any]]:
    """List all cross-domain continuity records (summaries only)."""
    records = list_cross_domain_continuity_records()
    return [get_continuity_summary(record) for record in records]


# ─────────────────────────────────────────────────────────────────────────────
# Federated Package endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/package", response_model=FederatedPackageResponse)
def create_federated_package(
    request: CreateFederatedPackageRequest,
) -> FederatedPackageResponse:
    """
    Create a federated review package.

    Bundles federation state for immutable cross-domain review.
    """
    package = create_federated_review_package(
        participating_domains=request.participating_domains,
        federation_ref_ids=request.federation_ref_ids,
        continuity_record_ids=request.continuity_record_ids,
        replay_package_refs=request.replay_package_refs,
        provenance_refs=request.provenance_refs,
        review_summary=request.review_summary,
    )

    success, error = register_federated_review_package(package)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return FederatedPackageResponse(
        package_id=package.package_id,
        participating_domains=package.participating_domains,
        federation_ref_ids=package.federation_ref_ids,
        continuity_record_ids=package.continuity_record_ids,
        replay_package_refs=package.replay_package_refs,
        provenance_refs=package.provenance_refs,
        review_summary=package.review_summary,
        warnings=package.warnings,
        blocking_issues=package.blocking_issues,
        immutable=package.immutable,
        deterministic_package_hash=package.deterministic_package_hash,
    )


@router.get("/package/{package_id}", response_model=FederatedPackageResponse)
def get_federated_package(package_id: str) -> FederatedPackageResponse:
    """Get a federated review package by ID."""
    package = get_federated_review_package(package_id)
    if not package:
        raise HTTPException(status_code=404, detail=f"Package {package_id} not found")

    return FederatedPackageResponse(
        package_id=package.package_id,
        participating_domains=package.participating_domains,
        federation_ref_ids=package.federation_ref_ids,
        continuity_record_ids=package.continuity_record_ids,
        replay_package_refs=package.replay_package_refs,
        provenance_refs=package.provenance_refs,
        review_summary=package.review_summary,
        warnings=package.warnings,
        blocking_issues=package.blocking_issues,
        immutable=package.immutable,
        deterministic_package_hash=package.deterministic_package_hash,
    )


@router.get("/packages", response_model=List[Dict[str, Any]])
def list_federated_packages() -> List[Dict[str, Any]]:
    """List all federated review packages (summaries only)."""
    packages = list_federated_review_packages()
    return [get_package_summary(package) for package in packages]


# ─────────────────────────────────────────────────────────────────────────────
# CI Summary endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ci", response_model=CISummaryResponse)
def get_ci_summary() -> CISummaryResponse:
    """
    Get CI summary for federation state.

    Status:
      - fail: authority override, ontology mutation, execution/machine output, invalid continuity
      - warn: fragmented federation or warnings exist
      - pass: all registered federation state is clean
    """
    summary = build_cross_domain_summary()
    return CISummaryResponse(**summary)
