"""
Provenance Record — Constitutional Runtime Foundation
=====================================================

DEV ORDER 1D: IBG Constitutional Intake Foundation

Defines provenance tracking for semantic objects in the IBG intake pipeline.
Provenance records the complete lineage of semantic transformations.

Key principle:
    Every semantic transformation must preserve:
    - provenance (where did this come from?)
    - derivation visibility (how was it produced?)
    - authority state (what trust level does it have?)
    - epistemic honesty (what do we actually know?)

Author: Constitutional Runtime Foundation
Date: 2026-05-18
Sprint: DEV ORDER 1D
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json


class TransformationStage(str, Enum):
    """
    Transformation stages in the semantic pipeline.

    Each stage represents a distinct transformation type with
    defined input/output contracts.
    """
    SOURCE_INTAKE = "source_intake"
    TOPOLOGY_RECONSTRUCTION = "topology_reconstruction"
    GAP_CLOSURE = "gap_closure"
    OCCUPANCY_ANALYSIS = "occupancy_analysis"
    CANDIDATE_RANKING = "candidate_ranking"
    SEMANTIC_CLASSIFICATION = "semantic_classification"
    HUMAN_REVIEW = "human_review"
    GENERATION_APPROVAL = "generation_approval"
    CAD_GENERATION = "cad_generation"
    BODY_ISOLATION = "body_isolation"
    MORPHOLOGY_ANALYSIS = "morphology_analysis"


@dataclass
class TransformationRecord:
    """
    Record of a single transformation in the pipeline.

    Captures what transformation was applied, by whom, and with what parameters.
    """
    stage: TransformationStage
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    input_artifact_id: Optional[str] = None
    output_artifact_id: Optional[str] = None
    actor: str = "system"
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stage": self.stage.value,
            "method": self.method,
            "params": self.params,
            "timestamp": self.timestamp.isoformat(),
            "input_artifact_id": self.input_artifact_id,
            "output_artifact_id": self.output_artifact_id,
            "actor": self.actor,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransformationRecord":
        """Create from dictionary."""
        return cls(
            stage=TransformationStage(data["stage"]),
            method=data["method"],
            params=data.get("params", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            input_artifact_id=data.get("input_artifact_id"),
            output_artifact_id=data.get("output_artifact_id"),
            actor=data.get("actor", "system"),
            notes=data.get("notes"),
        )


@dataclass
class ProvenanceRecord:
    """
    Complete provenance record for a semantic object.

    Tracks the full lineage from source artifact through all transformations.

    Required fields for IBG intake:
        - source_artifact: Original source path/id (REQUIRED)
        - derivation_chain: Full ancestry (REQUIRED if derived)
        - transformation_history: All transformations applied (REQUIRED)

    Attributes:
        object_id: Unique identifier for this object
        object_type: Type name (e.g., "BodyEvidenceCandidate")
        source_artifact: Path or ID of the original source
        derived_from: Parent object ID (if derived)
        derivation_chain: Full list of ancestor IDs
        transformation_history: All transformations applied
        created_at: When this provenance record was created
        last_updated_at: When this record was last updated
        topology_integrity_score: How much geometry was preserved (0.0-1.0)
        topology_degradation_notes: Notes about any degradation
        metadata: Additional metadata
    """
    object_id: str
    object_type: str
    source_artifact: str
    derived_from: Optional[str] = None
    derivation_chain: List[str] = field(default_factory=list)
    transformation_history: List[TransformationRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    topology_integrity_score: float = 1.0
    topology_degradation_notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_transformation(
        self,
        stage: TransformationStage,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        actor: str = "system",
        notes: Optional[str] = None,
    ) -> TransformationRecord:
        """
        Add a transformation record to the history.

        Args:
            stage: Transformation stage
            method: Method/function name used
            params: Parameters passed to the transformation
            actor: Who/what performed the transformation
            notes: Optional notes about the transformation

        Returns:
            The created transformation record
        """
        record = TransformationRecord(
            stage=stage,
            method=method,
            params=params or {},
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            notes=notes,
        )
        self.transformation_history.append(record)
        self.last_updated_at = datetime.now(timezone.utc)
        return record

    def record_topology_degradation(
        self,
        score: float,
        note: str,
    ) -> None:
        """
        Record topology degradation.

        Args:
            score: New integrity score (0.0-1.0)
            note: Description of the degradation
        """
        self.topology_integrity_score = min(self.topology_integrity_score, score)
        self.topology_degradation_notes.append(note)
        self.last_updated_at = datetime.now(timezone.utc)

    def compute_provenance_hash(self) -> str:
        """
        Compute a deterministic hash of the provenance lineage.

        This hash can be used to verify provenance integrity.
        """
        hash_input = {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "source_artifact": self.source_artifact,
            "derivation_chain": self.derivation_chain,
            "transformation_stages": [
                t.stage.value for t in self.transformation_history
            ],
        }
        canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).hexdigest()[:16]

    def has_complete_lineage(self) -> bool:
        """Check if provenance has complete lineage information."""
        if not self.source_artifact:
            return False
        if self.derived_from and not self.derivation_chain:
            return False
        return True

    def get_stage_count(self, stage: TransformationStage) -> int:
        """Count how many times a transformation stage has been applied."""
        return sum(1 for t in self.transformation_history if t.stage == stage)

    def get_last_transformation(self) -> Optional[TransformationRecord]:
        """Get the most recent transformation record."""
        if self.transformation_history:
            return self.transformation_history[-1]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "source_artifact": self.source_artifact,
            "derived_from": self.derived_from,
            "derivation_chain": self.derivation_chain,
            "transformation_history": [
                t.to_dict() for t in self.transformation_history
            ],
            "created_at": self.created_at.isoformat(),
            "last_updated_at": self.last_updated_at.isoformat(),
            "topology_integrity_score": self.topology_integrity_score,
            "topology_degradation_notes": self.topology_degradation_notes,
            "metadata": self.metadata,
            "provenance_hash": self.compute_provenance_hash(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceRecord":
        """Create from dictionary."""
        record = cls(
            object_id=data["object_id"],
            object_type=data["object_type"],
            source_artifact=data["source_artifact"],
            derived_from=data.get("derived_from"),
            derivation_chain=data.get("derivation_chain", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated_at=datetime.fromisoformat(data["last_updated_at"]),
            topology_integrity_score=data.get("topology_integrity_score", 1.0),
            topology_degradation_notes=data.get("topology_degradation_notes", []),
            metadata=data.get("metadata", {}),
        )
        record.transformation_history = [
            TransformationRecord.from_dict(t)
            for t in data.get("transformation_history", [])
        ]
        return record


def create_source_provenance(
    object_id: str,
    object_type: str,
    source_artifact: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> ProvenanceRecord:
    """
    Create provenance for a source/canonical artifact.

    Use this for objects that represent original source data,
    not derived artifacts.

    Args:
        object_id: Unique identifier
        object_type: Type name
        source_artifact: Path or ID of the source
        metadata: Optional additional metadata

    Returns:
        ProvenanceRecord for a source artifact
    """
    record = ProvenanceRecord(
        object_id=object_id,
        object_type=object_type,
        source_artifact=source_artifact,
        metadata=metadata or {},
    )
    record.add_transformation(
        stage=TransformationStage.SOURCE_INTAKE,
        method="create_source_provenance",
        params={"source_artifact": source_artifact},
        actor="system:provenance",
    )
    return record


def create_derived_provenance(
    object_id: str,
    object_type: str,
    parent_provenance: ProvenanceRecord,
    transformation_stage: TransformationStage,
    transformation_method: str,
    transformation_params: Optional[Dict[str, Any]] = None,
    actor: str = "system",
) -> ProvenanceRecord:
    """
    Create provenance for a derived artifact.

    Preserves lineage from the parent and records the transformation.

    Args:
        object_id: Unique identifier for the new object
        object_type: Type name
        parent_provenance: Provenance of the parent object
        transformation_stage: Stage of transformation
        transformation_method: Method used for transformation
        transformation_params: Parameters used
        actor: Who/what performed the transformation

    Returns:
        ProvenanceRecord for the derived artifact
    """
    # Build derivation chain
    derivation_chain = list(parent_provenance.derivation_chain)
    derivation_chain.append(parent_provenance.object_id)

    record = ProvenanceRecord(
        object_id=object_id,
        object_type=object_type,
        source_artifact=parent_provenance.source_artifact,
        derived_from=parent_provenance.object_id,
        derivation_chain=derivation_chain,
        topology_integrity_score=parent_provenance.topology_integrity_score,
        topology_degradation_notes=list(parent_provenance.topology_degradation_notes),
    )

    record.add_transformation(
        stage=transformation_stage,
        method=transformation_method,
        params=transformation_params or {},
        actor=actor,
    )

    return record


class ProvenanceMissingError(Exception):
    """Raised when provenance is required but missing."""

    def __init__(self, object_type: str, operation: str):
        self.object_type = object_type
        self.operation = operation
        super().__init__(
            f"Provenance required for {object_type} to perform {operation}"
        )


class ProvenanceIntegrityError(Exception):
    """Raised when provenance integrity validation fails."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Provenance integrity error: {reason}")
