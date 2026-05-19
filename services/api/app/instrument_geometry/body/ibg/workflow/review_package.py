"""
Review Package — Human Review Output Generation
================================================

Generates review packages for human approval of body evidence candidates.

Package contents:
- Artifact paths and hashes
- Candidate summaries
- Topology statistics
- Authority state and provenance
- Confidence declarations
- Gate decisions
- Review notes placeholder

DEV ORDER 1A-WORKFLOW: IBG Workflow Pipeline

Author: Production Shop
Date: 2026-05-18
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .artifact_preservation import PreservedArtifact
from .topology_recovery import TopologyStats
from .candidate_scoring import ScoredCandidate

logger = logging.getLogger(__name__)

# Output directory for review packages
REVIEW_PACKAGES_DIR = Path("morphology_harvest/outputs/workflow_1a/review_packages")


@dataclass
class CandidateSummary:
    """Summary of a candidate for review."""
    candidate_id: str
    rank: int
    rank_score: float
    is_closed: bool
    area_mm2: float
    perimeter_mm: float
    point_count: int
    rejection_flags: List[str]
    authority_state: str
    review_required: bool
    gate_decision: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "rank": self.rank,
            "rank_score": self.rank_score,
            "is_closed": self.is_closed,
            "area_mm2": self.area_mm2,
            "perimeter_mm": self.perimeter_mm,
            "point_count": self.point_count,
            "rejection_flags": self.rejection_flags,
            "authority_state": self.authority_state,
            "review_required": self.review_required,
            "gate_decision": self.gate_decision,
        }


@dataclass
class ReviewPackage:
    """
    Complete review package for human approval.

    Attributes:
        package_id: Unique package identifier
        created_at: Timestamp
        artifact_paths: Paths to preserved artifacts
        artifact_hashes: SHA-256 hashes of artifacts
        candidate_summaries: Summary of each candidate
        topology_stats: Statistics from topology recovery
        provenance: Provenance record
        confidence_declaration: Typed confidence
        gate_decision: Overall gate decision
        review_required: Whether review is required
        review_notes_placeholder: Empty placeholder for notes
        package_path: Path to saved package JSON
    """
    package_id: str
    created_at: str
    artifact_paths: Dict[str, str] = field(default_factory=dict)
    artifact_hashes: Dict[str, str] = field(default_factory=dict)
    candidate_summaries: List[CandidateSummary] = field(default_factory=list)
    topology_stats: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    confidence_declaration: Dict[str, Any] = field(default_factory=dict)
    gate_decision: Dict[str, Any] = field(default_factory=dict)
    review_required: bool = True
    review_notes_placeholder: str = ""
    package_path: Optional[str] = None
    preview_paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "created_at": self.created_at,
            "artifact_paths": self.artifact_paths,
            "artifact_hashes": self.artifact_hashes,
            "candidate_count": len(self.candidate_summaries),
            "candidate_summaries": [c.to_dict() for c in self.candidate_summaries],
            "topology_stats": self.topology_stats,
            "provenance": self.provenance,
            "confidence_declaration": self.confidence_declaration,
            "gate_decision": self.gate_decision,
            "review_required": self.review_required,
            "review_notes_placeholder": self.review_notes_placeholder,
            "preview_paths": self.preview_paths,
        }


@dataclass
class ReviewPackageResult:
    """Result of review package generation."""
    success: bool
    package: Optional[ReviewPackage] = None
    package_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "package_path": self.package_path,
            "package": self.package.to_dict() if self.package else None,
            "errors": self.errors,
        }


def emit_review_package(
    package_id: str,
    artifacts: List[PreservedArtifact],
    scored_candidates: List[ScoredCandidate],
    topology_stats: TopologyStats,
    body_evidence_candidates: List[Any],  # BodyEvidenceCandidate
    gate_results: List[Any],  # IntakeValidationResult
    output_dir: Optional[Path] = None,
) -> ReviewPackageResult:
    """
    Generate and save a review package.

    Args:
        package_id: Unique identifier for the package
        artifacts: Preserved artifacts
        scored_candidates: Scored contour candidates
        topology_stats: Topology recovery statistics
        body_evidence_candidates: Constitutional candidates
        gate_results: Gate validation results
        output_dir: Optional custom output directory

    Returns:
        ReviewPackageResult with package path
    """
    errors = []

    # Determine output directory
    if output_dir is None:
        output_dir = REVIEW_PACKAGES_DIR / package_id
    else:
        output_dir = Path(output_dir) / package_id

    # Create directory
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return ReviewPackageResult(
            success=False,
            errors=[f"Failed to create output directory: {e}"],
        )

    created_at = datetime.now(timezone.utc).isoformat()

    # Build artifact paths and hashes
    artifact_paths = {}
    artifact_hashes = {}
    for artifact in artifacts:
        artifact_paths[artifact.artifact_type] = artifact.artifact_path
        artifact_hashes[artifact.artifact_type] = artifact.artifact_hash

    # Build candidate summaries
    candidate_summaries = []
    for i, (scored, bec, gate) in enumerate(zip(
        scored_candidates,
        body_evidence_candidates,
        gate_results,
    )):
        summary = CandidateSummary(
            candidate_id=bec.candidate_id if bec else f"candidate_{i}",
            rank=scored.rank,
            rank_score=scored.rank_score,
            is_closed=scored.contour.is_closed,
            area_mm2=scored.contour.area_mm2,
            perimeter_mm=scored.contour.perimeter_mm,
            point_count=len(scored.contour.points),
            rejection_flags=scored.rejection_flags,
            authority_state=bec.authority_state.value if bec else "unknown",
            review_required=bec.review_required if bec else True,
            gate_decision={
                "is_valid": gate.is_valid if gate else False,
                "rejections": [r.value for r in gate.rejections] if gate else [],
            },
        )
        candidate_summaries.append(summary)

    # Build provenance from first candidate
    provenance = {}
    if body_evidence_candidates and body_evidence_candidates[0]:
        bec = body_evidence_candidates[0]
        if bec.provenance:
            provenance = bec.provenance.to_dict()

    # Build confidence declaration from first candidate
    confidence_declaration = {}
    if body_evidence_candidates and body_evidence_candidates[0]:
        bec = body_evidence_candidates[0]
        if bec.confidence:
            confidence_declaration = bec.confidence.to_dict()

    # Overall gate decision (all must pass for package to pass)
    all_valid = all(g.is_valid for g in gate_results if g)
    all_rejections = []
    for g in gate_results:
        if g and g.rejections:
            all_rejections.extend([r.value for r in g.rejections])

    gate_decision = {
        "all_valid": all_valid,
        "any_valid": any(g.is_valid for g in gate_results if g),
        "total_candidates": len(gate_results),
        "passed_candidates": sum(1 for g in gate_results if g and g.is_valid),
        "rejections": list(set(all_rejections)),
    }

    # Create package
    package = ReviewPackage(
        package_id=package_id,
        created_at=created_at,
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        candidate_summaries=candidate_summaries,
        topology_stats=topology_stats.to_dict(),
        provenance=provenance,
        confidence_declaration=confidence_declaration,
        gate_decision=gate_decision,
        review_required=True,  # Always require review in 1A
        review_notes_placeholder="",
    )

    # Save package JSON
    package_path = output_dir / f"{package_id}_review_package.json"
    try:
        with open(package_path, "w", encoding="utf-8") as f:
            json.dump(package.to_dict(), f, indent=2)
        package.package_path = str(package_path)
        logger.info(f"Wrote review package: {package_path}")
    except Exception as e:
        errors.append(f"Failed to write package JSON: {e}")

    return ReviewPackageResult(
        success=len(errors) == 0,
        package=package,
        package_path=str(package_path) if package_path.exists() else None,
        errors=errors if errors else None,
    )


def load_review_package(package_path: str) -> Optional[ReviewPackage]:
    """Load a review package from disk."""
    try:
        with open(package_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        summaries = []
        for s in data.get("candidate_summaries", []):
            summaries.append(CandidateSummary(
                candidate_id=s["candidate_id"],
                rank=s["rank"],
                rank_score=s["rank_score"],
                is_closed=s["is_closed"],
                area_mm2=s["area_mm2"],
                perimeter_mm=s["perimeter_mm"],
                point_count=s["point_count"],
                rejection_flags=s["rejection_flags"],
                authority_state=s["authority_state"],
                review_required=s["review_required"],
                gate_decision=s["gate_decision"],
            ))

        return ReviewPackage(
            package_id=data["package_id"],
            created_at=data["created_at"],
            artifact_paths=data.get("artifact_paths", {}),
            artifact_hashes=data.get("artifact_hashes", {}),
            candidate_summaries=summaries,
            topology_stats=data.get("topology_stats", {}),
            provenance=data.get("provenance", {}),
            confidence_declaration=data.get("confidence_declaration", {}),
            gate_decision=data.get("gate_decision", {}),
            review_required=data.get("review_required", True),
            review_notes_placeholder=data.get("review_notes_placeholder", ""),
            package_path=package_path,
            preview_paths=data.get("preview_paths", {}),
        )

    except Exception as e:
        logger.error(f"Failed to load review package: {e}")
        return None
