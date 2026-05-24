"""
Certified Runtime Service Contracts.

Sprint: MRP-5Q/R
Status: PROTOTYPE

Request/result contracts for the CertifiedRuntimeService.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from app.cam.topology_validation import CertifiedTopology
from app.cam.runtime_admission import (
    AdmissionDecision,
    ExecutionMode,
    RuntimeTier,
)
from app.cam.runtime_provenance import RuntimeReplayBundle


class ServiceExecutionStatus(str, Enum):
    """Status of service execution."""

    SUCCESS = "SUCCESS"
    ADMISSION_REJECTED = "ADMISSION_REJECTED"
    CAPABILITY_REJECTED = "CAPABILITY_REJECTED"
    TRANSLATION_FAILED = "TRANSLATION_FAILED"
    ADAPTER_FAILED = "ADAPTER_FAILED"
    PROVENANCE_FAILED = "PROVENANCE_FAILED"
    INVALID_REQUEST = "INVALID_REQUEST"


class ArtifactIntent(str, Enum):
    """Intended artifact type from service execution."""

    STEP_ACOUSTIC = "step_acoustic"
    STEP_FLAT_BODY = "step_flat_body"
    DXF_OUTLINE = "dxf_outline"
    MOCK_DETERMINISTIC = "mock_deterministic"


@dataclass
class CertifiedRuntimeRequest:
    """
    Request for certified runtime service execution.

    Encapsulates all inputs needed for governed runtime execution:
    - certified topology (from validation)
    - runtime context (tier, mode)
    - adapter selection
    - capability resolution
    - artifact intent
    - trace metadata
    """

    certified_topology: CertifiedTopology
    adapter_id: str = "mock"
    capability_id: Optional[str] = None  # MRP-5V: namespaced capability ID
    artifact_intent: ArtifactIntent = ArtifactIntent.MOCK_DETERMINISTIC
    runtime_tier: RuntimeTier = RuntimeTier.PROTOTYPE
    execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC
    is_replay_mode: bool = False  # MRP-5V: replay context flag
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.certified_topology, CertifiedTopology):
            raise TypeError(
                f"certified_topology must be CertifiedTopology, got {type(self.certified_topology).__name__}"
            )

    @property
    def topology_request_id(self) -> str:
        """Request ID from the certified topology."""
        return self.certified_topology.request_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "topology_request_id": self.topology_request_id,
            "adapter_id": self.adapter_id,
            "capability_id": self.capability_id,
            "artifact_intent": self.artifact_intent.value,
            "runtime_tier": self.runtime_tier.value,
            "execution_mode": self.execution_mode.value,
            "is_replay_mode": self.is_replay_mode,
            "metadata": self.metadata,
        }


@dataclass
class CertifiedRuntimeResult:
    """
    Result of certified runtime service execution.

    Contains:
    - execution status
    - admission decision
    - capability resolution report (MRP-5V)
    - artifact metadata (if successful)
    - replay bundle (if successful)
    - error details (if failed)
    """

    status: ServiceExecutionStatus
    request_id: str
    admission_decision: Optional[AdmissionDecision] = None
    capability_resolution_report: Optional[Dict[str, Any]] = None  # MRP-5V
    artifact_id: Optional[str] = None
    artifact_hash: Optional[str] = None
    artifact_size_bytes: Optional[int] = None
    replay_bundle: Optional[RuntimeReplayBundle] = None
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def success(self) -> bool:
        return self.status == ServiceExecutionStatus.SUCCESS

    @property
    def replay_bundle_id(self) -> Optional[str]:
        if self.replay_bundle:
            return self.replay_bundle.bundle_id
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "request_id": self.request_id,
            "admission_decision": self.admission_decision.value if self.admission_decision else None,
            "capability_resolution_report": self.capability_resolution_report,
            "artifact_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "artifact_size_bytes": self.artifact_size_bytes,
            "replay_bundle_id": self.replay_bundle_id,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp,
        }

    @classmethod
    def success_result(
        cls,
        request_id: str,
        admission_decision: AdmissionDecision,
        artifact_id: str,
        artifact_hash: str,
        artifact_size_bytes: int,
        replay_bundle: RuntimeReplayBundle,
        execution_time_ms: float,
        capability_resolution_report: Optional[Dict[str, Any]] = None,
    ) -> "CertifiedRuntimeResult":
        """Create a successful result."""
        return cls(
            status=ServiceExecutionStatus.SUCCESS,
            request_id=request_id,
            admission_decision=admission_decision,
            capability_resolution_report=capability_resolution_report,
            artifact_id=artifact_id,
            artifact_hash=artifact_hash,
            artifact_size_bytes=artifact_size_bytes,
            replay_bundle=replay_bundle,
            execution_time_ms=execution_time_ms,
        )

    @classmethod
    def failure_result(
        cls,
        request_id: str,
        status: ServiceExecutionStatus,
        error_message: str,
        admission_decision: Optional[AdmissionDecision] = None,
        error_details: Optional[Dict[str, Any]] = None,
        execution_time_ms: float = 0.0,
    ) -> "CertifiedRuntimeResult":
        """Create a failure result."""
        return cls(
            status=status,
            request_id=request_id,
            admission_decision=admission_decision,
            error_message=error_message,
            error_details=error_details or {},
            execution_time_ms=execution_time_ms,
        )
