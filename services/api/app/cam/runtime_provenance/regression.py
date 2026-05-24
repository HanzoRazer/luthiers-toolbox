"""
Artifact Regression Comparison.

Sprint: MRP-5O
Status: PROTOTYPE

Provides artifact hash and metadata comparison for replay regression testing.
Compares reproduced artifacts against recorded baselines without repairing divergence.

ARCHITECTURAL PRINCIPLE:
    Divergence is reported, not repaired.

    If reproduced artifact differs from recorded artifact:
    - Report the divergence
    - Classify severity
    - DO NOT normalize silently
    - DO NOT repair artifact
    - DO NOT update baseline automatically
    - DO NOT mutate provenance
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .classification import DivergenceSeverity, RegressionStatus
from .contracts import ArtifactLineage, RuntimeReplayBundle
from .execution import ReplayExecutionResult, ReproducedArtifact


@dataclass
class DivergenceDetail:
    """Details of a specific divergence."""

    field: str
    expected: Any
    actual: Any
    severity: DivergenceSeverity
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity.value,
            "message": self.message,
        }


@dataclass
class ArtifactRegressionReport:
    """Report from artifact regression comparison."""

    status: RegressionStatus
    bundle_run_id: str
    replay_run_id: str
    baseline_hash: Optional[str]
    reproduced_hash: Optional[str]
    hash_match: bool
    divergences: List[DivergenceDetail] = field(default_factory=list)
    overall_severity: DivergenceSeverity = DivergenceSeverity.NONE
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "bundle_run_id": self.bundle_run_id,
            "replay_run_id": self.replay_run_id,
            "baseline_hash": self.baseline_hash,
            "reproduced_hash": self.reproduced_hash,
            "hash_match": self.hash_match,
            "divergences": [d.to_dict() for d in self.divergences],
            "overall_severity": self.overall_severity.value,
            "message": self.message,
            "timestamp": self.timestamp,
        }

    @property
    def passed(self) -> bool:
        """True if regression comparison passed (no divergence)."""
        return self.status == RegressionStatus.MATCH


class ArtifactRegressionComparator:
    """
    Compares reproduced artifacts against recorded baselines.

    Responsibilities:
    - Compare artifact hashes
    - Compare artifact metadata
    - Classify divergence severity
    - Produce ArtifactRegressionReport

    Forbidden:
    - Normalizing divergence
    - Repairing artifacts
    - Updating baselines
    - Mutating provenance
    """

    def compare(
        self,
        bundle: RuntimeReplayBundle,
        execution_result: ReplayExecutionResult,
        reproduced: Optional[ReproducedArtifact] = None,
    ) -> ArtifactRegressionReport:
        """
        Compare reproduced artifact against baseline in bundle.

        Args:
            bundle: The replay bundle containing baseline artifact lineage
            execution_result: Result from replay execution
            reproduced: Optional reproduced artifact for metadata comparison

        Returns:
            ArtifactRegressionReport with comparison results
        """
        baseline = bundle.provenance.artifact_lineage
        bundle_run_id = bundle.provenance.run_id

        if baseline.content_hash is None:
            return ArtifactRegressionReport(
                status=RegressionStatus.BASELINE_MISSING,
                bundle_run_id=bundle_run_id,
                replay_run_id=execution_result.run_id,
                baseline_hash=None,
                reproduced_hash=execution_result.reproduced_hash,
                hash_match=False,
                message="Baseline artifact hash is missing from bundle",
                overall_severity=DivergenceSeverity.BLOCKING,
            )

        if execution_result.reproduced_hash is None:
            return ArtifactRegressionReport(
                status=RegressionStatus.INVALID,
                bundle_run_id=bundle_run_id,
                replay_run_id=execution_result.run_id,
                baseline_hash=baseline.content_hash,
                reproduced_hash=None,
                hash_match=False,
                message="Reproduced artifact hash is missing",
                overall_severity=DivergenceSeverity.BLOCKING,
            )

        hash_match = baseline.content_hash == execution_result.reproduced_hash
        divergences = []

        if not hash_match:
            divergences.append(
                DivergenceDetail(
                    field="artifact_hash",
                    expected=baseline.content_hash,
                    actual=execution_result.reproduced_hash,
                    severity=DivergenceSeverity.BLOCKING,
                    message="Artifact hash mismatch",
                )
            )

        if baseline.content_size_bytes != execution_result.reproduced_size:
            severity = DivergenceSeverity.WARNING if hash_match else DivergenceSeverity.BLOCKING
            divergences.append(
                DivergenceDetail(
                    field="artifact_size",
                    expected=baseline.content_size_bytes,
                    actual=execution_result.reproduced_size,
                    severity=severity,
                    message="Artifact size mismatch",
                )
            )

        if reproduced is not None:
            divergences.extend(
                self._compare_metadata(baseline, reproduced)
            )

        status = RegressionStatus.MATCH if hash_match and not divergences else RegressionStatus.DIVERGED
        overall_severity = self._compute_overall_severity(divergences)

        return ArtifactRegressionReport(
            status=status,
            bundle_run_id=bundle_run_id,
            replay_run_id=execution_result.run_id,
            baseline_hash=baseline.content_hash,
            reproduced_hash=execution_result.reproduced_hash,
            hash_match=hash_match,
            divergences=divergences,
            overall_severity=overall_severity,
            message=self._build_message(status, divergences),
        )

    def _compare_metadata(
        self,
        baseline: ArtifactLineage,
        reproduced: ReproducedArtifact,
    ) -> List[DivergenceDetail]:
        """Compare artifact metadata fields."""
        divergences = []

        if baseline.artifact_type != reproduced.artifact_type:
            divergences.append(
                DivergenceDetail(
                    field="artifact_type",
                    expected=baseline.artifact_type,
                    actual=reproduced.artifact_type,
                    severity=DivergenceSeverity.BLOCKING,
                    message="Artifact type mismatch",
                )
            )

        return divergences

    def _compute_overall_severity(
        self, divergences: List[DivergenceDetail]
    ) -> DivergenceSeverity:
        """Compute overall severity from list of divergences."""
        if not divergences:
            return DivergenceSeverity.NONE

        has_blocking = any(d.severity == DivergenceSeverity.BLOCKING for d in divergences)
        if has_blocking:
            return DivergenceSeverity.BLOCKING

        has_warning = any(d.severity == DivergenceSeverity.WARNING for d in divergences)
        if has_warning:
            return DivergenceSeverity.WARNING

        return DivergenceSeverity.NONE

    def _build_message(
        self, status: RegressionStatus, divergences: List[DivergenceDetail]
    ) -> str:
        """Build human-readable message for report."""
        if status == RegressionStatus.MATCH:
            return "Artifact regression check passed: hash match confirmed"

        if status == RegressionStatus.DIVERGED:
            fields = [d.field for d in divergences]
            return f"Artifact regression check failed: divergence in {', '.join(fields)}"

        return f"Artifact regression check: {status.value}"


def compare_regression(
    bundle: RuntimeReplayBundle,
    execution_result: ReplayExecutionResult,
    reproduced: Optional[ReproducedArtifact] = None,
) -> ArtifactRegressionReport:
    """Convenience function to compare regression."""
    comparator = ArtifactRegressionComparator()
    return comparator.compare(bundle, execution_result, reproduced)
