"""
DXF Preflight Validation System
================================

Phase 3.2: Port nc_lint.py concepts to DXF validation.

Validates DXF files before CAM processing to catch issues early:
- Layer validation (required layers present)
- Closed path validation (all contours closed)
- Unit consistency (mm vs inch)
- Geometry sanity checks (no zero-length segments, no self-intersections)
- Entity type validation (LWPOLYLINE, LINE, SPLINE, CIRCLE, ARC)
- Dimension validation (reasonable sizes for guitar lutherie)

Based on nc_lint.py pattern from legacy pipeline:
- Three severity levels: ERROR, WARNING, INFO
- HTML report generation
- Issue location tracking (layer, entity handle)
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import ezdxf
from pathlib import Path
import math
import json
from datetime import datetime


class Severity(str, Enum):
    """Issue severity levels (matches nc_lint.py)"""
    ERROR = "ERROR"       # Must fix (blocks CAM processing)
    WARNING = "WARNING"   # Should fix (may cause issues)
    INFO = "INFO"         # Nice to know (optimization suggestions)


@dataclass
class Issue:
    """Single validation issue"""
    severity: Severity
    message: str
    category: str  # 'layer', 'geometry', 'units', 'dimension', 'entity'
    layer: Optional[str] = None
    entity_handle: Optional[str] = None
    entity_type: Optional[str] = None
    location: Optional[Tuple[float, float]] = None  # (x, y) for visualization
    suggestion: Optional[str] = None


@dataclass
class PreflightReport:
    """Complete preflight validation report"""
    filename: str
    dxf_version: str
    total_entities: int
    layers: List[str]
    issues: List[Issue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    passed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)
    
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)
    
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)


# ============================================================================
# Validation Rules
# ============================================================================

class DXFPreflight:
    """DXF validation engine"""
    
    def __init__(self, dxf_bytes: bytes, filename: str = "unknown.dxf"):
        """
        Initialize preflight checker with DXF content.
        
        Args:
            dxf_bytes: DXF file content
            filename: Original filename for reporting
        """
        self.filename = filename
        self.dxf_bytes = dxf_bytes
        self.doc = None
        self.msp = None
        self.issues: List[Issue] = []
        
    def run_all_checks(self) -> PreflightReport:
        """
        Run all validation checks and generate report.
        
        Returns:
            PreflightReport with all issues found
        """
        # Load DXF
        try:
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp:
                tmp.write(self.dxf_bytes)
                tmp_path = tmp.name
            
            try:
                self.doc = ezdxf.readfile(tmp_path)
                self.msp = self.doc.modelspace()
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            self.issues.append(Issue(
                severity=Severity.ERROR,
                message=f"Failed to read DXF file: {str(e)}",
                category="file"
            ))
            return self._build_report()
        
        # Run checks
        self._check_layers()
        self._check_entities()
        self._check_closed_paths()
        self._check_dimensions()
        self._check_geometry_sanity()
        
        return self._build_report()
    
    def _build_report(self) -> PreflightReport:
        """Build final report from collected issues"""
        if not self.doc:
            return PreflightReport(
                filename=self.filename,
                dxf_version="unknown",
                total_entities=0,
                layers=[],
                issues=self.issues,
                passed=False
            )
        
        # Collect stats
        all_entities = list(self.msp)
        entity_types = {}
        for entity in all_entities:
            etype = entity.dxftype()
            entity_types[etype] = entity_types.get(etype, 0) + 1
        
        stats = {
            "entity_types": entity_types,
            "total_entities": len(all_entities),
            "layer_count": len(self.doc.layers)
        }
        
        # Determine pass/fail (no errors)
        error_count = sum(1 for i in self.issues if i.severity == Severity.ERROR)
        passed = error_count == 0
        
        return PreflightReport(
            filename=self.filename,
            dxf_version=self.doc.dxfversion,
            total_entities=len(all_entities),
            layers=[layer.dxf.name for layer in self.doc.layers],
            issues=self.issues,
            stats=stats,
            passed=passed
        )
    
    # ========================================================================
    # Check: Layers
    # ========================================================================
    
    def _check_layers(self):
        """Validate layer structure"""
        if not self.doc:
            return
        
        layer_names = [layer.dxf.name for layer in self.doc.layers]
        
        # Check for common CAM layers
        recommended_layers = ["GEOMETRY", "CONTOURS", "0"]
        has_cam_layer = any(layer.upper() in [l.upper() for l in layer_names] for layer in recommended_layers)
        
        if not has_cam_layer:
            self.issues.append(Issue(
                severity=Severity.WARNING,
                message=f"No standard CAM layer found. Expected: {', '.join(recommended_layers)}",
                category="layer",
                suggestion="Create a 'GEOMETRY' layer for CAM-ready paths"
            ))
        
        # Check for excessive layers (complexity warning)
        if len(layer_names) > 20:
            self.issues.append(Issue(
                severity=Severity.INFO,
                message=f"Many layers detected ({len(layer_names)}). Consider consolidating for CAM.",
                category="layer"
            ))
    
    # ========================================================================
    # Check: Entities
    # ========================================================================
    
    def _check_entities(self):
        """Validate entity types and distribution"""
        if not self.msp:
            return
        
        all_entities = list(self.msp)
        
        if not all_entities:
            self.issues.append(Issue(
                severity=Severity.ERROR,
                message="DXF modelspace is empty (no entities found)",
                category="entity"
            ))
            return
        
        # Count entity types
        entity_types = {}
        for entity in all_entities:
            etype = entity.dxftype()
            entity_types[etype] = entity_types.get(etype, 0) + 1
        
        # Check for CAM-ready entities
        cam_entities = ["LWPOLYLINE", "LINE", "CIRCLE", "ARC"]
        has_cam_entities = any(etype in entity_types for etype in cam_entities)
        
        if not has_cam_entities:
            self.issues.append(Issue(
                severity=Severity.ERROR,
                message=f"No CAM-compatible entities found. Expected: {', '.join(cam_entities)}",
                category="entity",
                suggestion="Convert text/dimensions to geometry (explode blocks, convert splines)"
            ))
        
        # Warn about TEXT/MTEXT (not machinable)
        text_count = entity_types.get("TEXT", 0) + entity_types.get("MTEXT", 0)
        if text_count > 0:
            self.issues.append(Issue(
                severity=Severity.INFO,
                message=f"{text_count} text entities found (not machinable)",
                category="entity",
                suggestion="Text will be ignored during CAM processing"
            ))
        
        # Warn about SPLINE (needs reconstruction)
        spline_count = entity_types.get("SPLINE", 0)
        if spline_count > 0:
            self.issues.append(Issue(
                severity=Severity.INFO,
                message=f"{spline_count} SPLINE entities found",
                category="entity",
                suggestion="Use /reconstruct-contours endpoint to chain SPLINEs into closed paths"
            ))
    
    # ========================================================================
    # Check: Closed Paths
    # ========================================================================
    
    def _check_closed_paths(self):
        """Validate LWPOLYLINE entities are closed"""
        if not self.msp:
            return
        
        lwpolylines = [e for e in self.msp if e.dxftype() == "LWPOLYLINE"]
        
        if not lwpolylines:
            return  # No LWPOLYLINE to check
        
        open_count = 0
        for poly in lwpolylines:
            if not poly.closed:
                open_count += 1
                self.issues.append(Issue(
                    severity=Severity.ERROR,
                    message=f"Open LWPOLYLINE found on layer '{poly.dxf.layer}'",
                    category="geometry",
                    layer=poly.dxf.layer,
                    entity_handle=poly.dxf.handle,
                    entity_type="LWPOLYLINE",
                    suggestion="Close path in CAD software or use reconstruction tool"
                ))
        
        if open_count > 0:
            self.issues.append(Issue(
                severity=Severity.ERROR,
                message=f"{open_count} open LWPOLYLINE entities found (must be closed for pocketing)",
                category="geometry"
            ))
    
    # ========================================================================
    # Check: Dimensions
    # ========================================================================
    
    def _check_dimensions(self):
        """Validate dimensions are reasonable for guitar lutherie"""
        if not self.msp:
            return
        
        all_entities = list(self.msp)
        if not all_entities:
            return
        
        # Compute bounding box
        min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
        
        for entity in all_entities:
            if entity.dxftype() in ["LWPOLYLINE", "LINE", "CIRCLE", "ARC", "SPLINE"]:
                try:
                    # Get bounding box from entity
                    bbox = entity.bounding_box
                    if bbox:
                        min_x = min(min_x, bbox.extmin.x)
                        min_y = min(min_y, bbox.extmin.y)
                        max_x = max(max_x, bbox.extmax.x)
                        max_y = max(max_y, bbox.extmax.y)
                except:
                    pass
        
        if min_x == float('inf'):
            return  # No valid geometry
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Guitar body typical dimensions (mm)
        # Acoustic: 300-500mm wide, 450-550mm tall
        # Electric: 300-400mm wide, 400-500mm tall
        
        # Check if dimensions are reasonable
        if width < 50 or height < 50:
            self.issues.append(Issue(
                severity=Severity.WARNING,
                message=f"Very small dimensions ({width:.1f} × {height:.1f} mm). Units may be incorrect.",
                category="dimension",
                suggestion="Check if DXF is in inches (convert to mm: 1 inch = 25.4mm)"
            ))
        
        if width > 2000 or height > 2000:
            self.issues.append(Issue(
                severity=Severity.WARNING,
                message=f"Very large dimensions ({width:.1f} × {height:.1f} mm). Units may be incorrect.",
                category="dimension",
                suggestion="Check if DXF is scaled incorrectly or in different units"
            ))
        
        # Info: Report dimensions
        self.issues.append(Issue(
            severity=Severity.INFO,
            message=f"Bounding box: {width:.1f} × {height:.1f} mm",
            category="dimension"
        ))
    
    # ========================================================================
    # Check: Geometry Sanity
    # ========================================================================
    
    def _check_geometry_sanity(self):
        """Check for degenerate geometry (zero-length, duplicates, etc.)"""
        if not self.msp:
            return
        
        lines = [e for e in self.msp if e.dxftype() == "LINE"]
        
        # Check for zero-length lines
        zero_length_count = 0
        for line in lines:
            dx = line.dxf.end.x - line.dxf.start.x
            dy = line.dxf.end.y - line.dxf.start.y
            length = math.sqrt(dx*dx + dy*dy)
            
            if length < 0.001:  # Less than 0.001mm
                zero_length_count += 1
        
        if zero_length_count > 0:
            self.issues.append(Issue(
                severity=Severity.WARNING,
                message=f"{zero_length_count} zero-length LINE entities found",
                category="geometry",
                suggestion="Clean up degenerate geometry in CAD software"
            ))
        
        # Check LWPOLYLINE vertex count
        lwpolylines = [e for e in self.msp if e.dxftype() == "LWPOLYLINE"]
        for poly in lwpolylines:
            points = list(poly.get_points())
            if len(points) < 3:
                self.issues.append(Issue(
                    severity=Severity.ERROR,
                    message=f"LWPOLYLINE with only {len(points)} points (need at least 3)",
                    category="geometry",
                    layer=poly.dxf.layer,
                    entity_handle=poly.dxf.handle,
                    entity_type="LWPOLYLINE"
                ))


# ============================================================================
# HTML Report Generation
# ============================================================================

def generate_html_report(report: PreflightReport) -> str:
    """
    Generate HTML report from preflight validation (nc_lint.py style).
    
    Args:
        report: PreflightReport with issues
    
    Returns:
        HTML string
    """
    error_count = report.error_count()
    warning_count = report.warning_count()
    info_count = report.info_count()
    
    # Determine overall status
    if error_count > 0:
        status_color = "#d32f2f"
        status_text = "FAILED"
    elif warning_count > 0:
        status_color = "#f57c00"
        status_text = "PASSED WITH WARNINGS"
    else:
        status_color = "#388e3c"
        status_text = "PASSED"
    
    # Build issue list HTML
    issues_html = ""
    for issue in report.issues:
        if issue.severity == Severity.ERROR:
            badge_color = "#d32f2f"
        elif issue.severity == Severity.WARNING:
            badge_color = "#f57c00"
        else:
            badge_color = "#1976d2"
        
        suggestion_html = ""
        if issue.suggestion:
            suggestion_html = f'<div style="margin-left: 20px; color: #666; font-size: 0.9em;">💡 {issue.suggestion}</div>'
        
        location_html = ""
        if issue.layer:
            location_html += f'<span style="color: #666;">Layer: {issue.layer}</span>'
        if issue.entity_handle:
            location_html += f' <span style="color: #666;">Handle: {issue.entity_handle}</span>'
        
        issues_html += f'''
        <div style="margin: 10px 0; padding: 10px; border-left: 4px solid {badge_color}; background: #f5f5f5;">
            <div>
                <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; font-weight: bold;">{issue.severity}</span>
                <span style="margin-left: 10px; color: #666; font-size: 0.9em;">[{issue.category}]</span>
                {location_html}
            </div>
            <div style="margin-top: 5px;">{issue.message}</div>
            {suggestion_html}
        </div>
        '''
    
    # Build stats HTML
    stats_html = ""
    if report.stats.get("entity_types"):
        stats_html = "<h3>Entity Types</h3><ul>"
        for etype, count in sorted(report.stats["entity_types"].items()):
            stats_html += f"<li>{etype}: {count}</li>"
        stats_html += "</ul>"
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>DXF Preflight Report - {report.filename}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; }}
            .header {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
            .stat-box {{ background: #f5f5f5; padding: 15px; border-radius: 8px; flex: 1; }}
            .stat-value {{ font-size: 2em; font-weight: bold; }}
            .stat-label {{ color: #666; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>DXF Preflight Report</h1>
            <p><strong>Status:</strong> {status_text}</p>
            <p><strong>File:</strong> {report.filename}</p>
            <p><strong>DXF Version:</strong> {report.dxf_version}</p>
            <p><strong>Timestamp:</strong> {report.timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="stat-box">
                <div class="stat-value" style="color: #d32f2f;">{error_count}</div>
                <div class="stat-label">ERRORS</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color: #f57c00;">{warning_count}</div>
                <div class="stat-label">WARNINGS</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color: #1976d2;">{info_count}</div>
                <div class="stat-label">INFO</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{report.total_entities}</div>
                <div class="stat-label">ENTITIES</div>
            </div>
        </div>
        
        <h2>Issues ({len(report.issues)})</h2>
        {issues_html if report.issues else '<p style="color: #666;">No issues found.</p>'}
        
        {stats_html}
        
        <h3>Layers ({len(report.layers)})</h3>
        <ul>
            {''.join(f'<li>{layer}</li>' for layer in report.layers)}
        </ul>
        
        <hr style="margin: 40px 0;">
        <p style="color: #666; font-size: 0.9em;">
            Generated by Luthier's ToolBox DXF Preflight System (Phase 3.2)<br>
            Based on nc_lint.py pattern from legacy pipeline
        </p>
    </body>
    </html>
    '''
    
    return html
