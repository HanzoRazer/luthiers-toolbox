"""Luthier & Woodworking Calculator - Luthier's ToolBox"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List, Optional
import math
from .scientific_calculator import LTBScientificCalculator

# Import canonical fret math - Fortran Rule: all math in subroutines
from ..instrument_geometry.neck.fret_math import (
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
)


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

class LTBLuthierCalculator(LTBScientificCalculator):
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
        """Calculate radius of circle passing through 3 points."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        
        # Check for collinear points (infinite radius = straight line)
        # Using cross product: (p2-p1) × (p3-p1)
        cross = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
        if abs(cross) < 1e-10:
            return float('inf')  # Points are collinear
        
        # Circle equation: (x-h)² + (y-k)² = r²
        # Using the circumcircle formula
        
        # Intermediate calculations
        a = x1 * (y2 - y3) - y1 * (x2 - x3) + x2 * y3 - x3 * y2
        
        b = (x1**2 + y1**2) * (y3 - y2) + \
            (x2**2 + y2**2) * (y1 - y3) + \
            (x3**2 + y3**2) * (y2 - y1)
        
        c = (x1**2 + y1**2) * (x2 - x3) + \
            (x2**2 + y2**2) * (x3 - x1) + \
            (x3**2 + y3**2) * (x1 - x2)
        
        # Center of circle
        h = -b / (2 * a)
        k = -c / (2 * a)
        
        # Radius
        radius = math.sqrt((x1 - h)**2 + (y1 - k)**2)
        
        self._history.append(f"radius_3pt({p1}, {p2}, {p3}) = {radius:.4f}")
        return round(radius, 4)
    
    def radius_from_chord(self, chord_length: float, height: float) -> float:
        """Calculate radius from chord length and arc height (sagitta)."""
        if height <= 0:
            return float('inf')  # Flat surface
        
        c = chord_length
        h = height
        
        radius = (c**2 / (8 * h)) + (h / 2)
        
        self._history.append(f"radius_chord({c}, {h}) = {radius:.4f}")
        return round(radius, 4)
    
    def sagitta(self, radius: float, chord_length: float) -> float:
        """Calculate arc height (sagitta) from radius and chord."""
        if radius <= 0:
            raise ValueError("Radius must be positive")
        
        r = radius
        c = chord_length
        
        # h = r - sqrt(r² - (c/2)²)
        half_chord = c / 2
        if half_chord > r:
            raise ValueError("Chord length exceeds diameter")
        
        h = r - math.sqrt(r**2 - half_chord**2)
        
        self._history.append(f"sagitta(r={r}, c={c}) = {h:.4f}")
        return round(h, 4)
    
    def compound_radius(self, nut_radius: float, saddle_radius: float,
                        scale_length: float, position: float) -> float:
        """Calculate radius at any position on a compound radius fretboard."""
        # Linear interpolation of radius along scale length
        # Some builders use conical (linear in 1/r), this uses linear in r
        t = position / scale_length
        radius = nut_radius + t * (saddle_radius - nut_radius)
        
        self._history.append(f"compound_r({nut_radius}-{saddle_radius}, pos={position}) = {radius:.4f}")
        return round(radius, 4)
    
    def compound_radius_conical(self, nut_radius: float, saddle_radius: float,
                                 scale_length: float, position: float) -> float:
        """
        Calculate compound radius using conical interpolation.
        
        True conical radius - interpolates 1/r linearly, which creates
        a true cone when the fretboard is unrolled.
        
        This is mathematically more correct for a conical surface.
        """
        # Linear interpolation of 1/r (curvature)
        t = position / scale_length
        curvature_nut = 1 / nut_radius
        curvature_saddle = 1 / saddle_radius
        curvature = curvature_nut + t * (curvature_saddle - curvature_nut)
        radius = 1 / curvature
        
        self._history.append(f"compound_r_conical({nut_radius}-{saddle_radius}, pos={position}) = {radius:.4f}")
        return round(radius, 4)
    
    def arc_length(self, radius: float, chord_length: float) -> float:
        """Calculate arc length along a curved surface."""
        if chord_length >= 2 * radius:
            raise ValueError("Chord exceeds diameter")
        
        # Arc length = r * θ, where θ = 2 * arcsin(c / 2r)
        theta = 2 * math.asin(chord_length / (2 * radius))
        arc = radius * theta
        
        self._history.append(f"arc_length(r={radius}, c={chord_length}) = {arc:.4f}")
        return round(arc, 4)
    
    # =========================================================================
    # FRET CALCULATIONS
    # =========================================================================
    
    def fret_position(self, scale_length: float, fret_number: int,
                      use_rule_of_18: bool = False) -> float:
        """Calculate fret position from nut."""
        if use_rule_of_18:
            # Legacy iterative rule of 18 (not in canonical fret_math)
            divisor = self.RULE_OF_18
            remaining = scale_length
            position = 0
            for _ in range(fret_number):
                fret_distance = remaining / divisor
                position += fret_distance
                remaining -= fret_distance
            return round(position, 4)

        # Delegate to canonical fret_math (convert inches <-> mm)
        scale_mm = scale_length * 25.4
        positions_mm = compute_fret_positions_mm(scale_mm, fret_number)
        position_in = positions_mm[fret_number - 1] / 25.4

        return round(position_in, 4)
    
    def fret_spacing(self, scale_length: float, fret_number: int) -> float:
        """Calculate spacing between fret and previous fret."""
        if fret_number < 1:
            return 0.0

        # Delegate to canonical fret_math (convert inches <-> mm)
        scale_mm = scale_length * 25.4
        spacings_mm = compute_fret_spacing_mm(scale_mm, fret_number)
        spacing_in = spacings_mm[fret_number - 1] / 25.4

        return round(spacing_in, 4)
    
    def fret_table(self, scale_length: float, num_frets: int = 24) -> List[FretPosition]:
        """
        Generate complete fret position table.
        
        Args:
            scale_length: Scale length
            num_frets: Number of frets to calculate
            
        Returns:
            List of FretPosition objects
        """
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
        # Position ratio: p = 1 - 2^(-f/12)
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
            # Convert kg/m to lb/in
            unit_weight = unit_weight * 0.0254 / 0.453592
            scale_length = scale_length / 25.4  # mm to inches
        
        # T = (2Lf)² × μ  [with L in inches, f in Hz, μ in lb/in]
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
        # f = (1/2L) * sqrt(T/μ)
        freq = (1 / (2 * scale_length)) * math.sqrt(tension_lbs / unit_weight)
        return round(freq, 2)
    
    # =========================================================================
    # NECK GEOMETRY
    # =========================================================================
    
    def neck_angle(self, bridge_height: float, fretboard_thickness: float,
                   neck_joint_fret: int, scale_length: float,
                   action_at_12th: float = 0.080) -> float:
        """Calculate neck angle for bolt-on or set neck."""
        # Distance from nut to neck joint
        joint_position = self.fret_position(scale_length, neck_joint_fret)
        
        # Distance from joint to bridge
        joint_to_bridge = scale_length - joint_position
        
        # Height difference needed
        height_at_joint = fretboard_thickness + action_at_12th
        height_difference = bridge_height - height_at_joint
        
        # Angle = arctan(height_diff / horizontal_distance)
        angle_rad = math.atan(height_difference / joint_to_bridge)
        angle_deg = math.degrees(angle_rad)
        
        self._history.append(f"neck_angle = {angle_deg:.3f}°")
        return round(angle_deg, 3)
    
    def action_at_fret(self, fret: int, action_at_12th: float,
                       scale_length: float, relief: float = 0.010) -> float:
        """Estimate string action at any fret."""
        # Simplified model: action increases linearly from nut
        # with relief adding a parabolic component
        
        pos = self.fret_position(scale_length, fret)
        pos_12 = self.fret_position(scale_length, 12)
        
        # Linear component
        linear = action_at_12th * (pos / pos_12)
        
        # Relief component (parabolic, max around 7th-9th fret)
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
        taper = (thick_end - thin_end) / length * 12  # Convert to per foot
        
        self._history.append(f"taper_per_foot = {taper:.4f} in/ft")
        return round(taper, 4)
    
    def taper_jig_offset(self, taper_per_foot: float, 
                         workpiece_length: float) -> float:
        """
        Calculate offset for tapering jig.
        
        Args:
            taper_per_foot: Desired taper (in/ft)
            workpiece_length: Length of workpiece in inches
            
        Returns:
            Offset needed at one end of jig
        """
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
        
        # Assume length in feet if <= 24, else inches
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
        # More practical formula based on geometry
        spacing = (2 * math.pi * radius * kerf_width) / 360 * (360 / (2 * math.pi))
        
        # Simpler approximation that works well in practice
        spacing = kerf_width * radius / 57.3 * 2 * math.pi
        
        # Even simpler practical formula
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


# =============================================================================
# TESTS
# =============================================================================

