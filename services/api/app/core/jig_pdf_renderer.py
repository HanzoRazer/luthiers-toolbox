from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    canvas = None  # type: ignore[assignment]
    letter = None  # type: ignore[assignment]


def _require_reportlab() -> None:
    if canvas is None or letter is None:
        raise RuntimeError(
            "PDF export requires reportlab. Install it via `pip install reportlab`."
        )


def render_jig_template_pdf(jig: Dict[str, Any]) -> bytes:
    _require_reportlab()

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    y = height - 48
    line_height = 14

    def draw(text: str, bold: bool = False) -> None:
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 11 if bold else 10)
        c.drawString(48, y, text)
        y -= line_height
        if y < 72:
            c.showPage()
            y = height - 48

    draw("Rosette Jig Template", bold=True)
    draw(f"Pattern: {jig['pattern_name']} ({jig['pattern_id']})")
    draw(f"Guitars: {jig.get('guitars', 1)}")
    draw(f"Tile length (mm): {jig.get('tile_length_mm', 'n/a')}")
    draw(f"Scrap factor: {jig.get('scrap_factor', 'n/a')}")
    draw(f"Center (mm): ({jig.get('base_center_x_mm', 0)}, {jig.get('base_center_y_mm', 0)})")
    draw("")

    draw("Ring Specs", bold=True)
    for ring in jig.get("rings", []):
        draw(
            "Ring {idx} | Family {fam} | R={radius:.2f}mm | W={width:.2f}mm | Circ={circ:.1f}mm | TileL={tile:.2f}mm | Tiles/Gtr={tpg} | Angle={angle:.1f}deg".format(
                idx=ring["ring_index"],
                fam=ring["strip_family_id"],
                radius=ring["radius_mm"],
                width=ring["width_mm"],
                circ=ring["circumference_mm"],
                tile=ring["tile_length_mm"],
                tpg=ring["tiles_per_guitar"],
                angle=ring["slice_angle_deg"],
            )
        )

    draw("")
    draw(
        f"Total tiles (incl. scrap): {jig.get('total_tiles_all_rings', 0)}",
        bold=True,
    )

    if jig.get("notes"):
        draw("")
        draw("Notes", bold=True)
        for line in str(jig["notes"]).splitlines():
            draw(line)

    c.save()
    return buf.getvalue()
