"""
Radial Engine - N-fold patterns around a center.

Generates radial patterns like sunburst, feather, amsterdam flower,
spirograph arcs, spiral arms, square floral, and open flower oval.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from ..inlay_geometry import GeometryCollection, GeometryElement, Pt
from ..inlay_primitives import (
    arc_band_pts,
    circle_pts,
    radial_material,
    wedge_pts,
)


@dataclass
class RadialConfig:
    """Configuration for RadialEngine."""
    n_fold: int = 8
    inner_r: float = 10.0
    outer_r: float = 40.0
    twist_deg: float = 0.0
    center_disc_r: float = 0.0  # 0 = no center disc
    n_materials: int = 2


class RadialEngine:
    """Engine for radial/N-fold patterns."""

    @staticmethod
    def generate(
        petal_fn: Callable[[float, float, float, Dict[str, Any]], List[Pt]],
        petal_params: Dict[str, Any],
        config: RadialConfig,
    ) -> GeometryCollection:
        """
        Generate a radial pattern.

        Args:
            petal_fn: Function(cx, cy, angle_rad, params) -> List[Pt]
            petal_params: Parameters passed to petal_fn
            config: Radial configuration

        Returns:
            GeometryCollection with radial elements
        """
        step = 2 * math.pi / config.n_fold
        twist_rad = math.radians(config.twist_deg)

        elements: List[GeometryElement] = []
        for k in range(config.n_fold):
            angle = k * step + twist_rad
            pts = petal_fn(0, 0, angle, {**petal_params, "index": k})
            mat_idx = radial_material(k, config.n_materials)

            elements.append(GeometryElement(
                kind="polygon",
                points=pts,
                material_index=mat_idx,
                stroke_width=0.25,
                grain_angle=math.degrees(angle),
            ))

        # Optional center disc
        if config.center_disc_r > 0:
            disc_pts = circle_pts(0, 0, config.center_disc_r, 24)
            elements.append(GeometryElement(
                kind="polygon",
                points=disc_pts,
                material_index=config.n_materials - 1,
                stroke_width=0.25,
            ))

        bbox = config.outer_r
        return GeometryCollection(
            elements=elements,
            width_mm=bbox * 2,
            height_mm=bbox * 2,
            origin_x=bbox,
            origin_y=bbox,
            radial=True,
        )

    @staticmethod
    def sunburst(params: Dict[str, Any]) -> GeometryCollection:
        """Sunburst wedge pattern."""
        rays = int(params.get("rays", 16))
        band_r = float(params.get("band_r", 55))
        inner_frac = float(params.get("inner_frac", 0.22))
        outer_frac = float(params.get("outer_frac", 0.92))
        alt_rays = bool(params.get("alt_rays", True))

        inner_r = inner_frac * band_r
        outer_r = outer_frac * band_r
        step = 2 * math.pi / rays

        def petal_fn(cx: float, cy: float, angle: float, p: Dict[str, Any]) -> List[Pt]:
            k = p["index"]
            w = 0.56 if (alt_rays and k % 2 == 0) else 0.44
            return wedge_pts(cx, cy, inner_r, outer_r, angle, angle + step * w)

        config = RadialConfig(
            n_fold=rays,
            inner_r=inner_r,
            outer_r=outer_r,
            twist_deg=float(params.get("twist", 0)),
            center_disc_r=inner_r,
            n_materials=3,
        )
        return RadialEngine.generate(petal_fn, {}, config)

    @staticmethod
    def feather(params: Dict[str, Any]) -> GeometryCollection:
        """Layered feather fan."""
        blades = int(params.get("blades", 14))
        layers = int(params.get("layers", 2))
        spread = float(params.get("spread", 270))
        taper = float(params.get("taper", 0.42))
        band_r = float(params.get("band_r", 55))

        elements: List[GeometryElement] = []
        for layer in range(layers - 1, -1, -1):
            o_r = band_r * (1 - (layer / layers) * 0.65)
            i_r = o_r * (1 - taper * 0.8)
            a_step = math.radians(spread) / blades
            base_a = math.radians(-spread * 0.5) + layer * math.radians(spread * 0.5) / layers

            for b_idx in range(blades):
                a0 = base_a + b_idx * a_step
                pts = wedge_pts(0, 0, i_r, o_r, a0, a0 + a_step * 0.9, 13)
                elements.append(GeometryElement(
                    kind="polygon", points=pts,
                    material_index=(b_idx + layer) % 3,
                    stroke_width=0.2,
                ))

        return GeometryCollection(
            elements=elements,
            width_mm=band_r * 2,
            height_mm=band_r * 2,
            origin_x=band_r,
            origin_y=band_r,
            radial=True,
        )

    @staticmethod
    def amsterdam_flower(params: Dict[str, Any]) -> GeometryCollection:
        """N-fold kite-petal medallion."""
        n_fold = max(3, int(params.get("n_fold", 8)))
        outer_r = float(params.get("outer_r", 40))
        inner_r = float(params.get("inner_r", 12))
        mid_frac = float(params.get("mid_frac", 0.6))
        inner_half_frac = float(params.get("inner_half_frac", 0.8))

        step = 2 * math.pi / n_fold
        half_a = step / 2
        mid_r = inner_r + (outer_r - inner_r) * mid_frac
        inner_half = half_a * inner_half_frac

        def petal_fn(cx: float, cy: float, angle: float, p: Dict[str, Any]) -> List[Pt]:
            p0 = (inner_r * math.cos(angle - inner_half), inner_r * math.sin(angle - inner_half))
            p1 = (outer_r * math.cos(angle), outer_r * math.sin(angle))
            p2 = (inner_r * math.cos(angle + inner_half), inner_r * math.sin(angle + inner_half))
            p3 = (mid_r * math.cos(angle + half_a), mid_r * math.sin(angle + half_a))
            return [p0, p1, p2, p3]

        config = RadialConfig(
            n_fold=n_fold,
            inner_r=inner_r,
            outer_r=outer_r,
            center_disc_r=inner_r * 0.55,
        )
        return RadialEngine.generate(petal_fn, {}, config)

    @staticmethod
    def spiro_arc(params: Dict[str, Any]) -> GeometryCollection:
        """Spirograph-style overlapping arcs."""
        arc_count = max(3, int(params.get("arc_count", 12)))
        outer_r = float(params.get("outer_r", 40))
        inner_r = float(params.get("inner_r", 12))
        sweep_deg = float(params.get("sweep_deg", 65))

        sweep = math.radians(sweep_deg)

        def petal_fn(cx: float, cy: float, angle: float, p: Dict[str, Any]) -> List[Pt]:
            return arc_band_pts(cx, cy, inner_r, outer_r, angle - sweep/2, sweep)

        config = RadialConfig(n_fold=arc_count, inner_r=inner_r, outer_r=outer_r)
        geo = RadialEngine.generate(petal_fn, {}, config)
        # Sort for Z-order (even behind, odd on top)
        geo.elements.sort(key=lambda e: e.material_index)
        return geo

    @staticmethod
    def spiral(params: Dict[str, Any]) -> GeometryCollection:
        """Archimedean spiral arms."""
        arm_dist = float(params.get("arm_dist", 12))
        circles = float(params.get("circles", 3))
        thickness = float(params.get("thickness", 1.5))
        sym_count = int(params.get("sym_count", 1))
        point_dist = float(params.get("point_dist", 0.25))

        b = arm_dist / 360.0
        angle_step = point_dist / b if b > 0 else 1.0
        max_pts = min(2000, int(circles * 360 / angle_step))

        base_pts: List[Pt] = []
        theta = 0.0
        for _ in range(max_pts):
            theta += angle_step
            r = b * theta
            rad = math.radians(theta)
            base_pts.append((r * math.cos(rad), r * math.sin(rad)))

        max_r = b * circles * 360
        elements: List[GeometryElement] = []

        for s in range(sym_count):
            ang = math.radians(s * 360.0 / sym_count)
            ca, sa = math.cos(ang), math.sin(ang)
            flip = s % 2 == 1 and sym_count > 1

            rotated = []
            for px, py in base_pts:
                fy = -py if flip else py
                rotated.append((px * ca - fy * sa, px * sa + fy * ca))

            elements.append(GeometryElement(
                kind="polyline", points=rotated,
                material_index=s % 2, stroke_width=thickness,
            ))

        return GeometryCollection(
            elements=elements,
            width_mm=max_r * 2, height_mm=max_r * 2,
            origin_x=max_r, origin_y=max_r,
            radial=True,
        )

    @staticmethod
    def sq_floral(params: Dict[str, Any]) -> GeometryCollection:
        """Radial ring of narrow kite petals."""
        n_fold = max(3, int(params.get("n_fold", 12)))
        outer_r = float(params.get("outer_r", 40))
        inner_r = float(params.get("inner_r", 14))

        step = 2 * math.pi / n_fold
        half_a = step / 2

        elements: List[GeometryElement] = []
        for k in range(n_fold):
            th = k * step
            p0 = (inner_r * math.cos(th - half_a * 0.7),
                  inner_r * math.sin(th - half_a * 0.7))
            p1 = (outer_r * math.cos(th), outer_r * math.sin(th))
            p2 = (inner_r * math.cos(th + half_a * 0.7),
                  inner_r * math.sin(th + half_a * 0.7))

            elements.append(GeometryElement(
                kind="polygon", points=[p0, p1, p2],
                material_index=k % 2, stroke_width=0.25,
                grain_angle=math.degrees(th),
            ))

        return GeometryCollection(
            elements=elements,
            width_mm=outer_r * 2, height_mm=outer_r * 2,
            origin_x=outer_r, origin_y=outer_r,
            radial=True,
        )

    @staticmethod
    def open_flower_oval(params: Dict[str, Any]) -> GeometryCollection:
        """N hook/comma petals arranged radially around an elliptical frame."""
        n_petals = max(4, int(params.get("n_petals", 18)))
        rx = float(params.get("rx", 35))
        ry = float(params.get("ry", 45))
        petal_r = float(params.get("petal_r", 14))
        petal_w = float(params.get("petal_w", 8))
        hook_depth = float(params.get("hook_depth", 0.55))
        pip_r = float(params.get("pip_r", 2))

        elements: List[GeometryElement] = []

        # Outer ellipse ring
        n_ring = 64
        ring_pts = [(rx * math.cos(i * 2 * math.pi / n_ring),
                     ry * math.sin(i * 2 * math.pi / n_ring))
                    for i in range(n_ring)]
        elements.append(GeometryElement(
            kind="polygon", points=ring_pts,
            material_index=0, stroke_width=0.3,
        ))

        # Hook petals
        step = 2 * math.pi / n_petals
        for k in range(n_petals):
            angle = k * step
            # Hook petal shape (simplified)
            tip_r = petal_r * 0.35
            far_r = tip_r + petal_r
            tip = (tip_r * math.cos(angle), tip_r * math.sin(angle))
            far = (far_r * math.cos(angle), far_r * math.sin(angle))
            pa = angle + math.pi / 2
            hook_r = tip_r + petal_r * hook_depth
            w_pt = (hook_r * math.cos(angle) + petal_w * math.cos(pa),
                    hook_r * math.sin(angle) + petal_w * math.sin(pa))

            pts = [tip, far, w_pt]
            elements.append(GeometryElement(
                kind="polygon", points=pts,
                material_index=k % 2, stroke_width=0.25,
                grain_angle=math.degrees(angle),
            ))

            # Inner pip
            pip_pts = circle_pts(tip[0] * 0.5, tip[1] * 0.5, pip_r, 12)
            elements.append(GeometryElement(
                kind="polygon", points=pip_pts,
                material_index=(k + 1) % 2, stroke_width=0.2,
            ))

        bbox = max(rx, ry) + petal_r
        return GeometryCollection(
            elements=elements,
            width_mm=bbox * 2, height_mm=bbox * 2,
            origin_x=bbox, origin_y=bbox,
            radial=True,
        )
