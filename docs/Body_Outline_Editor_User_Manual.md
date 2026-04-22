# Body Outline Editor User Manual
## v3.5.0 — Internal Use Only

**Access:** [INTERNAL_ACCESS_NOTE]

---

## Chapter 1: Interface Orientation

### What the Body Outline Editor does

The Body Outline Editor is a browser-based CAD tool for drawing and editing guitar body outlines. You work in millimeters, with a coordinate origin at the body center and the Y-axis pointing toward the neck. The tool produces three outputs: DXF files for CAM and Fusion 360, JSON files for the Body Solver API, and SVG files for documentation or web display.

The tool is designed for tracing reference photographs, refining outlines with Bezier curves, and exporting geometry that matches real instruments to millimeter precision.

### Opening the editor

[INTERNAL_ACCESS_NOTE]

When the page loads, you see four regions: the toolbar at the top, the canvas in the center, the right-side panel, and the status bar at the bottom. A default dreadnought-like outline appears on the canvas.

### The toolbar

The toolbar runs across the top of the window in grouped sections, separated by vertical divider lines.

**File and history group.** New, Undo, and Redo. New clears the canvas and resets to the default outline; unsaved changes trigger a confirmation. Undo and Redo work on a fifty-step history.

**Grid and display group.** Grid toggles the coordinate grid. Snap dropdown sets the grid increment to 0.1, 0.5, 1, 5, or 10 millimeters; nodes snap to these intervals when dragged. Handles toggles visibility of Bezier control handles for every node at once.

**Mode group.** Mirror toggles symmetric editing mode. Outer and + Void switch between editing the main body outline and editing a void (cavity, pickup opening, soundhole).

**Path editing group.** Simplify reduces the number of nodes while approximating the original curve; the tolerance field controls aggressiveness. Smooth All converts every node in the active path to a smooth curve.

**Measurement group.** Three measurement tools: Distance (📏), Angle (📐), Arc Length (〰️). Clear Measurements (🗑️) removes all.

**Image and calibration group.** Import Image loads a reference photograph. Calibrate sets real-world scale. Clear Image removes it. Image Layers panel manages multiple images.

**Template group.** Template dropdown lists eight built-in body shapes (Dreadnought, Jumbo, OM/000, Classical, Parlor, Stratocaster, Les Paul, Telecaster). Load Template replaces the current outline. Save Template stores custom templates.

**Instrument and Solve group.** Instrument dropdown selects the spec for the Body Solver API (Dreadnought, Cuatro Venezolano, Stratocaster, Jumbo). Solve Outline sends landmarks to the backend and receives a parametrically-derived outline. A confidence badge shows the solver's confidence (green ≥70%, amber 40-69%, orange <40%).

**Export group.** Export DXF, Export JSON, and Export SVG.

**Units selector.** Toggles display between mm, inches, and points.

**Auth group (hidden by default).** Login and Logout for API access. Appears when backend returns 401 or when an API key is stored.

### The canvas

The canvas fills the center. A dark grid shows the coordinate system. Origin (0,0) is the body center. Y-axis points upward (toward neck). X-axis runs left-right (bass positive, treble negative).

**Legend.** Alt+click node toggles smooth/cusp. Alt+drag handle makes asymmetric. Delete removes a node. Space+drag pans.

**Bounding box readout.** Upper-right corner displays width and height of the whole outline in millimeters. Updates when geometry changes.

**Cursor readout.** Status bar shows X,Y coordinates of mouse pointer.

**Selected node readout.** Status bar and Nodes panel show exact coordinates of selected node.

**Distance readout.** Appears when using Measure tools, showing measured value.

### The right panel

**Nodes panel.** Lists every node with X,Y coordinates. Clicking a row selects that node.

**Image Layers panel.** Manages multiple reference images: add, delete, reorder, visibility, locking, opacity.

**Measurements panel.** Lists all measurements with values and delete controls.

**Voids panel.** Lists voids with role and delete button. "+ Add Void" creates new voids.

**My Templates panel.** Lists user-saved templates.

### The status bar

Cursor — mouse coordinates. Selected — index of selected node. Nodes — total count. Zoom — percentage. Grid — ON/OFF. Mode — Outer or void ID. Auto-save indicator — green checkmark appears after edits.

---

## Chapter 2: Creating and Moving Nodes

### The default starting point

A small dreadnought-like outline appears on load — eight nodes at roughly one-quarter scale, centered at origin. Edit it or start fresh with Empty Mode.

### Two kinds of clicks that place nodes

**Click on existing curve** — inserts a new node exactly on the curve. New node is smooth by default.

**Click in empty space** — deselects.

**Empty Mode:** Start with no nodes. Click to place first dot. Click existing dot (green highlight) as anchor. Click empty space to place new dot after anchor. Click on dashed line to insert dot between.

### Selecting nodes

**Single-click** a node to select it. Handles become visible. Status bar shows position.

**Shift+click** to add a second node (max two).

**Click in Nodes panel** to select by coordinate.

**Click empty space** to deselect.

### Moving nodes

**Dragging:** Click and drag selected node. Snaps to grid. Orange circle appears at each snap point. Mirror mode moves the twin.

**Keyboard nudging:** Arrow keys move by current snap size. Shift+Arrow moves 0.1mm (fine adjustment). Works on multi-selections. Respects mirror mode.

**Numeric entry:** Double-click selected node. Enter exact X,Y values.

**Dimension label during drag:** Orange label shows Δx, Δy in mm. Appears only for single-node drags.

### Deleting nodes

Select node(s) and press Delete.

- Single node: deletes immediately
- Two+ nodes: confirmation dialog appears
- Minimum 3 nodes enforced

### Auto-save

Every node operation triggers auto-save to localStorage. Green "✓ Auto-saved" indicator appears. Restore prompt appears on reload within 24 hours.

---

## Chapter 3: Bezier Curves and Node Shaping

### What a Bezier node is

Every node has three components:

- **Anchor point** — X,Y position
- **Handle-in** — controls curve approaching the node
- **Handle-out** — controls curve leaving the node

### Three node states

**Cusp:** No handles. Sharp corner. Use at actual corners.

**Smooth symmetric:** Handles are mirror images. Curve flows smoothly through node. Default for most body work.

**Smooth asymmetric:** Handles have different lengths. Still smooth, but curvature differs on each side. Use for transitions.

### Showing and hiding handles

Handles appear only for selected nodes by default. "Handles: ON" toolbar button shows all handles at once.

### Dragging handles

**Default drag:** Symmetric — moving handle-in moves handle-out to mirror position.

**Alt+drag:** Asymmetric — only the dragged handle moves.

### Alt+click to toggle smooth/cusp

Alt+click on a node toggles between cusp and smooth symmetric.

### Smooth All button

Runs `.smooth()` on every node. Gives fresh symmetric handles.

**Use when:** After loading a template, after Simplify, after messy edits.

**Avoid when:** You have intentionally asymmetric handles — they will be overwritten.

### Simplify button

Reduces node count while approximating the curve. Tolerance field controls aggressiveness (1-10, default 2.5).

**Use when:** Outline has too many nodes (200+), after tracing, before export.

**Warning:** Simplify is one-step and undoable with Ctrl+Z, but no preview.

### Shaping a curve in practice

1. Place nodes at key anchor points
2. Run Smooth All
3. Inspect result
4. Drag handles to adjust
5. Use Alt+drag for asymmetric transitions
6. Use Alt+click for corners
7. Simplify if too many nodes

### Handle length as design lever

- **Short handles (20% of segment length):** Tighter curve, more angular
- **Medium handles (35-40%):** Natural look (auto-smooth target)
- **Long handles (50%+):** Looser, sweeping curve

---

## Chapter 4: Mirror Mode

### What mirror mode does

When ON, editing a node on one side automatically moves its mirror twin on the opposite side. The centerline (X=0) is preserved.

### Turning mirror mode on/off

Click "Mirror: OFF" button. Button turns green, dashed green centerline appears.

### What mirror mode affects

| Operation | Mirrored? |
|-----------|-----------|
| Dragging node | ✅ Yes |
| Keyboard nudge | ✅ Yes |
| Handle drag | ✅ Yes |
| Insert node | ❌ No (insert both sides manually) |
| Delete node | ❌ No (delete both sides manually) |
| Alt+click smooth/cusp | ❌ No (apply to both sides) |

### How mirror matching works

Weighted scoring formula:
- Y-coordinate match (weight 2)
- X-coordinate mirror match (weight 3)
- Handle similarity (weight 1)

Best match within 30mm threshold wins. If no good match, no mirroring occurs.

### Reliable mirror workflow

1. Start with mirror mode ON from the beginning
2. Use templates (they generate symmetric outlines)
3. Insert nodes on both sides manually
4. Edit by dragging (twins follow)
5. Delete nodes in pairs

### Mirror validation

The editor checks symmetry after deletions and shows warnings as orange toasts. Run `testWeightedMirror()` in console for detailed diagnostics.

### What mirror mode does NOT do

- Voids (edit them separately)
- Insert mirrored node pairs
- Delete mirrored pairs
- Alt+click smooth/cusp propagation

---

## Chapter 5: Reference Images and Calibration

### Supported formats

JPEG and PNG only.

### Importing an image

Click "Import Image". File picker opens. Image loads at view center, opacity 50%.

### Image Layers panel

Manage multiple reference images:

- **+ Layer** — add new image layer
- **- Layer** — delete active layer
- **↑/↓** — reorder layers
- **👁️** — toggle visibility
- **🔓 Lock** — prevent accidental movement

### Image transformations

**Rotation:**
- ↺ 90° / ↻ 90° — rotate in 90-degree increments
- Free rotation slider — continuous 0-360° rotation

**Scaling:**
- Click Scale button, drag horizontally for X scale, vertically for Y scale
- Hold Shift for uniform scaling (aspect locked)

**Locking:** Prevents any transformation of the image.

### Calibration workflow

Calibration establishes real-world scale:

1. Import image first
2. Click Calibrate (or press C)
3. Click first endpoint of known distance
4. Click second endpoint
5. Enter known distance in millimeters
6. Click Apply

The image is rescaled so pixel distances match mm.

### Validation checks

- Distance must be positive number
- Points must be at least 5 pixels apart
- Scale factor sanity check (0.01-100)
- Image size warning (if resulting image <50px or >5000px)

### User templates

**Save Template:** Saves current image + calibration + transforms to localStorage. Name the template.

**Load Template:** Select saved template from dropdown. Creates new layer with saved image.

Storage limit warning appears for images >4.5MB.

### Calibration accuracy

- **High (±0.5mm):** Scaled plan with printed scale bar, zoomed clicks
- **Medium (±2mm):** Photo with known feature, careful clicks
- **Low (±5mm+):** Guessed dimensions, rough placement

### What calibration doesn't do

- Correct perspective distortion (use orthographic renders)
- Correct lens distortion (avoid wide-angle photos)
- Persist in DXF/JSON (only in sessions and templates)

---

## Chapter 6: Voids

### What a void is

A closed region inside the body outline representing a cavity or opening: pickup routes, control cavities, switch pockets, jack holes, soundholes.

### Void roles

| Role | Color | DXF Layer |
|------|-------|-----------|
| pickup | orange | VOID_PICKUP |
| control_cavity | amber | VOID_CONTROL_CAVITY |
| switch | yellow | VOID_SWITCH |
| jack | orange-red | VOID_JACK |
| soundhole | blue | VOID_SOUNDHOLE |
| other | purple | VOID_OTHER |

Role is a tag — doesn't constrain shape.

### Creating a void

Click "+ Void" button or "+ Add Void" in Voids panel. Select role. Click Create. Default shape appears at origin.

### Editing voids

Same as outer outline: select nodes, drag, handles, insert, delete. Minimum 3 nodes enforced.

### Switching between voids

Click void entry in Voids panel to make it active. Status bar shows "Mode: void_id".

### Mirror mode and voids

Mirror mode does NOT apply to voids. For symmetric features, edit both sides manually.

### Deleting voids

Click × button on void entry. No confirmation (undo with Ctrl+Z).

### Void winding and export

DXF export automatically enforces:
- Outer outline: counterclockwise (CCW)
- Voids: clockwise (CW)

### Positioning voids

Use numeric entry for exact placement. Don't eyeball.

---

## Chapter 7: Templates

### Built-in templates (8)

**Acoustic:**
- Dreadnought — 508/394/286/254 (length/lower/upper/waist)
- Jumbo — 530/432/304/280
- OM/000 — 482/380/280/254
- Classical — 482/362/280/242
- Parlor — 400/304/228/204

**Electric:**
- Stratocaster — 400/318/166/220
- Les Paul — 400/342/166/230
- Telecaster — 394/318/204/240

All dimensions in mm.

### Loading a template

Select from dropdown, click Load Template. Replaces current outer path. Auto-smooths. View auto-centers.

### User templates

**Save Template:** Saves current outline to localStorage. Name required.

**Load Template (User):** Select from "My Templates" panel. Loads as current outline.

### Template-to-spec mapping

When loading a template, Instrument dropdown updates to closest match:
- Dreadnought → dreadnought
- Jumbo → jumbo
- OM/000, Classical, Parlor → cuatro_venezolano
- Stratocaster, Les Paul, Telecaster → stratocaster

---

## Chapter 8: Export

### DXF export

**Format options:**
- R12 (legacy, most compatible)
- R2004+ (modern, smaller files)

**Tessellation:** 10-100 points per curve. Higher = smoother but larger files.

**Layer naming:**
- Standard: BODY_OUTLINE, VOID_*, MEASUREMENTS
- CAM ready: 1,2,3...

**Include options:**
- Measurements as TEXT entities
- Voids

**Validation:** Self-intersection check before export. Warns if found.

### JSON export

Structured data for programmatic consumers:

```json
{
  "schema_version": 1,
  "units": "mm",
  "origin": "body_center_y_positive_toward_neck",
  "outer": { "points": [[x,y], ...], "winding": "ccw" },
  "voids": [...]
}
```

### SVG export

Bezier curves preserved. Measurement annotations included. For documentation and web display.

### Session files (.sgession)

Full editor state: all nodes, handles, voids, reference images, calibration, viewport. For continuing work later. Load with Ctrl+O, save with Ctrl+S.

### Which format to use

| Destination | Format |
|-------------|--------|
| Continue editing later | Session (.sgession) |
| CAM / Fusion 360 | DXF |
| Programmatic use | JSON |
| Documentation / web | SVG |
| Emergency recovery | Auto-save |

---

## Chapter 9: Body Solver API Integration

### What Solve does

Sends landmarks from your outline to the Body Solver API. Receives a mathematically-derived outline that satisfies design constraints for the selected instrument class.

### The UI

**Instrument dropdown:** Selects instrument spec (Dreadnought, Cuatro Venezolano, Stratocaster, Jumbo).

**Solve Outline button:** Green button. Invokes solver.

**Confidence badge:** Shows result confidence. Green ≥70%, amber 40-69%, orange <40%.

### How Solve works

1. **Landmark extraction:** pathToLandmarks() extracts up to five landmarks from outline
2. **Validation:** Sanity checks (lower bout wider than upper, waist narrower, Y-order correct)
3. **Minimum check:** At least 3 landmarks required
4. **API call:** POST to /api/body/solve-from-landmarks
5. **Response:** Returns generated outline, dimensions, confidence
6. **Replace outline:** Solver's output replaces current geometry
7. **Feedback:** Confidence badge updates, dimension overlay appears

### Authentication

API requires authentication for paid tier. Login button appears when backend returns 401 or when stored key exists.

**Login:** Enter API key when prompted. Stored in localStorage.

**Logout:** Clears stored key.

**Rate limiting:** 429 response shows alert. No automatic retry.

### Mock mode

Default `useMock: true` runs solver locally (no network). Returns synthetic responses for testing. Set `window.bodyAPI.useMock = false` in console for real API.

### Confidence interpretation

- **≥70% (green):** Solver confident. Landmarks consistent with instrument class.
- **40-69% (amber):** Reasonable fit, some compromise.
- **<40% (orange):** Struggled. Output may not match intent.

### Smart Guitar and Solve

The Smart Guitar is a custom design that doesn't match any spec. Two approaches:

1. **Solve as starting point:** Solve against Stratocaster, then edit toward Smart Guitar shape
2. **Don't use Solve:** Draw freehand with numeric entry for every critical dimension

### Error handling

| Error | Response |
|-------|----------|
| Landmark validation fails | Alert: "Cannot solve: [error]" |
| <3 landmarks | Alert: "Need at least 3 landmarks" |
| 401 | Auth UI appears, alert: "Authentication required" |
| 429 | Alert: "Rate limit exceeded. Try again." |
| Network/server error | Alert with error message |

---

## Appendix A: Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+N` | New |
| `Ctrl+S` | Save Session |
| `Ctrl+O` | Open Session |
| `Ctrl+E` | Export JSON |
| `Delete` | Delete selected node(s) |
| `Arrow keys` | Nudge by snap size |
| `Shift+Arrow` | Fine nudge (0.1mm) |
| `G` | Toggle grid |
| `M` | Measure distance |
| `C` | Calibrate image |
| `Space+drag` | Pan canvas |
| `Alt+click node` | Toggle smooth/cusp |
| `Alt+drag handle` | Asymmetric handle |
| `Esc` | Exit measurement/calibration mode |
| `Ctrl+Shift+M` | Clear all measurements |

---

## Appendix B: Test Functions (Console)

| Function | Purpose |
|----------|---------|
| `testBackendAPI()` | Test API connectivity |
| `testAll()` | Run all tests |
| `testTemplate(id)` | Load template |
| `testLandmarks()` | Extract and validate landmarks |
| `testWeightedMirror()` | Validate mirror symmetry |
| `testSelfIntersection()` | Check for self-crossings |
