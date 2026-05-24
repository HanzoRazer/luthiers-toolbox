"""
Runtime Capability Contracts.

Sprint: MRP-5V
Status: PROTOTYPE

Core contracts for the runtime capability federation layer.

Design principles:
  - CapabilitySource is an interface for domain-local registries
  - FederatedCapability is the unified representation
  - Resolution returns metadata + decision, not callables
  - Namespaced IDs prevent collision across domains
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Literal, Optional, Set


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class CapabilityNamespace(str, Enum):
    """Valid capability namespaces."""
    OPERATION = "operation"
    TRANSLATOR = "translator"
    ADAPTER = "adapter"
    SERVICE = "service"
    REPLAY = "replay"


class GovernanceClassification(str, Enum):
    """Governance classification for capabilities."""
    PUBLIC_GOVERNED = "public_governed"
    DEVELOPER_EXPERIMENTAL = "developer_experimental"
    INTERNAL_ONLY = "internal_only"


class PolicyDecision(str, Enum):
    """Policy evaluation decision."""
    ALLOWED = "allowed"
    RESTRICTED = "restricted"
    REJECTED = "rejected"


class ResolutionStatus(str, Enum):
    """Capability resolution status."""
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    DISABLED = "disabled"
    POLICY_REJECTED = "policy_rejected"
    REPLAY_UNSAFE = "replay_unsafe"
    COMPATIBILITY_FAILED = "compatibility_failed"


# -----------------------------------------------------------------------------
# Capability ID Utilities
# -----------------------------------------------------------------------------

def parse_capability_id(capability_id: str) -> tuple[CapabilityNamespace, str]:
    """
    Parse a namespaced capability ID.

    Args:
        capability_id: Full capability ID (e.g., "operation:nut_slot")

    Returns:
        Tuple of (namespace, local_id)

    Raises:
        ValueError: If ID format is invalid
    """
    if ":" not in capability_id:
        raise ValueError(
            f"Invalid capability ID '{capability_id}': missing namespace prefix. "
            f"Expected format: <namespace>:<id>"
        )

    parts = capability_id.split(":", 1)
    namespace_str = parts[0]
    local_id = parts[1]

    if not local_id:
        raise ValueError(
            f"Invalid capability ID '{capability_id}': empty local ID"
        )

    try:
        namespace = CapabilityNamespace(namespace_str)
    except ValueError:
        valid = [n.value for n in CapabilityNamespace]
        raise ValueError(
            f"Invalid capability ID '{capability_id}': unknown namespace '{namespace_str}'. "
            f"Valid namespaces: {valid}"
        )

    return namespace, local_id


def make_capability_id(namespace: CapabilityNamespace, local_id: str) -> str:
    """
    Create a namespaced capability ID.

    Args:
        namespace: Capability namespace
        local_id: Local identifier within namespace

    Returns:
        Full capability ID (e.g., "operation:nut_slot")
    """
    return f"{namespace.value}:{local_id}"


def validate_capability_id(capability_id: str) -> bool:
    """
    Validate a capability ID format.

    Args:
        capability_id: ID to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        parse_capability_id(capability_id)
        return True
    except ValueError:
        return False


# -----------------------------------------------------------------------------
# Federated Capability
# -----------------------------------------------------------------------------

@dataclass
class FederatedCapability:
    """
    Unified capability representation in the federation layer.

    This is the common structure that all domain-local capabilities
    are mapped to when federated.
    """

    # Identity
    capability_id: str
    namespace: CapabilityNamespace
    local_id: str
    version: str = "0.0.0"

    # Source tracking
    source_name: str = ""

    # Display
    display_name: str = ""
    description: str = ""

    # Governance
    governance_classification: GovernanceClassification = GovernanceClassification.INTERNAL_ONLY
    enabled: bool = True
    deterministic: bool = True
    replay_safe: bool = True

    # Compatibility
    compatibility_tags: Set[str] = field(default_factory=set)
    required_tags: Set[str] = field(default_factory=set)

    # Domain-specific metadata (passthrough)
    domain_metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.compatibility_tags, list):
            self.compatibility_tags = set(self.compatibility_tags)
        if isinstance(self.required_tags, list):
            self.required_tags = set(self.required_tags)


# -----------------------------------------------------------------------------
# Capability Source Interface
# -----------------------------------------------------------------------------

class CapabilitySource(ABC):
    """
    Interface for domain-local capability registries.

    Implementations wrap existing registries (cam_operation_registry,
    translator_capability_registry) without modifying them.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique name for this capability source."""
        ...

    @property
    @abstractmethod
    def namespace(self) -> CapabilityNamespace:
        """Namespace for capabilities from this source."""
        ...

    @abstractmethod
    def list_capability_ids(self) -> List[str]:
        """
        List all local capability IDs from this source.

        Returns:
            List of local IDs (without namespace prefix)
        """
        ...

    @abstractmethod
    def get_capability(self, local_id: str) -> Optional[FederatedCapability]:
        """
        Get a capability by local ID.

        Args:
            local_id: Local identifier (without namespace prefix)

        Returns:
            FederatedCapability if found, None otherwise
        """
        ...

    def list_capabilities(self) -> List[FederatedCapability]:
        """
        List all capabilities from this source.

        Returns:
            List of all FederatedCapability entries
        """
        capabilities = []
        for local_id in self.list_capability_ids():
            cap = self.get_capability(local_id)
            if cap is not None:
                capabilities.append(cap)
        return capabilities


# -----------------------------------------------------------------------------
# Resolution Context
# -----------------------------------------------------------------------------

@dataclass
class ResolutionContext:
    """
    Context for capability resolution.

    Provides information needed for policy evaluation.
    """

    # Execution context
    is_replay_mode: bool = False
    require_deterministic: bool = False
    require_replay_safe: bool = False

    # Compatibility requirements
    required_compatibility_tags: Set[str] = field(default_factory=set)

    # Request metadata (for audit trail)
    request_id: Optional[str] = None
    trace_id: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.required_compatibility_tags, list):
            self.required_compatibility_tags = set(self.required_compatibility_tags)

        # If replay mode, automatically require replay safety
        if self.is_replay_mode:
            self.require_replay_safe = True


# -----------------------------------------------------------------------------
# Resolution Result
# -----------------------------------------------------------------------------

@dataclass
class CompatibilitySummary:
    """Summary of compatibility check results."""

    compatible: bool = True
    satisfied_tags: Set[str] = field(default_factory=set)
    missing_tags: Set[str] = field(default_factory=set)
    notes: List[str] = field(default_factory=list)


@dataclass
class CapabilityResolutionResult:
    """
    Result of capability resolution.

    Contains decision + metadata, NOT callable executables.
    The runtime service owns orchestration and execution.
    """

    # Resolution outcome
    status: ResolutionStatus
    requested_capability_id: str

    # Resolved capability (if found)
    resolved_capability: Optional[FederatedCapability] = None

    # Policy decision
    policy_decision: PolicyDecision = PolicyDecision.REJECTED
    rejection_reasons: List[str] = field(default_factory=list)

    # Compatibility
    compatibility_summary: CompatibilitySummary = field(
        default_factory=CompatibilitySummary
    )

    # Audit trail
    policies_evaluated: List[str] = field(default_factory=list)

    @property
    def is_resolved(self) -> bool:
        """Whether resolution was successful."""
        return self.status == ResolutionStatus.RESOLVED

    @property
    def is_allowed(self) -> bool:
        """Whether capability may be used."""
        return self.is_resolved and self.policy_decision == PolicyDecision.ALLOWED

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "requested_capability_id": self.requested_capability_id,
            "resolved_capability_id": (
                self.resolved_capability.capability_id
                if self.resolved_capability
                else None
            ),
            "policy_decision": self.policy_decision.value,
            "rejection_reasons": self.rejection_reasons,
            "compatibility": {
                "compatible": self.compatibility_summary.compatible,
                "satisfied_tags": list(self.compatibility_summary.satisfied_tags),
                "missing_tags": list(self.compatibility_summary.missing_tags),
            },
            "policies_evaluated": self.policies_evaluated,
        }
