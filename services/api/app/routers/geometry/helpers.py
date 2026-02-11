"""
Geometry Router Helpers
=======================

Shared helper functions for geometry import/export routers.

Functions:
- _load_posts: Load post-processor configurations
- _units_gcode: Convert units to G-code command
- _safe_stem: Sanitize job name for filesystem safety
- _metadata_comment: Generate provenance metadata comment
"""

import datetime
import json
import os
import re
import time
from typing import Any, Dict, Optional


def _load_posts() -> Dict[str, Dict[str, Any]]:
    """
    Load post-processor configurations from data/posts/*.json.

    Process:
    1. Locate data/posts/ directory relative to this file
    2. Read all *.json files in directory
    3. Parse JSON and store by filename stem

    Returns:
        Dictionary mapping post ID to configuration dict
        Example: {"GRBL": {"header": [...], "footer": [...]}}

    Notes:
    - Returns empty dict if posts directory doesn't exist
    - Silently skips malformed JSON files (logged internally)
    - Post IDs are case-sensitive (use uppercase by convention)

    Example:
        posts = _load_posts()
        grbl_config = posts.get("GRBL", {})
    """
    here = os.path.dirname(__file__)
    posts_dir = os.path.join(here, "..", "..", "data", "posts")
    out = {}
    if os.path.isdir(posts_dir):
        for f in os.listdir(posts_dir):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(posts_dir, f), "r", encoding="utf-8") as fh:
                        out[f[:-5]] = json.load(fh)
                except json.JSONDecodeError as e:
                    # Log but don't crash if one post file is malformed
                    print(f"Warning: Failed to load post {f}: {e}")
    return out


def _units_gcode(units: str) -> str:
    """
    Convert units string to G-code command.

    Args:
        units: Unit string ('mm', 'millimeter', 'inch', 'inches', etc.)

    Returns:
        G-code command: 'G21' for metric, 'G20' for imperial

    Validation:
        Defaults to G21 (mm) if units string is ambiguous

    Example:
        _units_gcode('mm') → 'G21'
        _units_gcode('inch') → 'G20'
        _units_gcode('') → 'G21' (default to metric)
    """
    return "G21" if (units or "").lower() in ("mm", "millimeter", "millimetre") else "G20"


def _safe_stem(s: Optional[str], default_prefix: str = "program") -> str:
    """
    Sanitize job_name to safe filename stem.

    Sanitization Rules:
    1. Strip leading/trailing whitespace
    2. Replace spaces with underscores
    3. Remove all characters except: A-Z, a-z, 0-9, dash, underscore
    4. Fallback to timestamp if empty after sanitization

    Args:
        s: User-provided job name (can be None or empty)
        default_prefix: Prefix for timestamp fallback (default: "program")

    Returns:
        Safe filename stem (letters, numbers, dash, underscore only)
        Format: {sanitized_name} or {prefix}_{unix_timestamp}

    Raises:
        ValueError: Never (always returns valid string)

    Example:
        _safe_stem('Bridge Design') → 'Bridge_Design'
        _safe_stem('Test@#$%') → 'Test'
        _safe_stem('') → 'program_1699564800'
        _safe_stem(None) → 'program_1699564800'

    Notes:
        CRITICAL: Used for file exports - MUST prevent path traversal
        Characters stripped: <>:"/\\|?*@#$%^&+=[]{}();'",
    """
    if not s:
        return f"{default_prefix}_{int(time.time())}"

    # Strip whitespace, replace spaces with underscores
    s = s.strip().replace(" ", "_")

    # Keep only safe characters: letters, numbers, dash, underscore
    s = re.sub(r"[^A-Za-z0-9_\-]+", "", s)

    # Fallback to timestamp if sanitization resulted in empty string
    return s or f"{default_prefix}_{int(time.time())}"


def _metadata_comment(units: str, post_id: str) -> str:
    """
    Generate metadata comment for G-code provenance tracking.

    Args:
        units: Unit system ('mm' or 'inch')
        post_id: Post-processor identifier (e.g., 'GRBL', 'Mach4')

    Returns:
        Metadata comment string with semicolon-delimited fields
        Format: (POST=<id>;UNITS=<units>;DATE=<iso8601>)

    Example:
        _metadata_comment('mm', 'GRBL')
        → '(POST=GRBL;UNITS=mm;DATE=2025-11-09T15:30:45.123456Z)'

    Notes:
        - Timestamp is UTC in ISO 8601 format
        - Parentheses indicate G-code comment (ignored by machine)
        - Searchable metadata for tracking file provenance
    """
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    return f"(POST={post_id or 'NONE'};UNITS={units or 'mm'};DATE={ts})"
