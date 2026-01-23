#!/usr/bin/env python3
"""
Les Paul Body CNC Generator - Luthier's ToolBox

Reads your Les Paul DXF project files and generates production-ready
G-code for full body cuts. Designed to integrate with the existing
Luthier's ToolBox repository structure.

Key Features:
- Reads layered DXF (your "Les Paul CNC Files.dxf")
- Extracts body outline from Cutout layer
- Translates coordinates to work-zero (G54)
- Generates Mach4-compatible G-code with your tool specs
- Supports TXRX Labs and BCAMCNC 2030CA machines

DXF Layer Mapping (from your project):
- Cutout → Body perimeter (OP50)
- Neck Mortise → Neck pocket (OP20)
- Pickup Cavity → Humbucker routes (OP20)
- Electronic Cavities → Control cavity (OP20)
- Wiring Channel → Wire routes (OP40)
- Pot Holes, Through Hole, Studs → Drilling (OP60)

Usage:
    python lespaul_body_generator.py path/to/source.dxf --output body_cut.nc
    
    # Or import as module:
    from lespaul_body_generator import LesPaulBodyGenerator
    gen = LesPaulBodyGenerator("source.dxf")
    gen.generate_full_program("output.nc")

Author: Luthier's ToolBox Project
Target: TXRX Labs January 2026 demonstration
"""

from __future__ import annotations
import math
import ezdxf
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import argparse


# ============================================================================
# CONFIGURATION - Match your Fusion360 setup
# ============================================================================

@dataclass
class ToolConfig:
    """Tool configuration from your Fusion360 setup."""
    number: int
    name: str
    diameter_in: float
    rpm: int
    feed_ipm: float
    plunge_ipm: float
    stepdown_in: float
    stepover_pct: float
    
    @property
    def stepover_in(self) -> float:
        return self.diameter_in * (self.stepover_pct / 100)


@dataclass
class MachineConfig:
    """Machine configuration."""
    name: str
    max_x_in: float
    max_y_in: float
    max_z_in: float
    safe_z_in: float = 0.75
    retract_z_in: float = 0.25
    rapid_rate: float = 200.0  # IPM


# Default tool library (from your Tool_List_LP.csv, converted to inches)
TOOLS = {
    1: ToolConfig(1, "10mm Flat End Mill", 0.394, 18000, 220, 31, 0.22, 45),
    2: ToolConfig(2, "6mm Flat End Mill", 0.236, 18000, 150, 24, 0.06, 18),
    3: ToolConfig(3, "3mm Flat/Drill", 0.118, 20000, 60, 16, 0.03, 20),
}

# Machine configurations
MACHINES = {
    "txrx_router": MachineConfig("TXRX Labs Router", 48, 48, 4, 0.75, 0.25),
    "bcamcnc_2030ca": MachineConfig("BCAMCNC 2030CA", 48, 24, 4, 0.6, 0.2),
}


# ============================================================================
# DXF READER - Extract geometry from your layered DXF
# ============================================================================

@dataclass 
class ExtractedPath:
    """A path extracted from the DXF."""
    layer: str
    points: List[Tuple[float, float]]  # In inches
    is_closed: bool
    perimeter: float
    area: float
    bounds: Dict[str, float]
    
    @property
    def center(self) -> Tuple[float, float]:
        return (
            (self.bounds['min_x'] + self.bounds['max_x']) / 2,
            (self.bounds['min_y'] + self.bounds['max_y']) / 2,
        )
    
    @property
    def width(self) -> float:
        return self.bounds['max_x'] - self.bounds['min_x']
    
    @property
    def height(self) -> float:
        return self.bounds['max_y'] - self.bounds['min_y']


class LesPaulDXFReader:
    """
    Read Les Paul DXF and extract paths by layer.
    
    Handles:
    - LWPOLYLINE, POLYLINE, LINE, ARC, CIRCLE, SPLINE
    - Coordinate translation to work-zero
    - Unit detection (assumes inches based on your files)
    """
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.doc = None
        self.paths: Dict[str, List[ExtractedPath]] = {}
        self.origin_offset = (0.0, 0.0)  # DXF offset from work-zero
        self.body_outline: Optional[ExtractedPath] = None
    
    def load(self) -> 'LesPaulDXFReader':
        """Load and parse DXF file."""
        self.doc = ezdxf.readfile(str(self.filepath))
        self._extract_all_paths()
        self._find_body_outline()
        self._calculate_origin_offset()
        return self
    
    def _extract_all_paths(self):
        """Extract all paths from modelspace."""
        msp = self.doc.modelspace()
        
        for entity in msp:
            layer = entity.dxf.layer
            points = self._entity_to_points(entity)
            
            if not points or len(points) < 2:
                continue
            
            path = self._create_path(layer, points, entity)
            
            if layer not in self.paths:
                self.paths[layer] = []
            self.paths[layer].append(path)
    
    def _entity_to_points(self, entity) -> List[Tuple[float, float]]:
        """Convert DXF entity to point list."""
        points = []
        dxftype = entity.dxftype()
        
        if dxftype == 'LWPOLYLINE':
            for x, y, *_ in entity.get_points():
                points.append((x, y))
            if entity.closed and points and points[0] != points[-1]:
                points.append(points[0])
                
        elif dxftype == 'POLYLINE':
            for vertex in entity.vertices:
                points.append((vertex.dxf.location.x, vertex.dxf.location.y))
            if entity.is_closed and points and points[0] != points[-1]:
                points.append(points[0])
                
        elif dxftype == 'LINE':
            points = [
                (entity.dxf.start.x, entity.dxf.start.y),
                (entity.dxf.end.x, entity.dxf.end.y),
            ]
            
        elif dxftype == 'CIRCLE':
            cx, cy, r = entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius
            for i in range(65):
                angle = 2 * math.pi * i / 64
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
                
        elif dxftype == 'ARC':
            cx, cy = entity.dxf.center.x, entity.dxf.center.y
            r = entity.dxf.radius
            start = math.radians(entity.dxf.start_angle)
            end = math.radians(entity.dxf.end_angle)
            if end < start:
                end += 2 * math.pi
            segs = max(16, int((end - start) / (math.pi / 32)))
            for i in range(segs + 1):
                t = i / segs
                angle = start + t * (end - start)
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
                
        elif dxftype == 'SPLINE':
            try:
                for pt in entity.flattening(0.01):  # High resolution
                    points.append((pt.x, pt.y))
            except (AttributeError, RuntimeError):
                pass
        
        return points
    
    def _create_path(self, layer: str, points: List[Tuple[float, float]], entity) -> ExtractedPath:
        """Create ExtractedPath from points."""
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        # Calculate perimeter
        perimeter = 0.0
        for i in range(len(points) - 1):
            dx = points[i+1][0] - points[i][0]
            dy = points[i+1][1] - points[i][1]
            perimeter += math.sqrt(dx*dx + dy*dy)
        
        # Calculate area (shoelace formula)
        area = 0.0
        for i in range(len(points) - 1):
            area += points[i][0] * points[i+1][1]
            area -= points[i+1][0] * points[i][1]
        area = abs(area) / 2
        
        # Check if closed
        is_closed = False
        if hasattr(entity, 'closed'):
            is_closed = entity.closed
        elif points[0] == points[-1]:
            is_closed = True
        elif len(points) > 2:
            dx = points[0][0] - points[-1][0]
            dy = points[0][1] - points[-1][1]
            if math.sqrt(dx*dx + dy*dy) < 0.01:
                is_closed = True
        
        return ExtractedPath(
            layer=layer,
            points=points,
            is_closed=is_closed,
            perimeter=perimeter,
            area=area,
            bounds={
                'min_x': min(xs),
                'max_x': max(xs),
                'min_y': min(ys),
                'max_y': max(ys),
            }
        )
    
    def _find_body_outline(self):
        """Find the body outline (largest closed path on Cutout layer)."""
        if 'Cutout' not in self.paths:
            return
        
        # Find largest closed polyline by perimeter
        candidates = [p for p in self.paths['Cutout'] if p.is_closed]
        if candidates:
            self.body_outline = max(candidates, key=lambda p: p.perimeter)
    
    def _calculate_origin_offset(self):
        """Calculate offset to translate DXF coordinates to work-zero."""
        if self.body_outline:
            # Center body at origin, or use corner
            # Using lower-left corner as work-zero
            self.origin_offset = (
                self.body_outline.bounds['min_x'],
                self.body_outline.bounds['min_y'],
            )
    
    def translate_point(self, x: float, y: float) -> Tuple[float, float]:
        """Translate DXF coordinates to work coordinates."""
        return (x - self.origin_offset[0], y - self.origin_offset[1])
    
    def translate_path(self, path: ExtractedPath) -> List[Tuple[float, float]]:
        """Translate all points in a path to work coordinates."""
        return [self.translate_point(x, y) for x, y in path.points]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of extracted geometry."""
        summary = {
            'filepath': str(self.filepath),
            'origin_offset': self.origin_offset,
            'layers': {},
        }
        
        if self.body_outline:
            summary['body_outline'] = {
                'width_in': self.body_outline.width,
                'height_in': self.body_outline.height,
                'perimeter_in': self.body_outline.perimeter,
                'points': len(self.body_outline.points),
            }
        
        for layer, paths in self.paths.items():
            closed = sum(1 for p in paths if p.is_closed)
            summary['layers'][layer] = {
                'path_count': len(paths),
                'closed_paths': closed,
            }
        
        return summary


# ============================================================================
# G-CODE GENERATOR
# ============================================================================

class LesPaulGCodeGenerator:
    """
    Generate production G-code for Les Paul body cutting.
    
    Output formats:
    - Mach4 (default)
    - GRBL
    - LinuxCNC
    """
    
    def __init__(self,
                 reader: LesPaulDXFReader,
                 machine: MachineConfig = None,
                 tools: Dict[int, ToolConfig] = None,
                 stock_thickness_in: float = 1.75):
        self.reader = reader
        self.machine = machine or MACHINES['txrx_router']
        self.tools = tools or TOOLS
        self.stock_thickness = stock_thickness_in
        
        self.gcode: List[str] = []
        self.current_tool: Optional[int] = None
        self.current_z: float = self.machine.safe_z_in
        self.stats = {
            'rapid_distance': 0.0,
            'cut_distance': 0.0,
            'cut_time_min': 0.0,
        }
    
    def _emit(self, line: str):
        """Add line to G-code output."""
        self.gcode.append(line)
    
    def _header(self, program_name: str):
        """Generate program header."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        self._emit(f"; {program_name}")
        self._emit(f"; Generated: {now}")
        self._emit(f"; Generator: Luthier's ToolBox - Les Paul Body Generator")
        self._emit(f"; Machine: {self.machine.name}")
        self._emit(f"; Stock: {self.stock_thickness}\" thick")
        self._emit(";")
        
        if self.reader.body_outline:
            self._emit(f"; Body size: {self.reader.body_outline.width:.2f}\" × {self.reader.body_outline.height:.2f}\"")
            self._emit(f"; Perimeter: {self.reader.body_outline.perimeter:.1f}\"")
        
        self._emit(";")
        self._emit("")
        self._emit("( SAFE START )")
        self._emit("G20         ; Inches")
        self._emit("G17         ; XY plane")
        self._emit("G90         ; Absolute")
        self._emit("G94         ; Feed per minute")
        self._emit("G54         ; Work offset")
        self._emit(f"G0 Z{self.machine.safe_z_in:.4f}")
        self._emit("")
    
    def _footer(self):
        """Generate program footer."""
        self._emit("")
        self._emit("( PROGRAM END )")
        self._emit("M5          ; Spindle off")
        self._emit(f"G0 Z{self.machine.safe_z_in:.4f}")
        self._emit("G0 X0 Y0    ; Return home")
        self._emit("M30         ; End program")
    
    def _tool_change(self, tool_num: int, operation: str = ""):
        """Generate tool change sequence."""
        if self.current_tool == tool_num:
            return
        
        tool = self.tools[tool_num]
        
        if self.current_tool is not None:
            self._emit("M5")
        
        self._emit("")
        self._emit(f"( TOOL CHANGE: T{tool_num} - {tool.name} )")
        if operation:
            self._emit(f"( {operation} )")
        self._emit(f"T{tool_num} M6")
        self._emit(f"S{tool.rpm} M3")
        self._emit("G4 P2       ; Dwell for spindle")
        self._emit(f"G0 Z{self.machine.safe_z_in:.4f}")
        
        self.current_tool = tool_num
    
    def _rapid(self, x: float = None, y: float = None, z: float = None):
        """Rapid move."""
        parts = ["G0"]
        if x is not None:
            parts.append(f"X{x:.4f}")
        if y is not None:
            parts.append(f"Y{y:.4f}")
        if z is not None:
            parts.append(f"Z{z:.4f}")
            self.current_z = z
        self._emit(" ".join(parts))
    
    def _feed(self, x: float = None, y: float = None, z: float = None, f: float = None):
        """Feed move."""
        parts = ["G1"]
        if x is not None:
            parts.append(f"X{x:.4f}")
        if y is not None:
            parts.append(f"Y{y:.4f}")
        if z is not None:
            parts.append(f"Z{z:.4f}")
            self.current_z = z
        if f is not None:
            parts.append(f"F{f:.1f}")
        self._emit(" ".join(parts))
    
    def generate_body_perimeter(self,
                                tool_num: int = 2,
                                tab_count: int = 6,
                                tab_width_in: float = 0.5,
                                tab_height_in: float = 0.125,
                                finish_allowance_in: float = 0.02) -> str:
        """
        Generate body perimeter cut with holding tabs.
        
        This is the main body outline cut (OP50 in your workflow).
        """
        if not self.reader.body_outline:
            raise ValueError("No body outline found in DXF")
        
        tool = self.tools[tool_num]
        path = self.reader.translate_path(self.reader.body_outline)
        
        # Calculate passes
        doc = tool.stepdown_in
        total_depth = self.stock_thickness
        num_passes = max(1, math.ceil(total_depth / doc))
        tab_z = -total_depth + tab_height_in
        
        self._emit("")
        self._emit("( ============================================ )")
        self._emit("( OP50: BODY PERIMETER CONTOUR )")
        self._emit("( ============================================ )")
        self._emit(f"( Tool: T{tool_num} {tool.name} )")
        self._emit(f"( Depth: {total_depth}\" in {num_passes} passes )")
        self._emit(f"( DOC: {doc}\" per pass )")
        self._emit(f"( Tabs: {tab_count} × {tab_width_in}\" wide × {tab_height_in}\" tall )")
        self._emit(f"( Feed: {tool.feed_ipm} IPM )")
        
        self._tool_change(tool_num, "Body perimeter contour")
        
        # Calculate tab positions along path
        perimeter = self.reader.body_outline.perimeter
        tab_spacing = perimeter / tab_count
        tab_positions = [(i + 0.5) * tab_spacing for i in range(tab_count)]
        
        # Start point
        start_x, start_y = path[0]
        
        for pass_num in range(num_passes):
            current_depth = -doc * (pass_num + 1)
            if current_depth < -total_depth:
                current_depth = -total_depth
            
            is_final_passes = pass_num >= num_passes - 2  # Last 2 passes get tabs
            
            self._emit("")
            self._emit(f"( Pass {pass_num + 1}/{num_passes}: Z = {current_depth:.4f} )")
            
            # Move to start
            self._rapid(z=self.machine.safe_z_in)
            self._rapid(start_x, start_y)
            self._rapid(z=self.machine.retract_z_in)
            
            # Ramp entry (3° ramp angle)
            ramp_distance = abs(current_depth - self.machine.retract_z_in) / math.tan(math.radians(3))
            ramp_distance = min(ramp_distance, 2.0)  # Max 2" ramp
            
            if len(path) > 1:
                # Ramp along first segment
                dx = path[1][0] - path[0][0]
                dy = path[1][1] - path[0][1]
                seg_len = math.sqrt(dx*dx + dy*dy)
                if seg_len > 0:
                    t = min(1.0, ramp_distance / seg_len)
                    ramp_x = start_x + dx * t
                    ramp_y = start_y + dy * t
                    self._feed(ramp_x, ramp_y, current_depth, tool.plunge_ipm)
            else:
                self._feed(z=current_depth, f=tool.plunge_ipm)
            
            # Cut perimeter
            self._emit(f"F{tool.feed_ipm:.1f}")
            
            accumulated_dist = 0.0
            tab_idx = 0
            in_tab = False
            
            for i in range(1, len(path)):
                px, py = path[i]
                prev_x, prev_y = path[i-1]
                
                seg_len = math.sqrt((px - prev_x)**2 + (py - prev_y)**2)
                
                # Handle tabs on final passes when below tab_z
                if is_final_passes and current_depth < tab_z and tab_idx < len(tab_positions):
                    # Check if we're entering or in a tab zone
                    while tab_idx < len(tab_positions):
                        tab_start = tab_positions[tab_idx] - tab_width_in / 2
                        tab_end = tab_positions[tab_idx] + tab_width_in / 2
                        
                        if accumulated_dist < tab_start < accumulated_dist + seg_len:
                            # Entering tab - raise Z
                            if not in_tab:
                                self._feed(z=tab_z, f=tool.plunge_ipm)
                                in_tab = True
                        
                        if accumulated_dist < tab_end < accumulated_dist + seg_len:
                            # Exiting tab - lower Z
                            if in_tab:
                                self._feed(z=current_depth, f=tool.plunge_ipm)
                                in_tab = False
                                tab_idx += 1
                                continue
                        
                        break
                
                self._feed(px, py)
                accumulated_dist += seg_len
                
                # Track cutting distance
                self.stats['cut_distance'] += seg_len
            
            # Close the path if not already closed
            if path[0] != path[-1]:
                self._feed(path[0][0], path[0][1])
            
            self._rapid(z=self.machine.retract_z_in)
        
        # Calculate cut time
        self.stats['cut_time_min'] += self.stats['cut_distance'] / tool.feed_ipm
        
        return "\n".join(self.gcode)
    
    def generate_pocket(self,
                        layer: str,
                        tool_num: int,
                        depth_in: float,
                        operation_name: str) -> str:
        """Generate pocket clearing operation for a layer."""
        if layer not in self.reader.paths:
            return ""
        
        tool = self.tools[tool_num]
        paths = [p for p in self.reader.paths[layer] if p.is_closed]
        
        if not paths:
            return ""
        
        self._emit("")
        self._emit(f"( ============================================ )")
        self._emit(f"( {operation_name} )")
        self._emit(f"( ============================================ )")
        self._emit(f"( Layer: {layer} )")
        self._emit(f"( Paths: {len(paths)} )")
        self._emit(f"( Depth: {depth_in}\" )")
        
        self._tool_change(tool_num, operation_name)
        
        doc = tool.stepdown_in
        num_passes = max(1, math.ceil(depth_in / doc))
        stepover = tool.stepover_in
        
        for path in paths:
            translated = self.reader.translate_path(path)
            cx, cy = path.center
            cx -= self.reader.origin_offset[0]
            cy -= self.reader.origin_offset[1]
            
            self._emit(f"( Pocket at ({cx:.2f}, {cy:.2f}), {path.width:.2f}\" × {path.height:.2f}\" )")
            
            for pass_num in range(num_passes):
                current_depth = -doc * (pass_num + 1)
                if current_depth < -depth_in:
                    current_depth = -depth_in
                
                # Move to center
                self._rapid(z=self.machine.safe_z_in)
                self._rapid(cx, cy)
                self._rapid(z=self.machine.retract_z_in)
                
                # Helical entry
                helix_radius = tool.diameter_in / 4
                self._emit(f"( Pass {pass_num + 1}: helical entry to Z{current_depth:.4f} )")
                self._emit(f"G2 X{cx:.4f} Y{cy:.4f} I{helix_radius:.4f} J0 Z{current_depth:.4f} F{tool.plunge_ipm:.1f}")
                
                # Spiral outward
                self._emit(f"F{tool.feed_ipm:.1f}")
                
                max_offset = min(path.width, path.height) / 2 - tool.diameter_in / 2
                current_offset = stepover
                
                while current_offset < max_offset:
                    # Simple rectangular spiral
                    x1 = cx - current_offset
                    x2 = cx + current_offset
                    y1 = cy - current_offset
                    y2 = cy + current_offset
                    
                    self._feed(x1, y1)
                    self._feed(x2, y1)
                    self._feed(x2, y2)
                    self._feed(x1, y2)
                    self._feed(x1, y1)
                    
                    current_offset += stepover
                
                # Perimeter cleanup
                for px, py in translated:
                    self._feed(px, py)
            
            self._rapid(z=self.machine.retract_z_in)
        
        return "\n".join(self.gcode)
    
    def generate_drilling_operation(self,
                                    holes: List[Dict[str, float]],
                                    tool_num: int,
                                    depth_in: float,
                                    operation_name: str,
                                    peck_depth_in: float = 0.125) -> str:
        """
        Generate drilling operations using G83 peck cycle.
        
        Args:
            holes: List of {'x': float, 'y': float, 'diameter': float}
            tool_num: Tool number
            depth_in: Hole depth
            operation_name: Description
            peck_depth_in: Peck depth for chip clearing
        """
        if not holes:
            return ""
        
        tool = self.tools[tool_num]
        
        self._emit("")
        self._emit(f"( ============================================ )")
        self._emit(f"( {operation_name} )")
        self._emit(f"( ============================================ )")
        self._emit(f"( Holes: {len(holes)} )")
        self._emit(f"( Depth: {depth_in}\" )")
        self._emit(f"( Peck: {peck_depth_in}\" )")
        
        self._tool_change(tool_num, operation_name)
        
        for i, hole in enumerate(holes):
            x, y = hole['x'], hole['y']
            diameter = hole.get('diameter', 0.25)
            
            self._emit(f"( Hole {i+1}: ({x:.3f}, {y:.3f}) Ø{diameter:.3f}\" )")
            
            # Move to position
            self._rapid(z=self.machine.safe_z_in)
            self._rapid(x, y)
            
            # Determine if we need to bore (hole > tool) or just drill
            if diameter > tool.diameter_in * 1.1:
                # Helical bore for larger holes
                bore_radius = (diameter - tool.diameter_in) / 2
                self._emit(f"( Helical bore - radius {bore_radius:.3f}\" )")
                self._rapid(z=self.machine.retract_z_in)
                
                # Helical descent
                z_current = 0
                while z_current > -depth_in:
                    z_current -= tool.stepdown_in
                    if z_current < -depth_in:
                        z_current = -depth_in
                    self._emit(f"G2 X{x:.4f} Y{y:.4f} I{bore_radius:.4f} J0 Z{z_current:.4f} F{tool.plunge_ipm:.1f}")
                
                # Final cleanup circle
                self._emit(f"G2 X{x:.4f} Y{y:.4f} I{bore_radius:.4f} J0 F{tool.feed_ipm:.1f}")
            else:
                # Standard peck drill cycle
                self._emit(f"G83 Z{-depth_in:.4f} R{self.machine.retract_z_in:.4f} Q{peck_depth_in:.4f} F{tool.plunge_ipm:.1f}")
        
        self._emit("G80  ; Cancel canned cycle")
        self._rapid(z=self.machine.safe_z_in)
        
        return "\n".join(self.gcode)
    
    def generate_cover_recess(self,
                              tool_num: int = 2,
                              depth_in: float = 0.125) -> str:
        """
        Generate back cover recess pocket.
        
        From DXF Cover Recess layer:
        - Center: (12.533, 10.393)
        - Size: 5.043" × 3.551"
        - Bounds: X[10.011 to 15.055] Y[8.617 to 12.168]
        """
        if 'Cover Recess' not in self.reader.paths:
            return ""
        
        tool = self.tools[tool_num]
        # Get closed paths with reasonable dimensions (filter out arc artifacts)
        paths = [p for p in self.reader.paths['Cover Recess'] 
                 if p.is_closed and p.width > 1.0 and p.height > 1.0]
        
        if not paths:
            return ""
        
        # Use the largest path
        paths = sorted(paths, key=lambda p: p.perimeter, reverse=True)[:1]
        
        self._emit("")
        self._emit(f"( ============================================ )")
        self._emit(f"( OP25: BACK COVER RECESS )")
        self._emit(f"( ============================================ )")
        self._emit(f"( Rabbet for back cover plate )")
        self._emit(f"( Depth: {depth_in}\" )")
        
        self._tool_change(tool_num, "Back cover recess")
        
        for path in paths:
            translated = self.reader.translate_path(path)
            cx, cy = path.center
            cx -= self.reader.origin_offset[0]
            cy -= self.reader.origin_offset[1]
            
            self._emit(f"( Cover recess at ({cx:.2f}, {cy:.2f}), {path.width:.2f}\" × {path.height:.2f}\" )")
            
            # Single depth pass for shallow rabbet
            self._rapid(z=self.machine.safe_z_in)
            self._rapid(cx, cy)
            self._rapid(z=self.machine.retract_z_in)
            
            # Helical entry
            helix_radius = tool.diameter_in / 4
            self._emit(f"G2 X{cx:.4f} Y{cy:.4f} I{helix_radius:.4f} J0 Z{-depth_in:.4f} F{tool.plunge_ipm:.1f}")
            
            # Spiral out to clear pocket
            self._emit(f"F{tool.feed_ipm:.1f}")
            stepover = tool.stepover_in
            max_offset = min(path.width, path.height) / 2 - tool.diameter_in / 2
            current_offset = stepover
            
            while current_offset < max_offset:
                x1 = cx - current_offset
                x2 = cx + current_offset
                y1 = cy - current_offset
                y2 = cy + current_offset
                
                self._feed(x1, y1)
                self._feed(x2, y1)
                self._feed(x2, y2)
                self._feed(x1, y2)
                self._feed(x1, y1)
                
                current_offset += stepover
            
            # Perimeter cleanup
            for px, py in translated:
                self._feed(px, py)
            
            self._rapid(z=self.machine.retract_z_in)
        
        return "\n".join(self.gcode)
    
    def _extract_holes_from_layer(self, layer_name: str) -> List[Dict[str, float]]:
        """Extract hole data from arc-based polylines in a layer."""
        holes = []
        
        if not self.reader.doc:
            return holes
        
        msp = self.reader.doc.modelspace()
        
        for e in msp:
            if e.dxf.layer == layer_name and e.dxftype() == 'LWPOLYLINE':
                pts = list(e.get_points())
                # Arc-based circles have 2 points with bulge
                if len(pts) == 2 and pts[0][4] != 0:
                    x1, y1 = pts[0][0], pts[0][1]
                    x2, y2 = pts[1][0], pts[1][1]
                    
                    chord = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    diameter = chord
                    
                    # Center and translate to work coords
                    cx = (x1 + x2) / 2 - self.reader.origin_offset[0]
                    cy = (y1 + y2) / 2 - self.reader.origin_offset[1]
                    
                    # Only include holes within body bounds
                    if self.reader.body_outline:
                        body_w = self.reader.body_outline.width
                        body_h = self.reader.body_outline.height
                        if 0 <= cx <= body_w and 0 <= cy <= body_h:
                            holes.append({
                                'x': cx,
                                'y': cy,
                                'diameter': diameter,
                            })
        
        # Remove duplicates
        unique = []
        for h in holes:
            is_dup = any(
                abs(h['x'] - u['x']) < 0.01 and abs(h['y'] - u['y']) < 0.01
                for u in unique
            )
            if not is_dup:
                unique.append(h)
        
        return unique
    
    def generate_full_program(self, program_name: str = "LesPaul_Body") -> str:
        """
        Generate complete CNC program for Les Paul body.
        
        Operation sequence (from your Mach4 templates):
        - OP20: Pocket rough (neck mortise, pickups, electronics)
        - OP25: Cover recess (back cover rabbet)
        - OP30: Pocket finish
        - OP40: Channels (wiring)
        - OP50: Perimeter contour with tabs
        - OP60: Drilling (pot holes, studs, screw holes)
        """
        self.gcode = []
        
        self._header(program_name)
        
        # OP20: Pocket rough - T1 (10mm)
        self.generate_pocket("Neck Mortise", 1, 0.75, "OP20: Neck Pocket Rough")
        self.generate_pocket("Pickup Cavity", 1, 0.75, "OP21: Pickup Cavity Rough")
        self.generate_pocket("Electronic Cavities", 1, 1.25, "OP22: Electronics Cavity Rough")
        
        # OP25: Cover recess (back) - T2 (6mm)
        self.generate_cover_recess(tool_num=2, depth_in=0.125)
        
        # OP30: Pocket finish - T2 (6mm)
        self.generate_pocket("Neck Mortise", 2, 0.75, "OP30: Neck Pocket Finish")
        self.generate_pocket("Pickup Cavity", 2, 0.75, "OP31: Pickup Cavity Finish")
        
        # OP40: Channels - T3 (3mm)
        self.generate_pocket("Wiring Channel", 3, 0.5, "OP40: Wiring Channel")
        
        # OP50: Perimeter
        self.generate_body_perimeter(tool_num=2, tab_count=6)
        
        # OP60: Drilling operations - T3 (3mm drill)
        # Extract holes from DXF layers
        pot_holes = self._extract_holes_from_layer('Pot Holes')
        if pot_holes:
            self.generate_drilling_operation(
                pot_holes, 3, self.stock_thickness,
                "OP60: Pot Shaft Holes (3/8\" through)"
            )
        
        studs = self._extract_holes_from_layer('Studs')
        if studs:
            # Bridge studs are deeper, tailpiece studs shallower
            bridge_studs = [h for h in studs if h['diameter'] > 0.4]
            tailpiece_studs = [h for h in studs if h['diameter'] <= 0.4]
            
            if bridge_studs:
                self.generate_drilling_operation(
                    bridge_studs, 3, 0.75,
                    "OP61: Bridge Post Holes (7/16\")"
                )
            if tailpiece_studs:
                self.generate_drilling_operation(
                    tailpiece_studs, 3, 0.625,
                    "OP62: Tailpiece Stud Holes (9/32\")"
                )
        
        screw_holes = self._extract_holes_from_layer('Screws')
        if screw_holes:
            self.generate_drilling_operation(
                screw_holes, 3, 0.5,
                "OP63: Screw Pilot Holes (#8)"
            )
        
        self._footer()
        
        return "\n".join(self.gcode)
    
    def save(self, filepath: str):
        """Save G-code to file."""
        with open(filepath, 'w') as f:
            f.write("\n".join(self.gcode))
        return filepath
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cutting statistics."""
        return {
            'cut_distance_in': round(self.stats['cut_distance'], 2),
            'estimated_time_min': round(self.stats['cut_time_min'], 1),
            'gcode_lines': len(self.gcode),
        }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

class LesPaulBodyGenerator:
    """
    Main interface for Les Paul body G-code generation.
    
    Usage:
        gen = LesPaulBodyGenerator("Les Paul CNC Files.dxf")
        gen.generate("output.nc")
        print(gen.stats)
    """
    
    def __init__(self, dxf_path: str, machine: str = "txrx_router"):
        self.dxf_path = Path(dxf_path)
        self.machine = MACHINES.get(machine, MACHINES['txrx_router'])
        
        # Load DXF
        self.reader = LesPaulDXFReader(str(self.dxf_path))
        self.reader.load()
        
        self.generator = None
        self.stats = {}
    
    def generate(self, 
                 output_path: str,
                 stock_thickness: float = 1.75,
                 program_name: str = None) -> str:
        """Generate G-code and save to file."""
        if program_name is None:
            program_name = self.dxf_path.stem
        
        self.generator = LesPaulGCodeGenerator(
            reader=self.reader,
            machine=self.machine,
            stock_thickness_in=stock_thickness,
        )
        
        gcode = self.generator.generate_full_program(program_name)
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w') as f:
            f.write(gcode)
        
        self.stats = self.generator.get_stats()
        self.stats['output_path'] = str(output)
        self.stats['body_size'] = {
            'width': self.reader.body_outline.width if self.reader.body_outline else 0,
            'height': self.reader.body_outline.height if self.reader.body_outline else 0,
        }
        
        return str(output)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get DXF and generation summary."""
        summary = self.reader.get_summary()
        summary['stats'] = self.stats
        return summary


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate CNC G-code for Les Paul body cutting"
    )
    parser.add_argument("dxf", help="Input DXF file path")
    parser.add_argument("-o", "--output", default="lespaul_body.nc", 
                        help="Output G-code file")
    parser.add_argument("-t", "--thickness", type=float, default=1.75,
                        help="Stock thickness in inches")
    parser.add_argument("-m", "--machine", default="txrx_router",
                        choices=list(MACHINES.keys()),
                        help="Target machine")
    parser.add_argument("--tabs", type=int, default=6,
                        help="Number of holding tabs")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LES PAUL BODY GENERATOR - Luthier's ToolBox")
    print("=" * 60)
    
    gen = LesPaulBodyGenerator(args.dxf, machine=args.machine)
    
    print(f"\nDXF: {args.dxf}")
    print(f"Machine: {gen.machine.name}")
    
    if gen.reader.body_outline:
        print(f"Body: {gen.reader.body_outline.width:.2f}\" × {gen.reader.body_outline.height:.2f}\"")
        print(f"Perimeter: {gen.reader.body_outline.perimeter:.1f}\"")
    
    print(f"\nLayers found:")
    for layer, paths in gen.reader.paths.items():
        closed = sum(1 for p in paths if p.is_closed)
        if closed > 0:
            print(f"  {layer}: {len(paths)} paths ({closed} closed)")
    
    output = gen.generate(args.output, stock_thickness=args.thickness)
    
    print(f"\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"Output: {output}")
    print(f"Lines: {gen.stats['gcode_lines']}")
    print(f"Cut distance: {gen.stats['cut_distance_in']}\"")
    print(f"Estimated time: {gen.stats['estimated_time_min']} min")


if __name__ == "__main__":
    main()
