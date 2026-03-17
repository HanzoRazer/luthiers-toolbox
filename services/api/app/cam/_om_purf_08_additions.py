"""
OM-PURF-08: Channel Depth Probe Cycle

G38.2-based probe routine for verifying binding channel depth.
"""

from typing import List, Tuple, Optional


def generate_channel_depth_probe_gcode(
    points: List[Tuple[float, float]],
    expected_depth_mm: float,
    tolerance_mm: float = 0.1,
    probe_feed: float = 50.0,
    safe_z_mm: float = 5.0,
    max_probe_depth_mm: Optional[float] = None,
) -> str:
    """
    Generate G38.2-based probe routine to verify binding channel depth.

    After cutting a binding channel, this routine probes at multiple points
    along the channel to verify consistent depth and report variance.

    G38.2 probes toward the workpiece and alarms if no contact is made
    within the travel limit. This is safer than G31 for depth verification.

    Args:
        points: List of (X, Y) probe positions along binding channel
        expected_depth_mm: Expected channel depth (positive value, e.g., 2.0)
        tolerance_mm: Allowable deviation from expected depth (default 0.1mm)
        probe_feed: Probe feed rate in mm/min (default 50)
        safe_z_mm: Safe Z height for rapid moves (default 5.0)
        max_probe_depth_mm: Maximum probe travel below expected depth
                           (default: expected_depth + 2mm for safety)

    Returns:
        G-code string with probe routine including variance report

    Example:
        >>> points = [(10, 50), (100, 50), (200, 50), (300, 50)]
        >>> gcode = generate_channel_depth_probe_gcode(
        ...     points=points,
        ...     expected_depth_mm=2.0,
        ...     tolerance_mm=0.1,
        ... )

    Notes:
        - G38.2: Probe toward workpiece, alarm if no contact
        - Results stored in #5063 (Z position at contact)
        - Variance calculated as max - min of all probed depths
        - Tolerance check uses #3000 alarm for operator notification
    """
    if max_probe_depth_mm is None:
        max_probe_depth_mm = expected_depth_mm + 2.0

    probe_target_z = -(max_probe_depth_mm)  # Negative Z for downward probe
    retract_z = 2.0  # Local retract above surface

    lines = []

    # Header
    lines.append("(Binding Channel Depth Verification - OM-PURF-08)")
    lines.append(f"(Expected depth: {expected_depth_mm:.3f}mm)")
    lines.append(f"(Tolerance: +/-{tolerance_mm:.3f}mm)")
    lines.append(f"(Probe points: {len(points)})")
    lines.append("")

    # Setup
    lines.append("G21 (Units: mm)")
    lines.append("G90 (Absolute positioning)")
    lines.append("M5 (Spindle off - safety)")
    lines.append(f"G0 Z{safe_z_mm:.3f} (Safe height)")
    lines.append("")

    if not points:
        lines.append("(WARNING: No probe points specified)")
        lines.append("M30 (Program end)")
        return "\n".join(lines)

    # Variable initialization
    lines.append("(Initialize depth storage variables)")
    lines.append("#100 = 0 (Probe count)")
    lines.append("#101 = 0 (Sum of depths)")
    lines.append("#102 = 9999 (Min depth - initialized high)")
    lines.append("#103 = -9999 (Max depth - initialized low)")
    lines.append("#104 = 0 (Current depth)")
    lines.append(f"#105 = {expected_depth_mm:.3f} (Expected depth)")
    lines.append(f"#106 = {tolerance_mm:.3f} (Tolerance)")
    lines.append("#107 = 0 (Out-of-tolerance count)")
    lines.append("")

    # Store individual readings for detailed report
    for i, (x, y) in enumerate(points):
        lines.append(f"#1{10+i} = 0 (Depth at point {i+1})")
    lines.append("")

    # Probe each point
    for i, (x, y) in enumerate(points):
        lines.append(f"(Probe point {i+1}/{len(points)}: X{x:.3f} Y{y:.3f})")

        # Rapid to position
        lines.append(f"G0 X{x:.3f} Y{y:.3f}")
        lines.append(f"G0 Z{retract_z:.3f}")

        # Probe down with G38.2
        lines.append(f"G38.2 Z{probe_target_z:.3f} F{probe_feed:.1f}")

        # Store result
        lines.append("#104 = ABS[#5063] (Absolute depth)")
        lines.append(f"#1{10+i} = #104 (Store reading)")

        # Update statistics
        lines.append("#100 = #100 + 1 (Increment count)")
        lines.append("#101 = #101 + #104 (Add to sum)")
        lines.append("IF [#104 LT #102] THEN #102 = #104 (Update min)")
        lines.append("IF [#104 GT #103] THEN #103 = #104 (Update max)")

        # Check tolerance
        lines.append("IF [ABS[#104 - #105] GT #106] THEN #107 = #107 + 1 (Out of tolerance)")

        # Retract
        lines.append(f"G0 Z{retract_z:.3f}")
        lines.append("")

    # Calculate final statistics
    lines.append("(Calculate final statistics)")
    lines.append("#108 = #101 / #100 (Average depth)")
    lines.append("#109 = #103 - #102 (Variance: max - min)")
    lines.append("")

    # Report results
    lines.append("(=== CHANNEL DEPTH REPORT ===)")
    lines.append("(Points probed: #100)")
    lines.append("(Expected depth: #105)")
    lines.append("(Measured average: #108)")
    lines.append("(Min depth: #102)")
    lines.append("(Max depth: #103)")
    lines.append("(Variance: #109)")
    lines.append("(Out of tolerance: #107)")
    lines.append("")

    # Alert if variance too high or points out of tolerance
    lines.append("(Tolerance check)")
    variance_limit = tolerance_mm * 2
    lines.append(f"IF [#109 GT [{variance_limit:.3f}]] THEN #3000=1 (VARIANCE TOO HIGH: #109 mm)")
    lines.append("IF [#107 GT 0] THEN #3000=2 (OUT OF TOLERANCE: #107 points)")
    lines.append("")

    # Individual readings
    lines.append("(Individual depth readings:)")
    for i in range(len(points)):
        lines.append(f"(  Point {i+1}: #1{10+i} mm)")
    lines.append("")

    # Footer
    lines.append(f"G0 Z{safe_z_mm:.3f} (Final retract)")
    lines.append("M0 (Inspection pause - review results)")
    lines.append("M30 (Program end)")

    return "\n".join(lines)


def generate_channel_probe_points(
    path: List[Tuple[float, float]],
    probe_spacing_mm: float = 50.0,
    offset_from_edge_mm: float = 1.0,
) -> List[Tuple[float, float]]:
    """
    Generate probe points along a binding channel path.

    Distributes probe points evenly along the path at specified spacing.
    Points are offset inward from the path edge to probe the channel floor.

    Args:
        path: Binding channel path (list of XY points)
        probe_spacing_mm: Distance between probe points along path
        offset_from_edge_mm: Offset from path centerline (toward channel center)

    Returns:
        List of (X, Y) probe positions

    Example:
        >>> path = [(0, 0), (100, 0), (100, 100)]
        >>> points = generate_channel_probe_points(path, probe_spacing_mm=30)
        >>> len(points)  # Approximately 200mm / 30mm = 6-7 points
        7
    """
    if len(path) < 2:
        return []

    # Calculate total path length
    total_length = 0.0
    for i in range(1, len(path)):
        dx = path[i][0] - path[i-1][0]
        dy = path[i][1] - path[i-1][1]
        total_length += (dx**2 + dy**2) ** 0.5

    if total_length < probe_spacing_mm:
        # Path too short - just probe at midpoint
        mid_idx = len(path) // 2
        return [path[mid_idx]]

    # Generate evenly spaced points
    probe_points: List[Tuple[float, float]] = []
    num_points = max(2, int(total_length / probe_spacing_mm))
    spacing = total_length / num_points

    # Walk along path and place points
    current_dist = spacing / 2  # Start offset from beginning
    accumulated = 0.0

    for i in range(1, len(path)):
        p1 = path[i-1]
        p2 = path[i]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        seg_len = (dx**2 + dy**2) ** 0.5

        if seg_len < 1e-9:
            continue

        # Normalize direction
        nx, ny = dx / seg_len, dy / seg_len

        # Place points within this segment
        while current_dist <= accumulated + seg_len:
            t = (current_dist - accumulated) / seg_len
            x = p1[0] + t * dx
            y = p1[1] + t * dy

            # Apply offset perpendicular to path (toward inside)
            # Perpendicular: (-ny, nx) for left, (ny, -nx) for right
            # We'll use left perpendicular (assuming CCW path)
            ox = x - ny * offset_from_edge_mm
            oy = y + nx * offset_from_edge_mm

            probe_points.append((ox, oy))
            current_dist += spacing

        accumulated += seg_len

    return probe_points
