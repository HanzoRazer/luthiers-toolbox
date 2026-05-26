"""
Topology Continuity Evaluation

CAM Dev Order 7V: Topology continuity cognition without geometry mutation.

Provides:
  - TopologyContinuityEvaluation model
  - Topology risk categories
  - Continuity validation
  - Risk detection helpers (metadata-based)

7V invariants:
  - auto_correction_attempted: always False
  - geometry_mutation_attempted: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Topology continuity may be analyzed.
  Topology continuity may not be auto-corrected.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


TopologyRiskCategory = Literal[
    "thin_bridge",
    "unsupported_span",
    "fragmented_region",
    "clamp_interference",
    "edge_instability",
    "registration_instability",
    "fixture_conflict",
    "continuity_break",
]

ValidationGate = Literal["green", "yellow", "red"]


class TopologyRiskDeclaration(BaseModel):
    """Declaration of a topology risk for metadata-based evaluation."""

    risk_category: TopologyRiskCategory
    region_label: Optional[str] = None
    description: str = ""
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    declared_by: str = "unknown"


class TopologyContinuityEvaluation(BaseModel):
    """
    Topology continuity evaluation for a geometry authority reference.

    Evaluates topology risks based on declared metadata, not raw geometry analysis.
    One evaluation per geometry authority reference.

    7V invariants (model-enforced):
      - auto_correction_attempted: always False
      - geometry_mutation_attempted: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    evaluation_id: str = Field(
        default_factory=lambda: f"topo-eval-{uuid4().hex[:12]}",
        description="Unique evaluation identifier"
    )

    geometry_authority_ref_id: str = Field(
        ..., description="Geometry authority reference being evaluated"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="Associated workspace ID"
    )
    strategy_id: Optional[str] = Field(
        default=None,
        description="Associated strategy ID"
    )

    topology_risks: List[TopologyRiskCategory] = Field(
        default_factory=list,
        description="Detected topology risk categories"
    )

    risk_declarations: List[TopologyRiskDeclaration] = Field(
        default_factory=list,
        description="Detailed risk declarations"
    )

    continuity_integrity_valid: bool = Field(
        default=True,
        description="Whether topology continuity is valid"
    )

    fragmented_regions_detected: bool = Field(
        default=False,
        description="Whether fragmented regions were detected"
    )
    unsupported_spans_detected: bool = Field(
        default=False,
        description="Whether unsupported spans were detected"
    )
    clamp_interference_detected: bool = Field(
        default=False,
        description="Whether clamp interference was detected"
    )
    thin_bridges_detected: bool = Field(
        default=False,
        description="Whether thin bridges were detected"
    )

    gate: ValidationGate = Field(
        default="green",
        description="Validation gate result"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="YELLOW warnings"
    )

    review_required: bool = Field(
        default=True,
        description="Whether human review is required"
    )

    auto_correction_attempted: bool = Field(
        default=False,
        description="Always False — topology may not be auto-corrected"
    )
    geometry_mutation_attempted: bool = Field(
        default=False,
        description="Always False — geometry may not be mutated"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7V does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7V does not allow machine output"
    )

    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_topology_hash: str = Field(
        default="",
        description="Deterministic hash of evaluation state"
    )

    @model_validator(mode="after")
    def enforce_7v_invariants(self) -> "TopologyContinuityEvaluation":
        """Enforce 7V invariants."""
        if self.auto_correction_attempted:
            raise ValueError(
                "7V invariant violation: auto_correction_attempted must be False — "
                "topology may not be auto-corrected"
            )
        if self.geometry_mutation_attempted:
            raise ValueError(
                "7V invariant violation: geometry_mutation_attempted must be False — "
                "geometry may not be mutated"
            )
        if self.execution_authorized:
            raise ValueError(
                "7V invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7V invariant violation: machine_output_allowed must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of evaluation state."""
        hash_input = {
            "evaluation_id": self.evaluation_id,
            "geometry_authority_ref_id": self.geometry_authority_ref_id,
            "topology_risks": sorted(self.topology_risks),
            "continuity_integrity_valid": self.continuity_integrity_valid,
            "fragmented_regions_detected": self.fragmented_regions_detected,
            "unsupported_spans_detected": self.unsupported_spans_detected,
            "clamp_interference_detected": self.clamp_interference_detected,
            "thin_bridges_detected": self.thin_bridges_detected,
            "gate": self.gate,
            "blocking_issues": sorted(self.blocking_issues),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def evaluate_topology_continuity(
    geometry_authority_ref_id: str,
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    declared_thin_bridges: bool = False,
    declared_fragmented_regions: bool = False,
    declared_unsupported_spans: bool = False,
    declared_clamp_interference: bool = False,
    risk_declarations: Optional[List[TopologyRiskDeclaration]] = None,
    fixture_constraint_ids: Optional[List[str]] = None,
) -> TopologyContinuityEvaluation:
    """
    Evaluate topology continuity based on declared metadata.

    This is metadata-based evaluation, not real geometry analysis.
    Risks must be declared by the caller based on external analysis.

    Args:
        geometry_authority_ref_id: Geometry authority reference to evaluate
        workspace_id: Optional workspace context
        strategy_id: Optional strategy context
        declared_thin_bridges: Whether thin bridges are declared
        declared_fragmented_regions: Whether fragmented regions are declared
        declared_unsupported_spans: Whether unsupported spans are declared
        declared_clamp_interference: Whether clamp interference is declared
        risk_declarations: Optional detailed risk declarations
        fixture_constraint_ids: Optional fixture constraints to consider

    Returns:
        TopologyContinuityEvaluation with risks and gate
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []
    topology_risks: List[TopologyRiskCategory] = []

    if declared_thin_bridges:
        topology_risks.append("thin_bridge")
        warnings.append("Thin bridges detected — may affect workholding stability")

    if declared_fragmented_regions:
        topology_risks.append("fragmented_region")
        blocking_issues.append("Fragmented regions detected — continuity integrity compromised")

    if declared_unsupported_spans:
        topology_risks.append("unsupported_span")
        warnings.append("Unsupported spans detected — may require additional support")

    if declared_clamp_interference:
        topology_risks.append("clamp_interference")
        blocking_issues.append("Clamp interference detected — fixture conflict")

    if risk_declarations:
        for decl in risk_declarations:
            if decl.risk_category not in topology_risks:
                topology_risks.append(decl.risk_category)
            if decl.severity == "critical":
                blocking_issues.append(f"Critical risk: {decl.risk_category} — {decl.description}")
            elif decl.severity == "high":
                warnings.append(f"High risk: {decl.risk_category} — {decl.description}")

    continuity_integrity_valid = not (
        declared_fragmented_regions or
        "continuity_break" in topology_risks
    )

    if blocking_issues:
        gate: ValidationGate = "red"
    elif warnings:
        gate = "yellow"
    else:
        gate = "green"

    evaluation = TopologyContinuityEvaluation(
        geometry_authority_ref_id=geometry_authority_ref_id,
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        topology_risks=topology_risks,
        risk_declarations=risk_declarations or [],
        continuity_integrity_valid=continuity_integrity_valid,
        fragmented_regions_detected=declared_fragmented_regions,
        unsupported_spans_detected=declared_unsupported_spans,
        clamp_interference_detected=declared_clamp_interference,
        thin_bridges_detected=declared_thin_bridges,
        gate=gate,
        blocking_issues=blocking_issues,
        warnings=warnings,
    )

    evaluation.deterministic_topology_hash = evaluation.compute_hash()

    return evaluation


def detect_thin_bridges(
    declared_regions: Optional[List[str]] = None,
    bridge_width_threshold_mm: float = 5.0,
) -> tuple[bool, List[str]]:
    """
    Detect thin bridges based on declared metadata.

    This is a signature-complete stub for future real analysis.
    Currently operates on declared metadata only.

    Args:
        declared_regions: Region labels declared as thin bridges
        bridge_width_threshold_mm: Width threshold (metadata only)

    Returns:
        (detected, region_labels)
    """
    if declared_regions:
        return True, declared_regions
    return False, []


def detect_fragmented_regions(
    declared_regions: Optional[List[str]] = None,
) -> tuple[bool, List[str]]:
    """
    Detect fragmented regions based on declared metadata.

    This is a signature-complete stub for future real analysis.

    Args:
        declared_regions: Region labels declared as fragmented

    Returns:
        (detected, region_labels)
    """
    if declared_regions:
        return True, declared_regions
    return False, []


def detect_unsupported_spans(
    declared_regions: Optional[List[str]] = None,
    span_threshold_mm: float = 50.0,
) -> tuple[bool, List[str]]:
    """
    Detect unsupported spans based on declared metadata.

    This is a signature-complete stub for future real analysis.

    Args:
        declared_regions: Region labels declared as unsupported spans
        span_threshold_mm: Span threshold (metadata only)

    Returns:
        (detected, region_labels)
    """
    if declared_regions:
        return True, declared_regions
    return False, []


def detect_clamp_interference(
    constraint_region_labels: Optional[List[str]] = None,
    workpiece_region_labels: Optional[List[str]] = None,
) -> tuple[bool, List[str]]:
    """
    Detect clamp interference based on declared region label overlap.

    This is a metadata-based check using declared region labels.

    Args:
        constraint_region_labels: Regions affected by fixture constraints
        workpiece_region_labels: Regions of the workpiece geometry

    Returns:
        (detected, overlapping_regions)
    """
    if not constraint_region_labels or not workpiece_region_labels:
        return False, []

    overlapping = [
        r for r in constraint_region_labels
        if r in workpiece_region_labels
    ]

    return len(overlapping) > 0, overlapping


def detect_topology_continuity_risks(
    geometry_authority_ref_id: str,
    declared_risks: Optional[List[TopologyRiskCategory]] = None,
) -> List[TopologyRiskCategory]:
    """
    Detect topology continuity risks based on declared metadata.

    This is a signature-complete stub for future analysis.

    Args:
        geometry_authority_ref_id: Geometry reference
        declared_risks: Risks declared by external analysis

    Returns:
        List of detected risk categories
    """
    return declared_risks or []


def validate_topology_evaluation(
    evaluation: TopologyContinuityEvaluation,
) -> tuple[bool, List[str]]:
    """
    Validate a topology continuity evaluation.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if evaluation.auto_correction_attempted:
        issues.append("auto_correction_attempted must be False")

    if evaluation.geometry_mutation_attempted:
        issues.append("geometry_mutation_attempted must be False")

    if evaluation.execution_authorized:
        issues.append("execution_authorized must be False")

    if evaluation.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not evaluation.geometry_authority_ref_id:
        issues.append("geometry_authority_ref_id is required")

    return len(issues) == 0, issues


def build_topology_evaluation_hash(evaluation: TopologyContinuityEvaluation) -> str:
    """Build deterministic hash for a topology evaluation."""
    return evaluation.compute_hash()
