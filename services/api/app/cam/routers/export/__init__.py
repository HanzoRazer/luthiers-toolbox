"""
CAM Export Routers

SVG, post-processor, and DXF export operations.

Migrated from:
    - routers/cam_svg_v160_router.py   → svg_router (proxy)
    - routers/cam_post_v155_router.py  → post_router (proxy)
    - routers/cam_dxf_adaptive_router.py → dxf_router (proxy)

Note: Proxies to existing routers until full migration.
"""

from fastapi import APIRouter

# Proxy imports from existing routers (transitional)
try:
    from ....routers.cam_svg_v160_router import router as svg_router
except ImportError:
    svg_router = None

try:
    from ....routers.cam_post_v155_router import router as post_router
except ImportError:
    post_router = None

try:
    from ....routers.cam_dxf_adaptive_router import router as dxf_router
except ImportError:
    dxf_router = None

# Aggregate all export routers
router = APIRouter()

if svg_router:
    router.include_router(svg_router, prefix="/svg")
if post_router:
    router.include_router(post_router, prefix="/post")
if dxf_router:
    router.include_router(dxf_router, prefix="/dxf")

__all__ = ["router"]
