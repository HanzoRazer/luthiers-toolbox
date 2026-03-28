"""
The Production Shop Generator Suite

G-code generators for guitar building CNC operations.

Modules:
    body_generator - Electric guitar body (Les Paul, etc.)
    stratocaster_body_generator - Stratocaster body with pickup configs (GAP-07)
    neck_headstock_generator - Neck and headstock machining
    bezier_body - Parametric acoustic guitar body outlines

Routers:
    body_generator_router - FastAPI endpoints for body generation
    neck_generator_router - FastAPI endpoints for neck generation

Usage:
    from app.generators import LesPaulBodyGenerator, NeckGenerator

    # Body from DXF
    body_gen = LesPaulBodyGenerator("les_paul.dxf")
    body_gen.generate("output.nc")

    # Stratocaster body (parametric)
    from app.generators import StratocasterBodyGenerator, StratBodySpec, PickupConfig
    spec = StratBodySpec(pickup_config=PickupConfig.HSS, fret_count=22)
    gen = StratocasterBodyGenerator(spec)
    gen.generate("strat_output.nc")

    # Neck from parameters
    neck_gen = NeckGenerator(scale_length=25.5, headstock_style="gibson_open")
    neck_gen.generate("neck_output.nc")

    # Parametric acoustic body
    from app.generators import BezierBodyGenerator, BezierBodyParams
    params = BezierBodyParams.dreadnought()
    gen = BezierBodyGenerator(params)
    gen.to_dxf("dreadnought_outline.dxf")
"""

# Body generator (WP-3: config in lespaul_config.py, generator in lespaul_gcode_gen.py)
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

# Bezier body outline generator (parametric acoustic body shapes)
from .bezier_body import (
    BezierBodyParams,
    BezierBodyGenerator,
    ControlPoints,
    cubic_bezier,
    get_preset as get_body_preset,
    list_presets as list_body_presets,
    BODY_PRESETS,
)

# Stratocaster body generator (GAP-07)
from .stratocaster_body_generator import (
    StratocasterBodyGenerator,
    StratBodySpec,
    StratGCodeStats,
    generate_strat_body,
)
from .stratocaster_config import (
    PickupConfig,
    StratToolConfig,
    StratMachineConfig,
    STRAT_TOOLS,
    STRAT_MACHINES,
    STRAT_BODY_DIMS,
    NECK_POCKET,
    SINGLE_COIL_CAVITY,
    HUMBUCKER_CAVITY,
    TREMOLO_CAVITY,
    SPRING_CAVITY,
    CONTROL_CAVITY,
)


# Unified body generator dispatcher (GEN-1)
from .body_generator import (
    BodyGenerator,
    ELECTRIC_MODELS,
    ACOUSTIC_MODELS,
)

__all__ = [
    # Unified dispatcher (GEN-1)
    'BodyGenerator',
    'ELECTRIC_MODELS',
    'ACOUSTIC_MODELS',
    # Body (Les Paul / DXF-based)
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
    # Bezier body (parametric acoustic)
    'BezierBodyParams',
    'BezierBodyGenerator',
    'ControlPoints',
    'cubic_bezier',
    'get_body_preset',
    'list_body_presets',
    'BODY_PRESETS',
    # Stratocaster body (GAP-07)
    'StratocasterBodyGenerator',
    'StratBodySpec',
    'StratGCodeStats',
    'generate_strat_body',
    'PickupConfig',
    'StratToolConfig',
    'StratMachineConfig',
    'STRAT_TOOLS',
    'STRAT_MACHINES',
    'STRAT_BODY_DIMS',
    'NECK_POCKET',
    'SINGLE_COIL_CAVITY',
    'HUMBUCKER_CAVITY',
    'TREMOLO_CAVITY',
    'SPRING_CAVITY',
    'CONTROL_CAVITY',
]
