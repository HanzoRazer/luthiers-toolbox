"""
Path Engine - Patterns along a backbone curve.

Generates path-following patterns like vine scroll, floral spray,
binding flow, rope border motif, and twisted rope.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..inlay_geometry import GeometryCollection, GeometryElement, Polyline, Pt
from ..inlay_primitives import (
    cubic_bezier_point,
    cubic_bezier_tangent,
    lens_pts,
    offset_polyline_strip,
    sample_bezier,
    sample_spline,
    sine_backbone,
    straight_backbone,
    s_wave_backbone,
    teardrop_pts,
)


@dataclass
class PathConfig:
    """Configuration for PathEngine."""
    length_mm: float = 120.0
    backbone_type: str = "straight"  # straight, sine, swave, bezier, custom
    amplitude: float = 10.0
    frequency: float = 1.0
    n_backbone_pts: int = 50
    custom_pts: Optional[Polyline] = None
    bezier_controls: Optional[Tuple[Pt, Pt, Pt, Pt]] = None


class PathEngine:
    """Engine for patterns along a backbone curve."""

    @staticmethod
    def build_backbone(config: PathConfig) -> Polyline:
        """Build backbone curve based on config."""
        if config.backbone_type == "straight":
            return straight_backbone(config.length_mm, config.n_backbone_pts)
        elif config.backbone_type == "sine":
            return sine_backbone(config.length_mm, config.amplitude,
                               config.frequency, config.n_backbone_pts)
        elif config.backbone_type == "swave":
            return s_wave_backbone(config.length_mm, config.amplitude, config.n_backbone_pts)
        elif config.backbone_type == "bezier" and config.bezier_controls:
            p0, p1, p2, p3 = config.bezier_controls
            return sample_bezier(p0, p1, p2, p3, config.n_backbone_pts)
        elif config.backbone_type == "custom" and config.custom_pts:
            return sample_spline(config.custom_pts, config.n_backbone_pts)
        else:
            return straight_backbone(config.length_mm, config.n_backbone_pts)

    @staticmethod
    def generate(
        attachment_fn: Callable[[float, float, float, Dict[str, Any]], List[Pt]],
        attachment_params: Dict[str, Any],
        config: PathConfig,
        n_attachments: int = 8,
        stem_width: float = 1.5,
        alternate_sides: bool = True,
    ) -> GeometryCollection:
        """
        Generate a path-following pattern.

        Args:
            attachment_fn: Function(x, y, angle, params) -> List[Pt] for attachments
            attachment_params: Parameters passed to attachment_fn
            config: Path configuration
            n_attachments: Number of attachments along path
            stem_width: Width of the stem/backbone strip
            alternate_sides: Alternate attachments left/right
        """
        backbone = PathEngine.build_backbone(config)
        elements: List[GeometryElement] = []

        # Stem as polygon strip
        if stem_width > 0:
            stem_strip = offset_polyline_strip(backbone, stem_width / 2)
            elements.append(GeometryElement(
                kind="polygon", points=stem_strip,
                material_index=0, stroke_width=0.25,
            ))

        # Attachments along backbone
        n_pts = len(backbone)
        step = max(1, n_pts // n_attachments)

        for i in range(n_attachments):
            idx = min((i + 1) * step, n_pts - 2)
            px, py = backbone[idx]
            nx_idx = min(idx + 1, n_pts - 1)
            nx, ny = backbone[nx_idx]
            tang = math.atan2(ny - py, nx - px)

            side = 1 if (i % 2 == 0 or not alternate_sides) else -1
            attach_angle = tang + side * 1.4

            pts = attachment_fn(px, py, attach_angle, {**attachment_params, "index": i})
            elements.append(GeometryElement(
                kind="polygon", points=pts,
                material_index=1, stroke_width=0.2,
            ))

        # Compute bounding box
        all_x = [p[0] for e in elements for p in e.points]
        all_y = [p[1] for e in elements for p in e.points]
        min_x, max_x = min(all_x, default=0), max(all_x, default=0)
        min_y, max_y = min(all_y, default=0), max(all_y, default=0)

        return GeometryCollection(
            elements=elements,
            width_mm=max_x - min_x,
            height_mm=max_y - min_y,
            origin_x=-min_x,
            origin_y=-min_y,
            radial=False,
        )

    @staticmethod
    def vine_scroll(params: Dict[str, Any]) -> GeometryCollection:
        """Vine scroll with teardrop leaves."""
        curl = float(params.get("curl", 3.0))
        n_leaves = int(params.get("leaves", 8))
        vwidth = float(params.get("vwidth", 1.5))
        leafsize = float(params.get("leafsize", 6))
        length_mm = float(params.get("length_mm", 120))
        segments = int(params.get("segments", 28))

        # Build freq-modulated backbone
        seg_len = length_mm / segments
        backbone: Polyline = [(-length_mm / 2, 0.0)]
        heading = math.pi / 2
        x, y = backbone[0]
        for i in range(segments):
            x += math.cos(heading) * seg_len
            y += math.sin(heading) * seg_len
            backbone.append((x, y))
            heading += math.sin(i * 0.38) * curl * 0.4

        def leaf_fn(px: float, py: float, angle: float, p: Dict[str, Any]) -> List[Pt]:
            return teardrop_pts(px, py, leafsize, leafsize * 0.6, angle)

        elements: List[GeometryElement] = []

        # Stem
        stem_strip = offset_polyline_strip(backbone, vwidth / 2)
        elements.append(GeometryElement(
            kind="polygon", points=stem_strip,
            material_index=0, stroke_width=0.25,
        ))

        # Leaves
        if n_leaves > 0:
            leaf_step = max(1, segments // n_leaves)
            for li in range(n_leaves):
                idx = min((li + 1) * leaf_step, len(backbone) - 2)
                px, py = backbone[idx]
                nx, ny = backbone[min(idx + 1, len(backbone) - 1)]
                tang = math.atan2(ny - py, nx - px)
                side = 1 if li % 2 == 0 else -1
                leaf_angle = tang + side * 1.4
                pts = teardrop_pts(px, py, leafsize, leafsize * 0.6, leaf_angle)
                elements.append(GeometryElement(
                    kind="polygon", points=pts,
                    material_index=1, stroke_width=0.2,
                ))

        all_x = [p[0] for e in elements for p in e.points]
        all_y = [p[1] for e in elements for p in e.points]
        min_x, max_x = min(all_x, default=0), max(all_x, default=0)
        min_y, max_y = min(all_y, default=0), max(all_y, default=0)

        return GeometryCollection(
            elements=elements,
            width_mm=max_x - min_x,
            height_mm=max_y - min_y,
            origin_x=-min_x,
            origin_y=-min_y,
            radial=False,
        )

    @staticmethod
    def floral_spray(params: Dict[str, Any]) -> GeometryCollection:
        """Cubic Bezier stem with lens petals."""
        n_petals = max(1, int(params.get("n_petals", 5)))
        petal_l = float(params.get("petal_l", 12))
        petal_w = float(params.get("petal_w", 5))
        stem_wave = float(params.get("stem_wave", 12))
        leaf_l = float(params.get("leaf_l", 18))
        leaf_w = float(params.get("leaf_w", 7))
        alternate = bool(params.get("alternate", True))
        W = float(params.get("width_mm", 80))
        H = float(params.get("height_mm", 50))

        pad = 8
        x0, y0 = pad, H - pad
        x3, y3 = W - pad, pad
        cp1 = (x0 + stem_wave, y0 - (H - 2 * pad) * 0.35)
        cp2 = (x3 - stem_wave, y3 + (H - 2 * pad) * 0.35)

        elements: List[GeometryElement] = []

        # Stem as polyline
        stem_pts = sample_bezier((x0, y0), cp1, cp2, (x3, y3), 50)
        elements.append(GeometryElement(
            kind="polyline", points=stem_pts,
            material_index=2, stroke_width=1.5,
        ))

        # Petals
        for i in range(n_petals):
            t = (i + 0.5) / n_petals
            pt = cubic_bezier_point((x0, y0), cp1, cp2, (x3, y3), t)
            tan = cubic_bezier_tangent((x0, y0), cp1, cp2, (x3, y3), t)
            stem_angle = math.degrees(math.atan2(tan[1], tan[0]))

            side = (1 if i % 2 else -1) if alternate else 1
            petal_angle = stem_angle + side * 30

            pts = lens_pts(pt[0], pt[1], petal_l, petal_w, petal_angle)
            elements.append(GeometryElement(
                kind="polygon", points=pts,
                material_index=0, stroke_width=0.25,
                grain_angle=petal_angle,
            ))

            if alternate:
                petal_angle2 = stem_angle - side * 20
                pts2 = lens_pts(pt[0], pt[1], petal_l * 0.7, petal_w * 0.7, petal_angle2)
                elements.append(GeometryElement(
                    kind="polygon", points=pts2,
                    material_index=1, stroke_width=0.25,
                ))

        # Base leaves
        for i, t in enumerate([0.15, 0.28, 0.44]):
            pt = cubic_bezier_point((x0, y0), cp1, cp2, (x3, y3), t)
            tan = cubic_bezier_tangent((x0, y0), cp1, cp2, (x3, y3), t)
            sa = math.degrees(math.atan2(tan[1], tan[0]))
            leaf_angle = sa + (1 if i % 2 else -1) * 55

            pts = lens_pts(pt[0], pt[1], leaf_l, leaf_w, leaf_angle)
            elements.append(GeometryElement(
                kind="polygon", points=pts,
                material_index=1, stroke_width=0.25,
            ))

        return GeometryCollection(
            elements=elements,
            width_mm=W, height_mm=H,
            radial=False,
        )

    @staticmethod
    def binding_flow(params: Dict[str, Any]) -> GeometryCollection:
        """Catmull-Rom contour with vine wrapping for binding channels."""
        length_mm = float(params.get("length_mm", 150))
        amplitude = float(params.get("amplitude", 8))
        stem_width = float(params.get("stem_width", 2.5))
        n_leaves = int(params.get("n_leaves", 6))
        leaf_size = float(params.get("leaf_size", 5))

        # Build S-wave backbone
        backbone = s_wave_backbone(length_mm, amplitude, 60)
        elements: List[GeometryElement] = []

        # Stem strip
        stem_strip = offset_polyline_strip(backbone, stem_width / 2)
        elements.append(GeometryElement(
            kind="polygon", points=stem_strip,
            material_index=0, stroke_width=0.25,
        ))

        # Leaves along backbone
        if n_leaves > 0:
            step = len(backbone) // n_leaves
            for li in range(n_leaves):
                idx = min((li + 1) * step, len(backbone) - 2)
                px, py = backbone[idx]
                nx, ny = backbone[min(idx + 1, len(backbone) - 1)]
                tang = math.atan2(ny - py, nx - px)
                side = 1 if li % 2 == 0 else -1
                leaf_angle = tang + side * 1.3

                pts = teardrop_pts(px, py, leaf_size, leaf_size * 0.6, leaf_angle)
                elements.append(GeometryElement(
                    kind="polygon", points=pts,
                    material_index=1, stroke_width=0.2,
                ))

        all_x = [p[0] for e in elements for p in e.points]
        all_y = [p[1] for e in elements for p in e.points]
        min_x, max_x = min(all_x, default=0), max(all_x, default=0)
        min_y, max_y = min(all_y, default=0), max(all_y, default=0)

        return GeometryCollection(
            elements=elements,
            width_mm=max_x - min_x, height_mm=max_y - min_y,
            origin_x=-min_x, origin_y=-min_y,
            radial=False,
        )

    @staticmethod
    def rope_border_motif(params: Dict[str, Any]) -> GeometryCollection:
        """Static rope border motif — interleaving S-curve strands."""
        band_w = float(params.get("band_w_mm", 60))
        repeats = int(params.get("repeats", 4))
        material = int(params.get("material", 0))

        unit_w = band_w / repeats
        unit_h = unit_w * 0.22

        elements: List[GeometryElement] = []
        n_pts = 30
        for ri in range(repeats):
            ox = ri * unit_w
            for strand in range(2):
                phase = strand * math.pi
                pts: Polyline = []
                for i in range(n_pts):
                    t = i / (n_pts - 1)
                    x = ox + t * unit_w
                    y = unit_h * 0.5 + math.sin(t * 2 * math.pi + phase) * unit_h * 0.35
                    pts.append((x, y))
                strip = offset_polyline_strip(pts, unit_h * 0.08)
                elements.append(GeometryElement(
                    kind="polygon", points=strip,
                    material_index=(material + strand) % 3, stroke_width=0.25,
                ))

        return GeometryCollection(
            elements=elements, width_mm=band_w, height_mm=unit_h,
            radial=False, tile_w=unit_w, tile_h=unit_h,
        )

    @staticmethod
    def twisted_rope(params: Dict[str, Any]) -> GeometryCollection:
        """Parametric twisted rope inlay band."""
        num_strands = max(2, min(5, int(params.get("num_strands", 3))))
        rope_width = float(params.get("rope_width", 6))
        twist_per_mm = float(params.get("twist_per_mm", 0.25))
        strand_width_frac = max(0.2, min(0.9, float(params.get("strand_width", 0.55))))
        length_mm = float(params.get("length_mm", 120))
        amplitude = float(params.get("amplitude", 10))
        shape = str(params.get("shape", "straight"))

        rope_radius = rope_width / 2

        # Build centerline
        if shape == "swave":
            centerline = s_wave_backbone(length_mm, amplitude, 60)
        elif shape == "sine":
            centerline = sine_backbone(length_mm, amplitude, 1.0, 60)
        else:
            centerline = straight_backbone(length_mm, 60)

        elements: List[GeometryElement] = []

        # Centerline
        elements.append(GeometryElement(
            kind="polyline", points=centerline,
            material_index=0, stroke_width=0.15,
        ))

        # Generate strand paths (simplified helix around centerline)
        for k in range(num_strands):
            strand_pts: Polyline = []
            phase_offset = k * 2 * math.pi / num_strands
            strand_w = rope_radius * strand_width_frac

            for i, (cx, cy) in enumerate(centerline):
                t = i / len(centerline)
                angle = t * length_mm * twist_per_mm + phase_offset
                offset_x = math.cos(angle) * rope_radius * 0.7
                offset_y = math.sin(angle) * rope_radius * 0.7
                strand_pts.append((cx + offset_x, cy + offset_y))

            strip = offset_polyline_strip(strand_pts, strand_w * 0.5)
            elements.append(GeometryElement(
                kind="polygon", points=strip,
                material_index=k % 3, stroke_width=0.25,
            ))

        # Envelope
        envelope = offset_polyline_strip(centerline, rope_radius * 1.05)
        elements.append(GeometryElement(
            kind="polygon", points=envelope,
            material_index=0, stroke_width=0.15,
        ))

        all_x = [p[0] for e in elements for p in e.points]
        all_y = [p[1] for e in elements for p in e.points]
        min_x, max_x = min(all_x, default=0), max(all_x, default=0)
        min_y, max_y = min(all_y, default=0), max(all_y, default=0)

        return GeometryCollection(
            elements=elements,
            width_mm=max_x - min_x, height_mm=max_y - min_y,
            origin_x=-min_x, origin_y=-min_y,
            radial=False,
        )
