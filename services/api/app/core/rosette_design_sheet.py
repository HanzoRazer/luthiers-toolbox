"""
Rosette Design Sheet Generator (MM-3)

Generates PDF design sheets for mixed-material rosettes with:
- Plan summary (segments, arcs, lines)
- Strip family composition (materials + CAM profiles)
- CAM summary (feed range, fragility, lane hints)
- Machine defaults (optional)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    HAVE_REPORTLAB = True
except ImportError:
    HAVE_REPORTLAB = False

from ..core.cam_profile_registry import summarize_profiles_for_family
from ..schemas.strip_family import StripFamily


def _safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safe dict getter with default."""
    v = d.get(key)
    return v if v is not None else default


def _format_material_line(m: Dict[str, Any], idx: int) -> str:
    """Format a material as a table row string."""
    t = m.get("type", "unknown")
    species = m.get("species", "")
    thick = m.get("thickness_mm", "")
    finish = m.get("finish", "")
    cam_prof = m.get("cam_profile", "")
    return f"{idx+1:02d}  {t:8s}  {species:16s}  {thick!s:>5s}  {finish:12s}  {cam_prof:14s}"


def _format_cam_summary_line(summary: Dict[str, Any]) -> List[str]:
    """Format CAM summary as list of strings."""
    prof_ids = ", ".join(summary.get("profile_ids") or [])
    min_feed = summary.get("min_feed_rate_mm_min")
    max_feed = summary.get("max_feed_rate_mm_min")
    frag = summary.get("worst_fragility_score")
    lane = summary.get("dominant_lane_hint")
    line1 = f"Profiles        : {prof_ids or '—'}"
    line2 = f"Feed range      : {min_feed or '—'} – {max_feed or '—'} mm/min"
    line3 = f"Worst fragility : {frag if frag is not None else '—'}"
    line4 = f"Lane hint       : {lane or '—'}"
    return [line1, line2, line3, line4]


def _extract_basic_plan_info(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Extract basic plan info for display."""
    segs = plan.get("segments") or []
    arcs = [s for s in segs if s.get("type") in ("arc", "circle")]
    lines = [s for s in segs if s.get("type") == "line"]
    return {
        "segment_count": len(segs),
        "arc_count": len(arcs),
        "line_count": len(lines),
        "name": plan.get("name") or plan.get("id") or "Unnamed rosette plan",
        "id": plan.get("id") or "",
    }


def generate_rosette_design_sheet(
    plan: Dict[str, Any],
    strip_family: Dict[str, Any],
    machine_defaults: Optional[Dict[str, Any]],
    output_pdf: Path,
) -> Path:
    """
    Generate a PDF design sheet summarizing:
      - rosette plan
      - mixed-material strip family
      - inferred CAM profile summaries
      - machine defaults (optional)
    
    Args:
        plan: Rosette plan dict with segments
        strip_family: Strip family dict from MM-0
        machine_defaults: Optional machine parameters (spindle_rpm, feed_rate, etc.)
        output_pdf: Output path (will be suffixed with .pdf)
    
    Returns:
        Path to the generated PDF (or text stub if reportlab missing)
    """
    output_pdf = output_pdf.with_suffix(".pdf")
    summary = summarize_profiles_for_family(strip_family)
    plan_info = _extract_basic_plan_info(plan)

    if not HAVE_REPORTLAB:
        # Fallback: simple text file with .pdf extension to avoid breaking callers
        # You can customize this to generate HTML instead.
        output_pdf.write_text(_build_text_fallback(plan_info, strip_family, summary, machine_defaults or {}))
        return output_pdf

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_pdf), pagesize=A4)
    width, height = A4
    margin = 15 * mm
    y = height - margin

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Rosette Design Sheet")
    y -= 12 * mm

    c.setFont("Helvetica", 9)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    c.drawString(margin, y, f"Generated: {now_str}")
    y -= 5 * mm

    # Plan info
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Plan")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, f"Name       : {plan_info['name']}")
    y -= 4 * mm
    c.drawString(margin, y, f"Plan ID    : {plan_info['id']}")
    y -= 4 * mm
    c.drawString(margin, y, f"Segments   : {plan_info['segment_count']} (arcs: {plan_info['arc_count']}, lines: {plan_info['line_count']})")
    y -= 8 * mm

    # Strip family basic info
    sf = StripFamily(**strip_family)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Strip Family")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, f"ID         : {sf.id}")
    y -= 4 * mm
    c.drawString(margin, y, f"Name       : {sf.name}")
    y -= 4 * mm
    if sf.default_width_mm is not None:
        c.drawString(margin, y, f"Default width: {sf.default_width_mm} mm")
        y -= 4 * mm
    if sf.description:
        c.drawString(margin, y, f"Description: {sf.description[:80]}")
        y -= 4 * mm
    if sf.notes:
        c.drawString(margin, y, f"Notes      : {sf.notes[:80]}")
        y -= 6 * mm

    # Materials table
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Materials")
    y -= 5 * mm
    c.setFont("Helvetica", 8)
    c.drawString(margin, y, "Idx  Type      Species           Thk   Finish        CAM profile")
    y -= 4 * mm
    c.setStrokeColor(colors.black)
    c.line(margin, y, width - margin, y)
    y -= 3 * mm

    for idx, m in enumerate(strip_family.get("materials") or []):
        line = _format_material_line(m, idx)
        if y < margin + 40:
            c.showPage()
            y = height - margin
            c.setFont("Helvetica", 8)
        c.drawString(margin, y, line)
        y -= 4 * mm

    y -= 6 * mm

    # CAM summary
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "CAM summary (inferred from materials)")
    y -= 5 * mm
    c.setFont("Helvetica", 8)
    for line in _format_cam_summary_line(summary):
        c.drawString(margin, y, line)
        y -= 4 * mm

    y -= 4 * mm

    # Machine defaults (if provided)
    if machine_defaults:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, "Machine defaults")
        y -= 5 * mm
        c.setFont("Helvetica", 8)
        for key in ("spindle_rpm", "feed_rate_mm_min", "plunge_rate_mm_min", "stepdown_mm"):
            val = machine_defaults.get(key)
            c.drawString(margin, y, f"{key:18s}: {val if val is not None else '—'}")
            y -= 4 * mm

    c.showPage()
    c.save()
    return output_pdf


def _build_text_fallback(
    plan_info: Dict[str, Any],
    strip_family: Dict[str, Any],
    summary: Dict[str, Any],
    machine_defaults: Dict[str, Any],
) -> str:
    """Build text fallback when reportlab is not available."""
    sf = StripFamily(**strip_family)
    lines = []
    lines.append("Rosette Design Sheet (text fallback)")
    lines.append("------------------------------------")
    lines.append("")
    lines.append("[Plan]")
    lines.append(f"  Name     : {plan_info['name']}")
    lines.append(f"  Plan ID  : {plan_info['id']}")
    lines.append(
        f"  Segments : {plan_info['segment_count']} (arcs: {plan_info['arc_count']}, lines: {plan_info['line_count']})"
    )
    lines.append("")
    lines.append("[Strip Family]")
    lines.append(f"  ID        : {sf.id}")
    lines.append(f"  Name      : {sf.name}")
    if sf.default_width_mm is not None:
        lines.append(f"  Width mm  : {sf.default_width_mm}")
    if sf.description:
        lines.append(f"  Desc      : {sf.description}")
    if sf.notes:
        lines.append(f"  Notes     : {sf.notes}")
    lines.append("")
    lines.append("[Materials]")
    for idx, m in enumerate(strip_family.get("materials") or []):
        lines.append("  " + _format_material_line(m, idx))
    lines.append("")
    lines.append("[CAM summary]")
    lines.extend("  " + s for s in _format_cam_summary_line(summary))
    if machine_defaults:
        lines.append("")
        lines.append("[Machine defaults]")
        for k, v in machine_defaults.items():
            lines.append(f"  {k:18s}: {v}")
    lines.append("")
    return "\n".join(lines)
