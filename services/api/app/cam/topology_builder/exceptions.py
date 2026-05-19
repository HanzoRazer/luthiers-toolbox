"""
Topology Builder Exceptions.

Sprint: MRP-5H
Status: PROTOTYPE

Defines exception hierarchy for topology construction failures.
Follows the classification model from TOPOLOGY_FAILURE_CLASSIFICATION.md.
"""

from typing import Any, Dict, List, Optional


class TopologyBuildError(Exception):
    """Base exception for topology builder errors."""

    def __init__(
        self,
        message: str,
        classification: str = "BLOCKING",
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.classification = classification
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "classification": self.classification,
            "context": self.context,
        }


class GeometryMutationError(TopologyBuildError):
    """
    Raised when BOE-approved geometry would be mutated.

    Classification: BLOCKING
    This is a critical error - approved geometry must remain immutable.
    """

    def __init__(
        self,
        message: str,
        original_point: Optional[List[float]] = None,
        output_point: Optional[List[float]] = None,
        drift_mm: Optional[float] = None,
    ):
        context: Dict[str, Any] = {}
        if original_point:
            context["original_point"] = original_point
        if output_point:
            context["output_point"] = output_point
        if drift_mm is not None:
            context["drift_mm"] = drift_mm

        super().__init__(
            message=message,
            classification="BLOCKING",
            context=context,
        )
        self.original_point = original_point
        self.output_point = output_point
        self.drift_mm = drift_mm


class UnsupportedTopologyError(TopologyBuildError):
    """
    Raised when requested topology cannot be generated.

    Classification: UNSUPPORTED_RUNTIME
    Clean rejection - no degraded output produced.
    """

    def __init__(
        self,
        message: str,
        body_category: Optional[str] = None,
        unsupported_features: Optional[List[str]] = None,
    ):
        context: Dict[str, Any] = {}
        if body_category:
            context["body_category"] = body_category
        if unsupported_features:
            context["unsupported_features"] = unsupported_features

        super().__init__(
            message=message,
            classification="UNSUPPORTED_RUNTIME",
            context=context,
        )
        self.body_category = body_category
        self.unsupported_features = unsupported_features or []


class ContinuityValidationError(TopologyBuildError):
    """
    Raised when continuity requirements cannot be met.

    Classification: MAJOR (PROTOTYPE) or BLOCKING (PRODUCTION)
    """

    def __init__(
        self,
        message: str,
        target_continuity: str,
        achieved_continuity: Optional[str] = None,
        junction_type: Optional[str] = None,
        tier: str = "PROTOTYPE",
    ):
        # PROTOTYPE allows G0 fallback; PRODUCTION blocks
        classification = "MAJOR" if tier == "PROTOTYPE" else "BLOCKING"

        context = {
            "target_continuity": target_continuity,
            "tier": tier,
        }
        if achieved_continuity:
            context["achieved_continuity"] = achieved_continuity
        if junction_type:
            context["junction_type"] = junction_type

        super().__init__(
            message=message,
            classification=classification,
            context=context,
        )
        self.target_continuity = target_continuity
        self.achieved_continuity = achieved_continuity
        self.junction_type = junction_type
        self.tier = tier


class ShellClosureError(TopologyBuildError):
    """
    Raised when shell cannot be closed.

    Classification: BLOCKING
    Open shells are never acceptable.
    """

    def __init__(
        self,
        message: str,
        open_edge_count: Optional[int] = None,
        gap_mm: Optional[float] = None,
    ):
        context: Dict[str, Any] = {}
        if open_edge_count is not None:
            context["open_edge_count"] = open_edge_count
        if gap_mm is not None:
            context["gap_mm"] = gap_mm

        super().__init__(
            message=message,
            classification="BLOCKING",
            context=context,
        )
        self.open_edge_count = open_edge_count
        self.gap_mm = gap_mm


class ProfileValidationError(TopologyBuildError):
    """
    Raised when profile data is invalid.

    Classification: BLOCKING or MAJOR depending on severity.
    """

    def __init__(
        self,
        message: str,
        profile_type: str,
        issue: str,
        classification: str = "MAJOR",
    ):
        context = {
            "profile_type": profile_type,
            "issue": issue,
        }
        super().__init__(
            message=message,
            classification=classification,
            context=context,
        )
        self.profile_type = profile_type
        self.issue = issue


class KernelAdapterError(TopologyBuildError):
    """
    Raised when CAD kernel adapter fails.

    Classification: BLOCKING
    Kernel failures are infrastructure issues.
    """

    def __init__(
        self,
        message: str,
        kernel_name: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        context = {}
        if kernel_name:
            context["kernel_name"] = kernel_name
        if operation:
            context["operation"] = operation

        super().__init__(
            message=message,
            classification="BLOCKING",
            context=context,
        )
        self.kernel_name = kernel_name
        self.operation = operation
