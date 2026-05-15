"""
Topology Builder Implementation.

Sprint: MRP-5H
Status: PROTOTYPE

Implements the TopologyBuilder protocol and AcousticTopologyBuilder
for constructing topology from approved geometry and semantic descriptors.

Key Principles:
    - Topology Builder CONSTRUCTS topology
    - BOE geometry is IMMUTABLE
    - No AI/adaptive topology generation
    - Explicit runtime classification
    - No silent degradation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
import uuid

from .contracts import (
    ContinuityLevel,
    ContinuityMetadata,
    Point3D,
    ProfileStack,
    PrototypeTopologyObject,
    ShellDescriptor,
    ShellType,
    TopologyRequest,
    TopologyResult,
    TopologyTier,
)
from .exceptions import (
    GeometryMutationError,
    TopologyBuildError,
    UnsupportedTopologyError,
)
from .runtime_support import (
    TopologyRuntimeSupport,
    can_generate_topology,
    classify_topology_runtime,
    get_unsupported_reason,
)


class KernelAdapter(Protocol):
    """Protocol for CAD kernel adapters."""

    def create_face_from_points(
        self, points: List[Point3D]
    ) -> Any:
        """Create a planar face from closed wire points."""
        ...

    def extrude_face(
        self, face_handle: Any, direction: Point3D, distance: float
    ) -> Any:
        """Extrude a face to create a solid."""
        ...

    def validate_closed(self, shell_handle: Any) -> bool:
        """Check if the shell is closed."""
        ...

    def validate_manifold(self, shell_handle: Any) -> bool:
        """Check if the shell is manifold."""
        ...

    def get_bounding_box(
        self, shell_handle: Any
    ) -> tuple[Point3D, Point3D]:
        """Get the bounding box of a shell."""
        ...


class TopologyBuilder(ABC):
    """
    Abstract base class for topology builders.

    Topology builders construct geometry topology from approved
    geometry and semantic descriptors. They operate between
    cad_semantics and translators in the authority chain.
    """

    def __init__(self, kernel_adapter: Optional[KernelAdapter] = None):
        """
        Initialize the topology builder.

        Args:
            kernel_adapter: Optional CAD kernel adapter for geometry operations.
                           If None, a mock adapter may be used for testing.
        """
        self._kernel = kernel_adapter
        self._geometry_tolerance_mm = 0.001

    @abstractmethod
    def build(self, request: TopologyRequest) -> TopologyResult:
        """
        Build topology from the request.

        Args:
            request: The topology construction request

        Returns:
            TopologyResult with either success or failure
        """
        ...

    @abstractmethod
    def supports(self, request: TopologyRequest) -> TopologyRuntimeSupport:
        """
        Check if this builder supports the request.

        Args:
            request: The topology construction request

        Returns:
            Runtime support classification
        """
        ...

    def validate_geometry_preservation(
        self,
        original_points: List[Point3D],
        output_points: List[Point3D],
    ) -> None:
        """
        Validate that BOE geometry has not been mutated.

        Raises GeometryMutationError if any point has drifted
        beyond tolerance.
        """
        if len(original_points) != len(output_points):
            raise GeometryMutationError(
                message="Point count changed during topology construction",
                original_point=None,
                output_point=None,
            )

        for i, (orig, out) in enumerate(zip(original_points, output_points)):
            drift = (
                (orig.x - out.x) ** 2
                + (orig.y - out.y) ** 2
                + (orig.z - out.z) ** 2
            ) ** 0.5

            if drift > self._geometry_tolerance_mm:
                raise GeometryMutationError(
                    message=f"Point {i} drifted {drift:.6f}mm during construction",
                    original_point=[orig.x, orig.y, orig.z],
                    output_point=[out.x, out.y, out.z],
                    drift_mm=drift,
                )


class AcousticTopologyBuilder(TopologyBuilder):
    """
    Topology builder for acoustic instrument bodies.

    Constructs topology for acoustic bodies following the
    authority chain from BOE geometry through cad_semantics.
    """

    def __init__(self, kernel_adapter: Optional[KernelAdapter] = None):
        """Initialize the acoustic topology builder."""
        super().__init__(kernel_adapter)

    def supports(self, request: TopologyRequest) -> TopologyRuntimeSupport:
        """
        Check if this builder supports the request.

        Returns the runtime support classification based on
        body category and semantic configuration.
        """
        support, _, _ = classify_topology_runtime(
            body_category=request.body_category,
            cad_semantics=request.cad_semantics,
            tier=request.tier,
        )
        return support

    def build(self, request: TopologyRequest) -> TopologyResult:
        """
        Build acoustic topology from the request.

        Follows the construction pipeline:
        1. Validate request
        2. Classify runtime support
        3. Construct topology (if supported)
        4. Validate result
        5. Return success or failure
        """
        # Step 1: Validate the request
        is_valid, errors = request.validate()
        if not is_valid:
            return TopologyResult.failure_result(
                request_id=request.request_id,
                error_type="ValidationError",
                error_message=f"Request validation failed: {'; '.join(errors)}",
                classification="BLOCKING",
            )

        # Step 2: Classify runtime support
        support, supported_features, unsupported_features = classify_topology_runtime(
            body_category=request.body_category,
            cad_semantics=request.cad_semantics,
            tier=request.tier,
        )

        # Step 3: Check if we can proceed
        if not can_generate_topology(support):
            reason = get_unsupported_reason(support, unsupported_features)
            return TopologyResult.failure_result(
                request_id=request.request_id,
                error_type="UnsupportedTopologyError",
                error_message=reason,
                classification="UNSUPPORTED_RUNTIME",
            )

        # Step 4: Build topology based on body category
        try:
            topology = self._construct_topology(
                request, support, supported_features, unsupported_features
            )
        except TopologyBuildError as e:
            return TopologyResult.failure_result(
                request_id=request.request_id,
                error_type=e.__class__.__name__,
                error_message=e.message,
                classification=e.classification,
            )
        except Exception as e:
            return TopologyResult.failure_result(
                request_id=request.request_id,
                error_type="InternalError",
                error_message=str(e),
                classification="BLOCKING",
            )

        # Step 5: Add warnings for partial support
        warnings = []
        if support == TopologyRuntimeSupport.PARTIAL_PROTOTYPE:
            warnings.append(
                f"Partial support: some features skipped: {unsupported_features}"
            )

        return TopologyResult.success_result(
            request_id=request.request_id,
            topology=topology,
            warnings=warnings,
        )

    def _construct_topology(
        self,
        request: TopologyRequest,
        support: TopologyRuntimeSupport,
        supported_features: List[str],
        unsupported_features: List[str],
    ) -> PrototypeTopologyObject:
        """
        Construct the actual topology.

        Dispatches to the appropriate construction method based
        on body category and available features.
        """
        topology = PrototypeTopologyObject(
            request_id=request.request_id,
            tier=request.tier,
        )

        # Determine construction method based on body category
        body_category = request.body_category

        if body_category in ("flat_body", "acoustic_flat_top"):
            self._construct_flat_extrusion(request, topology)
        elif body_category == "hollow_electric":
            self._construct_hollow_body(request, topology)
        else:
            raise UnsupportedTopologyError(
                message=f"No construction method for body category: {body_category}",
                body_category=body_category,
            )

        # Store metadata about what was constructed
        topology.metadata["supported_features"] = supported_features
        topology.metadata["unsupported_features"] = unsupported_features
        topology.metadata["construction_method"] = (
            "flat_extrusion"
            if body_category in ("flat_body", "acoustic_flat_top")
            else "hollow_body"
        )

        return topology

    def _construct_flat_extrusion(
        self, request: TopologyRequest, topology: PrototypeTopologyObject
    ) -> None:
        """
        Construct topology using flat extrusion.

        This is the simplest construction method for flat bodies:
        1. Create face from profile
        2. Extrude face by thickness
        3. Validate closure
        """
        # For PROTOTYPE tier, we construct descriptors without kernel
        # The actual kernel operations would happen in PRODUCTION

        shell_id = f"shell_{uuid.uuid4().hex[:8]}"

        # Create shell descriptor
        shell = ShellDescriptor(
            shell_id=shell_id,
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,  # Extrusion always produces closed shell
            is_manifold=True,
        )

        # Add continuity metadata (flat extrusion has no junctions)
        # Continuity is implicitly G2 within the shell

        # If we have a kernel, perform actual construction
        if self._kernel and request.profile_stack:
            self._kernel_construct_extrusion(request, shell)

        # Add default metadata for prototype
        shell.surface_count = 6  # Top, bottom, 4 sides (simplified)
        shell.edge_count = 12
        shell.vertex_count = 8

        topology.add_shell(shell)

    def _construct_hollow_body(
        self, request: TopologyRequest, topology: PrototypeTopologyObject
    ) -> None:
        """
        Construct topology for hollow body.

        Hollow bodies have:
        1. Outer shell
        2. Inner cavity (subtracted)
        3. Rim connecting top and back

        For PROTOTYPE tier, we create descriptors without full geometry.
        """
        # Outer shell
        outer_shell = ShellDescriptor(
            shell_id=f"shell_outer_{uuid.uuid4().hex[:8]}",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body_outer",
            is_closed=True,
            is_manifold=True,
        )

        # For PROTOTYPE, we note that rim continuity would need validation
        outer_shell.continuity.append(
            ContinuityMetadata(
                junction_name="rim_to_top",
                target=ContinuityLevel.G0,
                achieved=ContinuityLevel.G0,
                validated=False,
            )
        )
        outer_shell.continuity.append(
            ContinuityMetadata(
                junction_name="rim_to_back",
                target=ContinuityLevel.G0,
                achieved=ContinuityLevel.G0,
                validated=False,
            )
        )

        topology.add_shell(outer_shell)

        # Add warning that hollow body is partial support
        topology.add_warning(
            "Hollow body construction is PARTIAL_PROTOTYPE: "
            "cavity subtraction not implemented"
        )

    def _kernel_construct_extrusion(
        self, request: TopologyRequest, shell: ShellDescriptor
    ) -> None:
        """
        Perform actual kernel extrusion operation.

        Only called when a kernel adapter is available.
        """
        if not self._kernel or not request.profile_stack:
            return

        # Get the first profile (base)
        if request.profile_stack.profile_count < 1:
            return

        profile = request.profile_stack.profiles[0]

        # Create face from profile
        face_handle = self._kernel.create_face_from_points(profile)

        # Extrude in Z direction
        direction = Point3D(0, 0, 1)
        solid_handle = self._kernel.extrude_face(
            face_handle, direction, request.thickness_mm
        )

        # Validate result
        shell.is_closed = self._kernel.validate_closed(solid_handle)
        shell.is_manifold = self._kernel.validate_manifold(solid_handle)

        # Get bounding box
        shell.bounding_box = self._kernel.get_bounding_box(solid_handle)
