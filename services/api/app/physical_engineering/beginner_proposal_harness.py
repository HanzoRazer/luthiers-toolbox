"""Beginner workflow adapter for LTB-MVS-BEGINNER-PROPOSAL-HARNESS-001.

New construction prompted by the MVS roadmap. This module is not recovered
historical code. There was no interrupted workflow harness to restore.

This is not a Grounding Agent. It does not import ``tools.grounding_agent``.
The live Grounding Agent checks handoff text against the repository. It does
not screen physical-engineering proposals, and this adapter does not take
that job.

The adapter collects one beginner request, builds one
``PhysicalEngineeringProposalV1``, calls ``validate_proposal()`` once, and
copies that verdict. Status values are the gate's own result names:
``advisory_allowed``, ``evidence_required``, and ``rejected``. The adapter
does not rename them, score them, or replace them.

It supplies no numeric engineering rule, no geometry inference, and no
manufacturing authority. Policy thresholds and evidence bytes stay with the
caller. ``schema_id`` and ``schema_version`` below are the existing proposal
contract's identity, not measurements.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.physical_engineering.evidence import EvidenceRef, text_token
from app.physical_engineering.proposal_v1 import (
    GeometryRegion,
    PhysicalEngineeringProposalV1,
    PhysicalEngineeringValidationV1,
    ProposedChange,
    validate_proposal,
)


HARNESS_ID = "ltb-mvs-beginner-proposal-harness-001"
ORDER_ID = "LTB-MVS-BEGINNER-PROPOSAL-HARNESS-001"
PROPOSING_ACTOR = "beginner-proposal-harness"
PROPOSAL_SCHEMA_ID = "physical_engineering_proposal"
PROPOSAL_SCHEMA_VERSION = "1.0"

_IDENTITY_FIELDS = (
    "workflow_id",
    "proposal_id",
    "subject_id",
    "subject_revision",
    "user_goal",
    "action",
)


class BeginnerProposalHarnessError(ValueError):
    """The request cannot be formed. ``validate_proposal()`` was not called."""


@dataclass(frozen=True)
class BeginnerProposalRequest:
    """Inputs for one beginner screening. Absence is left absent.

    ``magnitude_mm`` stays ``None`` when the caller did not give a number.
    Prose in ``user_goal`` is not parsed. An empty ``evidence_refs`` tuple
    means the caller cited nothing. ``claimed_authority`` is forwarded as
    given; this request does not rewrite it to ``advisory_only``.
    """

    workflow_id: str
    proposal_id: str
    subject_id: str
    subject_revision: str
    user_goal: str
    action: str
    claimed_authority: str
    magnitude_mm: float | None = None
    region_id: str | None = None
    coordinate_frame: str | None = None
    units: str | None = None
    evidence_refs: tuple[EvidenceRef, ...] = ()
    known_missing_evidence: tuple[str, ...] = ()
    contradictory_evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class BeginnerHarnessProvenance:
    """Records that this adapter is new and that the gate owns the result."""

    construction: str
    order: str
    recovered_historical_code: bool
    grounding_agent: str
    result_owner: str
    harness_id: str
    validator_version: str


@dataclass(frozen=True)
class BeginnerGuidedResult:
    """Gate verdict plus the proposal that was screened. No second status."""

    workflow_id: str
    status: str
    proposal: PhysicalEngineeringProposalV1
    validation: PhysicalEngineeringValidationV1
    explanations: tuple[str, ...]
    required_evidence: tuple[str, ...]
    guidance_lines: tuple[str, ...]
    provenance: BeginnerHarnessProvenance


def run_beginner_proposal(request, *, resolver, policy) -> BeginnerGuidedResult:
    """Screen one request. The resolver and policy are required arguments.

    A missing resolver or policy, or a blank identity field, raises
    ``BeginnerProposalHarnessError`` before ``validate_proposal()``. An
    unusable resolver or policy object is left to the validator, which may
    raise ``ValidatorConfigurationError``.
    """
    _require_session(resolver, policy)
    _require_request(request)
    proposal = _proposal_from(request)
    validation = validate_proposal(proposal, resolver=resolver, policy=policy)
    return _guided(request, proposal, validation)


def _require_session(resolver, policy) -> None:
    if resolver is None or policy is None:
        raise BeginnerProposalHarnessError(
            "resolver and policy are required; the harness supplies neither"
        )


def _require_request(request) -> None:
    if not isinstance(request, BeginnerProposalRequest):
        raise BeginnerProposalHarnessError("request must be a BeginnerProposalRequest")
    missing = [
        name for name in _IDENTITY_FIELDS if not text_token(getattr(request, name))
    ]
    if missing:
        raise BeginnerProposalHarnessError(
            "request identity is incomplete: " + ",".join(missing)
        )
    _require_tuple(request.evidence_refs, "evidence_refs")
    _require_tuple(request.known_missing_evidence, "known_missing_evidence")
    _require_tuple(request.contradictory_evidence, "contradictory_evidence")
    if request.claimed_authority is None or (
        isinstance(request.claimed_authority, str)
        and not text_token(request.claimed_authority)
    ):
        raise BeginnerProposalHarnessError("claimed_authority must be stated")


def _require_tuple(value, name: str) -> None:
    if not isinstance(value, tuple):
        raise BeginnerProposalHarnessError(f"{name} must be a tuple")


def _proposal_from(request: BeginnerProposalRequest) -> PhysicalEngineeringProposalV1:
    return PhysicalEngineeringProposalV1(
        schema_id=PROPOSAL_SCHEMA_ID,
        schema_version=PROPOSAL_SCHEMA_VERSION,
        proposal_id=request.proposal_id,
        proposing_actor=PROPOSING_ACTOR,
        claimed_authority=request.claimed_authority,
        geometry_region=GeometryRegion(
            object_id=request.subject_id,
            geometry_revision=request.subject_revision,
            region_id=request.region_id,
            coordinate_frame=request.coordinate_frame,
            units=request.units,
        ),
        proposed_change=ProposedChange(
            action=request.action,
            magnitude_mm=request.magnitude_mm,
            description=request.user_goal,
        ),
        evidence_refs=request.evidence_refs,
        known_missing_evidence=request.known_missing_evidence,
        contradictory_evidence=request.contradictory_evidence,
        engineering_basis=request.user_goal,
        requested_validation=(),
    )


def _guided(request, proposal, validation) -> BeginnerGuidedResult:
    status = validation.result.value
    explanations = tuple(validation.reason_codes)
    required = tuple(validation.required_evidence)
    return BeginnerGuidedResult(
        workflow_id=request.workflow_id,
        status=status,
        proposal=proposal,
        validation=validation,
        explanations=explanations,
        required_evidence=required,
        guidance_lines=_guidance_lines(validation, status, explanations, required),
        provenance=BeginnerHarnessProvenance(
            construction="new",
            order=ORDER_ID,
            recovered_historical_code=False,
            grounding_agent="not_used",
            result_owner="validate_proposal",
            harness_id=HARNESS_ID,
            validator_version=validation.validator_version,
        ),
    )


def _guidance_lines(validation, status, explanations, required) -> tuple[str, ...]:
    review = str(validation.advisory_review_allowed).lower()
    return (
        f"result={status}",
        f"advisory_review_allowed={review}",
        "reason_codes=" + ",".join(explanations),
        "required_evidence=" + ",".join(required),
    )
