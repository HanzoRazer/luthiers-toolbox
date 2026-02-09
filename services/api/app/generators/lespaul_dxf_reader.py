"""Les Paul DXF reader — geometry extraction from layered DXF files."""

from __future__ import annotations

import math
import ezdxf
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path


@dataclass
class ExtractedPath:
    """A path extracted from the DXF."""
    layer: str
    points: List[Tuple[float, float]]
    is_closed: bool
    perimeter: float
    area: float
    bounds: Dict[str, float]

    @property
    def center(self) -> Tuple[float, float]:
        return (
            (self.bounds['min_x'] + self.bounds['max_x']) / 2,
            (self.bounds['min_y'] + self.bounds['max_y']) / 2,
        )

    @property
    def width(self) -> float:
        return self.bounds['max_x'] - self.bounds['min_x']

    @property
    def height(self) -> float:
        return self.bounds['max_y'] - self.bounds['min_y']


class LesPaulDXFReader:
    """Read Les Paul DXF and extract paths by layer."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.doc = None
        self.paths: Dict[str, List[ExtractedPath]] = {}
        self.origin_offset = (0.0, 0.0)
        self.body_outline: Optional[ExtractedPath] = None

    def load(self) -> 'LesPaulDXFReader':
        """Load and parse DXF file."""
        self.doc = ezdxf.readfile(str(self.filepath))
        self._extract_all_paths()
        self._find_body_outline()
        self._calculate_origin_offset()
        return self

    def _extract_all_paths(self):
        """Extract all paths from modelspace."""
        msp = self.doc.modelspace()
        for entity in msp:
            layer = entity.dxf.layer
            points = self._entity_to_points(entity)
            if not points or len(points) < 2:
                continue
            path = self._create_path(layer, points, entity)
            if layer not in self.paths:
                self.paths[layer] = []
            self.paths[layer].append(path)

    def _entity_to_points(self, entity) -> List[Tuple[float, float]]:
        """Convert DXF entity to point list."""
        points = []
        dxftype = entity.dxftype()

        if dxftype == 'LWPOLYLINE':
            for x, y, *_ in entity.get_points():
                points.append((x, y))
            if entity.closed and points and points[0] != points[-1]:
                points.append(points[0])
        elif dxftype == 'POLYLINE':
            for vertex in entity.vertices:
                points.append((vertex.dxf.location.x, vertex.dxf.location.y))
            if entity.is_closed and points and points[0] != points[-1]:
                points.append(points[0])
        elif dxftype == 'LINE':
            points = [
                (entity.dxf.start.x, entity.dxf.start.y),
                (entity.dxf.end.x, entity.dxf.end.y),
            ]
        elif dxftype == 'CIRCLE':
            cx, cy, r = entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius
            for i in range(65):
                angle = 2 * math.pi * i / 64
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        elif dxftype == 'ARC':
            cx, cy = entity.dxf.center.x, entity.dxf.center.y
            r = entity.dxf.radius
            start = math.radians(entity.dxf.start_angle)
            end = math.radians(entity.dxf.end_angle)
            if end < start:
                end += 2 * math.pi
            segs = max(16, int((end - start) / (math.pi / 32)))
            for i in range(segs + 1):
                t = i / segs
                angle = start + t * (end - start)
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        elif dxftype == 'SPLINE':
            try:
                for pt in entity.flattening(0.01):
                    points.append((pt.x, pt.y))
            except (AttributeError, RuntimeError):
                pass

        return points

    def _create_path(self, layer: str, points: List[Tuple[float, float]], entity) -> ExtractedPath:
        """Create ExtractedPath from points."""
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        perimeter = 0.0
        for i in range(len(points) - 1):
            dx = points[i+1][0] - points[i][0]
            dy = points[i+1][1] - points[i][1]
            perimeter += math.sqrt(dx*dx + dy*dy)

        area = 0.0
        for i in range(len(points) - 1):
            area += points[i][0] * points[i+1][1]
            area -= points[i+1][0] * points[i][1]
        area = abs(area) / 2

        is_closed = False
        if hasattr(entity, 'closed'):
            is_closed = entity.closed
        elif points[0] == points[-1]:
            is_closed = True
        elif len(points) > 2:
            dx = points[0][0] - points[-1][0]
            dy = points[0][1] - points[-1][1]
            if math.sqrt(dx*dx + dy*dy) < 0.01:
                is_closed = True

        return ExtractedPath(
            layer=layer, points=points, is_closed=is_closed,
            perimeter=perimeter, area=area,
            bounds={'min_x': min(xs), 'max_x': max(xs), 'min_y': min(ys), 'max_y': max(ys)},
        )

    def _find_body_outline(self):
        """Find the body outline (largest closed path on Cutout layer)."""
        if 'Cutout' not in self.paths:
            return
        candidates = [p for p in self.paths['Cutout'] if p.is_closed]
        if candidates:
            self.body_outline = max(candidates, key=lambda p: p.perimeter)

    def _calculate_origin_offset(self):
        """Calculate offset to translate DXF coordinates to work-zero."""
        if self.body_outline:
            self.origin_offset = (
                self.body_outline.bounds['min_x'],
                self.body_outline.bounds['min_y'],
            )

    def translate_point(self, x: float, y: float) -> Tuple[float, float]:
        """Translate DXF coordinates to work coordinates."""
        return (x - self.origin_offset[0], y - self.origin_offset[1])

    def translate_path(self, path: ExtractedPath) -> List[Tuple[float, float]]:
        """Translate all points in a path to work coordinates."""
        return [self.translate_point(x, y) for x, y in path.points]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of extracted geometry."""
        summary = {
            'filepath': str(self.filepath),
            'origin_offset': self.origin_offset,
            'layers': {},
        }
        if self.body_outline:
            summary['body_outline'] = {
                'width_in': self.body_outline.width,
                'height_in': self.body_outline.height,
                'perimeter_in': self.body_outline.perimeter,
                'points': len(self.body_outline.points),
            }
        for layer, paths in self.paths.items():
            closed = sum(1 for p in paths if p.is_closed)
            summary['layers'][layer] = {
                'path_count': len(paths),
                'closed_paths': closed,
            }
        return summary
