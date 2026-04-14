"""
Layered DXF Writer
==================

Writes DXF files with layer assignment from LayeredEntities.
Supports export presets for controlled output.

Format: R12 (AC1009) with LINE entities only.
Layers are created in DXF and entities assigned accordingly.

Phase 4: Fabrication-oriented export with layer control.

Author: Production Shop
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

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

logger = logging.getLogger(__name__)


# ─── Layer DXF Configuration ────────────────────────────────────────────────

# DXF layer colors (ACI color indices)
LAYER_DXF_COLORS = {
    Layer.BODY: 3,         # Green
    Layer.AUX_VIEWS: 5,    # Blue
    Layer.ANNOTATION: 30,  # Orange
    Layer.TITLE_BLOCK: 6,  # Magenta
    Layer.PAGE_FRAME: 1,   # Red
}


# ─── DXF Writer ─────────────────────────────────────────────────────────────

def write_layered_dxf(
    entities: LayeredEntities,
    output_path: str,
    preset: ExportPreset = ExportPreset.GEOMETRY_ONLY,
    include_layers: Optional[Set[Layer]] = None,
) -> Dict[str, int]:
    """
    Write layered entities to DXF file.

    Args:
        entities: LayeredEntities from build_layers()
        output_path: Output DXF file path
        preset: Export preset (geometry_only, geometry_plus_aux, reference_full)
        include_layers: Override preset with specific layers (optional)

    Returns:
        Dict with entity counts per layer
    """
    # Determine which layers to include
    if include_layers is not None:
        layers_to_export = include_layers
    else:
        layers_to_export = PRESET_LAYERS[preset]

    logger.info(f"Writing layered DXF: preset={preset.value}, layers={[l.value for l in layers_to_export]}")

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

    # Write entities
    for layer in layers_to_export:
        layer_entities = entities.get_layer(layer)

        for entity in layer_entities:
            lines_written = _write_contour_as_lines(
                msp=msp,
                contour=entity.contour,
                layer_name=layer.value,
                mm_per_px=entities.mm_per_px,
            )
            counts[layer.value] += 1
            total_lines += lines_written

    # Save
    doc.saveas(output_path)

    logger.info(f"Layered DXF written: {output_path}")
    logger.info(f"  Total entities: {sum(counts.values())}, Total lines: {total_lines}")
    for layer, count in counts.items():
        if count > 0:
            logger.info(f"  {layer}: {count}")

    return counts


def _write_contour_as_lines(
    msp,
    contour: np.ndarray,
    layer_name: str,
    mm_per_px: float,
) -> int:
    """
    Write a contour as LINE entities to DXF.

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

        # Flip Y axis (image Y is inverted from CAD Y)
        # Actually, keep as-is for now - let orchestrator handle orientation

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
