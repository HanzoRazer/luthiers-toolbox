from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:  # pragma: no cover  # WP-1: narrowed from except Exception
    canvas = None  # type: ignore[assignment]
    letter = None  # type: ignore[assignment]


def _require_reportlab() -> None:
    if canvas is None or letter is None:
        raise RuntimeError(
            "PDF export requires reportlab. Install it via `pip install reportlab`."
        )


def render_manufacturing_plan_pdf(plan: Dict[str, Any]) -> bytes:
    """Render a ManufacturingPlan dict into a printable PDF."""
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

    draw("Rosette Manufacturing Plan", bold=True)
    draw(f"Pattern: {plan['pattern']['name']} ({plan['pattern']['id']})")
    draw(f"Guitars: {plan.get('guitars', 1)}")
    draw(f"Tile length (mm): {plan.get('tile_length_mm', 'n/a')}")
    draw(f"Scrap factor: {plan.get('scrap_factor', 'n/a')}")
    draw("")

    draw("Per-Ring Requirements", bold=True)
    for ring in plan.get("ring_requirements", []):
        draw(
            "Ring {idx} | Family {fam} | Circ {circ:.1f} mm | Tiles/gtr {tpg} | Total {total}".format(
                idx=ring["ring_index"],
                fam=ring["strip_family_id"],
                circ=ring["circumference_mm"],
                tpg=ring["tiles_per_guitar"],
                total=ring["total_tiles"],
            )
        )
    draw("")

    draw("Per-Strip Family Plan", bold=True)
    for fam in plan.get("strip_plans", []):
        draw(
            "{fam_id} | Tiles {tiles} | Len {length:.2f} m | Sticks {sticks}".format(
                fam_id=fam["strip_family_id"],
                tiles=fam["total_tiles_needed"],
                length=fam["total_strip_length_m"],
                sticks=fam["sticks_needed"],
            )
        )

    if plan.get("notes"):
        draw("")
        draw("Notes", bold=True)
        for line in str(plan["notes"]).splitlines():
            draw(line)

    c.save()
    return buf.getvalue()
