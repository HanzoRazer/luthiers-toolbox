from __future__ import annotations

import dataclasses

from app.ibg_repository import (
    build_cbsp21_patch_packet,
    build_proposal_target_binding,
    build_repository_change_proposal,
)

FILES = ("services/api/app/ibg_repository/proposal_target.py",)


def _reseal_plan(plan):
    """Re-derive the plan's content-addressed id after a deliberate edit.

    Isolates the defect under test: without resealing, ANY edit also trips
    ``execution.plan_id_matches_content_hash``, and the test could not tell the two apart.
    """
    return dataclasses.replace(plan, execution_plan_id="rep-" + plan.compute_plan_hash())


def _reseal_proposal(proposal):
    return dataclasses.replace(proposal, proposal_id="rcp-" + proposal.compute_proposal_hash())


def _finding(evaluation, check_id):
    for f in evaluation.all_findings():
        if f.check_id == check_id:
            return f
    raise AssertionError(f"no finding {check_id!r} in {[f.check_id for f in evaluation.all_findings()]}")


def _status(evaluation, check_id):
    return _finding(evaluation, check_id).status


def _packet(files=FILES, risk="low", verification=("pytest",), behavior_change="none", why="n/a"):
    return build_cbsp21_patch_packet(
        patch_id="IBG_TEST",
        title="test packet",
        intent="test intent",
        change_type="feat",
        behavior_change=behavior_change,
        risk_level=risk,
        paths_in_scope=list(files),
        files_expected_to_change=list(files),
        what_changed="adds a module",
        why_not_redundant=why,
        verification_commands=list(verification),
    )


def _proposal_with_packet(make_candidate, packet, files=FILES):
    binding = build_proposal_target_binding(
        make_candidate(),
        repository_id="luthiers-toolbox",
        base_revision="58ffadeb",
        authorized_target_paths=list(files),
        change_intent="evaluate",
    )
    return build_repository_change_proposal(
        target=binding, cbsp21_packet=packet, proposed_branch="feature/x"
    )
