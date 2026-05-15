"""
Topology Builder Contracts.

Sprint: MRP-5H
Status: PROTOTYPE

Defines data contracts for topology construction requests and results.
These contracts form the interface between cad_semantics and the topology builder.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ContinuityLevel(str, Enum):
    """Geometric continuity levels for surface junctions."""

    G0 = "G0"  # Positional continuity (touching)
    G1 = "G1"  # Tangent continuity (smooth)
    G2 = "G2"  # Curvature continuity (very smooth)


class ShellType(str, Enum):
    """Types of shells that can be constructed."""

    FLAT_EXTRUSION = "flat_extrusion"  # Simple extrusion from profile
    LOFTED = "lofted"  # Loft between profiles
    SWEPT = "swept"  # Sweep along path
    COMPOSITE = "composite"  # Multiple shells joined


class TopologyTier(str, Enum):
    """Runtime tier affecting validation strictness."""

    PROTOTYPE = "PROTOTYPE"  # G0 acceptable, warnings allowed
    PRODUCTION = "PRODUCTION"  # G1 required, strict validation


@dataclass
class Point3D:
    """3D coordinate point."""

    x: float
    y: float
    z: float

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple for kernel operations."""
        return (self.x, self.y, self.z)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float, float]) -> "Point3D":
        """Create from tuple."""
        return cls(x=t[0], y=t[1], z=t[2])


@dataclass
class ProfileStack:
    """
    Stack of profiles for lofting or sweep operations.

    A profile is a closed 2D contour defined at a specific Z height.
    Multiple profiles form a stack for loft operations.
    """

    profiles: List[List[Point3D]] = field(default_factory=list)
    z_heights: List[float] = field(default_factory=list)

    def add_profile(self, points: List[Point3D], z_height: float) -> None:
        """Add a profile at a specific Z height."""
        self.profiles.append(points)
        self.z_heights.append(z_height)

    @property
    def profile_count(self) -> int:
        """Number of profiles in the stack."""
        return len(self.profiles)

    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the profile stack."""
        if len(self.profiles) != len(self.z_heights):
            return False, "Profile count must match Z height count"
        if len(self.profiles) < 1:
            return False, "At least one profile required"
        for i, profile in enumerate(self.profiles):
            if len(profile) < 3:
                return False, f"Profile {i} has fewer than 3 points"
        return True, None


@dataclass
class ContinuityMetadata:
    """
    Continuity requirements and achievements for a junction.

    Tracks what continuity was requested vs. what was achieved.
    """

    junction_name: str
    target: ContinuityLevel
    achieved: Optional[ContinuityLevel] = None
    validated: bool = False
    validation_error: Optional[str] = None

    @property
    def met_target(self) -> bool:
        """Check if achieved continuity meets or exceeds target."""
        if self.achieved is None:
            return False
        order = [ContinuityLevel.G0, ContinuityLevel.G1, ContinuityLevel.G2]
        return order.index(self.achieved) >= order.index(self.target)


@dataclass
class ShellDescriptor:
    """
    Descriptor for a constructed shell.

    Contains metadata about a shell without the actual geometry
    (which lives in kernel-specific handles).
    """

    shell_id: str
    shell_type: ShellType
    component_name: str
    is_closed: bool = False
    is_manifold: bool = False
    bounding_box: Optional[Tuple[Point3D, Point3D]] = None
    surface_count: int = 0
    edge_count: int = 0
    vertex_count: int = 0
    continuity: List[ContinuityMetadata] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "shell_id": self.shell_id,
            "shell_type": self.shell_type.value,
            "component_name": self.component_name,
            "is_closed": self.is_closed,
            "is_manifold": self.is_manifold,
            "bounding_box": (
                [self.bounding_box[0].to_tuple(), self.bounding_box[1].to_tuple()]
                if self.bounding_box
                else None
            ),
            "surface_count": self.surface_count,
            "edge_count": self.edge_count,
            "vertex_count": self.vertex_count,
            "continuity": [
                {
                    "junction_name": c.junction_name,
                    "target": c.target.value,
                    "achieved": c.achieved.value if c.achieved else None,
                    "validated": c.validated,
                    "met_target": c.met_target,
                }
                for c in self.continuity
            ],
        }


@dataclass
class PrototypeTopologyObject:
    """
    Prototype topology output object.

    Contains the constructed topology result with kernel-agnostic
    metadata. The actual geometry is stored in a kernel-specific
    handle that can be passed to translators.
    """

    request_id: str
    tier: TopologyTier
    shells: List[ShellDescriptor] = field(default_factory=list)
    kernel_handle: Optional[Any] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if the topology is valid for export."""
        if not self.shells:
            return False
        return all(shell.is_closed and shell.is_manifold for shell in self.shells)

    @property
    def shell_count(self) -> int:
        """Number of shells in the topology."""
        return len(self.shells)

    def add_shell(self, shell: ShellDescriptor) -> None:
        """Add a shell to the topology."""
        self.shells.append(shell)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "tier": self.tier.value,
            "shells": [s.to_dict() for s in self.shells],
            "is_valid": self.is_valid,
            "shell_count": self.shell_count,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass
class TopologyRequest:
    """
    Request for topology construction.

    Contains all information needed to construct topology from
    approved geometry and semantic descriptors.
    """

    request_id: str
    body_category: str
    tier: TopologyTier = TopologyTier.PROTOTYPE
    profile_stack: Optional[ProfileStack] = None
    thickness_mm: float = 3.0
    continuity_targets: Dict[str, ContinuityLevel] = field(default_factory=dict)
    boe_geometry: Optional[Dict[str, Any]] = None
    cad_semantics: Optional[Dict[str, Any]] = None
    options: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the request before processing.

        Returns (is_valid, list_of_errors).
        """
        errors = []

        if not self.request_id:
            errors.append("request_id is required")

        if not self.body_category:
            errors.append("body_category is required")

        if self.thickness_mm <= 0:
            errors.append("thickness_mm must be positive")

        if self.profile_stack:
            valid, error = self.profile_stack.validate()
            if not valid:
                errors.append(f"Profile stack invalid: {error}")

        return len(errors) == 0, errors


@dataclass
class TopologyResult:
    """
    Result of topology construction.

    Contains either a successful topology object or error information.
    """

    request_id: str
    success: bool
    topology: Optional[PrototypeTopologyObject] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_classification: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls,
        request_id: str,
        topology: PrototypeTopologyObject,
        warnings: Optional[List[str]] = None,
    ) -> "TopologyResult":
        """Create a successful result."""
        return cls(
            request_id=request_id,
            success=True,
            topology=topology,
            warnings=warnings or [],
        )

    @classmethod
    def failure_result(
        cls,
        request_id: str,
        error_type: str,
        error_message: str,
        classification: str = "BLOCKING",
    ) -> "TopologyResult":
        """Create a failure result."""
        return cls(
            request_id=request_id,
            success=False,
            error_type=error_type,
            error_message=error_message,
            error_classification=classification,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "request_id": self.request_id,
            "success": self.success,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }
        if self.success and self.topology:
            result["topology"] = self.topology.to_dict()
        else:
            result["error"] = {
                "type": self.error_type,
                "message": self.error_message,
                "classification": self.error_classification,
            }
        return result
