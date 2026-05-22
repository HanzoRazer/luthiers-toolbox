"""
Cross-Domain Continuity

CAM Dev Order 7X: Continuity linkage across domains.

Provides:
  - CrossDomainContinuityRecord model
  - Replay continuity federation
  - Fragmented federation detection
  - Continuity integrity validation

7X invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Continuity coordinates semantic history.
  Continuity does not authorize execution or merge ontologies.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .federated_semantic_reference import FederatedDomainType


class CrossDomainContinuityRecord(BaseModel):
    """
    Cross-domain continuity linkage record.

    Links continuity across domain boundaries for replay and provenance.

    7X invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    continuity_record_id: str = Field(
        default_factory=lambda: f"cdcr-{uuid4().hex[:12]}",
        description="Unique continuity record identifier"
    )

    participating_domains: List[FederatedDomainType] = Field(
        default_factory=list,
        description="Domains participating in this continuity"
    )

    continuity_refs: List[str] = Field(
        default_factory=list,
        description="Continuity reference IDs across domains"
    )

    replay_session_refs: List[str] = Field(
        default_factory=list,
        description="Linked replay session IDs"
    )

    provenance_refs: List[str] = Field(
        default_factory=list,
        description="Provenance reference chain"
    )

    federation_ref_ids: List[str] = Field(
        default_factory=list,
        description="Linked federation reference IDs"
    )

    continuity_integrity_valid: bool = Field(
        default=True,
        description="Whether continuity integrity is valid"
    )

    fragmented_federation_detected: bool = Field(
        default=False,
        description="Whether fragmented federation was detected"
    )

    missing_refs_detected: bool = Field(
        default=False,
        description="Whether missing references were detected"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Issues blocking continuity validity"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7X does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7X does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_continuity_hash: str = Field(
        default="",
        description="Deterministic hash of continuity state"
    )

    @model_validator(mode="after")
    def enforce_7x_invariants(self) -> "CrossDomainContinuityRecord":
        """Enforce 7X invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7X invariant violation: execution_authorized must be False — "
                "7X does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7X invariant violation: machine_output_allowed must be False — "
                "7X does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of continuity state."""
        hash_input = {
            "participating_domains": sorted(self.participating_domains),
            "continuity_refs": sorted(self.continuity_refs),
            "replay_session_refs": sorted(self.replay_session_refs),
            "provenance_refs": sorted(self.provenance_refs),
            "federation_ref_ids": sorted(self.federation_ref_ids),
            "continuity_integrity_valid": self.continuity_integrity_valid,
            "fragmented_federation_detected": self.fragmented_federation_detected,
            "blocking_issues": sorted(self.blocking_issues),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_cross_domain_continuity_record(
    participating_domains: List[FederatedDomainType],
    continuity_refs: List[str] | None = None,
    replay_session_refs: List[str] | None = None,
    provenance_refs: List[str] | None = None,
    federation_ref_ids: List[str] | None = None,
) -> CrossDomainContinuityRecord:
    """
    Create a cross-domain continuity record.

    Links continuity across domains without authorizing execution.
    """
    record = CrossDomainContinuityRecord(
        participating_domains=participating_domains,
        continuity_refs=continuity_refs or [],
        replay_session_refs=replay_session_refs or [],
        provenance_refs=provenance_refs or [],
        federation_ref_ids=federation_ref_ids or [],
    )

    # Warn if fewer than 2 domains
    if len(participating_domains) < 2:
        record.warnings.append(
            "Cross-domain continuity with fewer than 2 participating domains"
        )

    record.deterministic_continuity_hash = record.compute_hash()
    return record


def validate_cross_domain_continuity(
    record: CrossDomainContinuityRecord,
) -> Tuple[bool, List[str]]:
    """
    Validate that a continuity record is well-formed.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if record.execution_authorized:
        issues.append("execution_authorized must be False")

    if record.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not record.participating_domains:
        issues.append("No participating domains specified")

    if not record.continuity_refs and not record.replay_session_refs:
        issues.append("Record has no continuity refs or replay session refs")

    if record.blocking_issues and record.continuity_integrity_valid:
        issues.append("Record has blocking issues but is marked valid")

    if record.fragmented_federation_detected and record.continuity_integrity_valid:
        issues.append("Fragmented federation detected but marked valid")

    return len(issues) == 0, issues


def detect_fragmented_federation(
    record: CrossDomainContinuityRecord,
) -> bool:
    """
    Detect if continuity record has fragmented federation.

    Fragmentation conditions:
      - Missing refs detected
      - Fragmented federation flag set
      - Continuity integrity invalid with multiple domains
    """
    if record.fragmented_federation_detected:
        return True
    if record.missing_refs_detected:
        return True
    if not record.continuity_integrity_valid and len(record.participating_domains) > 1:
        return True
    return False


def is_continuity_valid(record: CrossDomainContinuityRecord) -> bool:
    """Check if continuity record is valid."""
    is_valid, _ = validate_cross_domain_continuity(record)
    return is_valid and record.continuity_integrity_valid


def build_cross_domain_continuity_hash(
    record: CrossDomainContinuityRecord,
) -> str:
    """Build deterministic hash for a continuity record."""
    return record.compute_hash()


def add_participating_domain(
    record: CrossDomainContinuityRecord,
    domain: FederatedDomainType,
) -> CrossDomainContinuityRecord:
    """Add a participating domain."""
    if domain not in record.participating_domains:
        record.participating_domains.append(domain)
        record.updated_at = datetime.now(timezone.utc)
        record.deterministic_continuity_hash = record.compute_hash()
    return record


def add_continuity_ref(
    record: CrossDomainContinuityRecord,
    continuity_ref: str,
) -> CrossDomainContinuityRecord:
    """Add a continuity reference."""
    if continuity_ref not in record.continuity_refs:
        record.continuity_refs.append(continuity_ref)
        record.updated_at = datetime.now(timezone.utc)
        record.deterministic_continuity_hash = record.compute_hash()
    return record


def add_replay_session_ref(
    record: CrossDomainContinuityRecord,
    replay_session_ref: str,
) -> CrossDomainContinuityRecord:
    """Add a replay session reference."""
    if replay_session_ref not in record.replay_session_refs:
        record.replay_session_refs.append(replay_session_ref)
        record.updated_at = datetime.now(timezone.utc)
        record.deterministic_continuity_hash = record.compute_hash()
    return record


def add_federation_ref(
    record: CrossDomainContinuityRecord,
    federation_ref_id: str,
) -> CrossDomainContinuityRecord:
    """Add a federation reference."""
    if federation_ref_id not in record.federation_ref_ids:
        record.federation_ref_ids.append(federation_ref_id)
        record.updated_at = datetime.now(timezone.utc)
        record.deterministic_continuity_hash = record.compute_hash()
    return record


def add_provenance_ref(
    record: CrossDomainContinuityRecord,
    provenance_ref: str,
) -> CrossDomainContinuityRecord:
    """Add a provenance reference."""
    if provenance_ref not in record.provenance_refs:
        record.provenance_refs.append(provenance_ref)
        record.updated_at = datetime.now(timezone.utc)
        record.deterministic_continuity_hash = record.compute_hash()
    return record


def add_warning(
    record: CrossDomainContinuityRecord,
    warning: str,
) -> CrossDomainContinuityRecord:
    """Add a warning to the record."""
    if warning not in record.warnings:
        record.warnings.append(warning)
    return record


def add_blocking_issue(
    record: CrossDomainContinuityRecord,
    issue: str,
) -> CrossDomainContinuityRecord:
    """Add a blocking issue to the record."""
    if issue not in record.blocking_issues:
        record.blocking_issues.append(issue)
        record.continuity_integrity_valid = False
        record.updated_at = datetime.now(timezone.utc)
        record.deterministic_continuity_hash = record.compute_hash()
    return record


def mark_fragmented_federation(
    record: CrossDomainContinuityRecord,
) -> CrossDomainContinuityRecord:
    """Mark that fragmented federation was detected."""
    record.fragmented_federation_detected = True
    record.continuity_integrity_valid = False
    record.updated_at = datetime.now(timezone.utc)
    record.deterministic_continuity_hash = record.compute_hash()
    return record


def mark_missing_refs(
    record: CrossDomainContinuityRecord,
) -> CrossDomainContinuityRecord:
    """Mark that missing refs were detected."""
    record.missing_refs_detected = True
    record.continuity_integrity_valid = False
    record.updated_at = datetime.now(timezone.utc)
    record.deterministic_continuity_hash = record.compute_hash()
    return record


def get_continuity_summary(record: CrossDomainContinuityRecord) -> Dict[str, Any]:
    """Get a summary of the continuity record."""
    return {
        "continuity_record_id": record.continuity_record_id,
        "participating_domain_count": len(record.participating_domains),
        "participating_domains": record.participating_domains,
        "continuity_ref_count": len(record.continuity_refs),
        "replay_session_ref_count": len(record.replay_session_refs),
        "federation_ref_count": len(record.federation_ref_ids),
        "continuity_integrity_valid": record.continuity_integrity_valid,
        "fragmented_federation_detected": record.fragmented_federation_detected,
        "warning_count": len(record.warnings),
        "blocking_issue_count": len(record.blocking_issues),
    }
