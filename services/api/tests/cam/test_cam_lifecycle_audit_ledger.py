"""
Tests for CAM lifecycle audit ledger determinism.

CI-RED-024 / C24: rmos_summary carries persistence metadata such as run_id and
must stay outside deterministic_hash because that hash is consumed as provenance
ancestry.
"""

from app.cam.cam_lifecycle_audit_ledger import generate_lifecycle_audit_snapshot
from app.cam.cam_lifecycle_policy_engine import LifecyclePolicyEvaluation
from app.cam.export_lifecycle_orchestrator import GovernedExportLifecycleReport


def _policy_evaluation() -> LifecyclePolicyEvaluation:
    return LifecyclePolicyEvaluation(
        operation="nut_slot",
        allowed=True,
        lifecycle_gate="green",
        exportability_class="validation_only",
        maturity="stable",
        policy_checks=["test policy check"],
        blocking_issues=[],
        warnings=[],
        preview_allowed=True,
        export_object_allowed=True,
        machine_validation_allowed=True,
        translator_validation_allowed=True,
        rmos_persistence_allowed=True,
    )


def _lifecycle_report(*, export_ready: bool = True) -> GovernedExportLifecycleReport:
    return GovernedExportLifecycleReport(
        lifecycle_gate="green",
        export_ready=export_ready,
        machine_ready=False,
        translator_ready=True,
        machine_output_generated=False,
        translator_output_generated=False,
        preview_gate="green",
        preview_operation="nut_slot",
        machine_validation_gate="green",
        machine_validation_compatible=True,
        translator_validation_gate="green",
        translator_validation_compatible=True,
        blocking_issues=[],
        warnings=[],
    )


def _rmos_summary(run_id: str) -> dict:
    return {
        "persisted": True,
        "run_id": run_id,
        "artifact_count": 2,
        "artifact_kinds": ["export_object", "lifecycle_report"],
    }


def test_rmos_summary_run_id_does_not_change_deterministic_hash():
    """Identical audited content keeps the same hash across different RMOS runs."""
    policy = _policy_evaluation()

    snapshot_a = generate_lifecycle_audit_snapshot(
        lifecycle_report=_lifecycle_report(),
        policy_evaluation=policy,
    )
    snapshot_b = generate_lifecycle_audit_snapshot(
        lifecycle_report=_lifecycle_report(),
        policy_evaluation=policy,
    )

    snapshot_a.rmos_summary = _rmos_summary("RUN-A")
    snapshot_b.rmos_summary = _rmos_summary("RUN-B")

    assert snapshot_a.deterministic_hash == snapshot_b.deterministic_hash


def test_rmos_summary_mutation_does_not_recompute_hash():
    """A post-generation run_id mutation must not affect the stored audit hash."""
    snapshot = generate_lifecycle_audit_snapshot(
        lifecycle_report=_lifecycle_report(),
        policy_evaluation=_policy_evaluation(),
    )
    original_hash = snapshot.deterministic_hash

    snapshot.rmos_summary = _rmos_summary("RUN-FIRST")
    first_run_hash = snapshot.deterministic_hash
    snapshot.rmos_summary = _rmos_summary("RUN-SECOND")

    assert snapshot.deterministic_hash == first_run_hash == original_hash


def test_audited_content_change_changes_deterministic_hash():
    """The determinism guard is not asserting a constant hash."""
    policy = _policy_evaluation()

    ready_snapshot = generate_lifecycle_audit_snapshot(
        lifecycle_report=_lifecycle_report(export_ready=True),
        policy_evaluation=policy,
    )
    not_ready_snapshot = generate_lifecycle_audit_snapshot(
        lifecycle_report=_lifecycle_report(export_ready=False),
        policy_evaluation=policy,
    )

    assert ready_snapshot.deterministic_hash != not_ready_snapshot.deterministic_hash
