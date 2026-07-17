"""
Repository Proposal Evaluation — a deterministic, OBSERVATIONAL readiness evaluation (no approval
authority).

A ``RepositoryProposalEvaluation`` reports whether a ``RepositoryChangeProposal`` and its
``RepositoryExecutionPlan`` are *structurally* complete, internally consistent, and continuous with
the evidence provenance they claim. It is content-addressed: ``evaluation_id`` is derived from a
canonical hash of its content, so identical artifacts yield a byte-stable evaluation. Wall-clock time
is EXCLUDED from the id, the content hash, and the canonical serialization; an optional informational
``created_at`` surfaces only through ``to_audit_dict()``.

Constitutional boundary (PR F): this evaluation is OBSERVATIONAL ONLY. It scores, classifies, and
reports. It never edits a proposal or a plan, generates a commit, executes git, creates a pull
request, alters governance, promotes evidence, or authorizes engineering. A failed check is a
reported observation, NOT a rejection, a block, or a withheld approval — the human review boundary
established by PR A-E is unchanged.

Vocabulary boundary. ``readiness_summary`` is exactly one of:

    * ``complete``   — every applicable structural check passed
    * ``incomplete`` — one or more applicable structural checks failed

These labels describe STRUCTURAL evaluation only. ``complete`` never means approved, safe to merge,
authorized, canonically valid, or ready to execute; ``incomplete`` never means rejected or blocked.
The evaluator has no vocabulary for those concepts because it holds none of that authority.

Completeness score. ``completeness_score`` is an auditable structural ratio and nothing more:

    completeness_score = checks_passed / checks_applicable

It is NOT a confidence, quality, subjective-readiness, or inferred score, and it carries no weighting
or judgment — every applicable check counts exactly once. ``not_applicable`` checks are excluded from
the denominator, so a check that legitimately does not apply can neither reward nor penalize the
score. The four underlying counts are stored explicitly so the ratio is reproducible by hand.

The score is computed with ``decimal.Decimal`` and serialized as a fixed-precision STRING
(``"0.90"``), never a binary float: a float would make the canonical serialization — and therefore
the content-addressed id — dependent on binary floating-point representation. When no check applies
(``checks_applicable == 0``) construction fails closed with ``ProposalEvaluationError`` rather than
inventing a score for an empty denominator.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple

EVALUATION_CONSTITUTIONAL_CLASSIFICATION = "observational_proposal_evaluation__no_approval_authority"

# The two structural readiness labels. Deliberately NOT approve/reject/block/authorize — see docstring.
READINESS_COMPLETE = "complete"
READINESS_INCOMPLETE = "incomplete"
READINESS_SUMMARIES: Tuple[str, ...] = (READINESS_COMPLETE, READINESS_INCOMPLETE)

# Each check has exactly ONE owning category; a finding is never duplicated across category lists.
FINDING_CATEGORY_COMPLETENESS = "completeness"
FINDING_CATEGORY_GOVERNANCE = "governance"
FINDING_CATEGORY_PROVENANCE = "provenance"
FINDING_CATEGORY_EXECUTION = "execution"
FINDING_CATEGORY_INVARIANT = "invariant"
FINDING_CATEGORIES: Tuple[str, ...] = (
    FINDING_CATEGORY_COMPLETENESS,
    FINDING_CATEGORY_GOVERNANCE,
    FINDING_CATEGORY_PROVENANCE,
    FINDING_CATEGORY_EXECUTION,
    FINDING_CATEGORY_INVARIANT,
)

# There is deliberately no ``warn`` state in PR F. A warning is an implicit severity judgment, and
# severity is the reviewer's call, not the evaluator's.
FINDING_STATUS_PASS = "pass"
FINDING_STATUS_FAIL = "fail"
FINDING_STATUS_NOT_APPLICABLE = "not_applicable"
FINDING_STATUSES: Tuple[str, ...] = (
    FINDING_STATUS_PASS,
    FINDING_STATUS_FAIL,
    FINDING_STATUS_NOT_APPLICABLE,
)

# Fixed serialization precision for completeness_score (two decimal places, half-up).
_SCORE_QUANTUM = Decimal("0.01")


class ProposalEvaluationError(Exception):
    """Raised when the supplied artifacts cannot be coherently evaluated (fail-closed).

    Reserved for inputs the evaluator cannot *read* — a wrong type, ``None``, a proposal and plan
    that describe different proposals, data too malformed to interpret, or an empty applicable-check
    denominator. It is NOT the channel for readiness gaps: a substantive defect in an evaluable
    artifact is reported as a failed finding, never suppressed behind an exception.
    """


def _hash_content(content: Dict[str, Any]) -> str:
    """Deterministic 16-hex-char content hash (sorted keys, compact separators, no wall-clock)."""
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def compute_completeness_score(checks_passed: int, checks_applicable: int) -> str:
    """Return the auditable structural ratio ``checks_passed / checks_applicable`` as ``"0.90"``.

    Documented decimal calculation: an exact ``Decimal`` division quantized to two decimal places
    with ROUND_HALF_UP, serialized as a fixed-precision string. Binary floating-point is never used,
    so the value is byte-stable across platforms and safe to content-address.

    Fail-closed: a negative count, a passed count exceeding the applicable count, or an empty
    denominator raises rather than inventing a score.
    """
    if not isinstance(checks_passed, int) or isinstance(checks_passed, bool):
        raise ProposalEvaluationError("checks_passed must be an int")
    if not isinstance(checks_applicable, int) or isinstance(checks_applicable, bool):
        raise ProposalEvaluationError("checks_applicable must be an int")
    if checks_passed < 0 or checks_applicable < 0:
        raise ProposalEvaluationError(
            f"check counts must be non-negative: passed={checks_passed}, applicable={checks_applicable}"
        )
    if checks_applicable == 0:
        raise ProposalEvaluationError(
            "no applicable checks: completeness_score is undefined for an empty denominator"
        )
    if checks_passed > checks_applicable:
        raise ProposalEvaluationError(
            f"checks_passed ({checks_passed}) cannot exceed checks_applicable ({checks_applicable})"
        )
    ratio = (Decimal(checks_passed) / Decimal(checks_applicable)).quantize(
        _SCORE_QUANTUM, rounding=ROUND_HALF_UP
    )
    return str(ratio)


@dataclass(frozen=True)
class EvaluationFinding:
    """One structural check result: what was checked, which category owns it, and what was observed.

    ``detail`` is a deterministic, fact-only statement derived from the artifacts — never interpretive
    prose, a recommendation, or an approval/rejection verb.
    """

    check_id: str
    category: str
    status: str
    detail: str

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "status": self.status,
            "detail": self.detail,
        }


def sort_findings(findings: Tuple[EvaluationFinding, ...]) -> Tuple[EvaluationFinding, ...]:
    """Order findings deterministically by ``(category, check_id)``.

    The order in which checks happen to run is an implementation accident; it carries no
    constitutional meaning and must never leak into the content-addressed id.
    """
    return tuple(sorted(findings, key=lambda f: (f.category, f.check_id)))


def summarize_findings(findings: Tuple[EvaluationFinding, ...]) -> Dict[str, int]:
    """Tally findings by status: ``passed`` / ``failed`` / ``not_applicable`` / ``applicable``.

    ``applicable`` counts every check that was actually evaluated (passed + failed); a
    ``not_applicable`` check is excluded from it, and therefore from the score's denominator.
    """
    passed = sum(1 for f in findings if f.status == FINDING_STATUS_PASS)
    failed = sum(1 for f in findings if f.status == FINDING_STATUS_FAIL)
    not_applicable = sum(1 for f in findings if f.status == FINDING_STATUS_NOT_APPLICABLE)
    return {
        "passed": passed,
        "failed": failed,
        "not_applicable": not_applicable,
        "applicable": passed + failed,
    }


@dataclass(frozen=True)
class RepositoryProposalEvaluation:
    """Immutable, content-addressed, OBSERVATIONAL evaluation (no approval/repository authority)."""

    evaluation_id: str
    proposal_id: str
    execution_plan_id: str
    readiness_summary: str

    checks_passed: int
    checks_failed: int
    checks_not_applicable: int
    checks_applicable: int
    completeness_score: str

    completeness_findings: Tuple[EvaluationFinding, ...]
    governance_findings: Tuple[EvaluationFinding, ...]
    provenance_findings: Tuple[EvaluationFinding, ...]
    execution_findings: Tuple[EvaluationFinding, ...]
    invariant_results: Tuple[EvaluationFinding, ...]

    evaluation_summary: str
    constitutional_classification: str = EVALUATION_CONSTITUTIONAL_CLASSIFICATION
    # Informational only — excluded from evaluation_id, content hash, and canonical serialization.
    created_at: Optional[datetime] = None

    def all_findings(self) -> Tuple[EvaluationFinding, ...]:
        """Every finding across all categories, in deterministic ``(category, check_id)`` order."""
        return sort_findings(
            self.completeness_findings
            + self.governance_findings
            + self.provenance_findings
            + self.execution_findings
            + self.invariant_results
        )

    def _canonical_content(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "execution_plan_id": self.execution_plan_id,
            "readiness_summary": self.readiness_summary,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "checks_not_applicable": self.checks_not_applicable,
            "checks_applicable": self.checks_applicable,
            "completeness_score": self.completeness_score,
            "completeness_findings": [f.to_canonical_dict() for f in self.completeness_findings],
            "governance_findings": [f.to_canonical_dict() for f in self.governance_findings],
            "provenance_findings": [f.to_canonical_dict() for f in self.provenance_findings],
            "execution_findings": [f.to_canonical_dict() for f in self.execution_findings],
            "invariant_results": [f.to_canonical_dict() for f in self.invariant_results],
            "evaluation_summary": self.evaluation_summary,
            "constitutional_classification": self.constitutional_classification,
        }

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Byte-stable serialization for identical inputs (no wall-clock time)."""
        content = self._canonical_content()
        content["evaluation_id"] = self.evaluation_id
        return content

    def to_audit_dict(self) -> Dict[str, Any]:
        """Non-canonical serialization that may include the informational timestamp."""
        content = self.to_canonical_dict()
        content["created_at"] = self.created_at.isoformat() if self.created_at else None
        return content

    def compute_evaluation_hash(self) -> str:
        """Deterministic content hash (matches the ``eval-`` id suffix)."""
        return _hash_content(self._canonical_content())
