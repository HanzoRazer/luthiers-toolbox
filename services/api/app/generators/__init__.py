"""
Luthier's ToolBox Generator Suite

G-code generators for guitar building CNC operations.

Modules:
    body_generator - Electric guitar body (Les Paul, etc.)
    neck_headstock_generator - Neck and headstock machining
    
Routers:
    body_generator_router - FastAPI endpoints for body generation
    neck_generator_router - FastAPI endpoints for neck generation
    
Usage:
    from app.generators import LesPaulBodyGenerator, NeckGenerator
    
    # Body from DXF
    body_gen = LesPaulBodyGenerator("les_paul.dxf")
    body_gen.generate("output.nc")
    
    # Neck from parameters
    neck_gen = NeckGenerator(scale_length=25.5, headstock_style="gibson_open")
    neck_gen.generate("neck_output.nc")
"""

# Body generator
from .lespaul_body_generator import (
    LesPaulBodyGenerator,
    LesPaulDXFReader,
    LesPaulGCodeGenerator,
    TOOLS,
    MACHINES,
    ToolConfig,
    MachineConfig,
    ExtractedPath,
)

# Neck generator
from .neck_headstock_generator import (
    NeckGenerator,
    NeckGCodeGenerator,
    NeckDimensions,
    HeadstockStyle,
    NeckProfile,
    NECK_PRESETS,
    NECK_TOOLS,
    NeckToolConfig,
    generate_headstock_outline,
    generate_tuner_positions,
    generate_neck_profile_points,
)

__all__ = [
    # Body
    'LesPaulBodyGenerator',
    'LesPaulDXFReader', 
    'LesPaulGCodeGenerator',
    'TOOLS',
    'MACHINES',
    'ToolConfig',
    'MachineConfig',
    'ExtractedPath',
    # Neck
    'NeckGenerator',
    'NeckGCodeGenerator',
    'NeckDimensions',
    'HeadstockStyle',
    'NeckProfile',
    'NECK_PRESETS',
    'NECK_TOOLS',
    'NeckToolConfig',
    'generate_headstock_outline',
    'generate_tuner_positions',
    'generate_neck_profile_points',
]
