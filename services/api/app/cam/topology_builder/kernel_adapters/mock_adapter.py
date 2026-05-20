"""
Mock CAD Kernel Adapter.

Sprint: MRP-5H, MRP-5K
Status: PROTOTYPE

Provides a mock kernel adapter for testing topology construction
without requiring a real CAD kernel. Records operations for
verification in tests.

MRP-5K: Now implements KernelAdapterInterface formally.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .interface import (
    AdapterBoundingBox,
    AdapterErrorCode,
    AdapterExportResult,
    AdapterGeometryHandle,
    AdapterOperationType,
    AdapterPoint3D,
    AdapterResult,
    AdapterValidationResult,
    BaseKernelAdapter,
)


@dataclass
class OperationRecord:
    """Record of a kernel operation for test verification."""

    operation: AdapterOperationType
    args: Dict[str, Any] = field(default_factory=dict)
    result: Any = None


class MockKernelAdapter(BaseKernelAdapter):
    """
    Mock CAD kernel adapter for testing.

    Implements KernelAdapterInterface with configurable behavior.
    Records all operations for test verification.
    """

    def __init__(
        self,
        should_fail_create: bool = False,
        should_fail_extrude: bool = False,
        should_fail_loft: bool = False,
        should_fail_closure: bool = False,
        should_fail_manifold: bool = False,
        should_fail_export: bool = False,
    ):
        """
        Initialize the mock adapter.

        Args:
            should_fail_create: If True, create_face_from_points fails
            should_fail_extrude: If True, extrude_face fails
            should_fail_loft: If True, loft_profiles fails
            should_fail_closure: If True, validate_closed returns False
            should_fail_manifold: If True, validate_manifold returns False
            should_fail_export: If True, export_step fails
        """
        super().__init__(adapter_id="mock", kernel_name="mock")

        self._should_fail_create = should_fail_create
        self._should_fail_extrude = should_fail_extrude
        self._should_fail_loft = should_fail_loft
        self._should_fail_closure = should_fail_closure
        self._should_fail_manifold = should_fail_manifold
        self._should_fail_export = should_fail_export

        self._operations: List[OperationRecord] = []
        self._geometry_store: Dict[str, Dict[str, Any]] = {}

    @property
    def is_available(self) -> bool:
        """Mock kernel is always available."""
        return True

    def create_face_from_points(
        self,
        points: List[AdapterPoint3D],
    ) -> AdapterResult:
        """Create a mock face from points."""
        handle_id = self._next_handle_id("face")

        record = OperationRecord(
            operation=AdapterOperationType.CREATE_FACE,
            args={"point_count": len(points)},
        )

        if self._should_fail_create:
            record.result = "FAILED"
            self._operations.append(record)
            return AdapterResult(
                success=False,
                operation=AdapterOperationType.CREATE_FACE,
                error_code=AdapterErrorCode.OPERATION_FAILED,
                error_message="Mock: create_face_from_points configured to fail",
            )

        # Calculate bounding box
        bbox = None
        if points:
            min_x = min(p.x for p in points)
            max_x = max(p.x for p in points)
            min_y = min(p.y for p in points)
            max_y = max(p.y for p in points)
            min_z = min(p.z for p in points)
            max_z = max(p.z for p in points)

            bbox = AdapterBoundingBox(
                min_point=AdapterPoint3D(min_x, min_y, min_z),
                max_point=AdapterPoint3D(max_x, max_y, max_z),
            )

        handle = AdapterGeometryHandle(
            handle_id=handle_id,
            geometry_type="face",
        )

        # Store geometry data internally
        self._geometry_store[handle_id] = {
            "points": [p.to_tuple() for p in points],
            "bbox": bbox,
            "is_closed": not self._should_fail_closure,
            "is_manifold": not self._should_fail_manifold,
        }

        record.result = handle_id
        self._operations.append(record)

        return AdapterResult(
            success=True,
            operation=AdapterOperationType.CREATE_FACE,
            handle=handle,
        )

    def extrude_face(
        self,
        face_handle: AdapterGeometryHandle,
        direction: AdapterPoint3D,
        distance: float,
    ) -> AdapterResult:
        """Extrude a mock face to create a solid."""
        handle_id = self._next_handle_id("solid")

        record = OperationRecord(
            operation=AdapterOperationType.EXTRUDE,
            args={
                "face_handle_id": face_handle.handle_id,
                "direction": direction.to_tuple(),
                "distance": distance,
            },
        )

        if self._should_fail_extrude:
            record.result = "FAILED"
            self._operations.append(record)
            return AdapterResult(
                success=False,
                operation=AdapterOperationType.EXTRUDE,
                error_code=AdapterErrorCode.OPERATION_FAILED,
                error_message="Mock: extrude_face configured to fail",
            )

        # Get source face data
        face_data = self._geometry_store.get(face_handle.handle_id, {})
        source_bbox = face_data.get("bbox")

        # Update bounding box for extrusion
        bbox = None
        if source_bbox:
            min_pt = source_bbox.min_point
            max_pt = source_bbox.max_point

            new_min = AdapterPoint3D(
                min_pt.x + min(0, direction.x * distance),
                min_pt.y + min(0, direction.y * distance),
                min_pt.z + min(0, direction.z * distance),
            )
            new_max = AdapterPoint3D(
                max_pt.x + max(0, direction.x * distance),
                max_pt.y + max(0, direction.y * distance),
                max_pt.z + max(0, direction.z * distance),
            )
            bbox = AdapterBoundingBox(min_point=new_min, max_point=new_max)

        handle = AdapterGeometryHandle(
            handle_id=handle_id,
            geometry_type="solid",
        )

        self._geometry_store[handle_id] = {
            "source": face_handle.handle_id,
            "bbox": bbox,
            "is_closed": not self._should_fail_closure,
            "is_manifold": not self._should_fail_manifold,
        }

        record.result = handle_id
        self._operations.append(record)

        return AdapterResult(
            success=True,
            operation=AdapterOperationType.EXTRUDE,
            handle=handle,
        )

    def loft_profiles(
        self,
        profile_handles: List[AdapterGeometryHandle],
    ) -> AdapterResult:
        """Loft between multiple profile faces."""
        handle_id = self._next_handle_id("loft")

        record = OperationRecord(
            operation=AdapterOperationType.LOFT,
            args={"profile_count": len(profile_handles)},
        )

        if self._should_fail_loft:
            record.result = "FAILED"
            self._operations.append(record)
            return AdapterResult(
                success=False,
                operation=AdapterOperationType.LOFT,
                error_code=AdapterErrorCode.OPERATION_FAILED,
                error_message="Mock: loft_profiles configured to fail",
            )

        if len(profile_handles) < 2:
            record.result = "FAILED"
            self._operations.append(record)
            return AdapterResult(
                success=False,
                operation=AdapterOperationType.LOFT,
                error_code=AdapterErrorCode.INVALID_INPUT,
                error_message="Loft requires at least 2 profiles",
            )

        handle = AdapterGeometryHandle(
            handle_id=handle_id,
            geometry_type="solid",
        )

        self._geometry_store[handle_id] = {
            "profiles": [h.handle_id for h in profile_handles],
            "is_closed": not self._should_fail_closure,
            "is_manifold": not self._should_fail_manifold,
        }

        record.result = handle_id
        self._operations.append(record)

        return AdapterResult(
            success=True,
            operation=AdapterOperationType.LOFT,
            handle=handle,
        )

    def validate_closed(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> AdapterValidationResult:
        """Check if geometry is closed."""
        geom_data = self._geometry_store.get(geometry_handle.handle_id, {})
        is_closed = geom_data.get("is_closed", True)

        record = OperationRecord(
            operation=AdapterOperationType.VALIDATE_CLOSED,
            args={"handle_id": geometry_handle.handle_id},
            result=is_closed,
        )
        self._operations.append(record)

        return AdapterValidationResult(
            passed=is_closed,
            operation=AdapterOperationType.VALIDATE_CLOSED,
            details={"geometry_type": geometry_handle.geometry_type},
        )

    def validate_manifold(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> AdapterValidationResult:
        """Check if geometry is manifold."""
        geom_data = self._geometry_store.get(geometry_handle.handle_id, {})
        is_manifold = geom_data.get("is_manifold", True)

        record = OperationRecord(
            operation=AdapterOperationType.VALIDATE_MANIFOLD,
            args={"handle_id": geometry_handle.handle_id},
            result=is_manifold,
        )
        self._operations.append(record)

        return AdapterValidationResult(
            passed=is_manifold,
            operation=AdapterOperationType.VALIDATE_MANIFOLD,
            details={"geometry_type": geometry_handle.geometry_type},
        )

    def get_bounding_box(
        self,
        geometry_handle: AdapterGeometryHandle,
    ) -> Optional[AdapterBoundingBox]:
        """Get bounding box of geometry."""
        geom_data = self._geometry_store.get(geometry_handle.handle_id, {})

        record = OperationRecord(
            operation=AdapterOperationType.GET_BOUNDS,
            args={"handle_id": geometry_handle.handle_id},
        )

        bbox = geom_data.get("bbox")
        if bbox:
            record.result = "found"
        else:
            record.result = "not_found"

        self._operations.append(record)
        return bbox

    def export_step(
        self,
        geometry_handle: AdapterGeometryHandle,
        header_metadata: Optional[Dict[str, str]] = None,
    ) -> AdapterExportResult:
        """Export to STEP format."""
        record = OperationRecord(
            operation=AdapterOperationType.EXPORT_STEP,
            args={
                "handle_id": geometry_handle.handle_id,
                "has_header": header_metadata is not None,
            },
        )

        if self._should_fail_export:
            record.result = "FAILED"
            self._operations.append(record)
            return AdapterExportResult(
                success=False,
                error_code=AdapterErrorCode.EXPORT_FAILED,
                error_message="Mock: export_step configured to fail",
            )

        geom_data = self._geometry_store.get(geometry_handle.handle_id, {})

        step_content = f"""\
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Mock STEP export'),'2;1');
FILE_NAME('{geometry_handle.handle_id}.stp','2026-05-19T00:00:00',('MockKernel'),('MRP-5K'),'MockKernelAdapter','mock','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
/* Mock geometry: {geometry_handle.geometry_type} */
#1=PRODUCT('Mock','Mock Product',$,(#2));
#2=PRODUCT_CONTEXT('',#3,'mechanical');
#3=APPLICATION_CONTEXT('mock topology');
ENDSEC;
END-ISO-10303-21;
"""
        content = step_content.encode("utf-8")
        record.result = f"<{len(content)} bytes>"
        self._operations.append(record)

        return AdapterExportResult(
            success=True,
            content=content,
            format_version="STEP_PART21_MOCK",
        )

    # Test helper methods

    def get_operations(self) -> List[OperationRecord]:
        """Get list of all recorded operations."""
        return self._operations.copy()

    def get_operation_count(self) -> int:
        """Get total number of operations performed."""
        return len(self._operations)

    def get_operations_by_type(
        self, operation_type: AdapterOperationType
    ) -> List[OperationRecord]:
        """Get operations of a specific type."""
        return [op for op in self._operations if op.operation == operation_type]

    def reset(self) -> None:
        """Reset operation history and geometry store."""
        self._operations.clear()
        self._geometry_store.clear()
        self._handle_counter = 0

    def was_operation_called(self, operation_type: AdapterOperationType) -> bool:
        """Check if a specific operation was called."""
        return any(op.operation == operation_type for op in self._operations)
