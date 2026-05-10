# Spiral Component Containment Audit

**Date:** 2026-05-07  
**Dev Order:** 7  
**Status:** Complete  
**Policy:** FEATURE_PARITY_MIGRATION_POLICY.md

---

## Canonical Role

```
SpiralSoundholeDesigner.vue = canonical spiral implementation
ApertureWorkspace.vue = beta consolidation shell (State 3)
```

The workspace shell mounts the component but does not replace it. No migration is authorized until parity is verified.

---

## Component Location

```
packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue
```

Lines: 754 (template + script + style)

---

## Mounted Location

```
packages/client/src/views/art-studio/ApertureWorkspace.vue
```

Mounted via `defineAsyncComponent` with `<Suspense>` wrapper in the Spiral tab.

---

## Route Provenance

| Route | Status | Purpose |
|-------|--------|---------|
| `/calculators/acoustics/spiral-soundhole` | **Canonical** | Current production spiral tool |
| `/art-studio/aperture` | Beta | Consolidation shell mounting canonical component |

**Canonical production route:** `/calculators/acoustics/spiral-soundhole`  
**Beta consolidation route:** `/art-studio/aperture`

**Registry entries:**
- `spiral-soundhole` — stable, canonical: true
- `aperture-workspace` — beta, canonical: false, mounts: SpiralSoundholeDesigner.vue

**Replacement status:** Not allowed until parity checklist passes.

**Rule:** The standalone route must remain active until feature parity is verified under FEATURE_PARITY_MIGRATION_POLICY.md.

---

## Dependencies

### Vue Imports

```typescript
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
```

### Local Components

```typescript
import SliderRow from './SliderRow.vue'
```

SliderRow.vue created in Dev Order 6.1 — labeled range input with accent colors.

### External Dependencies

None. No store, no router, no provide/inject.

---

## Props / Emits

| Props | Emits |
|-------|-------|
| None | None |

The component is fully self-contained. It does not accept external configuration or emit events to parent components.

---

## Local State

### Reactive State

| Variable | Type | Purpose |
|----------|------|---------|
| `upper` | `reactive<SpiralParams>` | Upper bout spiral parameters |
| `lower` | `reactive<SpiralParams>` | Lower bout spiral parameters |
| `display` | `reactive` | Display options (centerlines, bodyFill, braceZones, grid) |

### Ref State

| Variable | Type | Purpose |
|----------|------|---------|
| `canvasEl` | `ref<HTMLCanvasElement>` | Canvas element reference |
| `exportLoading` | `ref<boolean>` | DXF export loading state |
| `exportError` | `ref<string>` | Export error message |
| `validationResult` | `ref<any>` | Validation response |

### Constants

| Variable | Value | Purpose |
|----------|-------|---------|
| `API_BASE` | `'/api/woodworking/soundhole/spiral'` | API endpoint base |
| `ROUND_REF_AREA` | `Math.PI * (50.8 / 2) ** 2` | 4-inch round reference (2026.8 mm²) |
| `canvasW` | `500` | Canvas width |
| `canvasH` | `660` | Canvas height |
| `SCALE` | `1.0` | Rendering scale |
| `OX`, `OY` | Computed | Canvas origin offsets |

### SpiralParams Interface

```typescript
interface SpiralParams {
  cx: number      // Center X (mm)
  cy: number      // Center Y (mm)
  r0: number      // Start radius (mm)
  k: number       // Growth rate per radian
  turns: number   // Number of turns
  slotW: number   // Slot width (mm)
  rot: number     // Rotation (degrees)
}
```

### Carlos Jumbo Defaults

```typescript
// Upper spiral
{ cx: -88, cy: -62, r0: 10, k: 0.18, turns: 1.1, slotW: 14, rot: 270 }

// Lower spiral
{ cx: 78, cy: 112, r0: 10, k: 0.18, turns: 1.1, slotW: 14, rot: 90 }
```

---

## API Calls

### Current Endpoints (WRONG)

```
POST /api/woodworking/soundhole/spiral/dxf
POST /api/woodworking/soundhole/spiral/validate
```

### Correct Endpoints

```
POST /api/instrument/soundhole/spiral/dxf
POST /api/instrument/soundhole/spiral/validate
POST /api/instrument/soundhole/spiral/geometry
GET  /api/instrument/soundhole/spiral/default
```

### Request Payload Format

```javascript
{
  upper: {
    center_x_mm: number,
    center_y_mm: number,
    start_radius_mm: number,
    growth_rate_k: number,
    turns: number,
    slot_width_mm: number,
    rotation_deg: number,
    label: string
  },
  lower: { /* same structure */ },
  body_type: 'carlos_jumbo',
  notes: string
}
```

---

## Geometry Calculations

### Client-Side Math

The component computes spiral metrics client-side via `spiralStats()`:

```typescript
function spiralStats(p: SpiralParams): SpiralStats {
  const thetaEnd = p.turns * 2 * Math.PI
  const rEnd = p.r0 * Math.exp(p.k * thetaEnd)
  
  // Corrected arc length formula
  let oneWall: number
  if (Math.abs(p.k) < 1e-6) {
    oneWall = p.r0 * thetaEnd  // Near-circular fallback
  } else {
    oneWall = Math.sqrt(1.0 + p.k * p.k) / p.k * (rEnd - p.r0)
  }
  
  const perim = 2 * oneWall
  const area = p.slotW * oneWall
  const pa = area > 0 ? perim / area : 0
  
  return { area, perim, pa, rEnd }
}
```

### Computed Properties

| Property | Formula | Purpose |
|----------|---------|---------|
| `upperStats` | `spiralStats(upper)` | Upper spiral metrics |
| `lowerStats` | `spiralStats(lower)` | Lower spiral metrics |
| `totalArea` | `upperStats.area + lowerStats.area` | Combined area |
| `areaRatioPct` | `totalArea / ROUND_REF_AREA * 100` | % vs 4-inch round |

### Math Correctness

The arc length formula matches the corrected formula in APERTURE_WORKSPACE_REFACTOR_STATUS.md:

```
L = sqrt(1 + k²) / k × (r_end - r0)
```

P:A ratio uses the closed-form relationship:

```
P:A = 2 / slot_width
```

---

## Rendering / Canvas Ownership

### Technology

Canvas 2D (not SVG). The component owns its own rendering loop.

### Drawing Functions

| Function | Purpose |
|----------|---------|
| `draw()` | Main render function, called on state change |
| `carlosJumboPoints()` | Generate Carlos Jumbo body outline (400 points) |
| `spiralWallPts()` | Generate outer/inner wall points for a spiral |
| `spiralCenterline()` | Generate centerline points |
| `drawPolyline()` | Canvas polyline helper |
| `drawSpiral()` | Render a single spiral with fill and stroke |

### Render Triggers

```typescript
watch([upper, lower, display], () => nextTick(draw), { deep: true })
onMounted(() => { nextTick(draw) })
```

### Visual Elements

- Body outline (Carlos Jumbo shape with flame maple grain texture)
- Upper spiral (gold accent #c8a050)
- Lower spiral (cyan accent #50a8c8)
- Brace keepout zones (optional)
- Coordinate grid (optional)
- Bridge reference
- Neck heel reference

---

## Export Behavior

### DXF Export

```typescript
async function exportDxf() {
  const res = await fetch(`${API_BASE}/dxf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildRequestBody()),
  })
  const blob = await res.blob()
  // Trigger download as 'spiral_soundhole_carlos_jumbo.dxf'
}
```

### Filename

```
spiral_soundhole_carlos_jumbo.dxf
```

### Other Exports

- SVG export: Not implemented
- JSON export: Not implemented
- Screenshot: Not implemented

---

## Presets / Defaults

### Hardcoded Presets

Carlos Jumbo dual-spiral defaults are hardcoded in component state initialization.

### Reset Function

```typescript
function resetToDefault() {
  upper.cx = -88; upper.cy = -62; upper.r0 = 10
  upper.k = 0.18; upper.turns = 1.1; upper.slotW = 14; upper.rot = 270
  lower.cx = 78; lower.cy = 112; lower.r0 = 10
  lower.k = 0.18; lower.turns = 1.1; lower.slotW = 14; lower.rot = 90
}
```

### Backend Presets

Not consumed. The backend has `/api/instrument/soundhole/spiral/default` but the component does not call it.

---

## CSS / Layout Assumptions

### Scoped Styles

All styles are scoped (`<style scoped>`). No global CSS leakage.

### Layout

- Flexbox column layout for overall structure
- CSS Grid for metric strip (6 columns)
- CSS Grid for designer body (3 columns: controls | canvas | stats)

### Color Theme

Dark theme assumed:
- Background: `#111827`, `#1f2937`
- Text: `#f9fafb`, `#9ca3af`
- Borders: `#374151`
- Accents: `#c8a050` (upper/gold), `#50a8c8` (lower/cyan), `#50b880` (good)

### CSS Variables Used

```css
var(--font-sans)
var(--font-mono)
var(--color-text-primary)
var(--color-text-secondary)
var(--color-text-tertiary)
var(--color-background-primary)
var(--color-background-secondary)
var(--color-border-secondary)
var(--color-border-tertiary)
```

---

## Runtime Verification

### Manual Test Results (2026-05-07)

| Test | Route | Result |
|------|-------|--------|
| Component loads | `/art-studio/aperture` | Pass |
| No console errors | Both routes | Pass |
| Sliders respond | Both routes | Pass |
| Preview updates | Both routes | Pass |
| DXF export | Both routes | **Likely Fails** (wrong endpoint) |
| Validation | Both routes | **Likely Fails** (wrong endpoint) |

### Backend Tests

```
pytest tests/test_aperture_geometry.py tests/test_aperture_geometry_endpoint.py -v
```

Result: **24 passed** (2026-05-07)

---

## Known Issues

### Issue 1 — Wrong API Endpoints

**Severity:** High  
**Status:** RESOLVED (Dev Order 8, 2026-05-07)

~~SpiralSoundholeDesigner calls:~~
```
/api/woodworking/soundhole/spiral/dxf   ← OLD (removed)
/api/woodworking/soundhole/spiral/validate   ← OLD (removed)
```

Now calls:
```
/api/instrument/soundhole/spiral/dxf   ← CORRECT
/api/instrument/soundhole/spiral/validate   ← CORRECT
```

The backend `soundhole_router.py` uses `DualSpiralRequest` which matches the frontend payload exactly. DXF export and validation now route to the correct endpoints.

### Issue 2 — No Backend Preset Consumption

**Severity:** Low

The component hardcodes Carlos Jumbo defaults instead of calling:
```
GET /api/instrument/soundhole/spiral/default
```

### Issue 3 — No aperture_geometry Display

**Severity:** Low

The backend now returns `aperture_geometry` in spiral responses (Dev Order 3), but the frontend does not display equivalent_diameter_mm or other normalized fields.

---

## Parity Checklist for Future Replacement

A future `SpiralAperturePanel.vue` may replace the canonical component only after:

- [ ] All current inputs are present (7 parameters × 2 spirals)
- [ ] All current sliders/controls are present
- [ ] Upper/lower spiral editing works
- [ ] Presets load correctly (hardcoded or from backend)
- [ ] Backend geometry call works (`/api/instrument/soundhole/spiral/geometry`)
- [ ] Corrected area/perimeter/path metrics display correctly
- [ ] `aperture_geometry` fields accessible (equivalent_diameter_mm, etc.)
- [ ] Preview updates live via canvas or SVG
- [ ] DXF export works (`/api/instrument/soundhole/spiral/dxf`)
- [ ] Validation behavior preserved
- [ ] Standalone route preserved or formally deprecated
- [ ] Browser runtime check passes (no console errors)
- [ ] Existing backend tests pass (24 aperture tests)

---

## Future Extraction Candidates

When migrating to a shared workspace architecture, consider extracting:

| Candidate | Reason |
|-----------|--------|
| `spiralStats()` | Pure function, reusable for any spiral geometry |
| `carlosJumboPoints()` | Body outline, could be backend-sourced |
| `spiralWallPts()` / `spiralCenterline()` | Geometry helpers |
| Canvas rendering | Could migrate to shared CanvasRenderer or SVG |
| Export logic | Could use shared ExportService |

---

## Do Not Change Yet

Per FEATURE_PARITY_MIGRATION_POLICY.md:

1. Do NOT rewrite SpiralSoundholeDesigner.vue
2. Do NOT split it into subcomponents
3. Do NOT move state to a store
4. Do NOT replace exports
5. Do NOT change API behavior
6. Do NOT remove `/calculators/acoustics/spiral-soundhole` route
7. Do NOT deprecate the component

All changes require parity verification first.

---

## Phase-2 Status Update

**Date:** 2026-05-07  
**Dev Order:** 14

Phase-2 Aperture Workspace development validated the containment audit findings:

**Resolved issues:**
- Endpoint mismatch resolved in Dev Order 8 (`/api/woodworking/` → `/api/instrument/`)
- Canonical provenance clarified in Dev Order 9
- Workspace mount validated (Spiral tab)

**Current status:**
- Shared comparison infrastructure operational
- Canonical spiral implementation remains intact
- Component still owns rendering, state, export behavior
- Workspace consumes spiral geometry outputs only

**Validation:**
- DXF export verified functional
- Validation endpoint verified functional
- Combined dual-spiral comparison operational
- No regression in canonical tool behavior

**Governance:**
`FEATURE_PARITY_MIGRATION_POLICY.md` successfully prevented regression during Phase-2.

---

## Revision History

| Date | Change |
|------|--------|
| 2026-05-07 | Phase-2 status update (Dev Order 14) |
| 2026-05-07 | Initial containment audit (Dev Order 7) |
