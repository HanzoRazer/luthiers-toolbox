"""
Runtime Provenance Exceptions.

Sprint: MRP-5N
Status: PROTOTYPE

Exceptions for runtime provenance and replay operations.
"""

from typing import Any, Dict, List, Optional


class ProvenanceError(Exception):
    """Base exception for provenance errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ReplayError(ProvenanceError):
    """
    Raised when replay verification fails.

    Indicates the replay bundle cannot be verified or replayed.
    """

    def __init__(
        self,
        message: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="REPLAY_ERROR",
            details=details,
        )
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["reason"] = self.reason
        return result


class IntegrityError(ProvenanceError):
    """
    Raised when provenance integrity verification fails.

    Indicates tampering or corruption in the provenance chain.
    """

    def __init__(
        self,
        message: str,
        check_name: str,
        expected_value: Optional[str] = None,
        actual_value: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="INTEGRITY_ERROR",
            details=details,
        )
        self.check_name = check_name
        self.expected_value = expected_value
        self.actual_value = actual_value

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["check_name"] = self.check_name
        if self.expected_value:
            result["expected_value"] = self.expected_value
        if self.actual_value:
            result["actual_value"] = self.actual_value
        return result


class ProvenanceRecordingError(ProvenanceError):
    """
    Raised when provenance recording fails.

    Indicates missing or invalid inputs during recording.
    """

    def __init__(
        self,
        message: str,
        missing_fields: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="RECORDING_ERROR",
            details=details,
        )
        self.missing_fields = missing_fields or []

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["missing_fields"] = self.missing_fields
        return result


class NonReplayableError(ProvenanceError):
    """
    Raised when a bundle is marked as non-replayable.

    Not an error per se, but indicates replay cannot proceed.
    """

    def __init__(
        self,
        message: str,
        constraints: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="NON_REPLAYABLE",
            details=details,
        )
        self.constraints = constraints or []

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["constraints"] = self.constraints
        return result


class BundleSerializationError(ProvenanceError):
    """
    Raised when bundle serialization/deserialization fails.
    """

    def __init__(
        self,
        message: str,
        operation: str,  # "serialize" or "deserialize"
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="SERIALIZATION_ERROR",
            details=details,
        )
        self.operation = operation

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["operation"] = self.operation
        return result
