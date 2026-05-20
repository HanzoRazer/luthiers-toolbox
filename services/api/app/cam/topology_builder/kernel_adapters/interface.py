"""
Kernel Adapter Interface.

Sprint: MRP-5K
Status: PROTOTYPE

Defines the narrow contract for CAD kernel adapters.
Adapters implement ONLY geometric execution primitives.

CRITICAL ARCHITECTURAL BOUNDARIES:

Adapters MUST:
    - Execute geometric operations (create, extrude, loft, export)
    - Report geometric validation results (closed, manifold)
    - Return kernel-agnostic result types
    - Remain stateless between operations

Adapters MUST NOT:
    - Infer semantics from geometry
    - Repair topology silently
    - Reinterpret morphology
    - Normalize geometry beyond precision
    - Classify runtime feasibility
    - Introduce kernel-native ontology into results
    - Make decisions about what "should" happen
    - Consume or produce CertifiedTopology
    - Bypass validation

The adapter is a MECHANICAL EXECUTOR, not a SEMANTIC AUTHORITY.

Semantic authority belongs to:
    - cad_semantics (meaning)
    - topology_builder (construction)
    - topology_validation (certification)
    - translators (orchestration)

The adapter is downstream of ALL semantic decisions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable


class AdapterOperationType(str, Enum):
    """Types of adapter operations (for audit/logging only)."""

    CREATE_FACE = "CREATE_FACE"
    EXTRUDE = "EXTRUDE"
    LOFT = "LOFT"
    VALIDATE_CLOSED = "VALIDATE_CLOSED"
    VALIDATE_MANIFOLD = "VALIDATE_MANIFOLD"
    GET_BOUNDS = "GET_BOUNDS"
    EXPORT_STEP = "EXPORT_STEP"


class AdapterErrorCode(str, Enum):
    """Kernel-agnostic error codes."""

    INVALID_INPUT = "INVALID_INPUT"
    OPERATION_FAILED = "OPERATION_FAILED"
    GEOMETRY_ERROR = "GEOMETRY_ERROR"
    EXPORT_FAILED = "EXPORT_FAILED"
    KERNEL_NOT_AVAILABLE = "KERNEL_NOT_AVAILABLE"


@dataclass
class AdapterPoint3D:
    """
    Kernel-agnostic 3D point.

    This is the ONLY coordinate type adapters should use.
    No kernel-native point types (gp_Pnt, Vector, etc.) should
    leak into or out of the adapter interface.
    """

    x: float
    y: float
    z: float

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float, float]) -> "AdapterPoint3D":
        return cls(x=t[0], y=t[1], z=t[2])


@dataclass
class AdapterBoundingBox:
    """Kernel-agnostic bounding box."""

    min_point: AdapterPoint3D
    max_point: AdapterPoint3D

    @property
    def dimensions(self) -> Tuple[float, float, float]:
        """Return (width, height, depth)."""
        return (
            self.max_point.x - self.min_point.x,
            self.max_point.y - self.min_point.y,
            self.max_point.z - self.min_point.z,
        )


@dataclass
class AdapterGeometryHandle:
    """
    Opaque handle to kernel geometry.

    The handle ID is the ONLY identifier that crosses the adapter boundary.
    Callers must not inspect or depend on handle internals.

    The kernel_ref field is for adapter-internal use only and
    MUST NOT be accessed by callers.
    """

    handle_id: str
    geometry_type: str  # "face", "solid", "shell"
    kernel_ref: Any = field(default=None, repr=False)  # Internal only


@dataclass
class AdapterResult:
    """
    Result of an adapter operation.

    Kernel-agnostic success/failure with optional geometry handle.
    No kernel-native types should appear in this result.
    """

    success: bool
    operation: AdapterOperationType
    handle: Optional[AdapterGeometryHandle] = None
    error_code: Optional[AdapterErrorCode] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterValidationResult:
    """Result of a validation operation (closed, manifold)."""

    passed: bool
    operation: AdapterOperationType
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterExportResult:
    """Result of an export operation."""

    success: bool
    content: bytes = field(default=b"")
    format_version: str = ""
    error_code: Optional[AdapterErrorCode] = None
    error_message: Optional[str] = None


@runtime_checkable
class KernelAdapterInterface(Protocol):
    """
    Protocol defining the narrow kernel adapter contract.

    All kernel adapters MUST implement this protocol.
    The interface is intentionally minimal — adapters execute
    geometric primitives only.

    FORBIDDEN BEHAVIORS (protocol cannot enforce, but callers should verify):
        - Semantic inference
        - Silent topology repair
        - Morphology reinterpretation
        - Geometry normalization beyond precision
        - Runtime feasibility classification
        - Kernel-native ontology in results
    """

    @property
    def adapter_id(self) -> str:
        """Unique identifier for this adapter."""
        ...

    @property
    def kernel_name(self) -> str:
        """Name of the underlying kernel (e.g., 'mock', 'occ', 'cadquery')."""
        ...

    @property
    def is_available(self) -> bool:
        """Check if the kernel is available for use."""
        ...

    def create_face_from_points(
        self,
        points: List[AdapterPoint3D],
    ) -> AdapterResult:
        """
        Create a planar face from closed wire points.

        Args:
            points: Ordered list of points forming a closed wire

        Returns:
            AdapterResult with face handle on success
        """
        ...

    def extrude_face(
        self,
        face_handle: AdapterGeometryHandle,
        direction: AdapterPoint3D,
        distance: float,
    ) -> AdapterResult:
        """
        Extrude a face to create a solid.

        Args:
            face_handle: Handle from create_face_from_points
            direction: Unit direction vector
            distance: Extrusion distance in mm

        Returns:
            AdapterResult with solid handle on success
        """
        ...

    def loft_profiles(
        self,
        profile_handles: List[AdapterGeometryHandle],
    ) -> AdapterResult:
        """
        Loft between multiple profile faces.

        Args:
            profile_handles: Ordered list of profile face handles

        Returns:
            AdapterResult with lofted solid handle on success
        """
        ...

    def validate_closed(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> AdapterValidationResult:
        """
        Check if geometry is closed (watertight).

        Returns:
            AdapterValidationResult with passed=True if closed
        """
        ...

    def validate_manifold(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> AdapterValidationResult:
        """
        Check if geometry is manifold.

        Returns:
            AdapterValidationResult with passed=True if manifold
        """
        ...

    def get_bounding_box(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> Optional[AdapterBoundingBox]:
        """
        Get bounding box of geometry.

        Returns:
            AdapterBoundingBox or None if unavailable
        """
        ...

    def export_step(
        self,
        geometry_handle: AdapterGeometryHandle,
        header_metadata: Optional[Dict[str, str]] = None,
    ) -> AdapterExportResult:
        """
        Export geometry to STEP format.

        Args:
            geometry_handle: Handle to geometry to export
            header_metadata: Optional STEP header fields

        Returns:
            AdapterExportResult with STEP content bytes
        """
        ...


class BaseKernelAdapter(ABC):
    """
    Abstract base class for kernel adapters.

    Provides common functionality and enforces the narrow interface.
    Subclasses implement kernel-specific operations.
    """

    def __init__(self, adapter_id: str, kernel_name: str):
        self._adapter_id = adapter_id
        self._kernel_name = kernel_name
        self._handle_counter = 0

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    @property
    def kernel_name(self) -> str:
        return self._kernel_name

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the kernel is available."""
        ...

    def _next_handle_id(self, prefix: str = "geom") -> str:
        """Generate unique handle ID."""
        self._handle_counter += 1
        return f"{prefix}_{self._adapter_id}_{self._handle_counter}"

    @abstractmethod
    def create_face_from_points(
        self,
        points: List[AdapterPoint3D],
    ) -> AdapterResult:
        ...

    @abstractmethod
    def extrude_face(
        self,
        face_handle: AdapterGeometryHandle,
        direction: AdapterPoint3D,
        distance: float,
    ) -> AdapterResult:
        ...

    @abstractmethod
    def loft_profiles(
        self,
        profile_handles: List[AdapterGeometryHandle],
    ) -> AdapterResult:
        ...

    @abstractmethod
    def validate_closed(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> AdapterValidationResult:
        ...

    @abstractmethod
    def validate_manifold(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> AdapterValidationResult:
        ...

    @abstractmethod
    def get_bounding_box(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> Optional[AdapterBoundingBox]:
        ...

    @abstractmethod
    def export_step(
        self,
        geometry_handle: AdapterGeometryHandle,
        header_metadata: Optional[Dict[str, str]] = None,
    ) -> AdapterExportResult:
        ...
