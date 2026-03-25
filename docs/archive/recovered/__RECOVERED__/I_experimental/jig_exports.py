from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse

from app.api.routes.rosette_patterns import ROSETTE_PATTERNS_DB
from app.core.jig_pdf_renderer import render_jig_template_pdf
from app.core.jig_template import build_jig_template

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/jig-template.json")
def export_jig_json(body: dict):
    pattern = ROSETTE_PATTERNS_DB.get(body.get("pattern_id"))
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    jig = build_jig_template(
        pattern=pattern,
        guitars=int(body.get("guitars", 1)),
        tile_length_mm=float(body.get("tile_length_mm", 8.0)),
        scrap_factor=float(body.get("scrap_factor", 0.12)),
    )

    filename = f"jig_template__{pattern.id}__g{body.get('guitars', 1)}.json"
    return JSONResponse(
        content=jig,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/jig-template.pdf")
def export_jig_pdf(body: dict):
    pattern = ROSETTE_PATTERNS_DB.get(body.get("pattern_id"))
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    jig = build_jig_template(
        pattern=pattern,
        guitars=int(body.get("guitars", 1)),
        tile_length_mm=float(body.get("tile_length_mm", 8.0)),
        scrap_factor=float(body.get("scrap_factor", 0.12)),
    )

    try:
        pdf_bytes = render_jig_template_pdf(jig)
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    filename = f"jig_template__{pattern.id}__g{body.get('guitars', 1)}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
