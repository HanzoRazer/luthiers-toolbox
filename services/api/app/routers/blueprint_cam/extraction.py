"""
Blueprint CAM Extraction Utilities
==================================

DXF loop extraction utilities for CAM integration.
"""

import os
import tempfile
from typing import List, Tuple

import ezdxf

from ..blueprint_cam_bridge_schemas import Loop


def extract_loops_from_dxf(dxf_bytes: bytes, layer_name: str = "GEOMETRY") -> Tuple[List[Loop], List[str]]:
    """
    Extract closed LWPOLYLINE loops from DXF file.

    Args:
        dxf_bytes: DXF file content
        layer_name: Layer to extract from (default: GEOMETRY)

    Returns:
        (loops, warnings) where loops is List[Loop] and warnings is List[str]

    Notes:
        - First loop is outer boundary, rest are islands
        - Open polylines are skipped with warning
        - Minimum 3 points required per loop
    """
    warnings = []
    loops = []

    try:
        # Write bytes to temp file and read with ezdxf (avoids text/binary issues)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp:
            tmp.write(dxf_bytes)
            tmp_path = tmp.name

        try:
            doc = ezdxf.readfile(tmp_path)
            msp = doc.modelspace()
        finally:
            os.unlink(tmp_path)

        # Query for LWPOLYLINE entities on specified layer
        all_entities = list(msp)
        all_lwpolylines = [e for e in all_entities if e.dxftype() == 'LWPOLYLINE']
        entities = [e for e in all_lwpolylines if e.dxf.layer == layer_name]

        # Debug: Log what we found
        if not all_entities:
            warnings.append("DXF modelspace is empty")
        elif not all_lwpolylines:
            entity_types = list(set([e.dxftype() for e in all_entities]))
            warnings.append(f"No LWPOLYLINE entities found. Entity types: {entity_types}")

        if not entities:
            if all_lwpolylines:
                layers_found = list(set([e.dxf.layer for e in all_lwpolylines]))
                warnings.append(f"No LWPOLYLINE on layer '{layer_name}'. Found layers: {layers_found}")
            else:
                warnings.append(f"No LWPOLYLINE entities found on layer '{layer_name}'")
            # Try fallback to all LWPOLYLINE entities
            entities = list(msp.query('LWPOLYLINE'))
            if entities:
                warnings.append(f"Found {len(entities)} LWPOLYLINE entities on other layers, using those instead")

        # Extract points from each closed LWPOLYLINE
        for entity in entities:
            if not entity.closed:
                warnings.append("Skipping open LWPOLYLINE (not closed)")
                continue

            try:
                # Get points (x, y) - ignore bulge for now
                points = [(p[0], p[1]) for p in entity.get_points()]

                if len(points) < 3:
                    warnings.append(f"Skipping LWPOLYLINE with only {len(points)} points (need at least 3)")
                    continue

                # Remove duplicate last point if it equals first (some CAD systems add it)
                if len(points) > 1 and points[0] == points[-1]:
                    points = points[:-1]

                loops.append(Loop(pts=points))

            except (ValueError, TypeError, KeyError) as e:
                warnings.append(f"Error extracting LWPOLYLINE points: {str(e)}")

        if not loops:
            warnings.append("No valid closed loops extracted from DXF")

    except ezdxf.DXFError as e:
        warnings.append(f"DXF parsing error: {str(e)}")
    except (ValueError, TypeError, KeyError, OSError) as e:
        warnings.append(f"Unexpected error reading DXF: {str(e)}")

    return loops, warnings
