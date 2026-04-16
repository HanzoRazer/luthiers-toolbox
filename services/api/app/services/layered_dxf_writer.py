"""
Layered DXF Writer
==================

Writes DXF files with layer assignment from LayeredEntities.
Supports export presets for controlled output.

Format: R12 (AC1009) with LINE entities only (default).
Phase 6B: Optional POLYLINE2D emission for accepted polyline runs.

Layers are created in DXF and entities assigned accordingly.

Phase 4: Fabrication-oriented export with layer control.
Phase 6B: Polyline emission for accepted primitives.

Author: Production Shop
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

import ezdxf
from ezdxf.enums import TextEntityAlignment
import numpy as np

from .layer_builder import (
    Layer,
    LayeredEntities,
    LayeredEntity,
    ExportPreset,
    PRESET_LAYERS,
)

if TYPE_CHECKING:
    from .body_geometry_repair import ReconstructedPrimitive

logger = logging.getLogger(__name__)


# ─── Layer DXF Configuration ────────────────────────────────────────────────

# DXF layer colors (ACI color indices)
# Using readable colors that work on both light and dark backgrounds
# 7 = white/black (adapts to background), 8 = gray, 9 = light gray
LAYER_DXF_COLORS = {
    Layer.BODY: 7,         # White/black - primary geometry
    Layer.AUX_VIEWS: 8,    # Gray - secondary geometry
    Layer.ANNOTATION: 7,   # White/black - readable text
    Layer.TITLE_BLOCK: 8,  # Gray - title block
    Layer.PAGE_FRAME: 9,   # Light gray - de-emphasized
}


# ─── DXF Writer ─────────────────────────────────────────────────────────────

def write_layered_dxf(
    entities: LayeredEntities,
    output_path: str,
    preset: ExportPreset = ExportPreset.GEOMETRY_ONLY,
    include_layers: Optional[Set[Layer]] = None,
    primitives: Optional[List["ReconstructedPrimitive"]] = None,
) -> Dict[str, int]:
    """
    Write layered entities to DXF file.

    Args:
        entities: LayeredEntities from build_layers()
        output_path: Output DXF file path
        preset: Export preset (geometry_only, geometry_plus_aux, reference_full)
        include_layers: Override preset with specific layers (optional)
        primitives: Phase 6B accepted primitives for POLYLINE emission (optional)

    Returns:
        Dict with entity counts per layer
    """
    # Determine which layers to include
    if include_layers is not None:
        layers_to_export = include_layers
    else:
        layers_to_export = PRESET_LAYERS[preset]

    # Phase 6B: Index accepted primitives by source contour for substitution
    primitive_map: Dict[int, List["ReconstructedPrimitive"]] = {}
    if primitives:
        for prim in primitives:
            if prim.source_contour_id is not None:
                if prim.source_contour_id not in primitive_map:
                    primitive_map[prim.source_contour_id] = []
                primitive_map[prim.source_contour_id].append(prim)

    has_primitives = bool(primitive_map)
    logger.info(
        f"Writing layered DXF: preset={preset.value}, "
        f"layers={[l.value for l in layers_to_export]}, "
        f"primitives={'YES' if has_primitives else 'NO'}"
    )

    # Create DXF document (R12 for compatibility)
    doc = ezdxf.new(dxfversion="R12")
    msp = doc.modelspace()

    # Create layers
    for layer in Layer:
        doc.layers.add(
            name=layer.value,
            color=LAYER_DXF_COLORS[layer],
        )

    # Track counts
    counts: Dict[str, int] = {layer.value: 0 for layer in Layer}
    total_lines = 0
    total_polylines = 0

    # Calculate image height in mm for Y-axis flip
    img_w, img_h = entities.image_size
    image_height_mm = img_h * entities.mm_per_px

    # Write entities
    for layer in layers_to_export:
        layer_entities = entities.get_layer(layer)

        for idx, entity in enumerate(layer_entities):
            # ─── Phase 6B: Confidence-gated BODY polyline substitution ───
            # This is BODY-only. Non-BODY layers always emit LINE (else branch).
            # Primitives only exist for BODY contours that passed positional
            # deviation acceptance (mean ≤ 0.5mm, max ≤ 1.5mm).
            # Rejected or uncovered BODY contours fall through to LINE emission.
            # This is additive — disable flags to restore prior behavior.
            if layer == Layer.BODY and idx in primitive_map:
                # Emit accepted polylines as R12-compatible POLYLINE2D
                for prim in primitive_map[idx]:
                    if prim.kind == "polyline" and prim.points:
                        _write_polyline2d(
                            msp=msp,
                            points=prim.points,
                            layer_name=layer.value,
                            image_height_mm=image_height_mm,
                        )
                        total_polylines += 1
                counts[layer.value] += 1
            else:
                # LINE fallback: rejected BODY runs, uncovered contours, non-BODY layers
                lines_written = _write_contour_as_lines(
                    msp=msp,
                    contour=entity.contour,
                    layer_name=layer.value,
                    mm_per_px=entities.mm_per_px,
                    image_height_mm=image_height_mm,
                )
                counts[layer.value] += 1
                total_lines += lines_written

    # Save
    doc.saveas(output_path)

    logger.info(f"Layered DXF written: {output_path}")
    logger.info(f"  Total entities: {sum(counts.values())}, Lines: {total_lines}, Polylines: {total_polylines}")
    for layer, count in counts.items():
        if count > 0:
            logger.info(f"  {layer}: {count}")

    return counts


def _write_polyline2d(
    msp,
    points: List[Tuple[float, float]],
    layer_name: str,
    image_height_mm: float,
) -> None:
    """
    Write points as an R12-compatible POLYLINE2D entity.

    Phase 6B: Used for accepted polyline runs to reduce entity count.
    Points are already in mm coordinates from body_geometry_repair.

    Args:
        msp: DXF modelspace
        points: List of (x, y) in mm coordinates
        layer_name: Target layer name
        image_height_mm: Image height for Y-axis flip
    """
    if len(points) < 2:
        return

    # Flip Y axis for CAD: CAD_Y = image_height - image_Y
    flipped_points = [
        (x, image_height_mm - y)
        for x, y in points
    ]

    # R12 uses add_polyline2d for old-style POLYLINE entity
    msp.add_polyline2d(
        flipped_points,
        dxfattribs={"layer": layer_name},
        close=False,  # Don't auto-close; runs are segments
    )


def _write_contour_as_lines(
    msp,
    contour: np.ndarray,
    layer_name: str,
    mm_per_px: float,
    image_height_mm: float,
) -> int:
    """
    Write a contour as LINE entities to DXF.

    Flips Y axis: image Y (0=top, increases down) → CAD Y (0=bottom, increases up)

    Returns number of lines written.
    """
    if len(contour) < 2:
        return 0

    # Flatten contour if needed
    points = contour.reshape(-1, 2)
    lines_written = 0

    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]  # Wrap to close

        # Convert to mm
        x1, y1 = p1[0] * mm_per_px, p1[1] * mm_per_px
        x2, y2 = p2[0] * mm_per_px, p2[1] * mm_per_px

        # Flip Y axis: CAD_Y = image_height - image_Y
        y1 = image_height_mm - y1
        y2 = image_height_mm - y2

        msp.add_line(
            start=(x1, y1),
            end=(x2, y2),
            dxfattribs={"layer": layer_name},
        )
        lines_written += 1

    return lines_written


def get_preset_from_string(preset_str: str) -> ExportPreset:
    """Convert string to ExportPreset enum."""
    preset_map = {
        "geometry_only": ExportPreset.GEOMETRY_ONLY,
        "geometry_plus_aux": ExportPreset.GEOMETRY_PLUS_AUX,
        "reference_full": ExportPreset.REFERENCE_FULL,
    }
    return preset_map.get(preset_str.lower(), ExportPreset.GEOMETRY_ONLY)


def get_included_layers(preset: ExportPreset) -> List[str]:
    """Get list of layer names included in a preset."""
    return [layer.value for layer in PRESET_LAYERS[preset]]
