"""
Review queue architecture readiness — contracts.

Answers one question: *are the declared operational prerequisites of the review-queue
subsystem present in this repository?*

This module is **assessment only**. It describes the presence of declared operational
prerequisites. It does not authorize implementation, execution, promotion, or machine
output — enforced below by ``__post_init__`` validation.

DEPENDENCY BOUNDARY EXCEPTION
-----------------------------
These contracts use **stdlib dataclasses rather than Pydantic** because they execute inside
the repository's dependency-free required check (``Fence Checks (Blocking)``). That job
installs no packages by design, which is what keeps the sole required merge gate fast and
independent of package-index availability.

**This is a runtime-boundary exception, not a competing domain-model convention.** Domain
models elsewhere in this package — ``ReviewQueueItem``, ``ReviewDecisionRecord``,
``ReviewQueueCISummary`` — remain Pydantic. The internal validator style differs here; the
**external contract does not**: the serialized report schema, statuses, severities,
ordering, and anti-authorization invariants are authoritative and unchanged.

A consequence worth stating: nothing in this readiness package may import a Pydantic model,
including the review-queue models it assesses. The evidence adapter therefore inspects
declarations via ``ast`` over source files rather than by importing them — which is a more
honest description of what it does anyway.

Three distinct readiness mechanisms exist in this repository. They are separate on purpose
and must not be conflated:

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

Historical lineage: the requirement *set* is ratified by owner ruling from the historical 8F
assessment (TD-2, recovery branch ``p0-repository-state-triage`` @ ``8035f499``). The
historical *implementation shape* — caller-supplied readiness booleans, an in-memory
assessment registry, and a ``POST /readiness`` endpoint — is **deliberately not** carried
forward. Readiness here is derived from repository evidence and can never be asserted by a
caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

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


class ReadinessContractError(ValueError):
    """Raised when a contract invariant is violated.

    A ValueError subclass so callers may catch either. Replaces Pydantic's
    ValidationError at this boundary; the *invariants* are unchanged.
    """


@dataclass(frozen=True)
class ReadinessRequirement:
    """A declared operational prerequisite of the review-queue subsystem."""

    requirement_id: str
    title: str
    description: str
    severity: ReadinessSeverity
    evidence_kind: str
    verification_mode: VerificationMode
    authority_source: str
    runtime_validation_note: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.requirement_id.strip():
            raise ReadinessContractError("requirement_id must be non-empty")
        if not self.authority_source.strip():
            raise ReadinessContractError(
                f"{self.requirement_id}: authority_source must name who requires this — "
                "a requirement without an authority is not policy"
            )
        if not isinstance(self.severity, ReadinessSeverity):
            raise ReadinessContractError(
                f"{self.requirement_id}: severity must be a ReadinessSeverity"
            )
        if not isinstance(self.verification_mode, VerificationMode):
            raise ReadinessContractError(
                f"{self.requirement_id}: verification_mode must be a VerificationMode"
            )


@dataclass(frozen=True)
class ReadinessEvidence:
    """A repository-derived fact used to evaluate a requirement.

    ``source`` is mandatory. Evidence without a citable source is rejected — a finding
    nobody can re-check is not evidence.
    """

    evidence_kind: str
    present: bool
    source: str
    detail: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.present, bool):
            raise ReadinessContractError(
                f"{self.evidence_kind}: present must be a bool — a tri-state would blur "
                "confirmed absence with unverifiability"
            )
        if not self.source or not self.source.strip():
            raise ReadinessContractError(
                "ReadinessEvidence.source must be a non-empty citable identifier — "
                "evidence that cannot be re-checked is not evidence"
            )


@dataclass(frozen=True)
class ReadinessFinding:
    """One requirement compared with current evidence."""

    requirement_id: str
    title: str
    status: ReadinessStatus
    severity: ReadinessSeverity
    detail: str
    evidence_sources: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, ReadinessStatus):
            raise ReadinessContractError(
                f"{self.requirement_id}: status must be a ReadinessStatus"
            )
        if not isinstance(self.severity, ReadinessSeverity):
            raise ReadinessContractError(
                f"{self.requirement_id}: severity must be a ReadinessSeverity"
            )

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


@dataclass(frozen=True)
class ReviewQueueReadinessContext:
    """Typed input to the evaluator. Pure data — no filesystem, no framework."""

    requirements: Tuple[ReadinessRequirement, ...]
    evidence: Tuple[ReadinessEvidence, ...]

    def __post_init__(self) -> None:
        seen: set = set()
        for req in self.requirements:
            if req.requirement_id in seen:
                raise ReadinessContractError(
                    f"Duplicate requirement_id {req.requirement_id!r} — requirement ids "
                    "must be unique or findings cannot be traced to a single requirement"
                )
            seen.add(req.requirement_id)


NON_AUTHORIZATION_NOTICE = (
    "Readiness describes the presence of declared operational prerequisites. "
    "It does not authorize implementation, execution, promotion, or machine output."
)


@dataclass(frozen=True)
class ReviewQueueReadinessReport:
    """The assessment result.

    Invariants (enforced in ``__post_init__``, same semantics as the 8E pattern in
    ``ReviewQueueCISummary``):
      - implementation_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False

    There is deliberately **no caller-settable ready field**. ``aggregate`` is computed
    from findings by the evaluator. This is the specific defect that made the historical
    TD-2 design unsound: it recorded whatever readiness the caller claimed.
    """

    aggregate: AggregateReadiness
    findings: Tuple[ReadinessFinding, ...]
    schema_version: str = SCHEMA_VERSION
    notice: str = NON_AUTHORIZATION_NOTICE
    implementation_authorized: bool = False
    execution_authorized: bool = False
    machine_output_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.aggregate, AggregateReadiness):
            raise ReadinessContractError("aggregate must be an AggregateReadiness")
        if self.implementation_authorized:
            raise ReadinessContractError(
                "Readiness invariant violation: implementation_authorized must be False — "
                "readiness does not authorize implementation"
            )
        if self.execution_authorized:
            raise ReadinessContractError(
                "Readiness invariant violation: execution_authorized must be False — "
                "readiness does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ReadinessContractError(
                "Readiness invariant violation: machine_output_allowed must be False — "
                "readiness does not allow machine output"
            )

    @property
    def blocking_failures(self) -> List[ReadinessFinding]:
        return [f for f in self.findings if f.is_blocking_failure]

    @property
    def warnings(self) -> List[ReadinessFinding]:
        return [f for f in self.findings if f.is_warning]

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic, host-independent mapping for JSON rendering.

        Field order and names are the authoritative external contract and are unchanged by
        the stdlib conversion. Contains no timestamps, host paths or generated ids — the
        same tree must always render byte-identically.
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
