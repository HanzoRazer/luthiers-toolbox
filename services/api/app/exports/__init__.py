"""
DXF/SVG Export Package for Luthier's Tool Box API
Provides utilities for generating DXF files and export history tracking.
Migrated from legacy ./server directory.
"""

from .dxf_helpers import (
    write_polyline_ascii,
    write_arc_ascii,
    build_ascii_r12,
    try_build_with_ezdxf,
    angle_between_points,
    distance_between_points,
)

from .curvemath_biarc import (
    biarc_entities,
    biarc_point_at_t,
    biarc_length,
)

from .history_store import (
    start_entry,
    write_file,
    write_text,
    finalize,
    list_entries,
    read_meta,
    file_bytes,
    get_units,
    get_version,
    get_git_sha,
)

__all__ = [
    "write_polyline_ascii",
    "write_arc_ascii",
    "build_ascii_r12",
    "try_build_with_ezdxf",
    "angle_between_points",
    "distance_between_points",
    "biarc_entities",
    "biarc_point_at_t",
    "biarc_length",
    "start_entry",
    "write_file",
    "write_text",
    "finalize",
    "list_entries",
    "read_meta",
    "file_bytes",
    "get_units",
    "get_version",
    "get_git_sha",
]
