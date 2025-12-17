"""
Rosette Preview Renderer - Bundle 31.0.3

Renders lightweight SVG previews of RosetteParamSpec.
This is NOT production geometry - it's a UI preview only.

- Concentric annulus bands from inner -> outer
- Pattern type influences hatch/stroke style (lightweight)
- No CAM, no toolpaths, no shapely/ML geometry
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from ..schemas.rosette_params import RosetteParamSpec


@dataclass(frozen=True)
class PreviewRenderResult:
    svg: str
    view_box: str
    warnings: List[str]
    debug: dict


def render_rosette_preview_svg(
    spec: RosetteParamSpec,
    size_px: int = 520,
    padding_px: int = 20,
) -> PreviewRenderResult:
    """
    Render a lightweight SVG preview of a rosette design.

    This is NOT production geometry.
    - Concentric annulus bands are drawn from inner -> outer using ring widths
    - Pattern types can influence hatch/stroke style (very light)
    - No CAM, no toolpaths, no shapely/ML geometry
    """
    warnings: List[str] = []

    # Validate and normalize
    outer = float(spec.outer_diameter_mm or 0.0)
    inner = float(spec.inner_diameter_mm or 0.0)

    if outer <= 0 or inner <= 0:
        warnings.append("Invalid diameters; rendering fallback.")
        outer = max(outer, 100.0)
        inner = max(inner, 70.0)

    if inner >= outer:
        warnings.append("inner_diameter_mm >= outer_diameter_mm; swapping for preview.")
        inner, outer = outer, inner

    ring_params = list(spec.ring_params or [])

    if not ring_params:
        warnings.append("No ring_params provided; rendering only inner/outer guide circles.")

    # We render in "mm-space" using a viewBox centered at (0,0), then map to pixels
    outer_r = outer / 2.0
    inner_r = inner / 2.0

    # Determine the implied outer radius from ring widths
    widths = [max(0.0, float(r.width_mm or 0.0)) for r in ring_params]
    total_radial = sum(widths)

    # Expected radial span from diameters
    span = outer_r - inner_r

    if ring_params and abs(total_radial - span) > max(0.5, 0.15 * span):
        warnings.append(
            "Ring widths do not match the inner/outer diameter span; preview uses widths from inner radius."
        )

    # Preview radii progression: start at inner_r and add widths
    bands: List[Tuple[float, float, str]] = []  # (r_in, r_out, pattern_type)
    r_cursor = inner_r

    for r in ring_params:
        w = max(0.0, float(r.width_mm or 0.0))
        pattern = str(r.pattern_type or "SOLID")
        r_in = r_cursor
        r_out = r_cursor + w
        if w <= 0:
            warnings.append("One or more rings has non-positive width; skipped in preview.")
        else:
            bands.append((r_in, r_out, pattern))
        r_cursor = r_out

    implied_outer_r = r_cursor if bands else outer_r

    # Scale: choose a viewBox that fits the larger of specified outer or implied outer
    r_max = max(outer_r, implied_outer_r)
    pad_mm = (padding_px / max(size_px, 1)) * (2.0 * r_max)  # rough mm padding
    r_box = r_max + pad_mm
    view_box = f"{-r_box:.4f} {-r_box:.4f} {2*r_box:.4f} {2*r_box:.4f}"

    # SVG defs: simple hatch patterns for non-solid types
    defs = """
<defs>
<pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<line x1="0" y1="0" x2="0" y2="4" stroke="rgba(0,0,0,0.35)" stroke-width="1"/>
</pattern>
<pattern id="dots" width="6" height="6" patternUnits="userSpaceOnUse">
<circle cx="1.5" cy="1.5" r="1" fill="rgba(0,0,0,0.35)"/>
</pattern>
</defs>
""".strip()

    # Background
    bg = f'<rect x="{-r_box:.4f}" y="{-r_box:.4f}" width="{2*r_box:.4f}" height="{2*r_box:.4f}" fill="white"/>'

    # Guide circles
    guides = []
    guides.append(_circle(inner_r, stroke="rgba(0,0,0,0.35)", stroke_width=0.25, fill="none"))
    guides.append(_circle(outer_r, stroke="rgba(0,0,0,0.35)", stroke_width=0.25, fill="none"))

    # Bands: draw as filled annulus using even-odd fill rule
    band_paths = []
    for idx, (r_in, r_out, pattern) in enumerate(bands):
        fill = "rgba(0,0,0,0.06)" if (idx % 2 == 0) else "rgba(0,0,0,0.03)"
        pat_upper = pattern.strip().upper()
        if pat_upper in {"MOSAIC", "HATCH"}:
            fill = "url(#hatch)"
        elif pat_upper in {"DOTS", "STIPPLE"}:
            fill = "url(#dots)"
        band_paths.append(_annulus(r_in, r_out, fill=fill))

    # Label: minimal center marker
    center = '<circle cx="0" cy="0" r="0.6" fill="rgba(0,0,0,0.65)"/>'

    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{size_px}" height="{size_px}" viewBox="{view_box}">
{defs}
{bg}
{''.join(band_paths)}
{''.join(guides)}
{center}
</svg>
""".strip()

    debug = {
        "outer_diameter_mm": outer,
        "inner_diameter_mm": inner,
        "outer_r": outer_r,
        "inner_r": inner_r,
        "implied_outer_r": implied_outer_r,
        "ring_count": len(ring_params),
        "bands_drawn": len(bands),
    }

    return PreviewRenderResult(svg=svg, view_box=view_box, warnings=warnings, debug=debug)


def _circle(r: float, stroke: str, stroke_width: float, fill: str) -> str:
    return f'<circle cx="0" cy="0" r="{r:.4f}" stroke="{stroke}" stroke-width="{stroke_width}" fill="{fill}"/>'.strip()


def _annulus(r_in: float, r_out: float, fill: str) -> str:
    """
    Create an annulus shape using even-odd fill:
    - outer circle path, then inner circle path reversed
    """
    r_in = max(0.0, float(r_in))
    r_out = max(r_in, float(r_out))

    outer = _circle_path(r_out)
    inner = _circle_path(r_in)

    # If inner radius is ~0, just draw a circle
    if r_in <= 1e-6:
        return f'<path d="{outer}" fill="{fill}" fill-rule="evenodd" stroke="rgba(0,0,0,0.08)" stroke-width="0.15"/>'

    d = f"{outer} {inner}"
    return f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="rgba(0,0,0,0.08)" stroke-width="0.15"/>'


def _circle_path(r: float) -> str:
    r = max(0.0, float(r))
    if r <= 1e-6:
        return "M 0 0"
    # Two half-arcs to complete a circle
    return (
        f"M {r:.4f} 0 "
        f"A {r:.4f} {r:.4f} 0 1 0 {-r:.4f} 0 "
        f"A {r:.4f} {r:.4f} 0 1 0 {r:.4f} 0 Z"
    )
