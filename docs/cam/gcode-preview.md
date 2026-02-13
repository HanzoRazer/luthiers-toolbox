# G-code Preview

Visualize and verify toolpaths before sending to your CNC machine.

---

## Preview Modes

### 2D View

Top-down view of toolpath lines.

**Features:**

- Pan and zoom
- Layer visibility toggle
- Rapid vs feed move colors
- Depth color gradient

**Color Coding:**

| Color | Meaning |
|-------|---------|
| Blue | Rapid moves (G0) |
| Green | Feed moves (G1) |
| Red | Plunge moves |
| Yellow | Retract moves |
| Orange | Arcs (G2/G3) |

---

### 3D View

Isometric view of toolpath with simulated stock.

**Features:**

- Rotate, pan, zoom
- Stock material visualization
- Material removal simulation
- Tool visualization

**Controls:**

| Action | Mouse | Keyboard |
|--------|-------|----------|
| Rotate | Left drag | Arrow keys |
| Pan | Right drag | Shift + Arrows |
| Zoom | Scroll | +/- |
| Reset | Double-click | Home |

---

### Simulation Mode

Animated playback of the machining process.

**Features:**

- Play/pause/step controls
- Speed adjustment (0.5x - 10x)
- Current position display
- Elapsed time / estimated time

**Controls:**

| Button | Action |
|--------|--------|
| Play | Start animation |
| Pause | Stop animation |
| Step | Advance one move |
| Reset | Return to start |
| Speed | Adjust playback speed |

---

## Analysis Tools

### Statistics Panel

| Statistic | Description |
|-----------|-------------|
| Total Distance | Length of all moves |
| Cutting Distance | Length of feed moves only |
| Rapid Distance | Length of rapid moves |
| Number of Retracts | Count of Z retracts |
| Estimated Time | Based on feed rates |
| Operations | Count by type |

---

### Bounds Check

Verify toolpath fits within machine limits:

| Check | Status |
|-------|--------|
| X Range | min → max |
| Y Range | min → max |
| Z Range | min → max |
| Fits Machine | ✓ / ✗ |

---

### Feed Rate Analysis

| Metric | Value |
|--------|-------|
| Minimum Feed | Slowest feed rate used |
| Maximum Feed | Fastest feed rate used |
| Average Feed | Weighted average |
| Feed Changes | Number of F commands |

---

## Verification Checklist

Before running on your machine:

### Geometry Checks

- [ ] Toolpath fits within work area
- [ ] No unexpected rapid moves through stock
- [ ] Plunge depths are reasonable
- [ ] Retracts clear fixtures and clamps

### Tool Checks

- [ ] Tool diameter correct for detail level
- [ ] Stepover appropriate (40-60% typical)
- [ ] Stepdown safe for material

### Feed/Speed Checks

- [ ] Feed rate within machine limits
- [ ] Spindle speed appropriate for tool/material
- [ ] Plunge rate not too aggressive

### Safety Checks

- [ ] Safe Z height clears all fixtures
- [ ] Start position is accessible
- [ ] End position is safe

---

## Measurement Tools

### Distance

Click two points to measure:

```
Point A: (10.5, 20.3)
Point B: (45.2, 20.3)
Distance: 34.7 mm
```

### Depth

Click a point to see Z depth:

```
Position: (25.0, 30.0)
Z Depth: -5.0 mm
Operation: Pocket
```

### Time to Point

Click any point to see estimated time to reach:

```
Position: (50.0, 50.0)
Time: 1:23 of 5:47 total
Progress: 24%
```

---

## Export Options

### Screenshot

Save current view as image:

- PNG (transparent background)
- JPG (white background)
- SVG (vector, 2D only)

### Video

Export simulation as video:

- MP4 (H.264)
- GIF (animated)
- Frame rate: 30/60 fps

---

## G-code Editor

View and edit raw G-code:

### Features

- Syntax highlighting
- Line numbers
- Search and replace
- Error highlighting

### Edit Capabilities

| Edit | Description |
|------|-------------|
| Modify values | Change coordinates/feeds |
| Insert lines | Add commands |
| Delete lines | Remove commands |
| Comment/uncomment | Toggle comments |

!!! warning "Edit with Caution"
    Manual G-code edits bypass safety checks.
    Always re-verify after editing.

---

## API Usage

```python
import requests

# Get preview data
response = requests.get(
    "http://localhost:8000/api/cam/preview/{job_id}"
)

preview = response.json()
print(f"Total distance: {preview['stats']['total_distance_mm']} mm")
print(f"Estimated time: {preview['stats']['estimated_time_sec']} sec")

# Get bounds
bounds = preview['bounds']
print(f"X: {bounds['x_min']} to {bounds['x_max']}")
print(f"Y: {bounds['y_min']} to {bounds['y_max']}")
print(f"Z: {bounds['z_min']} to {bounds['z_max']}")
```

---

## Troubleshooting

### Preview is slow

- Reduce G-code line count (increase tolerance)
- Disable 3D simulation
- Use 2D view for quick checks

### Unexpected movements

- Check for orphan geometry in DXF
- Verify operation order
- Check rapid height settings

### Missing geometry

- Ensure all layers are visible
- Check operation assignments
- Verify DXF import was complete

---

## Related

- [Toolpath Generation](../features/toolpaths.md) - Create toolpaths
- [Post Processors](post-processors.md) - G-code output
- [Safety & RMOS](safety-rmos.md) - Safety verification
