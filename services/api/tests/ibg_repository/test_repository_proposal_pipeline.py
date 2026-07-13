"""
Invariant tests for the canonical RepositoryProposalPipeline.

These bind the ratified mission: the pipeline REUSES existing contracts, PRESERVES provenance, does
NOT upgrade authority, TERMINATES at the human-review boundary, and performs NO git / filesystem /
GitHub / network mutation. It is orchestration-only — it must not duplicate contract logic.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import app.ibg_repository as ibg_repo
from app.ibg_repository import (
    CANONICAL_PIPELINE_MISSION,
    PIPELINE_TERMINAL_STAGE,
    EvidenceContractError,
    RepositoryChangeProposal,
    RepositoryChangeProposalError,
    RepositoryProposalPipeline,
    RepositoryProposalPipelineResult,
    RepositoryReviewBundle,
    RepositoryReviewBundleError,
    build_proposal_target_binding,
    build_repository_change_proposal,
    run_repository_proposal_pipeline,
)


def _run(make_candidate, make_packet, candidate=None, **over):
    files = ("services/api/app/ibg_repository/proposal_target.py",)
    kwargs = dict(
        candidate=candidate if candidate is not None else make_candidate(),
        repository_id="luthiers-toolbox",
        base_revision="b396284c",
        authorized_target_paths=list(files),
        change_intent="compose the canonical pipeline",
        proposed_branch="feature/ibg-x",
        cbsp21_packet=make_packet(files=files),
        target_branch="main",
    )
    kwargs.update(over)
    return run_repository_proposal_pipeline(**kwargs)


# --- reuse existing contracts ------------------------------------------

def test_result_types_are_existing_contracts(make_candidate, make_packet):
    r = _run(make_candidate, make_packet)
    assert isinstance(r, RepositoryProposalPipelineResult)
    assert isinstance(r.proposal, RepositoryChangeProposal)
    assert isinstance(r.review_bundle, RepositoryReviewBundle)


def test_bundle_embeds_the_same_proposal_no_remodel(make_candidate, make_packet):
    r = _run(make_candidate, make_packet)
    # the bundle carries the proposal's OWN canonical serialization, not a re-modeled copy
    assert r.review_bundle.proposal == r.proposal.to_canonical_dict()
    assert r.draft_pull_request is r.review_bundle.draft_pull_request


def test_pipeline_equals_direct_composition(make_candidate, make_packet):
    # Orchestration adds no logic: same candidate + inputs -> same proposal id as building directly.
    cand = make_candidate()
    packet = make_packet(files=("services/api/app/ibg_repository/proposal_target.py",))
    r = _run(make_candidate, make_packet, candidate=cand, cbsp21_packet=packet)
    binding = build_proposal_target_binding(
        cand,
        repository_id="luthiers-toolbox",
        base_revision="b396284c",
        authorized_target_paths=["services/api/app/ibg_repository/proposal_target.py"],
        change_intent="compose the canonical pipeline",
    )
    direct = build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/ibg-x"
    )
    assert r.proposal.proposal_id == direct.proposal_id


def test_convenience_matches_class(make_candidate, make_packet):
    cand = make_candidate()
    packet = make_packet(files=("services/api/app/ibg_repository/proposal_target.py",))
    common = dict(
        candidate=cand,
        repository_id="luthiers-toolbox",
        base_revision="b396284c",
        authorized_target_paths=["services/api/app/ibg_repository/proposal_target.py"],
        change_intent="x",
        proposed_branch="feature/ibg-x",
        cbsp21_packet=packet,
        target_branch="main",
    )
    a = run_repository_proposal_pipeline(**common).to_canonical_dict()
    b = RepositoryProposalPipeline().run(**common).to_canonical_dict()
    assert a == b


# --- provenance preserved ----------------------------------------------

def test_provenance_reference_preserved(make_candidate, make_packet):
    r = _run(make_candidate, make_packet)
    t = r.proposal.target
    assert r.provenance_reference == {
        "evidence_candidate_id": t.evidence_candidate_id,
        "evidence_provenance_hash": t.evidence_provenance_hash,
        "producing_subsystem": t.producing_subsystem,
        "source_authority_state": t.source_authority_state,
    }


def test_verified_provenance_lineage_flows_through(make_candidate, make_packet):
    cand = make_candidate()
    expected_hash = cand.provenance.compute_provenance_hash()

    class _Prov:
        def compute_provenance_hash(self):
            return expected_hash

        def to_dict(self):
            return {"lineage": "ok"}

    r = _run(make_candidate, make_packet, candidate=cand, provenance=_Prov())
    assert r.review_bundle.provenance_lineage_embedded is True
    assert r.review_bundle.provenance_lineage == {"lineage": "ok"}


def test_provenance_mismatch_propagates(make_candidate, make_packet):
    class _BadProv:
        def compute_provenance_hash(self):
            return "deadbeefdeadbeef"

        def to_dict(self):
            return {}

    with pytest.raises(RepositoryReviewBundleError):
        _run(make_candidate, make_packet, provenance=_BadProv())


# --- authority not upgraded --------------------------------------------

def test_authority_not_promoted(make_candidate, make_packet):
    cand = make_candidate()
    before = cand.authority_state
    r = _run(make_candidate, make_packet, candidate=cand)
    assert cand.authority_state == before  # candidate not mutated
    assert r.proposal.target.source_authority_state == before.value  # carried, not upgraded


# --- terminates at human review ----------------------------------------

def test_terminates_at_human_review(make_candidate, make_packet):
    r = _run(make_candidate, make_packet)
    assert r.terminates_at == PIPELINE_TERMINAL_STAGE == "human_review"


def test_pipeline_exposes_only_run_no_execution_verb():
    public = [m for m in dir(RepositoryProposalPipeline) if not m.startswith("_")]
    assert public == ["run"]
    forbidden = ("execute", "commit", "push", "merge", "pull_request", "mutate", "apply", "git", "github")
    for name in public:
        assert not any(tok in name.lower() for tok in forbidden)


def test_result_is_frozen(make_candidate, make_packet):
    r = _run(make_candidate, make_packet)
    with pytest.raises(FrozenInstanceError):
        r.terminates_at = "execute"  # type: ignore[misc]


# --- determinism --------------------------------------------------------

def test_deterministic_output(make_candidate, make_packet):
    cand = make_candidate()
    packet = make_packet(files=("services/api/app/ibg_repository/proposal_target.py",))
    a = _run(make_candidate, make_packet, candidate=cand, cbsp21_packet=packet).to_canonical_dict()
    b = _run(make_candidate, make_packet, candidate=cand, cbsp21_packet=packet).to_canonical_dict()
    assert a == b


# --- fail-closed propagation (pipeline adds no catch) ------------------

def test_bad_candidate_propagates(make_candidate, make_packet):
    # The PR-A binding builder's own fail-closed error propagates UNWRAPPED (no pipeline error).
    with pytest.raises(EvidenceContractError):
        _run(make_candidate, make_packet, candidate={"not": "a candidate"})


def test_unsafe_proposed_branch_propagates(make_candidate, make_packet):
    with pytest.raises(RepositoryChangeProposalError):
        _run(make_candidate, make_packet, proposed_branch="bad..branch")


def test_malformed_review_package_propagates(make_candidate, make_packet):
    # Optional-but-malformed input (not None) fails closed via the bundle builder, unwrapped.
    with pytest.raises(RepositoryReviewBundleError):
        _run(make_candidate, make_packet, review_package=object())


def test_malformed_workspace_metadata_propagates(make_candidate, make_packet):
    with pytest.raises(RepositoryReviewBundleError):
        _run(make_candidate, make_packet, workspace_metadata={"unrecognized_field": 1})


def test_target_branch_is_required(make_candidate, make_packet):
    # The canonical entry point must not silently assume "main": omitting target_branch is a
    # TypeError, forcing the caller to state the intended PR base.
    files = ("services/api/app/ibg_repository/proposal_target.py",)
    with pytest.raises(TypeError):
        run_repository_proposal_pipeline(
            candidate=make_candidate(),
            repository_id="luthiers-toolbox",
            base_revision="b396284c",
            authorized_target_paths=list(files),
            change_intent="x",
            proposed_branch="feature/ibg-x",
            cbsp21_packet=make_packet(files=files),
        )


# --- constitutional invariant: no git/network/GitHub in the module -----

def test_pipeline_module_has_no_git_or_network():
    # Import-precise (AST) so prose like "create pull requests" in the mission docstring is not a
    # false positive — we forbid the *imports*, not the words.
    import ast

    src = (Path(ibg_repo.__file__).parent / "repository_proposal_pipeline.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = (node.module or "").split(".")[0]
            if base:
                imported.add(base)
            # a relative "from .git_runner import ..." would land here as node.module
            if node.module:
                assert "git_runner" not in node.module, "pipeline must not import PR-B git_runner"
    forbidden = {"subprocess", "requests", "httpx", "urllib", "socket", "http", "pygithub", "os"}
    leaked = imported & forbidden
    assert not leaked, f"pipeline must not import {leaked}"


def test_mission_constant_present():
    assert "terminates at the human-review boundary" in CANONICAL_PIPELINE_MISSION
    assert "only composes them" in CANONICAL_PIPELINE_MISSION
