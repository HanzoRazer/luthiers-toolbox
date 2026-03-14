"""
Grid Engine - Tile repetition on a 2D grid.

Generates grid-based patterns like herringbone, diamond, checker,
greek key, hex chain, chevron panel, nested diamond, and block pin.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from ..inlay_geometry import GeometryCollection, GeometryElement, Pt
from ..inlay_primitives import (
    checkerboard_material,
    diamond_pts,
    hexagon_pts,
)


@dataclass
class GridConfig:
    """Configuration for GridEngine."""
    cell_w: float = 10.0
    cell_h: float = 10.0
    band_w: float = 120.0
    band_h: float = 40.0
    offset_odd_rows: float = 0.0  # Horizontal offset for odd rows (brick pattern)
    offset_odd_cols: float = 0.0  # Vertical offset for odd columns
    material_fn: Callable[[int, int], int] = checkerboard_material


class GridEngine:
    """Engine for grid-based tile patterns."""

    @staticmethod
    def generate(
        shape_fn: Callable[[float, float, Dict[str, Any]], List[Pt]],
        shape_params: Dict[str, Any],
        config: GridConfig,
    ) -> GeometryCollection:
        """
        Generate a grid pattern.

        Args:
            shape_fn: Function(cx, cy, params) -> List[Pt] for tile shape
            shape_params: Parameters passed to shape_fn
            config: Grid configuration

        Returns:
            GeometryCollection with tiled elements
        """
        cols = math.ceil(config.band_w / config.cell_w) + 1
        rows = math.ceil(config.band_h / config.cell_h) + 1

        elements: List[GeometryElement] = []
        for row in range(rows):
            for col in range(cols):
                # Calculate center with offsets
                cx = col * config.cell_w + config.cell_w / 2
                cy = row * config.cell_h + config.cell_h / 2

                if row % 2 == 1:
                    cx += config.offset_odd_rows
                if col % 2 == 1:
                    cy += config.offset_odd_cols

                # Generate shape
                pts = shape_fn(cx, cy, {**shape_params, "row": row, "col": col})
                mat_idx = config.material_fn(row, col)

                elements.append(GeometryElement(
                    kind="polygon",
                    points=pts,
                    material_index=mat_idx,
                    stroke_width=0.25,
                ))

        return GeometryCollection(
            elements=elements,
            width_mm=config.band_w,
            height_mm=config.band_h,
            radial=False,
            tile_w=config.cell_w * 2,
            tile_h=config.cell_h,
        )

    @staticmethod
    def herringbone(params: Dict[str, Any]) -> GeometryCollection:
        """Herringbone pattern using GridEngine."""
        tw = float(params.get("tooth_w", 10))
        th = float(params.get("tooth_h", 20))

        def shape_fn(cx: float, cy: float, p: Dict[str, Any]) -> List[Pt]:
            row, col = p["row"], p["col"]
            vert = (row + col) % 2 == 0
            w = tw if vert else th
            h = th if vert else tw
            x0, y0 = cx - w / 2, cy - h / 2
            return [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]

        config = GridConfig(
            cell_w=tw, cell_h=th,
            band_w=float(params.get("band_w", 120)),
            band_h=float(params.get("band_h", 22)),
        )
        return GridEngine.generate(shape_fn, {}, config)

    @staticmethod
    def diamond(params: Dict[str, Any]) -> GeometryCollection:
        """Diamond wave pattern using GridEngine."""
        tw = float(params.get("tile_w", 14))
        th = float(params.get("tile_h", 22))
        wave = float(params.get("wave", 0.35))
        lean = float(params.get("lean", 0.1))

        def shape_fn(cx: float, cy: float, p: Dict[str, Any]) -> List[Pt]:
            row, col = p["row"], p["col"]
            phase = (col * 0.5 + row * 0.3) * math.pi
            return diamond_pts(cx, cy, tw, th, wave, lean, phase)

        config = GridConfig(
            cell_w=tw, cell_h=th,
            band_w=float(params.get("band_w", 120)),
            band_h=float(params.get("band_h", 22)),
        )
        return GridEngine.generate(shape_fn, {}, config)

    @staticmethod
    def checker_chevron(params: Dict[str, Any]) -> GeometryCollection:
        """Diamond grid with alternating materials."""
        cell_w = float(params.get("cell_w", 10))
        diamond_r = float(params.get("diamond_r", 8))

        def shape_fn(cx: float, cy: float, p: Dict[str, Any]) -> List[Pt]:
            r = min(diamond_r, cell_w * 0.48)
            return [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]

        config = GridConfig(
            cell_w=cell_w, cell_h=cell_w,
            band_w=float(params.get("band_w", 120)),
            band_h=float(params.get("band_h", 40)),
        )
        return GridEngine.generate(shape_fn, {}, config)

    @staticmethod
    def greek_key(params: Dict[str, Any]) -> GeometryCollection:
        """Greek key meander pattern."""
        cs = float(params.get("cell_size", 10))
        uw, uh = cs * 4, cs * 4

        def shape_fn(cx: float, cy: float, p: Dict[str, Any]) -> List[Pt]:
            # Meander key centered at (cx, cy)
            ox, oy = cx - uw / 2, cy - uh / 2
            return [
                (ox, oy), (ox + cs * 3, oy), (ox + cs * 3, oy + cs * 3),
                (ox + cs, oy + cs * 3), (ox + cs, oy + cs),
                (ox + cs * 2, oy + cs), (ox + cs * 2, oy + cs * 2), (ox, oy + cs * 2),
            ]

        def uniform_material(row: int, col: int) -> int:
            return 0

        config = GridConfig(
            cell_w=uw, cell_h=uh,
            band_w=float(params.get("band_w", 120)),
            band_h=float(params.get("band_h", 22)),
            material_fn=uniform_material,
        )
        return GridEngine.generate(shape_fn, {}, config)

    @staticmethod
    def hex_chain(params: Dict[str, Any]) -> GeometryCollection:
        """Vertical hex chain band with cutouts and connectors."""
        cell_w = float(params.get("cell_w", 16))
        cell_h = float(params.get("cell_h", 20))
        band_w = float(params.get("band_w", 120))
        band_h = float(params.get("band_h", 22))

        def shape_fn(cx: float, cy: float, p: Dict[str, Any]) -> List[Pt]:
            return hexagon_pts(cx, cy, min(cell_w, cell_h) * 0.4, flat_top=True)

        config = GridConfig(
            cell_w=cell_w, cell_h=cell_h,
            band_w=band_w, band_h=band_h,
            offset_odd_rows=cell_w / 2,
        )
        return GridEngine.generate(shape_fn, {}, config)

    @staticmethod
    def chevron_panel(params: Dict[str, Any]) -> GeometryCollection:
        """Nested chevron band pattern."""
        cell_w = float(params.get("cell_w", 20))
        cell_h = float(params.get("cell_h", 15))
        band_w = float(params.get("band_w", 120))
        band_h = float(params.get("band_h", 30))

        def shape_fn(cx: float, cy: float, p: Dict[str, Any]) -> List[Pt]:
            hw, hh = cell_w * 0.4, cell_h * 0.4
            return [(cx - hw, cy), (cx, cy - hh), (cx + hw, cy), (cx, cy + hh)]

        config = GridConfig(
            cell_w=cell_w, cell_h=cell_h,
            band_w=band_w, band_h=band_h,
        )
        return GridEngine.generate(shape_fn, {}, config)

    @staticmethod
    def nested_diamond(params: Dict[str, Any]) -> GeometryCollection:
        """Band of nested diamond groups with corner accents."""
        band_w = float(params.get("band_w_mm", 60))
        diamonds = int(params.get("diamonds", 4))
        nest_depth = int(params.get("nest_depth", 3))

        cell_w = band_w / diamonds
        band_h = cell_w * 0.32

        elements: List[GeometryElement] = []
        for di in range(diamonds):
            cx = di * cell_w + cell_w / 2
            cy = band_h / 2
            for ni in range(nest_depth):
                frac = 1.0 - ni * 0.25
                hw = cell_w * 0.4 * frac
                hh = band_h * 0.42 * frac
                pts = [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]
                elements.append(GeometryElement(
                    kind="polygon", points=pts,
                    material_index=ni % 2, stroke_width=0.25,
                ))

            # Corner accent diamonds
            accent_r = cell_w * 0.06
            for ax_off, ay_off in [(-0.38, -0.35), (0.38, -0.35),
                                    (-0.38, 0.35), (0.38, 0.35)]:
                ax = cx + cell_w * ax_off
                ay = cy + band_h * ay_off
                pts_a = [(ax, ay - accent_r), (ax + accent_r, ay),
                         (ax, ay + accent_r), (ax - accent_r, ay)]
                elements.append(GeometryElement(
                    kind="polygon", points=pts_a,
                    material_index=0, stroke_width=0.2,
                ))

        return GeometryCollection(
            elements=elements, width_mm=band_w, height_mm=band_h,
            radial=False, tile_w=cell_w, tile_h=band_h,
        )

    @staticmethod
    def block_pin(params: Dict[str, Any]) -> GeometryCollection:
        """Alternating columns of diamond accents and rectangular pins."""
        col_w = float(params.get("col_w", 15))
        cell_h = float(params.get("cell_h", 22))
        diamond_r = float(params.get("diamond_r", 6))
        band_w = float(params.get("band_w", 120))
        band_h = float(params.get("band_h", 40))

        rect_h = cell_h * 0.35
        cols = math.ceil(band_w / col_w) + 1
        rows = math.ceil(band_h / cell_h) + 1

        elements: List[GeometryElement] = []
        for col in range(cols):
            cx = col * col_w + col_w / 2
            is_diamond_col = col % 2 == 0
            y_offset = cell_h / 2 if col % 2 == 1 else 0.0

            for row in range(rows + 1):
                cy = row * cell_h + y_offset
                if cy > band_h + cell_h:
                    break

                if is_diamond_col:
                    r = min(diamond_r, col_w * 0.4)
                    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
                    elements.append(GeometryElement(
                        kind="polygon", points=pts,
                        material_index=0, stroke_width=0.25,
                    ))
                else:
                    hw = col_w * 0.35
                    hh = rect_h / 2
                    pts = [(cx - hw, cy - hh), (cx + hw, cy - hh),
                           (cx + hw, cy + hh), (cx - hw, cy + hh)]
                    elements.append(GeometryElement(
                        kind="polygon", points=pts,
                        material_index=1, stroke_width=0.25,
                    ))

        return GeometryCollection(
            elements=elements, width_mm=band_w, height_mm=band_h,
            radial=False, tile_w=col_w * 2, tile_h=cell_h,
        )
