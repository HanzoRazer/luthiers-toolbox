"""
Post-Freeze Expansion Registry

CAM Dev Order 8A: Registry for post-freeze proposals and readiness evaluations.

Provides:
  - In-memory proposal registry
  - In-memory readiness registry
  - Registration helpers
  - Query helpers
  - CI summary building

8A invariants:
  - implementation_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Registry tracks proposals and evaluations for human review.
  It does not authorize implementation, execution, or machine output.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from .post_freeze_expansion_gate import (
    PostFreezeExpansionProposal,
    validate_post_freeze_proposal,
    get_proposal_summary,
    VALID_TARGET_LAYERS,
)
from .post_freeze_readiness import (
    PostFreezeExpansionReadiness,
    PostFreezeGate,
    classify_post_freeze_gate,
    validate_freeze_compatibility,
    get_readiness_summary,
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory indexes
# ─────────────────────────────────────────────────────────────────────────────

POST_FREEZE_EXPANSION_PROPOSAL_INDEX: Dict[str, PostFreezeExpansionProposal] = {}
POST_FREEZE_EXPANSION_READINESS_INDEX: Dict[str, PostFreezeExpansionReadiness] = {}

_POST_FREEZE_PROPOSAL_ORDER: List[str] = []
_POST_FREEZE_READINESS_ORDER: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Proposal registration
# ─────────────────────────────────────────────────────────────────────────────

def register_post_freeze_proposal(
    proposal: PostFreezeExpansionProposal,
) -> Tuple[bool, Optional[str]]:
    """
    Register a post-freeze expansion proposal.

    Returns (success, error_message).
    """
    is_valid, issues = validate_post_freeze_proposal(proposal)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    if proposal.proposal_id in POST_FREEZE_EXPANSION_PROPOSAL_INDEX:
        return False, f"Proposal {proposal.proposal_id} already exists"

    proposal.deterministic_proposal_hash = proposal.compute_hash()

    POST_FREEZE_EXPANSION_PROPOSAL_INDEX[proposal.proposal_id] = proposal
    _POST_FREEZE_PROPOSAL_ORDER.append(proposal.proposal_id)
    return True, None


def get_post_freeze_proposal(
    proposal_id: str,
) -> Optional[PostFreezeExpansionProposal]:
    """Get a proposal by ID."""
    return POST_FREEZE_EXPANSION_PROPOSAL_INDEX.get(proposal_id)


def get_latest_post_freeze_proposal() -> Optional[PostFreezeExpansionProposal]:
    """Get the most recently registered proposal."""
    if not _POST_FREEZE_PROPOSAL_ORDER:
        return None
    latest_id = _POST_FREEZE_PROPOSAL_ORDER[-1]
    return POST_FREEZE_EXPANSION_PROPOSAL_INDEX.get(latest_id)


def list_post_freeze_proposals() -> List[PostFreezeExpansionProposal]:
    """List all proposals in registration order."""
    return [
        POST_FREEZE_EXPANSION_PROPOSAL_INDEX[pid]
        for pid in _POST_FREEZE_PROPOSAL_ORDER
        if pid in POST_FREEZE_EXPANSION_PROPOSAL_INDEX
    ]


def list_proposals_by_target_layer(
    target_layer: str,
) -> List[PostFreezeExpansionProposal]:
    """List proposals by target layer."""
    return [
        p for p in list_post_freeze_proposals()
        if p.target_layer == target_layer
    ]


def list_proposals_by_state(
    state: str,
) -> List[PostFreezeExpansionProposal]:
    """List proposals by state."""
    return [
        p for p in list_post_freeze_proposals()
        if p.proposal_state == state
    ]


def get_post_freeze_proposal_count() -> int:
    """Get total proposal count."""
    return len(POST_FREEZE_EXPANSION_PROPOSAL_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# Readiness registration
# ─────────────────────────────────────────────────────────────────────────────

def register_post_freeze_readiness(
    readiness: PostFreezeExpansionReadiness,
) -> Tuple[bool, Optional[str]]:
    """
    Register a readiness evaluation.

    Returns (success, error_message).
    """
    if readiness.implementation_authorized:
        return False, "implementation_authorized must be False"
    if readiness.execution_authorized:
        return False, "execution_authorized must be False"
    if readiness.machine_output_allowed:
        return False, "machine_output_allowed must be False"

    if readiness.readiness_id in POST_FREEZE_EXPANSION_READINESS_INDEX:
        return False, f"Readiness {readiness.readiness_id} already exists"

    readiness.deterministic_readiness_hash = readiness.compute_hash()

    POST_FREEZE_EXPANSION_READINESS_INDEX[readiness.readiness_id] = readiness
    _POST_FREEZE_READINESS_ORDER.append(readiness.readiness_id)
    return True, None


def get_post_freeze_readiness(
    readiness_id: str,
) -> Optional[PostFreezeExpansionReadiness]:
    """Get a readiness evaluation by ID."""
    return POST_FREEZE_EXPANSION_READINESS_INDEX.get(readiness_id)


def get_latest_post_freeze_readiness() -> Optional[PostFreezeExpansionReadiness]:
    """Get the most recent readiness evaluation."""
    if not _POST_FREEZE_READINESS_ORDER:
        return None
    latest_id = _POST_FREEZE_READINESS_ORDER[-1]
    return POST_FREEZE_EXPANSION_READINESS_INDEX.get(latest_id)


def list_post_freeze_readiness() -> List[PostFreezeExpansionReadiness]:
    """List all readiness evaluations in registration order."""
    return [
        POST_FREEZE_EXPANSION_READINESS_INDEX[rid]
        for rid in _POST_FREEZE_READINESS_ORDER
        if rid in POST_FREEZE_EXPANSION_READINESS_INDEX
    ]


def list_readiness_by_gate(
    gate: PostFreezeGate,
) -> List[PostFreezeExpansionReadiness]:
    """List readiness evaluations by gate."""
    return [
        r for r in list_post_freeze_readiness()
        if r.gate == gate
    ]


def list_readiness_for_proposal(
    proposal_id: str,
) -> List[PostFreezeExpansionReadiness]:
    """List readiness evaluations for a specific proposal."""
    return [
        r for r in list_post_freeze_readiness()
        if r.proposal_id == proposal_id
    ]


def get_post_freeze_readiness_count() -> int:
    """Get total readiness evaluation count."""
    return len(POST_FREEZE_EXPANSION_READINESS_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# Readiness evaluation
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_post_freeze_readiness(
    proposal: PostFreezeExpansionProposal,
) -> PostFreezeExpansionReadiness:
    """
    Evaluate readiness for a post-freeze proposal.

    Checks:
      - Freeze compatibility (shallow 7Z read)
      - Required reviews declared
      - No execution authority
      - No machine output authority
      - No baseline rewrite
      - No ontology mutation
    """
    # Check freeze compatibility
    freeze_compatible, freeze_exists, freeze_status, freeze_blocking_issues = \
        validate_freeze_compatibility(proposal.depends_on_freeze_id)

    required_reviews_declared = len(proposal.required_reviews) > 0

    target_layer_clear = proposal.target_layer in VALID_TARGET_LAYERS

    governance_risks_complete = len(proposal.governance_risks) > 0

    gate, blocking_issues, warnings = classify_post_freeze_gate(
        baseline_rewrite_requested=proposal.baseline_rewrite_requested,
        execution_authorized=proposal.execution_authorized,
        machine_output_allowed=proposal.machine_output_allowed,
        implementation_authorized=proposal.implementation_authorized,
        ontology_mutation_requested=proposal.ontology_mutation_requested,
        depends_on_freeze_id=proposal.depends_on_freeze_id,
        freeze_exists=freeze_exists,
        required_reviews_declared=required_reviews_declared,
        target_layer_clear=target_layer_clear,
        governance_risks_complete=governance_risks_complete,
    )

    readiness = PostFreezeExpansionReadiness(
        proposal_id=proposal.proposal_id,
        freeze_compatible=freeze_compatible,
        freeze_exists=freeze_exists,
        freeze_status=freeze_status,
        freeze_blocking_issues=freeze_blocking_issues,
        required_reviews_declared=required_reviews_declared,
        no_execution_authority=not proposal.execution_authorized,
        no_machine_output_authority=not proposal.machine_output_allowed,
        ontology_mutation_requested=proposal.ontology_mutation_requested,
        baseline_rewrite_requested=proposal.baseline_rewrite_requested,
        gate=gate,
        blocking_issues=blocking_issues,
        warnings=warnings,
    )

    readiness.deterministic_readiness_hash = readiness.compute_hash()
    return readiness


# ─────────────────────────────────────────────────────────────────────────────
# CI summary
# ─────────────────────────────────────────────────────────────────────────────

PostFreezeCIStatus = Literal["pass", "warn", "fail"]


def build_post_freeze_ci_summary() -> Dict[str, Any]:
    """
    Build CI summary for post-freeze expansion state.

    Returns summary object with:
      - total_proposals
      - total_readiness_evaluations
      - green_count
      - yellow_count
      - red_count
      - missing_freeze_ref_count
      - baseline_rewrite_request_count
      - ontology_mutation_request_count
      - execution_request_count
      - machine_output_request_count
      - status: pass|warn|fail
      - blocking_issues
      - warnings
    """
    proposals = list_post_freeze_proposals()
    readiness_evals = list_post_freeze_readiness()

    green_count = sum(1 for r in readiness_evals if r.gate == "green")
    yellow_count = sum(1 for r in readiness_evals if r.gate == "yellow")
    red_count = sum(1 for r in readiness_evals if r.gate == "red")

    missing_freeze_ref_count = sum(
        1 for p in proposals if p.depends_on_freeze_id is None
    )

    baseline_rewrite_request_count = sum(
        1 for p in proposals if p.baseline_rewrite_requested
    )

    ontology_mutation_request_count = sum(
        1 for p in proposals if p.ontology_mutation_requested
    )

    execution_request_count = sum(
        1 for p in proposals if p.execution_authorized
    )

    machine_output_request_count = sum(
        1 for p in proposals if p.machine_output_allowed
    )

    blocking_issues: List[str] = []
    warnings: List[str] = []

    if red_count > 0:
        blocking_issues.append(f"{red_count} proposal(s) with RED gate")

    if baseline_rewrite_request_count > 0:
        blocking_issues.append(f"{baseline_rewrite_request_count} baseline rewrite request(s)")

    if ontology_mutation_request_count > 0:
        blocking_issues.append(f"{ontology_mutation_request_count} ontology mutation request(s)")

    if execution_request_count > 0:
        blocking_issues.append(f"{execution_request_count} execution request(s)")

    if machine_output_request_count > 0:
        blocking_issues.append(f"{machine_output_request_count} machine output request(s)")

    if yellow_count > 0:
        warnings.append(f"{yellow_count} proposal(s) with YELLOW gate")

    if missing_freeze_ref_count > 0:
        warnings.append(f"{missing_freeze_ref_count} proposal(s) missing freeze reference")

    # Determine status
    status: PostFreezeCIStatus
    if blocking_issues:
        status = "fail"
    elif warnings:
        status = "warn"
    else:
        status = "pass"

    return {
        "total_proposals": len(proposals),
        "total_readiness_evaluations": len(readiness_evals),
        "green_count": green_count,
        "yellow_count": yellow_count,
        "red_count": red_count,
        "missing_freeze_ref_count": missing_freeze_ref_count,
        "baseline_rewrite_request_count": baseline_rewrite_request_count,
        "ontology_mutation_request_count": ontology_mutation_request_count,
        "execution_request_count": execution_request_count,
        "machine_output_request_count": machine_output_request_count,
        "status": status,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
    }


def get_post_freeze_status_summary() -> Dict[str, Any]:
    """Get aggregated status summary."""
    proposals = list_post_freeze_proposals()
    readiness_evals = list_post_freeze_readiness()

    latest_proposal = get_latest_post_freeze_proposal()
    latest_readiness = get_latest_post_freeze_readiness()

    return {
        "total_proposals": len(proposals),
        "draft_proposals": sum(1 for p in proposals if p.proposal_state == "draft"),
        "submitted_proposals": sum(
            1 for p in proposals if p.proposal_state == "submitted_for_review"
        ),
        "total_readiness_evaluations": len(readiness_evals),
        "green_count": sum(1 for r in readiness_evals if r.gate == "green"),
        "yellow_count": sum(1 for r in readiness_evals if r.gate == "yellow"),
        "red_count": sum(1 for r in readiness_evals if r.gate == "red"),
        "latest_proposal_id": latest_proposal.proposal_id if latest_proposal else None,
        "latest_proposal_title": latest_proposal.title if latest_proposal else None,
        "latest_readiness_id": latest_readiness.readiness_id if latest_readiness else None,
        "latest_readiness_gate": latest_readiness.gate if latest_readiness else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

def clear_post_freeze_indexes_for_tests() -> None:
    """Clear all indexes for testing."""
    POST_FREEZE_EXPANSION_PROPOSAL_INDEX.clear()
    POST_FREEZE_EXPANSION_READINESS_INDEX.clear()
    _POST_FREEZE_PROPOSAL_ORDER.clear()
    _POST_FREEZE_READINESS_ORDER.clear()


def get_post_freeze_index_counts() -> Dict[str, int]:
    """Get index counts for debugging."""
    return {
        "proposals": len(POST_FREEZE_EXPANSION_PROPOSAL_INDEX),
        "readiness": len(POST_FREEZE_EXPANSION_READINESS_INDEX),
        "proposal_order": len(_POST_FREEZE_PROPOSAL_ORDER),
        "readiness_order": len(_POST_FREEZE_READINESS_ORDER),
    }
