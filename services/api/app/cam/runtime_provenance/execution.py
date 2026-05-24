"""
Replay Execution Harness.

Sprint: MRP-5O
Status: PROTOTYPE

Provides deterministic replay execution for RuntimeReplayBundles.
Reproduces artifacts using mock adapter execution and compares
against recorded artifact hashes.

ARCHITECTURAL PRINCIPLE:
    Replay is evidentiary reproduction, not execution authority.

    Replay may:
    - Reproduce execution artifacts
    - Verify deterministic consistency
    - Report divergence

    Replay may NOT:
    - Re-authorize execution
    - Reinterpret topology
    - Mutate certification
    - Infer missing metadata
    - Silently repair divergence
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import uuid

from .classification import DivergenceSeverity, RegressionStatus, ReplayExecutionStatus
from .contracts import RuntimeReplayBundle
from .integrity import verify_replay_bundle_integrity
from .serialization import stable_json_dumps


@dataclass
class ReplayExecutionResult:
    """Result of replay execution attempt."""

    status: ReplayExecutionStatus
    run_id: str
    bundle_run_id: str
    reproduced_hash: Optional[str] = None
    reproduced_size: Optional[int] = None
    execution_time_ms: float = 0.0
    message: str = ""
    constraints: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "run_id": self.run_id,
            "bundle_run_id": self.bundle_run_id,
            "reproduced_hash": self.reproduced_hash,
            "reproduced_size": self.reproduced_size,
            "execution_time_ms": self.execution_time_ms,
            "message": self.message,
            "constraints": self.constraints,
            "timestamp": self.timestamp,
        }


@dataclass
class ReproducedArtifact:
    """Artifact produced by replay execution."""

    artifact_id: str
    artifact_type: str
    content_bytes: bytes
    content_hash: str
    content_size: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_bytes(
        cls,
        content: bytes,
        artifact_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ReproducedArtifact":
        """Create from raw bytes."""
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        return cls(
            artifact_id=f"reproduced-{uuid.uuid4()}",
            artifact_type=artifact_type,
            content_bytes=content,
            content_hash=content_hash,
            content_size=len(content),
            metadata=metadata or {},
        )


class ReplayExecutionHarness:
    """
    Executes deterministic mock replay from RuntimeReplayBundles.

    Responsibilities:
    - Verify bundle integrity
    - Reject non-admitted bundles
    - Reject adapter mismatches (only mock adapter supported)
    - Invoke deterministic mock replay path
    - Produce ReplayExecutionResult

    Forbidden:
    - Re-admission
    - Semantic inference
    - Topology mutation
    - Provenance rewrite
    """

    SUPPORTED_ADAPTERS = {"mock"}

    def __init__(self):
        self._execution_count = 0

    def execute(self, bundle: RuntimeReplayBundle) -> ReplayExecutionResult:
        """
        Execute deterministic replay of a bundle.

        Returns ReplayExecutionResult with status indicating success or failure reason.
        """
        import time

        start_time = time.perf_counter()
        run_id = str(uuid.uuid4())
        bundle_run_id = bundle.provenance.run_id

        result = self._validate_for_replay(bundle, run_id, bundle_run_id)
        if result is not None:
            return result

        try:
            reproduced = self._execute_mock_replay(bundle)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            self._execution_count += 1

            return ReplayExecutionResult(
                status=ReplayExecutionStatus.REPLAYED,
                run_id=run_id,
                bundle_run_id=bundle_run_id,
                reproduced_hash=reproduced.content_hash,
                reproduced_size=reproduced.content_size,
                execution_time_ms=elapsed_ms,
                message="Replay execution completed successfully",
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ReplayExecutionResult(
                status=ReplayExecutionStatus.NON_REPLAYABLE,
                run_id=run_id,
                bundle_run_id=bundle_run_id,
                execution_time_ms=elapsed_ms,
                message=f"Replay execution failed: {str(e)}",
                constraints=[str(e)],
            )

    def _validate_for_replay(
        self, bundle: RuntimeReplayBundle, run_id: str, bundle_run_id: str
    ) -> Optional[ReplayExecutionResult]:
        """
        Validate bundle is eligible for replay.

        Returns ReplayExecutionResult if validation fails, None if OK.
        """
        integrity_result = verify_replay_bundle_integrity(bundle)
        if not integrity_result.passed:
            return ReplayExecutionResult(
                status=ReplayExecutionStatus.INVALID_BUNDLE,
                run_id=run_id,
                bundle_run_id=bundle_run_id,
                message=f"Bundle integrity check failed: {integrity_result.message}",
                constraints=[c.message for c in integrity_result.failed_checks],
            )

        admission = bundle.provenance.admission_lineage
        if admission.decision not in ("ADMITTED", "CONDITIONALLY_ADMITTED"):
            return ReplayExecutionResult(
                status=ReplayExecutionStatus.REJECTED_ADMISSION,
                run_id=run_id,
                bundle_run_id=bundle_run_id,
                message=f"Bundle admission status is {admission.decision}, replay requires ADMITTED",
                constraints=[f"admission_decision={admission.decision}"],
            )

        adapter_id = bundle.provenance.adapter_id
        if adapter_id not in self.SUPPORTED_ADAPTERS:
            return ReplayExecutionResult(
                status=ReplayExecutionStatus.NON_REPLAYABLE,
                run_id=run_id,
                bundle_run_id=bundle_run_id,
                message=f"Adapter '{adapter_id}' not supported for mock replay",
                constraints=[f"adapter_id={adapter_id} not in {self.SUPPORTED_ADAPTERS}"],
            )

        if not bundle.replayable:
            return ReplayExecutionResult(
                status=ReplayExecutionStatus.NON_REPLAYABLE,
                run_id=run_id,
                bundle_run_id=bundle_run_id,
                message="Bundle marked as non-replayable",
                constraints=bundle.replay_constraints,
            )

        return None

    def _execute_mock_replay(self, bundle: RuntimeReplayBundle) -> ReproducedArtifact:
        """
        Execute deterministic mock replay.

        Produces artifact bytes from the bundle's recorded topology hash
        using deterministic mock execution.
        """
        provenance = bundle.provenance
        artifact_type = provenance.artifact_lineage.artifact_type
        translator_id = provenance.translator_id
        topology_hash = provenance.source_topology_hash
        topology_id = provenance.source_topology_id

        content = self._generate_deterministic_mock_content(
            topology_hash=topology_hash,
            topology_id=topology_id,
            artifact_type=artifact_type,
            translator_id=translator_id,
        )

        return ReproducedArtifact.from_bytes(
            content=content,
            artifact_type=artifact_type,
            metadata={
                "replay_run_id": provenance.run_id,
                "translator_id": translator_id,
            },
        )

    def _generate_deterministic_mock_content(
        self,
        topology_hash: str,
        topology_id: str,
        artifact_type: str,
        translator_id: str,
    ) -> bytes:
        """
        Generate deterministic mock artifact content.

        Uses the recorded topology hash to ensure identical input
        produces identical output across replay executions.
        """
        content = f"""\
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Deterministic Mock Replay'),'2;1');
FILE_NAME('replay_{topology_hash}.stp','2026-01-01T00:00:00',('MockReplay'),('Luthiers Toolbox'),'MRP-5O Prototype','ReplayExecutionHarness','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
/* Deterministic replay from topology: {topology_id} */
/* Topology hash: {topology_hash} */
/* Artifact type: {artifact_type} */
/* Translator: {translator_id} */
#1=PRODUCT('Replay','Replay Product',$,(#2));
#2=PRODUCT_CONTEXT('',#3,'mechanical');
#3=APPLICATION_CONTEXT('deterministic replay');
ENDSEC;
END-ISO-10303-21;
"""
        return content.encode("utf-8")

    @property
    def execution_count(self) -> int:
        """Number of successful replay executions."""
        return self._execution_count


def execute_replay(bundle: RuntimeReplayBundle) -> ReplayExecutionResult:
    """Convenience function to execute replay."""
    harness = ReplayExecutionHarness()
    return harness.execute(bundle)
