# Rosette Designer

Create decorative sound hole patterns for acoustic instruments.

---

## What is a Rosette?

A rosette is the decorative ring around the sound hole of acoustic guitars and other stringed instruments. Traditional rosettes are made from inlaid wood pieces; modern techniques allow CNC-cut or laser-engraved patterns.

---

## Pattern Types

### Concentric Rings

Simple ring patterns with varying widths and spacing.

**Parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| Inner Diameter | Sound hole edge | 100 mm |
| Outer Diameter | Rosette outer edge | 130 mm |
| Ring Count | Number of rings | 5 |
| Ring Widths | Width of each ring | [2, 1, 5, 1, 2] mm |

---

### Radial Segments

Pie-slice divisions radiating from center.

**Parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| Segment Count | Number of divisions | 12 |
| Alternating | Two-color pattern | true |
| Rotation Offset | Starting angle | 15° |

---

### Tessellated Tiles

Repeating geometric patterns (hexagons, triangles, etc.).

**Parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| Tile Shape | Geometry type | hexagon |
| Tile Size | Size of each tile | 5 mm |
| Fill Pattern | How tiles are arranged | packed |

**Available Shapes:**

- Hexagon
- Triangle
- Square
- Diamond
- Custom polygon

---

### Celtic Knots

Interwoven band patterns.

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| Band Width | Width of knotwork bands |
| Crossings | Number of over/under crossings |
| Style | Round, square, or pointed corners |

---

### Herringbone

Classic inlay pattern.

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| Piece Width | Width of each piece |
| Piece Length | Length of each piece |
| Angle | Herringbone angle (45° typical) |

---

## Using the Designer

### Step 1: Set Dimensions

1. Enter **Sound Hole Diameter** (typically 100-110mm for guitar)
2. Enter **Rosette Width** (typically 10-30mm)
3. Set **Depth** for CNC routing (1-3mm typical)

### Step 2: Choose Pattern

Select a base pattern type and customize parameters.

### Step 3: Preview

View the design in:
- 2D top view
- 3D simulated view
- Color preview (for multi-material designs)

### Step 4: Export

| Format | Use Case |
|--------|----------|
| DXF | Import to CAD software |
| SVG | Laser cutting / vinyl |
| G-code | Direct to CNC |
| PDF | Print template |

---

## Design Tips

### For Inlay Work

1. Keep piece sizes appropriate for your materials
2. Account for kerf (laser) or tool diameter (CNC)
3. Design for your skill level—smaller pieces = more difficult
4. Consider grain direction in each piece

### For CNC Routing

1. Use tools appropriate for detail level
2. Consider V-carving for fine lines
3. Multiple depth levels add dimension
4. Leave tabs for island pieces

### For Laser Cutting

1. Adjust for kerf compensation
2. Use appropriate power/speed for material
3. Consider backing material adhesion
4. Test on scrap first

---

## Traditional Rosette Styles

### Spanish/Classical

- Mosaic tile patterns
- Multiple concentric bands
- Wood and purfling alternation

### Flamenco

- Simpler designs
- Often geometric
- Less ornate than classical

### Steel String

- Herringbone common
- Abalone inlay
- Pearl dots or rings

### Celtic

- Knotwork patterns
- Interlaced bands
- Zoomorphic elements

### Art Deco

- Geometric patterns
- Symmetrical designs
- Bold contrasts

---

## API Usage

```python
import requests

# Generate concentric ring pattern
response = requests.post(
    "http://localhost:8000/api/art-studio/rosette",
    json={
        "pattern_type": "concentric_rings",
        "inner_diameter": 100,
        "outer_diameter": 130,
        "params": {
            "ring_count": 5,
            "ring_widths": [2, 1, 5, 1, 2]
        }
    }
)

# Get DXF
dxf_data = response.json()["dxf"]

# Or generate toolpath directly
response = requests.post(
    "http://localhost:8000/api/art-studio/rosette/toolpath",
    json={
        "pattern_type": "radial_segments",
        "inner_diameter": 100,
        "outer_diameter": 125,
        "params": {
            "segment_count": 12,
            "alternating": True
        },
        "tool": {
            "diameter": 1.0,
            "type": "endmill"
        },
        "depth": 2.0
    }
)
```

---

## Material Considerations

### Wood Species

| Species | Properties | Use For |
|---------|-----------|---------|
| Maple | Light, hard | Binding, contrast |
| Ebony | Dark, very hard | Black elements |
| Rosewood | Medium-dark | Warm tones |
| Holly | White | Brightest elements |
| Koa | Golden | Hawaiian style |

### Synthetic Materials

| Material | Properties |
|----------|-----------|
| ABS Plastic | Easy to cut, durable |
| Acrylic | Clear or colored options |
| Corian | Solid surface, machinable |
| Mother of Pearl | Traditional, fragile |
| Abalone | Iridescent, expensive |

---

## Related

- [DXF Import](dxf-import.md) - Import custom rosette designs
- [Toolpath Generation](toolpaths.md) - Generate CNC code
- [V-Carving](toolpaths.md#v-carving) - Engraving techniques
