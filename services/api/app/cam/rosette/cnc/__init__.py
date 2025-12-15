# Patch N14.0 - RMOS Rosette CNC core skeleton
#
# This package defines the CNC toolchain interfaces for RMOS Studio.
# Implementations are intentionally simple placeholders; N14.x patches
# will flesh out real kerf physics, safety checks, and G-code output.

from .cnc_blade_model import (
    SawBladeModel,
    RouterBitModel,
)
from .cnc_jig_geometry import (
    JigAlignment,
    MachineEnvelope,
)
from .cnc_kerf_physics import (
    KerfPhysicsResult,
    compute_kerf_physics,
)
from .cnc_feed_table import (
    MaterialType,
    FeedRule,
    select_feed_rule,
)
from .cnc_toolpath import (
    ToolpathSegment,
    ToolpathPlan,
    build_linear_toolpaths,
)
from .cnc_safety_validator import (
    CNCSafetyDecision,
    evaluate_cnc_safety,
)
from .cnc_exporter import (
    CNCExportBundle,
    build_export_bundle_skeleton,
)
from .cnc_simulation import (
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

__all__ = [
    "SawBladeModel",
    "RouterBitModel",
    "JigAlignment",
    "MachineEnvelope",
    "KerfPhysicsResult",
    "compute_kerf_physics",
    "MaterialType",
    "FeedRule",
    "select_feed_rule",
    "ToolpathSegment",
    "ToolpathPlan",
    "build_linear_toolpaths",
    "CNCSafetyDecision",
    "evaluate_cnc_safety",
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
    # N16.4 - Material-specific presets
    "MaterialFeedRule",
    "select_material_feed_rule",
    # N16.7 - Hardware-tuned machine profiles
    "MachineConfig",
    "get_machine_config",
    "list_machine_configs",
]
