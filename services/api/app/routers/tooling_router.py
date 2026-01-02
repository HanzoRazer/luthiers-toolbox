"""
Tooling and Post-Processor Management Router

Provides endpoints for listing and configuring CNC post-processors used in
multi-machine CAM workflows. Supports 5 platforms: GRBL, Mach4, LinuxCNC,
PathPilot, and MASSO.

Features:
- List all available post-processors with metadata
- Retrieve specific post-processor configuration
- Consistent JSON format for G-code headers and footers
- Case-insensitive post_id matching

Endpoints:
- GET /tooling/posts - List all post-processors
- GET /tooling/posts/{post_id} - Get specific post-processor config

Architecture:
- Post-processor configs stored as JSON files in services/api/app/data/posts/
- Each config defines "header" and "footer" arrays for G-code wrapping
- Loaded on-demand (no caching) for hot-reload support during development

CRITICAL SAFETY RULES:
1. Post-processor IDs are case-insensitive (grbl == GRBL == Grbl)
2. Missing post configs return empty arrays (fail-safe, not error)
3. File I/O errors are logged but don't crash endpoint (graceful degradation)
4. JSON parse errors for individual posts are isolated (one bad file doesn't break all)
5. Always return consistent schema (id, name, title, header, footer)

Example:
    # List all posts
    GET /api/tooling/posts
    => [
        {"id": "grbl", "name": "grbl", "title": "GRBL CNC", "header": [...], "footer": [...]},
        {"id": "mach4", "name": "mach4", "title": "Mach4", "header": [...], "footer": [...]}
    ]
    
    # Get specific post
    GET /api/tooling/posts/GRBL
    => {"id": "grbl", "name": "grbl", "title": "GRBL CNC", "header": [...], "footer": [...]}
"""
import json
import logging
import os
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Note: prefix and tags are set in main.py when registering
router = APIRouter()

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Supported post-processor IDs (lowercase canonical form)
SUPPORTED_POST_IDS: Tuple[str, ...] = ("grbl", "mach4", "linuxcnc", "pathpilot", "masso")

# Maximum post-processor files to scan (prevent directory traversal attacks)
MAX_POST_FILES: int = 50

# =============================================================================
# HELPER FUNCTIONS - POST PROCESSOR LOADING
# =============================================================================

def _load_posts() -> Dict[str, Any]:
    """
    Load post-processor configurations from data/posts/*.json files.
    
    Scans the posts directory and parses each JSON file into a standardized
    post-processor configuration dictionary. Handles missing files, parse errors,
    and malformed configs gracefully.
    
    Returns:
        Dict mapping post_id (lowercase) to config dict with:
        - id: str (lowercase canonical ID)
        - name: str (same as id, for consistency)
        - title: str (human-readable display name)
        - header: List[str] (G-code lines to prepend)
        - footer: List[str] (G-code lines to append)
    
    File Structure Expected:
        services/api/app/data/posts/
        ├── grbl.json
        ├── mach4.json
        ├── linuxcnc.json
        ├── pathpilot.json
        └── masso.json
    
    JSON Format:
        {
          "header": ["G90", "G17", "(Machine: GRBL 1.1)"],
          "footer": ["M30", "(End of program)"]
        }
    
    Algorithm:
        1. Resolve posts directory relative to this router file
        2. Scan directory for *.json files (up to MAX_POST_FILES)
        3. For each file:
           a. Extract post_id from filename (remove .json extension)
           b. Parse JSON with error handling
           c. Build standardized config dict
           d. Store in output dict with lowercase key
        4. Return complete post configs
    
    Error Handling:
        - Missing directory: Returns empty dict (no posts available)
        - JSON parse error: Logs warning, skips file, continues loading others
        - Missing header/footer keys: Uses empty arrays as defaults
        - File count exceeds MAX_POST_FILES: Logs warning, stops scanning
    
    Example:
        >>> posts = _load_posts()
        >>> posts["grbl"]["header"]
        ["G90", "G17", "G91.1", "(GRBL 1.1 - Absolute distance mode)"]
    
    Notes:
        - No caching: Reloads from disk on every call (hot-reload friendly)
        - Case normalization: All keys stored lowercase for consistent lookup
        - Isolation: One bad JSON file doesn't prevent loading others
        - Logging: Parse errors logged at WARNING level for debugging
    
    Side Effects:
        - Reads from filesystem (services/api/app/data/posts/)
        - Logs warnings for malformed or missing configs
    """
    here = os.path.dirname(__file__)
    posts_dir = os.path.join(here, "..", "data", "posts")
    out = {}
    
    if not os.path.isdir(posts_dir):
        logger.warning(f"Posts directory not found: {posts_dir}")
        return out
    
    try:
        files = [f for f in os.listdir(posts_dir) if f.endswith(".json")]
        if len(files) > MAX_POST_FILES:
            logger.warning(f"Posts directory contains {len(files)} files, limiting to {MAX_POST_FILES}")
            files = files[:MAX_POST_FILES]
        
        for f in files:
            post_id = f[:-5]  # Remove .json extension
            post_id_lower = post_id.lower()
            
            try:
                with open(os.path.join(posts_dir, f), "r", encoding="utf-8") as fh:
                    config = json.load(fh)
                    out[post_id_lower] = {
                        "id": post_id_lower,
                        "name": post_id_lower,
                        "title": _post_title(post_id_lower),
                        "header": config.get("header", []),
                        "footer": config.get("footer", [])
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse post config {f}: {e}")
            except Exception as e:
                logger.warning(f"Failed to load post config {f}: {e}")
    
    except Exception as e:
        logger.error(f"Failed to scan posts directory: {e}")
    
    return out


def _post_title(post_id: str) -> str:
    """
    Generate human-readable display title for post-processor ID.
    
    Converts canonical post_id (lowercase) to user-friendly display name
    for UI presentation and logging.
    
    Args:
        post_id: Lowercase post-processor ID (e.g., "grbl", "mach4")
    
    Returns:
        Human-readable title string (e.g., "GRBL CNC", "Mach4")
    
    Mapping:
        - grbl       → "GRBL CNC"
        - mach4      → "Mach4"
        - linuxcnc   → "LinuxCNC (EMC2)"
        - pathpilot  → "Tormach PathPilot"
        - masso      → "MASSO Controller"
        - unknown    → Uppercased ID (fallback)
    
    Example:
        >>> _post_title("grbl")
        "GRBL CNC"
        >>> _post_title("custom_post")
        "CUSTOM_POST"
    
    Notes:
        - Case-insensitive input (always lowercase canonical IDs)
        - Fallback to uppercase for unknown IDs (graceful degradation)
        - No validation (accepts any string, never raises)
    """
    titles = {
        "grbl": "GRBL CNC",
        "mach4": "Mach4",
        "linuxcnc": "LinuxCNC (EMC2)",
        "pathpilot": "Tormach PathPilot",
        "masso": "MASSO Controller"
    }
    return titles.get(post_id.lower(), post_id.upper())

# =============================================================================
# API ENDPOINTS - POST PROCESSOR MANAGEMENT
# =============================================================================

@router.get("/posts")
def list_posts() -> List[Dict[str, Any]]:
    """
    List all available post-processors with their configurations.
    
    Returns array of post-processor objects sorted alphabetically by ID.
    Each object contains full configuration including headers and footers
    for G-code wrapping.
    
    Returns:
        List of post-processor dicts, each with:
        - id: str (lowercase canonical ID)
        - name: str (same as id)
        - title: str (human-readable display name)
        - header: List[str] (G-code initialization lines)
        - footer: List[str] (G-code shutdown lines)
    
    Response Format:
        [
          {
            "id": "grbl",
            "name": "grbl",
            "title": "GRBL CNC",
            "header": ["G90", "G17", "G91.1"],
            "footer": ["M30"]
          },
          {
            "id": "mach4",
            "name": "mach4",
            "title": "Mach4",
            "header": ["G90", "G20", "G17"],
            "footer": ["M30", "M5"]
          }
        ]
    
    Sorting:
        - Alphabetical by lowercase ID
        - Ensures consistent ordering across requests
        - Predictable for UI dropdowns and batch operations
    
    Example:
        GET /api/tooling/posts
        => HTTP 200 with JSON array of 5 post configs
    
    Notes:
        - Reloads from disk on every request (no caching)
        - Returns empty array if posts directory missing
        - Never errors (returns [] on failure, logs warning)
        - All post_ids normalized to lowercase
    
    Use Cases:
        - Populate UI post-processor dropdown
        - Batch export to multiple machines
        - Validation of user-supplied post_id
        - Admin panel for post management
    """
    posts = _load_posts()
    # Sort by id for consistent ordering
    return sorted(posts.values(), key=lambda x: x["id"])


@router.get("/posts/{post_id}")
def get_post(post_id: str) -> Dict[str, Any]:
    """
    Get configuration for a specific post-processor by ID.
    
    Retrieves full configuration including headers and footers for a single
    post-processor. Case-insensitive post_id lookup (GRBL == grbl == Grbl).
    
    Args:
        post_id: Post-processor ID (case-insensitive, e.g., "GRBL", "mach4")
    
    Returns:
        Post-processor config dict with:
        - id: str (lowercase canonical ID)
        - name: str (same as id)
        - title: str (human-readable display name)
        - header: List[str] (G-code initialization lines)
        - footer: List[str] (G-code shutdown lines)
        - error: str (optional, present if post not found)
    
    Response Format (Success):
        {
          "id": "grbl",
          "name": "grbl",
          "title": "GRBL CNC",
          "header": ["G90", "G17", "G91.1", "(GRBL 1.1)"],
          "footer": ["M30", "(End of program)"]
        }
    
    Response Format (Not Found):
        {
          "id": "unknown_post",
          "title": "unknown_post",
          "header": [],
          "footer": [],
          "error": "Post not found"
        }
    
    Case Handling:
        - Input: "GRBL", "grbl", "Grbl", "GrBl" → All resolve to same config
        - Normalization: post_id.lower() for consistent lookup
        - Fallback: Returns empty config with error field (not HTTP 404)
    
    Example (Success):
        GET /api/tooling/posts/GRBL
        => HTTP 200 with full GRBL config
    
    Example (Not Found):
        GET /api/tooling/posts/unknown
        => HTTP 200 with error field (fail-safe, not exception)
    
    Notes:
        - Always returns HTTP 200 (never 404, fail-safe design)
        - Empty arrays for missing posts (safe defaults for G-code wrapping)
        - Case-insensitive lookup prevents user input errors
        - Error field allows UI to show warning without breaking workflow
    
    Use Cases:
        - Preview post-processor config before export
        - Validate post_id from user input
        - Display machine-specific G-code examples
        - Admin panel post editor
    
    Side Effects:
        - Reads from filesystem (services/api/app/data/posts/)
        - Logs warning if post_id not found
    """
    posts = _load_posts()
    post_id_lower = post_id.lower()
    
    if post_id_lower not in posts:
        logger.warning(f"Post processor not found: {post_id}")
        return {
            "id": post_id_lower,
            "title": post_id,
            "header": [],
            "footer": [],
            "error": "Post not found"
        }
    
    return posts[post_id_lower]


# =============================================================================
# PHASE 1: TOOL & MATERIAL LIBRARY ENDPOINTS
# =============================================================================

from app.data.tool_library import (
    load_tool_library,
    get_tool_profile,
    get_material_profile,
)
from app.data.validate_tool_library import validate_library


@router.get("/library/tools", summary="List all tools from JSON library")
def list_library_tools() -> List[Dict[str, Any]]:
    """
    List all tools from the JSON tool library.
    
    Returns lightweight summary for each tool (id, name, type, diameter, flutes).
    Use GET /tooling/library/tools/{tool_id} for full details.
    
    Response Format:
        [
          {"tool_id": "flat_6.0", "name": "...", "type": "flat", "diameter_mm": 6.0, "flutes": 2},
          {"tool_id": "ball_3.0", ...}
        ]
    """
    lib = load_tool_library()
    results = []
    
    for tool_id in lib.list_tool_ids():
        tool = lib.get_tool(tool_id)
        if tool:
            results.append({
                "tool_id": tool.tool_id,
                "name": tool.name,
                "type": tool.tool_type,
                "diameter_mm": tool.diameter_mm,
                "flutes": tool.flutes,
            })
    
    return results


@router.get("/library/tools/{tool_id}", summary="Get tool by ID from JSON library")
def get_library_tool(tool_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific tool from the JSON library.
    
    Args:
        tool_id: Tool identifier (e.g., "flat_6.0", "ball_3.0")
    
    Returns:
        Full tool profile including chipload range.
        Returns error field if tool not found.
    """
    tool = get_tool_profile(tool_id)
    
    if tool is None:
        return {
            "tool_id": tool_id,
            "error": f"Tool not found: {tool_id}"
        }
    
    return {
        "tool_id": tool.tool_id,
        "name": tool.name,
        "type": tool.tool_type,
        "diameter_mm": tool.diameter_mm,
        "flutes": tool.flutes,
        "chipload_mm": {
            "min": tool.chipload_min_mm,
            "max": tool.chipload_max_mm,
        },
    }


@router.get("/library/materials", summary="List all materials from JSON library")
def list_library_materials() -> List[Dict[str, Any]]:
    """
    List all materials from the JSON library.
    
    Returns lightweight summary for each material.
    Use GET /tooling/library/materials/{material_id} for full details.
    """
    lib = load_tool_library()
    results = []
    
    for mat_id in lib.list_material_ids():
        mat = lib.get_material(mat_id)
        if mat:
            results.append({
                "material_id": mat.material_id,
                "name": mat.name,
                "heat_sensitivity": mat.heat_sensitivity,
                "hardness": mat.hardness,
            })
    
    return results


@router.get("/library/materials/{material_id}", summary="Get material by ID from JSON library")
def get_library_material(material_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific material from the JSON library.
    
    Args:
        material_id: Material identifier (e.g., "Ebony", "Hard Maple")
    
    Returns:
        Full material profile including density.
        Returns error field if material not found.
    """
    mat = get_material_profile(material_id)
    
    if mat is None:
        return {
            "material_id": material_id,
            "error": f"Material not found: {material_id}"
        }
    
    return {
        "material_id": mat.material_id,
        "name": mat.name,
        "heat_sensitivity": mat.heat_sensitivity,
        "hardness": mat.hardness,
        "density_kg_m3": mat.density_kg_m3,
    }


@router.get("/library/validate", summary="Validate tool library")
def validate_library_endpoint() -> Dict[str, Any]:
    """
    Validate the JSON tool and material library.
    
    Runs validation rules on all tools and materials.
    Returns validation status and any errors found.
    
    Response Format:
        {
          "valid": true/false,
          "tool_count": 15,
          "material_count": 7,
          "errors": ["tool_id: error message", ...]
        }
    """
    lib = load_tool_library()
    errors = validate_library(lib)
    
    tool_count = len(lib.list_tool_ids())
    material_count = len(lib.list_material_ids())
    
    return {
        "valid": len(errors) == 0,
        "tool_count": tool_count,
        "material_count": material_count,
        "errors": errors,
    }
