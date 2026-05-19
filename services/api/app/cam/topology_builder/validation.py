"""
Topology Validation Functions.

Sprint: MRP-5H
Status: PROTOTYPE

Provides validation functions for topology requests and results.
These functions implement the validation rules from
TOPOLOGY_FAILURE_CLASSIFICATION.md.
"""

from typing import Any, Dict, List, Optional, Tuple

from .contracts import (
    ContinuityLevel,
    Point3D,
    ProfileStack,
    PrototypeTopologyObject,
    ShellDescriptor,
    TopologyRequest,
    TopologyTier,
)
from .exceptions import (
    ContinuityValidationError,
    GeometryMutationError,
    ProfileValidationError,
    ShellClosureError,
)


# Tolerance constants
GEOMETRY_TOLERANCE_MM = 0.001  # 1 micron tolerance for geometry preservation
GAP_TOLERANCE_PROTOTYPE_MM = 0.1  # 0.1mm gap tolerance for PROTOTYPE tier
GAP_TOLERANCE_PRODUCTION_MM = 0.01  # 0.01mm gap tolerance for PRODUCTION tier


def validate_topology_request(
    request: TopologyRequest,
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate a topology request before processing.

    Args:
        request: The topology request to validate

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Required fields
    if not request.request_id:
        errors.append("request_id is required")

    if not request.body_category:
        errors.append("body_category is required")

    # Thickness validation
    if request.thickness_mm <= 0:
        errors.append("thickness_mm must be positive")
    elif request.thickness_mm < 1.0:
        warnings.append(f"thickness_mm={request.thickness_mm} is very thin")
    elif request.thickness_mm > 50.0:
        warnings.append(f"thickness_mm={request.thickness_mm} is unusually thick")

    # Profile stack validation
    if request.profile_stack:
        valid, error = request.profile_stack.validate()
        if not valid:
            errors.append(f"Profile stack: {error}")
        else:
            # Additional profile checks
            for i, profile in enumerate(request.profile_stack.profiles):
                if not _is_closed_profile(profile):
                    errors.append(f"Profile {i} is not closed")
                if _has_self_intersection(profile):
                    errors.append(f"Profile {i} has self-intersection")

    # Continuity target validation
    for junction, target in request.continuity_targets.items():
        if not isinstance(target, ContinuityLevel):
            try:
                ContinuityLevel(target)
            except ValueError:
                errors.append(f"Invalid continuity target for {junction}: {target}")

    # Tier-specific validation
    if request.tier == TopologyTier.PRODUCTION:
        # PRODUCTION tier requires more complete semantics
        if not request.cad_semantics:
            warnings.append("PRODUCTION tier without cad_semantics may limit output")

    return len(errors) == 0, errors, warnings


def validate_shell_closure(
    shell: ShellDescriptor,
    tier: TopologyTier = TopologyTier.PROTOTYPE,
) -> None:
    """
    Validate that a shell is properly closed.

    Open shells are BLOCKING errors in both tiers.

    Args:
        shell: The shell to validate
        tier: The runtime tier

    Raises:
        ShellClosureError: If shell is not closed
    """
    if not shell.is_closed:
        raise ShellClosureError(
            message=f"Shell '{shell.component_name}' is not closed",
            open_edge_count=None,  # Would be set by kernel
        )


def validate_shell_manifold(
    shell: ShellDescriptor,
    tier: TopologyTier = TopologyTier.PROTOTYPE,
) -> None:
    """
    Validate that a shell is manifold.

    Non-manifold is MAJOR in PROTOTYPE, BLOCKING in PRODUCTION.

    Args:
        shell: The shell to validate
        tier: The runtime tier

    Raises:
        ShellClosureError: If shell is non-manifold (PRODUCTION only raises)
    """
    if not shell.is_manifold:
        if tier == TopologyTier.PRODUCTION:
            raise ShellClosureError(
                message=f"Shell '{shell.component_name}' is non-manifold",
            )
        # PROTOTYPE: warning only, handled by caller


def validate_geometry_preservation(
    original_points: List[Point3D],
    output_points: List[Point3D],
    tolerance_mm: float = GEOMETRY_TOLERANCE_MM,
) -> None:
    """
    Validate that BOE-approved geometry has not been mutated.

    This is a CRITICAL validation - any drift beyond tolerance
    indicates geometry mutation, which is BLOCKING.

    Args:
        original_points: Original BOE-approved points
        output_points: Points after topology construction
        tolerance_mm: Maximum allowed drift in mm

    Raises:
        GeometryMutationError: If any point has drifted beyond tolerance
    """
    if len(original_points) != len(output_points):
        raise GeometryMutationError(
            message=(
                f"Point count changed: {len(original_points)} -> {len(output_points)}"
            ),
        )

    max_drift = 0.0
    max_drift_index = -1

    for i, (orig, out) in enumerate(zip(original_points, output_points)):
        drift = _point_distance(orig, out)
        if drift > max_drift:
            max_drift = drift
            max_drift_index = i

    if max_drift > tolerance_mm:
        orig = original_points[max_drift_index]
        out = output_points[max_drift_index]
        raise GeometryMutationError(
            message=f"Point {max_drift_index} drifted {max_drift:.6f}mm",
            original_point=[orig.x, orig.y, orig.z],
            output_point=[out.x, out.y, out.z],
            drift_mm=max_drift,
        )


def validate_continuity(
    shell: ShellDescriptor,
    tier: TopologyTier = TopologyTier.PROTOTYPE,
) -> List[str]:
    """
    Validate continuity requirements for a shell.

    PROTOTYPE tier: G0 acceptable, G1 produces warning
    PRODUCTION tier: G1 required, G0 is BLOCKING

    Args:
        shell: The shell with continuity metadata
        tier: The runtime tier

    Returns:
        List of warning messages

    Raises:
        ContinuityValidationError: If continuity requirements not met (PRODUCTION)
    """
    warnings: List[str] = []

    for cont in shell.continuity:
        if not cont.met_target:
            if tier == TopologyTier.PRODUCTION:
                raise ContinuityValidationError(
                    message=(
                        f"Junction '{cont.junction_name}' requires {cont.target.value} "
                        f"but achieved {cont.achieved.value if cont.achieved else 'none'}"
                    ),
                    target_continuity=cont.target.value,
                    achieved_continuity=(
                        cont.achieved.value if cont.achieved else None
                    ),
                    junction_type=cont.junction_name,
                    tier="PRODUCTION",
                )
            else:
                warnings.append(
                    f"Junction '{cont.junction_name}': target {cont.target.value}, "
                    f"achieved {cont.achieved.value if cont.achieved else 'none'}"
                )

    return warnings


def validate_profile_data(
    profile_stack: ProfileStack,
    profile_type: str = "body",
) -> None:
    """
    Validate profile data before topology construction.

    Args:
        profile_stack: The profile stack to validate
        profile_type: Type of profile for error messages

    Raises:
        ProfileValidationError: If profile data is invalid
    """
    # Basic validation
    valid, error = profile_stack.validate()
    if not valid:
        raise ProfileValidationError(
            message=f"Invalid {profile_type} profile: {error}",
            profile_type=profile_type,
            issue=error or "unknown",
            classification="BLOCKING",
        )

    # Check each profile
    for i, profile in enumerate(profile_stack.profiles):
        # Minimum points
        if len(profile) < 3:
            raise ProfileValidationError(
                message=f"Profile {i} has only {len(profile)} points (minimum 3)",
                profile_type=profile_type,
                issue="insufficient_points",
                classification="BLOCKING",
            )

        # Check for degenerate profile (all points same)
        if _is_degenerate_profile(profile):
            raise ProfileValidationError(
                message=f"Profile {i} is degenerate (all points identical)",
                profile_type=profile_type,
                issue="degenerate",
                classification="BLOCKING",
            )

        # Check for near-zero area
        area = _approximate_profile_area(profile)
        if area < 1.0:  # Less than 1 sq mm
            raise ProfileValidationError(
                message=f"Profile {i} has near-zero area ({area:.4f} sq mm)",
                profile_type=profile_type,
                issue="near_zero_area",
                classification="MAJOR",
            )


def validate_topology_result(
    topology: PrototypeTopologyObject,
    tier: TopologyTier = TopologyTier.PROTOTYPE,
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate a completed topology result.

    Args:
        topology: The topology to validate
        tier: The runtime tier

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Must have at least one shell
    if not topology.shells:
        errors.append("Topology has no shells")
        return False, errors, warnings

    # Validate each shell
    for shell in topology.shells:
        try:
            validate_shell_closure(shell, tier)
        except ShellClosureError as e:
            errors.append(e.message)

        try:
            validate_shell_manifold(shell, tier)
        except ShellClosureError as e:
            if tier == TopologyTier.PRODUCTION:
                errors.append(e.message)
            else:
                warnings.append(f"Non-manifold shell: {shell.component_name}")

        # Validate continuity
        try:
            cont_warnings = validate_continuity(shell, tier)
            warnings.extend(cont_warnings)
        except ContinuityValidationError as e:
            errors.append(e.message)

    return len(errors) == 0, errors, warnings


# Helper functions


def _point_distance(p1: Point3D, p2: Point3D) -> float:
    """Calculate Euclidean distance between two points."""
    return (
        (p1.x - p2.x) ** 2
        + (p1.y - p2.y) ** 2
        + (p1.z - p2.z) ** 2
    ) ** 0.5


def _is_closed_profile(profile: List[Point3D]) -> bool:
    """Check if a profile is closed (first point == last point)."""
    if len(profile) < 3:
        return False

    first = profile[0]
    last = profile[-1]

    return _point_distance(first, last) < GEOMETRY_TOLERANCE_MM


def _has_self_intersection(profile: List[Point3D]) -> bool:
    """
    Check if a profile has self-intersection.

    This is a simplified check using line segment intersection.
    A full implementation would use proper geometric algorithms.
    """
    if len(profile) < 4:
        return False

    # For PROTOTYPE, we do a simple O(n^2) check
    # Production would use a sweep line algorithm
    n = len(profile)
    for i in range(n - 1):
        p1 = profile[i]
        p2 = profile[i + 1]

        # Check against non-adjacent segments
        for j in range(i + 2, n - 1):
            if j == i + 1 or (i == 0 and j == n - 2):
                continue  # Skip adjacent segments

            p3 = profile[j]
            p4 = profile[j + 1]

            if _segments_intersect(p1, p2, p3, p4):
                return True

    return False


def _segments_intersect(
    p1: Point3D, p2: Point3D, p3: Point3D, p4: Point3D
) -> bool:
    """Check if two line segments intersect (2D projection)."""
    # Cross product method for 2D line segment intersection
    def cross(o: Point3D, a: Point3D, b: Point3D) -> float:
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True

    return False


def _is_degenerate_profile(profile: List[Point3D]) -> bool:
    """Check if all points in a profile are identical."""
    if len(profile) < 2:
        return True

    first = profile[0]
    for point in profile[1:]:
        if _point_distance(first, point) > GEOMETRY_TOLERANCE_MM:
            return False

    return True


def _approximate_profile_area(profile: List[Point3D]) -> float:
    """
    Approximate the area of a profile using the shoelace formula.

    Uses 2D projection (X, Y).
    """
    if len(profile) < 3:
        return 0.0

    # Shoelace formula for 2D polygon area
    n = len(profile)
    area = 0.0

    for i in range(n):
        j = (i + 1) % n
        area += profile[i].x * profile[j].y
        area -= profile[j].x * profile[i].y

    return abs(area) / 2.0
