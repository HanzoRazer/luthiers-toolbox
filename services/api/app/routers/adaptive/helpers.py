"""
Adaptive Pocketing Helpers
==========================

Shared helper functions for adaptive pocketing routers.

Functions:
- _load_post_profiles: Load post processor configurations
- _merge_adaptive_override: Merge user override with post profile
- _apply_adaptive_feed: Apply adaptive feed translation to moves
- _safe_stem: Sanitize job name for filesystem safety
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Literal, Optional


def _load_post_profiles() -> Dict[str, Dict[str, Any]]:
    """
    Load post processor profiles from JSON configuration file.

    Returns:
        Dictionary mapping profile IDs to profile configurations
        Empty dict if file not found or invalid JSON

    Example:
        >>> profiles = _load_post_profiles()
        >>> 'GRBL' in profiles
        True

    Notes:
        - Profiles located in ../assets/post_profiles.json
        - Fails gracefully by returning empty dict
        - Used for adaptive feed mode configuration
    """
    profile_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "assets", "post_profiles.json"
    )
    try:
        with open(profile_path, "r") as f:
            profiles = json.load(f)
            return {p["id"]: p for p in profiles}
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}


def _merge_adaptive_override(
    post: Dict[str, Any],
    override: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Merge user adaptive feed override with post processor profile.

    Allows runtime override of adaptive feed settings without modifying
    post-processor JSON configuration files. Honors "inherit" mode to
    preserve profile defaults.

    Args:
        post: Post processor profile dictionary
        override: User override dictionary with keys:
            - mode: "comment" | "inline_f" | "mcode" | "inherit"
            - slowdown_threshold: float (0-1)
            - inline_min_f: float (min feed rate in mm/min)
            - mcode_start: str (M-code for zone start)
            - mcode_end: str (M-code for zone end)

    Returns:
        Modified post profile with override applied

    Notes:
        - If override.mode is "inherit" or None, returns post unchanged
        - Only overrides keys present in override dict (partial updates)
        - Original post dict is not modified (creates copy)
    """
    if not override or override.get("mode") in (None, "inherit"):
        return post

    post = post.copy()
    adaptive_feed = (post.get("adaptive_feed") or {}).copy()

    # Explicit mode wins
    adaptive_feed["mode"] = override.get("mode", adaptive_feed.get("mode", "comment"))

    # Merge other keys if present
    for key in ("slowdown_threshold", "inline_min_f", "mcode_start", "mcode_end"):
        if override.get(key) is not None:
            adaptive_feed[key] = override[key]

    post["adaptive_feed"] = adaptive_feed
    return post


def _apply_adaptive_feed(
    moves: List[Dict[str, Any]],
    post: Optional[Dict[str, Any]],
    base_units: Literal["mm", "inch"]
) -> List[str]:
    """
    Apply adaptive feed translation based on post processor profile.

    Transforms move dictionaries with slowdown metadata into G-code lines
    with post-processor-specific feed control. Supports three modes:
    - comment: Emit (FEED_HINT START/END) comments around slowed segments
    - inline_f: Scale F values directly in slowed segments
    - mcode: Emit M-codes at zone boundaries (e.g., LinuxCNC M52 P...)

    Args:
        moves: List of move dictionaries with meta.slowdown from L.2/L.3
               Each move has keys: code, x, y, z, i, j, f, meta
        post: Post processor profile dictionary with adaptive_feed config
              If None, defaults to comment mode
        base_units: "mm" or "inch" (used for unit consistency checks)

    Returns:
        List of G-code lines with adaptive feed applied

    Notes:
        - slowdown_threshold (default 0.95): values below trigger slowdown zone
        - inline_min_f (default 100.0): minimum feed rate in mm/min
        - M-codes configurable via mcode_start/mcode_end (e.g., LinuxCNC M52)
        - Zone boundaries automatically closed if file ends inside zone
    """
    prof = (post or {}).get("adaptive_feed") or {
        "mode": "comment",
        "slowdown_threshold": 0.95
    }
    mode = prof.get("mode", "comment")
    thr = float(prof.get("slowdown_threshold", 0.95))
    inline_min_f = float(prof.get("inline_min_f", 100.0))
    m_start = prof.get("mcode_start", "M200")
    m_end = prof.get("mcode_end", "M201")

    out_lines = []
    in_zone = False

    def line_from_move(m: Dict[str, Any], force_f: Optional[float] = None) -> str:
        """Convert move dictionary to G-code line."""
        code = m["code"]
        parts = [code]
        if "x" in m:
            parts.append(f"X{m['x']:.4f}")
        if "y" in m:
            parts.append(f"Y{m['y']:.4f}")
        if "z" in m:
            parts.append(f"Z{m['z']:.4f}")
        if "i" in m:
            parts.append(f"I{m['i']:.4f}")
        if "j" in m:
            parts.append(f"J{m['j']:.4f}")

        fval = force_f if force_f is not None else m.get("f", None)
        if fval is not None:
            parts.append(f"F{max(inline_min_f, fval):.1f}")

        return " ".join(parts)

    for m in moves:
        slow = float(m.get("meta", {}).get("slowdown", 1.0))
        is_slow = slow < thr and m["code"] in ("G1", "G2", "G3")

        # Zone enter
        if is_slow and not in_zone:
            if mode == "comment":
                out_lines.append(f"(FEED_HINT START scale={slow:.3f})")
            elif mode == "mcode":
                out_lines.append(m_start)
            in_zone = True

        # Zone exit (if not slow now, but was slow)
        if (not is_slow) and in_zone:
            if mode == "comment":
                out_lines.append("(FEED_HINT END)")
            elif mode == "mcode":
                out_lines.append(m_end)
            in_zone = False

        # Generate move line
        if mode == "inline_f" and is_slow:
            # Scale current move feed
            base_f = m.get("f", 1200.0)
            force_f = base_f * slow
            out_lines.append(line_from_move(m, force_f=force_f))
        else:
            out_lines.append(line_from_move(m))

    # If file ends while inside a slow zone, close it
    if in_zone:
        if mode == "comment":
            out_lines.append("(FEED_HINT END)")
        elif mode == "mcode":
            out_lines.append(m_end)

    return out_lines


def _safe_stem(s: Optional[str]) -> str:
    """
    Sanitize job name to safe filename stem.

    Removes unsafe characters and ensures valid filename for cross-platform
    compatibility. Falls back to timestamp-based name if sanitization
    results in empty string.

    Args:
        s: User-provided job name (can be None or empty string)

    Returns:
        Safe filename stem containing only:
        - Letters: A-Z, a-z
        - Numbers: 0-9
        - Dash: -
        - Underscore: _
        Fallback: "pocket_<unix_timestamp>" if input invalid

    Notes:
        - Spaces replaced with underscores before sanitization
        - Leading/trailing whitespace stripped
        - Empty string after sanitization triggers timestamp fallback
    """
    if not s:
        return f"pocket_{int(time.time())}"

    # Strip whitespace, replace spaces with underscores
    s = s.strip().replace(" ", "_")

    # Keep only safe characters: letters, numbers, dash, underscore
    s = re.sub(r"[^A-Za-z0-9_\-]+", "", s)

    # Fallback to timestamp if sanitization resulted in empty string
    return s or f"pocket_{int(time.time())}"


# Allowed adaptive feed modes (validated in batch export)
ALLOWED_MODES = ("comment", "inline_f", "mcode")
