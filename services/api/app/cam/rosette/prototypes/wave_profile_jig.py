#!/usr/bin/env python3
"""
Wave rosette profile and jig SVG builders.

Ported from:
    ProfileCanvas — wave-rosette-v3-patched.jsx (cross-section swell/crash diagram)
    JigCanvas     — wave-rosette-v2.jsx (multi-strand routing jig template)

ProfileCanvas shows the asymmetric arch shape of a single wave strand:
    - Two consecutive arch segments (filled envelopes + centerlines)
    - Peak marker (dashed vertical line at skew point)
    - "swell" and "crash" labels on respective sides
    - Amplitude arrow on left margin
    - Gap zone shading between segments

JigCanvas shows the flat routing jig layout with all strands:
    - Multiple strand paths with phase stagger (rowOffset or chase)
    - Three arch shapes: sine, triangle, flat (squared sine)
    - Segment boundary guides (dashed vertical lines)
    - Gap dots between segments
    - Amplitude annotation and segment/gap labels

Both produce standalone SVG strings (no external dependencies).

Usage:
    python -m app.cam.rosette.prototypes.wave_profile_jig
"""

import math
import os
from pathlib import Path


# ── Ring dimensions (mm) ──────────────────────────────────────────
SOUNDHOLE_R = 40.8
INNER_R     = 41.8
OUTER_R     = 47.8

# ── Default parameters (Torres / Ramirez preset) ─────────────────
A           = 6        # arch height (squares)
SEG_LEN     = 18       # wave segment length (squares)
GAP         = 2        # air between waves (squares)
SKEW        = 0.72     # peak position (0-1), 0.72 = steep crash face
CHASE       = 13       # row stagger (squares)
D           = 4        # row pitch (squares)
STRAND_W    = 1.8      # strand width (squares)
NUM_STRANDS = 7
COLS        = 52
ROWS        = 18
ROW_OFFSET  = 10       # for segment-arch mode
ARCH_SHAPE  = "sine"   # sine | tri | flat

# ── SVG palette (from JSX UI theme) ──────────────────────────────
BG_COLOR    = "#0e0b07"
GOLD        = "#e8c87a"
GOLD_DIM    = "rgba(200,160,50,0.5)"
GOLD_FAINT  = "rgba(200,160,50,0.15)"
GOLD_VERY_FAINT = "rgba(200,160,50,0.08)"
RED_FAINT   = "rgba(200,80,50,0.6)"
RED_ZONE    = "rgba(200,80,50,0.06)"
RED_GUIDE   = "rgba(200,80,50,0.25)"
CREAM       = "#f0e8d0"


# ── Arch shape functions ──────────────────────────────────────────

def arch_y_crash(local_x: float, seg_len: float, amplitude: float, skew: float) -> float:
    """Asymmetric crashing wave arch (from v3-patched ProfileCanvas)."""
    peak_x = skew * seg_len
    if peak_x <= 0 or seg_len <= 0:
        return 0.0
    if local_x <= peak_x:
        return amplitude * math.sin((math.pi / 2) * (local_x / peak_x))
    else:
        return amplitude * math.cos(
            (math.pi / 2) * ((local_x - peak_x) / (seg_len - peak_x))
        )


def arch_y_segment(local_x: float, seg_len: float, amplitude: float, shape: str) -> float:
    """Symmetric arch for discrete segment mode (from v2 JigCanvas)."""
    if seg_len <= 0:
        return 0.0
    t = local_x / seg_len
    if shape == "sine":
        return amplitude * math.sin(math.pi * t)
    elif shape == "tri":
        return amplitude * (1.0 - abs(2.0 * t - 1.0))
    elif shape == "flat":
        s = math.sin(math.pi * t)
        return amplitude * s * s
    return amplitude * math.sin(math.pi * t)


# ── ProfileCanvas SVG ─────────────────────────────────────────────

def build_profile_svg(
    amplitude: float = A,
    seg_len: float = SEG_LEN,
    gap: float = GAP,
    skew: float = SKEW,
    strand_w: float = STRAND_W,
    width: float = 400,
    height: float = 120,
) -> str:
    """
    Build SVG cross-section of the asymmetric crashing wave arch.

    Shows two consecutive segments with filled envelopes, centerlines,
    peak marker, swell/crash labels, amplitude arrow, and gap zone.
    """
    pitch = seg_len + gap
    scale_x = width / (pitch * 2.2)
    scale_y = height / (amplitude * 3 + strand_w * 2)
    base_y = height * 0.85

    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">',
        "<title>Wave Profile - Swell/Crash Cross-Section</title>",
        f'<rect width="{width}" height="{height}" fill="{BG_COLOR}"/>',
    ]

    # Draw two consecutive arch segments
    for seg in range(2):
        x_off = seg * pitch * scale_x + 10
        fill_opacity = 0.15 if seg == 0 else 0.08

        # Build arch path points
        points: list[tuple[float, float]] = []
        lx = 0.0
        while lx <= seg_len:
            y = arch_y_crash(lx, seg_len, amplitude, skew)
            points.append((x_off + lx * scale_x, base_y - y * scale_y))
            lx += 0.2

        # Filled envelope
        fill_path = f"M{x_off:.1f},{base_y:.1f} "
        fill_path += " ".join(f"L{px:.1f},{py:.1f}" for px, py in points)
        fill_path += f" L{x_off + seg_len * scale_x:.1f},{base_y:.1f} Z"
        parts.append(
            f'<path d="{fill_path}" fill="rgb(200,160,50)" '
            f'fill-opacity="{fill_opacity}" stroke="none"/>'
        )

        # Centerline stroke
        center_path = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in points)
        stroke_color = GOLD if seg == 0 else GOLD_DIM
        parts.append(
            f'<path d="{center_path}" fill="none" stroke="{stroke_color}" '
            f'stroke-width="{strand_w * scale_y:.1f}" stroke-linecap="round"/>'
        )

    # Peak marker (dashed vertical)
    peak_x = skew * seg_len
    peak_px = 10 + peak_x * scale_x
    peak_py = base_y - amplitude * scale_y
    parts.append(
        f'<line x1="{peak_px:.1f}" y1="{peak_py - 4:.1f}" '
        f'x2="{peak_px:.1f}" y2="{base_y:.1f}" '
        f'stroke="{RED_FAINT}" stroke-width="1" stroke-dasharray="2,3"/>'
    )

    # Swell / crash labels
    parts.append(
        f'<text x="12" y="{base_y - amplitude * scale_y * 0.5:.1f}" '
        f'font-family="Courier New" font-size="8" fill="{GOLD_DIM}">swell &lt;-</text>'
    )
    parts.append(
        f'<text x="{peak_px + 3:.1f}" y="{base_y - amplitude * scale_y * 0.5:.1f}" '
        f'font-family="Courier New" font-size="8" fill="{GOLD_DIM}">-&gt; crash</text>'
    )

    # Amplitude arrow
    mid_y = (base_y + peak_py) / 2
    parts.append(
        f'<line x1="4" y1="{base_y:.1f}" x2="4" y2="{peak_py:.1f}" '
        f'stroke="rgba(200,160,50,0.4)" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="6" y="{mid_y + 3:.1f}" '
        f'font-family="Courier New" font-size="8" fill="rgba(200,160,50,0.6)">A</text>'
    )

    # Gap zone shading
    gap_start = 10 + seg_len * scale_x
    gap_end = 10 + pitch * scale_x
    parts.append(
        f'<rect x="{gap_start:.1f}" y="0" width="{gap_end - gap_start:.1f}" '
        f'height="{height}" fill="{RED_ZONE}"/>'
    )
    parts.append(
        f'<text x="{gap_start + 2:.1f}" y="{base_y - 4:.1f}" '
        f'font-family="Courier New" font-size="7" fill="rgba(200,80,50,0.4)">gap</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ── JigCanvas SVG (crashing-wave version, v3) ────────────────────

def build_jig_svg_crash(
    cols: int = COLS,
    rows: int = ROWS,
    amplitude: float = A,
    seg_len: float = SEG_LEN,
    gap: float = GAP,
    d: float = D,
    strand_w: float = STRAND_W,
    num_strands: int = NUM_STRANDS,
    skew: float = SKEW,
    chase: int = CHASE,
    width: float = 600,
    height: float = 250,
) -> str:
    """
    Build SVG routing jig for crashing-wave strands (v3 mode).

    Shows all strand paths with chase stagger, using the asymmetric
    arch formula. Includes direction arrow label.
    """
    pitch = seg_len + gap
    scale_x = width / cols
    scale_y = height / rows
    mid_y = height * 0.5

    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">',
        "<title>Wave Jig - Crashing Wave Routing Template</title>",
        f'<rect width="{width}" height="{height}" fill="{BG_COLOR}"/>',
    ]

    # Draw each strand
    for n in range(-1, num_strands + 2):
        offset = ((n * chase) % pitch + pitch * 100) % pitch
        base_y_n = n * d
        color_idx = ((n % 3) + 3) % 3
        stroke = CREAM if color_idx == 0 else GOLD_DIM

        for k in range(-1, math.ceil(cols / pitch) + 2):
            x_start = k * pitch + offset
            if x_start > cols or x_start + seg_len < 0:
                continue

            path_pts: list[str] = []
            lx = 0.0
            while lx <= seg_len:
                cx = x_start + lx
                if 0 <= cx <= cols:
                    y = arch_y_crash(lx, seg_len, amplitude, skew)
                    px = cx * scale_x
                    py = (base_y_n + y) * scale_y + mid_y
                    prefix = "M" if not path_pts else "L"
                    path_pts.append(f"{prefix}{px:.1f},{py:.1f}")
                lx += 0.4

            if path_pts:
                lw = max(strand_w * scale_y * 0.8, 1)
                parts.append(
                    f'<path d="{" ".join(path_pts)}" fill="none" stroke="{stroke}" '
                    f'stroke-width="{lw:.1f}" stroke-linecap="round"/>'
                )

    # Direction arrow
    parts.append(
        f'<line x1="{width - 40}" y1="12" x2="{width - 10}" y2="12" '
        f'stroke="{GOLD_DIM}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<polyline points="{width - 16},8 {width - 10},12 {width - 16},16" '
        f'fill="none" stroke="{GOLD_DIM}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<text x="{width - 60}" y="10" font-family="Courier New" font-size="8" '
        f'fill="{GOLD_DIM}">-&gt; travel</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ── JigCanvas SVG (segment-arch version, v2) ─────────────────────

def build_jig_svg_segment(
    cols: int = COLS,
    rows: int = ROWS,
    amplitude: float = 5,
    seg_len: int = 16,
    gap: int = 4,
    d: float = D,
    strand_w: float = STRAND_W,
    num_strands: int = NUM_STRANDS,
    row_offset: int = ROW_OFFSET,
    arch_shape: str = ARCH_SHAPE,
    width: float = 600,
    height: float = 250,
) -> str:
    """
    Build SVG routing jig for discrete segment arches (v2 mode).

    Shows all strand paths with rowOffset stagger, three arch shapes
    (sine/tri/flat), gap dots, segment boundary guides, amplitude
    annotation, and seg/gap labels.
    """
    pitch = seg_len + gap
    scale_x = width / cols
    scale_y = height / rows
    mid_y = height * 0.5

    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">',
        f'<title>Wave Jig - Segment Arches ({arch_shape})</title>',
        f'<rect width="{width}" height="{height}" fill="{BG_COLOR}"/>',
    ]

    # Draw strand segments
    for n in range(-1, num_strands + 2):
        strand_phase = (n * row_offset) % pitch
        base_y_n = n * d
        color_idx = n % 3
        if color_idx == 0:
            stroke = CREAM
        elif color_idx == 1:
            stroke = GOLD_DIM
        else:
            stroke = "rgba(200,160,50,0.5)"

        for k in range(-1, math.ceil(cols / pitch) + 2):
            x_start = k * pitch + strand_phase
            if x_start > cols or x_start + seg_len < 0:
                continue

            path_pts: list[str] = []
            lx = 0.0
            while lx <= seg_len:
                x = (x_start + lx) * scale_x
                y = (base_y_n + arch_y_segment(lx, seg_len, amplitude, arch_shape)) * scale_y + mid_y
                prefix = "M" if not path_pts else "L"
                path_pts.append(f"{prefix}{x:.1f},{y:.1f}")
                lx += 0.5

            if path_pts:
                lw = strand_w * scale_y
                parts.append(
                    f'<path d="{" ".join(path_pts)}" fill="none" stroke="{stroke}" '
                    f'stroke-width="{lw:.1f}" stroke-linecap="round"/>'
                )

            # Gap dots
            if gap > 0:
                gap_x = (x_start + seg_len + gap / 2) * scale_x
                gap_y = base_y_n * scale_y + mid_y
                if 0 < gap_x < width:
                    parts.append(
                        f'<circle cx="{gap_x:.1f}" cy="{gap_y:.1f}" r="1.5" '
                        f'fill="rgba(200,160,50,0.2)"/>'
                    )

    # Segment boundary guides (dashed)
    k = 0
    while k * pitch < cols + pitch:
        # Segment start (gold)
        x = k * pitch * scale_x
        if 0 <= x <= width:
            parts.append(
                f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{height}" '
                f'stroke="rgba(200,160,50,0.3)" stroke-width="0.8" stroke-dasharray="2,4"/>'
            )
        # Segment end (red)
        x_end = (k * pitch + seg_len) * scale_x
        if 0 <= x_end <= width:
            parts.append(
                f'<line x1="{x_end:.1f}" y1="0" x2="{x_end:.1f}" y2="{height}" '
                f'stroke="{RED_GUIDE}" stroke-width="0.8" stroke-dasharray="2,4"/>'
            )
        k += 1

    # Amplitude annotation
    anno_x = (seg_len * 0.5) * scale_x
    anno_y_base = mid_y
    anno_y_tip = mid_y - amplitude * scale_y
    parts.append(
        f'<line x1="{anno_x:.1f}" y1="{anno_y_base:.1f}" '
        f'x2="{anno_x:.1f}" y2="{anno_y_tip:.1f}" '
        f'stroke="rgba(200,160,50,0.6)" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{anno_x + 4:.1f}" y="{(anno_y_base + anno_y_tip) / 2 + 3:.1f}" '
        f'font-family="Courier New" font-size="9" fill="rgba(200,160,50,0.7)">A={amplitude}</text>'
    )

    # Bottom labels
    parts.append(
        f'<text x="4" y="{height - 16}" font-family="Courier New" font-size="8" '
        f'fill="rgba(200,160,50,0.4)">seg={seg_len}sq</text>'
    )
    parts.append(
        f'<text x="4" y="{height - 5}" font-family="Courier New" font-size="8" '
        f'fill="rgba(200,160,50,0.4)">gap={gap}sq</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    out_dir = Path(os.environ.get(
        "ROSETTE_OUT",
        Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "docs",
    ))

    # Profile SVG (cross-section)
    profile_svg = build_profile_svg()
    profile_path = out_dir / "wave_profile.svg"
    profile_path.write_text(profile_svg, encoding="utf-8")
    print(f"Profile SVG saved: {profile_path}")

    # Jig SVG - crashing wave (v3 mode)
    jig_crash_svg = build_jig_svg_crash()
    jig_crash_path = out_dir / "wave_jig_crash.svg"
    jig_crash_path.write_text(jig_crash_svg, encoding="utf-8")
    print(f"Jig SVG (crash) saved: {jig_crash_path}")

    # Jig SVG - segment arches (v2 mode, all 3 shapes)
    for shape in ("sine", "tri", "flat"):
        jig_seg_svg = build_jig_svg_segment(arch_shape=shape)
        jig_seg_path = out_dir / f"wave_jig_segment_{shape}.svg"
        jig_seg_path.write_text(jig_seg_svg, encoding="utf-8")
        print(f"Jig SVG (segment/{shape}) saved: {jig_seg_path}")

    print("\nAll wave profile/jig SVGs generated.")


if __name__ == "__main__":
    main()
