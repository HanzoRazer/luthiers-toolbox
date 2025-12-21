"""
Compare Automation Router

SVG comparison automation for CLI and batch operations.

Migrated from:
    - routers/compare_automation_router.py

Endpoints:
    POST /run    - Compare two SVG images
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Optional

router = APIRouter()

CompareMode = Literal["side-by-side", "overlay", "delta"]


class CompareInput(BaseModel):
    left: dict               # { kind: "svg", value: "<svg...>" }
    right: dict
    mode: CompareMode = "overlay"
    export: List[str] = ["json"]
    zoom_to_diff: bool = True
    include_layers: bool = True


class CompareOutput(BaseModel):
    mode: CompareMode
    result_json: dict = []  # Renamed from 'json' to avoid shadowing BaseModel.json()
    png_data_base64: Optional[str] = None
    warnings: List[str] = []


@router.post("/run", response_model=CompareOutput)
async def run_compare(payload: CompareInput):
    """
    Compare two SVG images. This is the API endpoint used by:
    - CompareLab UI
    - compare_report_cli
    - compare_golden_cli
    """

    # -------------------------------------------------------
    # TODO: Replace with the real compare engine.
    # For now we return a stub that matches expected structure.
    # -------------------------------------------------------

    try:
        result_json = {
            "fullBBox": {"minX": 0, "minY": 0, "maxX": 100, "maxY": 100},
            "diffBBox": {"minX": 10, "minY": 20, "maxX": 80, "maxY": 90},
            "layers": [
                {"id": "layer1", "inLeft": True, "inRight": True},
                {"id": "layer2", "inLeft": True, "inRight": False},
            ],
        }

        png_b64 = None
        if "png" in payload.export:
            # stub; later we can plug in a real PNG renderer
            png_b64 = ""

        return CompareOutput(
            mode=payload.mode,
            result_json=result_json,
            png_data_base64=png_b64,
            warnings=[],
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
