# services/api/app/calculators/binding_geometry.py

"""
Binding Geometry Calculator — Computes binding paths for neck, headstock, and body.

Handles the geometric complexities of binding installation:
- Neck binding with fretboard taper and compound radius
- Headstock binding with tight bend radius constraints
- Miter joint angle computation for corners
- Bend radius validation for material selection

GAP Resolutions:
- BEN-GAP-04: Neck binding geometry (fretboard taper + radius)
- BEN-GAP-05: Headstock binding geometry (tight bend at ~20mm tip)
- BEN-GAP-07: Miter joint geometry computation

References:
- Standard binding widths: 1.5mm (delicate) to 7mm (bold acoustic)
- Celluloid minimum bend radius: ~6mm (brittle below this)
- ABS/plastic minimum bend radius: ~3mm (more flexible)
- Wood veneer minimum bend radius: ~15mm (grain dependent)
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple, Dict, Any

# =============================================================================
# IMPORTS FROM EXTRACTED MODULES
# =============================================================================

from .binding_materials import (
    BindingMaterial,
    MINIMUM_BEND_RADII_MM,
    BINDING_WIDTHS,
    MaterialFeedSettings,
    MATERIAL_FEED_RATES,
    DEFAULT_FEED_SETTINGS,
    get_material_feed_settings,
    PurflingStripProfile,
    PurflingStripSpec,
    PURFLING_STRIP_PATTERNS,
)

from .binding_models import (
    Pt2D,
    Pt3D,
    BindingChannelSpec,
    BINDING_CHANNEL_PRESETS,
    BendRadiusCheck,
    MiterJoint,
    NeckBindingGeometry,
    HeadstockBindingGeometry,
    InstallationMethod,
    BindingStripEstimate,
    DEFAULT_OVERLAP_ALLOWANCE_MM,
    DEFAULT_MITER_WASTE_PER_CORNER_MM,
    DEFAULT_HANDLING_WASTE_PERCENT,
)

from .binding_math import (
    distance_2d,
    distance_3d,
    normalize_2d,
    angle_between_vectors,
    calculate_curvature_radius,
    polyline_length,
    polyline_length_3d,
)


# =============================================================================
# NECK BINDING GEOMETRY
# =============================================================================

def calculate_neck_binding_geometry(
    nut_width_mm: float = 43.0,
    heel_width_mm: float = 56.0,
    fretboard_length_mm: float = 320.0,
    fretboard_radius_mm: Optional[float] = 254.0,  # 10" radius
    compound_radius: Optional[Tuple[float, float]] = None,  # (nut_radius, heel_radius)
    binding_width_mm: float = 2.0,
    binding_thickness_mm: float = 1.5,
    material: BindingMaterial = BindingMaterial.CELLULOID,
    resolution_mm: float = 5.0,  # Point spacing along fretboard
) -> NeckBindingGeometry:
    """
    Calculate neck binding geometry accounting for fretboard taper and radius.

    The neck binding follows the edge of the fretboard, which:
    1. Tapers from nut width to heel width
    2. Curves with the fretboard radius (cylindrical or compound)

    Args:
        nut_width_mm: Width at nut end
        heel_width_mm: Width at heel/body junction
        fretboard_length_mm: Length from nut to end of fretboard
        fretboard_radius_mm: Cylindrical radius (None for flat)
        compound_radius: Tuple of (nut_radius, heel_radius) for compound radius
        binding_width_mm: Width of binding strip
        binding_thickness_mm: Thickness of binding
        material: Binding material for bend radius validation
        resolution_mm: Spacing between computed points

    Returns:
        NeckBindingGeometry with complete path and validation
    """
    warnings = []

    # Calculate taper angle
    width_diff = heel_width_mm - nut_width_mm
    taper_angle_rad = math.atan2(width_diff / 2, fretboard_length_mm)
    taper_angle_deg = math.degrees(taper_angle_rad)

    # Generate points along the fretboard length
    num_points = max(10, int(fretboard_length_mm / resolution_mm) + 1)
    positions = [i * fretboard_length_mm / (num_points - 1) for i in range(num_points)]

    left_points: List[Pt3D] = []
    right_points: List[Pt3D] = []

    for pos in positions:
        # Interpolate width at this position
        t = pos / fretboard_length_mm
        width_at_pos = nut_width_mm + t * (heel_width_mm - nut_width_mm)
        half_width = width_at_pos / 2

        # X position along neck (0 = nut)
        x = pos

        # Y positions (left and right edges)
        y_left = -half_width
        y_right = half_width

        # Z position (height due to fretboard radius)
        if compound_radius is not None:
            # Compound radius: interpolate between nut and heel radii
            nut_r, heel_r = compound_radius
            radius_at_pos = nut_r + t * (heel_r - nut_r)
        elif fretboard_radius_mm is not None:
            radius_at_pos = fretboard_radius_mm
        else:
            radius_at_pos = None

        if radius_at_pos is not None and radius_at_pos > 0:
            # Z = R - sqrt(R² - y²) for cylindrical surface
            # At the edge (y = half_width), the binding sits lower than center
            z_left = radius_at_pos - math.sqrt(max(0, radius_at_pos ** 2 - y_left ** 2))
            z_right = radius_at_pos - math.sqrt(max(0, radius_at_pos ** 2 - y_right ** 2))
        else:
            z_left = 0.0
            z_right = 0.0

        left_points.append((x, y_left, z_left))
        right_points.append((x, y_right, z_right))

    # Calculate total binding length (3D path length)
    total_length = polyline_length_3d(left_points)  # Same for both sides

    # Check bend radii along the path
    bend_checks = []
    min_material_radius = MINIMUM_BEND_RADII_MM.get(material, 10.0)

    # For neck binding, curvature comes from the taper, not sharp corners
    # The taper is gradual, so bend radius is essentially infinite (straight line in XY)
    # However, if compound radius changes rapidly, check that
    if compound_radius is not None:
        nut_r, heel_r = compound_radius
        if abs(nut_r - heel_r) > 100:  # Significant compound change
            warnings.append(
                f"Compound radius changes from {nut_r}mm to {heel_r}mm - "
                "ensure binding can conform to varying cross-section"
            )

    # The primary constraint for neck binding is the taper angle
    if abs(taper_angle_deg) > 5:
        warnings.append(
            f"Fretboard taper angle is {taper_angle_deg:.1f}° - "
            "ensure binding is cut with matching angle at ends"
        )

    return NeckBindingGeometry(
        scale_length_mm=fretboard_length_mm * 2,  # Approximate
        nut_width_mm=nut_width_mm,
        heel_width_mm=heel_width_mm,
        fretboard_length_mm=fretboard_length_mm,
        fretboard_radius_mm=fretboard_radius_mm,
        compound_radius=compound_radius,
        binding_width_mm=binding_width_mm,
        binding_thickness_mm=binding_thickness_mm,
        left_edge_points=left_points,
        right_edge_points=right_points,
        taper_angle_degrees=taper_angle_deg,
        total_length_mm=total_length,
        bend_radius_checks=bend_checks,
        warnings=warnings,
    )


# =============================================================================
# HEADSTOCK BINDING GEOMETRY
# =============================================================================

def calculate_headstock_binding_geometry(
    outline_points: List[Pt2D],
    binding_width_mm: float = 2.0,
    binding_thickness_mm: float = 1.5,
    material: BindingMaterial = BindingMaterial.CELLULOID,
) -> HeadstockBindingGeometry:
    """
    Calculate headstock binding geometry with bend radius validation.

    Headstock binding often has tight curves, especially at the tip.
    This function:
    1. Analyzes the outline for minimum curvature radii
    2. Validates against material bend limits
    3. Identifies miter joint positions at sharp corners

    Args:
        outline_points: Closed polygon of headstock outline (2D)
        binding_width_mm: Width of binding strip
        binding_thickness_mm: Thickness of binding
        material: Binding material for bend radius validation

    Returns:
        HeadstockBindingGeometry with validation and warnings
    """
    if len(outline_points) < 4:
        raise ValueError("Headstock outline requires at least 4 points")

    # Ensure closed polygon
    if outline_points[0] != outline_points[-1]:
        outline_points = outline_points + [outline_points[0]]

    warnings = []
    bend_checks = []
    miter_joints = []

    min_material_radius = MINIMUM_BEND_RADII_MM.get(material, 10.0)
    is_manufacturable = True

    # Analyze curvature at each point
    min_radius = float("inf")
    min_radius_pos = outline_points[0]

    for i in range(1, len(outline_points) - 1):
        p1 = outline_points[i - 1]
        p2 = outline_points[i]
        p3 = outline_points[i + 1]

        radius = calculate_curvature_radius(p1, p2, p3)

        # Track minimum radius
        if radius < min_radius:
            min_radius = radius
            min_radius_pos = p2

        # Create bend check for tight curves
        if radius < min_material_radius * 2:  # Check anything within 2x minimum
            if radius < min_material_radius:
                severity = "critical"
                is_safe = False
                is_manufacturable = False
                recommendation = f"Radius {radius:.1f}mm is below {material.value} minimum ({min_material_radius}mm). Consider miter joint or different material."
            elif radius < min_material_radius * 1.5:
                severity = "warning"
                is_safe = True
                recommendation = f"Radius {radius:.1f}mm is close to {material.value} minimum. Pre-bend or heat may be required."
            else:
                severity = "ok"
                is_safe = True
                recommendation = "Within safe bending limits."

            # Calculate position along path
            path_pos = polyline_length(outline_points[:i + 1])

            bend_checks.append(BendRadiusCheck(
                position_mm=path_pos,
                actual_radius_mm=radius,
                minimum_radius_mm=min_material_radius,
                is_safe=is_safe,
                severity=severity,
                recommendation=recommendation,
            ))

        # Detect sharp corners that need miter joints (typically > 30° direction change)
        v1 = normalize_2d((p2[0] - p1[0], p2[1] - p1[1]))
        v2 = normalize_2d((p3[0] - p2[0], p3[1] - p2[1]))

        if v1 != (0.0, 0.0) and v2 != (0.0, 0.0):
            corner_angle = angle_between_vectors(v1, v2)

            if corner_angle > 30:  # Sharp corner
                miter_angle = corner_angle / 2
                miter_joints.append(MiterJoint(
                    position=p2,
                    angle_degrees=miter_angle,
                    corner_angle_degrees=180 - corner_angle,  # Interior angle
                    piece_1_direction=v1,
                    piece_2_direction=v2,
                    notes=f"Sharp corner ({corner_angle:.1f}°) requires miter joint",
                ))

    # Calculate total binding length
    total_length = polyline_length(outline_points)

    # Generate offset path for routing (simplified - uses original outline)
    # Full implementation would use polygon offset
    binding_path = outline_points.copy()

    # Add summary warnings
    if not is_manufacturable:
        warnings.append(
            f"CRITICAL: Headstock has curves tighter than {min_material_radius}mm - "
            f"{material.value} cannot bend this tight without cracking"
        )
    if len(miter_joints) > 0:
        warnings.append(
            f"Found {len(miter_joints)} sharp corners requiring miter joints"
        )
    if min_radius < 25:
        warnings.append(
            f"Minimum curve radius is {min_radius:.1f}mm at headstock tip - "
            "ensure material can conform"
        )

    return HeadstockBindingGeometry(
        outline_points=outline_points,
        binding_width_mm=binding_width_mm,
        binding_thickness_mm=binding_thickness_mm,
        material=material,
        binding_path=binding_path,
        total_length_mm=total_length,
        minimum_radius_mm=min_radius,
        minimum_radius_position=min_radius_pos,
        bend_radius_checks=bend_checks,
        miter_joints=miter_joints,
        is_manufacturable=is_manufacturable,
        warnings=warnings,
    )


# =============================================================================
# MITER JOINT CALCULATIONS
# =============================================================================

def calculate_miter_angle(
    incoming_direction: Tuple[float, float],
    outgoing_direction: Tuple[float, float],
) -> float:
    """
    Calculate the miter cut angle for a corner joint.

    At a corner, both binding pieces are cut at the miter angle
    so they meet cleanly. The miter angle is half the turn angle.

    Args:
        incoming_direction: Unit vector of incoming binding direction
        outgoing_direction: Unit vector of outgoing binding direction

    Returns:
        Miter cut angle in degrees
    """
    turn_angle = angle_between_vectors(incoming_direction, outgoing_direction)
    return turn_angle / 2


def calculate_miter_joints_for_polygon(
    outline_points: List[Pt2D],
    corner_threshold_degrees: float = 25.0,
) -> List[MiterJoint]:
    """
    Find all corners in a polygon that require miter joints.

    Args:
        outline_points: Closed polygon points
        corner_threshold_degrees: Corners sharper than this need miter joints

    Returns:
        List of MiterJoint specifications
    """
    if len(outline_points) < 3:
        return []

    # Ensure closed
    if outline_points[0] != outline_points[-1]:
        outline_points = outline_points + [outline_points[0]]

    joints = []

    for i in range(1, len(outline_points) - 1):
        p1 = outline_points[i - 1]
        p2 = outline_points[i]
        p3 = outline_points[i + 1]

        v1 = normalize_2d((p2[0] - p1[0], p2[1] - p1[1]))
        v2 = normalize_2d((p3[0] - p2[0], p3[1] - p2[1]))

        if v1 == (0.0, 0.0) or v2 == (0.0, 0.0):
            continue

        turn_angle = angle_between_vectors(v1, v2)

        if turn_angle > corner_threshold_degrees:
            joints.append(MiterJoint(
                position=p2,
                angle_degrees=turn_angle / 2,
                corner_angle_degrees=180 - turn_angle,
                piece_1_direction=v1,
                piece_2_direction=v2,
                notes=f"Corner at {turn_angle:.1f}° turn",
            ))

    return joints


# =============================================================================
# BODY BINDING GEOMETRY
# =============================================================================

def calculate_body_binding_path(
    body_outline: List[Pt2D],
    binding_width_mm: float = 2.5,
    material: BindingMaterial = BindingMaterial.ABS_PLASTIC,
) -> Dict[str, Any]:
    """
    Analyze a body outline for binding installation.

    Guitar bodies typically have gentle curves except at cutaways
    and waist areas where tighter bends occur.

    Args:
        body_outline: Closed polygon of body outline
        binding_width_mm: Width of binding
        material: Binding material

    Returns:
        Dictionary with analysis results
    """
    if len(body_outline) < 10:
        raise ValueError("Body outline requires at least 10 points")

    # Ensure closed
    if body_outline[0] != body_outline[-1]:
        body_outline = body_outline + [body_outline[0]]

    min_material_radius = MINIMUM_BEND_RADII_MM.get(material, 10.0)
    total_length = polyline_length(body_outline)

    # Find tightest curves
    tight_curves = []
    for i in range(1, len(body_outline) - 1):
        p1 = body_outline[i - 1]
        p2 = body_outline[i]
        p3 = body_outline[i + 1]

        radius = calculate_curvature_radius(p1, p2, p3)

        if radius < min_material_radius * 3:  # Notable curves
            path_pos = polyline_length(body_outline[:i + 1])
            tight_curves.append({
                "position_mm": round(path_pos, 2),
                "radius_mm": round(radius, 2),
                "is_safe": radius >= min_material_radius,
                "location": _estimate_body_region(p2, body_outline),
            })

    # Calculate miter joints (usually only at neck pocket area)
    miter_joints = calculate_miter_joints_for_polygon(body_outline, corner_threshold_degrees=45)

    warnings = []
    for curve in tight_curves:
        if not curve["is_safe"]:
            warnings.append(
                f"Tight curve at {curve['location']} ({curve['radius_mm']}mm radius) - "
                f"requires careful bending or miter joint"
            )

    return {
        "total_length_mm": round(total_length, 2),
        "binding_width_mm": binding_width_mm,
        "material": material.value,
        "minimum_safe_radius_mm": min_material_radius,
        "tight_curves": tight_curves,
        "miter_joints": [m.to_dict() for m in miter_joints],
        "warnings": warnings,
        "is_manufacturable": all(c["is_safe"] for c in tight_curves),
    }


def _estimate_body_region(point: Pt2D, outline: List[Pt2D]) -> str:
    """Estimate which region of the body a point is in (heuristic)."""
    # Find bounding box
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width = max_x - min_x
    height = max_y - min_y

    # Normalize position
    rel_x = (point[0] - min_x) / width if width > 0 else 0.5
    rel_y = (point[1] - min_y) / height if height > 0 else 0.5

    # Heuristic region detection
    if rel_y > 0.7:
        if rel_x < 0.3:
            return "lower_bout_bass"
        elif rel_x > 0.7:
            return "lower_bout_treble"
        else:
            return "lower_bout_center"
    elif rel_y > 0.4:
        return "waist"
    else:
        if rel_x < 0.3:
            return "upper_bout_bass"
        elif rel_x > 0.7:
            return "upper_bout_treble_cutaway"
        else:
            return "upper_bout_center"


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_binding_material_for_radius(
    minimum_radius_mm: float,
    preferred_material: BindingMaterial = BindingMaterial.ABS_PLASTIC,
) -> Dict[str, Any]:
    """
    Check which binding materials can handle a given minimum bend radius.

    Args:
        minimum_radius_mm: Tightest curve in the design
        preferred_material: Material you'd like to use

    Returns:
        Dictionary with material compatibility analysis
    """
    compatible = []
    incompatible = []
    preferred_ok = False

    for material, min_radius in MINIMUM_BEND_RADII_MM.items():
        if minimum_radius_mm >= min_radius:
            compatible.append({
                "material": material.value,
                "minimum_bend_radius_mm": min_radius,
                "margin_mm": round(minimum_radius_mm - min_radius, 2),
            })
            if material == preferred_material:
                preferred_ok = True
        else:
            incompatible.append({
                "material": material.value,
                "minimum_bend_radius_mm": min_radius,
                "would_need_mm": round(min_radius - minimum_radius_mm, 2),
            })

    recommendation = ""
    if preferred_ok:
        recommendation = f"{preferred_material.value} is suitable for this design."
    elif compatible:
        recommendation = f"Use {compatible[0]['material']} instead (most flexible compatible option)."
    else:
        recommendation = "No standard binding material can handle this radius. Consider miter joints at tight corners."

    return {
        "minimum_radius_mm": round(minimum_radius_mm, 2),
        "preferred_material": preferred_material.value,
        "preferred_is_compatible": preferred_ok,
        "compatible_materials": compatible,
        "incompatible_materials": incompatible,
        "recommendation": recommendation,
    }


# =============================================================================
# BIND-GAP-04: BINDING STRIP LENGTH CALCULATOR
# =============================================================================


def calculate_binding_strip_length(
    perimeter_mm: float,
    installation_method: InstallationMethod = InstallationMethod.SINGLE_CONTINUOUS,
    num_miter_corners: int = 0,
    num_joints: int = 1,
    include_top: bool = True,
    include_back: bool = True,
    include_sides: bool = False,
    side_depth_mm: Optional[float] = None,
    material: Optional[BindingMaterial] = None,
    strip_width_mm: Optional[float] = None,
    overlap_allowance_mm: float = DEFAULT_OVERLAP_ALLOWANCE_MM,
    handling_waste_percent: float = DEFAULT_HANDLING_WASTE_PERCENT,
) -> BindingStripEstimate:
    """
    Calculate binding strip length for material ordering.

    BIND-GAP-04: Binding strip length calculator

    Accounts for:
    - Perimeter measurement
    - Installation method (continuous, sections, etc.)
    - Overlap allowance at joints
    - Miter waste at corners
    - Handling waste (5% default)
    - Top/back/sides as separate components

    Args:
        perimeter_mm: Body perimeter (from outline measurement)
        installation_method: How binding will be installed
        num_miter_corners: Number of corners requiring miter cuts
        num_joints: Number of butt joints (typically 1 for continuous)
        include_top: Include top edge binding
        include_back: Include back edge binding
        include_sides: Include side strips (acoustic guitars)
        side_depth_mm: Side depth for side strip calculation
        material: Binding material (for notes)
        strip_width_mm: Strip width (for notes)
        overlap_allowance_mm: Allowance per joint for overlap
        handling_waste_percent: Percentage for handling/mistakes

    Returns:
        BindingStripEstimate with lengths and breakdown
    """
    notes: List[str] = []
    sections: List[Dict[str, Any]] = []

    # Base calculations depend on installation method
    if installation_method == InstallationMethod.SINGLE_CONTINUOUS:
        # Single strip wraps entire perimeter
        base_length = perimeter_mm
        num_joints = 1  # One overlap point
        notes.append("Single continuous strip wraps entire perimeter")
        sections.append({
            "name": "full_perimeter",
            "length_mm": round(perimeter_mm, 2),
            "quantity": 1,
        })

    elif installation_method == InstallationMethod.TOP_AND_BACK:
        # Top and back are separate (each is half perimeter approximately)
        half_perimeter = perimeter_mm / 2
        base_length = 0.0

        if include_top:
            sections.append({
                "name": "top_edge",
                "length_mm": round(half_perimeter, 2),
                "quantity": 1,
            })
            base_length += half_perimeter

        if include_back:
            sections.append({
                "name": "back_edge",
                "length_mm": round(half_perimeter, 2),
                "quantity": 1,
            })
            base_length += half_perimeter

        num_joints = len(sections)  # One joint per section
        notes.append("Separate strips for top and back edges")

    elif installation_method == InstallationMethod.TRADITIONAL_ACOUSTIC:
        # Traditional acoustic: top rim, back rim, plus side strips
        half_perimeter = perimeter_mm / 2
        base_length = 0.0

        if include_top:
            sections.append({
                "name": "top_rim",
                "length_mm": round(half_perimeter, 2),
                "quantity": 1,
            })
            base_length += half_perimeter

        if include_back:
            sections.append({
                "name": "back_rim",
                "length_mm": round(half_perimeter, 2),
                "quantity": 1,
            })
            base_length += half_perimeter

        if include_sides and side_depth_mm is not None:
            # Side strips run vertically along body depth
            # Typically 2 side strips (bass and treble)
            side_length = side_depth_mm * 2  # Both edges of side
            sections.append({
                "name": "side_strips",
                "length_mm": round(side_length, 2),
                "quantity": 2,
                "note": f"Side depth {side_depth_mm}mm × 2 sides",
            })
            base_length += side_length * 2  # Two side strips

        num_joints = len(sections)
        notes.append("Traditional acoustic installation with separate rim and side strips")

    elif installation_method == InstallationMethod.SECTIONAL:
        # Multiple sections - caller defines num_joints
        base_length = perimeter_mm
        section_length = perimeter_mm / max(1, num_joints)
        for i in range(num_joints):
            sections.append({
                "name": f"section_{i + 1}",
                "length_mm": round(section_length, 2),
                "quantity": 1,
            })
        notes.append(f"Sectional installation with {num_joints} pieces")

    else:
        # Default to single continuous
        base_length = perimeter_mm
        num_joints = 1

    # Calculate allowances
    miter_waste = num_miter_corners * DEFAULT_MITER_WASTE_PER_CORNER_MM
    overlap_waste = num_joints * overlap_allowance_mm
    handling_waste = base_length * handling_waste_percent

    # Total lengths
    minimum_length = base_length
    recommended_length = base_length + miter_waste + overlap_waste + handling_waste

    # Round up to nearest 50mm for ordering (practical increment)
    order_length = math.ceil(recommended_length / 50) * 50

    # Add material-specific notes
    if material is not None:
        min_bend = MINIMUM_BEND_RADII_MM.get(material, 10.0)
        notes.append(f"{material.value}: min bend radius {min_bend}mm")

    if strip_width_mm is not None:
        notes.append(f"Strip width: {strip_width_mm}mm")

    # Add ordering note
    notes.append(
        f"Order length rounded up to {order_length}mm "
        f"(+{round(order_length - minimum_length, 1)}mm allowance)"
    )

    return BindingStripEstimate(
        perimeter_mm=perimeter_mm,
        installation_method=installation_method.value,
        overlap_allowance_mm=overlap_waste,
        miter_waste_mm=miter_waste,
        handling_waste_mm=handling_waste,
        minimum_length_mm=minimum_length,
        recommended_length_mm=recommended_length,
        order_length_mm=order_length,
        sections=sections,
        material=material.value if material else None,
        strip_width_mm=strip_width_mm,
        notes=notes,
    )


def calculate_binding_strip_from_outline(
    outline_points: List[Pt2D],
    installation_method: InstallationMethod = InstallationMethod.SINGLE_CONTINUOUS,
    material: Optional[BindingMaterial] = None,
    strip_width_mm: float = 2.5,
    include_top: bool = True,
    include_back: bool = True,
    side_depth_mm: Optional[float] = None,
) -> BindingStripEstimate:
    """
    Calculate binding strip length from body outline points.

    Convenience wrapper that:
    1. Computes perimeter from outline
    2. Detects sharp corners for miter count
    3. Calls calculate_binding_strip_length()

    Args:
        outline_points: Body outline as list of (x, y) tuples
        installation_method: How binding will be installed
        material: Binding material
        strip_width_mm: Strip width for reference
        include_top: Include top edge
        include_back: Include back edge
        side_depth_mm: Side depth for acoustic guitars

    Returns:
        BindingStripEstimate
    """
    # Calculate perimeter
    perimeter = polyline_length(outline_points)

    # Count sharp corners (> 45° turn) that would need miter cuts
    num_miter_corners = 0
    if len(outline_points) >= 3:
        # Ensure closed
        pts = outline_points
        if pts[0] != pts[-1]:
            pts = pts + [pts[0]]

        for i in range(1, len(pts) - 1):
            p1 = pts[i - 1]
            p2 = pts[i]
            p3 = pts[i + 1]

            v1 = normalize_2d((p2[0] - p1[0], p2[1] - p1[1]))
            v2 = normalize_2d((p3[0] - p2[0], p3[1] - p2[1]))

            if v1 != (0.0, 0.0) and v2 != (0.0, 0.0):
                turn_angle = angle_between_vectors(v1, v2)
                if turn_angle > 45:
                    num_miter_corners += 1

    return calculate_binding_strip_length(
        perimeter_mm=perimeter,
        installation_method=installation_method,
        num_miter_corners=num_miter_corners,
        include_top=include_top,
        include_back=include_back,
        include_sides=side_depth_mm is not None,
        side_depth_mm=side_depth_mm,
        material=material,
        strip_width_mm=strip_width_mm,
    )
