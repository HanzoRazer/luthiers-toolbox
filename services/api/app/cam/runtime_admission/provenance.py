"""
Admission Provenance Tracking.

Sprint: MRP-5M
Status: PROTOTYPE

Tracks provenance of admission decisions for observability and audit.
Every admission or rejection produces observable provenance.

ARCHITECTURAL PRINCIPLE:
    Rejection is first-class.
    Admission decisions are explicit artifacts.
    All decisions must be traceable.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from .contracts import (
    AdmissionDecision,
    AdmissionRejection,
    AdmissionTrace,
    ExecutionAdmissionRequest,
    ExecutionAdmissionResult,
    PolicyEvaluationResult,
    RejectionReason,
)
from .integrity import IntegrityVerificationResult


@dataclass
class AdmissionProvenance:
    """
    Complete provenance record of an admission decision.

    Captures the full evaluation path from request to decision.
    """

    admission_id: str
    request_id: str
    trace_id: str
    decision: AdmissionDecision
    timestamp_iso: str
    topology_request_id: Optional[str] = None
    topology_tier: Optional[str] = None
    topology_input_hash: Optional[str] = None
    runtime_tier: Optional[str] = None
    execution_mode: Optional[str] = None
    integrity_result: Optional[Dict[str, Any]] = None
    policy_results: List[Dict[str, Any]] = field(default_factory=list)
    rejection_details: Optional[Dict[str, Any]] = None
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    authorized_adapters: List[str] = field(default_factory=list)
    authorization_token: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "admission_id": self.admission_id,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "decision": self.decision.value,
            "timestamp_iso": self.timestamp_iso,
            "topology_request_id": self.topology_request_id,
            "topology_tier": self.topology_tier,
            "topology_input_hash": self.topology_input_hash,
            "runtime_tier": self.runtime_tier,
            "execution_mode": self.execution_mode,
            "integrity_result": self.integrity_result,
            "policy_results": self.policy_results,
            "rejection_details": self.rejection_details,
            "warnings": self.warnings,
            "authorized_adapters": self.authorized_adapters,
            "authorization_token": self.authorization_token,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class ProvenanceBuilder:
    """
    Builder for admission provenance records.

    Accumulates evaluation data and produces a complete provenance record.
    """

    def __init__(self, request: ExecutionAdmissionRequest):
        self._admission_id = str(uuid.uuid4())
        self._request = request
        self._start_time = datetime.now(timezone.utc)
        self._integrity_result: Optional[IntegrityVerificationResult] = None
        self._policy_results: List[PolicyEvaluationResult] = []
        self._decision: Optional[AdmissionDecision] = None
        self._rejection: Optional[AdmissionRejection] = None
        self._warnings: List[PolicyEvaluationResult] = []
        self._authorized_adapters: List[str] = []
        self._authorization_token: Optional[str] = None
        self._metadata: Dict[str, Any] = {}

    def record_integrity_result(self, result: IntegrityVerificationResult) -> None:
        """Record integrity verification result."""
        self._integrity_result = result

    def record_policy_results(self, results: List[PolicyEvaluationResult]) -> None:
        """Record policy evaluation results."""
        self._policy_results = results

    def record_admission(
        self,
        authorized_adapters: List[str],
        authorization_token: str,
        warnings: Optional[List[PolicyEvaluationResult]] = None,
        conditional: bool = False,
    ) -> None:
        """Record admission decision."""
        self._decision = (
            AdmissionDecision.CONDITIONALLY_ADMITTED
            if conditional
            else AdmissionDecision.ADMITTED
        )
        self._authorized_adapters = authorized_adapters
        self._authorization_token = authorization_token
        self._warnings = warnings or []

    def record_rejection(self, rejection: AdmissionRejection) -> None:
        """Record rejection decision."""
        self._decision = AdmissionDecision.REJECTED
        self._rejection = rejection

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to provenance."""
        self._metadata[key] = value

    def build(self) -> AdmissionProvenance:
        """Build the provenance record."""
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - self._start_time).total_seconds() * 1000

        topology = self._request.certified_topology
        topology_request_id = None
        topology_tier = None
        topology_input_hash = None

        if hasattr(topology, "request_id"):
            topology_request_id = topology.request_id
        if hasattr(topology, "tier"):
            topology_tier = topology.tier.value if hasattr(topology.tier, "value") else str(topology.tier)
        if hasattr(topology, "signature") and topology.signature:
            topology_input_hash = topology.signature.input_hash

        return AdmissionProvenance(
            admission_id=self._admission_id,
            request_id=self._request.request_id,
            trace_id=self._request.trace_id,
            decision=self._decision or AdmissionDecision.REJECTED,
            timestamp_iso=end_time.isoformat(),
            topology_request_id=topology_request_id,
            topology_tier=topology_tier,
            topology_input_hash=topology_input_hash,
            runtime_tier=self._request.runtime_context.runtime_tier.value,
            execution_mode=self._request.runtime_context.execution_mode.value,
            integrity_result=(
                self._integrity_result.to_dict() if self._integrity_result else None
            ),
            policy_results=[pr.to_dict() for pr in self._policy_results],
            rejection_details=(
                self._rejection.to_dict() if self._rejection else None
            ),
            warnings=[w.to_dict() for w in self._warnings],
            authorized_adapters=self._authorized_adapters,
            authorization_token=self._authorization_token,
            duration_ms=duration_ms,
            metadata=self._metadata,
        )


class AdmissionLedger:
    """
    In-memory ledger of admission decisions.

    Stores recent admission provenance for audit and debugging.
    Production implementations would persist to storage.
    """

    def __init__(self, max_entries: int = 1000):
        self._entries: List[AdmissionProvenance] = []
        self._max_entries = max_entries

    def record(self, provenance: AdmissionProvenance) -> None:
        """Record a provenance entry."""
        self._entries.append(provenance)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)

    def get_by_admission_id(self, admission_id: str) -> Optional[AdmissionProvenance]:
        """Get provenance by admission ID."""
        for entry in self._entries:
            if entry.admission_id == admission_id:
                return entry
        return None

    def get_by_request_id(self, request_id: str) -> List[AdmissionProvenance]:
        """Get all provenance entries for a request ID."""
        return [e for e in self._entries if e.request_id == request_id]

    def get_by_trace_id(self, trace_id: str) -> List[AdmissionProvenance]:
        """Get all provenance entries for a trace ID."""
        return [e for e in self._entries if e.trace_id == trace_id]

    def get_rejections(self) -> List[AdmissionProvenance]:
        """Get all rejection entries."""
        return [
            e for e in self._entries
            if e.decision == AdmissionDecision.REJECTED
        ]

    def get_admissions(self) -> List[AdmissionProvenance]:
        """Get all admission entries."""
        return [
            e for e in self._entries
            if e.decision in (
                AdmissionDecision.ADMITTED,
                AdmissionDecision.CONDITIONALLY_ADMITTED,
            )
        ]

    def get_recent(self, count: int = 10) -> List[AdmissionProvenance]:
        """Get most recent entries."""
        return self._entries[-count:]

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export ledger contents."""
        return {
            "entry_count": len(self._entries),
            "max_entries": self._max_entries,
            "rejection_count": len(self.get_rejections()),
            "admission_count": len(self.get_admissions()),
            "entries": [e.to_dict() for e in self._entries],
        }


# Global ledger instance
_ADMISSION_LEDGER: Optional[AdmissionLedger] = None


def get_admission_ledger() -> AdmissionLedger:
    """Get the global admission ledger."""
    global _ADMISSION_LEDGER
    if _ADMISSION_LEDGER is None:
        _ADMISSION_LEDGER = AdmissionLedger()
    return _ADMISSION_LEDGER
