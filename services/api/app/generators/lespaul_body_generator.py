#!/usr/bin/env python3
"""Les Paul Body CNC Generator - Luthier's ToolBox

WP-3: Config moved to lespaul_config.py, generator to lespaul_gcode_gen.py.
This module retains the LesPaulBodyGenerator facade and re-exports for
backward compatibility.
"""

from __future__ import annotations
from typing import Dict, Any
from pathlib import Path

from .lespaul_dxf_reader import ExtractedPath, LesPaulDXFReader
from .lespaul_config import ToolConfig as ToolConfig, MachineConfig as MachineConfig
from .lespaul_config import TOOLS as TOOLS, MACHINES as MACHINES
from .lespaul_gcode_gen import LesPaulGCodeGenerator as LesPaulGCodeGenerator


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

class LesPaulBodyGenerator:
    """Main interface for Les Paul body G-code generation."""
    
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





