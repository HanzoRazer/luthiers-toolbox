"""
Art Studio v15.5 Smoke Test Router

Automated testing endpoint that validates all 4 post-processor presets
by generating G-code for a standard test contour.

GET /api/cam_gcode/smoke/posts
Returns: {"ok": bool, "results": {...}, "errors": [...]}
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from .cam_post_v155_router import V155Req, post_v155

router = APIRouter(prefix="/api/cam_gcode", tags=["cam_gcode"])

@router.get("/smoke/posts")
def smoke_posts() -> Dict[str, Any]:
    """
    Smoke test all v15.5 post-processor presets.
    
    Tests each preset (GRBL, Mach3, Haas, Marlin) with a standard contour:
    - 60x25mm rectangle
    - 1mm depth cut
    - Tangent lead-in (3mm)
    - Corner smoothing (0.3mm fillet)
    
    Returns:
        Dict with:
        - ok: True if all presets generated non-empty G-code
        - results: Per-preset status and byte count
        - errors: List of failure messages
    
    Example:
        GET /api/cam_gcode/smoke/posts
        => {"ok": true, "results": {"GRBL": {"ok": true, "bytes": 547}, ...}, "errors": []}
    """
    presets: List[str] = ["GRBL", "Mach3", "Haas", "Marlin"]
    contour = [(0.0, 0.0), (60.0, 0.0), (60.0, 25.0), (0.0, 25.0), (0.0, 0.0)]
    results = {}
    errors = []
    
    for name in presets:
        try:
            req = V155Req(
                contour=contour,
                z_cut_mm=-1.0,
                feed_mm_min=600.0,
                plane_z_mm=5.0,
                preset=name,
                lead_type="tangent",
                lead_len_mm=3.0,
                lead_arc_radius_mm=2.0,
                crc_mode="none",
                fillet_radius_mm=0.3,
                fillet_angle_min_deg=15.0,
            )
            out = post_v155(req)
            g = (out or {}).get("gcode", "").strip()
            results[name] = {"ok": bool(g), "bytes": len(g)}
            if not g:
                errors.append(f"{name}: empty gcode")
        except (ValueError, TypeError, KeyError) as e:  # WP-1: narrowed from except Exception
            results[name] = {"ok": False, "error": str(e)}
            errors.append(f"{name}: {e}")
    
    return {"ok": len(errors) == 0, "results": results, "errors": errors}
