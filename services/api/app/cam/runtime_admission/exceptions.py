"""
Runtime Admission Exceptions.

Sprint: MRP-5M
Status: PROTOTYPE
"""

from typing import Any, Dict, List, Optional


class AdmissionError(Exception):
    """Base exception for admission errors."""

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
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class AdmissionDeniedError(AdmissionError):
    """Raised when execution admission is denied."""

    def __init__(
        self,
        message: str,
        policy_violations: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, error_code="ADMISSION_DENIED", details=details)
        self.policy_violations = policy_violations or []


class IntegrityViolationError(AdmissionError):
    """Raised when certification integrity is violated."""

    def __init__(
        self,
        message: str,
        violation_type: str,
        expected_hash: Optional[str] = None,
        actual_hash: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, error_code="INTEGRITY_VIOLATION", details=details)
        self.violation_type = violation_type
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash


class PolicyViolationError(AdmissionError):
    """Raised when a specific admission policy is violated."""

    def __init__(
        self,
        message: str,
        policy_id: str,
        severity: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, error_code="POLICY_VIOLATION", details=details)
        self.policy_id = policy_id
        self.severity = severity


class UncertifiedTopologyError(AdmissionError):
    """Raised when uncertified topology is submitted for admission."""

    def __init__(
        self,
        message: str = "Only CertifiedTopology may be submitted for runtime admission",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, error_code="UNCERTIFIED_TOPOLOGY", details=details)


class InvalidAdmissionRequestError(AdmissionError):
    """Raised when an admission request is malformed."""

    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, error_code="INVALID_REQUEST", details=details)
        self.validation_errors = validation_errors or []
