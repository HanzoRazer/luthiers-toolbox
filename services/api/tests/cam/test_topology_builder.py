"""
Tests for Topology Builder.

Sprint: MRP-5H
Status: PROTOTYPE
"""

import pytest
from uuid import uuid4

from app.cam.topology_builder import (
    AcousticTopologyBuilder,
    MockKernelAdapter,
    ProfileStack,
    PrototypeTopologyObject,
    ShellDescriptor,
    TopologyBuildError,
    TopologyRequest,
    TopologyResult,
    TopologyRuntimeSupport,
    UnsupportedTopologyError,
)
from app.cam.topology_builder.contracts import (
    ContinuityLevel,
    Point3D,
    ShellType,
    TopologyTier,
)


class TestTopologyRequest:
    """Tests for TopologyRequest validation."""

    def test_valid_request(self):
        """Valid request passes validation."""
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="flat_body",
            thickness_mm=3.0,
        )
        is_valid, errors = request.validate()
        assert is_valid
        assert errors == []

    def test_missing_request_id(self):
        """Missing request_id fails validation."""
        request = TopologyRequest(
            request_id="",
            body_category="flat_body",
        )
        is_valid, errors = request.validate()
        assert not is_valid
        assert "request_id is required" in errors

    def test_missing_body_category(self):
        """Missing body_category fails validation."""
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="",
        )
        is_valid, errors = request.validate()
        assert not is_valid
        assert "body_category is required" in errors

    def test_invalid_thickness(self):
        """Non-positive thickness fails validation."""
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="flat_body",
            thickness_mm=-1.0,
        )
        is_valid, errors = request.validate()
        assert not is_valid
        assert "thickness_mm must be positive" in errors

    def test_request_with_profile_stack(self):
        """Request with valid profile stack passes."""
        profile_stack = ProfileStack()
        profile_stack.add_profile(
            [Point3D(0, 0, 0), Point3D(100, 0, 0), Point3D(100, 100, 0), Point3D(0, 100, 0)],
            z_height=0.0,
        )

        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="flat_body",
            profile_stack=profile_stack,
        )
        is_valid, errors = request.validate()
        assert is_valid


class TestAcousticTopologyBuilder:
    """Tests for AcousticTopologyBuilder."""

    def test_supports_flat_body(self):
        """Flat body is supported for prototype."""
        builder = AcousticTopologyBuilder()
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="flat_body",
        )
        support = builder.supports(request)
        assert support == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE

    def test_supports_acoustic_flat_top(self):
        """Acoustic flat top is supported for prototype."""
        builder = AcousticTopologyBuilder()
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="acoustic_flat_top",
        )
        support = builder.supports(request)
        assert support == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE

    def test_unsupported_archtop(self):
        """Archtop requires research."""
        builder = AcousticTopologyBuilder()
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="archtop",
        )
        support = builder.supports(request)
        assert support == TopologyRuntimeSupport.RESEARCH_REQUIRED

    def test_unsupported_unknown(self):
        """Unknown category is unsupported."""
        builder = AcousticTopologyBuilder()
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="unknown",
        )
        support = builder.supports(request)
        assert support == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME

    def test_build_flat_body_success(self):
        """Build flat body returns success."""
        builder = AcousticTopologyBuilder()
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="flat_body",
            thickness_mm=3.0,
        )
        result = builder.build(request)

        assert result.success
        assert result.topology is not None
        assert result.topology.shell_count == 1
        assert result.topology.shells[0].shell_type == ShellType.FLAT_EXTRUSION

    def test_build_unsupported_fails(self):
        """Build unsupported body category fails cleanly."""
        builder = AcousticTopologyBuilder()
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="archtop",
        )
        result = builder.build(request)

        assert not result.success
        assert result.error_type == "UnsupportedTopologyError"
        assert result.error_classification == "UNSUPPORTED_RUNTIME"

    def test_build_invalid_request_fails(self):
        """Build with invalid request fails."""
        builder = AcousticTopologyBuilder()
        request = TopologyRequest(
            request_id="",
            body_category="flat_body",
        )
        result = builder.build(request)

        assert not result.success
        assert result.error_type == "ValidationError"
        assert "request_id is required" in result.error_message

    def test_build_hollow_body_partial(self):
        """Hollow body has partial support with warning."""
        builder = AcousticTopologyBuilder()
        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="hollow_electric",
        )
        result = builder.build(request)

        assert result.success
        assert result.topology is not None
        assert len(result.topology.warnings) > 0 or len(result.warnings) > 0


class TestAcousticTopologyBuilderWithKernel:
    """Tests for AcousticTopologyBuilder with mock kernel."""

    def test_build_with_mock_kernel(self):
        """Build with mock kernel records operations."""
        kernel = MockKernelAdapter()
        builder = AcousticTopologyBuilder(kernel_adapter=kernel)

        profile_stack = ProfileStack()
        profile_stack.add_profile(
            [
                Point3D(0, 0, 0),
                Point3D(100, 0, 0),
                Point3D(100, 100, 0),
                Point3D(0, 100, 0),
            ],
            z_height=0.0,
        )

        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="flat_body",
            thickness_mm=3.0,
            profile_stack=profile_stack,
        )
        result = builder.build(request)

        assert result.success
        assert kernel.was_operation_called("create_face_from_points")
        assert kernel.was_operation_called("extrude_face")

    def test_kernel_failure_handling(self):
        """Kernel failures are handled gracefully."""
        kernel = MockKernelAdapter(should_fail_create=True)
        builder = AcousticTopologyBuilder(kernel_adapter=kernel)

        profile_stack = ProfileStack()
        profile_stack.add_profile(
            [Point3D(0, 0, 0), Point3D(100, 0, 0), Point3D(100, 100, 0)],
            z_height=0.0,
        )

        request = TopologyRequest(
            request_id=str(uuid4()),
            body_category="flat_body",
            profile_stack=profile_stack,
        )
        result = builder.build(request)

        assert not result.success
        assert result.error_classification == "BLOCKING"


class TestTopologyResult:
    """Tests for TopologyResult."""

    def test_success_result(self):
        """Success result creation."""
        topology = PrototypeTopologyObject(
            request_id="test-123",
            tier=TopologyTier.PROTOTYPE,
        )
        result = TopologyResult.success_result(
            request_id="test-123",
            topology=topology,
        )
        assert result.success
        assert result.topology is not None

    def test_failure_result(self):
        """Failure result creation."""
        result = TopologyResult.failure_result(
            request_id="test-123",
            error_type="TestError",
            error_message="Something failed",
            classification="BLOCKING",
        )
        assert not result.success
        assert result.error_type == "TestError"
        assert result.error_classification == "BLOCKING"

    def test_result_serialization(self):
        """Result can be serialized to dict."""
        topology = PrototypeTopologyObject(
            request_id="test-123",
            tier=TopologyTier.PROTOTYPE,
        )
        result = TopologyResult.success_result(
            request_id="test-123",
            topology=topology,
        )
        data = result.to_dict()

        assert data["request_id"] == "test-123"
        assert data["success"] is True
        assert "topology" in data


class TestPrototypeTopologyObject:
    """Tests for PrototypeTopologyObject."""

    def test_empty_topology_invalid(self):
        """Empty topology (no shells) is not valid."""
        topology = PrototypeTopologyObject(
            request_id="test-123",
            tier=TopologyTier.PROTOTYPE,
        )
        assert not topology.is_valid

    def test_topology_with_closed_shell_valid(self):
        """Topology with closed manifold shell is valid."""
        topology = PrototypeTopologyObject(
            request_id="test-123",
            tier=TopologyTier.PROTOTYPE,
        )
        shell = ShellDescriptor(
            shell_id="shell-1",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=True,
        )
        topology.add_shell(shell)

        assert topology.is_valid
        assert topology.shell_count == 1

    def test_topology_with_open_shell_invalid(self):
        """Topology with open shell is not valid."""
        topology = PrototypeTopologyObject(
            request_id="test-123",
            tier=TopologyTier.PROTOTYPE,
        )
        shell = ShellDescriptor(
            shell_id="shell-1",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=False,
            is_manifold=True,
        )
        topology.add_shell(shell)

        assert not topology.is_valid

    def test_topology_serialization(self):
        """Topology can be serialized to dict."""
        topology = PrototypeTopologyObject(
            request_id="test-123",
            tier=TopologyTier.PROTOTYPE,
        )
        shell = ShellDescriptor(
            shell_id="shell-1",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=True,
        )
        topology.add_shell(shell)

        data = topology.to_dict()
        assert data["request_id"] == "test-123"
        assert data["tier"] == "PROTOTYPE"
        assert len(data["shells"]) == 1
