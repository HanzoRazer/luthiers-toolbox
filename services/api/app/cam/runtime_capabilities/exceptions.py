"""
Runtime Capability Exceptions.

Sprint: MRP-5V
Status: PROTOTYPE

Exceptions for the runtime capability federation layer.
"""

from typing import List, Optional


class RuntimeCapabilityError(Exception):
    """Base exception for runtime capability errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class CapabilityNotFoundError(RuntimeCapabilityError):
    """Raised when a requested capability is not registered."""

    def __init__(self, capability_id: str, available_ids: Optional[List[str]] = None):
        self.capability_id = capability_id
        self.available_ids = available_ids or []
        message = f"Capability not found: {capability_id}"
        details = {
            "capability_id": capability_id,
            "available_count": len(self.available_ids),
        }
        super().__init__(message, details)


class DuplicateCapabilityError(RuntimeCapabilityError):
    """Raised when attempting to register a duplicate capability ID."""

    def __init__(self, capability_id: str, source_name: str):
        self.capability_id = capability_id
        self.source_name = source_name
        message = f"Duplicate capability ID: {capability_id} (from source: {source_name})"
        details = {
            "capability_id": capability_id,
            "source_name": source_name,
        }
        super().__init__(message, details)


class CapabilityDisabledError(RuntimeCapabilityError):
    """Raised when attempting to use a disabled capability."""

    def __init__(self, capability_id: str, reason: Optional[str] = None):
        self.capability_id = capability_id
        self.reason = reason
        message = f"Capability is disabled: {capability_id}"
        if reason:
            message += f" ({reason})"
        details = {
            "capability_id": capability_id,
            "reason": reason,
        }
        super().__init__(message, details)


class ReplaySafetyViolationError(RuntimeCapabilityError):
    """Raised when a replay-unsafe capability is used in replay context."""

    def __init__(self, capability_id: str):
        self.capability_id = capability_id
        message = f"Capability is not replay-safe: {capability_id}"
        details = {
            "capability_id": capability_id,
            "violation": "replay_safety",
        }
        super().__init__(message, details)


class PolicyEvaluationError(RuntimeCapabilityError):
    """Raised when policy evaluation fails."""

    def __init__(self, capability_id: str, policy_name: str, reason: str):
        self.capability_id = capability_id
        self.policy_name = policy_name
        self.reason = reason
        message = f"Policy '{policy_name}' rejected capability '{capability_id}': {reason}"
        details = {
            "capability_id": capability_id,
            "policy_name": policy_name,
            "reason": reason,
        }
        super().__init__(message, details)


class CapabilityResolutionError(RuntimeCapabilityError):
    """Raised when capability resolution fails."""

    def __init__(
        self,
        capability_id: str,
        rejection_reasons: List[str],
    ):
        self.capability_id = capability_id
        self.rejection_reasons = rejection_reasons
        message = f"Capability resolution failed: {capability_id}"
        details = {
            "capability_id": capability_id,
            "rejection_reasons": rejection_reasons,
        }
        super().__init__(message, details)


class InvalidCapabilityIdError(RuntimeCapabilityError):
    """Raised when a capability ID has invalid format."""

    VALID_NAMESPACES = ["operation", "translator", "adapter", "service", "replay"]

    def __init__(self, capability_id: str, reason: str):
        self.capability_id = capability_id
        self.reason = reason
        message = f"Invalid capability ID '{capability_id}': {reason}"
        details = {
            "capability_id": capability_id,
            "reason": reason,
            "valid_namespaces": self.VALID_NAMESPACES,
        }
        super().__init__(message, details)


class SourceAdapterError(RuntimeCapabilityError):
    """Raised when a capability source adapter fails."""

    def __init__(self, source_name: str, reason: str):
        self.source_name = source_name
        self.reason = reason
        message = f"Source adapter '{source_name}' failed: {reason}"
        details = {
            "source_name": source_name,
            "reason": reason,
        }
        super().__init__(message, details)


class ManifestGenerationError(RuntimeCapabilityError):
    """Raised when manifest generation fails."""

    def __init__(self, reason: str):
        self.reason = reason
        message = f"Manifest generation failed: {reason}"
        details = {"reason": reason}
        super().__init__(message, details)
