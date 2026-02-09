#!/usr/bin/env python3
"""
Neck & Headstock CNC Generator - Luthier's ToolBox

Config/data layer and geometry helpers live in neck_headstock_config.py.
"""

from __future__ import annotations
import math
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from .neck_headstock_config import (
    NeckToolConfig as NeckToolConfig,
    NECK_TOOLS as NECK_TOOLS,
    HeadstockStyle as HeadstockStyle,
    NeckProfile as NeckProfile,
    NeckDimensions as NeckDimensions,
    NECK_PRESETS as NECK_PRESETS,
    generate_headstock_outline as generate_headstock_outline,
    generate_tuner_positions as generate_tuner_positions,
    generate_neck_profile_points as generate_neck_profile_points,
)




class NeckGCodeGenerator:
    """
    Generate G-code for neck machining operations.
    """
    
    def __init__(
        self,
        dims: NeckDimensions,
        headstock_style: HeadstockStyle = HeadstockStyle.PADDLE,
        profile: NeckProfile = NeckProfile.C_SHAPE,
        tools: Dict[int, NeckToolConfig] = None
    ):
        self.dims = dims
        self.headstock_style = headstock_style
        self.profile = profile
        self.tools = tools or NECK_TOOLS
        
        self.gcode: List[str] = []
        self.current_tool: Optional[int] = None
        self.safe_z = 1.0
        self.retract_z = 0.25
        
        self.stats = {
            'operations': [],
            'cut_time_min': 0.0,
        }
    
    def _emit(self, line: str):
        self.gcode.append(line)
    
    def _tool_change(self, tool_num: int, operation: str = ""):
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
        self._emit("G4 P2")
        self._emit(f"G0 Z{self.safe_z:.4f}")
        
        self.current_tool = tool_num
        self.stats['operations'].append({
            'tool': tool_num,
            'operation': operation,
        })
    
    def generate_header(self, job_name: str) -> str:
        """Generate program header."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        lines = [
            f"; {job_name} - Neck Program",
            f"; Generated: {now}",
            f"; Generator: Luthier's ToolBox - Neck Generator",
            f"; Scale: {self.dims.scale_length_in}\"",
            f"; Headstock: {self.headstock_style.value}",
            f"; Profile: {self.profile.value}",
            ";",
            "",
            "( SAFE START )",
            "G20         ; Inches",
            "G17         ; XY plane",
            "G90         ; Absolute",
            "G94         ; Feed per minute",
            "G54         ; Work offset",
            f"G0 Z{self.safe_z:.4f}",
            "",
        ]
        
        return "\n".join(lines)
    
    def generate_truss_rod_channel(self) -> str:
        """Generate truss rod channel cut."""
        self._emit("")
        self._emit("( ============================================ )")
        self._emit("( OP10: TRUSS ROD CHANNEL )")
        self._emit("( ============================================ )")
        self._emit(f"( Width: {self.dims.truss_rod_width_in}\" )")
        self._emit(f"( Depth: {self.dims.truss_rod_depth_in}\" )")
        self._emit(f"( Length: {self.dims.truss_rod_length_in}\" )")
        
        tool = self.tools[2]  # 1/8" flat end
        self._tool_change(2, "Truss rod channel")
        
        half_width = self.dims.truss_rod_width_in / 2 - tool.diameter_in / 2
        
        # Calculate passes
        depth = self.dims.truss_rod_depth_in
        doc = tool.stepdown_in
        num_passes = max(1, math.ceil(depth / doc))
        
        self._emit(f"( {num_passes} passes @ {doc}\" DOC )")
        
        for pass_num in range(num_passes):
            current_depth = -doc * (pass_num + 1)
            if current_depth < -depth:
                current_depth = -depth
            
            self._emit("")
            self._emit(f"( Pass {pass_num + 1}/{num_passes}: Z = {current_depth:.4f} )")
            
            # Start position (at nut)
            self._emit(f"G0 Z{self.safe_z:.4f}")
            self._emit(f"G0 X0.0000 Y{-half_width:.4f}")
            self._emit(f"G0 Z{self.retract_z:.4f}")
            
            # Plunge
            self._emit(f"G1 Z{current_depth:.4f} F{tool.plunge_ipm:.1f}")
            
            # Cut channel (back and forth)
            self._emit(f"G1 X{self.dims.truss_rod_length_in:.4f} F{tool.feed_ipm:.1f}")
            self._emit(f"G1 Y{half_width:.4f}")
            self._emit(f"G1 X0.0000")
            
            self._emit(f"G0 Z{self.retract_z:.4f}")
        
        self._emit(f"G0 Z{self.safe_z:.4f}")
        return "\n".join(self.gcode)
    
    def generate_headstock_outline(self) -> str:
        """Generate headstock perimeter cut."""
        self._emit("")
        self._emit("( ============================================ )")
        self._emit("( OP20: HEADSTOCK OUTLINE )")
        self._emit("( ============================================ )")
        self._emit(f"( Style: {self.headstock_style.value} )")
        
        tool = self.tools[3]  # 1/4" flat end
        self._tool_change(3, "Headstock outline")
        
        # Get outline points
        outline = generate_headstock_outline(self.headstock_style, self.dims)
        
        if not outline:
            self._emit("( No outline generated - paddle headstock )")
            return "\n".join(self.gcode)
        
        # Cutting parameters
        depth = self.dims.headstock_thickness_in + 0.1  # Through cut
        doc = tool.stepdown_in
        num_passes = max(1, math.ceil(depth / doc))
        
        self._emit(f"( {len(outline)} points, {num_passes} passes )")
        
        for pass_num in range(num_passes):
            current_depth = -doc * (pass_num + 1)
            if current_depth < -depth:
                current_depth = -depth
            
            self._emit("")
            self._emit(f"( Pass {pass_num + 1}/{num_passes}: Z = {current_depth:.4f} )")
            
            # Move to start
            x0, y0 = outline[0]
            self._emit(f"G0 Z{self.safe_z:.4f}")
            self._emit(f"G0 X{x0:.4f} Y{y0:.4f}")
            self._emit(f"G0 Z{self.retract_z:.4f}")
            self._emit(f"G1 Z{current_depth:.4f} F{tool.plunge_ipm:.1f}")
            
            # Cut outline
            self._emit(f"F{tool.feed_ipm:.1f}")
            for x, y in outline[1:]:
                self._emit(f"G1 X{x:.4f} Y{y:.4f}")
            
            # Close path
            self._emit(f"G1 X{x0:.4f} Y{y0:.4f}")
            
            self._emit(f"G0 Z{self.retract_z:.4f}")
        
        self._emit(f"G0 Z{self.safe_z:.4f}")
        return "\n".join(self.gcode)
    
    def generate_tuner_holes(self) -> str:
        """
        Generate tuner hole drilling.
        
        Standard tuner holes are 11/32" (0.344") for most tuners.
        """
        self._emit("")
        self._emit("( ============================================ )")
        self._emit("( OP30: TUNER HOLES )")
        self._emit("( ============================================ )")
        
        positions = generate_tuner_positions(self.headstock_style, self.dims)
        
        if not positions:
            self._emit("( No tuner positions for this headstock style )")
            return "\n".join(self.gcode)
        
        tool = self.tools[10]  # 11/32" drill
        self._tool_change(10, "Tuner holes")
        
        depth = self.dims.headstock_thickness_in + 0.1  # Through
        peck = 0.125  # Peck depth
        
        self._emit(f"( {len(positions)} holes, 11/32\" diameter )")
        
        for i, (x, y) in enumerate(positions, 1):
            self._emit("")
            self._emit(f"( Hole {i}: String {i if i <= 3 else 7 - i} )")
            self._emit(f"G0 Z{self.safe_z:.4f}")
            self._emit(f"G0 X{x:.4f} Y{y:.4f}")
            self._emit(f"G0 Z{self.retract_z:.4f}")
            
            # Peck drilling
            current = 0.0
            while current < depth:
                current = min(current + peck, depth)
                self._emit(f"G1 Z{-current:.4f} F{tool.plunge_ipm:.1f}")
                self._emit(f"G0 Z{self.retract_z:.4f}")
            
        self._emit(f"G0 Z{self.safe_z:.4f}")
        return "\n".join(self.gcode)
    
    def generate_neck_profile_rough(self) -> str:
        """Generate rough neck profile carve."""
        self._emit("")
        self._emit("( ============================================ )")
        self._emit("( OP40: NECK PROFILE ROUGH )")
        self._emit("( ============================================ )")
        self._emit(f"( Profile: {self.profile.value} )")
        self._emit("( Finish allowance: 0.030\" )")
        
        tool = self.tools[4]  # 3/8" ball end
        self._tool_change(4, "Neck profile rough")
        
        finish_allowance = 0.030
        stepover = tool.diameter_in * 0.4  # 40% stepover for roughing
        
        # Generate profile at multiple stations along neck
        stations = [0, 2, 4, 6, 8, 10, 12]  # Inches from nut
        
        self._emit(f"( {len(stations)} stations, {stepover:.3f}\" stepover )")
        
        for station in stations:
            profile_pts = generate_neck_profile_points(self.profile, self.dims, station)
            
            self._emit("")
            self._emit(f"( Station: {station}\" from nut )")
            
            for y, z in profile_pts:
                # Apply finish allowance
                z_rough = z + finish_allowance
                
                self._emit(f"G0 X{station:.4f} Y{y:.4f}")
                self._emit(f"G1 Z{z_rough:.4f} F{tool.feed_ipm:.1f}")
        
        self._emit(f"G0 Z{self.safe_z:.4f}")
        return "\n".join(self.gcode)
    
    def generate_footer(self) -> str:
        """Generate program footer."""
        lines = [
            "",
            "( PROGRAM END )",
            "M5          ; Spindle off",
            f"G0 Z{self.safe_z:.4f}",
            "G0 X0 Y0    ; Return to origin",
            "M30         ; End program",
        ]
        return "\n".join(lines)
    
    def generate_full_program(self, job_name: str = "Neck_Program") -> str:
        """Generate complete neck machining program."""
        self.gcode = []
        
        # Header
        self._emit(self.generate_header(job_name))
        
        # Operations
        self.generate_truss_rod_channel()
        self.generate_headstock_outline()
        self.generate_tuner_holes()
        self.generate_neck_profile_rough()
        
        # Footer
        self._emit(self.generate_footer())
        
        return "\n".join(self.gcode)


# =============================================================================
# MAIN INTERFACE
# =============================================================================

class NeckGenerator:
    """Main interface for neck G-code generation."""
    
    def __init__(
        self,
        scale_length: float = 25.5,
        headstock_style: str = "paddle",
        profile: str = "c",
        preset: Optional[str] = None
    ):
        # Get dimensions from preset or defaults
        if preset and preset in NECK_PRESETS:
            self.dims = NECK_PRESETS[preset]
        else:
            self.dims = NeckDimensions(scale_length_in=scale_length)
        
        # Parse headstock style
        try:
            self.headstock_style = HeadstockStyle(headstock_style)
        except ValueError:
            self.headstock_style = HeadstockStyle.PADDLE
        
        # Parse profile
        try:
            self.profile = NeckProfile(profile)
        except ValueError:
            self.profile = NeckProfile.C_SHAPE
        
        self.generator = None
        self.stats = {}
    
    def generate(self, output_path: str, job_name: str = None) -> str:
        """Generate G-code and save to file."""
        if job_name is None:
            job_name = Path(output_path).stem
        
        self.generator = NeckGCodeGenerator(
            dims=self.dims,
            headstock_style=self.headstock_style,
            profile=self.profile,
        )
        
        gcode = self.generator.generate_full_program(job_name)
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w', encoding="utf-8") as f:
            f.write(gcode)
        
        self.stats = {
            'output_path': str(output),
            'gcode_lines': len(gcode.split('\n')),
            'operations': self.generator.stats['operations'],
        }
        
        return str(output)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get generation summary."""
        return {
            'scale_length': self.dims.scale_length_in,
            'headstock_style': self.headstock_style.value,
            'profile': self.profile.value,
            'dimensions': {
                'nut_width': self.dims.nut_width_in,
                'heel_width': self.dims.heel_width_in,
                'depth_at_1st': self.dims.depth_at_1st_in,
                'depth_at_12th': self.dims.depth_at_12th_in,
            },
            'stats': self.stats,
        }


# =============================================================================
# CLI
