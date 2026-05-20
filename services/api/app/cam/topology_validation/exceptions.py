"""
Topology Validation Exceptions.

Sprint: MRP-5I
Status: PROTOTYPE

Defines exception hierarchy for validation errors.
All validation exceptions inherit from ValidationError.
"""

from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """Base exception for all validation errors."""

    def __init__(
        self,
        message: str,
        classification: str = "BLOCKING",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.classification = classification
        self.details = details or {}


class ShellIntegrityError(ValidationError):
    """Error raised when shell integrity validation fails."""

    def __init__(
        self,
        message: str,
        shell_id: Optional[str] = None,
        is_closed: Optional[bool] = None,
        is_manifold: Optional[bool] = None,
        open_edge_count: Optional[int] = None,
    ):
        super().__init__(message, classification="BLOCKING")
        self.shell_id = shell_id
        self.is_closed = is_closed
        self.is_manifold = is_manifold
        self.open_edge_count = open_edge_count
        self.details = {
            "shell_id": shell_id,
            "is_closed": is_closed,
            "is_manifold": is_manifold,
            "open_edge_count": open_edge_count,
        }


class ContinuityError(ValidationError):
    """Error raised when continuity validation fails."""

    def __init__(
        self,
        message: str,
        junction_name: str,
        target_level: str,
        achieved_level: Optional[str] = None,
        classification: str = "MAJOR",
    ):
        super().__init__(message, classification=classification)
        self.junction_name = junction_name
        self.target_level = target_level
        self.achieved_level = achieved_level
        self.details = {
            "junction_name": junction_name,
            "target_level": target_level,
            "achieved_level": achieved_level,
        }


class BoundsError(ValidationError):
    """Error raised when bounding box validation fails."""

    def __init__(
        self,
        message: str,
        expected_bounds: Optional[List[float]] = None,
        actual_bounds: Optional[List[float]] = None,
    ):
        super().__init__(message, classification="MAJOR")
        self.expected_bounds = expected_bounds
        self.actual_bounds = actual_bounds
        self.details = {
            "expected_bounds": expected_bounds,
            "actual_bounds": actual_bounds,
        }


class TopologyStructureError(ValidationError):
    """Error raised when topology structure validation fails."""

    def __init__(
        self,
        message: str,
        expected_shells: Optional[int] = None,
        actual_shells: Optional[int] = None,
    ):
        super().__init__(message, classification="BLOCKING")
        self.expected_shells = expected_shells
        self.actual_shells = actual_shells
        self.details = {
            "expected_shells": expected_shells,
            "actual_shells": actual_shells,
        }


class ValidationRequestError(ValidationError):
    """Error raised when validation request is invalid."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[str]] = None,
    ):
        super().__init__(message, classification="BLOCKING")
        self.errors = errors or []
        self.details = {"errors": self.errors}
