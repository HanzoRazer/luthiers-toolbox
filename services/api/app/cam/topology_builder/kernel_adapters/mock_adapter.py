"""
Mock CAD Kernel Adapter.

Sprint: MRP-5H
Status: PROTOTYPE

Provides a mock kernel adapter for testing topology construction
without requiring a real CAD kernel. Records operations for
verification in tests.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..contracts import Point3D


@dataclass
class MockShellHandle:
    """Mock handle representing a kernel shell object."""

    handle_id: str
    shell_type: str
    points: List[Point3D] = field(default_factory=list)
    is_closed: bool = True
    is_manifold: bool = True
    bounding_box: Optional[Tuple[Point3D, Point3D]] = None


@dataclass
class OperationRecord:
    """Record of a kernel operation for test verification."""

    operation: str
    args: Dict[str, Any] = field(default_factory=dict)
    result: Any = None


class MockKernelAdapter:
    """
    Mock CAD kernel adapter for testing.

    Records all operations and returns configurable results.
    Can be configured to fail specific operations for error path testing.
    """

    def __init__(
        self,
        should_fail_create: bool = False,
        should_fail_extrude: bool = False,
        should_fail_closure: bool = False,
        should_fail_manifold: bool = False,
    ):
        """
        Initialize the mock adapter.

        Args:
            should_fail_create: If True, create_face_from_points fails
            should_fail_extrude: If True, extrude_face fails
            should_fail_closure: If True, validate_closed returns False
            should_fail_manifold: If True, validate_manifold returns False
        """
        self._should_fail_create = should_fail_create
        self._should_fail_extrude = should_fail_extrude
        self._should_fail_closure = should_fail_closure
        self._should_fail_manifold = should_fail_manifold

        self._operations: List[OperationRecord] = []
        self._handle_counter = 0

    def create_face_from_points(
        self, points: List[Point3D]
    ) -> MockShellHandle:
        """
        Create a mock face from points.

        Records the operation and returns a mock handle.
        """
        self._handle_counter += 1
        handle_id = f"face_{self._handle_counter}"

        record = OperationRecord(
            operation="create_face_from_points",
            args={"point_count": len(points)},
        )

        if self._should_fail_create:
            record.result = None
            self._operations.append(record)
            raise RuntimeError("Mock: create_face_from_points failed")

        # Calculate bounding box
        if points:
            min_x = min(p.x for p in points)
            max_x = max(p.x for p in points)
            min_y = min(p.y for p in points)
            max_y = max(p.y for p in points)
            min_z = min(p.z for p in points)
            max_z = max(p.z for p in points)

            bbox = (
                Point3D(min_x, min_y, min_z),
                Point3D(max_x, max_y, max_z),
            )
        else:
            bbox = None

        handle = MockShellHandle(
            handle_id=handle_id,
            shell_type="face",
            points=points.copy(),
            bounding_box=bbox,
        )

        record.result = handle
        self._operations.append(record)

        return handle

    def extrude_face(
        self,
        face_handle: MockShellHandle,
        direction: Point3D,
        distance: float,
    ) -> MockShellHandle:
        """
        Extrude a mock face to create a solid.

        Records the operation and returns a mock solid handle.
        """
        self._handle_counter += 1
        handle_id = f"solid_{self._handle_counter}"

        record = OperationRecord(
            operation="extrude_face",
            args={
                "face_handle_id": face_handle.handle_id,
                "direction": (direction.x, direction.y, direction.z),
                "distance": distance,
            },
        )

        if self._should_fail_extrude:
            record.result = None
            self._operations.append(record)
            raise RuntimeError("Mock: extrude_face failed")

        # Update bounding box for extrusion
        bbox = None
        if face_handle.bounding_box:
            min_pt, max_pt = face_handle.bounding_box

            # Extend bounding box in extrusion direction
            new_min = Point3D(
                min_pt.x + min(0, direction.x * distance),
                min_pt.y + min(0, direction.y * distance),
                min_pt.z + min(0, direction.z * distance),
            )
            new_max = Point3D(
                max_pt.x + max(0, direction.x * distance),
                max_pt.y + max(0, direction.y * distance),
                max_pt.z + max(0, direction.z * distance),
            )
            bbox = (new_min, new_max)

        handle = MockShellHandle(
            handle_id=handle_id,
            shell_type="solid",
            points=face_handle.points.copy(),
            is_closed=not self._should_fail_closure,
            is_manifold=not self._should_fail_manifold,
            bounding_box=bbox,
        )

        record.result = handle
        self._operations.append(record)

        return handle

    def validate_closed(self, shell_handle: MockShellHandle) -> bool:
        """Check if shell is closed (mock always returns configured value)."""
        record = OperationRecord(
            operation="validate_closed",
            args={"handle_id": shell_handle.handle_id},
            result=shell_handle.is_closed,
        )
        self._operations.append(record)

        return shell_handle.is_closed

    def validate_manifold(self, shell_handle: MockShellHandle) -> bool:
        """Check if shell is manifold (mock always returns configured value)."""
        record = OperationRecord(
            operation="validate_manifold",
            args={"handle_id": shell_handle.handle_id},
            result=shell_handle.is_manifold,
        )
        self._operations.append(record)

        return shell_handle.is_manifold

    def get_bounding_box(
        self, shell_handle: MockShellHandle
    ) -> Tuple[Point3D, Point3D]:
        """Get bounding box of a shell."""
        record = OperationRecord(
            operation="get_bounding_box",
            args={"handle_id": shell_handle.handle_id},
        )

        if shell_handle.bounding_box:
            record.result = shell_handle.bounding_box
            self._operations.append(record)
            return shell_handle.bounding_box

        # Default bounding box if not set
        default_bbox = (
            Point3D(0, 0, 0),
            Point3D(100, 100, 10),
        )
        record.result = default_bbox
        self._operations.append(record)
        return default_bbox

    def export_step(
        self,
        shell_handle: MockShellHandle,
        header: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """
        Export to STEP format (mock returns placeholder).

        In a real kernel, this would generate valid STEP.
        """
        record = OperationRecord(
            operation="export_step",
            args={
                "handle_id": shell_handle.handle_id,
                "header": header,
            },
        )

        # Return mock STEP content
        step_content = f"""\
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Mock STEP export'),'2;1');
FILE_NAME('{shell_handle.handle_id}.stp','2026-05-14T00:00:00',('MockKernel'),('Luthiers Toolbox'),'MRP-5H Prototype','MockKernelAdapter','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
/* Mock topology data - {shell_handle.shell_type} with {len(shell_handle.points)} base points */
#1=PRODUCT('Mock','Mock Product',$,(#2));
#2=PRODUCT_CONTEXT('',#3,'mechanical');
#3=APPLICATION_CONTEXT('mock topology');
ENDSEC;
END-ISO-10303-21;
"""
        result = step_content.encode("utf-8")
        record.result = f"<{len(result)} bytes>"
        self._operations.append(record)

        return result

    # Test helper methods

    def get_operations(self) -> List[OperationRecord]:
        """Get list of all recorded operations."""
        return self._operations.copy()

    def get_operation_count(self) -> int:
        """Get total number of operations performed."""
        return len(self._operations)

    def get_operations_by_type(self, operation_type: str) -> List[OperationRecord]:
        """Get operations of a specific type."""
        return [op for op in self._operations if op.operation == operation_type]

    def reset(self) -> None:
        """Reset operation history."""
        self._operations.clear()
        self._handle_counter = 0

    def was_operation_called(self, operation_type: str) -> bool:
        """Check if a specific operation was called."""
        return any(op.operation == operation_type for op in self._operations)
