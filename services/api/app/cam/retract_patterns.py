"""
Advanced retract strategies and tool path optimization.

Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Phase 5 Part 3: N.08 Retract Patterns
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class Point3D:
    """3D point with X, Y, Z coordinates."""
    x: float
    y: float
    z: float


@dataclass
class RetractConfig:
    """Configuration for retract strategies."""
    strategy: str = "safe"  # minimal, safe, incremental, spiral
    safe_z: float = 10.0
    r_plane: float = 2.0
    cutting_depth: float = -15.0
    min_hop: float = 2.0  # Minimum retract height for minimal strategy
    short_move_threshold: float = 20.0  # mm
    long_move_threshold: float = 100.0  # mm


@dataclass
class LeadInConfig:
    """Configuration for lead-in/lead-out patterns."""
    pattern: str = "linear"  # linear, arc, spiral
    distance: float = 3.0  # Lead distance in mm
    angle: float = 45.0  # Entry angle in degrees
    radius: float = 2.0  # Arc radius for arc pattern
    feed_reduction: float = 0.5  # Feed rate multiplier (0.5 = 50%)


def distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate 2D distance between two points."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def distance_3d(p1: Point3D, p2: Point3D) -> float:
    """Calculate 3D distance between two points."""
    return math.sqrt(
        (p2.x - p1.x)**2 + 
        (p2.y - p1.y)**2 + 
        (p2.z - p1.z)**2
    )


def calculate_retract_height(
    current_pos: Tuple[float, float],
    next_pos: Tuple[float, float],
    config: RetractConfig
) -> float:
    """Calculate optimal retract height based on strategy and travel distance."""
    distance = distance_2d(current_pos, next_pos)
    
    if config.strategy == "minimal":
        # Always use minimum hop (r_plane + min_hop)
        return config.r_plane + config.min_hop
    
    elif config.strategy == "safe":
        # Always use full safe_z
        return config.safe_z
    
    elif config.strategy == "incremental":
        # Adaptive based on distance
        if distance < config.short_move_threshold:
            # Short move: minimal retract
            return config.r_plane + config.min_hop
        elif distance < config.long_move_threshold:
            # Medium move: half retract
            return config.safe_z / 2
        else:
            # Long move: full retract
            return config.safe_z
    
    else:
        # Default to safe
        return config.safe_z


def generate_minimal_retract(
    features: List[List[Tuple[float, float, float]]],
    config: RetractConfig,
    feed_rate: float = 300.0
) -> Tuple[List[str], Dict[str, Any]]:
    """Generate G-code with minimal retract strategy."""
    lines = []
    total_retracts = 0
    total_distance = 0.0
    air_distance = 0.0
    
    lines.append("(Minimal Retract Strategy)")
    lines.append(f"G0 Z{config.safe_z:.4f}")  # Initial safe
    
    for feature_idx, feature in enumerate(features):
        if not feature:
            continue
        
        # Move to feature start
        start_x, start_y, start_z = feature[0]
        lines.append(f"G0 X{start_x:.4f} Y{start_y:.4f}")
        lines.append(f"G0 Z{config.r_plane:.4f}")
        lines.append(f"G1 Z{start_z:.4f} F{feed_rate:.1f}")
        
        # Cut feature
        prev_point = feature[0]
        for point in feature[1:]:
            x, y, z = point
            lines.append(f"G1 X{x:.4f} Y{y:.4f} Z{z:.4f} F{feed_rate:.1f}")
            total_distance += distance_3d(
                Point3D(*prev_point), 
                Point3D(*point)
            )
            prev_point = point
        
        # Minimal hop to next feature (if not last)
        if feature_idx < len(features) - 1:
            next_feature = features[feature_idx + 1]
            if next_feature:
                hop_z = config.r_plane + config.min_hop
                lines.append(f"G0 Z{hop_z:.4f}")
                total_retracts += 1
                
                next_x, next_y, _ = next_feature[0]
                curr_x, curr_y, _ = feature[-1]
                air_distance += distance_2d(
                    (curr_x, curr_y), 
                    (next_x, next_y)
                )
    
    # Final retract
    lines.append(f"G0 Z{config.safe_z:.4f}")
    total_retracts += 1
    
    stats = {
        "strategy": "minimal",
        "features": len(features),
        "retracts": total_retracts,
        "cutting_distance_mm": round(total_distance, 2),
        "air_distance_mm": round(air_distance, 2),
        "time_saved_pct": round((1 - total_retracts / (len(features) * 2)) * 100, 1)
    }
    
    return lines, stats


def generate_safe_retract(
    features: List[List[Tuple[float, float, float]]],
    config: RetractConfig,
    feed_rate: float = 300.0
) -> Tuple[List[str], Dict[str, Any]]:
    """Generate G-code with safe retract strategy."""
    lines = []
    total_retracts = 0
    total_distance = 0.0
    air_distance = 0.0
    
    lines.append("(Safe Retract Strategy)")
    lines.append(f"G0 Z{config.safe_z:.4f}")
    
    for feature in features:
        if not feature:
            continue
        
        # Move to feature start
        start_x, start_y, start_z = feature[0]
        lines.append(f"G0 X{start_x:.4f} Y{start_y:.4f}")
        lines.append(f"G0 Z{config.r_plane:.4f}")
        lines.append(f"G1 Z{start_z:.4f} F{feed_rate:.1f}")
        
        # Cut feature
        prev_point = feature[0]
        for point in feature[1:]:
            x, y, z = point
            lines.append(f"G1 X{x:.4f} Y{y:.4f} Z{z:.4f} F{feed_rate:.1f}")
            total_distance += distance_3d(
                Point3D(*prev_point), 
                Point3D(*point)
            )
            prev_point = point
        
        # Full retract after each feature
        lines.append(f"G0 Z{config.safe_z:.4f}")
        total_retracts += 1
        
        # Track air distance
        if feature != features[-1]:
            next_idx = features.index(feature) + 1
            if next_idx < len(features) and features[next_idx]:
                curr_x, curr_y, _ = feature[-1]
                next_x, next_y, _ = features[next_idx][0]
                air_distance += distance_2d(
                    (curr_x, curr_y), 
                    (next_x, next_y)
                )
    
    stats = {
        "strategy": "safe",
        "features": len(features),
        "retracts": total_retracts,
        "cutting_distance_mm": round(total_distance, 2),
        "air_distance_mm": round(air_distance, 2),
        "safety_level": "maximum"
    }
    
    return lines, stats


def generate_incremental_retract(
    features: List[List[Tuple[float, float, float]]],
    config: RetractConfig,
    feed_rate: float = 300.0
) -> Tuple[List[str], Dict[str, Any]]:
    """Generate G-code with incremental retract strategy."""
    lines = []
    total_retracts = 0
    total_distance = 0.0
    air_distance = 0.0
    retract_breakdown = {"minimal": 0, "medium": 0, "full": 0}
    
    lines.append("(Incremental Retract Strategy)")
    lines.append(f"G0 Z{config.safe_z:.4f}")
    
    for feature_idx, feature in enumerate(features):
        if not feature:
            continue
        
        # Move to feature start
        start_x, start_y, start_z = feature[0]
        lines.append(f"G0 X{start_x:.4f} Y{start_y:.4f}")
        lines.append(f"G0 Z{config.r_plane:.4f}")
        lines.append(f"G1 Z{start_z:.4f} F{feed_rate:.1f}")
        
        # Cut feature
        prev_point = feature[0]
        for point in feature[1:]:
            x, y, z = point
            lines.append(f"G1 X{x:.4f} Y{y:.4f} Z{z:.4f} F{feed_rate:.1f}")
            total_distance += distance_3d(
                Point3D(*prev_point), 
                Point3D(*point)
            )
            prev_point = point
        
        # Adaptive retract based on next move distance
        if feature_idx < len(features) - 1:
            next_feature = features[feature_idx + 1]
            if next_feature:
                curr_x, curr_y, _ = feature[-1]
                next_x, next_y, _ = next_feature[0]
                travel_dist = distance_2d(
                    (curr_x, curr_y), 
                    (next_x, next_y)
                )
                
                retract_z = calculate_retract_height(
                    (curr_x, curr_y),
                    (next_x, next_y),
                    config
                )
                
                lines.append(f"G0 Z{retract_z:.4f}")
                total_retracts += 1
                air_distance += travel_dist
                
                # Track retract type
                if retract_z <= config.r_plane + config.min_hop + 1:
                    retract_breakdown["minimal"] += 1
                elif retract_z < config.safe_z - 1:
                    retract_breakdown["medium"] += 1
                else:
                    retract_breakdown["full"] += 1
    
    # Final retract
    lines.append(f"G0 Z{config.safe_z:.4f}")
    total_retracts += 1
    retract_breakdown["full"] += 1
    
    stats = {
        "strategy": "incremental",
        "features": len(features),
        "retracts": total_retracts,
        "cutting_distance_mm": round(total_distance, 2),
        "air_distance_mm": round(air_distance, 2),
        "retract_breakdown": retract_breakdown
    }
    
    return lines, stats


def generate_linear_lead_in(
    start_x: float,
    start_y: float,
    start_z: float,
    entry_x: float,
    entry_y: float,
    config: LeadInConfig,
    feed_rate: float = 300.0
) -> List[str]:
    """Generate linear lead-in pattern."""
    lines = []
    
    # Calculate lead-in start point (back from entry point)
    angle_rad = math.radians(config.angle)
    dx = config.distance * math.cos(angle_rad)
    dy = config.distance * math.sin(angle_rad)
    
    lead_start_x = entry_x - dx
    lead_start_y = entry_y - dy
    
    # Position above lead-in start
    lines.append(f"G0 X{lead_start_x:.4f} Y{lead_start_y:.4f}")
    lines.append(f"G0 Z{start_z + 2:.4f}")  # 2mm above cutting depth
    lines.append(f"G1 Z{start_z:.4f} F{feed_rate:.1f}")
    
    # Lead-in at reduced feed
    lead_feed = feed_rate * config.feed_reduction
    lines.append(f"G1 X{entry_x:.4f} Y{entry_y:.4f} F{lead_feed:.1f}")
    
    return lines


def generate_arc_lead_in(
    start_x: float,
    start_y: float,
    start_z: float,
    entry_x: float,
    entry_y: float,
    config: LeadInConfig,
    feed_rate: float = 300.0
) -> List[str]:
    """Generate arc lead-in pattern."""
    lines = []
    
    # Calculate arc center and start point
    radius = config.radius
    
    # Arc center is at entry point offset by radius
    center_x = entry_x - radius
    center_y = entry_y
    
    # Arc starts 90° before entry (quarter circle)
    arc_start_x = center_x
    arc_start_y = center_y - radius
    
    # Position above arc start
    lines.append(f"G0 X{arc_start_x:.4f} Y{arc_start_y:.4f}")
    lines.append(f"G0 Z{start_z + 2:.4f}")
    lines.append(f"G1 Z{start_z:.4f} F{feed_rate:.1f}")
    
    # Arc lead-in (CW for external approach)
    lead_feed = feed_rate * config.feed_reduction
    i = center_x - arc_start_x
    j = center_y - arc_start_y
    lines.append(f"G2 X{entry_x:.4f} Y{entry_y:.4f} I{i:.4f} J{j:.4f} F{lead_feed:.1f}")
    
    return lines


def optimize_path_order(
    features: List[List[Tuple[float, float, float]]],
    algorithm: str = "nearest_neighbor"
) -> List[List[Tuple[float, float, float]]]:
    """
    Optimize feature order to minimize travel distance.
    
    Args:
        features: List of feature paths
        algorithm: "nearest_neighbor" or "reverse" or "none"
    
    Returns:
        Reordered features
    """
    if algorithm == "none" or not features:
        return features
    
    if algorithm == "reverse":
        return features[::-1]
    
    if algorithm == "nearest_neighbor":
        # Start from origin
        current_pos = (0.0, 0.0)
        ordered = []
        remaining = features.copy()
        
        while remaining:
            # Find nearest feature start point
            min_dist = float('inf')
            nearest_idx = 0
            
            for idx, feature in enumerate(remaining):
                if feature:
                    start_x, start_y, _ = feature[0]
                    dist = distance_2d(current_pos, (start_x, start_y))
                    if dist < min_dist:
                        min_dist = dist
                        nearest_idx = idx
            
            # Add nearest to ordered list
            nearest_feature = remaining.pop(nearest_idx)
            ordered.append(nearest_feature)
            
            # Update current position to end of this feature
            if nearest_feature:
                end_x, end_y, _ = nearest_feature[-1]
                current_pos = (end_x, end_y)
        
        return ordered
    
    return features


def calculate_time_savings(
    strategy: str,
    features_count: int,
    avg_feature_distance: float = 50.0
) -> Dict[str, float]:
    """Estimate time savings for different retract strategies."""
    # Assume:
    # - Rapid Z rate: 500 mm/min
    # - Rapid XY rate: 3000 mm/min
    # - Full retract height: 10mm
    # - Minimal retract: 4mm
    
    z_rapid_rate = 500.0 / 60.0  # mm/s
    xy_rapid_rate = 3000.0 / 60.0  # mm/s
    
    if strategy == "safe":
        # Full retract every time
        z_time = features_count * 2 * (10.0 / z_rapid_rate)  # up + down
        xy_time = features_count * (avg_feature_distance / xy_rapid_rate)
        total_time = z_time + xy_time
        
    elif strategy == "minimal":
        # Minimal retract
        z_time = features_count * 2 * (4.0 / z_rapid_rate)
        xy_time = features_count * (avg_feature_distance / xy_rapid_rate)
        total_time = z_time + xy_time
        
    else:  # incremental
        # Mix of minimal (50%), medium (30%), full (20%)
        z_time = (
            features_count * 0.5 * 2 * (4.0 / z_rapid_rate) +
            features_count * 0.3 * 2 * (7.0 / z_rapid_rate) +
            features_count * 0.2 * 2 * (10.0 / z_rapid_rate)
        )
        xy_time = features_count * (avg_feature_distance / xy_rapid_rate)
        total_time = z_time + xy_time
    
    # Calculate savings vs safe strategy
    safe_time = (
        features_count * 2 * (10.0 / z_rapid_rate) +
        features_count * (avg_feature_distance / xy_rapid_rate)
    )
    
    savings_pct = ((safe_time - total_time) / safe_time) * 100
    
    return {
        "total_time_s": round(total_time, 2),
        "z_time_s": round(z_time, 2),
        "xy_time_s": round(xy_time, 2),
        "savings_pct": round(savings_pct, 1)
    }
