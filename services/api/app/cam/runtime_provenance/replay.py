"""
Runtime Replay Engine.

Sprint: MRP-5N
Status: PROTOTYPE

Verifies replay bundles for audit and reproducibility.
Does NOT re-execute the pipeline — verification only.

ARCHITECTURAL PRINCIPLE:
    Replay observes and verifies.
    Replay does not:
    - re-authorize execution,
    - repair invalid topology,
    - infer missing data,
    - mutate state.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .contracts import (
    ReplayStatus,
    ReplayVerificationResult,
    RuntimeReplayBundle,
    RuntimeTraceEvent,
    TraceEventType,
)
from .exceptions import NonReplayableError, ReplayError
from .integrity import (
    BundleIntegrityResult,
    verify_replay_bundle_integrity,
)


class RuntimeReplayEngine:
    """
    Engine for replay verification.

    Verifies that a replay bundle is valid and replayable.
    Does NOT re-execute the pipeline.

    Usage:
        engine = RuntimeReplayEngine()
        result = engine.verify(bundle)

        if result.passed:
            print("Bundle verified successfully")
        else:
            print(f"Verification failed: {result.message}")
    """

    def __init__(self, strict: bool = False):
        """
        Initialize the replay engine.

        Args:
            strict: If True, raises exceptions on verification failure
        """
        self._strict = strict

    def verify(
        self,
        bundle: RuntimeReplayBundle,
        verify_replayable: bool = True,
    ) -> ReplayVerificationResult:
        """
        Verify a replay bundle.

        Runs all integrity checks and validates the bundle structure.

        Args:
            bundle: The replay bundle to verify
            verify_replayable: If True, also check replayability status

        Returns:
            ReplayVerificationResult

        Raises:
            ReplayError: If strict mode and verification fails
            NonReplayableError: If strict mode and bundle is non-replayable
        """
        if verify_replayable and not bundle.replayable:
            result = ReplayVerificationResult.non_replayable(
                bundle_id=bundle.bundle_id,
                constraints=bundle.replay_constraints,
                message="Bundle is marked as non-replayable",
            )

            if self._strict:
                raise NonReplayableError(
                    message=result.message,
                    constraints=bundle.replay_constraints,
                )

            return result

        integrity_result = verify_replay_bundle_integrity(bundle)

        if integrity_result.passed:
            checks_passed = [c.check_name for c in integrity_result.passed_checks]

            event = RuntimeTraceEvent.create(
                event_type=TraceEventType.REPLAY_VERIFIED,
                details={
                    "bundle_id": bundle.bundle_id,
                    "checks_passed": len(checks_passed),
                },
            )

            return ReplayVerificationResult.success(
                bundle_id=bundle.bundle_id,
                checks_passed=checks_passed,
            )

        checks_passed = [c.check_name for c in integrity_result.passed_checks]
        checks_failed = [c.check_name for c in integrity_result.failed_checks]

        result = ReplayVerificationResult.failure(
            bundle_id=bundle.bundle_id,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            message=integrity_result.message,
        )

        if self._strict:
            raise ReplayError(
                message=result.message,
                reason="INTEGRITY_FAILURE",
                details={
                    "checks_failed": checks_failed,
                    "checks_passed": checks_passed,
                },
            )

        return result

    def verify_or_raise(
        self,
        bundle: RuntimeReplayBundle,
    ) -> ReplayVerificationResult:
        """
        Verify and raise on any failure.

        Convenience method that always uses strict mode.
        """
        old_strict = self._strict
        self._strict = True
        try:
            return self.verify(bundle)
        finally:
            self._strict = old_strict

    def compare_bundles(
        self,
        bundle1: RuntimeReplayBundle,
        bundle2: RuntimeReplayBundle,
    ) -> Dict[str, Any]:
        """
        Compare two replay bundles for equivalence.

        Useful for regression testing.

        Args:
            bundle1: First bundle
            bundle2: Second bundle

        Returns:
            Comparison result with differences
        """
        differences = []

        if bundle1.provenance.source_topology_hash != bundle2.provenance.source_topology_hash:
            differences.append({
                "field": "source_topology_hash",
                "bundle1": bundle1.provenance.source_topology_hash,
                "bundle2": bundle2.provenance.source_topology_hash,
            })

        if bundle1.provenance.artifact_lineage.content_hash != bundle2.provenance.artifact_lineage.content_hash:
            differences.append({
                "field": "artifact_content_hash",
                "bundle1": bundle1.provenance.artifact_lineage.content_hash,
                "bundle2": bundle2.provenance.artifact_lineage.content_hash,
            })

        if bundle1.provenance.validation_lineage.signature_validation_hash != bundle2.provenance.validation_lineage.signature_validation_hash:
            differences.append({
                "field": "validation_signature_hash",
                "bundle1": bundle1.provenance.validation_lineage.signature_validation_hash,
                "bundle2": bundle2.provenance.validation_lineage.signature_validation_hash,
            })

        if bundle1.provenance.translator_id != bundle2.provenance.translator_id:
            differences.append({
                "field": "translator_id",
                "bundle1": bundle1.provenance.translator_id,
                "bundle2": bundle2.provenance.translator_id,
            })

        if bundle1.provenance.adapter_id != bundle2.provenance.adapter_id:
            differences.append({
                "field": "adapter_id",
                "bundle1": bundle1.provenance.adapter_id,
                "bundle2": bundle2.provenance.adapter_id,
            })

        event_count_1 = len(bundle1.provenance.trace_events)
        event_count_2 = len(bundle2.provenance.trace_events)
        if event_count_1 != event_count_2:
            differences.append({
                "field": "trace_event_count",
                "bundle1": event_count_1,
                "bundle2": event_count_2,
            })

        return {
            "equivalent": len(differences) == 0,
            "difference_count": len(differences),
            "differences": differences,
            "bundle1_id": bundle1.bundle_id,
            "bundle2_id": bundle2.bundle_id,
        }

    def get_bundle_summary(
        self,
        bundle: RuntimeReplayBundle,
    ) -> Dict[str, Any]:
        """
        Get human-readable summary of a bundle.

        Useful for inspection utilities.

        Args:
            bundle: Bundle to summarize

        Returns:
            Summary dictionary
        """
        provenance = bundle.provenance

        return {
            "bundle_id": bundle.bundle_id,
            "run_id": provenance.run_id,
            "replayable": bundle.replayable,
            "version": bundle.version,
            "source": {
                "topology_id": provenance.source_topology_id,
                "topology_hash": provenance.source_topology_hash[:16] + "..." if provenance.source_topology_hash else "N/A",
            },
            "validation": {
                "request_id": provenance.validation_lineage.request_id,
                "tier": provenance.validation_lineage.tier,
                "passed": provenance.validation_lineage.passed,
            },
            "admission": {
                "decision": provenance.admission_lineage.decision,
                "authorized_adapters": provenance.admission_lineage.authorized_adapters,
            },
            "execution": {
                "translator_id": provenance.translator_id,
                "adapter_id": provenance.adapter_id,
            },
            "artifact": {
                "id": provenance.artifact_lineage.artifact_id,
                "type": provenance.artifact_lineage.artifact_type,
                "size_bytes": provenance.artifact_lineage.content_size_bytes,
                "hash": provenance.artifact_lineage.content_hash[:16] + "..." if provenance.artifact_lineage.content_hash else "N/A",
            },
            "trace": {
                "event_count": len(provenance.trace_events),
                "events": [e.event_type.value for e in provenance.trace_events],
            },
            "timestamps": {
                "created_at": provenance.created_at,
            },
            "constraints": bundle.replay_constraints if bundle.replay_constraints else None,
            "hashes": {
                "provenance_hash": provenance.provenance_hash[:16] + "..." if provenance.provenance_hash else "N/A",
                "bundle_hash": bundle.bundle_hash[:16] + "..." if bundle.bundle_hash else "N/A",
            },
        }


def verify_bundle(
    bundle: RuntimeReplayBundle,
    strict: bool = False,
) -> ReplayVerificationResult:
    """
    Convenience function to verify a bundle.

    Equivalent to:
        RuntimeReplayEngine(strict=strict).verify(bundle)
    """
    engine = RuntimeReplayEngine(strict=strict)
    return engine.verify(bundle)


def get_bundle_summary(bundle: RuntimeReplayBundle) -> Dict[str, Any]:
    """
    Convenience function to get bundle summary.

    Equivalent to:
        RuntimeReplayEngine().get_bundle_summary(bundle)
    """
    engine = RuntimeReplayEngine()
    return engine.get_bundle_summary(bundle)
