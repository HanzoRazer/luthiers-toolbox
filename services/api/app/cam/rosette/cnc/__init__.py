# Patch N14.0 - RMOS Rosette CNC core skeleton
# Rosette Consolidation: absorbed micro-files into receiver modules
#
# This package defines the CNC toolchain interfaces for RMOS Studio.
# Implementations are intentionally simple placeholders; N14.x patches
# will flesh out real kerf physics, safety checks, and G-code output.

# Tool models + material types (absorbed cnc_blade_model + cnc_feed_table)
from .cnc_materials import (
    SawBladeModel,
    RouterBitModel,
    ToolMode,
    MaterialType,
    BasicFeedRule,
    select_basic_feed_rule,
    HARDWOOD_RULE,
    SOFTWOOD_RULE,
    COMPOSITE_RULE,
)
# Jig geometry (kept separate to avoid circular imports)
from .cnc_jig_geometry import (
    JigAlignment,
    MachineEnvelope,
)
# Kerf physics (absorbed into safety validator)
from .cnc_safety_validator import (
    KerfPhysicsResult,
    compute_kerf_physics,
    CNCSafetyDecision,
    evaluate_cnc_safety,
)
# Toolpaths
from .cnc_toolpath import (
    ToolpathSegment,
    ToolpathPlan,
    build_linear_toolpaths,
)
# Export bundle + simulation (absorbed cnc_simulation)
from .cnc_exporter import (
    CNCExportBundle,
    build_export_bundle_skeleton,
    CNCSimulationResult,
    simulate_toolpaths,
)
from .cnc_ring_toolpath import (
    build_ring_arc_toolpaths,
    build_ring_arc_toolpaths_multipass,
)
from .cnc_gcode_exporter import (
    MachineProfile,
    GCodePostConfig,
    generate_gcode_from_toolpaths,
)
from .cnc_materials import (
    FeedRule as MaterialFeedRule,
    select_feed_rule as select_material_feed_rule,
)
from .cnc_machine_profiles import (
    MachineConfig,
    get_machine_config,
    list_machine_configs,
)

# Backward compatibility aliases (absorbed from cnc_feed_table)
FeedRule = BasicFeedRule
select_feed_rule = select_basic_feed_rule

__all__ = [
    # Tool models (absorbed from cnc_blade_model)
    "SawBladeModel",
    "RouterBitModel",
    "ToolMode",
    # Jig geometry
    "JigAlignment",
    "MachineEnvelope",
    # Kerf physics (absorbed from cnc_kerf_physics)
    "KerfPhysicsResult",
    "compute_kerf_physics",
    # Material types (absorbed from cnc_feed_table)
    "MaterialType",
    "BasicFeedRule",
    "select_basic_feed_rule",
    "FeedRule",  # alias for BasicFeedRule (backward compat)
    "select_feed_rule",  # alias for select_basic_feed_rule (backward compat)
    "HARDWOOD_RULE",
    "SOFTWOOD_RULE",
    "COMPOSITE_RULE",
    # Toolpaths
    "ToolpathSegment",
    "ToolpathPlan",
    "build_linear_toolpaths",
    # Safety
    "CNCSafetyDecision",
    "evaluate_cnc_safety",
    # Export + simulation (absorbed from cnc_simulation)
    "CNCExportBundle",
    "build_export_bundle_skeleton",
    "CNCSimulationResult",
    "simulate_toolpaths",
    # N16.0 - Ring Toolpath Geometry Core
    "build_ring_arc_toolpaths",
    # N16.2 - Multi-pass Z stepping
    "build_ring_arc_toolpaths_multipass",
    # N16.3 - G-code skeleton generator
    "generate_gcode_from_toolpaths",
    # N16.5 - Machine profiles
    "MachineProfile",
    "GCodePostConfig",
    # N16.4 - Material-specific presets (extended feed rules)
    "MaterialFeedRule",
    "select_material_feed_rule",
    # N16.7 - Hardware-tuned machine profiles
    "MachineConfig",
    "get_machine_config",
    "list_machine_configs",
]
