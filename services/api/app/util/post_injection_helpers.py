# services/api/app/util/post_injection_helpers.py
"""
Post-processor injection helpers (compatibility wrapper for N10 routers).
Wraps existing post_injection_helpers.py functions.
"""

try:
    from ..post_injection_helpers import (
        build_post_context_all as build_post_context_v2,
        wrap_with_post_all as wrap_with_post_v2
    )
    HAS_HELPERS = True
except ImportError:
    # Fallback: No post-processor support
    HAS_HELPERS = False
    
    def build_post_context_v2(**kwargs):
        """Fallback: Return empty context"""
        return kwargs
    
    def wrap_with_post_v2(response, ctx):
        """Fallback: Return response unchanged"""
        return response

__all__ = ['build_post_context_v2', 'wrap_with_post_v2', 'HAS_HELPERS']
