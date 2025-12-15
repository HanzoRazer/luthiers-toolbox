# services/api/app/cam/dxf_limits.py
"""
DXF Processing Limits

Centralized constants for DXF processing guards.
Import these wherever DXF files are processed.

Security patch addressing:
- Missing file size limits (memory overflow)
- Unbounded recursion (stack overflow)
- O(n²) deduplication (CPU exhaustion)
- No operation timeouts (hung requests)
"""

from typing import Final


# =============================================================================
# FILE SIZE LIMITS
# =============================================================================

MAX_DXF_FILE_SIZE_BYTES: Final[int] = 15 * 1024 * 1024  # 15 MB (user-specified)
MAX_DXF_FILE_SIZE_MB: Final[float] = MAX_DXF_FILE_SIZE_BYTES / (1024 * 1024)

# Enterprise tier limits (4x standard)
ENTERPRISE_MAX_DXF_FILE_SIZE_BYTES: Final[int] = 50 * 1024 * 1024  # 50 MB


# =============================================================================
# ENTITY/GEOMETRY LIMITS
# =============================================================================

# Maximum DXF entities after parse (lines, arcs, polylines, etc.)
MAX_DXF_ENTITIES: Final[int] = 50_000

# Enterprise tier entity limit (4x standard)
ENTERPRISE_MAX_DXF_ENTITIES: Final[int] = 200_000

# Maximum unique points after deduplication
MAX_DXF_POINTS: Final[int] = 100_000

# Maximum edges in adjacency graph
MAX_DXF_EDGES: Final[int] = 100_000


# =============================================================================
# PROCESSING LIMITS
# =============================================================================

# Maximum path depth for iterative DFS (prevents infinite loops)
MAX_RECURSION_DEPTH: Final[int] = 500

# Maximum iterations in cycle search (prevents CPU exhaustion)
MAX_CYCLE_SEARCH_ITERATIONS: Final[int] = 1_000_000

# Timeout for geometry operations (seconds)
OPERATION_TIMEOUT_SECONDS: Final[float] = 30.0


# =============================================================================
# SPATIAL HASH SETTINGS
# =============================================================================

# Grid cell size for O(n) point deduplication
# Smaller = more precise but more cells
# 0.1mm is good for typical CNC tolerance (0.01mm)
SPATIAL_HASH_CELL_SIZE_MM: Final[float] = 0.1
