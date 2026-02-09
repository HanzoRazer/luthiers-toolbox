"""WP-3: Les Paul G-code generation engine.

Extracted from lespaul_body_generator.py to reduce god-object size.
Contains the full LesPaulGCodeGenerator class with all CNC operations.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from datetime import datetime

from .lespaul_dxf_reader import ExtractedPath, LesPaulDXFReader
from .lespaul_config import ToolConfig, MachineConfig


class LesPaulGCodeGenerator:
    """Generate production G-code for Les Paul body cutting."""
    
    def __init__(self,
                 reader: LesPaulDXFReader,
                 machine: MachineConfig = None,
                 tools: Dict[int, ToolConfig] = None,
                 stock_thickness_in: float = 1.75):
        from .lespaul_config import MACHINES, TOOLS

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
    
    # -----------------------------------------------------------------
    # Core G-code primitives
    # -----------------------------------------------------------------

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
    
    # -----------------------------------------------------------------
    # CNC Operations
    # -----------------------------------------------------------------

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
        """Generate drilling operations using G83 peck cycle."""
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
        """Generate back cover recess pocket."""
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
        """Generate complete CNC program for Les Paul body."""
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
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.gcode))
        return filepath
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cutting statistics."""
        return {
            'cut_distance_in': round(self.stats['cut_distance'], 2),
            'estimated_time_min': round(self.stats['cut_time_min'], 1),
            'gcode_lines': len(self.gcode),
        }
