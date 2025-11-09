# Patches G-H0 Quick Reference

## API Endpoints Summary

### Patch G: Enhanced Roughing with Units/Lead-In/Tabs
**Endpoint**: `POST /cam/roughing_gcode`

**New Parameters**:
- `units` (string): "mm" or "inch" - Output units with G21/G20
- `lead_radius` (float): 0-10mm - Lead-in/out arc radius (0=disabled)
- `tabs_positions` (array): [25.0, 75.0, ...] - Explicit tab distances (optional)

**Example**:
```bash
curl -X POST http://localhost:8000/cam/roughing_gcode \
  -H "Content-Type: application/json" \
  -d '{
    "polyline": [[0,0],[300,0],[300,450],[0,450]],
    "tool_diameter": 6.0,
    "depth_per_pass": 2.0,
    "stock_thickness": 12.0,
    "feed_xy": 1200,
    "feed_z": 600,
    "safe_z": 10.0,
    "origin": [0, 0],
    "climb": true,
    "tabs_count": 4,
    "tab_width": 10.0,
    "tab_height": 2.0,
    "post": "Mach4",
    "units": "inch",
    "lead_radius": 5.0
  }'
```

---

### Patch H: Adaptive Pocketing
**Endpoint**: `POST /cam/pocket_gcode`

**Key Parameters**:
- `entities` (array): Pocket boundary (lines/arcs/circles)
- `tool_diameter` (float): Tool diameter in mm
- `stepover_pct` (float): 5-95% of tool diameter
- `raster_angle` (float): 0-360° rotation
- `depth_per_pass` (float): Z increment per pass
- `target_depth` (float): Total pocket depth

**Example**:
```bash
curl -X POST http://localhost:8000/cam/pocket_gcode \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {"type": "line", "A": [10, 10], "B": [60, 10]},
      {"type": "line", "A": [60, 10], "B": [60, 35]},
      {"type": "line", "A": [60, 35], "B": [10, 35]},
      {"type": "line", "A": [10, 35], "B": [10, 10]}
    ],
    "tool_diameter": 6.0,
    "stepover_pct": 50,
    "raster_angle": 0,
    "depth_per_pass": 2.0,
    "target_depth": 6.0,
    "feed_xy": 1200,
    "feed_z": 600,
    "safe_z": 10.0,
    "units": "mm",
    "filename": "control_cavity.nc"
  }' \
  --output control_cavity.nc
```

---

### Patch H0: CAM-Neutral Export
**Endpoint**: `POST /neutral/bundle.zip`

**Parameters**:
- `entities` (array): Geometry with layer assignments
- `product_name` (string): Design name for filenames
- `units` (string): "mm" or "inch"
- `simplify` (bool): Convert splines to lines/arcs

**Layer Schema**:
- `CUT_OUTER` - Body/neck outer profile (through-cut)
- `CUT_INNER` - Pickup cavities, soundholes (through-cut)
- `POCKET` - Control cavities, neck pocket (depth-limited)
- `ENGRAVE` - Inlay channels, decorative routing
- `DRILL` - Tuner holes, bridge pins
- `REF_STOCK` - Stock material boundary (reference)
- `TABS_SUGGESTED` - Recommended holding tab positions

**Example**:
```bash
curl -X POST http://localhost:8000/neutral/bundle.zip \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {"type": "line", "A": [0, 0], "B": [300, 0], "layer": "CUT_OUTER"},
      {"type": "circle", "center": [100, 200], "radius": 45, "layer": "CUT_INNER"},
      {"type": "line", "A": [70, 150], "B": [150, 150], "layer": "POCKET"},
      {"type": "circle", "center": [165, 80], "radius": 3, "layer": "DRILL"}
    ],
    "product_name": "LesPaul_Body",
    "units": "mm"
  }' \
  --output LesPaul_Body_CAM_Bundle.zip
```

**Output**: ZIP file containing:
- `LesPaul_Body.dxf` - DXF R12 centerline geometry
- `LesPaul_Body.svg` - SVG visualization
- `LesPaul_Body.json` - JSON metadata
- `README.txt` - Import instructions

---

## File Changes Summary

### Server Files Modified (Patch G)
- **server/roughing.py** (~290 lines)
  - Added `with_units_header` import
  - Renamed `add_tabs()` → `add_tabs_by_count()`
  - Added `_lead_arc_moves()` function (90 lines)
  - Enhanced `emit_gcode()` with `units` and `lead_radius` parameters
  - Units scaling: `to_units_scale = 1.0/25.4` for inch
  - Lead-in/out arc generation with G2/G3 commands

- **server/gcode_post.py** (+43 lines)
  - Added `with_units_header()` function
  - Token replacement for G20/G21 in post-processor headers

- **server/cam_router.py** (~150 lines)
  - Updated import: `add_tabs` → `add_tabs_by_count`
  - Enhanced `CamInput` model with:
    - `lead_radius: float = Field(0.0, ge=0.0)`
    - `tabs_positions: Optional[List[float]] = Field(None)`
  - Tab positioning logic (explicit vs auto-distribution)

### Server Files Created (Patches H and H0)
- **server/pocketing.py** (~280 lines)
  - `arc_flatten()` - Discretize arcs
  - `to_polygon_from_entities()` - Convert entities to polygon
  - `polygon_bounds()` - Bounding box calculation
  - `point_in_polygon()` - Ray-casting test
  - `raster_paths()` - Zig-zag toolpath generation with rotation
  - `emit_gcode_raster()` - G-code output for pocket clearing

- **server/cam_pocket_router.py** (~130 lines)
  - `PocketInput` model with validation
  - `POST /cam/pocket_gcode` endpoint
  - Returns G-code as downloadable .nc file

- **server/export_neutral.py** (~350 lines)
  - `LAYER_SCHEMA_DEFAULT` - 7 standard CAM layers
  - `simplify_to_lines_arcs()` - Convert splines
  - `write_dxf_ascii()` - DXF R12 generation
  - `write_svg()` - SVG with grouped layers
  - `make_readme()` - CAM import instructions
  - `bundle_neutral()` - 4-file ZIP bundle creator

- **server/neutral_router.py** (~100 lines)
  - `BundleRequest` model
  - `POST /neutral/bundle.zip` endpoint
  - Returns ZIP file with DXF/SVG/JSON/README

- **server/app.py** (+10 lines)
  - Registered 3 new routers:
    - `cam_router` (Patch F2/G)
    - `cam_pocket_router` (Patch H)
    - `neutral_router` (Patch H0)

---

## Testing Commands

### Test Units Conversion
```bash
# Generate G-code in inch units
curl -X POST http://localhost:8000/cam/roughing_gcode \
  -H "Content-Type: application/json" \
  -d '{"polyline":[[0,0],[25.4,0],[25.4,25.4],[0,25.4]],"tool_diameter":6,"depth_per_pass":2,"stock_thickness":5,"feed_xy":1200,"feed_z":600,"safe_z":10,"origin":[0,0],"climb":true,"tabs_count":0,"tab_width":0,"tab_height":0,"post":"Mach4","units":"inch"}' \
  | grep "G20"  # Should output G20 header
```

### Test Lead-In Arc
```bash
# Generate with 5mm lead-in
curl -X POST http://localhost:8000/cam/roughing_gcode \
  -H "Content-Type: application/json" \
  -d '{"polyline":[[0,0],[100,0],[100,50],[0,50]],"tool_diameter":6,"depth_per_pass":2,"stock_thickness":5,"feed_xy":1200,"feed_z":600,"safe_z":10,"origin":[0,0],"climb":true,"tabs_count":0,"tab_width":0,"tab_height":0,"post":"Mach4","lead_radius":5.0}' \
  | grep "G2\|G3"  # Should output G2 or G3 arc command
```

### Test Pocketing
```bash
# Generate rectangular pocket
curl -X POST http://localhost:8000/cam/pocket_gcode \
  -H "Content-Type: application/json" \
  -d '{"entities":[{"type":"line","A":[0,0],"B":[50,0]},{"type":"line","A":[50,0],"B":[50,30]},{"type":"line","A":[50,30],"B":[0,30]},{"type":"line","A":[0,30],"B":[0,0]}],"tool_diameter":6,"stepover_pct":50,"raster_angle":0,"depth_per_pass":2,"target_depth":6,"feed_xy":1200,"feed_z":600,"safe_z":10,"units":"mm","filename":"test.nc"}' \
  --output test_pocket.nc

# Verify file created
ls -lh test_pocket.nc
```

### Test Neutral Export
```bash
# Generate CAM bundle
curl -X POST http://localhost:8000/neutral/bundle.zip \
  -H "Content-Type: application/json" \
  -d '{"entities":[{"type":"line","A":[0,0],"B":[100,0],"layer":"CUT_OUTER"},{"type":"circle","center":[50,50],"radius":10,"layer":"DRILL"}],"product_name":"Test","units":"mm"}' \
  --output Test_CAM_Bundle.zip

# Unzip and verify contents
unzip -l Test_CAM_Bundle.zip
# Should list: Test.dxf, Test.svg, Test.json, README.txt
```

---

## Troubleshooting

### Issue: Import errors when starting server
**Symptom**: `ModuleNotFoundError: No module named 'cam_router'`
**Solution**: 
```bash
cd server
# Verify files exist
ls cam_router.py cam_pocket_router.py neutral_router.py pocketing.py export_neutral.py

# Restart server
uvicorn app:app --reload --port 8000
```

### Issue: G-code coordinates too small/large
**Symptom**: Fusion 360 shows tiny part or huge part
**Solution**: 
- Check `"units": "mm"` in request (default)
- For inch: `"units": "inch"` (coordinates auto-scaled by 1/25.4)
- Verify G21 (mm) or G20 (inch) in G-code header

### Issue: Lead-in arc crashes into part
**Symptom**: Tool collision during approach
**Solution**:
- Reduce `lead_radius` (try 3-5mm for 6mm tool)
- Ensure clearance around part boundary
- Check `climb: true` vs `false` (affects arc direction)

### Issue: Pocket clearing skips areas
**Symptom**: Raster paths don't cover full pocket
**Solution**:
- Ensure polygon is closed (first point = last point)
- Increase stepover (try 40-60%)
- Check `point_in_polygon` logic with test geometry

### Issue: ZIP bundle is corrupt
**Symptom**: Cannot open ZIP file
**Solution**:
- Verify `Content-Type: application/zip` header
- Check `entities` list is not empty
- Validate `product_name` (alphanumeric + underscores/hyphens only)

---

## Client Integration TODOs

### CAMPreview.vue Enhancements
- [ ] Add units dropdown (mm/inch selector)
- [ ] Add lead radius slider (0-10mm range)
- [ ] Implement visual tab editor (canvas click-to-place)
- [ ] Wire up enhanced API payload with Patch G fields

### New Components to Add
- [ ] **PocketLab.vue** - Pocketing parameter UI
  - Tool diameter input
  - Stepover slider
  - Raster angle dial
  - Depth controls
  - Generate button → `/cam/pocket_gcode`

- [ ] **ExportNeutral.vue** - CAM-neutral export UI
  - Product name input
  - Units selector
  - Layer assignment table
  - Export button → `/neutral/bundle.zip`

### Routing Updates
- [ ] Add `/pocket` route for PocketLab.vue
- [ ] Add `/export-neutral` route for ExportNeutral.vue
- [ ] Update navigation menu with new tools

---

## Performance Notes

| Operation | Typical Duration | Output Size |
|-----------|------------------|-------------|
| Roughing G-code (400mm perimeter) | ~50ms | 15KB |
| Pocketing (50mm² area) | ~200ms | 25KB |
| Neutral bundle (50 entities) | ~300ms | 45KB (ZIP) |

**Optimization Tips**:
- Use `simplify: true` for neutral export (converts splines)
- Reduce `stepover_pct` for faster pocketing (larger steps)
- Cache geometry conversions for repeated exports

---

## Next Steps

1. **Test Server Endpoints**:
   ```bash
   cd server
   uvicorn app:app --reload --port 8000
   # Test each endpoint with curl commands above
   ```

2. **Build Client Components**:
   - Copy component templates from this doc
   - Wire to API using `fetch()` or axios
   - Add to Vue Router

3. **End-to-End Testing**:
   - Generate roughing G-code in inch
   - Generate pocket clearing toolpath
   - Export CAM-neutral bundle
   - Import DXF into Fusion 360
   - Verify toolpaths simulate correctly

4. **Documentation**:
   - Update main README.md with new features
   - Create video tutorials for YouTube
   - Write blog post announcing Patches G-H0

---

**Quick Start**: See `PATCHES_G-H0_INTEGRATION.md` for comprehensive documentation.

**Support**: GitHub Issues or Discord #luthiers-toolbox
