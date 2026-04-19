"""
BACKEND-002: Rosette design dimension sheet → PDF.

POST /api/export/rosette-pdf
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["export", "rosette"])


class RosettePdfRequest(BaseModel):
    design: Dict[str, Any] = Field(
        ...,
        description="Rosette state: dimensions, segments, template/material metadata.",
    )
    bom: Optional[Dict[str, Any]] = Field(
        None,
        description="Bill of materials: map of item name to quantity or detail.",
    )
    title: str = "Rosette Design"
    include_bom: bool = True
    include_measurements: bool = True


def _derive_bom_from_design(design: Dict[str, Any]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for seg in design.get("segments") or []:
        if not isinstance(seg, dict):
            continue
        m = str(seg.get("material", "unknown"))
        counts[m] = counts.get(m, 0) + 1
    return counts


def _make_rosette_diagram(dimensions: Dict[str, Any]) -> Any:
    from reportlab.graphics.shapes import Circle, Drawing, String
    from reportlab.lib import colors

    w, h = 280, 160
    d = Drawing(w, h)
    cx, cy = w / 2, h / 2
    try:
        sd = float(dimensions.get("soundholeDiameter", 100))
        rw = float(dimensions.get("rosetteWidth", 20))
    except (TypeError, ValueError):
        sd, rw = 100.0, 20.0
    inner_r = sd / 2
    outer_r = inner_r + rw
    scale = min(65 / max(outer_r, 1e-6), 2.5)
    d.add(
        String(
            10,
            h - 18,
            "Schematic (not to manufacturing scale)",
            fontSize=8,
            fillColor=colors.grey,
        )
    )
    d.add(
        Circle(
            cx,
            cy,
            outer_r * scale,
            fillColor=None,
            strokeColor=colors.HexColor("#333333"),
            strokeWidth=1.2,
        )
    )
    d.add(
        Circle(
            cx,
            cy,
            inner_r * scale,
            fillColor=None,
            strokeColor=colors.HexColor("#666666"),
            strokeWidth=1,
        )
    )
    d.add(
        String(
            cx - 40,
            cy - 4,
            f"Ø{sd:.0f} mm soundhole",
            fontSize=8,
            fillColor=colors.black,
        )
    )
    return d


def build_rosette_pdf(req: RosettePdfRequest) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="reportlab is required for PDF export: pip install reportlab",
        ) from e

    class DrawingFlowable(Flowable):
        """Embed a reportlab.graphics.shapes.Drawing in the story."""

        def __init__(self, drawing: Any) -> None:
            super().__init__()
            self.drawing = drawing
            self.width = float(drawing.width)
            self.height = float(drawing.height)

        def draw(self) -> None:
            from reportlab.graphics import renderPDF

            renderPDF.draw(self.drawing, self.canv, 0, 0)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title=req.title)
    styles = getSampleStyleSheet()
    story: List[Any] = []

    story.append(Paragraph(req.title, styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            f"<i>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</i>",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 12))

    meta_bits: List[str] = []
    st = req.design.get("selectedTemplate")
    if st:
        meta_bits.append(f"Template: <b>{st}</b>")
    sm = req.design.get("selectedMaterial")
    if sm:
        meta_bits.append(f"Primary material: <b>{sm}</b>")
    if meta_bits:
        story.append(Paragraph(" &nbsp;|&nbsp; ".join(meta_bits), styles["Normal"]))
        story.append(Spacer(1, 10))

    dim = req.design.get("dimensions") or {}
    story.append(Paragraph("<b>Diagram</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(
        DrawingFlowable(_make_rosette_diagram(dim if isinstance(dim, dict) else {}))
    )
    story.append(Spacer(1, 14))

    if req.include_measurements:
        story.append(Paragraph("<b>Measurements</b>", styles["Heading2"]))
        story.append(Spacer(1, 6))
        rows = [["Parameter", "Value"]]
        rows.append(["Soundhole diameter (mm)", str(dim.get("soundholeDiameter", "—"))])
        rows.append(["Rosette width (mm)", str(dim.get("rosetteWidth", "—"))])
        rows.append(["Channel depth (mm)", str(dim.get("channelDepth", "—"))])
        rows.append(["Radial segments", str(dim.get("symmetryCount", "—"))])
        mt = Table(rows, colWidths=[220, 120])
        mt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(mt)
        story.append(Spacer(1, 14))

    bom_data: Dict[str, Any] = {}
    if req.include_bom:
        bom_data = req.bom if req.bom is not None else _derive_bom_from_design(req.design)
        if bom_data:
            story.append(Paragraph("<b>Bill of materials</b>", styles["Heading2"]))
            story.append(Spacer(1, 6))
            brow = [["Material / item", "Qty / notes"]]
            for k, v in bom_data.items():
                brow.append([str(k), str(v)])
            bt = Table(brow, colWidths=[220, 120])
            bt.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(bt)

    doc.build(story)
    return buf.getvalue()


@router.post("/rosette-pdf", response_class=StreamingResponse)
def export_rosette_pdf(req: RosettePdfRequest) -> StreamingResponse:
    """Generate a printable rosette design sheet (PDF)."""
    try:
        pdf_bytes = build_rosette_pdf(req)
    except HTTPException:
        raise
    except Exception as e:  # audited: http-500 — ValueError,IOError
        raise HTTPException(status_code=422, detail=f"PDF build error: {e}") from e

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="rosette-design.pdf"'},
    )
