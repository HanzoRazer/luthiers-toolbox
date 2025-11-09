# Patch N.09 — Probing Patterns & SVG Visualization

**Status:** 🔜 Specification Complete (Implementation Pending)  
**Date:** November 6, 2025  
**Target:** Automated probing routines with visual setup sheets

---

## 🎯 Overview

Add **CNC probing patterns** and **SVG setup sheets** for precision work offset establishment:

- **10 probing patterns** (corner, boss, pocket, web, vise, angle, center, grid, surface, tool length)
- **SVG setup sheets** (2D diagrams with probe points and dimensions)
- **Post-processor aware** (Renishaw, Haas, Blum, Marposs, manual touch-off)
- **G65/G31 modal macros** (parametric probing subroutines)
- **Automatic WCS calculation** (G54-G59 work offsets from probe data)
- **Tolerance zones** (inspection pass/fail with color-coded feedback)
- **Multi-part locating** (fixture grid arrays)
- **Tool length offset** (automatic TLO with broken tool detection)

**Use Cases:**
- **Production setup:** Automated part locating for batch runs
- **Inspection:** In-process dimensional verification
- **Fixture alignment:** Vise squaring and tramming
- **Tool management:** Automatic tool length measurement
- **First article:** Setup sheet generation with probe coordinates

---

## 📦 Probing Patterns

### **1. Corner Find (Outside)**

Locate workpiece by probing external corner.

```python
Pattern: corner_outside
Probes: 4 (2 per axis)
Measures: X/Y position + corner angle
Sets: WCS origin at corner

Sequence:
1. Approach +X side from left
2. Touch +X face, record X1
3. Retract, move up in Y
4. Touch +X face again, record X2
5. Approach +Y side from below
6. Touch +Y face, record Y1
7. Retract, move right in X
8. Touch +Y face again, record Y2
9. Calculate corner at intersection
10. Set G54 X0 Y0 at corner

Safety:
- Overtravel distance: 20mm max
- Retract after each touch: 2mm
- Feed rate: 100 mm/min
- Spindle stopped (M5)
```

**G-code Output:**
```gcode
(Corner Find - Outside)
G54 (Work offset)
G90 (Absolute)
M5 (Spindle off)

(Probe +X face, lower point)
G0 X-10.0 Y10.0 Z5.0
G31 X30.0 F100  ; Touch +X
#100 = #5061     ; Store X position
G0 X[#100-2.0]   ; Retract 2mm

(Probe +X face, upper point)
G0 Y40.0
G31 X30.0 F100
#101 = #5061
G0 X[#101-2.0]

(Probe +Y face, left point)
G0 X10.0 Y-10.0
G31 Y30.0 F100
#102 = #5062     ; Store Y position
G0 Y[#102-2.0]

(Probe +Y face, right point)
G0 X40.0
G31 Y30.0 F100
#103 = #5062
G0 Y[#103-2.0]

(Calculate corner)
#104 = [#100 + #101] / 2  ; X center
#105 = [#102 + #103] / 2  ; Y center
G10 L20 P1 X#104 Y#105    ; Set G54 origin

(Return to safe position)
G0 Z50.0
M0 (Probing complete - Check offset)
```

**SVG Setup Sheet:**
```svg
<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
  <!-- Part outline -->
  <rect x="100" y="100" width="200" height="200" 
        fill="none" stroke="black" stroke-width="2"/>
  
  <!-- Probe points -->
  <circle cx="80" cy="120" r="5" fill="red"/>
  <text x="60" y="125" font-size="10">P1 (+X Low)</text>
  
  <circle cx="80" cy="280" r="5" fill="red"/>
  <text x="60" y="285" font-size="10">P2 (+X High)</text>
  
  <circle cx="120" cy="80" r="5" fill="red"/>
  <text x="125" y="75" font-size="10">P3 (+Y Left)</text>
  
  <circle cx="280" cy="80" r="5" fill="red"/>
  <text x="285" y="75" font-size="10">P4 (+Y Right)</text>
  
  <!-- Origin marker -->
  <circle cx="100" cy="100" r="8" fill="gold" stroke="black"/>
  <text x="110" y="105" font-weight="bold">X0 Y0</text>
  
  <!-- Dimensions -->
  <text x="150" y="350" font-size="12">
    Corner Find Pattern - 4 Probes
  </text>
</svg>
```

---

### **2. Boss Find (Circular)**

Locate cylindrical boss by probing at 4 cardinal points.

```python
Pattern: boss_circular
Probes: 4 (N/S/E/W at 90° intervals)
Measures: Center X/Y + diameter
Sets: WCS origin at boss center

Sequence:
1. Approach from +X (East)
2. Touch boss, record X_east
3. Retract, rotate 90° to +Y (North)
4. Touch boss, record Y_north
5. Rotate 90° to -X (West)
6. Touch boss, record X_west
7. Rotate 90° to -Y (South)
8. Touch boss, record Y_south
9. Calculate center: X = (X_east + X_west)/2, Y = (Y_north + Y_south)/2
10. Calculate diameter: D = (X_east - X_west), D = (Y_north - Y_south)
11. Verify: |D_x - D_y| < 0.1mm (roundness check)

Safety:
- Start radius estimate: 25mm (user input)
- Overtravel: 10mm beyond estimated edge
- Retract: 5mm radial
```

**G-code with Macro:**
```gcode
(Boss Find - Circular)
#110 = 25.0  ; Estimated radius
#111 = 5.0   ; Retract distance

(Probe East +X)
G0 X[#110 + 20] Y0 Z5.0
G31 X-50.0 F100
#120 = #5061  ; X_east
G0 X[#120 + #111]

(Probe North +Y)
G0 X0 Y[#110 + 20]
G31 Y-50.0 F100
#121 = #5062  ; Y_north
G0 Y[#121 + #111]

(Probe West -X)
G0 X-[#110 + 20] Y0
G31 X50.0 F100
#122 = #5061  ; X_west
G0 X[#122 - #111]

(Probe South -Y)
G0 X0 Y-[#110 + 20]
G31 Y50.0 F100
#123 = #5062  ; Y_south
G0 Y[#123 - #111]

(Calculate center and diameter)
#124 = [#120 + #122] / 2  ; Center X
#125 = [#121 + #123] / 2  ; Center Y
#126 = #120 - #122         ; Diameter X
#127 = #121 - #123         ; Diameter Y
#128 = [#126 + #127] / 2  ; Average diameter

(Check roundness)
#129 = ABS[#126 - #127]    ; Diameter difference
IF [#129 GT 0.1] THEN #3000=1 (BOSS NOT ROUND - CHECK PART)

G10 L20 P1 X#124 Y#125     ; Set G54 at boss center
G0 Z50.0
M0 (Boss probed - Ø#128mm, Center at G54 X0 Y0)
```

---

### **3. Pocket Find (Inside Corner)**

Locate internal pocket by probing inside walls.

```python
Pattern: pocket_inside
Probes: 4-6 (2 per axis + optional diagonal)
Measures: X/Y position + pocket size
Sets: WCS origin at pocket center or corner

Sequence:
1. Position probe inside pocket (manual or estimated)
2. Approach -X wall from right
3. Touch -X wall, record X1
4. Retract, move up in Y
5. Touch -X wall again, record X2
6. Approach -Y wall from above
7. Touch -Y wall, record Y1
8. Retract, move right in X
9. Touch -Y wall again, record Y2
10. Calculate pocket corner at intersection
11. Optionally probe opposite walls for size verification

Safety:
- Start inside pocket (manual positioning)
- Overtravel: 50mm max (must hit wall)
- Wall detection timeout: 5 seconds
```

**G-code:**
```gcode
(Pocket Find - Inside)
(Assume starting inside pocket at X20 Y20 Z5)
G54 G90 M5

(Probe -X wall, lower point)
G0 X30.0 Y10.0 Z5.0
G31 X-50.0 F100
#130 = #5061  ; X1 (left wall)
G0 X[#130 + 2.0]

(Probe -X wall, upper point)
G0 Y30.0
G31 X-50.0 F100
#131 = #5061  ; X2
G0 X[#131 + 2.0]

(Probe -Y wall, left point)
G0 X10.0 Y30.0
G31 Y-50.0 F100
#132 = #5062  ; Y1 (bottom wall)
G0 Y[#132 + 2.0]

(Probe -Y wall, right point)
G0 X30.0
G31 Y-50.0 F100
#133 = #5062  ; Y2
G0 Y[#133 + 2.0]

(Calculate pocket corner)
#134 = [#130 + #131] / 2  ; X left wall
#135 = [#132 + #133] / 2  ; Y bottom wall

(Optional: Probe opposite walls for size)
G0 X10.0 Y20.0
G31 X50.0 F100
#136 = #5061  ; X right wall
G0 X[#136 - 2.0]

G0 X20.0 Y10.0
G31 Y50.0 F100
#137 = #5062  ; Y top wall
G0 Y[#137 - 2.0]

(Calculate pocket size)
#138 = #136 - #134  ; Width
#139 = #137 - #135  ; Height
#140 = [#134 + #136] / 2  ; Center X
#141 = [#135 + #137] / 2  ; Center Y

G10 L20 P1 X#140 Y#141  ; Set G54 at pocket center
G0 Z50.0
M0 (Pocket: #138mm × #139mm, Center at G54 X0 Y0)
```

---

### **4. Web Find (Center Between Features)**

Locate center of thin web between two pockets/holes.

```python
Pattern: web_center
Probes: 2 (one per side)
Measures: Web center + thickness
Sets: WCS origin at web centerline

Use: Guitar neck pocket routing, inlay channels
```

**G-code:**
```gcode
(Web Center Find)
(Assume web runs along Y axis)
G54 G90 M5

(Probe left side of web)
G0 X-10.0 Y50.0 Z5.0
G31 X50.0 F100
#150 = #5061  ; X_left
G0 X[#150 - 2.0]

(Probe right side of web)
G0 X60.0 Y50.0
G31 X-50.0 F100
#151 = #5061  ; X_right
G0 X[#151 + 2.0]

(Calculate web center and thickness)
#152 = [#150 + #151] / 2  ; Center X
#153 = #151 - #150         ; Thickness

G10 L20 P1 X#152 Y0  ; Set G54 X0 at web center
G0 Z50.0
M0 (Web: #153mm thick, Center at G54 X0)
```

---

### **5. Vise Square (Angle Measurement)**

Check vise squareness by probing jaw face at two Y positions.

```python
Pattern: vise_square
Probes: 2 (same face, different Y)
Measures: Angle deviation from Y axis
Reports: Angle error in degrees + tramming adjustment

Tolerance: ±0.005° (±0.1mm over 1000mm)
```

**G-code:**
```gcode
(Vise Squareness Check)
G54 G90 M5

(Probe jaw at Y=0)
G0 X-10.0 Y0.0 Z5.0
G31 X50.0 F100
#160 = #5061  ; X at Y=0
G0 X[#160 - 5.0]

(Probe jaw at Y=200)
G0 X-10.0 Y200.0
G31 X50.0 F100
#161 = #5061  ; X at Y=200
G0 X[#161 - 5.0]

(Calculate angle)
#162 = #161 - #160      ; X difference
#163 = 200.0            ; Y span
#164 = ATAN[#162 / #163] * 180 / 3.14159  ; Angle in degrees

(Check tolerance)
#165 = ABS[#164]
IF [#165 GT 0.005] THEN #3000=2 (VISE NOT SQUARE - #164°)

G0 Z50.0
M0 (Vise angle: #164° - Adjust fixed jaw by #162mm)
```

---

### **6. Angle Reference (Rotary Setup)**

Measure angle of angled feature for rotary axis alignment.

```python
Pattern: angle_reference
Probes: 2 (along angled edge)
Measures: Angle relative to X axis
Sets: G68 coordinate rotation or A-axis offset

Use: Angled neck pockets, binding channels
```

---

### **7. Center Find (Hole/Boss)**

Locate hole or boss center using 4-probe or adaptive spiral.

```python
Pattern: center_adaptive
Probes: 4-12 (adaptive based on size)
Measures: X/Y center + circularity
Algorithm: 
  1. Initial 4-probe (N/S/E/W)
  2. Calculate center estimate
  3. Re-probe 8 points around center
  4. Least-squares circle fit
  5. Iterate until converged (<0.01mm)
```

---

### **8. Grid Array (Multi-Part)**

Probe fixture grid for batch part locating.

```python
Pattern: grid_array
Probes: N × M features (e.g., 3×2 = 6 vises)
Measures: XY position of each vise corner
Stores: G54-G59 work offsets (up to 6 parts)

Use: Production runs, fixture plates
```

**G-code:**
```gcode
(Grid Array - 2x3 Vise Setup)
(Probe vise 1 at row 1, col 1)
G65 P9810 X0 Y0 R25.0      ; Call corner find subroutine
G10 L20 P1 X0 Y0           ; Store in G54

(Probe vise 2 at row 1, col 2)
G0 X150.0 Y0
G65 P9810 X150.0 Y0 R25.0
G10 L20 P2 X150.0 Y0       ; Store in G55

(Probe vise 3 at row 1, col 3)
G0 X300.0 Y0
G65 P9810 X300.0 Y0 R25.0
G10 L20 P3 X300.0 Y0       ; Store in G56

(Repeat for row 2...)
G0 Z50.0
M0 (Grid probed - G54/G55/G56 ready)
```

---

### **9. Surface Height (Z Touch-Off)**

Measure Z surface height for work offset or inspection.

```python
Pattern: surface_z
Probes: 1-9 (single point or 3×3 grid)
Measures: Z height + flatness (if grid)
Sets: G54 Z0 at surface

Options:
- Single point: Fast, assumes flat surface
- 3-point: Plane fit for tilted parts
- 9-point: Full flatness map (0.1mm resolution)
```

**G-code:**
```gcode
(Surface Z Touch-Off - Single Point)
G54 G90 M5

(Move to probe position)
G0 X50.0 Y50.0 Z20.0

(Probe down to surface)
G31 Z-50.0 F50
#170 = #5063  ; Store Z position
G0 Z[#170 + 5.0]

(Set G54 Z0 at surface)
G10 L20 P1 Z0

G0 Z50.0
M0 (Z surface set at G54 Z0)
```

---

### **10. Tool Length Offset (TLO)**

Automatic tool length measurement with broken tool detection.

```python
Pattern: tool_length
Probes: 1 (down to reference surface)
Measures: Tool length offset
Sets: G43 H<tool_number> offset
Detects: Broken/worn tools (out-of-tolerance)

Safety:
- Reference surface at known Z position
- Expected length ±2mm tolerance
- Alarm if tool too short (broken)
```

**G-code:**
```gcode
(Tool Length Offset - T1)
G54 G90 M5
T1 M6  ; Load tool 1

(Move to TLO probe position)
G0 X-50.0 Y-50.0 Z20.0

(Probe down to reference)
G31 Z-100.0 F50
#180 = #5063  ; Z position when probe triggered
G0 Z[#180 + 10.0]

(Calculate TLO relative to reference)
#181 = -150.0  ; Reference surface Z in machine coords
#182 = #180 - #181  ; Tool length offset

(Check for broken tool)
#183 = 50.0  ; Expected length
#184 = ABS[#182 - #183]
IF [#184 GT 2.0] THEN #3000=3 (TOOL BROKEN OR WRONG - Length #182mm)

(Store TLO)
G10 L1 P1 Z#182

G0 Z50.0
M0 (T1 length: #182mm)
```

---

## 🎨 SVG Setup Sheet Generator

### **Module:** `services/api/app/cam/probe_svg.py`

```python
"""
SVG setup sheet generator for probing patterns.
"""
from typing import List, Tuple, Optional, Dict, Any
from xml.etree import ElementTree as ET

class ProbeSetupSheet:
    """Generate SVG setup sheets for CNC probing."""
    
    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        margin: int = 50
    ):
        self.width = width
        self.height = height
        self.margin = margin
        self.scale = 1.0
        
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
            .part { fill: none; stroke: black; stroke-width: 2; }
            .probe { fill: red; stroke: black; stroke-width: 1; }
            .origin { fill: gold; stroke: black; stroke-width: 2; }
            .dimension { stroke: blue; stroke-width: 1; }
            .label { font-family: Arial; font-size: 12px; }
            .title { font-family: Arial; font-size: 16px; font-weight: bold; }
            .grid { stroke: lightgray; stroke-width: 0.5; stroke-dasharray: 5,5; }
        """
    
    def add_title(self, title: str, subtitle: Optional[str] = None):
        """Add title to setup sheet."""
        title_elem = ET.SubElement(self.svg, 'text', {
            'x': str(self.width / 2),
            'y': '30',
            'text-anchor': 'middle',
            'class': 'title'
        })
        title_elem.text = title
        
        if subtitle:
            sub_elem = ET.SubElement(self.svg, 'text', {
                'x': str(self.width / 2),
                'y': '50',
                'text-anchor': 'middle',
                'class': 'label'
            })
            sub_elem.text = subtitle
    
    def add_grid(self, spacing: int = 50):
        """Add reference grid."""
        g = ET.SubElement(self.svg, 'g', {'class': 'grid'})
        
        # Vertical lines
        for x in range(self.margin, self.width - self.margin, spacing):
            ET.SubElement(g, 'line', {
                'x1': str(x), 'y1': str(self.margin),
                'x2': str(x), 'y2': str(self.height - self.margin)
            })
        
        # Horizontal lines
        for y in range(self.margin, self.height - self.margin, spacing):
            ET.SubElement(g, 'line', {
                'x1': str(self.margin), 'y1': str(y),
                'x2': str(self.width - self.margin), 'y2': str(y)
            })
    
    def add_rectangle_part(
        self,
        x: float, y: float,
        width: float, height: float
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
        cx: float, cy: float,
        radius: float
    ):
        """Add circular part/feature."""
        ET.SubElement(self.svg, 'circle', {
            'cx': str(cx),
            'cy': str(cy),
            'r': str(radius),
            'class': 'part'
        })
    
    def add_probe_point(
        self,
        x: float, y: float,
        label: str,
        radius: float = 5
    ):
        """Add probe point marker."""
        # Probe circle
        ET.SubElement(self.svg, 'circle', {
            'cx': str(x),
            'cy': str(y),
            'r': str(radius),
            'class': 'probe'
        })
        
        # Label
        ET.SubElement(self.svg, 'text', {
            'x': str(x + 10),
            'y': str(y + 5),
            'class': 'label'
        }).text = label
    
    def add_origin_marker(
        self,
        x: float, y: float,
        label: str = "X0 Y0"
    ):
        """Add work coordinate origin marker."""
        # Crosshair
        g = ET.SubElement(self.svg, 'g', {'class': 'origin'})
        
        ET.SubElement(g, 'circle', {
            'cx': str(x),
            'cy': str(y),
            'r': '8'
        })
        
        # Cross lines
        ET.SubElement(g, 'line', {
            'x1': str(x - 12), 'y1': str(y),
            'x2': str(x + 12), 'y2': str(y),
            'stroke': 'black', 'stroke-width': '2'
        })
        ET.SubElement(g, 'line', {
            'x1': str(x), 'y1': str(y - 12),
            'x2': str(x), 'y2': str(y + 12),
            'stroke': 'black', 'stroke-width': '2'
        })
        
        # Label
        ET.SubElement(self.svg, 'text', {
            'x': str(x + 15),
            'y': str(y + 5),
            'class': 'label',
            'font-weight': 'bold'
        }).text = label
    
    def add_dimension_line(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        label: str,
        offset: float = 20
    ):
        """Add dimension line with arrows and label."""
        g = ET.SubElement(self.svg, 'g', {'class': 'dimension'})
        
        # Main line
        ET.SubElement(g, 'line', {
            'x1': str(x1), 'y1': str(y1),
            'x2': str(x2), 'y2': str(y2)
        })
        
        # Arrows (simple triangles)
        # TODO: Add proper arrowheads
        
        # Label at midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        ET.SubElement(self.svg, 'text', {
            'x': str(mid_x),
            'y': str(mid_y - offset),
            'text-anchor': 'middle',
            'class': 'label'
        }).text = label
    
    def add_note_box(
        self,
        x: float, y: float,
        lines: List[str]
    ):
        """Add note/instruction box."""
        # Background box
        box_height = len(lines) * 20 + 20
        ET.SubElement(self.svg, 'rect', {
            'x': str(x),
            'y': str(y),
            'width': '250',
            'height': str(box_height),
            'fill': 'lightyellow',
            'stroke': 'black',
            'stroke-width': '1'
        })
        
        # Text lines
        for i, line in enumerate(lines):
            ET.SubElement(self.svg, 'text', {
                'x': str(x + 10),
                'y': str(y + 20 + i * 20),
                'class': 'label'
            }).text = line
    
    def to_svg_string(self) -> str:
        """Convert to SVG string."""
        return ET.tostring(self.svg, encoding='unicode')
    
    def save(self, filepath: str):
        """Save SVG to file."""
        tree = ET.ElementTree(self.svg)
        tree.write(filepath, encoding='unicode', xml_declaration=True)


def generate_corner_outside_sheet(
    part_width: float,
    part_height: float,
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
    sheet = ProbeSetupSheet(width=600, height=600)
    
    sheet.add_title("Corner Find - Outside", "4-Point Probe Pattern")
    sheet.add_grid(spacing=50)
    
    # Part outline (centered)
    part_x = 200
    part_y = 200
    sheet.add_rectangle_part(part_x, part_y, part_width, part_height)
    
    # Probe points
    sheet.add_probe_point(
        part_x - probe_offset, part_y + 20,
        "P1: +X Low"
    )
    sheet.add_probe_point(
        part_x - probe_offset, part_y + part_height - 20,
        "P2: +X High"
    )
    sheet.add_probe_point(
        part_x + 20, part_y - probe_offset,
        "P3: +Y Left"
    )
    sheet.add_probe_point(
        part_x + part_width - 20, part_y - probe_offset,
        "P4: +Y Right"
    )
    
    # Origin marker
    sheet.add_origin_marker(part_x, part_y, "G54 X0 Y0")
    
    # Dimensions
    sheet.add_dimension_line(
        part_x, part_y + part_height + 30,
        part_x + part_width, part_y + part_height + 30,
        f"{part_width}mm"
    )
    sheet.add_dimension_line(
        part_x + part_width + 30, part_y,
        part_x + part_width + 30, part_y + part_height,
        f"{part_height}mm"
    )
    
    # Notes
    sheet.add_note_box(400, 100, [
        "Setup Instructions:",
        "1. Mount part in vise",
        "2. Install probe in spindle",
        "3. Run corner_outside.nc",
        "4. Verify G54 offset",
        f"Probe offset: {probe_offset}mm"
    ])
    
    return sheet.to_svg_string()


def generate_boss_circular_sheet(
    boss_diameter: float,
    boss_center_x: float = 0,
    boss_center_y: float = 0
) -> str:
    """Generate setup sheet for circular boss pattern."""
    sheet = ProbeSetupSheet()
    
    sheet.add_title("Boss Find - Circular", "4-Point Cardinal Probe")
    sheet.add_grid()
    
    # Boss outline
    cx = 400
    cy = 300
    radius = boss_diameter / 2
    sheet.add_circle_part(cx, cy, radius * 2)  # Scale for visibility
    
    # Probe points (cardinal directions)
    probe_dist = radius * 2 + 30
    sheet.add_probe_point(cx + probe_dist, cy, "P1: East (+X)")
    sheet.add_probe_point(cx, cy - probe_dist, "P2: North (+Y)")
    sheet.add_probe_point(cx - probe_dist, cy, "P3: West (-X)")
    sheet.add_probe_point(cx, cy + probe_dist, "P4: South (-Y)")
    
    # Origin at center
    sheet.add_origin_marker(cx, cy, "G54 Center")
    
    # Diameter dimension
    sheet.add_dimension_line(
        cx - radius * 2, cy + radius * 2 + 40,
        cx + radius * 2, cy + radius * 2 + 40,
        f"Ø{boss_diameter}mm"
    )
    
    sheet.add_note_box(50, 100, [
        "Setup Instructions:",
        "1. Estimate boss position",
        "2. Start probe near boss",
        "3. Run boss_circular.nc",
        f"Expected Ø: {boss_diameter}mm",
        "Tolerance: ±0.1mm"
    ])
    
    return sheet.to_svg_string()
```

---

## 🔌 API Endpoints

### **Router:** `services/api/app/routers/probe_router.py`

```python
"""
Probing pattern generation and SVG setup sheets.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from ..cam import probe_patterns, probe_svg

router = APIRouter(prefix="/cam/probe", tags=["probing"])


class ProbePointIn(BaseModel):
    """Single probe point definition."""
    x: float
    y: float
    z: float
    label: str = ""


class CornerProbeIn(BaseModel):
    """Corner find pattern input."""
    pattern: Literal["corner_outside", "corner_inside"] = "corner_outside"
    approach_distance: float = Field(20.0, description="Distance to start probe from edge (mm)")
    retract_distance: float = Field(2.0, description="Retract after each probe (mm)")
    feed_probe: float = Field(100.0, description="Probing feed rate (mm/min)")
    safe_z: float = Field(10.0, description="Safe Z height (mm)")
    work_offset: int = Field(1, ge=1, le=6, description="G54-G59 offset number (1-6)")
    post_id: str = Field("GRBL", description="Post-processor ID")


class BossProbeIn(BaseModel):
    """Boss/hole find pattern input."""
    pattern: Literal["boss_circular", "hole_circular"] = "boss_circular"
    estimated_diameter: float = Field(50.0, description="Estimated feature diameter (mm)")
    estimated_center_x: float = Field(0.0, description="Estimated center X (mm)")
    estimated_center_y: float = Field(0.0, description="Estimated center Y (mm)")
    probe_count: int = Field(4, ge=4, le=12, description="Number of probe points (4/8/12)")
    retract_distance: float = Field(5.0, description="Radial retract (mm)")
    feed_probe: float = Field(100.0, description="Probing feed (mm/min)")
    safe_z: float = Field(10.0, description="Safe Z (mm)")
    work_offset: int = Field(1, ge=1, le=6)
    post_id: str = "GRBL"


class SetupSheetIn(BaseModel):
    """Setup sheet generation input."""
    pattern: Literal[
        "corner_outside", "corner_inside",
        "boss_circular", "hole_circular",
        "pocket_inside", "web_center",
        "vise_square", "grid_array"
    ]
    part_width: Optional[float] = 100.0
    part_height: Optional[float] = 60.0
    feature_diameter: Optional[float] = 50.0
    probe_points: Optional[List[ProbePointIn]] = None
    notes: Optional[List[str]] = None


@router.post("/corner/gcode")
async def generate_corner_probe(body: CornerProbeIn):
    """
    Generate G-code for corner probing pattern.
    
    Returns G-code with G31 probes and G10 L20 offset setting.
    """
    try:
        gcode = probe_patterns.generate_corner_probe(
            pattern=body.pattern,
            approach_distance=body.approach_distance,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset
        )
        
        return Response(
            content=gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=corner_{body.pattern}.nc"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/boss/gcode")
async def generate_boss_probe(body: BossProbeIn):
    """Generate G-code for circular boss/hole probing."""
    try:
        gcode = probe_patterns.generate_boss_probe(
            pattern=body.pattern,
            estimated_diameter=body.estimated_diameter,
            estimated_center=(body.estimated_center_x, body.estimated_center_y),
            probe_count=body.probe_count,
            retract_distance=body.retract_distance,
            feed_probe=body.feed_probe,
            safe_z=body.safe_z,
            work_offset=body.work_offset
        )
        
        return Response(
            content=gcode,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=boss_{body.pattern}.nc"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup_sheet/svg")
async def generate_setup_sheet(body: SetupSheetIn):
    """
    Generate SVG setup sheet for probing pattern.
    
    Returns SVG document with part outline, probe points, and dimensions.
    """
    try:
        if body.pattern in ["corner_outside", "corner_inside"]:
            svg = probe_svg.generate_corner_outside_sheet(
                part_width=body.part_width,
                part_height=body.part_height,
                probe_offset=20.0
            )
        
        elif body.pattern in ["boss_circular", "hole_circular"]:
            svg = probe_svg.generate_boss_circular_sheet(
                boss_diameter=body.feature_diameter
            )
        
        else:
            raise ValueError(f"Pattern '{body.pattern}' not implemented")
        
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename=setup_{body.pattern}.svg"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def list_probe_patterns():
    """List all available probing patterns."""
    return {
        "patterns": [
            {
                "id": "corner_outside",
                "name": "Corner Find (Outside)",
                "description": "4-point probe on external corner",
                "probes": 4,
                "sets": "X/Y origin at corner"
            },
            {
                "id": "corner_inside",
                "name": "Corner Find (Inside)",
                "description": "4-point probe on internal corner",
                "probes": 4,
                "sets": "X/Y origin at pocket corner"
            },
            {
                "id": "boss_circular",
                "name": "Boss Find (Circular)",
                "description": "4-12 point probe on cylindrical boss",
                "probes": "4-12",
                "sets": "X/Y origin at boss center"
            },
            {
                "id": "hole_circular",
                "name": "Hole Find (Circular)",
                "description": "4-12 point probe inside hole",
                "probes": "4-12",
                "sets": "X/Y origin at hole center"
            },
            {
                "id": "pocket_inside",
                "name": "Pocket Find",
                "description": "4-6 point probe inside rectangular pocket",
                "probes": "4-6",
                "sets": "X/Y origin at pocket center or corner"
            },
            {
                "id": "web_center",
                "name": "Web Center",
                "description": "2-point probe on thin web",
                "probes": 2,
                "sets": "X origin at web centerline"
            },
            {
                "id": "vise_square",
                "name": "Vise Squareness Check",
                "description": "2-point angle measurement",
                "probes": 2,
                "sets": "Reports angle deviation"
            },
            {
                "id": "surface_z",
                "name": "Surface Z Touch-Off",
                "description": "1-9 point Z height measurement",
                "probes": "1-9",
                "sets": "Z origin at surface"
            },
            {
                "id": "tool_length",
                "name": "Tool Length Offset",
                "description": "Automatic TLO measurement",
                "probes": 1,
                "sets": "G43 H offset for active tool"
            },
            {
                "id": "grid_array",
                "name": "Grid Array",
                "description": "Multi-part fixture grid",
                "probes": "N×M",
                "sets": "Multiple G54-G59 offsets"
            }
        ]
    }
```

---

## 🧪 Testing

### **Test 1: Corner Outside Probe**

```powershell
$body = @{
    pattern = "corner_outside"
    approach_distance = 20.0
    retract_distance = 2.0
    feed_probe = 100.0
    safe_z = 10.0
    work_offset = 1
    post_id = "GRBL"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/probe/corner/gcode" `
    -Method POST -Body $body -ContentType "application/json" `
    -OutFile "corner_outside_g54.nc"

# Expected: G31 probes with G10 L20 P1 setting G54 offset
```

---

### **Test 2: Boss Circular Probe**

```powershell
$body = @{
    pattern = "boss_circular"
    estimated_diameter = 50.0
    estimated_center_x = 0.0
    estimated_center_y = 0.0
    probe_count = 4
    retract_distance = 5.0
    feed_probe = 100.0
    safe_z = 10.0
    work_offset = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/probe/boss/gcode" `
    -Method POST -Body $body -ContentType "application/json" `
    -OutFile "boss_probe.nc"
```

---

### **Test 3: SVG Setup Sheet**

```powershell
$body = @{
    pattern = "corner_outside"
    part_width = 100.0
    part_height = 60.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/probe/setup_sheet/svg" `
    -Method POST -Body $body -ContentType "application/json" `
    -OutFile "setup_corner.svg"

# Open setup_corner.svg in browser to view setup sheet
```

---

## 📊 Benefits

### **1. Setup Time Reduction**
- **Manual touch-off:** 5-10 minutes per part
- **Automated probing:** 30-60 seconds per part
- **Savings:** **80-90%** setup time reduction

### **2. Accuracy Improvement**
- **Manual indicator:** ±0.05mm typical
- **Electronic probe:** ±0.002mm repeatability
- **Improvement:** **25× more precise**

### **3. Production Efficiency**
- **Batch runs:** Automatic fixture grid probing
- **First article:** SVG setup sheets for documentation
- **Quality control:** In-process dimensional verification

### **4. Safety**
- **Broken tool detection:** Automatic TLO verification
- **Fixture collision:** Pre-check vise squareness
- **Part presence:** Verify part loaded before cutting

---

## ✅ Implementation Checklist

### **Phase 1: Core Probing Engine (4 hours)**
- [ ] Create `probe_patterns.py` module
- [ ] Implement corner find (outside/inside)
- [ ] Implement boss/hole find (circular)
- [ ] Implement pocket find
- [ ] Test G31 probes on simulator

### **Phase 2: SVG Generator (3 hours)**
- [ ] Create `probe_svg.py` module
- [ ] Implement `ProbeSetupSheet` class
- [ ] Implement corner sheet generator
- [ ] Implement boss sheet generator
- [ ] Test SVG rendering in browser

### **Phase 3: API Endpoints (2 hours)**
- [ ] Create `probe_router.py`
- [ ] Implement `/corner/gcode` endpoint
- [ ] Implement `/boss/gcode` endpoint
- [ ] Implement `/setup_sheet/svg` endpoint
- [ ] Register router in `main.py`

### **Phase 4: Advanced Patterns (4 hours)**
- [ ] Implement web center find
- [ ] Implement vise square check
- [ ] Implement surface Z touch-off
- [ ] Implement tool length offset
- [ ] Implement grid array (multi-part)

### **Phase 5: UI Integration (4 hours)**
- [ ] Create `ProbingLab.vue` component
- [ ] Add pattern selector
- [ ] Add SVG setup sheet preview
- [ ] Add G-code export buttons
- [ ] Add live probe data visualization

**Total Effort:** ~17 hours

---

## 🏆 Summary

Patch N.09 adds **CNC probing patterns** and **SVG setup sheets**:

✅ **10 probing patterns** (corner, boss, pocket, web, vise, angle, center, grid, surface, TLO)  
✅ **SVG setup sheets** (2D diagrams with probe points and dimensions)  
✅ **G31 probe moves** with G10 L20 work offset setting  
✅ **Post-processor aware** (Renishaw, Haas, Blum, Marposs)  
✅ **80-90% setup time reduction**  
✅ **25× accuracy improvement** (±0.002mm repeatability)  
✅ **Automatic TLO** with broken tool detection  
✅ **Multi-part fixtures** (grid array probing)  

**Implementation:** ~17 hours  
**Status:** 🔜 Ready for implementation  
**Dependencies:** None (standalone module)  
**Impact:** Professional setup sheets + automated work offset establishment
