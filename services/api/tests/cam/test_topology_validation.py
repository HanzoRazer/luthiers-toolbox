"""
Tests for Topology Validation Functions.

Sprint: MRP-5H
Status: PROTOTYPE
"""

import pytest

from app.cam.topology_builder import (
    ProfileStack,
    ShellDescriptor,
    TopologyRequest,
    validate_geometry_preservation,
    validate_shell_closure,
    validate_topology_request,
)
from app.cam.topology_builder.contracts import (
    ContinuityLevel,
    ContinuityMetadata,
    Point3D,
    PrototypeTopologyObject,
    ShellType,
    TopologyTier,
)
from app.cam.topology_builder.exceptions import (
    ContinuityValidationError,
    GeometryMutationError,
    ProfileValidationError,
    ShellClosureError,
)
from app.cam.topology_builder.validation import (
    validate_continuity,
    validate_profile_data,
    validate_shell_manifold,
    validate_topology_result,
)


class TestValidateTopologyRequest:
    """Tests for validate_topology_request function."""

    def test_valid_request(self):
        """Valid request passes validation."""
        request = TopologyRequest(
            request_id="test-123",
            body_category="flat_body",
            thickness_mm=3.0,
        )
        is_valid, errors, warnings = validate_topology_request(request)

        assert is_valid
        assert errors == []

    def test_missing_request_id(self):
        """Missing request_id is an error."""
        request = TopologyRequest(
            request_id="",
            body_category="flat_body",
        )
        is_valid, errors, warnings = validate_topology_request(request)

        assert not is_valid
        assert any("request_id" in e for e in errors)

    def test_very_thin_thickness_warning(self):
        """Very thin thickness produces warning."""
        request = TopologyRequest(
            request_id="test-123",
            body_category="flat_body",
            thickness_mm=0.5,
        )
        is_valid, errors, warnings = validate_topology_request(request)

        assert is_valid
        assert any("thin" in w for w in warnings)

    def test_very_thick_thickness_warning(self):
        """Very thick thickness produces warning."""
        request = TopologyRequest(
            request_id="test-123",
            body_category="flat_body",
            thickness_mm=100.0,
        )
        is_valid, errors, warnings = validate_topology_request(request)

        assert is_valid
        assert any("thick" in w for w in warnings)


class TestValidateShellClosure:
    """Tests for validate_shell_closure function."""

    def test_closed_shell_passes(self):
        """Closed shell passes validation."""
        shell = ShellDescriptor(
            shell_id="test",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=True,
        )
        validate_shell_closure(shell)

    def test_open_shell_fails(self):
        """Open shell fails validation."""
        shell = ShellDescriptor(
            shell_id="test",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=False,
            is_manifold=True,
        )
        with pytest.raises(ShellClosureError):
            validate_shell_closure(shell)


class TestValidateShellManifold:
    """Tests for validate_shell_manifold function."""

    def test_manifold_shell_passes(self):
        """Manifold shell passes validation."""
        shell = ShellDescriptor(
            shell_id="test",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=True,
        )
        validate_shell_manifold(shell, TopologyTier.PRODUCTION)

    def test_non_manifold_production_fails(self):
        """Non-manifold in PRODUCTION fails."""
        shell = ShellDescriptor(
            shell_id="test",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=False,
        )
        with pytest.raises(ShellClosureError):
            validate_shell_manifold(shell, TopologyTier.PRODUCTION)

    def test_non_manifold_prototype_passes(self):
        """Non-manifold in PROTOTYPE passes (warning only)."""
        shell = ShellDescriptor(
            shell_id="test",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=False,
        )
        validate_shell_manifold(shell, TopologyTier.PROTOTYPE)


class TestValidateGeometryPreservation:
    """Tests for validate_geometry_preservation function."""

    def test_identical_points_pass(self):
        """Identical points pass validation."""
        original = [Point3D(0, 0, 0), Point3D(100, 0, 0), Point3D(100, 100, 0)]
        output = [Point3D(0, 0, 0), Point3D(100, 0, 0), Point3D(100, 100, 0)]

        validate_geometry_preservation(original, output)

    def test_within_tolerance_pass(self):
        """Points within tolerance pass."""
        original = [Point3D(0, 0, 0), Point3D(100, 0, 0)]
        output = [Point3D(0.0001, 0.0001, 0), Point3D(100.0001, 0, 0)]

        validate_geometry_preservation(original, output)

    def test_drift_beyond_tolerance_fails(self):
        """Points drifting beyond tolerance fail."""
        original = [Point3D(0, 0, 0), Point3D(100, 0, 0)]
        output = [Point3D(0.1, 0.1, 0), Point3D(100, 0, 0)]

        with pytest.raises(GeometryMutationError) as exc_info:
            validate_geometry_preservation(original, output)

        assert exc_info.value.drift_mm is not None
        assert exc_info.value.drift_mm > 0.001

    def test_point_count_mismatch_fails(self):
        """Different point counts fail."""
        original = [Point3D(0, 0, 0), Point3D(100, 0, 0)]
        output = [Point3D(0, 0, 0)]

        with pytest.raises(GeometryMutationError):
            validate_geometry_preservation(original, output)


class TestValidateContinuity:
    """Tests for validate_continuity function."""

    def test_met_target_passes(self):
        """Continuity meeting target passes."""
        shell = ShellDescriptor(
            shell_id="test",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=True,
        )
        shell.continuity.append(
            ContinuityMetadata(
                junction_name="rim_to_top",
                target=ContinuityLevel.G0,
                achieved=ContinuityLevel.G1,
                validated=True,
            )
        )

        warnings = validate_continuity(shell)
        assert warnings == []

    def test_unmet_target_prototype_warning(self):
        """Unmet target in PROTOTYPE produces warning."""
        shell = ShellDescriptor(
            shell_id="test",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=True,
        )
        shell.continuity.append(
            ContinuityMetadata(
                junction_name="rim_to_top",
                target=ContinuityLevel.G1,
                achieved=ContinuityLevel.G0,
                validated=True,
            )
        )

        warnings = validate_continuity(shell, TopologyTier.PROTOTYPE)
        assert len(warnings) > 0
        assert "rim_to_top" in warnings[0]

    def test_unmet_target_production_fails(self):
        """Unmet target in PRODUCTION raises error."""
        shell = ShellDescriptor(
            shell_id="test",
            shell_type=ShellType.FLAT_EXTRUSION,
            component_name="body",
            is_closed=True,
            is_manifold=True,
        )
        shell.continuity.append(
            ContinuityMetadata(
                junction_name="rim_to_top",
                target=ContinuityLevel.G1,
                achieved=ContinuityLevel.G0,
                validated=True,
            )
        )

        with pytest.raises(ContinuityValidationError):
            validate_continuity(shell, TopologyTier.PRODUCTION)


class TestValidateProfileData:
    """Tests for validate_profile_data function."""

    def test_valid_profile_passes(self):
        """Valid profile stack passes."""
        profile_stack = ProfileStack()
        profile_stack.add_profile(
            [Point3D(0, 0, 0), Point3D(100, 0, 0), Point3D(100, 100, 0), Point3D(0, 100, 0)],
            z_height=0.0,
        )

        validate_profile_data(profile_stack)

    def test_insufficient_points_fails(self):
        """Profile with < 3 points fails."""
        profile_stack = ProfileStack()
        profile_stack.add_profile(
            [Point3D(0, 0, 0), Point3D(100, 0, 0)],
            z_height=0.0,
        )

        with pytest.raises(ProfileValidationError):
            validate_profile_data(profile_stack)

    def test_degenerate_profile_fails(self):
        """Degenerate profile (all same point) fails."""
        profile_stack = ProfileStack()
        profile_stack.add_profile(
            [Point3D(0, 0, 0), Point3D(0, 0, 0), Point3D(0, 0, 0)],
            z_height=0.0,
        )

        with pytest.raises(ProfileValidationError) as exc_info:
            validate_profile_data(profile_stack)

        assert exc_info.value.issue == "degenerate"


class TestValidateTopologyResult:
    """Tests for validate_topology_result function."""

    def test_valid_topology_passes(self):
        """Valid topology passes validation."""
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

        is_valid, errors, warnings = validate_topology_result(topology)

        assert is_valid
        assert errors == []

    def test_empty_topology_fails(self):
        """Empty topology (no shells) fails."""
        topology = PrototypeTopologyObject(
            request_id="test-123",
            tier=TopologyTier.PROTOTYPE,
        )

        is_valid, errors, warnings = validate_topology_result(topology)

        assert not is_valid
        assert any("no shells" in e for e in errors)

    def test_open_shell_fails(self):
        """Topology with open shell fails."""
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

        is_valid, errors, warnings = validate_topology_result(topology)

        assert not is_valid


class TestContinuityMetadata:
    """Tests for ContinuityMetadata helper properties."""

    def test_met_target_g0_achieves_g0(self):
        """G0 target met by G0 achieved."""
        meta = ContinuityMetadata(
            junction_name="test",
            target=ContinuityLevel.G0,
            achieved=ContinuityLevel.G0,
        )
        assert meta.met_target

    def test_met_target_g0_exceeds_with_g1(self):
        """G0 target exceeded by G1 achieved."""
        meta = ContinuityMetadata(
            junction_name="test",
            target=ContinuityLevel.G0,
            achieved=ContinuityLevel.G1,
        )
        assert meta.met_target

    def test_unmet_target_g1_with_g0(self):
        """G1 target not met by G0 achieved."""
        meta = ContinuityMetadata(
            junction_name="test",
            target=ContinuityLevel.G1,
            achieved=ContinuityLevel.G0,
        )
        assert not meta.met_target

    def test_unmet_target_none_achieved(self):
        """Target not met when nothing achieved."""
        meta = ContinuityMetadata(
            junction_name="test",
            target=ContinuityLevel.G0,
            achieved=None,
        )
        assert not meta.met_target
