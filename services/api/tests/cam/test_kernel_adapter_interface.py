"""
Tests for Kernel Adapter Interface (MRP-5K).

Sprint: MRP-5K
Status: PROTOTYPE

Tests the kernel adapter abstraction layer:
- KernelAdapterInterface protocol compliance
- Adapter isolation (no kernel-native ontology leakage)
- Registry functionality
- Mock adapter behavior
"""

import pytest

from app.cam.topology_builder.kernel_adapters import (
    # Interface
    KernelAdapterInterface,
    BaseKernelAdapter,
    # Data types
    AdapterPoint3D,
    AdapterBoundingBox,
    AdapterGeometryHandle,
    AdapterResult,
    AdapterValidationResult,
    AdapterExportResult,
    # Enums
    AdapterOperationType,
    AdapterErrorCode,
    # Implementations
    MockKernelAdapter,
    # Registry
    KernelAdapterRegistry,
    AdapterDeclaration,
    AdapterCapability,
    AdapterMaturity,
    get_adapter_registry,
    get_adapter,
    get_mock_adapter,
    list_available_adapters,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_adapter():
    """Fresh mock adapter for testing."""
    return MockKernelAdapter()


@pytest.fixture
def square_points():
    """Points forming a square profile."""
    return [
        AdapterPoint3D(0, 0, 0),
        AdapterPoint3D(100, 0, 0),
        AdapterPoint3D(100, 100, 0),
        AdapterPoint3D(0, 100, 0),
        AdapterPoint3D(0, 0, 0),  # Closed
    ]


# =============================================================================
# Protocol Compliance Tests
# =============================================================================


class TestProtocolCompliance:
    """Tests for KernelAdapterInterface protocol compliance."""

    def test_mock_adapter_implements_protocol(self, mock_adapter):
        """MockKernelAdapter should implement KernelAdapterInterface."""
        assert isinstance(mock_adapter, KernelAdapterInterface)

    def test_mock_adapter_has_required_properties(self, mock_adapter):
        """Mock adapter should have required properties."""
        assert mock_adapter.adapter_id == "mock"
        assert mock_adapter.kernel_name == "mock"
        assert mock_adapter.is_available == True

    def test_mock_adapter_has_required_methods(self, mock_adapter):
        """Mock adapter should have all required methods."""
        assert hasattr(mock_adapter, "create_face_from_points")
        assert hasattr(mock_adapter, "extrude_face")
        assert hasattr(mock_adapter, "loft_profiles")
        assert hasattr(mock_adapter, "validate_closed")
        assert hasattr(mock_adapter, "validate_manifold")
        assert hasattr(mock_adapter, "get_bounding_box")
        assert hasattr(mock_adapter, "export_step")


# =============================================================================
# Data Type Tests
# =============================================================================


class TestDataTypes:
    """Tests for kernel-agnostic data types."""

    def test_adapter_point3d_creation(self):
        """AdapterPoint3D should be creatable."""
        point = AdapterPoint3D(1.0, 2.0, 3.0)
        assert point.x == 1.0
        assert point.y == 2.0
        assert point.z == 3.0

    def test_adapter_point3d_tuple_conversion(self):
        """AdapterPoint3D should convert to/from tuple."""
        point = AdapterPoint3D(1.0, 2.0, 3.0)
        assert point.to_tuple() == (1.0, 2.0, 3.0)

        point2 = AdapterPoint3D.from_tuple((4.0, 5.0, 6.0))
        assert point2.x == 4.0
        assert point2.y == 5.0
        assert point2.z == 6.0

    def test_adapter_bounding_box(self):
        """AdapterBoundingBox should work correctly."""
        bbox = AdapterBoundingBox(
            min_point=AdapterPoint3D(0, 0, 0),
            max_point=AdapterPoint3D(100, 200, 50),
        )
        assert bbox.dimensions == (100, 200, 50)

    def test_adapter_geometry_handle_is_opaque(self):
        """AdapterGeometryHandle should be opaque to callers."""
        handle = AdapterGeometryHandle(
            handle_id="test_123",
            geometry_type="solid",
            kernel_ref={"internal": "data"},  # Should not be accessed
        )
        # Callers should only use handle_id and geometry_type
        assert handle.handle_id == "test_123"
        assert handle.geometry_type == "solid"


# =============================================================================
# Mock Adapter Operation Tests
# =============================================================================


class TestMockAdapterOperations:
    """Tests for MockKernelAdapter operations."""

    def test_create_face_success(self, mock_adapter, square_points):
        """create_face_from_points should return success result."""
        result = mock_adapter.create_face_from_points(square_points)

        assert result.success
        assert result.operation == AdapterOperationType.CREATE_FACE
        assert result.handle is not None
        assert result.handle.geometry_type == "face"

    def test_create_face_failure(self, square_points):
        """create_face_from_points should fail when configured."""
        adapter = MockKernelAdapter(should_fail_create=True)
        result = adapter.create_face_from_points(square_points)

        assert not result.success
        assert result.error_code == AdapterErrorCode.OPERATION_FAILED
        assert result.error_message is not None

    def test_extrude_face_success(self, mock_adapter, square_points):
        """extrude_face should return success result."""
        face_result = mock_adapter.create_face_from_points(square_points)
        direction = AdapterPoint3D(0, 0, 1)

        result = mock_adapter.extrude_face(face_result.handle, direction, 10.0)

        assert result.success
        assert result.operation == AdapterOperationType.EXTRUDE
        assert result.handle is not None
        assert result.handle.geometry_type == "solid"

    def test_extrude_face_failure(self, square_points):
        """extrude_face should fail when configured."""
        adapter = MockKernelAdapter(should_fail_extrude=True)
        face_result = adapter.create_face_from_points(square_points)
        direction = AdapterPoint3D(0, 0, 1)

        result = adapter.extrude_face(face_result.handle, direction, 10.0)

        assert not result.success
        assert result.error_code == AdapterErrorCode.OPERATION_FAILED

    def test_loft_profiles_success(self, mock_adapter, square_points):
        """loft_profiles should work with multiple profiles."""
        face1 = mock_adapter.create_face_from_points(square_points)
        face2 = mock_adapter.create_face_from_points(square_points)

        result = mock_adapter.loft_profiles([face1.handle, face2.handle])

        assert result.success
        assert result.operation == AdapterOperationType.LOFT
        assert result.handle.geometry_type == "solid"

    def test_loft_profiles_requires_two(self, mock_adapter, square_points):
        """loft_profiles should require at least 2 profiles."""
        face1 = mock_adapter.create_face_from_points(square_points)

        result = mock_adapter.loft_profiles([face1.handle])

        assert not result.success
        assert result.error_code == AdapterErrorCode.INVALID_INPUT

    def test_validate_closed(self, mock_adapter, square_points):
        """validate_closed should return validation result."""
        face_result = mock_adapter.create_face_from_points(square_points)
        extrude_result = mock_adapter.extrude_face(
            face_result.handle, AdapterPoint3D(0, 0, 1), 10.0
        )

        validation = mock_adapter.validate_closed(extrude_result.handle)

        assert isinstance(validation, AdapterValidationResult)
        assert validation.passed == True
        assert validation.operation == AdapterOperationType.VALIDATE_CLOSED

    def test_validate_closed_fails_when_configured(self, square_points):
        """validate_closed should fail when configured."""
        adapter = MockKernelAdapter(should_fail_closure=True)
        face_result = adapter.create_face_from_points(square_points)
        extrude_result = adapter.extrude_face(
            face_result.handle, AdapterPoint3D(0, 0, 1), 10.0
        )

        validation = adapter.validate_closed(extrude_result.handle)

        assert validation.passed == False

    def test_validate_manifold(self, mock_adapter, square_points):
        """validate_manifold should return validation result."""
        face_result = mock_adapter.create_face_from_points(square_points)
        extrude_result = mock_adapter.extrude_face(
            face_result.handle, AdapterPoint3D(0, 0, 1), 10.0
        )

        validation = mock_adapter.validate_manifold(extrude_result.handle)

        assert isinstance(validation, AdapterValidationResult)
        assert validation.passed == True

    def test_get_bounding_box(self, mock_adapter, square_points):
        """get_bounding_box should return bounding box."""
        face_result = mock_adapter.create_face_from_points(square_points)

        bbox = mock_adapter.get_bounding_box(face_result.handle)

        assert bbox is not None
        assert isinstance(bbox, AdapterBoundingBox)
        assert bbox.min_point.x == 0
        assert bbox.max_point.x == 100

    def test_export_step(self, mock_adapter, square_points):
        """export_step should return STEP content."""
        face_result = mock_adapter.create_face_from_points(square_points)
        extrude_result = mock_adapter.extrude_face(
            face_result.handle, AdapterPoint3D(0, 0, 1), 10.0
        )

        export_result = mock_adapter.export_step(extrude_result.handle)

        assert export_result.success
        assert len(export_result.content) > 0
        content = export_result.content.decode("utf-8")
        assert "ISO-10303-21;" in content

    def test_export_step_failure(self, square_points):
        """export_step should fail when configured."""
        adapter = MockKernelAdapter(should_fail_export=True)
        face_result = adapter.create_face_from_points(square_points)

        export_result = adapter.export_step(face_result.handle)

        assert not export_result.success
        assert export_result.error_code == AdapterErrorCode.EXPORT_FAILED


# =============================================================================
# Operation Recording Tests
# =============================================================================


class TestOperationRecording:
    """Tests for operation recording (test utility)."""

    def test_records_operations(self, mock_adapter, square_points):
        """Mock adapter should record operations."""
        mock_adapter.create_face_from_points(square_points)

        assert mock_adapter.get_operation_count() == 1
        assert mock_adapter.was_operation_called(AdapterOperationType.CREATE_FACE)

    def test_reset_clears_operations(self, mock_adapter, square_points):
        """reset() should clear operation history."""
        mock_adapter.create_face_from_points(square_points)
        assert mock_adapter.get_operation_count() == 1

        mock_adapter.reset()

        assert mock_adapter.get_operation_count() == 0

    def test_get_operations_by_type(self, mock_adapter, square_points):
        """Should filter operations by type."""
        mock_adapter.create_face_from_points(square_points)
        face_result = mock_adapter.create_face_from_points(square_points)
        mock_adapter.extrude_face(face_result.handle, AdapterPoint3D(0, 0, 1), 10.0)

        create_ops = mock_adapter.get_operations_by_type(AdapterOperationType.CREATE_FACE)
        extrude_ops = mock_adapter.get_operations_by_type(AdapterOperationType.EXTRUDE)

        assert len(create_ops) == 2
        assert len(extrude_ops) == 1


# =============================================================================
# Registry Tests
# =============================================================================


class TestAdapterRegistry:
    """Tests for kernel adapter registry."""

    def test_get_registry(self):
        """get_adapter_registry should return registry."""
        registry = get_adapter_registry()

        assert registry is not None
        assert isinstance(registry, KernelAdapterRegistry)

    def test_mock_adapter_registered(self):
        """Mock adapter should be registered by default."""
        registry = get_adapter_registry()
        entry = registry.get("mock")

        assert entry is not None
        assert entry.declaration.adapter_id == "mock"
        assert entry.declaration.maturity == AdapterMaturity.MOCK

    def test_list_adapters(self):
        """list_adapters should return declarations."""
        registry = get_adapter_registry()
        adapters = registry.list_adapters()

        assert len(adapters) >= 1
        ids = [a.adapter_id for a in adapters]
        assert "mock" in ids

    def test_list_available(self):
        """list_available should return available adapters."""
        available = list_available_adapters()

        assert len(available) >= 1
        ids = [a.adapter_id for a in available]
        assert "mock" in ids

    def test_list_by_capability(self):
        """list_by_capability should filter by capability."""
        registry = get_adapter_registry()
        adapters = registry.list_by_capability(AdapterCapability.EXTRUDE)

        assert len(adapters) >= 1
        for adapter in adapters:
            assert adapter.supports(AdapterCapability.EXTRUDE)

    def test_get_adapter_by_id(self):
        """get_adapter should return adapter instance."""
        adapter = get_adapter("mock")

        assert adapter is not None
        assert isinstance(adapter, MockKernelAdapter)

    def test_get_mock_adapter_convenience(self):
        """get_mock_adapter should return configured mock."""
        adapter = get_mock_adapter(should_fail_create=True)

        assert adapter._should_fail_create == True


# =============================================================================
# Adapter Declaration Tests
# =============================================================================


class TestAdapterDeclaration:
    """Tests for AdapterDeclaration."""

    def test_supports_capability(self):
        """supports() should check capability."""
        declaration = AdapterDeclaration(
            adapter_id="test",
            kernel_name="test",
            maturity=AdapterMaturity.EXPERIMENTAL,
            capabilities=[AdapterCapability.CREATE_FACE, AdapterCapability.EXTRUDE],
        )

        assert declaration.supports(AdapterCapability.CREATE_FACE)
        assert declaration.supports(AdapterCapability.EXTRUDE)
        assert not declaration.supports(AdapterCapability.LOFT)


# =============================================================================
# Isolation Tests (No Kernel-Native Ontology Leakage)
# =============================================================================


class TestIsolation:
    """Tests for adapter isolation."""

    def test_result_types_are_kernel_agnostic(self, mock_adapter, square_points):
        """All result types should be kernel-agnostic."""
        result = mock_adapter.create_face_from_points(square_points)

        # Result should be AdapterResult, not kernel-specific
        assert isinstance(result, AdapterResult)
        assert isinstance(result.handle, AdapterGeometryHandle)

        # No kernel-native types should leak
        assert not hasattr(result, "occ_shape")
        assert not hasattr(result, "cadquery_solid")

    def test_validation_results_are_kernel_agnostic(self, mock_adapter, square_points):
        """Validation results should be kernel-agnostic."""
        face_result = mock_adapter.create_face_from_points(square_points)
        validation = mock_adapter.validate_closed(face_result.handle)

        assert isinstance(validation, AdapterValidationResult)
        # Should use our enum, not kernel-specific
        assert validation.operation == AdapterOperationType.VALIDATE_CLOSED

    def test_export_result_is_kernel_agnostic(self, mock_adapter, square_points):
        """Export result should be kernel-agnostic."""
        face_result = mock_adapter.create_face_from_points(square_points)
        export_result = mock_adapter.export_step(face_result.handle)

        assert isinstance(export_result, AdapterExportResult)
        # Content should be bytes, not kernel-specific stream
        assert isinstance(export_result.content, bytes)

    def test_bounding_box_is_kernel_agnostic(self, mock_adapter, square_points):
        """Bounding box should use AdapterPoint3D, not kernel types."""
        face_result = mock_adapter.create_face_from_points(square_points)
        bbox = mock_adapter.get_bounding_box(face_result.handle)

        assert isinstance(bbox, AdapterBoundingBox)
        assert isinstance(bbox.min_point, AdapterPoint3D)
        assert isinstance(bbox.max_point, AdapterPoint3D)
