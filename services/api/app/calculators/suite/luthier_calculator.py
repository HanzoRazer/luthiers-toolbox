"""
Luthier & Woodworking Calculator - Luthier's ToolBox

Specialized calculations for guitar building and woodworking.

Luthier Functions:
    Curves & Radius:
        radius_from_3_points()      Classic geometry - find radius from 3 points on arc
        radius_from_chord()         Radius from chord length and height
        compound_radius()           Fretboard compound radius at any position
        arc_length()                Length along curved surface
        
    Frets & Scale:
        fret_position()             Fret distance from nut
        fret_spacing()              Distance between adjacent frets
        scale_length()              Calculate scale length
        compensation()              Saddle compensation estimate
        
    Strings & Tension:
        string_tension()            Tension in pounds/newtons
        pitch_from_tension()        Frequency from physical properties
        
    Neck Geometry:
        neck_angle()                Neck pitch/angle calculation
        action_at_fret()            String height at any fret
        relief_depth()              Neck relief measurement

Woodworking Functions:
    Tapers & Wedges:
        wedge_angle()               Angle from taper dimensions
        taper_per_foot()            TPF from dimensions
        taper_offset()              Offset for tapering jig
        
    Materials:
        board_feet()                Lumber volume calculation
        sheet_goods_yield()         Plywood cut optimization
        wood_movement()             Seasonal expansion estimate
        
    Joinery:
        miter_angle()               Miter for n-sided polygon
        dovetail_angle()            Dovetail slope calculation
        box_joint_spacing()         Finger joint layout
        kerf_bend_spacing()         Kerf cuts for bending

Usage:
    calc = LuthierCalculator()
    
    # Find radius of an archtop curve from 3 measured points
    radius = calc.radius_from_3_points(
        (0, 0), (6, 0.5), (12, 0)
    )  # Returns radius in same units as input

Author: Luthier's ToolBox
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List, Optional
import math
from .scientific_calculator import ScientificCalculator


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FretPosition:
    """Fret position data."""
    fret_number: int
    distance_from_nut: float      # Cumulative distance
    distance_from_previous: float  # Spacing from previous fret
    remaining_to_bridge: float     # Distance to bridge


@dataclass
class CompoundRadiusPoint:
    """Point on a compound radius fretboard."""
    position: float          # Distance from nut
    radius: float            # Radius at this position
    arc_height: float        # Height of arc at centerline


@dataclass
class StringTension:
    """String tension calculation result."""
    tension_lbs: float
    tension_newtons: float
    tension_kg: float
    unit_weight: float       # lb/in or kg/m


# =============================================================================
# LUTHIER CALCULATOR
# =============================================================================

class LuthierCalculator(ScientificCalculator):
    """
    Calculator for luthiers and woodworkers.
    
    Extends ScientificCalculator with specialized functions for
    guitar building, instrument making, and general woodworking.
    """
    
    # Standard scale lengths (inches)
    SCALE_FENDER = 25.5
    SCALE_GIBSON = 24.75
    SCALE_PRS = 25.0
    SCALE_MARTIN = 25.4
    SCALE_CLASSICAL = 25.6  # 650mm
    
    # Fret divisor
    RULE_OF_18 = 18.0           # Traditional approximation
    EQUAL_TEMPERAMENT = 17.817  # Precise 12-TET: 12th root of 2
    
    def __init__(self):
        super().__init__()
        self.fret_divisor = self.EQUAL_TEMPERAMENT  # Default to precise
    
    # =========================================================================
    # CURVE & RADIUS CALCULATIONS
    # =========================================================================
    
    def radius_from_3_points(self, p1: Tuple[float, float], 
                              p2: Tuple[float, float],
                              p3: Tuple[float, float]) -> float:
        """
        Calculate radius of circle passing through 3 points.
        
        Classic luthier measurement: place 3 points on a curve
        (like an archtop or radius gauge) and calculate the radius.
        
        Args:
            p1, p2, p3: Three points as (x, y) tuples
            
        Returns:
            Radius of the circle (same units as input)
            
        Example:
            # Measure archtop curve: center is 0.5" higher than edges
            # Points at x=0, x=6, x=12 inches
            >>> calc.radius_from_3_points((0, 0), (6, 0.5), (12, 0))
            36.25  # inches
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        
        # Check for collinear points (infinite radius = straight line)
        cross = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
        if abs(cross) < 1e-10:
            return float('inf')  # Points are collinear
        
        # Circle equation: (x-h)² + (y-k)² = r²
        a = x1 * (y2 - y3) - y1 * (x2 - x3) + x2 * y3 - x3 * y2
        
        b = (x1**2 + y1**2) * (y3 - y2) + \
            (x2**2 + y2**2) * (y1 - y3) + \
            (x3**2 + y3**2) * (y2 - y1)
        
        c = (x1**2 + y1**2) * (x2 - x3) + \
            (x2**2 + y2**2) * (x3 - x1) + \
            (x3**2 + y3**2) * (x1 - x2)
        
        h = -b / (2 * a)
        k = -c / (2 * a)
        
        radius = math.sqrt((x1 - h)**2 + (y1 - k)**2)
        
        self._history.append(f"radius_3pt({p1}, {p2}, {p3}) = {radius:.4f}")
        return round(radius, 4)
    
    def radius_from_chord(self, chord_length: float, height: float) -> float:
        """
        Calculate radius from chord length and arc height (sagitta).
        
        Useful for measuring fretboard radius with a straightedge:
        measure the gap under the straightedge at the center.
        
        Args:
            chord_length: Length of straightedge/chord
            height: Height of arc at center (gap under straightedge)
            
        Returns:
            Radius
        """
        if height <= 0:
            return float('inf')
        
        c = chord_length
        h = height
        
        radius = (c**2 / (8 * h)) + (h / 2)
        
        self._history.append(f"radius_chord({c}, {h}) = {radius:.4f}")
        return round(radius, 4)
    
    def sagitta(self, radius: float, chord_length: float) -> float:
        """
        Calculate arc height (sagitta) from radius and chord.
        
        Args:
            radius: Fretboard/surface radius
            chord_length: Width being measured
            
        Returns:
            Height of arc at center (sagitta)
        """
        if radius <= 0:
            raise ValueError("Radius must be positive")
        
        r = radius
        c = chord_length
        
        half_chord = c / 2
        if half_chord > r:
            raise ValueError("Chord length exceeds diameter")
        
        h = r - math.sqrt(r**2 - half_chord**2)
        
        self._history.append(f"sagitta(r={r}, c={c}) = {h:.4f}")
        return round(h, 4)
    
    def compound_radius(self, nut_radius: float, saddle_radius: float,
                        scale_length: float, position: float) -> float:
        """
        Calculate radius at any position on a compound radius fretboard.
        
        Args:
            nut_radius: Radius at nut
            saddle_radius: Radius at saddle/bridge
            scale_length: Scale length
            position: Distance from nut
            
        Returns:
            Radius at specified position
        """
        t = position / scale_length
        radius = nut_radius + t * (saddle_radius - nut_radius)
        
        self._history.append(f"compound_r({nut_radius}-{saddle_radius}, pos={position}) = {radius:.4f}")
        return round(radius, 4)
    
    def compound_radius_conical(self, nut_radius: float, saddle_radius: float,
                                 scale_length: float, position: float) -> float:
        """Calculate compound radius using conical interpolation."""
        t = position / scale_length
        curvature_nut = 1 / nut_radius
        curvature_saddle = 1 / saddle_radius
        curvature = curvature_nut + t * (curvature_saddle - curvature_nut)
        radius = 1 / curvature
        
        self._history.append(f"compound_r_conical({nut_radius}-{saddle_radius}, pos={position}) = {radius:.4f}")
        return round(radius, 4)
    
    def arc_length(self, radius: float, chord_length: float) -> float:
        """
        Calculate arc length along a curved surface.
        
        Args:
            radius: Surface radius
            chord_length: Straight-line width
            
        Returns:
            Length along the curved surface
        """
        if chord_length >= 2 * radius:
            raise ValueError("Chord exceeds diameter")
        
        theta = 2 * math.asin(chord_length / (2 * radius))
        arc = radius * theta
        
        self._history.append(f"arc_length(r={radius}, c={chord_length}) = {arc:.4f}")
        return round(arc, 4)
    
    # =========================================================================
    # FRET CALCULATIONS
    # =========================================================================
    
    def fret_position(self, scale_length: float, fret_number: int,
                      use_rule_of_18: bool = False) -> float:
        """
        Calculate fret position from nut.
        
        Args:
            scale_length: Scale length (nut to saddle)
            fret_number: Fret number (1 = first fret)
            use_rule_of_18: Use traditional approximation vs precise 12-TET
            
        Returns:
            Distance from nut to fret
        """
        divisor = self.RULE_OF_18 if use_rule_of_18 else self.EQUAL_TEMPERAMENT
        
        if not use_rule_of_18:
            position = scale_length * (1 - math.pow(2, -fret_number / 12))
        else:
            remaining = scale_length
            position = 0
            for _ in range(fret_number):
                fret_distance = remaining / divisor
                position += fret_distance
                remaining -= fret_distance
        
        return round(position, 4)
    
    def fret_spacing(self, scale_length: float, fret_number: int) -> float:
        """Calculate spacing between fret and previous fret."""
        if fret_number < 1:
            return 0.0
        
        current = self.fret_position(scale_length, fret_number)
        previous = self.fret_position(scale_length, fret_number - 1) if fret_number > 1 else 0
        
        return round(current - previous, 4)
    
    def fret_table(self, scale_length: float, num_frets: int = 24) -> List[FretPosition]:
        """Generate complete fret position table."""
        positions = []
        
        for fret in range(1, num_frets + 1):
            distance = self.fret_position(scale_length, fret)
            spacing = self.fret_spacing(scale_length, fret)
            remaining = scale_length - distance
            
            positions.append(FretPosition(
                fret_number=fret,
                distance_from_nut=round(distance, 4),
                distance_from_previous=round(spacing, 4),
                remaining_to_bridge=round(remaining, 4)
            ))
        
        return positions
    
    def scale_length_from_frets(self, fret1_to_fret2: float, 
                                 fret1: int, fret2: int) -> float:
        """Calculate scale length from distance between two frets."""
        ratio1 = 1 - math.pow(2, -fret1 / 12)
        ratio2 = 1 - math.pow(2, -fret2 / 12)
        
        scale = fret1_to_fret2 / (ratio2 - ratio1)
        
        return round(scale, 4)
    
    # =========================================================================
    # STRING TENSION
    # =========================================================================
    
    def string_tension(self, scale_length: float, frequency: float,
                       unit_weight: float, unit_weight_metric: bool = False) -> StringTension:
        """Calculate string tension."""
        if unit_weight_metric:
            unit_weight = unit_weight * 0.0254 / 0.453592
            scale_length = scale_length / 25.4
        
        tension_lbs = (2 * scale_length * frequency) ** 2 * unit_weight
        
        return StringTension(
            tension_lbs=round(tension_lbs, 2),
            tension_newtons=round(tension_lbs * 4.44822, 2),
            tension_kg=round(tension_lbs * 0.453592, 2),
            unit_weight=unit_weight
        )
    
    def frequency_from_tension(self, scale_length: float, tension_lbs: float,
                                unit_weight: float) -> float:
        """Calculate frequency from string properties."""
        freq = (1 / (2 * scale_length)) * math.sqrt(tension_lbs / unit_weight)
        return round(freq, 2)
    
    # =========================================================================
    # NECK GEOMETRY
    # =========================================================================
    
    def neck_angle(self, bridge_height: float, fretboard_thickness: float,
                   neck_joint_fret: int, scale_length: float,
                   action_at_12th: float = 0.080) -> float:
        """Calculate neck angle for bolt-on or set neck."""
        joint_position = self.fret_position(scale_length, neck_joint_fret)
        joint_to_bridge = scale_length - joint_position
        height_at_joint = fretboard_thickness + action_at_12th
        height_difference = bridge_height - height_at_joint
        
        angle_rad = math.atan(height_difference / joint_to_bridge)
        angle_deg = math.degrees(angle_rad)
        
        self._history.append(f"neck_angle = {angle_deg:.3f}°")
        return round(angle_deg, 3)
    
    def action_at_fret(self, fret: int, action_at_12th: float,
                       scale_length: float, relief: float = 0.010) -> float:
        """Estimate string action at any fret."""
        pos = self.fret_position(scale_length, fret)
        pos_12 = self.fret_position(scale_length, 12)
        
        linear = action_at_12th * (pos / pos_12)
        
        relief_center = self.fret_position(scale_length, 8)
        relief_factor = 1 - ((pos - relief_center) / relief_center) ** 2
        relief_component = relief * max(0, relief_factor)
        
        return round(linear + relief_component, 4)
    
    # =========================================================================
    # WEDGE & TAPER CALCULATIONS
    # =========================================================================
    
    def wedge_angle(self, length: float, thick_end: float, thin_end: float) -> float:
        """Calculate wedge angle from dimensions."""
        if length <= 0:
            raise ValueError("Length must be positive")
        
        difference = thick_end - thin_end
        angle_rad = math.atan(difference / length)
        angle_deg = math.degrees(angle_rad)
        
        self._history.append(f"wedge_angle({length}, {thick_end}, {thin_end}) = {angle_deg:.4f}°")
        return round(angle_deg, 4)
    
    def wedge_thickness(self, length: float, thick_end: float, 
                        angle_deg: float, position: float) -> float:
        """Calculate thickness at any point along a wedge."""
        taper_per_unit = math.tan(math.radians(angle_deg))
        thickness = thick_end - (taper_per_unit * position)
        
        return round(thickness, 4)
    
    def taper_per_foot(self, thick_end: float, thin_end: float, 
                       length: float) -> float:
        """Calculate taper in inches per foot."""
        taper = (thick_end - thin_end) / length * 12
        
        self._history.append(f"taper_per_foot = {taper:.4f} in/ft")
        return round(taper, 4)
    
    def taper_jig_offset(self, taper_per_foot: float, 
                         workpiece_length: float) -> float:
        """Calculate offset for tapering jig."""
        offset = (taper_per_foot / 12) * workpiece_length
        return round(offset, 4)
    
    # =========================================================================
    # WOODWORKING CALCULATIONS
    # =========================================================================
    
    def board_feet(self, thickness: float, width: float, length: float,
                   quarters: bool = False) -> float:
        """Calculate board feet."""
        if quarters:
            thickness = thickness / 4
        
        if length > 24:
            length_feet = length / 12
        else:
            length_feet = length
        
        bf = (thickness * width * length_feet) / 12
        
        self._history.append(f"board_feet = {bf:.2f}")
        return round(bf, 2)
    
    def kerf_bend_spacing(self, radius: float, material_thickness: float,
                          kerf_width: float = 0.125) -> float:
        """Calculate kerf spacing for bent laminations."""
        spacing = math.sqrt(2 * radius * kerf_width)
        
        self._history.append(f"kerf_spacing(r={radius}, t={material_thickness}) = {spacing:.4f}")
        return round(spacing, 4)
    
    def miter_angle(self, num_sides: int) -> float:
        """Calculate miter angle for regular polygon."""
        if num_sides < 3:
            raise ValueError("Polygon must have at least 3 sides")
        
        angle = 180 / num_sides
        
        return round(angle, 4)
    
    def dovetail_angle(self, ratio: str = "1:8") -> float:
        """Calculate dovetail angle from ratio."""
        if ':' in str(ratio):
            parts = str(ratio).split(':')
            rise = float(parts[0])
            run = float(parts[1])
        else:
            rise = 1
            run = float(ratio)
        
        angle = math.degrees(math.atan(rise / run))
        
        self._history.append(f"dovetail({ratio}) = {angle:.2f}°")
        return round(angle, 2)
    
    def wood_movement(self, width: float, mc_change: float,
                      tangential_coef: float = 0.00369) -> float:
        """Estimate wood movement due to moisture change."""
        movement = width * mc_change * tangential_coef
        
        return round(movement, 4)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("Testing luthier calculator...")
        calc = LuthierCalculator()
        
        # Test fret positions
        print(f"12th fret at 25.5\" scale: {calc.fret_position(25.5, 12)}\"")
        
        # Test radius from 3 points
        r = calc.radius_from_3_points((0, 0), (6, 0.5), (12, 0))
        print(f"Archtop radius (12\" wide, 0.5\" rise): {r}\"")
        
        # Test compound radius
        r = calc.compound_radius(9.5, 14.0, 25.5, 12.75)
        print(f"Compound radius at 12th fret: {r}\"")
