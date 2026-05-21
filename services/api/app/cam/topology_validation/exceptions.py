"""
Topology Validation Exceptions.

Sprint: MRP-5I
Status: PROTOTYPE

Exceptions for topology validation operations.
"""

from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """
    Raised when topology validation fails.

    Contains details about why validation failed.
    """

    def __init__(
        self,
        message: str,
        classification: str = "VALIDATION_FAILED",
        blocking_count: int = 0,
        findings: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.classification = classification
        self.blocking_count = blocking_count
        self.findings = findings or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": "ValidationError",
            "message": self.message,
            "classification": self.classification,
            "blocking_count": self.blocking_count,
            "findings": self.findings,
        }


class ShellIntegrityError(ValidationError):
    """Raised when shell integrity validation fails."""

    def __init__(self, message: str, shell_id: str = "unknown"):
        super().__init__(message, classification="SHELL_INTEGRITY")
        self.shell_id = shell_id


class ValidationRequestError(ValidationError):
    """Raised when validation request is malformed."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message, classification="REQUEST_ERROR")
        self.errors = errors or []
