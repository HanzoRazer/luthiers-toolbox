"""
Certified Runtime Service Exceptions.

Sprint: MRP-5Q/R
Status: PROTOTYPE
"""

from typing import Any, Dict, Optional


class RuntimeServiceError(Exception):
    """Base exception for runtime service errors."""

    def __init__(
        self,
        message: str,
        code: str = "RUNTIME_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class InvalidRequestError(RuntimeServiceError):
    """Request validation failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INVALID_REQUEST", details)


class UncertifiedTopologyError(RuntimeServiceError):
    """Topology is not certified."""

    def __init__(self, message: str = "Topology must be certified"):
        super().__init__(message, "UNCERTIFIED_TOPOLOGY")


class AdmissionRejectedError(RuntimeServiceError):
    """Admission was rejected."""

    def __init__(
        self,
        message: str,
        decision: str,
        rejections: Optional[list] = None,
    ):
        super().__init__(
            message,
            "ADMISSION_REJECTED",
            {"decision": decision, "rejections": rejections or []},
        )
        self.decision = decision
        self.rejections = rejections or []


class AdapterUnavailableError(RuntimeServiceError):
    """Requested adapter is not available."""

    def __init__(self, adapter_id: str, available: Optional[list] = None):
        super().__init__(
            f"Adapter '{adapter_id}' is not available",
            "ADAPTER_UNAVAILABLE",
            {"adapter_id": adapter_id, "available_adapters": available or []},
        )
        self.adapter_id = adapter_id


class TranslationFailedError(RuntimeServiceError):
    """Translation failed."""

    def __init__(self, message: str, translator_id: Optional[str] = None):
        super().__init__(
            message,
            "TRANSLATION_FAILED",
            {"translator_id": translator_id},
        )


class ProvenanceRecordingError(RuntimeServiceError):
    """Failed to record provenance."""

    def __init__(self, message: str):
        super().__init__(message, "PROVENANCE_RECORDING_FAILED")


class CapabilityResolutionFailedError(RuntimeServiceError):
    """Capability resolution failed."""

    def __init__(
        self,
        capability_id: str,
        rejection_reasons: list,
    ):
        super().__init__(
            f"Capability resolution failed for '{capability_id}'",
            "CAPABILITY_RESOLUTION_FAILED",
            {
                "capability_id": capability_id,
                "rejection_reasons": rejection_reasons,
            },
        )
        self.capability_id = capability_id
        self.rejection_reasons = rejection_reasons
