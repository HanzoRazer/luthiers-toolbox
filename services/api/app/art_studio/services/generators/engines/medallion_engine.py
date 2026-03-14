"""
Medallion Engine - Concentric layered patterns.

Generates medallion patterns like oak medallion, girih rosette,
and parquet panel with multiple concentric layers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from ..inlay_geometry import GeometryCollection, GeometryElement, Pt
from ..inlay_primitives import circle_pts, kite_pts


@dataclass
class MedallionLayer:
    """Configuration for one layer of a medallion."""
    shape_fn: Callable[[float, float, float, Dict[str, Any]], List[Pt]]
    shape_params: Dict[str, Any] = field(default_factory=dict)
    n_fold: int = 8
    inner_r: float = 10.0
    outer_r: float = 30.0
    material_offset: int = 0


@dataclass
class MedallionConfig:
    """Configuration for MedallionEngine."""
    layers: List[MedallionLayer] = field(default_factory=list)
    center_disc_r: float = 0.0
    center_material: int = 2


class MedallionEngine:
    """Engine for concentric layered patterns."""

    @staticmethod
    def generate(config: MedallionConfig) -> GeometryCollection:
        """Generate a medallion pattern with multiple concentric layers."""
        elements: List[GeometryElement] = []
        max_r = 0.0

        for layer in config.layers:
            step = 2 * math.pi / layer.n_fold
            for k in range(layer.n_fold):
                angle = k * step
                pts = layer.shape_fn(0, 0, angle, {**layer.shape_params, "index": k})
                mat_idx = (k + layer.material_offset) % 2

                elements.append(GeometryElement(
                    kind="polygon", points=pts,
                    material_index=mat_idx, stroke_width=0.25,
                    grain_angle=math.degrees(angle),
                ))

            max_r = max(max_r, layer.outer_r)

        # Center disc
        if config.center_disc_r > 0:
            disc_pts = circle_pts(0, 0, config.center_disc_r, 24)
            elements.append(GeometryElement(
                kind="polygon", points=disc_pts,
                material_index=config.center_material,
                stroke_width=0.25,
            ))

        return GeometryCollection(
            elements=elements,
            width_mm=max_r * 2,
            height_mm=max_r * 2,
            origin_x=max_r,
            origin_y=max_r,
            radial=True,
        )

    @staticmethod
    def oak_medallion(params: Dict[str, Any]) -> GeometryCollection:
        """N-fold kite ring with concentric layers."""
        n_fold = max(4, int(params.get("n_fold", 16)))
        inner_r = float(params.get("inner_r", 8))
        outer_r = float(params.get("outer_r", 35))
        kite_w = float(params.get("kite_w", 8))
        ring_count = max(1, min(3, int(params.get("ring_count", 2))))
        mid_r = float(params.get("mid_r", 13))
        inner_scale = float(params.get("inner_scale", 0.38))

        step = 2 * math.pi / n_fold
        elements: List[GeometryElement] = []

        for k in range(n_fold):
            angle = k * step

            # Primary kite
            pts = kite_pts(0, 0, inner_r, outer_r, kite_w, angle)
            elements.append(GeometryElement(
                kind="polygon", points=pts,
                material_index=k % 2, stroke_width=0.25,
                grain_angle=math.degrees(angle),
            ))

            # Inner kite (ring 2)
            if ring_count >= 2:
                r2_w = kite_w * inner_scale
                rl = inner_r + (mid_r - inner_r) * 0.4
                rr = inner_r + (mid_r - inner_r) * 1.3
                inner_angle = angle + step / 2
                pts2 = kite_pts(0, 0, rl, rr, r2_w, inner_angle)
                elements.append(GeometryElement(
                    kind="polygon", points=pts2,
                    material_index=(k + 1) % 2, stroke_width=0.25,
                ))

            # Outer accent (ring 3)
            if ring_count >= 3:
                r3_w = kite_w * inner_scale * 0.5
                pts3 = kite_pts(0, 0, outer_r * 0.85, outer_r * 1.05, r3_w, angle)
                elements.append(GeometryElement(
                    kind="polygon", points=pts3,
                    material_index=2, stroke_width=0.25,
                ))

        # Center disc
        disc_r = inner_r * 0.52
        disc_pts = circle_pts(0, 0, disc_r, 24)
        elements.append(GeometryElement(
            kind="polygon", points=disc_pts,
            material_index=2, stroke_width=0.25,
        ))

        bbox = outer_r * (1.05 if ring_count >= 3 else 1.0)
        return GeometryCollection(
            elements=elements,
            width_mm=bbox * 2, height_mm=bbox * 2,
            origin_x=bbox, origin_y=bbox,
            radial=True,
        )

    @staticmethod
    def girih_rosette(params: Dict[str, Any]) -> GeometryCollection:
        """Five-tile Girih Islamic geometry rosette."""
        edge_mm = float(params.get("edge_mm", 10))
        rot_deg = float(params.get("rotation_deg", 0))

        sin_pi10 = math.sin(math.pi / 10)
        sin_pi5 = math.sin(math.pi / 5)

        r_dec = edge_mm / (2.0 * sin_pi10)
        r_pent = edge_mm / (2.0 * sin_pi5)
        a_dec = r_dec * math.cos(math.pi / 10)
        a_pent = r_pent * math.cos(math.pi / 5)

        elements: List[GeometryElement] = []

        # Helper to place a regular polygon
        def place_polygon(n_sides: int, r: float, cx: float, cy: float,
                         rot: float, mat: int) -> None:
            pts = [(cx + r * math.cos(math.radians(rot) + i * 2 * math.pi / n_sides),
                    cy + r * math.sin(math.radians(rot) + i * 2 * math.pi / n_sides))
                   for i in range(n_sides)]
            elements.append(GeometryElement(
                kind="polygon", points=pts,
                material_index=mat, stroke_width=0.25,
            ))

        # Central decagon
        place_polygon(10, r_dec, 0, 0, rot_deg, 0)

        # 10 pentagons around decagon
        pent_dist = a_dec + a_pent
        for i in range(10):
            a = rot_deg + i * 36
            rad = math.radians(a)
            px = pent_dist * math.cos(rad)
            py = pent_dist * math.sin(rad)
            place_polygon(5, r_pent, px, py, a + 180, 1)

        # 5 rhombuses
        rhomb_dist = pent_dist + r_pent * 0.95
        for i in range(5):
            a = rot_deg + i * 72 + 18
            rad = math.radians(a)
            rx = rhomb_dist * math.cos(rad)
            ry = rhomb_dist * math.sin(rad)
            # Rhombus as 4-pt polygon
            elements.append(GeometryElement(
                kind="polygon",
                points=[(rx + edge_mm * 0.4 * math.cos(math.radians(a + j * 90)),
                         ry + edge_mm * 0.4 * math.sin(math.radians(a + j * 90)))
                        for j in range(4)],
                material_index=2, stroke_width=0.25,
            ))

        # Bounding
        all_x = [p[0] for e in elements for p in e.points]
        all_y = [p[1] for e in elements for p in e.points]
        r_outer = max(max(abs(v) for v in all_x) if all_x else 0,
                      max(abs(v) for v in all_y) if all_y else 0)
        size = r_outer * 2

        return GeometryCollection(
            elements=elements,
            width_mm=size, height_mm=size,
            origin_x=r_outer, origin_y=r_outer,
            radial=True,
        )

    @staticmethod
    def parquet_panel(params: Dict[str, Any]) -> GeometryCollection:
        """Parquet diamond panel with concentric layers and wedges."""
        size_mm = float(params.get("size_mm", 40))
        layers = int(params.get("layers", 4))

        w = size_mm * 0.8
        h = size_mm
        cx, cy = w / 2, h / 2

        elements: List[GeometryElement] = []

        # Concentric diamonds
        for li in range(layers):
            frac = 1.0 - li * 0.2
            hw = w * 0.45 * frac
            hh = h * 0.45 * frac
            pts = [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]
            elements.append(GeometryElement(
                kind="polygon", points=pts,
                material_index=li % 2, stroke_width=0.25,
            ))

        # Cross-hatching wedges (4 quadrant fills)
        for qi in range(4):
            a0 = qi * math.pi / 2 + math.pi / 4
            a1 = a0 + math.pi / 6
            r_outer = min(w, h) * 0.44
            pts_q: List[Pt] = [(cx, cy)]
            for s in range(7):
                a = a0 + (a1 - a0) * s / 6
                pts_q.append((cx + r_outer * math.cos(a), cy + r_outer * math.sin(a)))
            elements.append(GeometryElement(
                kind="polygon", points=pts_q,
                material_index=0, stroke_width=0.25,
            ))

        return GeometryCollection(
            elements=elements, width_mm=w, height_mm=h,
            radial=False,
        )
