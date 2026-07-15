"""
Repository Execution Plan — a deterministic, DESCRIPTIVE execution plan (no repository authority).

A ``RepositoryExecutionPlan`` describes *how* an already-approved ``RepositoryChangeProposal`` could
be organized for a human engineer to execute. It is content-addressed: ``execution_plan_id`` is
derived from a canonical hash of its content, so identical proposals yield a byte-stable plan.
Wall-clock time is EXCLUDED from the id, the content hash, and the canonical serialization; an
optional informational ``created_at`` surfaces only through ``to_audit_dict()``.

Constitutional boundary (PR E): this plan is DESCRIPTIVE ONLY. It carries no repository or canonical
authority. It never commits, pushes, merges, creates a pull request, mutates a checkout, promotes
evidence, or invents structure the proposal does not declare. Every field is DERIVED from data that
the proposal (and its embedded CBSP21 packet) already carries:

    * recommended_validation_sequence  <- the packet's declared verification.commands_run (verbatim)
    * recommended_commit_sequence      <- declared files grouped by authorized target-path prefix
    * recommended_review_order         <- the same evidence-backed groups, deterministic path order
    * structural_dependency_groups     <- the same path grouping, HONESTLY labelled a structural
                                          grouping (no synthetic dependency edges are asserted)
    * estimated_complexity             <- a documented deterministic table over declared counts +
                                          the declared risk level (no effort/duration/score inference)
    * provenance_reference             <- the four evidence-owned fields, preserved exactly
    * planning_summary                 <- a deterministic template over declared facts only

The field is deliberately named ``structural_dependency_groups`` rather than ``dependency_graph``:
the proposal declares NO inter-file dependency evidence, so representing the path grouping as a
proven dependency graph would misstate what is known. The name states what the data actually is.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION = "descriptive_execution_plan__no_repository_authority"

# The relationship a structural grouping asserts: containment under a declared authorized path.
# It is explicitly NOT a proven build/semantic dependency — see the module docstring.
STRUCTURAL_GROUPING_RELATIONSHIP = "declared_path_grouping"


def _hash_content(content: Dict[str, Any]) -> str:
    """Deterministic 16-hex-char content hash (sorted keys, compact separators, no wall-clock)."""
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class ExecutionGroup:
    """A deterministic group of declared files sharing one authorized target-path prefix.

    Used for both the recommended commit sequence and the recommended review order. It is a
    DESCRIPTIVE grouping of files the proposal already declares — never a claim that the group must
    become exactly one commit or be reviewed in isolation.
    """

    group_id: str
    path_prefix: str
    files: Tuple[str, ...]

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "path_prefix": self.path_prefix,
            "files": list(self.files),
        }


@dataclass(frozen=True)
class DependencyGroup:
    """A structural (path-containment) grouping — explicitly NOT a proven dependency edge.

    ``relationship`` is fixed to ``declared_path_grouping`` so a consumer can never mistake this for
    a synthesized build/semantic dependency. When the proposal declares no dependency evidence (it
    never does today), this is the honest limit of what can be described.
    """

    group_id: str
    path_prefix: str
    files: Tuple[str, ...]
    relationship: str = STRUCTURAL_GROUPING_RELATIONSHIP

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "path_prefix": self.path_prefix,
            "files": list(self.files),
            "relationship": self.relationship,
        }


@dataclass(frozen=True)
class ComplexitySummary:
    """A mechanical complexity summary: a documented deterministic label plus its raw inputs.

    The ``label`` is a pure function of ``changed_file_count`` and ``declared_risk_level`` via a
    documented table (see ``execution_planner._complexity_label``). The raw inputs are kept visible
    so the label is auditable. This is NOT an effort estimate, duration, confidence, or subjective
    complexity score — none of those are derivable from the proposal, so none are asserted.
    """

    label: str
    changed_file_count: int
    authorized_path_count: int
    declared_risk_level: str

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "changed_file_count": self.changed_file_count,
            "authorized_path_count": self.authorized_path_count,
            "declared_risk_level": self.declared_risk_level,
        }


@dataclass(frozen=True)
class ProvenanceReference:
    """The four evidence-owned provenance fields, preserved EXACTLY from the proposal's binding.

    Planning never reinterprets or promotes evidence; it carries these through unchanged. Mirrors
    the review bundle's provenance reference so the two artifacts agree byte-for-byte.
    """

    evidence_candidate_id: str
    evidence_provenance_hash: str
    producing_subsystem: str
    source_authority_state: str

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "evidence_candidate_id": self.evidence_candidate_id,
            "evidence_provenance_hash": self.evidence_provenance_hash,
            "producing_subsystem": self.producing_subsystem,
            "source_authority_state": self.source_authority_state,
        }


@dataclass(frozen=True)
class RepositoryExecutionPlan:
    """Immutable, content-addressed, DESCRIPTIVE execution plan (no runtime/repository authority)."""

    execution_plan_id: str
    proposal_id: str
    recommended_commit_sequence: Tuple[ExecutionGroup, ...]
    recommended_validation_sequence: Tuple[str, ...]
    recommended_review_order: Tuple[ExecutionGroup, ...]
    structural_dependency_groups: Tuple[DependencyGroup, ...]
    estimated_complexity: ComplexitySummary
    provenance_reference: ProvenanceReference
    planning_summary: str
    constitutional_classification: str = EXECUTION_PLAN_CONSTITUTIONAL_CLASSIFICATION
    # Informational only — excluded from execution_plan_id, content hash, and canonical serialization.
    created_at: Optional[datetime] = None

    def _canonical_content(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "recommended_commit_sequence": [g.to_canonical_dict() for g in self.recommended_commit_sequence],
            "recommended_validation_sequence": list(self.recommended_validation_sequence),
            "recommended_review_order": [g.to_canonical_dict() for g in self.recommended_review_order],
            "structural_dependency_groups": [d.to_canonical_dict() for d in self.structural_dependency_groups],
            "estimated_complexity": self.estimated_complexity.to_canonical_dict(),
            "provenance_reference": self.provenance_reference.to_canonical_dict(),
            "planning_summary": self.planning_summary,
            "constitutional_classification": self.constitutional_classification,
        }

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Byte-stable serialization for identical inputs (no wall-clock time)."""
        content = self._canonical_content()
        content["execution_plan_id"] = self.execution_plan_id
        return content

    def to_audit_dict(self) -> Dict[str, Any]:
        """Non-canonical serialization that may include the informational timestamp."""
        content = self.to_canonical_dict()
        content["created_at"] = self.created_at.isoformat() if self.created_at else None
        return content

    def compute_plan_hash(self) -> str:
        """Deterministic content hash (matches the ``rep-`` id suffix)."""
        return _hash_content(self._canonical_content())
