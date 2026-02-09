# services/api/app/post_injection_helpers.py
# Patch N 0.4c — Post Injection Helper Utilities
"""================================================================================"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
from starlette.responses import Response

# Import from drop-in module
from .post_injection_dropin import (
    build_post_context,
    set_post_headers,
    _find_post,
    _load_posts
)


# ============================================================================
# QUICK CONTEXT BUILDERS (TIERED PARAMETER EXTRACTION)
# ============================================================================

def quick_context_basic(body: BaseModel) -> Dict[str, Any]:
    """
    Extract basic post context from any Pydantic model.
    Looks for common field names: post, units, tool_d, feed_xy.
    
    Usage:
        ctx = quick_context_basic(body)
        set_post_headers(resp, ctx)
    """
    return build_post_context(
        post=getattr(body, 'post', None),
        units=getattr(body, 'units', 'mm'),
        DIAM=getattr(body, 'tool_d', None) or getattr(body, 'tool_diameter', None),
        FEED_XY=getattr(body, 'feed_xy', None)
    )


def quick_context_standard(body: BaseModel) -> Dict[str, Any]:
    """
    Extract standard post context from any Pydantic model.
    Includes tool, feeds, safe Z, and spindle RPM.
    
    Usage:
        ctx = quick_context_standard(body)
        set_post_headers(resp, ctx)
    """
    return build_post_context(
        post=getattr(body, 'post', None),
        post_mode=getattr(body, 'post_mode', 'auto'),
        units=getattr(body, 'units', 'mm'),
        DIAM=getattr(body, 'tool_d', None) or getattr(body, 'tool_diameter', None),
        FEED_XY=getattr(body, 'feed_xy', None),
        FEED_Z=getattr(body, 'feed_z', None),
        RPM=getattr(body, 'spindle_rpm', None) or getattr(body, 'rpm', None),
        SAFE_Z=getattr(body, 'safe_z', 5.0)
    )


def quick_context_rich(body: BaseModel) -> Dict[str, Any]:
    """
    Extract rich post context from any Pydantic model.
    Includes all available token fields.
    
    Usage:
        ctx = quick_context_rich(body)
        set_post_headers(resp, ctx)
    """
    return build_post_context(
        post=getattr(body, 'post', None),
        post_mode=getattr(body, 'post_mode', 'auto'),
        units=getattr(body, 'units', 'mm'),
        TOOL=getattr(body, 'tool_number', None) or getattr(body, 'tool', None),
        DIAM=getattr(body, 'tool_d', None) or getattr(body, 'tool_diameter', None),
        FEED_XY=getattr(body, 'feed_xy', None),
        FEED_Z=getattr(body, 'feed_z', None),
        RPM=getattr(body, 'spindle_rpm', None) or getattr(body, 'rpm', None),
        SAFE_Z=getattr(body, 'safe_z', 5.0),
        WORK_OFFSET=getattr(body, 'work_offset', None),
        PROGRAM_NO=getattr(body, 'program_no', None),
        machine_id=getattr(body, 'machine_id', None)
    )


# ============================================================================
# Response Builders
# ============================================================================

def build_post_response(
    gcode: str,
    body: BaseModel,
    context_level: str = "standard"
) -> Response:
    """Build Response with automatic context extraction."""
    # Choose context builder
    if context_level == "basic":
        ctx = quick_context_basic(body)
    elif context_level == "rich":
        ctx = quick_context_rich(body)
    else:  # standard
        ctx = quick_context_standard(body)
    
    # Build response
    resp = Response(content=gcode, media_type="text/plain; charset=utf-8")
    set_post_headers(resp, ctx)
    return resp


def build_post_response_custom(
    gcode: str,
    **context_fields
) -> Response:
    """Build Response with explicit context fields."""
    ctx = build_post_context(**context_fields)
    resp = Response(content=gcode, media_type="text/plain; charset=utf-8")
    set_post_headers(resp, ctx)
    return resp


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_post_exists(post_id: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Check if post-processor exists."""
    if not post_id:
        return True, None  # No post specified is OK
    
    post = _find_post(post_id)
    if not post:
        return False, f"Post-processor '{post_id}' not found"
    
    return True, None


def validate_post_compatible(
    post_id: Optional[str],
    requires_arcs: bool = False,
    requires_tool_changer: bool = False
) -> Tuple[bool, List[str]]:
    """Check if post-processor is compatible with operation requirements."""
    if not post_id:
        return True, []
    
    post = _find_post(post_id)
    if not post:
        return False, [f"Post '{post_id}' not found"]
    
    warnings = []
    
    # Check arc support
    if requires_arcs:
        metadata = post.get('metadata', {})
        supports_arcs = metadata.get('supports_arcs', True)
        if not supports_arcs:
            warnings.append(f"Post '{post_id}' may not support G2/G3 arcs")
    
    # Check tool changer
    if requires_tool_changer:
        metadata = post.get('metadata', {})
        has_tool_changer = metadata.get('has_tool_changer', False)
        if not has_tool_changer:
            warnings.append(f"Post '{post_id}' does not support tool changes")
    
    return len(warnings) == 0, warnings


# ============================================================================
# Post Information Queries
# ============================================================================

def list_available_posts() -> List[Dict[str, Any]]:
    """
    Get list of all available post-processors.
    
    Returns:
        List of post configs with id, title, controller
    
    Usage:
        posts = list_available_posts()
        print(f"Available posts: {[p['id'] for p in posts]}")
    """
    posts = _load_posts()
    return [
        {
            'id': p.get('id'),
            'title': p.get('title', p.get('name', p.get('id'))),
            'controller': p.get('controller', 'Unknown')
        }
        for p in posts
    ]


def get_post_info(post_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a post-processor."""
    return _find_post(post_id)


def get_post_tokens(post_id: str) -> List[str]:
    """
    Extract all token placeholders from a post config.
    
    Returns:
        List of token names (e.g., ['DATE', 'UNITS', 'DIAM'])
    
    Usage:
        tokens = get_post_tokens("grbl")
        print(f"Post uses tokens: {tokens}")
    """
    import re
    
    post = _find_post(post_id)
    if not post:
        return []
    
    tokens = set()
    pattern = r'\{([A-Z_]+)\}'
    
    for line in post.get('header', []):
        matches = re.findall(pattern, line)
        tokens.update(matches)
    
    for line in post.get('footer', []):
        matches = re.findall(pattern, line)
        tokens.update(matches)
    
    return sorted(tokens)


# ============================================================================
# Decorator for Automatic Post Integration
# ============================================================================

def with_post_injection(context_level: str = "standard"):
    """Decorator to automatically add post injection to a router function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Call original function
            result = func(*args, **kwargs)
            
            # If already a Response, return as-is
            if isinstance(result, Response):
                return result
            
            # If string, wrap with post context
            if isinstance(result, str):
                # Try to extract body from args/kwargs
                body = None
                for arg in args:
                    if isinstance(arg, BaseModel):
                        body = arg
                        break
                if not body:
                    for v in kwargs.values():
                        if isinstance(v, BaseModel):
                            body = v
                            break
                
                if body:
                    return build_post_response(result, body, context_level)
                else:
                    # No body found, return plain response
                    return Response(content=result, media_type="text/plain")
            
            # Unknown return type, return as-is
            return result
        
        return wrapper
    return decorator


# ============================================================================
# Filename Helpers
# ============================================================================

def build_gcode_filename(
    operation: str,
    post_id: Optional[str] = None,
    units: str = "mm",
    extension: str = "nc"
) -> str:
    """Generate standard G-code filename."""
    parts = [operation]
    
    if post_id:
        parts.append(post_id.lower())
    else:
        parts.append("raw")
    
    if units:
        parts.append(units.lower())
    
    return f"{'_'.join(parts)}.{extension}"


def build_content_disposition(
    operation: str,
    post_id: Optional[str] = None,
    units: str = "mm"
) -> str:
    """
    Generate Content-Disposition header for file download.
    
    Usage:
        headers = {
            "Content-Disposition": build_content_disposition("roughing", "grbl", "mm")
        }
        return Response(content=gcode, headers=headers, media_type="text/plain")
    """
    filename = build_gcode_filename(operation, post_id, units)
    return f'attachment; filename="{filename}"'


# ============================================================================
# Common Schema Mixins
# ============================================================================

class PostMixin(BaseModel):
    """
    Mixin for post-processor fields (basic).
    
    Usage:
        class MyOperationIn(PostMixin):
            tool_d: float
            feed_xy: float
    """
    post: Optional[str] = None
    units: str = "mm"


class PostRichMixin(BaseModel):
    """
    Mixin for post-processor fields (rich tokens).
    
    Usage:
        class MyOperationIn(PostRichMixin):
            tool_d: float
            feed_xy: float
    """
    post: Optional[str] = None
    post_mode: str = "auto"
    units: str = "mm"
    tool_number: Optional[str] = None
    spindle_rpm: Optional[float] = None
    safe_z: float = 5.0
    work_offset: Optional[str] = None
    program_no: Optional[str] = None
    machine_id: Optional[str] = None


# ============================================================================
# Testing Helpers
# ============================================================================

def mock_post_context(
    post: str = "grbl",
    units: str = "mm",
    **overrides
) -> Dict[str, Any]:
    """
    Create mock post context for testing.
    
    Usage:
        ctx = mock_post_context("linuxcnc", DIAM=6.0, FEED_XY=1200)
    """
    defaults = {
        'post': post,
        'units': units,
        'DIAM': 6.0,
        'FEED_XY': 1200,
        'RPM': 18000,
        'SAFE_Z': 5.0
    }
    defaults.update(overrides)
    return build_post_context(**defaults)


def verify_post_injection(gcode: str, post_id: str) -> bool:
    """
    Verify that G-code has been post-processed.
    
    Returns:
        True if post headers/footers detected
    
    Usage:
        gcode = export_operation(body)
        assert verify_post_injection(gcode, "grbl")
    """
    post = _find_post(post_id)
    if not post:
        return False
    
    # Check for at least one header line
    header = post.get('header', [])
    if header and len(header) > 0:
        # Check if first header line appears in gcode
        first_line = header[0]
        if first_line in gcode:
            return True
    
    # Check for at least one footer line
    footer = post.get('footer', [])
    if footer and len(footer) > 0:
        # Check if last footer line appears in gcode
        last_line = footer[-1]
        if last_line in gcode:
            return True
    
    return False


# ============================================================================
# Example Usage
# ============================================================================

"""
Example 1: Quick Context (Minimal Code)
----------------------------------------
from .post_injection_helpers import quick_context_standard, build_post_response

@router.post("/operation_gcode")
def export_operation(body: OperationIn):
    gcode = generate_moves(body)
    return build_post_response(gcode, body, "standard")


Example 2: Validation Before Export
------------------------------------
from .post_injection_helpers import validate_post_exists, build_post_response
from fastapi import HTTPException

@router.post("/operation_gcode")
def export_operation(body: OperationIn):
    # Validate post exists
    exists, error = validate_post_exists(body.post)
    if not exists:
        raise HTTPException(404, error)
    
    gcode = generate_moves(body)
    return build_post_response(gcode, body, "standard")


Example 3: Custom Filename
---------------------------
from .post_injection_helpers import build_post_response, build_content_disposition

@router.post("/operation_gcode")
def export_operation(body: OperationIn):
    gcode = generate_moves(body)
    resp = build_post_response(gcode, body, "standard")
    resp.headers["Content-Disposition"] = build_content_disposition(
        "roughing", body.post, body.units
    )
    return resp


Example 4: Using Decorator
---------------------------
from .post_injection_helpers import with_post_injection

@router.post("/operation_gcode")
@with_post_injection("standard")
def export_operation(body: OperationIn):
    gcode = generate_moves(body)
    return gcode  # Decorator handles Response wrapping


Example 5: Schema with Mixin
-----------------------------
from .post_injection_helpers import PostRichMixin

class OperationIn(PostRichMixin):
    tool_d: float
    feed_xy: float
    paths: List[Dict]
    # Inherits: post, post_mode, units, tool_number, spindle_rpm, etc.


Example 6: Testing
------------------
from .post_injection_helpers import verify_post_injection

def test_export_with_post():
    body = OperationIn(tool_d=6.0, feed_xy=1200, post="grbl")
    result = export_operation(body)
    gcode = result.body.decode()
    assert verify_post_injection(gcode, "grbl")
"""
