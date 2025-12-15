"""
Rosette Design Sheet API Router (MM-3)

API endpoint to generate and download PDF design sheets for rosettes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...core.rosette_design_sheet import generate_rosette_design_sheet
from ...stores.rmos_stores import get_rmos_stores


router = APIRouter(prefix="/rmos/design-sheet", tags=["RMOS", "Design Sheets"])


def _get_plan(plan_id: str) -> Dict[str, Any]:
    """
    Get plan from store.
    TODO: Wire to your actual plan store when available.
    For now, returns a stub error.
    """
    # Example implementation when plan store is available:
    # stores = get_rmos_stores()
    # plan = stores.rosette_plans.get(plan_id)
    # if not plan:
    #     raise KeyError(f"Plan '{plan_id}' not found")
    # return plan
    
    raise KeyError("Plan store not wired; implement _get_plan(plan_id) when plan persistence is ready.")


@router.get("/{plan_id}/{strip_family_id}")
def download_design_sheet(plan_id: str, strip_family_id: str):
    """
    Generate and return a design sheet PDF for the given plan + strip family.
    
    Args:
        plan_id: Rosette plan ID
        strip_family_id: Strip family ID from MM-0
    
    Returns:
        FileResponse with PDF attachment
    
    Note: Wire _get_plan() to your real rosette plan store before enabling.
          Currently returns 501 Not Implemented until plan store is ready.
    """
    # Get plan (currently returns error until store is wired)
    try:
        plan = _get_plan(plan_id)
    except KeyError as e:
        # Return 501 instead of 404 since feature is not fully implemented
        raise HTTPException(
            status_code=501, 
            detail=f"Plan store not implemented yet. {str(e)}"
        )

    # Get strip family
    stores = get_rmos_stores()
    strip_family_raw = stores.strip_families.get(strip_family_id)
    if not strip_family_raw:
        raise HTTPException(
            status_code=404, 
            detail=f"Strip family '{strip_family_id}' not found."
        )
    
    strip_family = strip_family_raw if isinstance(strip_family_raw, dict) else strip_family_raw.__dict__

    # Optional: machine defaults could come from config or machine profile store
    machine_defaults: Dict[str, Any] = {
        # "spindle_rpm": 18000,
        # "feed_rate_mm_min": 1200,
        # "plunge_rate_mm_min": 400,
        # "stepdown_mm": 0.6,
    }

    # Generate PDF
    out_dir = Path("data") / "rmos" / "design_sheets"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"designsheet_{plan_id}_{strip_family_id}.pdf"
    out_path = out_dir / filename

    pdf_path = generate_rosette_design_sheet(plan, strip_family, machine_defaults, out_path)
    
    return FileResponse(
        path=str(pdf_path),
        filename=filename,
        media_type="application/pdf",
    )
