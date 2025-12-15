"""
SVG setup sheet generator for CNC probing patterns.

Creates visual documentation showing probe points, dimensions, and setup instructions.
"""

from typing import List, Tuple, Optional
from xml.etree import ElementTree as ET


class ProbeSetupSheet:
    """Generate SVG setup sheets for CNC probing operations."""
    
    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        margin: int = 50
    ):
        """
        Initialize SVG canvas.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
            margin: Margin around drawing in pixels
        """
        self.width = width
        self.height = height
        self.margin = margin
        
        # Create SVG root
        self.svg = ET.Element('svg', {
            'width': str(width),
            'height': str(height),
            'xmlns': 'http://www.w3.org/2000/svg',
            'viewBox': f'0 0 {width} {height}'
        })
        
        # Add stylesheet
        style = ET.SubElement(self.svg, 'style')
        style.text = """
            .part { fill: #f0f0f0; stroke: #333; stroke-width: 2; }
            .probe { fill: #ef4444; stroke: #991b1b; stroke-width: 2; }
            .origin { fill: #fbbf24; stroke: #92400e; stroke-width: 2; }
            .grid { stroke: #e5e5e5; stroke-width: 0.5; }
            .dimension { stroke: #666; stroke-width: 1; fill: none; }
            .arrow { fill: #666; }
            .label { font-family: Arial, sans-serif; font-size: 12px; fill: #333; }
            .title { font-family: Arial, sans-serif; font-size: 20px; font-weight: bold; fill: #111; }
            .subtitle { font-family: Arial, sans-serif; font-size: 14px; fill: #555; }
            .note-box { fill: #fef3c7; stroke: #d97706; stroke-width: 1; }
            .note-text { font-family: Arial, sans-serif; font-size: 11px; fill: #78350f; }
        """
        
        # Background
        bg = ET.SubElement(self.svg, 'rect', {
            'width': str(width),
            'height': str(height),
            'fill': 'white'
        })
    
    def add_grid(self, spacing: int = 50, color: str = "#e5e5e5"):
        """Add reference grid."""
        # Vertical lines
        for x in range(0, self.width + 1, spacing):
            ET.SubElement(self.svg, 'line', {
                'x1': str(x), 'y1': '0',
                'x2': str(x), 'y2': str(self.height),
                'class': 'grid'
            })
        
        # Horizontal lines
        for y in range(0, self.height + 1, spacing):
            ET.SubElement(self.svg, 'line', {
                'x1': '0', 'y1': str(y),
                'x2': str(self.width), 'y2': str(y),
                'class': 'grid'
            })
    
    def add_title(self, title: str, subtitle: str = ""):
        """Add title and subtitle at top."""
        title_elem = ET.SubElement(self.svg, 'text', {
            'x': str(self.margin),
            'y': '30',
            'class': 'title'
        })
        title_elem.text = title
        
        if subtitle:
            subtitle_elem = ET.SubElement(self.svg, 'text', {
                'x': str(self.margin),
                'y': '50',
                'class': 'subtitle'
            })
            subtitle_elem.text = subtitle
    
    def add_rectangle_part(
        self,
        x: float,
        y: float,
        width: float,
        height: float
    ):
        """Add rectangular part outline."""
        ET.SubElement(self.svg, 'rect', {
            'x': str(x),
            'y': str(y),
            'width': str(width),
            'height': str(height),
            'class': 'part'
        })
    
    def add_circle_part(
        self,
        cx: float,
        cy: float,
        diameter: float
    ):
        """Add circular part outline."""
        ET.SubElement(self.svg, 'circle', {
            'cx': str(cx),
            'cy': str(cy),
            'r': str(diameter / 2),
            'class': 'part'
        })
    
    def add_probe_point(
        self,
        x: float,
        y: float,
        label: str = "",
        radius: float = 5.0
    ):
        """Add probe point marker."""
        # Probe dot
        ET.SubElement(self.svg, 'circle', {
            'cx': str(x),
            'cy': str(y),
            'r': str(radius),
            'class': 'probe'
        })
        
        # Label
        if label:
            label_elem = ET.SubElement(self.svg, 'text', {
                'x': str(x + radius + 5),
                'y': str(y + 4),
                'class': 'label'
            })
            label_elem.text = label
    
    def add_origin_marker(
        self,
        x: float,
        y: float,
        label: str = "X0 Y0"
    ):
        """Add origin marker (gold circle)."""
        # Origin circle
        ET.SubElement(self.svg, 'circle', {
            'cx': str(x),
            'cy': str(y),
            'r': '8',
            'class': 'origin'
        })
        
        # Crosshairs
        ET.SubElement(self.svg, 'line', {
            'x1': str(x - 12), 'y1': str(y),
            'x2': str(x + 12), 'y2': str(y),
            'stroke': '#92400e',
            'stroke-width': '1'
        })
        ET.SubElement(self.svg, 'line', {
            'x1': str(x), 'y1': str(y - 12),
            'x2': str(x), 'y2': str(y + 12),
            'stroke': '#92400e',
            'stroke-width': '1'
        })
        
        # Label
        if label:
            label_elem = ET.SubElement(self.svg, 'text', {
                'x': str(x + 15),
                'y': str(y + 4),
                'class': 'label',
                'font-weight': 'bold'
            })
            label_elem.text = label
    
    def add_dimension_line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str,
        offset: float = 20.0
    ):
        """Add dimension line with arrows and label."""
        # Main line
        ET.SubElement(self.svg, 'line', {
            'x1': str(x1), 'y1': str(y1),
            'x2': str(x2), 'y2': str(y2),
            'class': 'dimension'
        })
        
        # Start arrow
        ET.SubElement(self.svg, 'polygon', {
            'points': f"{x1-5},{y1-3} {x1},{y1} {x1-5},{y1+3}",
            'class': 'arrow'
        })
        
        # End arrow
        ET.SubElement(self.svg, 'polygon', {
            'points': f"{x2+5},{y2-3} {x2},{y2} {x2+5},{y2+3}",
            'class': 'arrow'
        })
        
        # Label at midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        label_elem = ET.SubElement(self.svg, 'text', {
            'x': str(mid_x),
            'y': str(mid_y - 5),
            'class': 'label',
            'text-anchor': 'middle'
        })
        label_elem.text = label
    
    def add_note_box(
        self,
        x: float,
        y: float,
        lines: List[str],
        width: float = 250.0,
        line_height: float = 16.0
    ):
        """Add note box with instructions."""
        height = len(lines) * line_height + 20
        
        # Box background
        ET.SubElement(self.svg, 'rect', {
            'x': str(x),
            'y': str(y),
            'width': str(width),
            'height': str(height),
            'class': 'note-box',
            'rx': '5'
        })
        
        # Text lines
        for i, line in enumerate(lines):
            text_y = y + 15 + i * line_height
            text_elem = ET.SubElement(self.svg, 'text', {
                'x': str(x + 10),
                'y': str(text_y),
                'class': 'note-text'
            })
            text_elem.text = line
    
    def to_svg_string(self) -> str:
        """Convert to SVG string."""
        return ET.tostring(self.svg, encoding='unicode')
    
    def save(self, filepath: str):
        """Save SVG to file."""
        tree = ET.ElementTree(self.svg)
        tree.write(filepath, encoding='unicode', xml_declaration=True)


def generate_corner_outside_sheet(
    part_width: float = 100.0,
    part_height: float = 60.0,
    probe_offset: float = 20.0
) -> str:
    """
    Generate setup sheet for outside corner find pattern.
    
    Args:
        part_width: Part width in mm
        part_height: Part height in mm
        probe_offset: Distance to start probe from part edge
    
    Returns:
        SVG string
    """
    sheet = ProbeSetupSheet(width=800, height=600)
    
    sheet.add_title("Corner Find - Outside", "4-Point Probe Pattern")
    sheet.add_grid(spacing=50)
    
    # Part outline (centered in view)
    part_x = 250
    part_y = 200
    sheet.add_rectangle_part(part_x, part_y, part_width * 2, part_height * 2)
    
    # Probe points (scaled for visibility)
    probe_x_left = part_x - probe_offset
    probe_y_bottom = part_y - probe_offset
    
    sheet.add_probe_point(
        probe_x_left, part_y + 40,
        "P1: +X Low"
    )
    sheet.add_probe_point(
        probe_x_left, part_y + part_height * 2 - 40,
        "P2: +X High"
    )
    sheet.add_probe_point(
        part_x + 40, probe_y_bottom,
        "P3: +Y Left"
    )
    sheet.add_probe_point(
        part_x + part_width * 2 - 40, probe_y_bottom,
        "P4: +Y Right"
    )
    
    # Origin marker at corner
    sheet.add_origin_marker(part_x, part_y, "G54 X0 Y0")
    
    # Dimensions
    sheet.add_dimension_line(
        part_x, part_y + part_height * 2 + 30,
        part_x + part_width * 2, part_y + part_height * 2 + 30,
        f"{part_width}mm"
    )
    sheet.add_dimension_line(
        part_x + part_width * 2 + 30, part_y,
        part_x + part_width * 2 + 30, part_y + part_height * 2,
        f"{part_height}mm"
    )
    
    # Instructions
    sheet.add_note_box(500, 150, [
        "Setup Instructions:",
        "1. Mount part in vise",
        "2. Install probe in spindle",
        "3. Run corner_outside.nc",
        "4. Verify G54 offset",
        f"Probe offset: {probe_offset}mm",
        "",
        "Probing Sequence:",
        "- Touch +X face (2 points)",
        "- Touch +Y face (2 points)",
        "- Calculate corner intersection",
        "- Set G54 X0 Y0 at corner"
    ])
    
    return sheet.to_svg_string()


def generate_boss_circular_sheet(
    boss_diameter: float = 50.0,
    boss_center_x: float = 0.0,
    boss_center_y: float = 0.0
) -> str:
    """
    Generate setup sheet for circular boss pattern.
    
    Args:
        boss_diameter: Boss diameter in mm
        boss_center_x: Estimated center X (mm)
        boss_center_y: Estimated center Y (mm)
    
    Returns:
        SVG string
    """
    sheet = ProbeSetupSheet(width=800, height=600)
    
    sheet.add_title("Boss Find - Circular", "4-Point Cardinal Probe")
    sheet.add_grid(spacing=50)
    
    # Boss outline (centered, scaled)
    cx = 400
    cy = 300
    radius = boss_diameter * 1.5  # Scale for visibility
    sheet.add_circle_part(cx, cy, radius * 2)
    
    # Probe points (cardinal directions)
    probe_dist = radius + 30
    sheet.add_probe_point(cx + probe_dist, cy, "P1: East (+X)")
    sheet.add_probe_point(cx, cy - probe_dist, "P2: North (+Y)")
    sheet.add_probe_point(cx - probe_dist, cy, "P3: West (-X)")
    sheet.add_probe_point(cx, cy + probe_dist, "P4: South (-Y)")
    
    # Origin at center
    sheet.add_origin_marker(cx, cy, "G54 Center")
    
    # Diameter dimension
    sheet.add_dimension_line(
        cx - radius, cy + radius + 40,
        cx + radius, cy + radius + 40,
        f"Ø{boss_diameter}mm"
    )
    
    # Instructions
    sheet.add_note_box(100, 150, [
        "Setup Instructions:",
        "1. Estimate boss position",
        "2. Position over boss center",
        "3. Run boss_circular.nc",
        "4. Verify G54 center",
        f"Expected Ø: {boss_diameter}mm",
        "",
        "Probing Sequence:",
        "- Touch East (+X)",
        "- Touch North (+Y)",
        "- Touch West (-X)",
        "- Touch South (-Y)",
        "- Calculate center average",
        "- Set G54 X0 Y0 at center"
    ])
    
    return sheet.to_svg_string()


def generate_pocket_inside_sheet(
    pocket_width: float = 100.0,
    pocket_height: float = 60.0,
    origin_corner: str = "lower_left"
) -> str:
    """
    Generate setup sheet for inside pocket pattern.
    
    Args:
        pocket_width: Pocket width in mm
        pocket_height: Pocket height in mm
        origin_corner: Origin location ("lower_left", "center", etc.)
    
    Returns:
        SVG string
    """
    sheet = ProbeSetupSheet(width=800, height=600)
    
    sheet.add_title("Pocket Find - Inside", "4-Wall Probe Pattern")
    sheet.add_grid(spacing=50)
    
    # Pocket outline (centered)
    pocket_x = 250
    pocket_y = 200
    pw = pocket_width * 2
    ph = pocket_height * 2
    sheet.add_rectangle_part(pocket_x, pocket_y, pw, ph)
    
    # Probe points (inside walls)
    sheet.add_probe_point(pocket_x + 30, pocket_y + ph / 2, "P1: -X Wall")
    sheet.add_probe_point(pocket_x + pw - 30, pocket_y + ph / 2, "P2: +X Wall")
    sheet.add_probe_point(pocket_x + pw / 2, pocket_y + 30, "P3: -Y Wall")
    sheet.add_probe_point(pocket_x + pw / 2, pocket_y + ph - 30, "P4: +Y Wall")
    
    # Origin marker
    if origin_corner == "center":
        origin_x = pocket_x + pw / 2
        origin_y = pocket_y + ph / 2
        label = "G54 Center"
    elif origin_corner == "lower_left":
        origin_x = pocket_x
        origin_y = pocket_y
        label = "G54 LL"
    else:
        origin_x = pocket_x
        origin_y = pocket_y
        label = "G54 Origin"
    
    sheet.add_origin_marker(origin_x, origin_y, label)
    
    # Dimensions
    sheet.add_dimension_line(
        pocket_x, pocket_y + ph + 30,
        pocket_x + pw, pocket_y + ph + 30,
        f"{pocket_width}mm"
    )
    sheet.add_dimension_line(
        pocket_x + pw + 30, pocket_y,
        pocket_x + pw + 30, pocket_y + ph,
        f"{pocket_height}mm"
    )
    
    # Instructions
    sheet.add_note_box(500, 150, [
        "Setup Instructions:",
        "1. Position inside pocket",
        "2. Run pocket_inside.nc",
        "3. Verify G54 offset",
        f"Origin: {origin_corner}",
        "",
        "Probing Sequence:",
        "- Touch -X wall",
        "- Touch +X wall",
        "- Touch -Y wall",
        "- Touch +Y wall",
        "- Calculate pocket center",
        f"- Set G54 at {origin_corner}"
    ])
    
    return sheet.to_svg_string()


def generate_surface_z_sheet() -> str:
    """Generate setup sheet for surface Z touch-off."""
    sheet = ProbeSetupSheet(width=800, height=400)
    
    sheet.add_title("Surface Z Touch-Off", "Single Z-Axis Probe")
    
    # Simple side view diagram
    # Part surface
    ET.SubElement(sheet.svg, 'rect', {
        'x': '150', 'y': '250',
        'width': '500', 'height': '50',
        'class': 'part'
    })
    
    # Probe tool (above surface)
    ET.SubElement(sheet.svg, 'rect', {
        'x': '390', 'y': '180',
        'width': '20', 'height': '70',
        'fill': '#666', 'stroke': '#333', 'stroke-width': '2'
    })
    
    # Probe tip
    ET.SubElement(sheet.svg, 'circle', {
        'cx': '400', 'cy': '250',
        'r': '8',
        'class': 'probe'
    })
    
    # Arrow showing probe direction
    ET.SubElement(sheet.svg, 'line', {
        'x1': '450', 'y1': '200',
        'x2': '450', 'y2': '240',
        'stroke': '#ef4444',
        'stroke-width': '2',
        'marker-end': 'url(#arrowhead)'
    })
    
    # Z-zero line
    ET.SubElement(sheet.svg, 'line', {
        'x1': '100', 'y1': '250',
        'x2': '700', 'y2': '250',
        'stroke': '#fbbf24',
        'stroke-width': '2',
        'stroke-dasharray': '5,5'
    })
    
    # Label
    label = ET.SubElement(sheet.svg, 'text', {
        'x': '460', 'y': '220',
        'class': 'label'
    })
    label.text = "Probe down"
    
    z_label = ET.SubElement(sheet.svg, 'text', {
        'x': '710', 'y': '255',
        'class': 'label',
        'font-weight': 'bold'
    })
    z_label.text = "Z0 = Surface"
    
    # Instructions
    sheet.add_note_box(150, 50, [
        "Setup Instructions:",
        "1. Position probe over part surface",
        "2. Ensure X/Y are already set (G54 X/Y)",
        "3. Start above surface (Z+10mm)",
        "4. Run surface_z.nc",
        "5. Verify Z-zero at top surface",
        "",
        "Probing Sequence:",
        "- Move to X0 Y0",
        "- Probe down to surface",
        "- Set G54 Z0 at contact point",
        "- Retract to safe Z"
    ])
    
    return sheet.to_svg_string()
