"""
Review Safe Export Package

CAM Dev Order 7U: Human-review bundle for export intent.

Provides:
  - ReviewSafeExportPackage model
  - ID-only reference collection
  - Review status tracking
  - Package validation

7U invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - serializer_invocation_allowed: always False
  - generates_gcode: always False

Guardrail:
  7U packages review-safe export intent by reference.
  It does not resolve objects into authority, create export payloads,
  invoke translators, or serialize geometry.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


PackageReviewStatus = Literal[
    "draft",
    "pending_review",
    "under_review",
    "approved",
    "rejected",
    "deferred",
]


class ReviewSafeExportPackage(BaseModel):
    """
    Human-review bundle for export intent.

    Collects ID-only references to cognition artifacts, geometry authority,
    export objects, and translation artifacts without creating dependencies.

    7U invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
      - serializer_invocation_allowed: always False
      - generates_gcode: always False
    """

    package_id: str = Field(
        default_factory=lambda: f"export-pkg-{uuid4().hex[:12]}",
        description="Unique package identifier"
    )

    title: str = Field(
        default="",
        description="Human-readable package title"
    )
    description: str = Field(
        default="",
        description="Package description"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="ID of source workspace"
    )
    strategy_id: Optional[str] = Field(
        default=None,
        description="ID of source strategy"
    )
    strategy_ids: List[str] = Field(
        default_factory=list,
        description="Additional strategy IDs"
    )

    geometry_authority_ref_ids: List[str] = Field(
        default_factory=list,
        description="Geometry authority reference IDs"
    )

    export_object_id: Optional[str] = Field(
        default=None,
        description="Target export object ID"
    )
    export_object_ids: List[str] = Field(
        default_factory=list,
        description="Additional export object IDs"
    )

    translation_artifact_id: Optional[str] = Field(
        default=None,
        description="Target translation artifact ID"
    )
    translation_artifact_ids: List[str] = Field(
        default_factory=list,
        description="Additional translation artifact IDs"
    )

    translator_id: Optional[str] = Field(
        default=None,
        description="Target translator ID"
    )

    compatibility_evaluation_ids: List[str] = Field(
        default_factory=list,
        description="IDs of compatibility evaluations"
    )

    review_status: PackageReviewStatus = Field(
        default="draft",
        description="Current review status"
    )
    reviewer_notes: List[str] = Field(
        default_factory=list,
        description="Notes from reviewers"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Issues blocking approval"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    provenance_refs: List[str] = Field(
        default_factory=list,
        description="Provenance reference chain"
    )

    replay_session_refs: List[str] = Field(
        default_factory=list,
        description="Replay session references (7W linkage)"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7U does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7U does not allow machine output"
    )
    serializer_invocation_allowed: bool = Field(
        default=False,
        description="Always False — 7U does not invoke serializers"
    )
    generates_gcode: bool = Field(
        default=False,
        description="Always False — 7U does not generate G-code"
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

    deterministic_package_hash: str = Field(
        default="",
        description="Deterministic hash of package state"
    )

    @model_validator(mode="after")
    def enforce_7u_invariants(self) -> "ReviewSafeExportPackage":
        """Enforce 7U invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7U invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7U invariant violation: machine_output_allowed must be False"
            )
        if self.serializer_invocation_allowed:
            raise ValueError(
                "7U invariant violation: serializer_invocation_allowed must be False"
            )
        if self.generates_gcode:
            raise ValueError(
                "7U invariant violation: generates_gcode must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of package state."""
        hash_input = {
            "package_id": self.package_id,
            "workspace_id": self.workspace_id,
            "strategy_id": self.strategy_id,
            "strategy_ids": sorted(self.strategy_ids),
            "geometry_authority_ref_ids": sorted(self.geometry_authority_ref_ids),
            "export_object_id": self.export_object_id,
            "translation_artifact_id": self.translation_artifact_id,
            "translator_id": self.translator_id,
            "review_status": self.review_status,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_review_safe_export_package(
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    export_object_id: Optional[str] = None,
    translation_artifact_id: Optional[str] = None,
    translator_id: Optional[str] = None,
    title: str = "",
    description: str = "",
) -> ReviewSafeExportPackage:
    """
    Create a review-safe export package.

    Collects references without resolving objects or creating dependencies.
    """
    package = ReviewSafeExportPackage(
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        geometry_authority_ref_ids=geometry_authority_ref_ids or [],
        export_object_id=export_object_id,
        translation_artifact_id=translation_artifact_id,
        translator_id=translator_id,
        title=title,
        description=description,
    )
    package.deterministic_package_hash = package.compute_hash()
    return package


def add_compatibility_evaluation(
    package: ReviewSafeExportPackage,
    evaluation_id: str,
) -> ReviewSafeExportPackage:
    """Add a compatibility evaluation to the package."""
    if evaluation_id not in package.compatibility_evaluation_ids:
        package.compatibility_evaluation_ids.append(evaluation_id)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_strategy_to_package(
    package: ReviewSafeExportPackage,
    strategy_id: str,
) -> ReviewSafeExportPackage:
    """Add a strategy to the package."""
    if strategy_id not in package.strategy_ids:
        package.strategy_ids.append(strategy_id)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_geometry_authority_ref(
    package: ReviewSafeExportPackage,
    geometry_authority_ref_id: str,
) -> ReviewSafeExportPackage:
    """Add a geometry authority reference to the package."""
    if geometry_authority_ref_id not in package.geometry_authority_ref_ids:
        package.geometry_authority_ref_ids.append(geometry_authority_ref_id)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_provenance_ref(
    package: ReviewSafeExportPackage,
    provenance_ref: str,
) -> ReviewSafeExportPackage:
    """Add a provenance reference to the package."""
    if provenance_ref not in package.provenance_refs:
        package.provenance_refs.append(provenance_ref)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def update_review_status(
    package: ReviewSafeExportPackage,
    new_status: PackageReviewStatus,
    reviewer_note: Optional[str] = None,
) -> ReviewSafeExportPackage:
    """Update the review status of the package."""
    package.review_status = new_status
    if reviewer_note:
        package.reviewer_notes.append(reviewer_note)
    package.updated_at = datetime.now(timezone.utc)
    package.deterministic_package_hash = package.compute_hash()
    return package


def add_blocking_issue(
    package: ReviewSafeExportPackage,
    issue: str,
) -> ReviewSafeExportPackage:
    """Add a blocking issue to the package."""
    if issue not in package.blocking_issues:
        package.blocking_issues.append(issue)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_warning(
    package: ReviewSafeExportPackage,
    warning: str,
) -> ReviewSafeExportPackage:
    """Add a warning to the package."""
    if warning not in package.warnings:
        package.warnings.append(warning)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def validate_package_for_review(
    package: ReviewSafeExportPackage,
) -> tuple[bool, List[str]]:
    """
    Validate that a package is ready for review.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if not package.workspace_id and not package.strategy_id:
        issues.append("Package must reference a workspace or strategy")

    if not package.geometry_authority_ref_ids:
        issues.append("Package has no geometry authority references")

    if package.blocking_issues:
        issues.append(f"Package has {len(package.blocking_issues)} blocking issues")

    if not package.compatibility_evaluation_ids:
        issues.append("Package has no compatibility evaluations")

    return len(issues) == 0, issues


def is_package_approved(package: ReviewSafeExportPackage) -> bool:
    """Check if package is approved for downstream use."""
    return package.review_status == "approved" and not package.blocking_issues
