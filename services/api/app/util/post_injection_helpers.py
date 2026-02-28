# services/api/app/util/post_injection_helpers.py
"""
Post-processor injection helpers (compatibility wrapper for N10 routers).

Fixed 2026-02-27: Now correctly imports from post_injection_dropin.py
instead of the deleted post_injection_helpers.py.
"""
from __future__ import annotations

from typing import Any, Dict

from starlette.responses import Response

# Import from the actual drop-in module (not the deleted helpers file)
from ..post_injection_dropin import (
    build_post_context,
    set_post_headers,
)

HAS_HELPERS = True


def build_post_context_v2(**kwargs) -> Dict[str, Any]:
    """
    Build post context from keyword arguments.

    Common keys:
        post, post_mode ('auto'|'off'|'force'), units,
        TOOL, DIAM, FEED_XY, FEED_Z, RPM, SAFE_Z, WORK_OFFSET, PROGRAM_NO, machine_id

    Returns:
        Dict with non-None values for middleware processing.
    """
    return build_post_context(**kwargs)


def wrap_with_post_v2(response: Response, ctx: Dict[str, Any]) -> Response:
    """
    Set post headers on response for middleware processing.

    The PostInjectionMiddleware will read these headers and inject
    appropriate header/footer into G-code responses.

    Args:
        response: Starlette Response object
        ctx: Post context dict from build_post_context_v2()

    Returns:
        Response with X-TB-Post-Context header set
    """
    set_post_headers(response, ctx)
    return response


# Quick context builders (tiered parameter extraction)

def quick_context_basic(post: str = None, units: str = "mm", tool_d: float = None,
                        feed_xy: float = None) -> Dict[str, Any]:
    """
    Extract basic post context.

    Usage:
        ctx = quick_context_basic(post="GRBL", units="mm", tool_d=6.0, feed_xy=1200)
        wrap_with_post_v2(resp, ctx)
    """
    return build_post_context(
        post=post,
        units=units,
        DIAM=tool_d,
        FEED_XY=feed_xy,
    )


def quick_context_standard(
    post: str = None,
    post_mode: str = "auto",
    units: str = "mm",
    tool_d: float = None,
    feed_xy: float = None,
    feed_z: float = None,
    spindle_rpm: float = None,
    safe_z: float = 5.0,
) -> Dict[str, Any]:
    """
    Extract standard post context including tool, feeds, safe Z, and spindle RPM.
    """
    return build_post_context(
        post=post,
        post_mode=post_mode,
        units=units,
        DIAM=tool_d,
        FEED_XY=feed_xy,
        FEED_Z=feed_z,
        RPM=spindle_rpm,
        SAFE_Z=safe_z,
    )


def quick_context_rich(
    post: str = None,
    post_mode: str = "auto",
    units: str = "mm",
    tool_number: int = None,
    tool_d: float = None,
    feed_xy: float = None,
    feed_z: float = None,
    spindle_rpm: float = None,
    safe_z: float = 5.0,
    work_offset: str = None,
    program_no: int = None,
    machine_id: str = None,
) -> Dict[str, Any]:
    """
    Extract rich post context with all available token fields.
    """
    return build_post_context(
        post=post,
        post_mode=post_mode,
        units=units,
        TOOL=tool_number,
        DIAM=tool_d,
        FEED_XY=feed_xy,
        FEED_Z=feed_z,
        RPM=spindle_rpm,
        SAFE_Z=safe_z,
        WORK_OFFSET=work_offset,
        PROGRAM_NO=program_no,
        machine_id=machine_id,
    )


__all__ = [
    'build_post_context_v2',
    'wrap_with_post_v2',
    'quick_context_basic',
    'quick_context_standard',
    'quick_context_rich',
    'HAS_HELPERS',
]
