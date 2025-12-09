"""
Saw Lab 2.0 - Geometry Engine

Provides geometry calculations specific to saw blade operations.
"""
from __future__ import annotations

import math
from typing import List, Dict, Any

from .models import SawContext, SawDesign


class SawGeometryEngine:
    """
    Geometry computation for saw blade operations.
    
    Calculates:
        - Blade arc paths
        - Entry/exit points
        - Stock intersection geometry
        - Kerf offset calculations
    """
    
    def compute_blade_arc(
        self,
        ctx: SawContext,
        cut_depth_mm: float
    ) -> Dict[str, Any]:
        """
        Compute the blade arc that intersects the stock.
        
        Args:
            ctx: Saw context with blade parameters
            cut_depth_mm: Depth of cut into stock
        
        Returns:
            Dict with arc parameters (center, radius, angles)
        """
        blade_radius = ctx.blade_diameter_mm / 2.0
        
        # Arbor center is at blade_radius above table surface
        # Stock sits on table at Z=0
        arbor_z = blade_radius
        
        # Cut depth determines how far blade descends
        blade_bottom_z = arbor_z - blade_radius  # Table surface
        cut_z = blade_bottom_z + cut_depth_mm
        
        # Calculate entry/exit angles
        if cut_depth_mm >= blade_radius:
            # Full semicircle cut
            entry_angle = 180.0
            exit_angle = 0.0
        else:
            # Partial arc cut
            # Using geometry: cos(θ) = (R - depth) / R
            cos_theta = (blade_radius - cut_depth_mm) / blade_radius
            cos_theta = max(-1.0, min(1.0, cos_theta))  # Clamp for safety
            half_angle = math.acos(cos_theta)
            entry_angle = 90.0 + math.degrees(half_angle)
            exit_angle = 90.0 - math.degrees(half_angle)
        
        return {
            "center_x": 0.0,
            "center_z": arbor_z,
            "radius": blade_radius,
            "entry_angle_deg": entry_angle,
            "exit_angle_deg": exit_angle,
            "arc_length_mm": self._arc_length(blade_radius, entry_angle, exit_angle),
        }
    
    def _arc_length(
        self,
        radius: float,
        start_angle_deg: float,
        end_angle_deg: float
    ) -> float:
        """Calculate arc length from angles."""
        angle_span = abs(start_angle_deg - end_angle_deg)
        return 2 * math.pi * radius * (angle_span / 360.0)
    
    def compute_cut_profile(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> Dict[str, Any]:
        """
        Compute the complete cut profile geometry.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            Dict with cut profile geometry
        """
        kerf_half = ctx.blade_kerf_mm / 2.0
        
        # Effective cut depth accounting for bevel
        if design.bevel_angle_deg != 0:
            bevel_rad = math.radians(abs(design.bevel_angle_deg))
            effective_depth = ctx.stock_thickness_mm / math.cos(bevel_rad)
        else:
            effective_depth = ctx.stock_thickness_mm
        
        # Miter adjustments
        if design.miter_angle_deg != 0:
            miter_rad = math.radians(abs(design.miter_angle_deg))
            effective_length = design.cut_length_mm / math.cos(miter_rad)
        else:
            effective_length = design.cut_length_mm
        
        # Material removed volume
        if design.dado_width_mm > 0:
            # Dado cut
            cut_width = design.dado_width_mm
            cut_depth = design.dado_depth_mm
        else:
            # Through cut
            cut_width = ctx.blade_kerf_mm
            cut_depth = effective_depth
        
        material_removed = cut_width * cut_depth * effective_length * design.repeat_count
        
        return {
            "kerf_offset_mm": kerf_half,
            "effective_depth_mm": effective_depth,
            "effective_length_mm": effective_length,
            "material_removed_mm3": material_removed,
            "cut_count": design.repeat_count,
        }
    
    def generate_cut_points(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> List[Dict[str, float]]:
        """
        Generate the sequence of cut points.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            List of point dicts with x, y, z coordinates
        """
        points = []
        
        for cut_idx in range(design.repeat_count):
            offset = cut_idx * (ctx.blade_kerf_mm + design.offset_mm)
            
            # Entry point (above stock)
            points.append({
                "x": offset,
                "y": 0.0,
                "z": ctx.stock_thickness_mm + 10.0,  # 10mm clearance
                "type": "rapid"
            })
            
            # Cut start (at stock surface)
            points.append({
                "x": offset,
                "y": 0.0,
                "z": ctx.stock_thickness_mm,
                "type": "plunge_start"
            })
            
            # Cut end (through stock)
            points.append({
                "x": offset,
                "y": design.cut_length_mm,
                "z": -1.0,  # 1mm below stock
                "type": "cut"
            })
            
            # Retract
            points.append({
                "x": offset,
                "y": design.cut_length_mm,
                "z": ctx.stock_thickness_mm + 10.0,
                "type": "retract"
            })
        
        return points
    
    def compute_tooth_engagement(
        self,
        ctx: SawContext,
        cut_depth_mm: float
    ) -> Dict[str, Any]:
        """
        Calculate tooth engagement metrics.
        
        Args:
            ctx: Saw context
            cut_depth_mm: Depth of cut
        
        Returns:
            Dict with tooth engagement data
        """
        blade_arc = self.compute_blade_arc(ctx, cut_depth_mm)
        arc_length = blade_arc["arc_length_mm"]
        
        # Tooth spacing
        circumference = math.pi * ctx.blade_diameter_mm
        tooth_spacing = circumference / ctx.tooth_count
        
        # Number of teeth in cut at any time
        teeth_in_cut = arc_length / tooth_spacing
        
        # Feed per tooth
        feed_per_tooth = ctx.feed_rate_mm_per_min / (ctx.max_rpm * ctx.tooth_count)
        
        return {
            "teeth_in_cut": round(teeth_in_cut, 2),
            "tooth_spacing_mm": round(tooth_spacing, 2),
            "feed_per_tooth_mm": round(feed_per_tooth, 4),
            "arc_length_mm": round(arc_length, 2),
        }
