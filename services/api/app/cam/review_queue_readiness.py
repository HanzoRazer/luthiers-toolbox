"""
Review queue architecture readiness — contracts.

Answers one question: *are the declared operational prerequisites of the review-queue
subsystem present in this repository?*

This module is **assessment only**. It describes the presence of declared operational
prerequisites. It does not authorize implementation, execution, promotion, or machine
output — enforced below by model validators, following the 8E pattern already used by
``ReviewQueueCISummary``.

Three distinct readiness mechanisms exist in this repository. They are separate on
purpose and must not be conflated:

===========================================  ==================================================
Mechanism                                    Subject
===========================================  ==================================================
``review_queue_ci.py``                       queue *contents* — item counts, blocking issues,
                                             missing assignments. "Is the queue healthy now?"
``review_queue_readiness*.py`` (this)        subsystem *architecture* — persistence, identity,
                                             timestamps, notification. "Could this queue be
                                             relied on operationally?"
``translator_governance_review_matrix.py``   governance *evidence* readiness for translator
                                             work (CAM 7J).
===========================================  ==================================================

**None of the three authorizes implementation, execution, or machine output.**

Structural precedent: CAM 7J (``translator_governance_review_matrix.py``) — deterministic
evaluation, blocker/warning classification, stable ordering, anti-authorization language.

Historical lineage: the requirement *set* is ratified by owner ruling from the historical
8F assessment (TD-2, recovery branch ``p0-repository-state-triage`` @ ``8035f499``). The
historical *implementation shape* — caller-supplied readiness booleans, an in-memory
assessment registry, and a ``POST /readiness`` endpoint — is **deliberately not** carried
forward. Readiness here is derived from repository evidence and can never be asserted by a
caller.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, model_validator

SCHEMA_VERSION = "review-queue-readiness/v1"


class ReadinessStatus(str, Enum):
    """Result of comparing one requirement against current evidence."""

    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"
    UNRESOLVED_RUNTIME_VALIDATION_REQUIRED = "UNRESOLVED_RUNTIME_VALIDATION_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    DEFERRED_BY_POLICY = "DEFERRED_BY_POLICY"


class ReadinessSeverity(str, Enum):
    """How much a requirement matters when unmet."""

    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"


class VerificationMode(str, Enum):
    """How a requirement can be verified at all.

    ``RUNTIME`` requirements cannot be settled by static inspection. Encountering one
    during a static evaluation yields UNRESOLVED_RUNTIME_VALIDATION_REQUIRED rather than a
    guess in either direction — an unverifiable requirement is not the same finding as a
    missing one.
    """

    STATIC = "STATIC"
    RUNTIME = "RUNTIME"
    HYBRID = "HYBRID"


class AggregateReadiness(str, Enum):
    """Report-level rollup, derived from findings — never accepted as input."""

    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"


class ReadinessEvaluationError(Exception):
    """Raised when the evaluator itself fails.

    Distinct from a truthful NOT_READY result: a broken evaluator must never be reported
    as a legitimate readiness verdict. The CLI maps this to exit code 2.
    """


class ReadinessRequirement(BaseModel):
    """A declared operational prerequisite of the review-queue subsystem."""

    requirement_id: str = Field(..., description="Stable identifier, e.g. RQR-PERSISTENCE")
    title: str
    description: str
    severity: ReadinessSeverity
    evidence_kind: str = Field(
        ...,
        description="The kind of evidence that can satisfy this requirement; matched "
                    "against ReadinessEvidence.evidence_kind.",
    )
    verification_mode: VerificationMode
    authority_source: str = Field(
        ...,
        description="Who says this is required. Every requirement must name its authority.",
    )
    runtime_validation_note: Optional[str] = Field(
        default=None,
        description="For RUNTIME/HYBRID requirements: what a runtime check would have to show.",
    )

    model_config = {"frozen": True}


class ReadinessEvidence(BaseModel):
    """A repository-derived fact used to evaluate a requirement.

    ``source`` is mandatory. Evidence without a citable source is rejected — a finding
    nobody can re-check is not evidence.
    """

    evidence_kind: str
    present: bool = Field(
        ...,
        description="True when the declaration was found. False means confirmed absence, "
                    "not merely 'not looked for'.",
    )
    source: str = Field(
        ...,
        min_length=1,
        description="Path or identifier the fact was read from.",
    )
    detail: Optional[str] = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def require_source(self) -> "ReadinessEvidence":
        if not self.source.strip():
            raise ValueError(
                "ReadinessEvidence.source must be a non-empty citable identifier — "
                "evidence that cannot be re-checked is not evidence"
            )
        return self


class ReadinessFinding(BaseModel):
    """One requirement compared with current evidence."""

    requirement_id: str
    title: str
    status: ReadinessStatus
    severity: ReadinessSeverity
    detail: str
    evidence_sources: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}

    @property
    def is_blocking_failure(self) -> bool:
        """A BLOCKING requirement that is unmet or unverifiable.

        UNRESOLVED counts: an unverifiable blocking prerequisite is not a pass.
        """
        return self.severity is ReadinessSeverity.BLOCKING and self.status in (
            ReadinessStatus.UNSATISFIED,
            ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED,
        )

    @property
    def is_warning(self) -> bool:
        return self.severity is ReadinessSeverity.WARNING and self.status in (
            ReadinessStatus.UNSATISFIED,
            ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED,
        )


class ReviewQueueReadinessContext(BaseModel):
    """Typed input to the evaluator. Pure data — no filesystem, no framework."""

    requirements: Tuple[ReadinessRequirement, ...]
    evidence: Tuple[ReadinessEvidence, ...]

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def reject_duplicate_requirement_ids(self) -> "ReviewQueueReadinessContext":
        seen: set = set()
        for req in self.requirements:
            if req.requirement_id in seen:
                raise ValueError(
                    f"Duplicate requirement_id {req.requirement_id!r} — requirement ids "
                    "must be unique or findings cannot be traced to a single requirement"
                )
            seen.add(req.requirement_id)
        return self


NON_AUTHORIZATION_NOTICE = (
    "Readiness describes the presence of declared operational prerequisites. "
    "It does not authorize implementation, execution, promotion, or machine output."
)


class ReviewQueueReadinessReport(BaseModel):
    """The assessment result.

    Invariants (model-enforced, matching the 8E pattern in ``ReviewQueueCISummary``):
      - implementation_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False

    There is deliberately **no caller-settable ready field**. ``aggregate`` is computed
    from findings by the evaluator. This is the specific defect that made the historical
    TD-2 design unsound: it recorded whatever readiness the caller claimed.
    """

    schema_version: str = Field(default=SCHEMA_VERSION)
    aggregate: AggregateReadiness
    findings: Tuple[ReadinessFinding, ...]
    notice: str = Field(default=NON_AUTHORIZATION_NOTICE)

    implementation_authorized: bool = Field(default=False)
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def enforce_authorization_invariants(self) -> "ReviewQueueReadinessReport":
        """Enforce the anti-authorization invariants."""
        if self.implementation_authorized:
            raise ValueError(
                "Readiness invariant violation: implementation_authorized must be False — "
                "readiness does not authorize implementation"
            )
        if self.execution_authorized:
            raise ValueError(
                "Readiness invariant violation: execution_authorized must be False — "
                "readiness does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "Readiness invariant violation: machine_output_allowed must be False — "
                "readiness does not allow machine output"
            )
        return self

    @property
    def blocking_failures(self) -> List[ReadinessFinding]:
        return [f for f in self.findings if f.is_blocking_failure]

    @property
    def warnings(self) -> List[ReadinessFinding]:
        return [f for f in self.findings if f.is_warning]

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic, host-independent mapping for JSON rendering.

        Contains no timestamps, no host paths and no generated ids — the same tree must
        always render byte-identically.
        """
        return {
            "schema_version": self.schema_version,
            "aggregate": self.aggregate.value,
            "notice": self.notice,
            "implementation_authorized": self.implementation_authorized,
            "execution_authorized": self.execution_authorized,
            "machine_output_allowed": self.machine_output_allowed,
            "findings": [
                {
                    "requirement_id": f.requirement_id,
                    "title": f.title,
                    "status": f.status.value,
                    "severity": f.severity.value,
                    "detail": f.detail,
                    "evidence_sources": list(f.evidence_sources),
                }
                for f in self.findings
            ],
        }
