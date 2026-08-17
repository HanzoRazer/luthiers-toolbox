"""
Repository Readiness Report — a deterministic AGGREGATION of the merged proposal, execution-plan,
and proposal-evaluation artifacts into a single presentation record (no approval authority).

A ``RepositoryReadinessReport`` collects, in one content-addressed artifact, the canonical values a
human reviewer needs to read a proposal + plan + evaluation as a coherent chain: the three artifact
IDs, the upstream summary strings, a structural governance projection, and four fixed report
sections. It is content-addressed — ``readiness_report_id`` is derived from a canonical hash of its
content — so identical inputs yield a byte-stable report. Wall-clock time is EXCLUDED from the id,
the content hash, and the canonical serialization; an optional informational ``created_at`` surfaces
only through ``to_audit_dict()``.

Constitutional boundary (PR G): this report is an AGGREGATION and PRESENTATION artifact only. It
copies canonical upstream values verbatim and arranges them; it manufactures no new finding, score,
severity, recommendation, approval status, or narrative interpretation. It never edits an artifact,
generates a commit, executes git, inspects a worktree, invokes a subprocess, creates a pull request,
alters governance, promotes evidence, or authorizes engineering. It has no vocabulary for approval
because it holds none of that authority.

Readiness vocabulary. ``readiness_summary`` is a PROJECTION of the proposal evaluation's
``readiness_summary`` — exactly ``complete`` or ``incomplete`` (the closed vocabulary defined by
PR F). The report never introduces ``ready``, ``blocked``, ``approved``, ``rejected``, ``pass``, or
``fail``; the builder rejects any readiness value outside F's vocabulary rather than normalize or
reinterpret it. ``complete`` means "every applicable structural check passed"; it never means
approved, safe to merge, authorized, or ready to execute.

Summary copying vs composition. ``execution_summary``, ``evaluation_summary``, and
``readiness_summary`` are copied VERBATIM from their canonical upstream fields — the report composes
no new interpretive rollup. The one different destination name (the execution plan's canonical
``planning_summary`` is carried as ``execution_summary``) is a fixed, documented mapping the report
schema settled on; the value is unchanged.

Governance projection. ``governance_summary`` is a deterministic STRUCTURAL projection of the
evaluation's ``governance_findings`` — a count and the finding ``check_id`` values in their upstream
canonical order — and nothing more. It carries no severity conclusion, recommendation, approval
status, or prose. See ``RepositoryGovernanceSummary``.

Lineage. Every retained ID (``proposal_id``, ``execution_plan_id``, ``evaluation_id``) is a
REFERENCE to a canonical upstream artifact, never a newly generated substitute. ``readiness_report_id``
identifies the aggregation artifact itself and replaces none of them. The builder proves the three
artifacts describe one coherent chain before it constructs or hashes a report; a broken chain is a
construction error, never a partial or "incomplete" report.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

try:  # Literal is only needed for the closed section-key vocabulary annotation.
    from typing import Literal
except ImportError:  # pragma: no cover - Python <3.8 is not supported by this package
    Literal = None  # type: ignore[assignment]

from .repository_proposal_evaluation import READINESS_SUMMARIES

READINESS_REPORT_CONSTITUTIONAL_CLASSIFICATION = (
    "aggregation_readiness_report__no_approval_authority"
)

# Content-addressed id prefix, matching the package convention (rep- plan, eval- evaluation).
READINESS_REPORT_ID_PREFIX = "rpt-"

# Closed, ordered section-key vocabulary. The builder owns this order; callers cannot supply,
# reorder, or extend it. A section key outside this set is a construction error.
if Literal is not None:
    RepositoryReadinessSectionKey = Literal[  # type: ignore[misc]
        "proposal",
        "execution",
        "evaluation",
        "provenance",
    ]
else:  # pragma: no cover
    RepositoryReadinessSectionKey = str  # type: ignore[misc]

SECTION_PROPOSAL = "proposal"
SECTION_EXECUTION = "execution"
SECTION_EVALUATION = "evaluation"
SECTION_PROVENANCE = "provenance"

# The canonical section order. Serialization preserves exactly this order.
REPORT_SECTION_ORDER: Tuple[str, ...] = (
    SECTION_PROPOSAL,
    SECTION_EXECUTION,
    SECTION_EVALUATION,
    SECTION_PROVENANCE,
)


class ReadinessReportError(Exception):
    """Raised when the supplied artifacts cannot be coherently aggregated (fail-closed).

    Reserved for inputs the report builder cannot AGGREGATE: a wrong type, ``None``, a lineage
    mismatch across the three artifacts, a provenance disagreement between the plan and the proposal
    binding, an unsupported readiness value, or content that cannot be canonically serialized. There
    is deliberately no "readiness gap" channel here — readiness is F's judgment, already reported in
    the evaluation the report merely carries. A corrupt artifact chain is never softened into a
    partial or "incomplete" report; ``incomplete`` describes evaluated readiness, not a broken chain.
    """


def _hash_content(content: Dict[str, Any]) -> str:
    """Deterministic 16-hex-char content hash (sorted keys, compact separators, no wall-clock)."""
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class RepositoryGovernanceSummary:
    """A deterministic STRUCTURAL projection of the evaluation's governance findings.

    ``finding_count`` equals the number of governance findings; ``check_ids`` are their ``check_id``
    values in the evaluation's own upstream canonical order (the report never re-sorts them). This
    type carries facts already present in the findings and nothing interpretive — no severity, no
    recommendation, no approval status, no prose.
    """

    finding_count: int
    check_ids: Tuple[str, ...]

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "finding_count": self.finding_count,
            "check_ids": list(self.check_ids),
        }


@dataclass(frozen=True)
class RepositoryReadinessSection:
    """One fixed report section: its closed key and an ordered tuple of (name, canonical value) pairs.

    ``entries`` hold references and verbatim canonical values copied from the upstream artifacts —
    never an independently authored conclusion. The tuple ordering is fixed by the builder so
    serialization is byte-identical for semantically identical inputs.
    """

    section_key: str
    entries: Tuple[Tuple[str, Any], ...]

    def to_canonical_dict(self) -> Dict[str, Any]:
        # Entries serialize as an ordered list of [name, value] pairs so the builder's fixed order
        # is preserved verbatim (a dict would let json's key-sorting hide an ordering change).
        return {
            "section_key": self.section_key,
            "entries": [[name, value] for name, value in self.entries],
        }


@dataclass(frozen=True)
class RepositoryReadinessReport:
    """Immutable, content-addressed AGGREGATION of a proposal + plan + evaluation (no authority)."""

    readiness_report_id: str
    proposal_id: str
    execution_plan_id: str
    evaluation_id: str

    governance_summary: RepositoryGovernanceSummary
    execution_summary: str
    evaluation_summary: str
    readiness_summary: str

    report_sections: Tuple[RepositoryReadinessSection, ...]

    constitutional_classification: str = READINESS_REPORT_CONSTITUTIONAL_CLASSIFICATION
    # Informational only — excluded from readiness_report_id, content hash, and canonical form.
    created_at: Optional[datetime] = None

    def _canonical_content(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "execution_plan_id": self.execution_plan_id,
            "evaluation_id": self.evaluation_id,
            "governance_summary": self.governance_summary.to_canonical_dict(),
            "execution_summary": self.execution_summary,
            "evaluation_summary": self.evaluation_summary,
            "readiness_summary": self.readiness_summary,
            "report_sections": [s.to_canonical_dict() for s in self.report_sections],
            "constitutional_classification": self.constitutional_classification,
        }

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Byte-stable serialization for identical inputs (no wall-clock time)."""
        content = self._canonical_content()
        content["readiness_report_id"] = self.readiness_report_id
        return content

    def to_audit_dict(self) -> Dict[str, Any]:
        """Non-canonical serialization that may include the informational timestamp."""
        content = self.to_canonical_dict()
        content["created_at"] = self.created_at.isoformat() if self.created_at else None
        return content

    def compute_report_hash(self) -> str:
        """Deterministic content hash (matches the ``rpt-`` id suffix)."""
        return _hash_content(self._canonical_content())


def validate_readiness_summary(value: str) -> str:
    """Return ``value`` iff it is one of F's structural readiness labels; else fail closed.

    The report is a projection of the evaluation artifact, not a new classification: a readiness
    value outside ``complete``/``incomplete`` means the input is not an evaluation this report can
    faithfully carry, so the builder rejects it rather than normalize or reinterpret it.
    """
    if value not in READINESS_SUMMARIES:
        raise ReadinessReportError(
            f"unsupported readiness_summary {value!r}; must be one of {list(READINESS_SUMMARIES)}"
        )
    return value
