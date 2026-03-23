"""
cantilever_armrest_calc.py
==========================
Parametric geometry calculator for a cantilever acoustic guitar arm rest.

Construction model
------------------
The cantilever arm rest is an ADDITIVE piece — it sits on top of the guitar
corner, not carved into it. Cross-section at any span station:

  z ↑  (up from guitar top surface)
  x →  (positive = into guitar body / glue zone;
         negative = overhang past side wall)

  The piece has three surfaces:
    1. Glue face      — flat, on the guitar top, x ∈ [0, w_glue]
    2. Outer face     — oblique at angle θ(t) from vertical
    3. Top/upper edge — rounded over with radius r_edge

Key insight (variable angle)
-----------------------------
θ(t) is NOT constant. It follows the same sinusoidal taper law as h(t):

    θ(t) = θ_max × f(t)    where f is the asymmetric half-cosine taper

This means the face is steep (≈43°, just shy of 45°) at the apex and
dissolves to horizontal (0°) at both tips — producing a developable ruled
surface with invisible transitions at the ends.

Source honesty
--------------
EXACT (geometry):
  - All cross-section relationships: trigonometric, exact
  - Ruled surface parameterization: exact

EMPIRICAL (from builder practice / photos):
  - θ_max ≈ 43°  (just shy of 45°, Rolo/Gabriel builder consensus)
  - t_apex ≈ 0.38  (apex biased toward lower end, ergonomic)
  - t_v ≈ 3mm  (minimum practical veneer thickness)
  - w_glue_max ≈ 22mm  (lining constraint — empirical)

References:
  Padron, R. "How I Make a Cantilever Arrorest." Rev. 2, 2018.
  Gabriel, J. "Photo-essay on using a bandsaw to make an integral
    Laskin-style beveled armrest." MIMF, 2005.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple

from ..core.safety import safety_critical


# ---------------------------------------------------------------------------
# Core taper function
# ---------------------------------------------------------------------------

def f_taper(t: float, t_apex: float) -> float:
    """
    Asymmetric half-cosine taper: rises from 0 at t=0, peaks at t=t_apex,
    falls back to 0 at t=1.

    Rise: sin(π/2 · t/t_apex)
    Fall: cos(π/2 · (t − t_apex)/(1 − t_apex))
    """
    t = max(0.0, min(1.0, t))
    if t <= t_apex:
        return math.sin(math.pi / 2.0 * t / t_apex) if t_apex > 0 else 0.0
    return math.cos(math.pi / 2.0 * (t - t_apex) / (1.0 - t_apex))


# ---------------------------------------------------------------------------
# Parameter dataclass
# ---------------------------------------------------------------------------

@dataclass
class ArmRestSpec:
    """
    Complete parametric specification for a cantilever arm rest.

    All dimensions in mm and degrees.
    """
    # ── Span ──────────────────────────────────────────────────────────────
    span_mm: float = 140.0
    """Total length tip-to-tip along the rim (mm). Typical: 120–160mm."""

    t_apex: float = 0.38
    """Normalized span position of the apex (0–1). Asymmetric: 0.35–0.42."""

    # ── Height profile ────────────────────────────────────────────────────
    h_max_mm: float = 14.0
    """Maximum height of the complete piece above the guitar top (mm)."""

    # ── Face angle ────────────────────────────────────────────────────────
    theta_max_deg: float = 43.0
    """Peak face angle from vertical at the apex (degrees). Just shy of 45°."""

    # ── Veneer ────────────────────────────────────────────────────────────
    t_veneer_mm: float = 3.0
    """Veneer thickness (mm). Minimum ~2.5mm for a bendable wood veneer."""

    # ── Glue face ─────────────────────────────────────────────────────────
    w_glue_max_mm: float = 22.0
    """Maximum glue face width on guitar top (mm). Constrained by lining width."""

    # ── Edge roundover ────────────────────────────────────────────────────
    r_edge_mm: float = 10.0
    """Upper edge roundover radius (mm). Generous for ergonomics."""

    # ── Body reference ────────────────────────────────────────────────────
    r_lower_bout_mm: float = 200.0
    """Body outline radius at arm rest location (mm). Used for rim curvature."""

    def validate(self) -> List[str]:
        """Return list of warnings for out-of-range parameters."""
        warnings = []
        if not 0.25 < self.t_apex < 0.55:
            warnings.append(f"t_apex={self.t_apex} outside typical 0.25–0.55")
        if not 100 <= self.span_mm <= 200:
            warnings.append(f"span={self.span_mm}mm outside typical 100–200mm")
        if not 8 <= self.h_max_mm <= 20:
            warnings.append(f"h_max={self.h_max_mm}mm outside typical 8–20mm")
        if not 35 <= self.theta_max_deg <= 50:
            warnings.append(f"theta_max={self.theta_max_deg}° outside 35–50°")
        if self.t_veneer_mm < 2.5:
            warnings.append(f"t_veneer={self.t_veneer_mm}mm below minimum 2.5mm")
        if self.r_edge_mm > self.h_max_mm * 0.8:
            warnings.append(
                f"r_edge={self.r_edge_mm}mm > 80% of h_max — roundover dominates entire height"
            )
        if self.w_glue_max_mm > 25:
            warnings.append(
                f"w_glue_max={self.w_glue_max_mm}mm likely exceeds lining (typically ≤22mm)"
            )
        return warnings


# ---------------------------------------------------------------------------
# Section dataclass — geometry at a single span station
# ---------------------------------------------------------------------------

@dataclass
class ArmRestSection:
    """Cross-section geometry at a single normalized span position t."""
    t: float
    h_total_mm: float       # total height above guitar top
    theta_deg: float        # face angle from vertical
    h_block_mm: float       # block height (h_total − t_veneer)
    x_overhang_mm: float    # horizontal projection past side wall (into air)
    w_glue_mm: float        # glue face width on guitar top
    face_length_mm: float   # length of the oblique face surface
    total_width_mm: float   # w_glue + x_overhang

    def to_dict(self) -> dict:
        return {k: round(v, 3) for k, v in asdict(self).items()}


# ---------------------------------------------------------------------------
# Main geometry computation
# ---------------------------------------------------------------------------

def compute_section(t: float, spec: ArmRestSpec) -> ArmRestSection:
    """
    Compute cross-section geometry at normalized span position t ∈ [0, 1].

    Cross-section is perpendicular to the rim arc at position t.

    Coordinate system:
        x: horizontal, positive into guitar body (glue zone)
              negative = overhang past side wall
        z: vertical, positive up from guitar top surface

    The outer face of the block makes angle θ(t) with the vertical.
    At height z on the block, the horizontal position is:
        x_face(z) = −z / tan(θ)    [negative = overhanging]

    So x_overhang = h_block / tan(θ).

    With variable θ(t), the face angle and height both taper together,
    keeping the surface smooth and developable.
    """
    f = f_taper(t, spec.t_apex)

    h_total = spec.h_max_mm * f
    theta_rad = math.radians(spec.theta_max_deg * f)

    h_block = max(0.0, h_total - spec.t_veneer_mm)

    # x_overhang from block geometry: h_block / tan(θ)
    # At θ → 0 (tips), overhang → 0 (face becomes horizontal)
    if theta_rad > 1e-4:
        x_ov = h_block / math.tan(theta_rad)
    else:
        x_ov = 0.0

    # Glue face: present where piece has height; tapers to zero at tips
    w_glue = spec.w_glue_max_mm * f if h_total > 0.5 else 0.0
    w_glue = min(w_glue, spec.w_glue_max_mm)

    # Oblique face length: h_block / sin(θ)
    face_len = h_block / math.sin(theta_rad) if theta_rad > 1e-4 else 0.0

    return ArmRestSection(
        t=round(t, 4),
        h_total_mm=round(h_total, 3),
        theta_deg=round(spec.theta_max_deg * f, 2),
        h_block_mm=round(h_block, 3),
        x_overhang_mm=round(x_ov, 3),
        w_glue_mm=round(w_glue, 3),
        face_length_mm=round(face_len, 3),
        total_width_mm=round(w_glue + x_ov, 3),
    )


# ---------------------------------------------------------------------------
# Ruled surface
# ---------------------------------------------------------------------------

@dataclass
class RuledSurfacePoint:
    """Single point on the arm rest ruled surface."""
    t: float        # normalized span [0, 1]
    u: float        # normalized cross-section [0, 1]: 0=outer, 1=inner
    x_mm: float     # horizontal (negative = past side)
    y_mm: float     # along span (0 at one tip, span_mm at other)
    z_mm: float     # vertical above guitar top


def compute_ruled_surface(
    spec: ArmRestSpec,
    n_span: int = 60,
    n_cross: int = 8,
) -> List[List[RuledSurfacePoint]]:
    """
    Generate the ruled surface S(t, u) of the arm rest outer face.

    The surface is ruled between two guide curves:
        u=0: outer bottom edge (on guitar top, overhanging past side)
        u=1: inner top edge (top of block, at x≈0)

    At each span station t:
        bottom = (−x_overhang, y, 0)
        top    = (0, y, h_block)
        S(t,u) = (1−u) × bottom + u × top

    This is a developable ruled surface — can be unrolled flat.

    Returns grid[i_span][j_cross] of surface points.
    """
    grid: List[List[RuledSurfacePoint]] = []

    for i in range(n_span + 1):
        t = i / n_span
        sec = compute_section(t, spec)
        y = t * spec.span_mm

        row: List[RuledSurfacePoint] = []
        for j in range(n_cross + 1):
            u = j / n_cross
            # Bottom edge (u=0): outer lower point, on guitar top surface
            x0 = -sec.x_overhang_mm
            z0 = 0.0
            # Top edge (u=1): inner upper point, top of block
            x1 = 0.0
            z1 = sec.h_block_mm

            x = x0 + u * (x1 - x0)
            z = z0 + u * (z1 - z0)

            row.append(RuledSurfacePoint(
                t=round(t, 4), u=round(u, 4),
                x_mm=round(x, 3), y_mm=round(y, 3), z_mm=round(z, 3),
            ))
        grid.append(row)

    return grid


# ---------------------------------------------------------------------------
# CNC toolpath
# ---------------------------------------------------------------------------

@dataclass
class GcodeConfig:
    """G-code output configuration."""
    feed_roughing: float = 2000.0    # mm/min
    feed_finishing: float = 800.0    # mm/min
    spindle_rpm: int = 18000
    tool_diameter_mm: float = 6.35   # 1/4" ball-end
    stepover_mm: float = 1.0         # finishing stepover
    safe_z_mm: float = 10.0


@safety_critical
def generate_gcode(
    spec: ArmRestSpec,
    cfg: GcodeConfig,
    n_span: int = 80,
) -> str:
    """
    Generate CNC G-code toolpath for the arm rest outer face.

    Strategy: raster along span (Y axis), stepping across the oblique
    face at each Y station. Ball-end mill follows the ruled surface.

    The face at each Y station is a straight line from bottom to top,
    so each Y-pass is a single angled plunge — ideal for the bandsaw
    method (set bandsaw table to θ(t) and feed through).

    For CNC: output Z-level passes along Y, stepping in X.
    """
    lines = [
        f"( Cantilever Arm Rest — CNC Toolpath )",
        f"( Span: {spec.span_mm}mm  h_max: {spec.h_max_mm}mm  theta_max: {spec.theta_max_deg}° )",
        f"( Tool: {cfg.tool_diameter_mm}mm ball-end  Stepover: {cfg.stepover_mm}mm )",
        f"",
        f"G90 G21 G17",
        f"M3 S{cfg.spindle_rpm}",
        f"G0 Z{cfg.safe_z_mm:.3f}",
        f"",
    ]

    surface = compute_ruled_surface(spec, n_span=n_span, n_cross=20)

    # Raster: for each span station, drive along the face
    for i, row in enumerate(surface):
        y = row[0].y_mm
        lines.append(f"( Station t={i/n_span:.3f}  Y={y:.2f} )")
        lines.append(f"G0 Z{cfg.safe_z_mm:.3f}")
        lines.append(f"G0 X{row[0].x_mm:.3f} Y{y:.3f}")

        for pt in row:
            lines.append(
                f"G1 X{pt.x_mm:.3f} Y{pt.y_mm:.3f} Z{pt.z_mm:.3f} "
                f"F{cfg.feed_finishing:.0f}"
            )
        lines.append("")

    lines += [
        f"G0 Z{cfg.safe_z_mm:.3f}",
        f"G0 X0.000 Y0.000",
        f"M5",
        f"M30",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

@dataclass
class ArmRestResult:
    """Complete computed result for an arm rest specification."""
    spec: ArmRestSpec
    warnings: List[str]
    sections: List[ArmRestSection]

    # Key derived values at apex
    apex_section: ArmRestSection = field(init=False)
    max_overhang_mm: float = field(init=False)
    max_total_width_mm: float = field(init=False)
    face_length_apex_mm: float = field(init=False)

    def __post_init__(self):
        self.apex_section = compute_section(self.spec.t_apex, self.spec)
        self.max_overhang_mm = max(s.x_overhang_mm for s in self.sections)
        self.max_total_width_mm = max(s.total_width_mm for s in self.sections)
        self.face_length_apex_mm = self.apex_section.face_length_mm

    def format_report(self) -> str:
        sp = self.spec
        ap = self.apex_section
        lines = [
            "═" * 58,
            "  CANTILEVER ARM REST — GEOMETRY REPORT",
            "═" * 58,
            "",
            "  INPUTS",
            f"    Span            {sp.span_mm:.0f} mm",
            f"    h_max           {sp.h_max_mm:.1f} mm",
            f"    θ_max           {sp.theta_max_deg:.0f}°  (just shy of 45°)",
            f"    t_apex          {sp.t_apex:.2f}",
            f"    Veneer          {sp.t_veneer_mm:.1f} mm",
            f"    w_glue max      {sp.w_glue_max_mm:.0f} mm",
            f"    r_edge          {sp.r_edge_mm:.0f} mm",
            "",
            "  AT APEX (t = {:.2f})".format(sp.t_apex),
            f"    Height total    {ap.h_total_mm:.1f} mm",
            f"    Block height    {ap.h_block_mm:.1f} mm",
            f"    Face angle      {ap.theta_deg:.1f}°",
            f"    x_overhang      {ap.x_overhang_mm:.1f} mm  (past side wall)",
            f"    Glue face       {ap.w_glue_mm:.1f} mm  (on top surface)",
            f"    Face length     {ap.face_length_mm:.1f} mm  (veneer cut width)",
            f"    Total width     {ap.total_width_mm:.1f} mm",
            "",
            "  PROFILE ALONG SPAN",
            f"    {'t':>6}  {'h(mm)':>7}  {'θ(°)':>7}  {'x_ov':>7}  {'w_gl':>7}",
        ]
        for s in self.sections:
            lines.append(
                f"    {s.t:>6.2f}  {s.h_total_mm:>7.1f}  "
                f"{s.theta_deg:>7.1f}  {s.x_overhang_mm:>7.1f}  {s.w_glue_mm:>7.1f}"
            )
        if self.warnings:
            lines += ["", "  WARNINGS"]
            for w in self.warnings:
                lines.append(f"    ⚠  {w}")
        lines += ["", "═" * 58]
        return "\n".join(lines)


def compute_armrest(
    spec: ArmRestSpec,
    n_stations: int = 11,
) -> ArmRestResult:
    """
    Full computation for a cantilever arm rest specification.

    Returns ArmRestResult with sections, apex stats, warnings, and report.
    """
    warnings = spec.validate()
    t_vals = [i / (n_stations - 1) for i in range(n_stations)]
    sections = [compute_section(t, spec) for t in t_vals]
    return ArmRestResult(spec=spec, warnings=warnings, sections=sections)


# ---------------------------------------------------------------------------
# Convenience presets
# ---------------------------------------------------------------------------

def preset_standard() -> ArmRestSpec:
    """Standard dreadnought / OM arm rest — resolved from inverse solver."""
    return ArmRestSpec(
        span_mm=140, h_max_mm=14, theta_max_deg=43,
        t_apex=0.38, t_veneer_mm=3.0, w_glue_max_mm=22,
        r_edge_mm=10, r_lower_bout_mm=200,
    )


def preset_classical() -> ArmRestSpec:
    """Smaller classical guitar arm rest — lower profile."""
    return ArmRestSpec(
        span_mm=120, h_max_mm=11, theta_max_deg=40,
        t_apex=0.40, t_veneer_mm=2.5, w_glue_max_mm=18,
        r_edge_mm=8, r_lower_bout_mm=180,
    )


def preset_archtop() -> ArmRestSpec:
    """Archtop jazz guitar — deeper body, more aggressive bevel."""
    return ArmRestSpec(
        span_mm=160, h_max_mm=18, theta_max_deg=45,
        t_apex=0.35, t_veneer_mm=4.0, w_glue_max_mm=25,
        r_edge_mm=12, r_lower_bout_mm=220,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("\nCantilever Arm Rest Calculator\n")

    spec = preset_standard()
    result = compute_armrest(spec, n_stations=11)
    print(result.format_report())

    print("\nGenerating G-code sample (first 20 lines)...")
    cfg = GcodeConfig()
    gcode = generate_gcode(spec, cfg, n_span=20)
    for line in gcode.split("\n")[:20]:
        print(" ", line)
    print("  ...")

    print(f"\nRuled surface: {len(compute_ruled_surface(spec))} span stations × 9 cross-section points")
    print("Done.\n")
