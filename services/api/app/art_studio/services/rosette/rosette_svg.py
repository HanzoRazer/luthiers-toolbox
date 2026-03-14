"""
Rosette SVG — Preview and drafting mode rendering.

SVG generation for rosette wheel preview, including patterns, extension tabs,
guide circles, radial lines, and optional drafting annotations.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.art_studio.schemas.rosette_designer import RING_DEFS

from .rosette_geometry import _fmt, _pt_on_circle, arc_cell_path, tab_path
from .rosette_design import get_tile_fill


# ─────────────────────────────────────────────────────────────────────────────
# SVG Pattern Definitions
# ─────────────────────────────────────────────────────────────────────────────

_SVG_DEFS = """
<linearGradient id="g-abalone" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#6ae0d0"/><stop offset="28%" stop-color="#50c8e8"/>
  <stop offset="55%" stop-color="#8860d0"/><stop offset="78%" stop-color="#50e890"/>
  <stop offset="100%" stop-color="#60b8e8"/>
</linearGradient>
<pattern id="pat-abalone" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">
  <rect width="28" height="28" fill="url(#g-abalone)" opacity="0.88"/>
  <ellipse cx="9" cy="9" rx="7" ry="4" fill="rgba(255,255,255,0.18)" transform="rotate(-30,9,9)"/>
  <ellipse cx="20" cy="20" rx="5" ry="3" fill="rgba(255,255,255,0.12)" transform="rotate(20,20,20)"/>
</pattern>
<linearGradient id="g-mop" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#f0f0ee"/><stop offset="45%" stop-color="#e8ddf8"/>
  <stop offset="100%" stop-color="#d8f0ee"/>
</linearGradient>
<pattern id="pat-mop" x="0" y="0" width="18" height="18" patternUnits="userSpaceOnUse">
  <rect width="18" height="18" fill="url(#g-mop)"/>
  <line x1="0" y1="9" x2="18" y2="9" stroke="rgba(200,190,220,0.28)" stroke-width="0.5"/>
  <line x1="9" y1="0" x2="9" y2="18" stroke="rgba(200,190,220,0.2)" stroke-width="0.5"/>
</pattern>
<pattern id="pat-burl" x="0" y="0" width="22" height="15" patternUnits="userSpaceOnUse">
  <rect width="22" height="15" fill="#C8A048"/>
  <ellipse cx="6" cy="7" rx="4.5" ry="2.5" fill="none" stroke="#a07828" stroke-width="1" opacity="0.55"/>
  <ellipse cx="15" cy="5" rx="3.5" ry="2" fill="none" stroke="#b09030" stroke-width="0.8" opacity="0.5"/>
</pattern>
<pattern id="pat-herringbone" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
  <rect width="20" height="20" fill="#C09850"/>
  <line x1="-2" y1="12" x2="8" y2="-2" stroke="#7a5c28" stroke-width="2.8"/>
  <line x1="2" y1="16" x2="14" y2="-2" stroke="#7a5c28" stroke-width="2.8"/>
  <line x1="7" y1="20" x2="20" y2="4" stroke="#7a5c28" stroke-width="2.8"/>
  <line x1="10" y1="-2" x2="22" y2="14" stroke="#5a3c10" stroke-width="2.8"/>
  <line x1="5" y1="-2" x2="20" y2="16" stroke="#5a3c10" stroke-width="2.8"/>
  <line x1="-2" y1="4" x2="12" y2="20" stroke="#5a3c10" stroke-width="2.8"/>
</pattern>
<pattern id="pat-checker" x="0" y="0" width="14" height="14" patternUnits="userSpaceOnUse">
  <rect width="14" height="14" fill="#f0e8d8"/>
  <rect x="0" y="0" width="7" height="7" fill="#1a1a1a"/>
  <rect x="7" y="7" width="7" height="7" fill="#1a1a1a"/>
</pattern>
<pattern id="pat-celtic" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
  <rect width="24" height="24" fill="#1a3a2a"/>
  <path d="M4,4 Q12,12 20,4 Q12,0 4,4Z" fill="none" stroke="#50c880" stroke-width="2" opacity="0.8"/>
  <path d="M4,20 Q12,12 20,20 Q12,24 4,20Z" fill="none" stroke="#50c880" stroke-width="2" opacity="0.8"/>
  <circle cx="12" cy="12" r="3" fill="none" stroke="#50c880" stroke-width="1.5"/>
</pattern>
<pattern id="pat-diagonal" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
  <rect width="12" height="12" fill="#c8922a"/>
  <line x1="-2" y1="10" x2="10" y2="-2" stroke="#8B5a10" stroke-width="3.5"/>
  <line x1="4" y1="14" x2="14" y2="4" stroke="#8B5a10" stroke-width="3.5"/>
</pattern>
<pattern id="pat-dots" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
  <rect width="12" height="12" fill="#f5e6c8"/>
  <circle cx="6" cy="6" r="2.4" fill="#1a1a1a"/>
</pattern>
<pattern id="pat-bwb" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
  <rect x="0" y="0" width="9" height="3" fill="#111"/>
  <rect x="0" y="3" width="9" height="3" fill="#eee"/>
  <rect x="0" y="6" width="9" height="3" fill="#111"/>
</pattern>
<pattern id="pat-rbr" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
  <rect x="0" y="0" width="9" height="3" fill="#cc0033"/>
  <rect x="0" y="3" width="9" height="3" fill="#111"/>
  <rect x="0" y="6" width="9" height="3" fill="#cc0033"/>
</pattern>
<pattern id="pat-wbw" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
  <rect x="0" y="0" width="9" height="3" fill="#eee"/>
  <rect x="0" y="3" width="9" height="3" fill="#111"/>
  <rect x="0" y="6" width="9" height="3" fill="#eee"/>
</pattern>
<radialGradient id="g-soundhole" cx="50%" cy="50%" r="50%">
  <stop offset="0%" stop-color="#060402"/>
  <stop offset="100%" stop-color="#0d0905"/>
</radialGradient>"""


# ─────────────────────────────────────────────────────────────────────────────
# Preview Rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_preview_svg(
    num_segs: int,
    grid: Dict[str, str],
    ring_active: List[bool],
    show_tabs: bool = True,
    show_annotations: bool = False,
    width: int = 620,
    height: int = 620,
) -> str:
    """Render a full SVG preview of the rosette wheel."""
    cx = width / 2
    cy = height / 2
    seg_ang = 360.0 / num_segs
    parts: List[str] = []

    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append(f"<defs>{_SVG_DEFS}</defs>")

    # Background
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="354" fill="none" '
                 f'stroke="rgba(200,146,42,0.12)" stroke-width="8"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="148" fill="url(#g-soundhole)" '
                 f'stroke="rgba(200,146,42,0.45)" stroke-width="1.2"/>')

    # Ring backgrounds
    for ri, rd in enumerate(RING_DEFS):
        bg_fill = (("#12282e" if ri == 2 else rd.color)
                   if ring_active[ri] else "rgba(20,18,14,0.5)")
        opacity = 1 if ring_active[ri] else 0.35
        d = arc_cell_path(cx, cy, rd.r1, rd.r2, 0, 359.999)
        parts.append(f'<path d="{d}" fill="{bg_fill}" stroke="none" opacity="{opacity}"/>')

    # Cells
    for ri, rd in enumerate(RING_DEFS):
        for si in range(num_segs):
            a1 = si * seg_ang
            a2 = (si + 1) * seg_ang
            key = f"{ri}-{si}"
            d = arc_cell_path(cx, cy, rd.r1, rd.r2, a1, a2)
            fill = get_tile_fill(grid.get(key, "")) if key in grid else "none"
            parts.append(f'<path d="{d}" fill="{fill}"/>')

    # Extension tabs
    if show_tabs:
        for ri, rd in enumerate(RING_DEFS):
            if not rd.has_tabs or not ring_active[ri]:
                continue
            half_aw = rd.tab_ang_width / 2
            for si in range(num_segs):
                mid = (si + 0.5) * seg_ang
                tile_id = grid.get(f"{ri}-{si}", "")
                if tile_id:
                    fill = get_tile_fill(tile_id)
                else:
                    fill = rd.tab_fill_even if si % 2 == 0 else rd.tab_fill_odd
                # Outer tab
                d_outer = tab_path(cx, cy, rd.r2, rd.tab_outer_r, mid, half_aw)
                parts.append(f'<path d="{d_outer}" fill="{fill}" stroke="#1a1a2e" '
                             f'stroke-width="0.7" opacity="0.92"/>')
                # Inner tab
                d_inner = tab_path(cx, cy, rd.tab_inner_r, rd.r1, mid, half_aw)
                parts.append(f'<path d="{d_inner}" fill="{fill}" stroke="#1a1a2e" '
                             f'stroke-width="0.7" opacity="0.85"/>')

    # Guide circles and radial lines
    for r in [150, 190, 200, 210, 300, 312, 320, 350]:
        is_tab = r in (200, 312)
        stroke = "rgba(200,146,42,0.18)" if is_tab else "rgba(200,146,42,0.38)"
        sw = 0.4 if is_tab else 0.7
        dash = 'stroke-dasharray="2,3"' if is_tab else ""
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                     f'stroke="{stroke}" stroke-width="{sw}" {dash}/>')
    for si in range(num_segs):
        angle = si * seg_ang
        x1, y1 = _pt_on_circle(cx, cy, 150, angle)
        x2, y2 = _pt_on_circle(cx, cy, 350, angle)
        parts.append(f'<line x1="{_fmt(x1)}" y1="{_fmt(y1)}" x2="{_fmt(x2)}" '
                     f'y2="{_fmt(y2)}" stroke="rgba(200,146,42,0.28)" stroke-width="0.55"/>')

    # Center crosshair
    parts.append(f'<line x1="{cx-14}" y1="{cy}" x2="{cx+14}" y2="{cy}" '
                 f'stroke="rgba(200,146,42,0.55)" stroke-width="0.8" stroke-dasharray="2,2"/>')
    parts.append(f'<line x1="{cx}" y1="{cy-14}" x2="{cx}" y2="{cy+14}" '
                 f'stroke="rgba(200,146,42,0.55)" stroke-width="0.8" stroke-dasharray="2,2"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="none" '
                 f'stroke="rgba(200,146,42,0.55)" stroke-width="0.8"/>')

    # Annotation layer (drafting mode)
    if show_annotations:
        parts.append(_build_annotations_svg(cx, cy, num_segs, seg_ang))

    parts.append("</svg>")
    return "\n".join(parts)


def _build_annotations_svg(cx: float, cy: float, num_segs: int, seg_ang: float) -> str:
    """Build the drafting annotation overlay SVG group."""
    ds = "#1a1a2e"
    lines: List[str] = []
    lines.append(f'<rect x="0" y="0" width="{int(cx*2)}" height="{int(cy*2)}" '
                 f'fill="#f5f0e8" opacity="0.85"/>')
    # Diameter dimensions
    for r, label in [(350, 'Ø 7.00"'), (300, 'Ø 6.00"'), (150, 'Ø 3.00"')]:
        y_line = cy - r - 15 if r > 200 else cy + 20
        lines.append(f'<line x1="{_fmt(cx - r)}" y1="{_fmt(y_line)}" '
                     f'x2="{_fmt(cx + r)}" y2="{_fmt(y_line)}" '
                     f'stroke="{ds}" stroke-width="0.7" fill="none"/>')
        lines.append(f'<text x="{_fmt(cx)}" y="{_fmt(y_line - 5)}" fill="{ds}" '
                     f'font-family="monospace" font-size="8" text-anchor="middle">{label}</text>')

    # Zone labels
    zones = [
        (335, "Outer Binding 0.30\""), (310, "Outer Purfling 0.20\""),
        (255, "Main Channel 0.90\""), (200, "Inner Purfling 0.20\""),
        (170, "Soundhole Bind 0.40\""),
    ]
    lx = cx + 160
    for i, (r, label) in enumerate(zones):
        px, py = _pt_on_circle(cx, cy, r, 75)
        ly = cy - 140 + i * 40
        lines.append(f'<line x1="{_fmt(px)}" y1="{_fmt(py)}" '
                     f'x2="{_fmt(lx)}" y2="{_fmt(ly)}" '
                     f'stroke="{ds}" stroke-width="0.55" fill="none"/>')
        lines.append(f'<text x="{_fmt(lx + 4)}" y="{_fmt(ly + 3)}" fill="{ds}" '
                     f'font-family="monospace" font-size="7.5">{label}</text>')

    # Segment count label
    lines.append(f'<text x="{_fmt(cx)}" y="{_fmt(cy + 180)}" fill="{ds}" '
                 f'font-family="monospace" font-size="8" text-anchor="middle">'
                 f'{num_segs} EQUAL DIVISIONS × {seg_ang:.1f}°</text>')

    # Section line A-A
    lines.append(f'<line x1="30" y1="{_fmt(cy)}" x2="{_fmt(cx*2 - 30)}" y2="{_fmt(cy)}" '
                 f'stroke="{ds}" stroke-width="0.8" stroke-dasharray="8,4,2,4"/>')

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Backward Compatibility Wrapper
# ─────────────────────────────────────────────────────────────────────────────

def render_preview_svg_compat(
    num_segs_or_req=None,
    grid: Optional[Dict[str, str]] = None,
    ring_active: Optional[List[bool]] = None,
    show_tabs: bool = True,
    show_annotations: bool = False,
    width: int = 620,
    height: int = 620,
    *,
    num_segs: Optional[int] = None,
) -> str:
    """Render preview SVG. Accepts PreviewRequest object or keyword args."""
    # Handle keyword-only num_segs (from route calls like num_segs=12)
    if num_segs is not None:
        return render_preview_svg(
            num_segs=num_segs,
            grid=grid or {},
            ring_active=ring_active or [True] * 5,
            show_tabs=show_tabs,
            show_annotations=show_annotations,
            width=width,
            height=height,
        )
    # Handle PreviewRequest-like object (from unit tests)
    if hasattr(num_segs_or_req, "num_segs"):
        req = num_segs_or_req
        return render_preview_svg(
            num_segs=req.num_segs,
            grid=req.grid,
            ring_active=req.ring_active,
            show_tabs=getattr(req, "show_tabs", True),
            show_annotations=getattr(req, "show_annotations", False),
            width=getattr(req, "width", 620),
            height=getattr(req, "height", 620),
        )
    # Handle int as first positional arg
    if isinstance(num_segs_or_req, int):
        return render_preview_svg(
            num_segs=num_segs_or_req,
            grid=grid or {},
            ring_active=ring_active or [True] * 5,
            show_tabs=show_tabs,
            show_annotations=show_annotations,
            width=width,
            height=height,
        )
    raise ValueError("render_preview_svg requires num_segs (int) or PreviewRequest")
