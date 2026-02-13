# DXF Import

Import, validate, and process CAD files for CNC machining.

---

## Supported Formats

| Format | Extension | Support Level |
|--------|-----------|---------------|
| DXF R12-R2018 | .dxf | Full |
| DXF R2024 | .dxf | Partial |
| SVG | .svg | Planned |

---

## Importing a File

### Via UI

1. Navigate to **CAM > DXF Import**
2. Click **Upload** or drag-and-drop your file
3. Wait for geometry validation
4. Review any issues found

### Via API

```python
import requests

with open("body.dxf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/dxf/upload",
        files={"file": f}
    )

result = response.json()
print(f"Entities: {result['entity_count']}")
print(f"Layers: {result['layers']}")
print(f"Issues: {result['issues']}")
```

---

## Geometry Validation

The importer automatically checks for common issues:

### Open Contours

**Problem:** Paths that don't close on themselves.

**Impact:** Cannot generate pocket toolpaths; may cause unexpected contour behavior.

**Solutions:**

- Close gaps in CAD software
- Use auto-heal feature (closes gaps < 0.1mm)
- Manually connect endpoints in ToolBox

### Self-Intersecting Paths

**Problem:** Contours that cross themselves.

**Impact:** Ambiguous inside/outside determination; toolpath errors.

**Solutions:**

- Split into non-intersecting segments
- Redraw in CAD software
- Use "Explode" and "Rebuild" tools

### Duplicate Entities

**Problem:** Multiple identical entities stacked on top of each other.

**Impact:** Double cutting, wasted time, tool wear.

**Solution:** Auto-dedupe feature removes exact duplicates.

### Zero-Length Segments

**Problem:** Degenerate line segments with no length.

**Impact:** Can cause toolpath generation to hang or crash.

**Solution:** Automatically filtered during import.

### Non-Planar Geometry

**Problem:** 3D geometry when 2D is expected.

**Impact:** Incorrect toolpath depth calculations.

**Solution:** Project to XY plane (Z values flattened to 0).

---

## Layer Management

Layers from the DXF file are preserved and can be:

- **Shown/Hidden** - Toggle visibility
- **Selected/Deselected** - Include in toolpath generation
- **Renamed** - For organization
- **Color-coded** - Visual differentiation

### Recommended Layer Naming

| Layer Name | Purpose |
|------------|---------|
| `OUTLINE` | Outer profile cuts |
| `POCKETS` | Areas to clear |
| `HOLES` | Drilling locations |
| `ENGRAVE` | V-carve or engrave paths |
| `REFERENCE` | Construction geometry (not machined) |

---

## Entity Types

### Supported

| Entity | Description |
|--------|-------------|
| LINE | Straight line segments |
| ARC | Circular arcs |
| CIRCLE | Full circles |
| LWPOLYLINE | Lightweight polylines (2D) |
| POLYLINE | 3D polylines (flattened) |
| SPLINE | NURBS curves (approximated) |
| ELLIPSE | Elliptical arcs |
| POINT | Drilling locations |

### Partially Supported

| Entity | Notes |
|--------|-------|
| HATCH | Boundary extracted, fill ignored |
| DIMENSION | Reference only, not machined |
| TEXT | Converted to polylines (if font available) |
| MTEXT | Converted to polylines (if font available) |

### Not Supported

| Entity | Alternative |
|--------|-------------|
| 3DFACE | Use projected 2D geometry |
| MESH | Export as 2D section |
| SOLID3D | Export as 2D section |
| IMAGE | Not applicable |

---

## Auto-Heal Features

### Gap Closing

Connects endpoints within tolerance:

```
Default tolerance: 0.1 mm
Maximum tolerance: 1.0 mm
```

### Arc Fitting

Converts dense point sequences back to arcs:

```
Minimum points: 8
Maximum deviation: 0.01 mm
```

### Duplicate Removal

Removes exact duplicate entities (same type, coordinates, layer).

---

## Coordinate System

DXF files use the following coordinate mapping:

| DXF Axis | ToolBox Axis | CNC Axis |
|----------|--------------|----------|
| X | X | X |
| Y | Y | Y |
| Z | Ignored | Depth from toolpath |

### Origin Handling

Options for setting the work origin:

| Option | Description |
|--------|-------------|
| DXF Origin | Use (0,0) from the DXF file |
| Bounding Box Center | Center of geometry |
| Bounding Box Corner | Lower-left corner of geometry |
| Custom | User-specified coordinates |

---

## Best Practices

### Before Export from CAD

1. **Explode blocks and references** - Nested entities may not import correctly
2. **Convert splines to polylines** - Better toolpath accuracy
3. **Check for overlapping geometry** - Remove duplicates
4. **Verify scale** - Confirm units (mm vs inches)
5. **Clean up layers** - Remove unused layers

### After Import

1. **Review validation report** - Address any issues
2. **Check bounding box** - Verify dimensions are correct
3. **Inspect contour direction** - CW vs CCW matters for climb/conventional
4. **Verify layer assignments** - Correct operations for each layer

---

## Troubleshooting

### "File too large"

- Maximum file size: 50 MB
- Solution: Simplify geometry, reduce point density

### "Invalid DXF format"

- File may be corrupted or unsupported version
- Solution: Re-export as DXF R2013 from CAD software

### "No geometry found"

- All entities may be on frozen/off layers
- Solution: Unfreeze layers in CAD software before export

### "Too many open contours"

- Common with laser-cut files that use disconnected segments
- Solution: Use "Join Contours" tool with appropriate tolerance

---

## Related

- [Toolpath Generation](toolpaths.md) - Create G-code from imported geometry
- [Machine Profiles](../cam/machine-profiles.md) - Configure work area limits
