"""
IBG Workflow Pipeline — Canonical Artifact to Review Package
=============================================================

Staged orchestration pipeline:

1. preserve_artifacts() - Save DXF/SVG exactly as produced
2. recover_topology() - Extract contours, detect loops, compute gap stats
3. isolate_candidates() - Generate candidate body regions
4. score_candidates() - Compute ranking scores
5. wrap_candidates() - Create BodyEvidenceCandidate[] with provenance
6. run_intake_gate() - Validate through IBGIntakeGate (expect blocked)
7. emit_review_package() - Write review package to disk

Success condition:
    Given canonical DXF/SVG artifacts, produce provenance-bearing,
    confidence-declared, gate-blocked BodyEvidenceCandidate[] and
    a human-review package.

DEV ORDER 1A-WORKFLOW: IBG Workflow Pipeline

Author: Production Shop
Date: 2026-05-18
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .artifact_preservation import (
    PreservationResult,
    PreservedArtifact,
    preserve_artifacts,
)
from .topology_recovery import (
    TopologyRecoveryResult,
    ContourCandidate,
    recover_topology,
)
from .candidate_scoring import (
    ScoringResult,
    ScoredCandidate,
    score_candidates,
)
from .review_package import (
    ReviewPackageResult,
    ReviewPackage,
    emit_review_package,
)

from ..body_evidence_candidate import (
    BodyEvidenceCandidate,
    create_candidate_from_evidence,
)
from ..ibg_intake_gate import (
    IBGIntakeGate,
    IntakeValidationResult,
    create_default_intake_gate,
)
from ..body_grid.body_grid_schema import (
    BodyEvidence,
    ContourSegment,
    NormalizedPoint,
    RawCoordinate,
    CoordinateSpace,
    EvidenceSource,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineStageResult:
    """Result of a single pipeline stage."""
    stage: str
    success: bool
    duration_ms: float = 0.0
    data: Any = None
    errors: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """
    Complete result of workflow pipeline execution.

    Attributes:
        success: Whether pipeline completed successfully
        pipeline_id: Unique identifier for this run
        stages: Results from each stage
        artifacts: Preserved artifacts
        candidates: Final BodyEvidenceCandidate list
        gate_results: Gate validation results
        review_package: Generated review package
        errors: List of errors
    """
    success: bool
    pipeline_id: str
    stages: List[PipelineStageResult] = field(default_factory=list)
    artifacts: List[PreservedArtifact] = field(default_factory=list)
    candidates: List[BodyEvidenceCandidate] = field(default_factory=list)
    gate_results: List[IntakeValidationResult] = field(default_factory=list)
    review_package: Optional[ReviewPackage] = None
    review_package_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "pipeline_id": self.pipeline_id,
            "stage_count": len(self.stages),
            "stages": [
                {
                    "stage": s.stage,
                    "success": s.success,
                    "duration_ms": s.duration_ms,
                    "errors": s.errors,
                }
                for s in self.stages
            ],
            "artifact_count": len(self.artifacts),
            "candidate_count": len(self.candidates),
            "gate_results": [
                {
                    "candidate_id": self.candidates[i].candidate_id if i < len(self.candidates) else None,
                    "is_valid": r.is_valid,
                    "rejections": [rej.value for rej in r.rejections],
                }
                for i, r in enumerate(self.gate_results)
            ],
            "review_package_path": self.review_package_path,
            "errors": self.errors,
        }


class IBGWorkflowPipeline:
    """
    Staged workflow pipeline for IBG artifact processing.

    Usage:
        pipeline = IBGWorkflowPipeline()
        result = pipeline.run(
            dxf_base64="...",
            source_filename="guitar_body.dxf",
            source_mode="pdf",
        )

        if result.success:
            print(f"Review package: {result.review_package_path}")
            print(f"Candidates: {len(result.candidates)}")
    """

    def __init__(
        self,
        top_n_candidates: int = 5,
        endpoint_tolerance: float = 1.0,
        gate: Optional[IBGIntakeGate] = None,
    ):
        """
        Initialize pipeline.

        Args:
            top_n_candidates: Number of top candidates to return
            endpoint_tolerance: Tolerance for endpoint matching in mm
            gate: Optional custom intake gate
        """
        self.top_n_candidates = top_n_candidates
        self.endpoint_tolerance = endpoint_tolerance
        self.gate = gate or create_default_intake_gate()

    def run(
        self,
        dxf_base64: Optional[str] = None,
        dxf_bytes: Optional[bytes] = None,
        svg_content: Optional[str] = None,
        source_filename: str = "unknown",
        source_mode: str = "pdf",
        pipeline_id: Optional[str] = None,
    ) -> PipelineResult:
        """
        Run the complete workflow pipeline.

        Args:
            dxf_base64: Base64-encoded DXF content
            dxf_bytes: Raw DXF bytes
            svg_content: SVG content string
            source_filename: Original filename
            source_mode: "pdf" or "photo"
            pipeline_id: Optional custom pipeline ID

        Returns:
            PipelineResult with all outputs
        """
        import time

        if pipeline_id is None:
            pipeline_id = f"pipeline_{uuid4().hex[:12]}"

        stages = []
        errors = []

        # Stage 1: Preserve artifacts
        t0 = time.time()
        preservation = self.preserve_artifacts(
            dxf_base64=dxf_base64,
            dxf_bytes=dxf_bytes,
            svg_content=svg_content,
            source_filename=source_filename,
            source_mode=source_mode,
            artifact_id=pipeline_id,
        )
        stages.append(PipelineStageResult(
            stage="preserve_artifacts",
            success=preservation.success,
            duration_ms=(time.time() - t0) * 1000,
            data=preservation,
            errors=preservation.errors or [],
        ))

        if not preservation.success:
            errors.append("Artifact preservation failed")
            return PipelineResult(
                success=False,
                pipeline_id=pipeline_id,
                stages=stages,
                errors=errors,
            )

        # Get DXF bytes for topology recovery
        if dxf_bytes is None and dxf_base64:
            import base64
            dxf_bytes = base64.b64decode(dxf_base64)

        if dxf_bytes is None:
            errors.append("No DXF content available for topology recovery")
            return PipelineResult(
                success=False,
                pipeline_id=pipeline_id,
                stages=stages,
                artifacts=preservation.artifacts,
                errors=errors,
            )

        # Stage 2: Recover topology
        t0 = time.time()
        topology = self.recover_topology(dxf_bytes)
        stages.append(PipelineStageResult(
            stage="recover_topology",
            success=topology.success,
            duration_ms=(time.time() - t0) * 1000,
            data=topology,
            errors=topology.errors,
        ))

        if not topology.success or not topology.contours:
            errors.append("Topology recovery failed or no contours found")
            return PipelineResult(
                success=False,
                pipeline_id=pipeline_id,
                stages=stages,
                artifacts=preservation.artifacts,
                errors=errors,
            )

        # Stage 3: Isolate candidates (filtering)
        t0 = time.time()
        isolated = self.isolate_candidates(topology.contours)
        stages.append(PipelineStageResult(
            stage="isolate_candidates",
            success=len(isolated) > 0,
            duration_ms=(time.time() - t0) * 1000,
            data={"count": len(isolated)},
        ))

        # Stage 4: Score candidates
        t0 = time.time()
        scoring = self.score_candidates(isolated)
        stages.append(PipelineStageResult(
            stage="score_candidates",
            success=len(scoring.candidates) > 0,
            duration_ms=(time.time() - t0) * 1000,
            data=scoring,
        ))

        if not scoring.candidates:
            errors.append("No candidates scored")
            return PipelineResult(
                success=False,
                pipeline_id=pipeline_id,
                stages=stages,
                artifacts=preservation.artifacts,
                errors=errors,
            )

        # Stage 5: Wrap candidates in BodyEvidenceCandidate
        t0 = time.time()
        wrapped = self.wrap_candidates(
            scored_candidates=scoring.candidates,
            source_filename=source_filename,
            source_mode=source_mode,
        )
        stages.append(PipelineStageResult(
            stage="wrap_candidates",
            success=len(wrapped) > 0,
            duration_ms=(time.time() - t0) * 1000,
            data={"count": len(wrapped)},
        ))

        # Stage 6: Run intake gate
        t0 = time.time()
        gate_results = self.run_intake_gate(wrapped)
        stages.append(PipelineStageResult(
            stage="run_intake_gate",
            success=True,  # Gate always runs, blocking is expected
            duration_ms=(time.time() - t0) * 1000,
            data={
                "total": len(gate_results),
                "passed": sum(1 for r in gate_results if r.is_valid),
                "blocked": sum(1 for r in gate_results if not r.is_valid),
            },
        ))

        # Stage 7: Emit review package
        t0 = time.time()
        review_result = self.emit_review_package(
            package_id=pipeline_id,
            artifacts=preservation.artifacts,
            scored_candidates=scoring.candidates,
            topology_stats=topology.stats,
            body_evidence_candidates=wrapped,
            gate_results=gate_results,
        )
        stages.append(PipelineStageResult(
            stage="emit_review_package",
            success=review_result.success,
            duration_ms=(time.time() - t0) * 1000,
            data=review_result,
            errors=review_result.errors or [],
        ))

        return PipelineResult(
            success=True,
            pipeline_id=pipeline_id,
            stages=stages,
            artifacts=preservation.artifacts,
            candidates=wrapped,
            gate_results=gate_results,
            review_package=review_result.package,
            review_package_path=review_result.package_path,
        )

    def preserve_artifacts(
        self,
        dxf_base64: Optional[str],
        dxf_bytes: Optional[bytes],
        svg_content: Optional[str],
        source_filename: str,
        source_mode: str,
        artifact_id: str,
    ) -> PreservationResult:
        """Stage 1: Preserve artifacts to disk."""
        return preserve_artifacts(
            dxf_base64=dxf_base64,
            dxf_bytes=dxf_bytes,
            svg_content=svg_content,
            source_filename=source_filename,
            source_mode=source_mode,
            artifact_id=artifact_id,
        )

    def recover_topology(self, dxf_bytes: bytes) -> TopologyRecoveryResult:
        """Stage 2: Recover topology from DXF."""
        return recover_topology(
            dxf_bytes=dxf_bytes,
            tolerance=self.endpoint_tolerance,
        )

    def isolate_candidates(
        self,
        contours: List[ContourCandidate],
    ) -> List[ContourCandidate]:
        """
        Stage 3: Filter contours to plausible body candidates.

        Keeps:
        - Closed loops
        - Near-closed loops (gap < 5mm)
        - Large connected chains (perimeter > 500mm, points > 50)
        - Body-scale rectangles from LINE entities (perimeter > 800mm, 4+ corners)
        """
        candidates = []

        for contour in contours:
            # Keep closed contours
            if contour.is_closed:
                candidates.append(contour)
                continue

            # Keep near-closed contours
            if contour.gap_distance < 5.0:
                candidates.append(contour)
                continue

            # Keep large chains (polyline-sourced body contours)
            if contour.perimeter_mm > 500 and len(contour.points) > 50:
                candidates.append(contour)
                continue

            # Keep body-scale LINE-sourced contours (fewer points but large perimeter)
            # This handles DXFs where body outline is composed of individual LINE entities
            # Typical guitar body perimeter: 800-1800mm
            if contour.perimeter_mm >= 800 and len(contour.points) >= 4:
                candidates.append(contour)

        return candidates

    def score_candidates(
        self,
        contours: List[ContourCandidate],
    ) -> ScoringResult:
        """Stage 4: Score and rank candidates."""
        return score_candidates(
            contours=contours,
            top_n=self.top_n_candidates,
        )

    def wrap_candidates(
        self,
        scored_candidates: List[ScoredCandidate],
        source_filename: str,
        source_mode: str,
    ) -> List[BodyEvidenceCandidate]:
        """Stage 5: Wrap scored candidates in BodyEvidenceCandidate."""
        wrapped = []

        for scored in scored_candidates:
            # Convert contour to BodyEvidence
            evidence = self._contour_to_evidence(scored.contour)

            # Create constitutional candidate
            candidate = create_candidate_from_evidence(
                evidence=evidence,
                source_artifact=source_filename,
                extraction_method="ibg_workflow_pipeline",
                extraction_params={
                    "source_mode": source_mode,
                    "rank": scored.rank,
                    "rank_score": scored.rank_score,
                    "is_closed": scored.contour.is_closed,
                    "rejection_flags": scored.rejection_flags,
                },
                confidence_value=scored.rank_score,
                confidence_origin="ibg_workflow_pipeline_scoring",
            )

            # Record topology integrity based on closure
            if candidate.provenance:
                if not scored.contour.is_closed:
                    integrity = max(0.3, 1.0 - scored.contour.gap_distance / 50.0)
                    candidate.provenance.record_topology_degradation(
                        integrity,
                        f"Open contour with {scored.contour.gap_distance:.1f}mm gap",
                    )

            wrapped.append(candidate)

        return wrapped

    def _contour_to_evidence(self, contour: ContourCandidate) -> BodyEvidence:
        """Convert ContourCandidate to BodyEvidence."""
        min_x, min_y, max_x, max_y = contour.bounding_box
        width = max_x - min_x
        height = max_y - min_y
        centerline_x = (min_x + max_x) / 2

        # Normalize points
        def normalize(x: float, y: float) -> NormalizedPoint:
            x_norm = (x - centerline_x) / (width / 2) if width > 0 else 0.0
            y_norm = (y - min_y) / height if height > 0 else 0.0
            return NormalizedPoint(
                x_norm=x_norm,
                y_norm=y_norm,
                raw=RawCoordinate(x=x, y=y, space=CoordinateSpace.RAW_MM),
                confidence=0.7,
            )

        normalized = [normalize(p[0], p[1]) for p in contour.points]

        contour_segment = ContourSegment(
            points=normalized,
            is_closed=contour.is_closed,
            side="unknown",
            source=EvidenceSource.VECTORIZER_DXF,
        )

        return BodyEvidence(
            outline_points=contour.points,
            contour_segments=[contour_segment],
            source_type=EvidenceSource.VECTORIZER_DXF,
            bounding_box_mm=contour.bounding_box,
            centerline_x_mm=centerline_x,
        )

    def run_intake_gate(
        self,
        candidates: List[BodyEvidenceCandidate],
    ) -> List[IntakeValidationResult]:
        """Stage 6: Validate candidates through IBG Intake Gate."""
        results = []
        for candidate in candidates:
            result = self.gate.validate(candidate)
            results.append(result)
        return results

    def emit_review_package(
        self,
        package_id: str,
        artifacts: List[PreservedArtifact],
        scored_candidates: List[ScoredCandidate],
        topology_stats: Any,
        body_evidence_candidates: List[BodyEvidenceCandidate],
        gate_results: List[IntakeValidationResult],
    ) -> ReviewPackageResult:
        """Stage 7: Generate review package."""
        return emit_review_package(
            package_id=package_id,
            artifacts=artifacts,
            scored_candidates=scored_candidates,
            topology_stats=topology_stats,
            body_evidence_candidates=body_evidence_candidates,
            gate_results=gate_results,
        )
