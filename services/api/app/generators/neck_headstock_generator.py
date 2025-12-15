#!/usr/bin/env python3
"""
Neck & Headstock CNC Generator - Luthier's ToolBox

Generates production G-code for neck blank processing:
- Headstock outline
- Truss rod channel
- Fretboard slot/glue surface
- Neck profile (rough + finish)
- Heel shaping
- Tuner holes

This is a SEPARATE program from body cutting because:
1. Different stock dimensions (neck blank vs body blank)
2. Different work holding (typically vertical or angled)
3. Different tool requirements (smaller tools, tighter tolerances)
4. Often done on different machine or different setup

Usage:
    python neck_headstock_generator.py --scale 25.5 --headstock gibson
    
    # Or import as module:
    from neck_headstock_generator import NeckGenerator
    gen = NeckGenerator(scale_length=25.5, headstock_style="gibson")
    gen.generate_full_program("output.nc")

Author: Luthier's ToolBox Project
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Literal
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import argparse


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class NeckToolConfig:
    """Tool configuration for neck operations."""
    number: int
    name: str
    diameter_in: float
    rpm: int
    feed_ipm: float
    plunge_ipm: float
    stepdown_in: float
    
    @property
    def diameter_mm(self) -> float:
        return self.diameter_in * 25.4


# Neck-specific tool library (smaller tools for precision work)
NECK_TOOLS = {
    1: NeckToolConfig(1, "1/4\" Ball End", 0.250, 18000, 100, 20, 0.10),
    2: NeckToolConfig(2, "1/8\" Flat End", 0.125, 20000, 60, 15, 0.05),
    3: NeckToolConfig(3, "1/4\" Flat End", 0.250, 18000, 80, 18, 0.08),
    4: NeckToolConfig(4, "3/8\" Ball End", 0.375, 16000, 120, 25, 0.12),
    5: NeckToolConfig(5, "1/16\" Flat End", 0.0625, 24000, 30, 10, 0.02),
    10: NeckToolConfig(10, "11/32\" Drill", 0.344, 2000, 10, 5, 0.05),  # Tuner holes
}


class HeadstockStyle(str, Enum):
    """Headstock shape styles."""
    GIBSON_OPEN = "gibson_open"       # Gibson open-book
    GIBSON_SOLID = "gibson_solid"     # Gibson solid
    FENDER_STRAT = "fender_strat"     # Fender 6-in-line
    FENDER_TELE = "fender_tele"       # Fender Telecaster
    PRS = "prs"                       # PRS style
    CLASSICAL = "classical"           # Slotted classical
    PADDLE = "paddle"                 # Blank paddle (user carves)


class NeckProfile(str, Enum):
    """Neck carve profile shapes."""
    C_SHAPE = "c"
    D_SHAPE = "d"
    V_SHAPE = "v"
    U_SHAPE = "u"
    ASYMMETRIC = "asymmetric"
    COMPOUND = "compound"  # Changes along length


@dataclass
class NeckDimensions:
    """Neck blank and finished dimensions."""
    # Blank dimensions
    blank_length_in: float = 26.0      # Includes headstock + heel
    blank_width_in: float = 3.5        # Wide enough for headstock
    blank_thickness_in: float = 1.0    # Before carving
    
    # Finished dimensions
    nut_width_in: float = 1.6875       # 1-11/16" standard
    heel_width_in: float = 2.25        # At body joint
    depth_at_1st_in: float = 0.82      # Neck depth at 1st fret
    depth_at_12th_in: float = 0.92     # Neck depth at 12th fret
    
    # Scale
    scale_length_in: float = 25.5
    
    # Headstock
    headstock_angle_deg: float = 14.0  # Gibson style
    headstock_thickness_in: float = 0.55
    headstock_length_in: float = 7.5
    
    # Truss rod
    truss_rod_width_in: float = 0.25
    truss_rod_depth_in: float = 0.375
    truss_rod_length_in: float = 18.0  # From nut


# Standard neck dimensions by style
NECK_PRESETS = {
    "gibson_50s": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.86,
        depth_at_12th_in=0.96,
        scale_length_in=24.75,
        headstock_angle_deg=17.0,
    ),
    "gibson_60s": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.80,
        depth_at_12th_in=0.90,
        scale_length_in=24.75,
        headstock_angle_deg=17.0,
    ),
    "fender_vintage": NeckDimensions(
        nut_width_in=1.625,
        depth_at_1st_in=0.82,
        depth_at_12th_in=0.92,
        scale_length_in=25.5,
        headstock_angle_deg=0.0,  # Flat headstock
    ),
    "fender_modern": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.78,
        depth_at_12th_in=0.88,
        scale_length_in=25.5,
        headstock_angle_deg=0.0,
    ),
    "prs": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.83,
        depth_at_12th_in=0.90,
        scale_length_in=25.0,
        headstock_angle_deg=10.0,
    ),
    "classical": NeckDimensions(
        nut_width_in=2.0,
        depth_at_1st_in=0.85,
        depth_at_12th_in=0.95,
        scale_length_in=25.6,  # 650mm
        headstock_angle_deg=15.0,
        blank_width_in=4.0,  # Wider for slotted
    ),
}


# =============================================================================
# HEADSTOCK GEOMETRY
# =============================================================================

def generate_headstock_outline(style: HeadstockStyle, dims: NeckDimensions) -> List[Tuple[float, float]]:
    """
    Generate headstock outline points.
    
    Returns list of (x, y) coordinates where:
    - Origin (0, 0) is at the nut
    - X is along neck length (negative toward headstock)
    - Y is across neck width
    """
    points = []
    
    if style == HeadstockStyle.GIBSON_OPEN:
        # Gibson open-book headstock
        # Symmetric about centerline
        half_width = dims.nut_width_in / 2
        
        points = [
            # Start at nut, right side
            (0.0, half_width),
            # Transition to headstock width
            (-0.5, half_width + 0.125),
            (-1.0, 1.5),
            # Upper bout
            (-2.0, 1.75),
            (-3.5, 1.85),
            # Top curve
            (-5.0, 1.8),
            (-6.0, 1.6),
            (-6.5, 1.3),
            (-7.0, 0.9),
            # Center notch (open book)
            (-7.2, 0.3),
            (-7.5, 0.0),  # Center point
            # Mirror for left side
            (-7.2, -0.3),
            (-7.0, -0.9),
            (-6.5, -1.3),
            (-6.0, -1.6),
            (-5.0, -1.8),
            (-3.5, -1.85),
            (-2.0, -1.75),
            (-1.0, -1.5),
            (-0.5, -half_width - 0.125),
            (0.0, -half_width),
        ]
        
    elif style == HeadstockStyle.FENDER_STRAT:
        # Fender 6-in-line
        half_width = dims.nut_width_in / 2
        
        points = [
            (0.0, half_width),
            (-0.25, half_width),
            (-0.5, half_width + 0.25),
            (-1.0, half_width + 0.5),
            # Upper edge (tuner side)
            (-2.0, 1.5),
            (-4.0, 1.45),
            (-6.0, 1.35),
            (-7.0, 1.2),
            # Tip
            (-7.5, 0.8),
            (-7.5, -0.4),  # Asymmetric
            # Lower edge
            (-7.0, -0.7),
            (-5.0, -0.65),
            (-3.0, -0.6),
            (-1.0, -half_width),
            (0.0, -half_width),
        ]
        
    elif style == HeadstockStyle.PADDLE:
        # Simple paddle shape
        half_width = dims.blank_width_in / 2
        length = dims.headstock_length_in
        
        points = [
            (0.0, half_width),
            (-length, half_width),
            (-length, -half_width),
            (0.0, -half_width),
        ]
    
    else:
        # Default to paddle if not implemented
        return generate_headstock_outline(HeadstockStyle.PADDLE, dims)
    
    return points


def generate_tuner_positions(style: HeadstockStyle, dims: NeckDimensions) -> List[Tuple[float, float]]:
    """
    Generate tuner hole positions.
    
    Returns list of (x, y) coordinates for drilling.
    """
    positions = []
    
    if style == HeadstockStyle.GIBSON_OPEN:
        # 3+3 configuration
        # Treble side (Y positive)
        positions.extend([
            (-1.8, 1.25),   # 1st string
            (-3.5, 1.45),   # 2nd string
            (-5.2, 1.35),   # 3rd string
        ])
        # Bass side (Y negative)
        positions.extend([
            (-1.8, -1.25),  # 6th string
            (-3.5, -1.45),  # 5th string
            (-5.2, -1.35),  # 4th string
        ])
        
    elif style == HeadstockStyle.FENDER_STRAT:
        # 6-in-line
        spacing = 0.9  # ~23mm
        y_offset = 0.9
        
        for i in range(6):
            x = -1.5 - (i * spacing)
            positions.append((x, y_offset))
    
    return positions


# =============================================================================
# NECK PROFILE GEOMETRY
# =============================================================================

def generate_neck_profile_points(
    profile: NeckProfile,
    dims: NeckDimensions,
    position_from_nut: float
) -> List[Tuple[float, float]]:
    """
    Generate cross-section profile points at a given position.
    
    Returns (y, z) coordinates for the back carve at this position.
    Position 0 = at nut, positive = toward body.
    """
    # Interpolate dimensions at this position
    t = position_from_nut / dims.scale_length_in
    t = max(0, min(1, t))  # Clamp to 0-1
    
    width = dims.nut_width_in + (dims.heel_width_in - dims.nut_width_in) * t
    depth = dims.depth_at_1st_in + (dims.depth_at_12th_in - dims.depth_at_1st_in) * t
    
    half_width = width / 2
    
    if profile == NeckProfile.C_SHAPE:
        # Classic C shape - comfortable, versatile
        points = []
        for i in range(21):
            angle = math.pi * i / 20  # 0 to π
            y = half_width * math.cos(angle)
            z = -depth * (0.2 + 0.8 * math.sin(angle))  # Slightly flat bottom
            points.append((y, z))
        return points
    
    elif profile == NeckProfile.D_SHAPE:
        # D shape - flatter back
        points = []
        for i in range(21):
            angle = math.pi * i / 20
            y = half_width * math.cos(angle)
            z = -depth * (0.4 + 0.6 * math.sin(angle))  # Flatter
            points.append((y, z))
        return points
    
    elif profile == NeckProfile.V_SHAPE:
        # V shape - vintage feel
        points = []
        for i in range(21):
            t_local = i / 20  # 0 to 1
            y = half_width * (1 - 2 * t_local)  # Linear across
            z = -depth * (1 - abs(1 - 2 * t_local) * 0.3)  # V shape
            points.append((y, z))
        return points
    
    else:
        # Default to C
        return generate_neck_profile_points(NeckProfile.C_SHAPE, dims, position_from_nut)


# =============================================================================
# G-CODE GENERATOR
# =============================================================================

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
        """
        Generate truss rod channel cut.
        
        This is typically the first operation on the neck blank.
        Work zero: X at nut centerline, Y at neck centerline, Z at fretboard surface.
        """
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
        """
        Generate headstock perimeter cut.
        
        This cuts the headstock shape from the blank.
        Assumes headstock face is up, angled appropriately.
        """
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
        """
        Generate rough neck profile carve.
        
        This is a 3D operation that removes bulk material.
        Leaves 0.030" for finish pass.
        """
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
    """
    Main interface for neck G-code generation.
    
    Usage:
        gen = NeckGenerator(scale_length=25.5, headstock_style="gibson_open")
        gen.generate("output.nc")
    """
    
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
        
        with open(output, 'w') as f:
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
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate CNC G-code for guitar neck machining"
    )
    parser.add_argument("-o", "--output", default="neck_program.nc",
                        help="Output G-code file")
    parser.add_argument("-s", "--scale", type=float, default=25.5,
                        help="Scale length in inches")
    parser.add_argument("--headstock", default="paddle",
                        choices=[s.value for s in HeadstockStyle],
                        help="Headstock style")
    parser.add_argument("--profile", default="c",
                        choices=[p.value for p in NeckProfile],
                        help="Neck profile shape")
    parser.add_argument("--preset", choices=list(NECK_PRESETS.keys()),
                        help="Use preset dimensions")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("NECK GENERATOR - Luthier's ToolBox")
    print("=" * 60)
    
    gen = NeckGenerator(
        scale_length=args.scale,
        headstock_style=args.headstock,
        profile=args.profile,
        preset=args.preset,
    )
    
    print(f"\nScale: {gen.dims.scale_length_in}\"")
    print(f"Headstock: {gen.headstock_style.value}")
    print(f"Profile: {gen.profile.value}")
    print(f"Nut width: {gen.dims.nut_width_in}\"")
    
    output = gen.generate(args.output)
    
    print(f"\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"Output: {output}")
    print(f"Lines: {gen.stats['gcode_lines']}")


if __name__ == "__main__":
    main()
