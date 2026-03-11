"""
Contour Reconstruction Pipeline
================================

Pipeline module for reconstructing closed contours from scattered LINE/ARC entities.

Resolves: VINE-09 (Bracing DXF has raw lines/arcs, not closed contours)

The problem: CAD drawings often contain brace outlines as collections of individual
LINE and ARC entities rather than closed LWPOLYLINE contours. The CAM pipeline
requires closed polylines to define pocket boundaries.

Solution: Chain LINE/ARC entities by endpoint proximity to form closed loops,
then convert each loop to a closed LWPOLYLINE.

Usage:
    result = reconstruct_contours(
        dxf_bytes=bytes,
        layer_name="TOP_BRACING",
        tolerance_mm=0.5,
    )
"""

from __future__ import annotations

import math
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import ezdxf
from ezdxf.math import Vec2


@dataclass
class EntityEndpoints:
    """Represents an entity with its start and end points."""
    entity_id: int
    entity_type: str
    start: Tuple[float, float]
    end: Tuple[float, float]
    points: List[Tuple[float, float]]  # All points along the entity
    used: bool = False


@dataclass
class ContourLoop:
    """A reconstructed closed contour."""
    points: List[Tuple[float, float]]
    entity_count: int
    is_closed: bool
    perimeter_mm: float = 0.0
    bounds: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # min_x, min_y, max_x, max_y


@dataclass
class ReconstructionResult:
    """Result of contour reconstruction."""
    success: bool = False
    dxf_bytes: bytes = b""

    # Stats
    total_entities: int = 0
    entities_used: int = 0
    entities_orphaned: int = 0
    contours_found: int = 0
    closed_contours: int = 0
    open_chains: int = 0

    # Contour details
    contours: List[ContourLoop] = field(default_factory=list)

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _arc_to_points(
    center: Tuple[float, float],
    radius: float,
    start_angle: float,
    end_angle: float,
    segments: int = 16,
) -> List[Tuple[float, float]]:
    """Convert arc to polyline points."""
    points = []

    # Handle arc direction (CCW)
    if end_angle < start_angle:
        end_angle += 360.0

    angle_span = end_angle - start_angle
    for i in range(segments + 1):
        t = i / segments
        angle = math.radians(start_angle + t * angle_span)
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))

    return points


def _extract_entity_endpoints(entity) -> Optional[EntityEndpoints]:
    """Extract start/end points and intermediate points from an entity."""

    if entity.dxftype() == "LINE":
        start = (entity.dxf.start.x, entity.dxf.start.y)
        end = (entity.dxf.end.x, entity.dxf.end.y)
        return EntityEndpoints(
            entity_id=id(entity),
            entity_type="LINE",
            start=start,
            end=end,
            points=[start, end],
        )

    elif entity.dxftype() == "ARC":
        center = (entity.dxf.center.x, entity.dxf.center.y)
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle

        # Arc endpoints
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        start = (center[0] + radius * math.cos(start_rad), center[1] + radius * math.sin(start_rad))
        end = (center[0] + radius * math.cos(end_rad), center[1] + radius * math.sin(end_rad))

        # Full arc points for the polyline
        points = _arc_to_points(center, radius, start_angle, end_angle)

        return EntityEndpoints(
            entity_id=id(entity),
            entity_type="ARC",
            start=start,
            end=end,
            points=points,
        )

    elif entity.dxftype() == "LWPOLYLINE":
        pts = [(p[0], p[1]) for p in entity.get_points()]
        if len(pts) < 2:
            return None

        return EntityEndpoints(
            entity_id=id(entity),
            entity_type="LWPOLYLINE",
            start=pts[0],
            end=pts[-1] if not entity.closed else pts[0],
            points=pts,
        )

    return None


def _find_nearest_endpoint(
    point: Tuple[float, float],
    entities: List[EntityEndpoints],
    tolerance: float,
    exclude_ids: Set[int],
) -> Optional[Tuple[EntityEndpoints, str]]:
    """
    Find the nearest unused entity endpoint within tolerance.

    Returns (entity, endpoint_type) where endpoint_type is 'start' or 'end'.
    """
    best_entity = None
    best_endpoint = None
    best_dist = float("inf")

    for ent in entities:
        if ent.used or ent.entity_id in exclude_ids:
            continue

        dist_to_start = _distance(point, ent.start)
        dist_to_end = _distance(point, ent.end)

        if dist_to_start <= tolerance and dist_to_start < best_dist:
            best_dist = dist_to_start
            best_entity = ent
            best_endpoint = "start"

        if dist_to_end <= tolerance and dist_to_end < best_dist:
            best_dist = dist_to_end
            best_entity = ent
            best_endpoint = "end"

    if best_entity:
        return (best_entity, best_endpoint)
    return None


def _chain_entities(
    entities: List[EntityEndpoints],
    tolerance: float,
) -> List[ContourLoop]:
    """
    Chain entities by endpoint proximity to form contours.

    Algorithm:
    1. Pick an unused entity as chain start
    2. Follow its 'end' point to find connecting entities
    3. Continue until no more connections or back to start (closed)
    4. Repeat for remaining unused entities
    """
    contours = []

    for start_entity in entities:
        if start_entity.used:
            continue

        # Start a new chain
        chain_points: List[Tuple[float, float]] = []
        chain_entities: List[EntityEndpoints] = []
        used_ids: Set[int] = set()

        # Add first entity
        start_entity.used = True
        used_ids.add(start_entity.entity_id)
        chain_entities.append(start_entity)
        chain_points.extend(start_entity.points)

        # Current endpoint to continue from
        current_end = start_entity.end
        chain_start = start_entity.start

        # Follow the chain
        while True:
            match = _find_nearest_endpoint(current_end, entities, tolerance, used_ids)

            if not match:
                break

            next_entity, endpoint_type = match
            next_entity.used = True
            used_ids.add(next_entity.entity_id)
            chain_entities.append(next_entity)

            # Add points in correct order
            if endpoint_type == "start":
                # Entity connects at its start, traverse forward
                chain_points.extend(next_entity.points[1:])  # Skip first (duplicate)
                current_end = next_entity.end
            else:
                # Entity connects at its end, traverse backward
                reversed_points = list(reversed(next_entity.points))
                chain_points.extend(reversed_points[1:])  # Skip first (duplicate)
                current_end = next_entity.start

        # Check if chain closes back to start
        is_closed = _distance(current_end, chain_start) <= tolerance

        if is_closed and len(chain_points) > 2:
            # Remove last point if it's essentially the same as first
            if _distance(chain_points[-1], chain_points[0]) <= tolerance:
                chain_points = chain_points[:-1]

        # Calculate bounds and perimeter
        if chain_points:
            xs = [p[0] for p in chain_points]
            ys = [p[1] for p in chain_points]
            bounds = (min(xs), min(ys), max(xs), max(ys))

            perimeter = sum(
                _distance(chain_points[i], chain_points[(i + 1) % len(chain_points)])
                for i in range(len(chain_points))
            )
        else:
            bounds = (0.0, 0.0, 0.0, 0.0)
            perimeter = 0.0

        contour = ContourLoop(
            points=chain_points,
            entity_count=len(chain_entities),
            is_closed=is_closed,
            perimeter_mm=perimeter,
            bounds=bounds,
        )
        contours.append(contour)

    return contours


def reconstruct_contours(
    dxf_bytes: bytes,
    layer_name: Optional[str] = None,
    tolerance_mm: float = 0.5,
    min_points: int = 3,
    output_layer: str = "CONTOURS",
) -> ReconstructionResult:
    """
    Reconstruct closed contours from LINE/ARC entities.

    Args:
        dxf_bytes: Input DXF file bytes
        layer_name: Layer to process (None = all layers with LINE/ARC)
        tolerance_mm: Maximum gap between endpoints to consider connected
        min_points: Minimum points required for a valid contour
        output_layer: Layer name for output LWPOLYLINE entities

    Returns:
        ReconstructionResult with reconstructed DXF bytes and stats
    """
    result = ReconstructionResult()

    # Load DXF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        tmp.write(dxf_bytes)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
    except Exception as e:
        result.errors.append(f"Failed to read DXF: {e}")
        return result
    finally:
        import os
        os.unlink(tmp_path)

    msp = doc.modelspace()

    # Collect LINE and ARC entities
    entities: List[EntityEndpoints] = []

    for entity in msp:
        if entity.dxftype() not in ("LINE", "ARC"):
            continue

        if layer_name and entity.dxf.layer != layer_name:
            continue

        ep = _extract_entity_endpoints(entity)
        if ep:
            entities.append(ep)

    result.total_entities = len(entities)

    if not entities:
        result.warnings.append(f"No LINE/ARC entities found" + (f" on layer '{layer_name}'" if layer_name else ""))
        result.success = True
        return result

    # Chain entities into contours
    contours = _chain_entities(entities, tolerance_mm)

    # Count stats
    result.entities_used = sum(1 for e in entities if e.used)
    result.entities_orphaned = result.total_entities - result.entities_used
    result.contours_found = len(contours)
    result.closed_contours = sum(1 for c in contours if c.is_closed)
    result.open_chains = result.contours_found - result.closed_contours

    # Filter contours
    valid_contours = [c for c in contours if len(c.points) >= min_points]
    result.contours = valid_contours

    if result.entities_orphaned > 0:
        result.warnings.append(
            f"{result.entities_orphaned} entities could not be chained (check tolerance)"
        )

    if result.open_chains > 0:
        result.warnings.append(
            f"{result.open_chains} chains are not closed (may need larger tolerance)"
        )

    # Create output DXF with LWPOLYLINE contours
    out_doc = ezdxf.new("R2000")  # R2000 for LWPOLYLINE support
    out_msp = out_doc.modelspace()

    # Add layer
    out_doc.layers.add(output_layer)

    for i, contour in enumerate(valid_contours):
        if len(contour.points) < 3:
            continue

        out_msp.add_lwpolyline(
            contour.points,
            close=contour.is_closed,
            dxfattribs={"layer": output_layer},
        )

    # Save to bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        out_doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            result.dxf_bytes = f.read()
    finally:
        import os
        os.unlink(tmp_path)

    result.success = True
    return result


def reconstruct_bracing_dxf(
    dxf_bytes: bytes,
    tolerance_mm: float = 1.0,
) -> ReconstructionResult:
    """
    Specialized reconstruction for bracing DXF files.

    Processes multiple bracing layers and outputs named contours.

    Args:
        dxf_bytes: Input bracing DXF file
        tolerance_mm: Endpoint connection tolerance

    Returns:
        ReconstructionResult with all bracing contours
    """
    result = ReconstructionResult()

    # Load DXF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        tmp.write(dxf_bytes)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
    except Exception as e:
        result.errors.append(f"Failed to read DXF: {e}")
        return result
    finally:
        import os
        os.unlink(tmp_path)

    msp = doc.modelspace()

    # Find bracing layers
    bracing_layers = []
    for entity in msp:
        layer = entity.dxf.layer
        if "BRAC" in layer.upper() and layer not in bracing_layers:
            bracing_layers.append(layer)

    if not bracing_layers:
        result.warnings.append("No bracing layers found (looking for *BRAC*)")
        result.success = True
        return result

    # Create output DXF
    out_doc = ezdxf.new("R2000")
    out_msp = out_doc.modelspace()

    total_contours = 0
    total_closed = 0
    all_contours = []

    # Process each bracing layer
    for layer in bracing_layers:
        # Collect entities for this layer
        entities: List[EntityEndpoints] = []

        for entity in msp:
            if entity.dxf.layer != layer:
                continue
            if entity.dxftype() not in ("LINE", "ARC"):
                continue

            ep = _extract_entity_endpoints(entity)
            if ep:
                entities.append(ep)

        if not entities:
            continue

        result.total_entities += len(entities)

        # Chain entities
        contours = _chain_entities(entities, tolerance_mm)

        # Add output layer
        output_layer = f"{layer}_CONTOURS"
        out_doc.layers.add(output_layer)

        for contour in contours:
            if len(contour.points) < 3:
                continue

            all_contours.append(contour)
            total_contours += 1
            if contour.is_closed:
                total_closed += 1

            out_msp.add_lwpolyline(
                contour.points,
                close=contour.is_closed,
                dxfattribs={"layer": output_layer},
            )

        result.entities_used += sum(1 for e in entities if e.used)

    result.entities_orphaned = result.total_entities - result.entities_used
    result.contours_found = total_contours
    result.closed_contours = total_closed
    result.open_chains = total_contours - total_closed
    result.contours = all_contours

    # Save output
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        out_doc.saveas(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            result.dxf_bytes = f.read()
    finally:
        import os
        os.unlink(tmp_path)

    if result.entities_orphaned > 0:
        result.warnings.append(
            f"{result.entities_orphaned} entities not chained (increase tolerance or check geometry)"
        )

    result.success = True
    return result
