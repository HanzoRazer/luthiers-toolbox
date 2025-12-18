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
from scientific_calculator import ScientificCalculator


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
        """
        Calculate radius from chord length and arc height (sagitta).
        
        Useful for measuring fretboard radius with a straightedge:
        measure the gap under the straightedge at the center.
        
        Args:
            chord_length: Length of straightedge/chord (e.g., fretboard width)
            height: Height of arc at center (gap under straightedge)
            
        Returns:
            Radius
            
        Formula:
            r = (c²/8h) + (h/2)
            where c = chord length, h = height (sagitta)
            
        Example:
            # 2" wide fretboard, 0.028" gap = ~9.5" radius
            >>> calc.radius_from_chord(2.0, 0.028)
            17.87
        """
        if height <= 0:
            return float('inf')  # Flat surface
        
        c = chord_length
        h = height
        
        radius = (c**2 / (8 * h)) + (h / 2)
        
        self._history.append(f"radius_chord({c}, {h}) = {radius:.4f}")
        return round(radius, 4)
    
    def sagitta(self, radius: float, chord_length: float) -> float:
        """
        Calculate arc height (sagitta) from radius and chord.
        
        Inverse of radius_from_chord - useful for:
        - Setting up radius sanding blocks
        - Checking fretboard radius with feeler gauges
        
        Args:
            radius: Fretboard/surface radius
            chord_length: Width being measured
            
        Returns:
            Height of arc at center (sagitta)
            
        Example:
            # 9.5" radius, 2" wide fretboard
            >>> calc.sagitta(9.5, 2.0)
            0.053  # inches gap at center
        """
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
        """
        Calculate radius at any position on a compound radius fretboard.
        
        Compound radius fretboards transition from a tighter radius at the
        nut (easier chording) to a flatter radius at the bridge (easier bending).
        
        Args:
            nut_radius: Radius at nut (e.g., 9.5")
            saddle_radius: Radius at saddle/bridge (e.g., 14")
            scale_length: Scale length
            position: Distance from nut
            
        Returns:
            Radius at specified position
            
        Example:
            # 9.5" to 14" compound, 25.5" scale, at 12th fret
            >>> calc.compound_radius(9.5, 14, 25.5, 12.75)
            11.75  # inches
        """
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
        """
        Calculate arc length along a curved surface.
        
        Useful for:
        - Cutting fret wire to length
        - Binding strips for curved surfaces
        - Archtop carving dimensions
        
        Args:
            radius: Surface radius
            chord_length: Straight-line width
            
        Returns:
            Length along the curved surface
        """
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
        """
        Calculate fret position from nut.
        
        Args:
            scale_length: Scale length (nut to saddle)
            fret_number: Fret number (1 = first fret)
            use_rule_of_18: Use traditional approximation vs precise 12-TET
            
        Returns:
            Distance from nut to fret
            
        Formula:
            position = scale_length * (1 - (1 / 2^(fret/12)))
            
        Example:
            >>> calc.fret_position(25.5, 12)
            12.75  # 12th fret is exactly half scale length
        """
        divisor = self.RULE_OF_18 if use_rule_of_18 else self.EQUAL_TEMPERAMENT
        
        # Precise formula: position = scale * (1 - 2^(-fret/12))
        if not use_rule_of_18:
            position = scale_length * (1 - math.pow(2, -fret_number / 12))
        else:
            # Iterative rule of 18
            remaining = scale_length
            position = 0
            for _ in range(fret_number):
                fret_distance = remaining / divisor
                position += fret_distance
                remaining -= fret_distance
        
        return round(position, 4)
    
    def fret_spacing(self, scale_length: float, fret_number: int) -> float:
        """
        Calculate spacing between fret and previous fret.
        
        Args:
            scale_length: Scale length
            fret_number: Fret number (1 = nut to first fret)
            
        Returns:
            Distance from previous fret (or nut if fret 1)
        """
        if fret_number < 1:
            return 0.0
        
        current = self.fret_position(scale_length, fret_number)
        previous = self.fret_position(scale_length, fret_number - 1) if fret_number > 1 else 0
        
        return round(current - previous, 4)
    
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
        """
        Calculate scale length from distance between two frets.
        
        Useful for measuring unknown instruments.
        
        Args:
            fret1_to_fret2: Measured distance between frets
            fret1: First fret number
            fret2: Second fret number
            
        Returns:
            Calculated scale length
        """
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
        """
        Calculate string tension.
        
        Args:
            scale_length: Vibrating length in inches (or mm if metric)
            frequency: Target frequency in Hz
            unit_weight: String unit weight (lb/in or kg/m)
            unit_weight_metric: True if unit_weight is in kg/m
            
        Returns:
            StringTension with tension in various units
            
        Formula:
            T = (2 * L * f)² * μ
            where L = length, f = frequency, μ = unit weight
            
        Example:
            # Standard E2 (82.41 Hz), 25.5" scale, .046 string
            >>> calc.string_tension(25.5, 82.41, 0.00017436)
            StringTension(tension_lbs=17.5, ...)
        """
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
        """
        Calculate frequency from string properties.
        
        Args:
            scale_length: Vibrating length in inches
            tension_lbs: Tension in pounds
            unit_weight: String unit weight (lb/in)
            
        Returns:
            Frequency in Hz
        """
        # f = (1/2L) * sqrt(T/μ)
        freq = (1 / (2 * scale_length)) * math.sqrt(tension_lbs / unit_weight)
        return round(freq, 2)
    
    # =========================================================================
    # NECK GEOMETRY
    # =========================================================================
    
    def neck_angle(self, bridge_height: float, fretboard_thickness: float,
                   neck_joint_fret: int, scale_length: float,
                   action_at_12th: float = 0.080) -> float:
        """
        Calculate neck angle for bolt-on or set neck.
        
        Args:
            bridge_height: Height of bridge/saddle above body
            fretboard_thickness: Fretboard thickness at neck joint
            neck_joint_fret: Fret number at neck joint (e.g., 16)
            scale_length: Scale length
            action_at_12th: Desired action at 12th fret
            
        Returns:
            Neck angle in degrees (positive = back angle)
        """
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
        """
        Estimate string action at any fret.
        
        Args:
            fret: Fret number
            action_at_12th: Measured action at 12th fret
            scale_length: Scale length  
            relief: Neck relief (bow) at deepest point
            
        Returns:
            Approximate action at specified fret
        """
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
        """
        Calculate wedge angle from dimensions.
        
        Useful for:
        - Neck tapers
        - Shims
        - Saddle blanks
        - Headstock angles
        
        Args:
            length: Length of wedge
            thick_end: Thickness at thick end
            thin_end: Thickness at thin end
            
        Returns:
            Angle in degrees
            
        Example:
            # Neck blank: 20" long, 1" at heel, 0.80" at nut
            >>> calc.wedge_angle(20, 1.0, 0.80)
            0.573  # degrees
        """
        if length <= 0:
            raise ValueError("Length must be positive")
        
        difference = thick_end - thin_end
        angle_rad = math.atan(difference / length)
        angle_deg = math.degrees(angle_rad)
        
        self._history.append(f"wedge_angle({length}, {thick_end}, {thin_end}) = {angle_deg:.4f}°")
        return round(angle_deg, 4)
    
    def wedge_thickness(self, length: float, thick_end: float, 
                        angle_deg: float, position: float) -> float:
        """
        Calculate thickness at any point along a wedge.
        
        Args:
            length: Total wedge length
            thick_end: Thickness at thick end (position 0)
            angle_deg: Wedge angle in degrees
            position: Distance from thick end
            
        Returns:
            Thickness at position
        """
        taper_per_unit = math.tan(math.radians(angle_deg))
        thickness = thick_end - (taper_per_unit * position)
        
        return round(thickness, 4)
    
    def taper_per_foot(self, thick_end: float, thin_end: float, 
                       length: float) -> float:
        """
        Calculate taper in inches per foot.
        
        Common woodworking measurement for tapered legs, etc.
        
        Args:
            thick_end: Thickness at thick end
            thin_end: Thickness at thin end
            length: Length of taper (in same units as thickness)
            
        Returns:
            Taper in units per foot
        """
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
        """
        Calculate board feet.
        
        Args:
            thickness: Thickness in inches (or quarters if quarters=True)
            width: Width in inches
            length: Length in inches (or feet - see note)
            quarters: If True, thickness is in quarter inches (4/4, 8/4, etc.)
            
        Returns:
            Board feet
            
        Note:
            If length > 24, assumes length is in inches
            If length <= 24, assumes length is in feet
            
        Example:
            >>> calc.board_feet(1, 8, 96)      # 1" × 8" × 8'
            5.33
            >>> calc.board_feet(4, 8, 8, quarters=True)  # 4/4 × 8" × 8'
            5.33
        """
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
        """
        Calculate kerf spacing for bent laminations.
        
        Kerf bending: making parallel saw cuts to allow wood to bend.
        
        Args:
            radius: Desired bend radius
            material_thickness: Stock thickness
            kerf_width: Width of saw kerf
            
        Returns:
            Spacing between kerfs (center to center)
            
        Formula:
            spacing = 2π × radius × kerf_width / 360°
            Simplified: spacing ≈ kerf_width × radius / 57.3
        """
        # More practical formula based on geometry
        spacing = (2 * math.pi * radius * kerf_width) / 360 * (360 / (2 * math.pi))
        
        # Simpler approximation that works well in practice
        spacing = kerf_width * radius / 57.3 * 2 * math.pi
        
        # Even simpler practical formula
        spacing = math.sqrt(2 * radius * kerf_width)
        
        self._history.append(f"kerf_spacing(r={radius}, t={material_thickness}) = {spacing:.4f}")
        return round(spacing, 4)
    
    def miter_angle(self, num_sides: int) -> float:
        """
        Calculate miter angle for regular polygon.
        
        Args:
            num_sides: Number of sides
            
        Returns:
            Miter angle in degrees (blade tilt from 90°)
            
        Example:
            >>> calc.miter_angle(6)   # Hexagon
            30.0  # degrees
            >>> calc.miter_angle(8)   # Octagon
            22.5  # degrees
        """
        if num_sides < 3:
            raise ValueError("Polygon must have at least 3 sides")
        
        angle = 180 / num_sides
        
        return round(angle, 4)
    
    def dovetail_angle(self, ratio: str = "1:8") -> float:
        """
        Calculate dovetail angle from ratio.
        
        Common ratios:
            1:6  - Softwood (steep, more mechanical strength)
            1:7  - General purpose
            1:8  - Hardwood (traditional)
            1:10 - Fine hardwood (elegant look)
            
        Args:
            ratio: Ratio as string "1:N" or just N
            
        Returns:
            Angle in degrees
        """
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
        """
        Estimate wood movement due to moisture change.
        
        Args:
            width: Board width in inches
            mc_change: Moisture content change (percentage points)
            tangential_coef: Tangential shrinkage coefficient
                            (default is average domestic hardwood)
            
        Returns:
            Expected movement in inches
            
        Common coefficients (tangential):
            Mahogany:   0.00250
            Maple:      0.00353  
            Walnut:     0.00274
            Oak (red):  0.00369
            Spruce:     0.00260
            
        Example:
            # 12" wide oak board, 4% MC change
            >>> calc.wood_movement(12, 4, 0.00369)
            0.177  # inches
        """
        movement = width * mc_change * tangential_coef
        
        return round(movement, 4)


# =============================================================================
# TESTS
# =============================================================================

def run_tests():
    """Run luthier calculator tests."""
    calc = LuthierCalculator()
    
    tests_passed = 0
    tests_failed = 0
    
    def test(name: str, expected: float, actual: float, tolerance: float = 0.01):
        nonlocal tests_passed, tests_failed
        if expected == float('inf') and actual == float('inf'):
            print(f"  ✓ {name}")
            tests_passed += 1
        elif abs(expected - actual) < tolerance:
            print(f"  ✓ {name}")
            tests_passed += 1
        else:
            print(f"  ✗ {name}: expected {expected}, got {actual}")
            tests_failed += 1
    
    print("\n=== Luthier Calculator Tests ===\n")
    
    # -------------------------------------------------------------------------
    # Radius from 3 points
    # -------------------------------------------------------------------------
    print("Radius from 3 points:")
    
    # Known case: points on circle of radius 10
    # Point at top of circle and two points at 45°
    r = 10
    p1 = (0, r)  # Top
    p2 = (r * math.sin(math.pi/4), r * math.cos(math.pi/4))  # 45°
    p3 = (-r * math.sin(math.pi/4), r * math.cos(math.pi/4))  # -45°
    test("Circle r=10, 3 points", 10.0, calc.radius_from_3_points(p1, p2, p3), 0.001)
    
    # Practical case: archtop measurement
    # 12" wide, 0.5" rise at center = ~36" radius
    r = calc.radius_from_3_points((0, 0), (6, 0.5), (12, 0))
    test("Archtop: 12\" wide, 0.5\" rise ≈ 36\"", 36.25, r, 0.5)
    
    # Collinear points = infinite radius
    r = calc.radius_from_3_points((0, 0), (5, 0), (10, 0))
    test("Collinear points = infinite", float('inf'), r)
    
    # -------------------------------------------------------------------------
    # Radius from chord
    # -------------------------------------------------------------------------
    print("\nRadius from chord (sagitta):")
    
    r = calc.radius_from_chord(2.0, 0.053)
    test("2\" chord, 0.053\" height ≈ 9.5\" radius", 9.5, r, 0.1)
    
    # -------------------------------------------------------------------------
    # Compound radius
    # -------------------------------------------------------------------------
    print("\nCompound radius:")
    
    # 9.5" to 14", at halfway should be ~11.75"
    r = calc.compound_radius(9.5, 14.0, 25.5, 12.75)
    test("9.5-14 compound at 12th fret", 11.75, r, 0.01)
    
    # At nut
    r = calc.compound_radius(9.5, 14.0, 25.5, 0)
    test("Compound at nut = 9.5", 9.5, r)
    
    # At saddle
    r = calc.compound_radius(9.5, 14.0, 25.5, 25.5)
    test("Compound at saddle = 14", 14.0, r)
    
    # -------------------------------------------------------------------------
    # Fret positions
    # -------------------------------------------------------------------------
    print("\nFret positions:")
    
    # 12th fret is exactly half scale length
    pos = calc.fret_position(25.5, 12)
    test("12th fret at half scale (25.5\")", 12.75, pos, 0.001)
    
    pos = calc.fret_position(24.75, 12)
    test("12th fret at half scale (24.75\")", 12.375, pos, 0.001)
    
    # First fret spacing check
    pos = calc.fret_position(25.5, 1)
    test("1st fret position (25.5\" scale)", 1.432, pos, 0.01)
    
    # -------------------------------------------------------------------------
    # Scale length from frets
    # -------------------------------------------------------------------------
    print("\nScale length from frets:")
    
    scale = calc.scale_length_from_frets(12.75, 0, 12)  # Nut to 12th
    test("Scale from nut-to-12th (12.75\")", 25.5, scale, 0.01)
    
    # -------------------------------------------------------------------------
    # Wedge angle
    # -------------------------------------------------------------------------
    print("\nWedge & taper:")
    
    angle = calc.wedge_angle(20, 1.0, 0.8)
    test("Wedge: 20\" long, 1\" to 0.8\"", 0.573, angle, 0.01)
    
    tpf = calc.taper_per_foot(1.0, 0.8, 20)
    test("Taper per foot: 1\" to 0.8\" in 20\"", 0.12, tpf, 0.01)
    
    # -------------------------------------------------------------------------
    # Woodworking
    # -------------------------------------------------------------------------
    print("\nWoodworking:")
    
    bf = calc.board_feet(1, 12, 8)  # 1" × 12" × 8'
    test("Board feet: 1×12×8ft", 8.0, bf)
    
    bf = calc.board_feet(1, 6, 96)  # 1" × 6" × 96" (8')
    test("Board feet: 1×6×96in", 4.0, bf)
    
    miter = calc.miter_angle(8)
    test("Octagon miter", 22.5, miter)
    
    miter = calc.miter_angle(6)
    test("Hexagon miter", 30.0, miter)
    
    dovetail = calc.dovetail_angle("1:8")
    test("Dovetail 1:8 ratio", 7.125, dovetail, 0.01)
    
    # -------------------------------------------------------------------------
    # Arc length
    # -------------------------------------------------------------------------
    print("\nArc length:")
    
    arc = calc.arc_length(9.5, 2.0)
    test("Arc length: r=9.5\", chord=2\"", 2.0035, arc, 0.001)
    
    print(f"\n=== Results: {tests_passed} passed, {tests_failed} failed ===")
    
    return tests_failed == 0


# =============================================================================
# CLI
# =============================================================================

def calculator_repl():
    """Interactive luthier calculator."""
    calc = LuthierCalculator()
    
    print("=" * 60)
    print("Luthier & Woodworking Calculator")
    print("=" * 60)
    print()
    print("Commands:")
    print("  r3p x1 y1 x2 y2 x3 y3  - Radius from 3 points")
    print("  rchord chord height    - Radius from chord & sagitta")
    print("  compound r1 r2 L pos   - Compound radius at position")
    print("  fret scale n           - Fret position")
    print("  frets scale            - Full fret table")
    print("  wedge len t1 t2        - Wedge angle")
    print("  bf t w l               - Board feet")
    print("  miter n                - Miter angle for n-sided polygon")
    print("  dovetail ratio         - Dovetail angle (e.g., 1:8)")
    print("  q                      - Quit")
    print()
    
    while True:
        try:
            user_input = input("luthier> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        parts = user_input.lower().split()
        cmd = parts[0]
        args = parts[1:]
        
        try:
            if cmd in ('q', 'quit', 'exit'):
                break
            
            elif cmd == 'r3p' and len(args) >= 6:
                x1, y1, x2, y2, x3, y3 = map(float, args[:6])
                r = calc.radius_from_3_points((x1, y1), (x2, y2), (x3, y3))
                print(f"  Radius: {r}")
            
            elif cmd == 'rchord' and len(args) >= 2:
                chord, height = map(float, args[:2])
                r = calc.radius_from_chord(chord, height)
                print(f"  Radius: {r}")
            
            elif cmd == 'sagitta' and len(args) >= 2:
                radius, chord = map(float, args[:2])
                h = calc.sagitta(radius, chord)
                print(f"  Sagitta (arc height): {h}")
            
            elif cmd == 'compound' and len(args) >= 4:
                r1, r2, scale, pos = map(float, args[:4])
                r = calc.compound_radius(r1, r2, scale, pos)
                print(f"  Radius at position {pos}: {r}")
            
            elif cmd == 'fret' and len(args) >= 2:
                scale = float(args[0])
                fret = int(args[1])
                pos = calc.fret_position(scale, fret)
                spacing = calc.fret_spacing(scale, fret)
                print(f"  Fret {fret}: {pos}\" from nut (spacing: {spacing}\")")
            
            elif cmd == 'frets' and len(args) >= 1:
                scale = float(args[0])
                num = int(args[1]) if len(args) > 1 else 22
                table = calc.fret_table(scale, num)
                print(f"  {'Fret':>4} {'From Nut':>10} {'Spacing':>10} {'To Bridge':>10}")
                print("  " + "-" * 44)
                for row in table:
                    print(f"  {row.fret_number:4d} {row.distance_from_nut:10.4f} "
                          f"{row.distance_from_previous:10.4f} {row.remaining_to_bridge:10.4f}")
            
            elif cmd == 'wedge' and len(args) >= 3:
                length, t1, t2 = map(float, args[:3])
                angle = calc.wedge_angle(length, t1, t2)
                print(f"  Wedge angle: {angle}°")
            
            elif cmd == 'bf' and len(args) >= 3:
                t, w, l = map(float, args[:3])
                bf = calc.board_feet(t, w, l)
                print(f"  Board feet: {bf}")
            
            elif cmd == 'miter' and len(args) >= 1:
                n = int(args[0])
                angle = calc.miter_angle(n)
                print(f"  Miter angle for {n}-sided polygon: {angle}°")
            
            elif cmd == 'dovetail' and len(args) >= 1:
                ratio = args[0]
                angle = calc.dovetail_angle(ratio)
                print(f"  Dovetail angle ({ratio}): {angle}°")
            
            elif cmd == 'arc' and len(args) >= 2:
                radius, chord = map(float, args[:2])
                arc = calc.arc_length(radius, chord)
                print(f"  Arc length: {arc}")
            
            else:
                # Try as math expression
                result = calc.evaluate(user_input)
                if calc.error:
                    print(f"  Error: {calc.error}")
                else:
                    print(f"  = {result}")
                    
        except (ValueError, IndexError) as e:
            print(f"  Error: {e}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        calculator_repl()
