"""Shared fixtures for ibg_repository contract tests.

Factory fixtures build a REAL governed BodyEvidenceCandidate (via the harvested
create_candidate_from_evidence) and a valid CBSP21 packet, so the contract tests exercise the
genuine evidence contract rather than a stub.
"""

from __future__ import annotations

import pytest

from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import BodyEvidence
from app.instrument_geometry.body.ibg.body_evidence_candidate import (
    create_candidate_from_evidence,
)
from app.ibg_repository import (
    build_cbsp21_patch_packet,
    build_proposal_target_binding,
    build_repository_change_proposal,
)


@pytest.fixture
def make_candidate():
    def _make():
        evidence = BodyEvidence(
            outline_points=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        )
        return create_candidate_from_evidence(
            evidence,
            source_artifact="tests/fixtures/body.dxf",
            extraction_method="body_isolation_stage",
        )

    return _make


@pytest.fixture
def make_packet():
    def _make(files=("services/api/app/ibg_repository/proposal_target.py",)):
        return build_cbsp21_patch_packet(
            patch_id="IBG_TEST",
            title="test packet",
            intent="test intent",
            change_type="feat",
            behavior_change="none",
            risk_level="low",
            paths_in_scope=list(files),
            files_expected_to_change=list(files),
            what_changed="adds a module",
            why_not_redundant="n/a",
            verification_commands=["pytest"],
        )

    return _make


@pytest.fixture
def make_proposal(make_candidate, make_packet):
    """Build a real, governed RepositoryChangeProposal (used by PR C review-package tests)."""

    def _make(
        files=("services/api/app/ibg_repository/proposal_target.py",),
        *,
        proposed_branch="feature/ibg-proposal",
        change_intent="assemble a repository proposal",
    ):
        binding = build_proposal_target_binding(
            make_candidate(),
            repository_id="luthiers-toolbox",
            base_revision="a708259d",
            authorized_target_paths=list(files),
            change_intent=change_intent,
        )
        return build_repository_change_proposal(
            target=binding,
            cbsp21_packet=make_packet(files=files),
            proposed_branch=proposed_branch,
        )

    return _make
