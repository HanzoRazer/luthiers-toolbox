"""================================================================================"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import ezdxf
from shapely.geometry import Polygon, LineString, Point
from shapely.validation import explain_validity
from shapely.ops import unary_union
import io
import math

from .dxf_preflight import Severity, Issue


# =============================================================================
# DATA STRUCTURES (ISSUE & REPORT MODELS)
# =============================================================================

@dataclass
class TopologyIssue:
    """Issue related to geometric topology"""
    severity: Severity
    message: str
    category: str = "topology"
    layer: Optional[str] = None
    entity_handle: Optional[str] = None
    entity_type: Optional[str] = None
    topology_error: Optional[str] = None  # From explain_validity()
    intersection_point: Optional[Tuple[float, float]] = None
    repair_suggestion: Optional[str] = None


@dataclass
class TopologyReport:
    """Complete topology validation report"""
    filename: str
    is_valid: bool
    issues: List[TopologyIssue] = field(default_factory=list)
    entities_checked: int = 0
    self_intersections: int = 0
    degenerate_polygons: int = 0
    repairable_count: int = 0
    
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)
    
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)


# =============================================================================
# TOPOLOGY VALIDATOR (SHAPELY-BASED VALIDATION)
# =============================================================================

class TopologyValidator:
    """Validate DXF geometry topology using Shapely."""
    
    def __init__(self, dxf_bytes: bytes, filename: str = "unknown.dxf"):
        """
        Initialize validator with DXF file data.
        
        Args:
            dxf_bytes: Raw DXF file content
            filename: Original filename (for reporting)
        """
        self.doc = ezdxf.readfile(io.BytesIO(dxf_bytes))
        self.filename = filename
        self.msp = self.doc.modelspace()
        self.issues: List[TopologyIssue] = []
    
    def check_self_intersections(self) -> TopologyReport:
        """
        Check all closed paths for self-intersections.
        
        Returns:
            TopologyReport with all detected issues
        """
        entities_checked = 0
        self_intersections = 0
        degenerate_polygons = 0
        repairable_count = 0
        
        # Check LWPOLYLINE entities (most common in CAM files)
        lwpolylines = [e for e in self.msp if e.dxftype() == "LWPOLYLINE"]
        
        for entity in lwpolylines:
            entities_checked += 1
            
            # Extract vertices
            points = [(p[0], p[1]) for p in entity.get_points('xy')]
            
            if len(points) < 3:
                # Degenerate polygon (not enough vertices)
                degenerate_polygons += 1
                self.issues.append(TopologyIssue(
                    severity=Severity.ERROR,
                    message=f"Degenerate polygon on layer '{entity.dxf.layer}' (only {len(points)} vertices)",
                    layer=entity.dxf.layer,
                    entity_handle=entity.dxf.handle,
                    entity_type="LWPOLYLINE",
                    repair_suggestion="Add more vertices or remove entity"
                ))
                continue
            
            # Create Shapely polygon
            try:
                poly = Polygon(points)
                
                # Check validity
                if not poly.is_valid:
                    self_intersections += 1
                    
                    # Get detailed error description
                    error_reason = explain_validity(poly)
                    
                    # Try to extract intersection point from error message
                    # Format: "Ring Self-intersection[x, y]"
                    intersection_point = None
                    if "[" in error_reason and "]" in error_reason:
                        try:
                            coords_str = error_reason.split("[")[1].split("]")[0]
                            x, y = map(float, coords_str.split(","))
                            intersection_point = (x, y)
                        except (ValueError, IndexError):
                            pass
                    
                    # Try buffer(0) repair
                    repair_suggestion = self._suggest_repair(poly)
                    if repair_suggestion.startswith("Use buffer(0)"):
                        repairable_count += 1
                    
                    self.issues.append(TopologyIssue(
                        severity=Severity.ERROR,
                        message=f"Self-intersecting polygon on layer '{entity.dxf.layer}'",
                        layer=entity.dxf.layer,
                        entity_handle=entity.dxf.handle,
                        entity_type="LWPOLYLINE",
                        topology_error=error_reason,
                        intersection_point=intersection_point,
                        repair_suggestion=repair_suggestion
                    ))
                
                # Check for near-zero area (collapsed polygon)
                elif poly.area < 0.01:  # < 0.01 mm² (effectively zero)
                    degenerate_polygons += 1
                    self.issues.append(TopologyIssue(
                        severity=Severity.WARNING,
                        message=f"Near-zero area polygon on layer '{entity.dxf.layer}' ({poly.area:.6f} mm²)",
                        layer=entity.dxf.layer,
                        entity_handle=entity.dxf.handle,
                        entity_type="LWPOLYLINE",
                        repair_suggestion="Remove entity or increase size"
                    ))
            
            except (ValueError, TypeError, AttributeError) as e:
                self.issues.append(TopologyIssue(
                    severity=Severity.ERROR,
                    message=f"Failed to validate geometry on layer '{entity.dxf.layer}': {str(e)}",
                    layer=entity.dxf.layer,
                    entity_handle=entity.dxf.handle,
                    entity_type="LWPOLYLINE",
                    repair_suggestion="Check vertex coordinates for NaN/infinity"
                ))
        
        # Create report
        return TopologyReport(
            filename=self.filename,
            is_valid=len(self.issues) == 0,
            issues=self.issues,
            entities_checked=entities_checked,
            self_intersections=self_intersections,
            degenerate_polygons=degenerate_polygons,
            repairable_count=repairable_count
        )
    
    def _suggest_repair(self, poly: Polygon) -> str:
        """
        Generate repair suggestion for invalid polygon.
        
        Args:
            poly: Invalid Shapely polygon
        
        Returns:
            Human-readable repair suggestion
        """
        try:
            # Try buffer(0) repair (removes self-intersections)
            fixed = poly.buffer(0)
            
            if fixed.is_valid:
                # Check if geometry changed significantly
                area_change = abs(fixed.area - poly.area) / poly.area
                
                if area_change < 0.01:  # <1% change
                    return "Use buffer(0) to auto-repair (minimal geometry change)"
                elif area_change < 0.05:  # <5% change
                    return f"Use buffer(0) to auto-repair (~{area_change*100:.1f}% area change)"
                else:
                    return f"buffer(0) repairs but changes area by {area_change*100:.1f}% - manual fix recommended"
            else:
                # buffer(0) didn't fix it
                return "Complex topology error - manual repair required in CAD software"
        
        except (ValueError, TypeError) as e:
            return f"Manual repair required in CAD software ({str(e)})"
    
    def check_line_segments(self) -> List[TopologyIssue]:
        """
        Check LINE entities for issues.
        
        Returns:
            List of issues found in LINE entities
        """
        line_issues = []
        
        lines = [e for e in self.msp if e.dxftype() == "LINE"]
        
        for line in lines:
            start = line.dxf.start
            end = line.dxf.end
            
            # Check for zero-length lines
            length = math.sqrt((end[0] - start[0])**2 + 
                             (end[1] - start[1])**2 + 
                             (end[2] - start[2])**2)
            
            if length < 0.001:  # < 1 micron
                line_issues.append(TopologyIssue(
                    severity=Severity.WARNING,
                    message=f"Zero-length LINE on layer '{line.dxf.layer}' ({length:.6f} mm)",
                    layer=line.dxf.layer,
                    entity_handle=line.dxf.handle,
                    entity_type="LINE",
                    repair_suggestion="Remove entity"
                ))
        
        self.issues.extend(line_issues)
        return line_issues
    
    def check_overlapping_entities(self) -> List[TopologyIssue]:
        """
        Check for overlapping/duplicate entities.
        
        Note: This is a computationally expensive operation for large files.
        Use sparingly or only on selected layers.
        
        Returns:
            List of overlapping entity issues
        """
        overlap_issues = []
        
        # Get all LWPOLYLINE entities
        polys = [e for e in self.msp if e.dxftype() == "LWPOLYLINE"]
        
        # Convert to Shapely polygons
        shapely_polys = []
        for entity in polys:
            try:
                points = [(p[0], p[1]) for p in entity.get_points('xy')]
                if len(points) >= 3:
                    poly = Polygon(points)
                    if poly.is_valid:
                        shapely_polys.append((entity, poly))
            except (ValueError, AttributeError):
                pass
        
        # Check for overlaps (O(n²) - expensive!)
        for i, (entity1, poly1) in enumerate(shapely_polys):
            for entity2, poly2 in shapely_polys[i+1:]:
                if poly1.intersects(poly2):
                    intersection = poly1.intersection(poly2)
                    
                    # Ignore tiny overlaps (tolerance)
                    if intersection.area > 0.1:  # > 0.1 mm²
                        overlap_issues.append(TopologyIssue(
                            severity=Severity.WARNING,
                            message=f"Overlapping polygons on layers '{entity1.dxf.layer}' and '{entity2.dxf.layer}' ({intersection.area:.2f} mm² overlap)",
                            layer=entity1.dxf.layer,
                            entity_handle=entity1.dxf.handle,
                            entity_type="LWPOLYLINE",
                            repair_suggestion="Remove duplicate or adjust geometry"
                        ))
        
        self.issues.extend(overlap_issues)
        return overlap_issues


# =============================================================================
# TEST UTILITIES (DXF GENERATION FOR VALIDATION)
# =============================================================================

def create_test_figure8_dxf() -> bytes:
    """
    Create a test DXF with self-intersecting figure-8 polygon.
    
    Returns:
        DXF file bytes
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Figure-8 path (self-intersects at center)
    points = [
        (0, 0),
        (10, 10),
        (20, 0),
        (20, 20),
        (10, 10),
        (0, 20)
    ]
    
    msp.add_lwpolyline(points, dxfattribs={'layer': 'GEOMETRY', 'closed': True})
    
    # Save to bytes
    output = io.BytesIO()
    doc.write(output)
    return output.getvalue()


def create_test_valid_dxf() -> bytes:
    """
    Create a test DXF with valid polygon (no self-intersections).
    
    Returns:
        DXF file bytes
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Simple rectangle (valid)
    points = [
        (0, 0),
        (100, 0),
        (100, 60),
        (0, 60)
    ]
    
    msp.add_lwpolyline(points, dxfattribs={'layer': 'GEOMETRY', 'closed': True})
    
    # Save to bytes
    output = io.BytesIO()
    doc.write(output)
    return output.getvalue()
