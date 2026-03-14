"""Post-Processor Management Router.

Provides:
- GET /posts - List all post-processors
- GET /posts/{post_id} - Get post-processor by ID

LANE: UTILITY (machine configuration)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Post Processors", "Tooling"])

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
    post-processor configuration dictionary.

    Returns:
        Dict mapping post_id (lowercase) to config dict with:
        - id: str (lowercase canonical ID)
        - name: str (same as id, for consistency)
        - title: str (human-readable display name)
        - header: List[str] (G-code lines to prepend)
        - footer: List[str] (G-code lines to append)
    """
    here = os.path.dirname(__file__)
    posts_dir = os.path.join(here, "..", "..", "data", "posts")
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
            except (OSError, KeyError, TypeError) as e:  # WP-1: per-file load fallback
                logger.warning(f"Failed to load post config {f}: {e}")

    except OSError as e:  # WP-1: directory scan fallback
        logger.error(f"Failed to scan posts directory: {e}")

    return out


def _post_title(post_id: str) -> str:
    """Generate human-readable display title for post-processor ID."""
    titles = {
        "grbl": "GRBL CNC",
        "mach4": "Mach4",
        "linuxcnc": "LinuxCNC (EMC2)",
        "pathpilot": "Tormach PathPilot",
        "masso": "MASSO Controller"
    }
    return titles.get(post_id.lower(), post_id.upper())


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/posts", summary="List post-processors")
def list_posts() -> List[Dict[str, Any]]:
    """
    List all available post-processors with their configurations.

    Returns array of post-processor objects sorted alphabetically by ID.
    """
    posts = _load_posts()
    return sorted(posts.values(), key=lambda x: x["id"])


@router.get("/posts/{post_id}", summary="Get post-processor by ID")
def get_post(post_id: str) -> Dict[str, Any]:
    """
    Get configuration for a specific post-processor by ID.

    Case-insensitive lookup (GRBL == grbl == Grbl).
    Returns error field if post not found (fail-safe, not HTTP 404).
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


__all__ = ["router", "SUPPORTED_POST_IDS", "_load_posts", "_post_title"]
