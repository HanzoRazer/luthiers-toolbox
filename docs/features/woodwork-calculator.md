# Woodwork Calculator

Calculate material requirements, weights, and angles for woodworking projects.

---

## Board Feet Calculator

Calculate lumber volume in board feet.

### Input

| Field | Description | Example |
|-------|-------------|---------|
| Thickness | Lumber thickness in inches | 1.0 |
| Width | Lumber width in inches | 8.0 |
| Length | Lumber length in inches | 96.0 |
| Quantity | Number of boards | 2 |

### Formula

```
Board Feet = (Thickness × Width × Length) ÷ 144 × Quantity
```

### Common Lumber Sizes

| Nominal | Actual (S4S) | Per Linear Foot |
|---------|--------------|-----------------|
| 4/4 × 4" | 13/16" × 3.5" | 0.33 bf |
| 4/4 × 6" | 13/16" × 5.5" | 0.5 bf |
| 4/4 × 8" | 13/16" × 7.25" | 0.67 bf |
| 5/4 × 6" | 1-1/16" × 5.5" | 0.63 bf |
| 8/4 × 6" | 1-3/4" × 5.5" | 1.0 bf |

---

## Wood Weight Calculator

Estimate the weight of a piece of wood based on species and dimensions.

### Wood Densities (Air Dry)

| Species | lb/ft³ | kg/m³ | Category |
|---------|--------|-------|----------|
| Sitka Spruce | 28 | 449 | Softwood |
| Western Red Cedar | 23 | 368 | Softwood |
| Douglas Fir | 34 | 545 | Softwood |
| Black Walnut | 38 | 609 | Hardwood |
| Hard Maple | 44 | 705 | Hardwood |
| White Oak | 47 | 753 | Hardwood |
| Ebony | 69 | 1105 | Exotic |
| Rosewood (Indian) | 52 | 833 | Exotic |
| Mahogany (Genuine) | 35 | 561 | Exotic |

### Formula

```
Weight (lb) = Volume (ft³) × Density (lb/ft³)
Volume (ft³) = (Thickness × Width × Length) ÷ 1728
```

---

## Miter Angle Calculator

Calculate miter angles for joining pieces at various configurations.

### Simple Miter (Flat Joint)

For joining two pieces at an angle:

```
Miter Angle = Joint Angle ÷ 2
```

| Joint Angle | Miter Setting |
|-------------|---------------|
| 90° (square) | 45° |
| 60° (hexagon) | 30° |
| 45° | 22.5° |
| 120° | 60° |

### Polygon Miters

For regular polygons (picture frames, etc.):

```
Miter Angle = 180° ÷ Number of Sides
```

| Shape | Sides | Miter Angle |
|-------|-------|-------------|
| Triangle | 3 | 60° |
| Square | 4 | 45° |
| Pentagon | 5 | 36° |
| Hexagon | 6 | 30° |
| Octagon | 8 | 22.5° |

---

## Compound Angle Calculator

For cuts that are both mitered and beveled (crown molding, sloped boxes).

### Inputs

| Field | Description |
|-------|-------------|
| Corner Angle | The angle of the corner (typically 90°) |
| Slope Angle | The tilt from vertical |

### Formulas

```
Miter Angle = arctan(sin(Slope) × tan(Corner/2))
Bevel Angle = arcsin(cos(Slope) × sin(Corner/2))
```

### Common Compound Angles

| Application | Corner | Slope | Miter | Bevel |
|-------------|--------|-------|-------|-------|
| Crown Molding (38°) | 90° | 38° | 31.6° | 33.9° |
| Crown Molding (45°) | 90° | 45° | 35.3° | 30.0° |
| Sloped Box (10°) | 90° | 10° | 7.9° | 44.7° |

---

## Taper Calculator

Calculate taper dimensions for tapered legs or parts.

### Inputs

| Field | Description |
|-------|-------------|
| Top Width | Width at narrow end |
| Bottom Width | Width at wide end |
| Length | Total length of taper |

### Results

- **Taper per foot**: (Bottom - Top) ÷ (Length ÷ 12)
- **Taper angle**: arctan((Bottom - Top) ÷ 2 ÷ Length)

---

## API Usage

```python
import requests

# Calculate board feet
response = requests.post(
    "http://localhost:8000/api/calculators/board-feet",
    json={
        "thickness_inches": 1.0,
        "width_inches": 8.0,
        "length_inches": 96.0,
        "quantity": 2
    }
)
print(response.json())
# {"board_feet": 10.67, "total_cubic_inches": 1536}

# Calculate wood weight
response = requests.post(
    "http://localhost:8000/api/calculators/wood-weight",
    json={
        "thickness_inches": 2.0,
        "width_inches": 12.0,
        "length_inches": 48.0,
        "species": "black_walnut"
    }
)
print(response.json())
# {"weight_lb": 25.3, "weight_kg": 11.5}
```

---

## Related

- [Unit Converter](unit-converter.md) - Convert between units
- [DXF Import](dxf-import.md) - Import CAD files for machining
