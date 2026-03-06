"""
DXF Parser - Extract geometry from DXF files
Parses DXF files using ezdxf and extracts entities for the vectorizer pipeline
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
import math

try:
    import ezdxf
    from ezdxf.entities import Line, Circle, Arc, LWPolyline, Polyline, Spline, Ellipse
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

logger = logging.getLogger(__name__)


class DXFParser:
    """
    Parse DXF files and extract geometry for the blueprint pipeline.

    Unlike image-based blueprints, DXF files contain actual vector geometry,
    so we extract entities directly rather than using AI analysis.
    """

    def __init__(self):
        if not HAS_EZDXF:
            raise ImportError("ezdxf package required for DXF parsing. Install with: pip install ezdxf")

    def parse_from_bytes(self, file_bytes: bytes, filename: str) -> Dict:
        """
        Parse DXF file and extract geometry.

        Args:
            file_bytes: Raw DXF file bytes
            filename: Original filename

        Returns:
            Dictionary compatible with BlueprintAnalyzer output format:
            - scale: Detected or assumed scale
            - scale_confidence: high (DXF has real units)
            - dimensions: List of extracted dimensions
            - entities: Raw entity data for vectorization
            - bounds: Bounding box of all geometry
        """
        try:
            # Parse DXF from bytes
            import io
            doc = ezdxf.read(io.BytesIO(file_bytes))
            msp = doc.modelspace()

            # Extract units from DXF header
            units = self._get_units(doc)

            # Extract all entities
            entities = []
            all_points = []

            for entity in msp:
                entity_data = self._extract_entity(entity)
                if entity_data:
                    entities.append(entity_data)
                    # Collect points for bounding box
                    if 'points' in entity_data:
                        all_points.extend(entity_data['points'])
                    if 'center' in entity_data:
                        all_points.append(entity_data['center'])

            # Calculate bounding box
            bounds = self._calculate_bounds(all_points)

            # Extract dimensions from DXF DIMENSION entities
            dimensions = self._extract_dimensions(msp, units)

            # If no explicit dimensions, calculate from geometry
            if not dimensions and bounds:
                dimensions = self._dimensions_from_bounds(bounds, units)

            logger.info(f"DXF parsed: {len(entities)} entities, {len(dimensions)} dimensions, units={units}")

            return {
                'source': 'dxf',
                'filename': filename,
                'scale': f"1:1 ({units})",
                'scale_confidence': 'high',  # DXF has explicit units
                'units': units,
                'dimensions': dimensions,
                'entities': entities,
                'bounds': bounds,
                'entity_count': len(entities),
                'notes': f"DXF file with {len(entities)} entities in {units} units"
            }

        except Exception as e:
            logger.error(f"Error parsing DXF {filename}: {e}")
            raise

    def _get_units(self, doc) -> str:
        """Extract units from DXF header."""
        try:
            # $INSUNITS: 0=Unitless, 1=Inches, 2=Feet, 3=Miles, 4=mm, 5=cm, 6=m
            insunits = doc.header.get('$INSUNITS', 0)
            units_map = {
                0: 'unitless',
                1: 'inches',
                2: 'feet',
                3: 'miles',
                4: 'mm',
                5: 'cm',
                6: 'm',
                7: 'km',
                8: 'microinches',
                9: 'mils',
                10: 'yards',
                11: 'angstroms',
                12: 'nanometers',
                13: 'microns',
                14: 'decimeters',
                15: 'decameters',
                16: 'hectometers',
                17: 'gigameters',
                18: 'au',
                19: 'lightyears',
                20: 'parsecs',
            }
            return units_map.get(insunits, 'mm')  # Default to mm
        except Exception:
            return 'mm'

    def _extract_entity(self, entity) -> Optional[Dict]:
        """Extract geometry data from a DXF entity."""
        try:
            dxftype = entity.dxftype()

            if dxftype == 'LINE':
                return {
                    'type': 'line',
                    'start': (entity.dxf.start.x, entity.dxf.start.y),
                    'end': (entity.dxf.end.x, entity.dxf.end.y),
                    'points': [(entity.dxf.start.x, entity.dxf.start.y),
                               (entity.dxf.end.x, entity.dxf.end.y)],
                    'layer': entity.dxf.layer,
                }

            elif dxftype == 'CIRCLE':
                return {
                    'type': 'circle',
                    'center': (entity.dxf.center.x, entity.dxf.center.y),
                    'radius': entity.dxf.radius,
                    'layer': entity.dxf.layer,
                }

            elif dxftype == 'ARC':
                return {
                    'type': 'arc',
                    'center': (entity.dxf.center.x, entity.dxf.center.y),
                    'radius': entity.dxf.radius,
                    'start_angle': entity.dxf.start_angle,
                    'end_angle': entity.dxf.end_angle,
                    'layer': entity.dxf.layer,
                }

            elif dxftype == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                return {
                    'type': 'polyline',
                    'points': points,
                    'closed': entity.closed,
                    'layer': entity.dxf.layer,
                }

            elif dxftype == 'POLYLINE':
                points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                return {
                    'type': 'polyline',
                    'points': points,
                    'closed': entity.is_closed,
                    'layer': entity.dxf.layer,
                }

            elif dxftype == 'SPLINE':
                # Flatten spline to polyline approximation
                points = [(p.x, p.y) for p in entity.flattening(0.1)]
                return {
                    'type': 'spline',
                    'points': points,
                    'closed': entity.closed,
                    'layer': entity.dxf.layer,
                }

            elif dxftype == 'ELLIPSE':
                return {
                    'type': 'ellipse',
                    'center': (entity.dxf.center.x, entity.dxf.center.y),
                    'major_axis': (entity.dxf.major_axis.x, entity.dxf.major_axis.y),
                    'ratio': entity.dxf.ratio,
                    'layer': entity.dxf.layer,
                }

            elif dxftype == 'POINT':
                return {
                    'type': 'point',
                    'location': (entity.dxf.location.x, entity.dxf.location.y),
                    'points': [(entity.dxf.location.x, entity.dxf.location.y)],
                    'layer': entity.dxf.layer,
                }

            # Skip unsupported entity types silently
            return None

        except Exception as e:
            logger.warning(f"Could not extract entity {entity.dxftype()}: {e}")
            return None

    def _calculate_bounds(self, points: List[Tuple[float, float]]) -> Optional[Dict]:
        """Calculate bounding box from list of points."""
        if not points:
            return None

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        return {
            'min_x': min(xs),
            'max_x': max(xs),
            'min_y': min(ys),
            'max_y': max(ys),
            'width': max(xs) - min(xs),
            'height': max(ys) - min(ys),
        }

    def _extract_dimensions(self, msp, units: str) -> List[Dict]:
        """Extract DIMENSION entities from DXF."""
        dimensions = []

        for entity in msp.query('DIMENSION'):
            try:
                dim_data = {
                    'location': entity.dxf.text if hasattr(entity.dxf, 'text') else 'unknown',
                    'value': entity.dxf.actual_measurement if hasattr(entity.dxf, 'actual_measurement') else 0,
                    'units': units,
                    'source': 'dxf_dimension',
                    'confidence': 'high',
                }
                dimensions.append(dim_data)
            except Exception as e:
                logger.warning(f"Could not extract dimension: {e}")

        return dimensions

    def _dimensions_from_bounds(self, bounds: Dict, units: str) -> List[Dict]:
        """Generate dimension entries from bounding box."""
        return [
            {
                'location': 'overall_width',
                'value': round(bounds['width'], 3),
                'units': units,
                'source': 'calculated',
                'confidence': 'high',
            },
            {
                'location': 'overall_height',
                'value': round(bounds['height'], 3),
                'units': units,
                'source': 'calculated',
                'confidence': 'high',
            },
        ]


def is_dxf_file(file_bytes: bytes, filename: str) -> bool:
    """Check if file is a DXF file."""
    # Check filename extension
    if filename.lower().endswith('.dxf'):
        return True

    # Check for DXF header (ASCII DXF starts with "0\nSECTION")
    # Binary DXF starts with "AutoCAD Binary DXF"
    try:
        header = file_bytes[:50].decode('utf-8', errors='ignore')
        if 'SECTION' in header or 'AutoCAD Binary DXF' in header:
            return True
    except Exception:
        pass

    return False
