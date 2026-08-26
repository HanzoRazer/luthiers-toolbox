"""Controlled models for Grounding Agent v0.1.

These are intentionally built from the Python standard library
(``dataclasses``, ``enum``, ``typing``) rather than a third-party model
framework. v0.1 is a truth-checking utility, not an AI platform, so it keeps
its dependency surface minimal.

Every model carries explicit JSON (de)serialization so the CLI and tests share
one canonical wire format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------


class EvidenceClass(str, Enum):
    """How the agent knows a claim's observed state (D2).

    Evidence quality is never collapsed into a confidence percentage; the class
    is reported alongside — not instead of — confidence.
    """

    GITHUB_STATE = "GITHUB_STATE"
    GIT_REF = "GIT_REF"
    GIT_ANCESTRY = "GIT_ANCESTRY"
    FILE_PRESENCE = "FILE_PRESENCE"
    WORKTREE_STATE = "WORKTREE_STATE"
    RECORDED_FIXTURE = "RECORDED_FIXTURE"
    INFERENCE = "INFERENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    # Added per D5/active_lane: policy checks over the input contract itself.
    INPUT_CONTRACT = "INPUT_CONTRACT"


class Confidence(str, Enum):
    """Secondary signal (D3). Never overrides evidence class."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClaimVerdict(str, Enum):
    """Per-claim outcome."""

    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BLOCKED = "BLOCKED"


class GroundingStatus(str, Enum):
    """Top-level report status."""

    MATCH = "MATCH"
    STALE = "STALE"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ExecutionDecision(str, Enum):
    """Mandatory execution decision that accompanies every report."""

    PROCEED = "PROCEED"
    STOP = "STOP"


class ClaimType(str, Enum):
    """The seven bounded v0.1 claim types."""

    REPO_HEAD = "repo_head"
    PR_STATE = "pr_state"
    FILE_EXISTS = "file_exists"
    LOCAL_PATH_EXISTS = "local_path_exists"
    COMMIT_ANCESTOR = "commit_ancestor"
    WORKTREE_CLEAN = "worktree_clean"
    ACTIVE_LANE = "active_lane"


class CrossRepoPolicy(str, Enum):
    """Cross-repository policy carried on the active lane (D4/D5).

    v0.1 defines exactly one policy value. Any other value is rejected as a
    malformed request (fail-closed) rather than silently accepted; a broader
    policy space is a later concern, not v0.1 surface.
    """

    EVIDENCE_ONLY = "EVIDENCE_ONLY"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class MalformedRequestError(ValueError):
    """Raised when an incoming request cannot be parsed into the contract.

    The CLI maps this to a dedicated tool-error exit code; it is never
    downgraded into a STALE/PROCEED verdict.
    """


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MalformedRequestError(message)


def _enum_from_value(enum_cls, value, field_name: str):
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(e.value for e in enum_cls)
        raise MalformedRequestError(
            f"{field_name}: {value!r} is not one of [{allowed}]"
        ) from exc


# ---------------------------------------------------------------------------
# Input contract
# ---------------------------------------------------------------------------


@dataclass
class ActiveLane:
    """Mandatory active-lane metadata (D4).

    The Grounding Agent does not manage the lane; it merely verifies and
    reports it.
    """

    project: str
    active_repository: str
    active_program: str
    active_order: str
    active_state: str
    cross_repo_policy: CrossRepoPolicy

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActiveLane":
        _require(isinstance(data, dict), "active_lane must be an object")
        required = [
            "project",
            "active_repository",
            "active_program",
            "active_order",
            "active_state",
            "cross_repo_policy",
        ]
        for key in required:
            _require(key in data and data[key] not in (None, ""), f"active_lane.{key} is required")
        return cls(
            project=str(data["project"]),
            active_repository=str(data["active_repository"]),
            active_program=str(data["active_program"]),
            active_order=str(data["active_order"]),
            active_state=str(data["active_state"]),
            cross_repo_policy=_enum_from_value(
                CrossRepoPolicy, data["cross_repo_policy"], "active_lane.cross_repo_policy"
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project,
            "active_repository": self.active_repository,
            "active_program": self.active_program,
            "active_order": self.active_order,
            "active_state": self.active_state,
            "cross_repo_policy": self.cross_repo_policy.value,
        }


@dataclass
class GroundingClaim:
    """A single structured claim to verify.

    v0.1 evaluates explicit, typed claims only (D6): natural-language handoff
    extraction is a later problem. Fields not relevant to a given claim type
    stay ``None`` and are omitted from serialization.
    """

    claim_id: str
    type: ClaimType
    material: bool = True
    repository: Optional[str] = None
    ref: Optional[str] = None
    expected_sha: Optional[str] = None
    pr_number: Optional[int] = None
    path: Optional[str] = None
    commit: Optional[str] = None
    target_ref: Optional[str] = None
    target_repository: Optional[str] = None
    action: Optional[str] = None  # active_lane: "mutation" | "evidence"
    scope: Optional[str] = None
    expected: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GroundingClaim":
        _require(isinstance(data, dict), "each claim must be an object")
        _require("claim_id" in data and data["claim_id"], "claim.claim_id is required")
        _require("type" in data, "claim.type is required")
        claim_type = _enum_from_value(ClaimType, data["type"], "claim.type")
        material = data.get("material", True)
        _require(isinstance(material, bool), f"{data['claim_id']}.material must be a boolean")

        pr_number = data.get("pr_number")
        if pr_number is not None:
            _require(isinstance(pr_number, int), f"{data['claim_id']}.pr_number must be an integer")

        expected = data.get("expected")
        if expected is not None and not isinstance(expected, (dict, bool)):
            raise MalformedRequestError(
                f"{data['claim_id']}.expected must be an object or boolean"
            )
        # Normalize a bare boolean `expected` (file/local path claims) to a dict.
        if isinstance(expected, bool):
            expected = {"exists": expected}

        return cls(
            claim_id=str(data["claim_id"]),
            type=claim_type,
            material=material,
            repository=data.get("repository"),
            ref=data.get("ref"),
            expected_sha=data.get("expected_sha"),
            pr_number=pr_number,
            path=data.get("path"),
            commit=data.get("commit"),
            target_ref=data.get("target_ref"),
            target_repository=data.get("target_repository"),
            action=data.get("action"),
            scope=data.get("scope"),
            expected=expected,
        )

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "claim_id": self.claim_id,
            "type": self.type.value,
            "material": self.material,
        }
        optional = {
            "repository": self.repository,
            "ref": self.ref,
            "expected_sha": self.expected_sha,
            "pr_number": self.pr_number,
            "path": self.path,
            "commit": self.commit,
            "target_ref": self.target_ref,
            "target_repository": self.target_repository,
            "action": self.action,
            "scope": self.scope,
            "expected": self.expected,
        }
        for key, value in optional.items():
            if value is not None:
                out[key] = value
        return out


@dataclass
class GroundingRequest:
    """Top-level request: active lane + typed claims."""

    active_lane: ActiveLane
    claims: List[GroundingClaim]
    schema_version: str = "grounding_request_v0.1"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GroundingRequest":
        _require(isinstance(data, dict), "request must be a JSON object")
        _require("active_lane" in data, "request.active_lane is required")
        _require("claims" in data, "request.claims is required")
        _require(isinstance(data["claims"], list), "request.claims must be an array")
        _require(len(data["claims"]) > 0, "request.claims must not be empty")

        active_lane = ActiveLane.from_dict(data["active_lane"])
        claims = [GroundingClaim.from_dict(c) for c in data["claims"]]

        seen = set()
        for claim in claims:
            _require(claim.claim_id not in seen, f"duplicate claim_id: {claim.claim_id}")
            seen.add(claim.claim_id)

        return cls(
            active_lane=active_lane,
            claims=claims,
            schema_version=str(data.get("schema_version", "grounding_request_v0.1")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "active_lane": self.active_lane.to_dict(),
            "claims": [c.to_dict() for c in self.claims],
        }


# ---------------------------------------------------------------------------
# Result contract
# ---------------------------------------------------------------------------


@dataclass
class ClaimResult:
    """Per-claim result.

    There is deliberately no hidden reasoning field and no remediation field
    (D8). The only free-text field is ``message`` — a factual statement of
    expected vs observed.
    """

    claim_id: str
    type: ClaimType
    material: bool
    verdict: ClaimVerdict
    evidence_class: EvidenceClass
    confidence: Confidence
    expected: Dict[str, Any] = field(default_factory=dict)
    observed: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    scope: Optional[str] = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "claim_id": self.claim_id,
            "type": self.type.value,
            "material": self.material,
            "verdict": self.verdict.value,
            "evidence_class": self.evidence_class.value,
            "confidence": self.confidence.value,
            "expected": self.expected,
            "observed": self.observed,
            "message": self.message,
        }
        if self.source is not None:
            out["source"] = self.source
        if self.scope is not None:
            out["scope"] = self.scope
        return out


@dataclass
class GroundingReport:
    """Top-level report. Serialization is stable and side-effect free."""

    status: GroundingStatus
    decision: ExecutionDecision
    active_lane: Dict[str, Any]
    claims: List[ClaimResult]
    repository_state: Dict[str, Any] = field(default_factory=dict)
    material_divergences: List[str] = field(default_factory=list)
    blocked_checks: List[str] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    schema_version: str = "grounding_report_v0.1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "decision": self.decision.value,
            "active_lane": self.active_lane,
            "repository_state": self.repository_state,
            "claims": [c.to_dict() for c in self.claims],
            "material_divergences": self.material_divergences,
            "blocked_checks": self.blocked_checks,
            "summary": self.summary,
        }
