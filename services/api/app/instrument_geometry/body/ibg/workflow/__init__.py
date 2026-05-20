"""
IBG Workflow Pipeline — Canonical Artifact to Review Package
=============================================================

Staged orchestration for converting vectorizer artifacts into
constitutional BodyEvidenceCandidate[] with human review packages.

DEV ORDER 1A-WORKFLOW: IBG Workflow Pipeline

Author: Production Shop
Date: 2026-05-18
"""

from .artifact_preservation import (
    PreservationResult,
    PreservedArtifact,
    preserve_artifacts,
    load_preserved_artifact,
    verify_artifact_integrity,
)

from .topology_recovery import (
    TopologyRecoveryResult,
    TopologyStats,
    ContourCandidate,
    recover_topology,
)

from .candidate_scoring import (
    ScoringResult,
    ScoringSignals,
    ScoredCandidate,
    score_candidates,
)

from .review_package import (
    ReviewPackageResult,
    ReviewPackage,
    CandidateSummary,
    emit_review_package,
    load_review_package,
)

from .ibg_workflow_pipeline import (
    IBGWorkflowPipeline,
    PipelineResult,
    PipelineStageResult,
)

__all__ = [
    # Artifact Preservation
    "PreservationResult",
    "PreservedArtifact",
    "preserve_artifacts",
    "load_preserved_artifact",
    "verify_artifact_integrity",
    # Topology Recovery
    "TopologyRecoveryResult",
    "TopologyStats",
    "ContourCandidate",
    "recover_topology",
    # Candidate Scoring
    "ScoringResult",
    "ScoringSignals",
    "ScoredCandidate",
    "score_candidates",
    # Review Package
    "ReviewPackageResult",
    "ReviewPackage",
    "CandidateSummary",
    "emit_review_package",
    "load_review_package",
    # Pipeline
    "IBGWorkflowPipeline",
    "PipelineResult",
    "PipelineStageResult",
]
