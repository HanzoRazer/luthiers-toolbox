"""
Runtime Provenance Contracts.

Sprint: MRP-5N
Status: PROTOTYPE

Data contracts for runtime artifact provenance and replay.
These define the structure for preserving executable lineage.

ARCHITECTURAL PRINCIPLE:
    Provenance is append-only.
    Every artifact must answer:
    - What produced me?
    - From what certified topology?
    - Under what validation result?
    - Under what admission decision?
    - Using what translator?
    - Using what adapter?
    - With what deterministic signature?
    - Can this run be replayed?
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import uuid

from .serialization import stable_hash_model, stable_json_dumps, stable_json_loads


class TraceEventType(str, Enum):
    """Types of trace events in the runtime pipeline."""

    VALIDATION_CERTIFIED = "VALIDATION_CERTIFIED"
    ADMISSION_COMPLETED = "ADMISSION_COMPLETED"
    TRANSLATION_COMPLETED = "TRANSLATION_COMPLETED"
    ADAPTER_COMPLETED = "ADAPTER_COMPLETED"
    ARTIFACT_RECORDED = "ARTIFACT_RECORDED"
    REPLAY_VERIFIED = "REPLAY_VERIFIED"


class ReplayStatus(str, Enum):
    """Status of replay verification."""

    VERIFIED = "VERIFIED"  # Bundle verified successfully
    FAILED = "FAILED"  # Verification failed
    NON_REPLAYABLE = "NON_REPLAYABLE"  # Bundle not replayable


@runtime_checkable
class RuntimeArtifact(Protocol):
    """
    Protocol for runtime artifacts that can be recorded in provenance.

    Artifacts must implement this protocol to be recorded.
    """

    @property
    def artifact_id(self) -> str:
        """Unique identifier for this artifact."""
        ...

    @property
    def artifact_type(self) -> str:
        """Type of artifact (e.g., 'step_acoustic', 'dxf')."""
        ...

    @property
    def content_bytes(self) -> bytes:
        """Raw content bytes of the artifact."""
        ...

    @property
    def metadata(self) -> Dict[str, Any]:
        """Artifact metadata."""
        ...

    def to_provenance_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for provenance recording."""
        ...


@dataclass
class RuntimeTraceEvent:
    """
    A single trace event in the runtime pipeline.

    Records a milestone in the execution path.
    """

    event_type: TraceEventType
    timestamp_iso: str
    details: Dict[str, Any] = field(default_factory=dict)
    sequence_number: int = 0

    @classmethod
    def create(
        cls,
        event_type: TraceEventType,
        details: Optional[Dict[str, Any]] = None,
        sequence_number: int = 0,
    ) -> "RuntimeTraceEvent":
        """Create a trace event with current timestamp."""
        return cls(
            event_type=event_type,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            details=details or {},
            sequence_number=sequence_number,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp_iso": self.timestamp_iso,
            "details": self.details,
            "sequence_number": self.sequence_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeTraceEvent":
        """Create from dictionary."""
        return cls(
            event_type=TraceEventType(data["event_type"]),
            timestamp_iso=data["timestamp_iso"],
            details=data.get("details", {}),
            sequence_number=data.get("sequence_number", 0),
        )


@dataclass
class ValidationLineage:
    """Snapshot of validation state for provenance."""

    request_id: str
    tier: str
    passed: bool
    signature_input_hash: str
    signature_validation_hash: str
    blocking_count: int = 0
    major_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "tier": self.tier,
            "passed": self.passed,
            "signature_input_hash": self.signature_input_hash,
            "signature_validation_hash": self.signature_validation_hash,
            "blocking_count": self.blocking_count,
            "major_count": self.major_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationLineage":
        """Create from dictionary."""
        return cls(
            request_id=data["request_id"],
            tier=data["tier"],
            passed=data["passed"],
            signature_input_hash=data["signature_input_hash"],
            signature_validation_hash=data["signature_validation_hash"],
            blocking_count=data.get("blocking_count", 0),
            major_count=data.get("major_count", 0),
        )


@dataclass
class AdmissionLineage:
    """Snapshot of admission state for provenance."""

    admission_id: str
    decision: str
    authorization_token: Optional[str]
    runtime_tier: str
    execution_mode: str
    authorized_adapters: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "admission_id": self.admission_id,
            "decision": self.decision,
            "authorization_token": self.authorization_token,
            "runtime_tier": self.runtime_tier,
            "execution_mode": self.execution_mode,
            "authorized_adapters": self.authorized_adapters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdmissionLineage":
        """Create from dictionary."""
        return cls(
            admission_id=data["admission_id"],
            decision=data["decision"],
            authorization_token=data.get("authorization_token"),
            runtime_tier=data["runtime_tier"],
            execution_mode=data["execution_mode"],
            authorized_adapters=data.get("authorized_adapters", []),
        )


@dataclass
class ArtifactLineage:
    """Snapshot of artifact for provenance."""

    artifact_id: str
    artifact_type: str
    content_hash: str
    content_size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "content_hash": self.content_hash,
            "content_size_bytes": self.content_size_bytes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArtifactLineage":
        """Create from dictionary."""
        return cls(
            artifact_id=data["artifact_id"],
            artifact_type=data["artifact_type"],
            content_hash=data["content_hash"],
            content_size_bytes=data["content_size_bytes"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class RuntimeArtifactProvenance:
    """
    Complete provenance record for a runtime artifact.

    Contains all lineage information needed for audit and replay.
    """

    run_id: str
    source_topology_id: str
    source_topology_hash: str
    validation_lineage: ValidationLineage
    admission_lineage: AdmissionLineage
    artifact_lineage: ArtifactLineage
    translator_id: str
    adapter_id: str
    trace_events: List[RuntimeTraceEvent]
    created_at: str
    provenance_hash: str = ""

    def __post_init__(self):
        if not self.provenance_hash:
            self.provenance_hash = self._compute_provenance_hash()

    def _compute_provenance_hash(self) -> str:
        """Compute hash of provenance content."""
        content = {
            "run_id": self.run_id,
            "source_topology_id": self.source_topology_id,
            "source_topology_hash": self.source_topology_hash,
            "validation_lineage": self.validation_lineage.to_dict(),
            "admission_lineage": self.admission_lineage.to_dict(),
            "artifact_lineage": self.artifact_lineage.to_dict(),
            "translator_id": self.translator_id,
            "adapter_id": self.adapter_id,
        }
        return stable_hash_model(content)[:32]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "source_topology_id": self.source_topology_id,
            "source_topology_hash": self.source_topology_hash,
            "validation_lineage": self.validation_lineage.to_dict(),
            "admission_lineage": self.admission_lineage.to_dict(),
            "artifact_lineage": self.artifact_lineage.to_dict(),
            "translator_id": self.translator_id,
            "adapter_id": self.adapter_id,
            "trace_events": [e.to_dict() for e in self.trace_events],
            "created_at": self.created_at,
            "provenance_hash": self.provenance_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeArtifactProvenance":
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            source_topology_id=data["source_topology_id"],
            source_topology_hash=data["source_topology_hash"],
            validation_lineage=ValidationLineage.from_dict(data["validation_lineage"]),
            admission_lineage=AdmissionLineage.from_dict(data["admission_lineage"]),
            artifact_lineage=ArtifactLineage.from_dict(data["artifact_lineage"]),
            translator_id=data["translator_id"],
            adapter_id=data["adapter_id"],
            trace_events=[
                RuntimeTraceEvent.from_dict(e) for e in data["trace_events"]
            ],
            created_at=data["created_at"],
            provenance_hash=data.get("provenance_hash", ""),
        )


@dataclass
class RuntimeReplayBundle:
    """
    Bundle containing all information needed for replay verification.

    This is a self-contained, serializable package of provenance.
    """

    bundle_id: str
    provenance: RuntimeArtifactProvenance
    replayable: bool
    replay_constraints: List[str] = field(default_factory=list)
    bundle_hash: str = ""
    version: str = "1.0.0"

    def __post_init__(self):
        if not self.bundle_hash:
            self.bundle_hash = self._compute_bundle_hash()

    def _compute_bundle_hash(self) -> str:
        """Compute hash of entire bundle."""
        content = {
            "bundle_id": self.bundle_id,
            "provenance": self.provenance.to_dict(),
            "replayable": self.replayable,
            "replay_constraints": self.replay_constraints,
            "version": self.version,
        }
        return stable_hash_model(content)[:32]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "bundle_id": self.bundle_id,
            "provenance": self.provenance.to_dict(),
            "replayable": self.replayable,
            "replay_constraints": self.replay_constraints,
            "bundle_hash": self.bundle_hash,
            "version": self.version,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return stable_json_dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeReplayBundle":
        """Create from dictionary."""
        return cls(
            bundle_id=data["bundle_id"],
            provenance=RuntimeArtifactProvenance.from_dict(data["provenance"]),
            replayable=data["replayable"],
            replay_constraints=data.get("replay_constraints", []),
            bundle_hash=data.get("bundle_hash", ""),
            version=data.get("version", "1.0.0"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "RuntimeReplayBundle":
        """Parse from JSON string."""
        data = stable_json_loads(json_str)
        return cls.from_dict(data)


@dataclass
class ReplayVerificationResult:
    """Result of replay verification."""

    status: ReplayStatus
    bundle_id: str
    verified_at: str
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    message: str = ""

    @property
    def passed(self) -> bool:
        """Check if verification passed."""
        return self.status == ReplayStatus.VERIFIED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "bundle_id": self.bundle_id,
            "verified_at": self.verified_at,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "constraints": self.constraints,
            "message": self.message,
            "passed": self.passed,
        }

    @classmethod
    def success(
        cls,
        bundle_id: str,
        checks_passed: List[str],
    ) -> "ReplayVerificationResult":
        """Create a successful verification result."""
        return cls(
            status=ReplayStatus.VERIFIED,
            bundle_id=bundle_id,
            verified_at=datetime.now(timezone.utc).isoformat(),
            checks_passed=checks_passed,
            message="Replay verification successful",
        )

    @classmethod
    def failure(
        cls,
        bundle_id: str,
        checks_failed: List[str],
        checks_passed: Optional[List[str]] = None,
        message: str = "Replay verification failed",
    ) -> "ReplayVerificationResult":
        """Create a failed verification result."""
        return cls(
            status=ReplayStatus.FAILED,
            bundle_id=bundle_id,
            verified_at=datetime.now(timezone.utc).isoformat(),
            checks_passed=checks_passed or [],
            checks_failed=checks_failed,
            message=message,
        )

    @classmethod
    def non_replayable(
        cls,
        bundle_id: str,
        constraints: List[str],
        message: str = "Bundle is not replayable",
    ) -> "ReplayVerificationResult":
        """Create a non-replayable result."""
        return cls(
            status=ReplayStatus.NON_REPLAYABLE,
            bundle_id=bundle_id,
            verified_at=datetime.now(timezone.utc).isoformat(),
            constraints=constraints,
            message=message,
        )
