# CP-S53: CNC Saw Lab Operation Panels

**Status:** ✅ Complete  
**Components:** 3 Vue panels + full integration  
**Total Code:** ~2400 lines (3 files)

---

## Overview

Three interactive Vue 3 components for CNC saw operations with complete integration of blade registry (CP-S50), validation (CP-S51), learned overrides (CP-S52), and telemetry (CP-S59B).

---

## Components

### **1. SawSlicePanel.vue** (~800 lines)
**Purpose:** Kerf-aware straight cuts with multi-pass depth control

**Features:**
- Blade selection from CP-S50 registry
- Real-time kerf visualization
- Multi-pass depth strategy
- Validation via CP-S51
- Learned parameter merging via CP-S52
- G-code generation with arc commands
- Send to JobLog (CP-S59B)

**UI Elements:**
- Left column: Parameters (blade, machine, material, geometry, feeds/speeds)
- Right column: Validation results, learned params, G-code preview, SVG canvas
- Actions: Validate → Apply Learned → Generate → Send to JobLog

**Key Calculations:**
- Path length: `sqrt((x2-x1)² + (y2-y1)²)`
- Total length: `path_length × depth_passes`
- Estimated time: `(length / feed_mm_min) × 60`

---

### **2. SawBatchPanel.vue** (~900 lines)
**Purpose:** Schedule multiple slices with batch-level optimization

**Features:**
- Configurable slice count (1-50)
- Spacing control (distance between slices)
- Orientation (horizontal/vertical)
- Batch statistics (total length, volume, kerf loss)
- Multi-slice G-code with optimized pathing
- Batch-level validation

**UI Elements:**
- Left column: Batch configuration (slices, spacing, orientation)
- Right column: Batch stats grid (6 metrics), SVG preview with numbered slices
- Actions: Validate Batch → Apply Learned → Generate Batch → Send to JobLog

**Key Calculations:**
- Total passes: `num_slices × depth_passes`
- Total length: `slice_length × num_slices × depth_passes`
- Volume removed: `slice_length × kerf × total_depth × num_slices`
- Overhead time: `total_passes × 3s` (retract time)

---

### **3. SawContourPanel.vue** (~700 lines)
**Purpose:** Curved paths for rosettes and binding with radius validation

**Features:**
- 3 contour types: Arc, Circle, Rosette
- Real-time radius validation against blade diameter
- Dynamic SVG path generation
- Rosette pattern with configurable petals
- Radius indicator visualization
- Curve-specific validation

**Contour Types:**

**Arc Segment:**
- Parameters: center, radius, start_angle, end_angle
- SVG path: `M x1,y1 A radius,radius 0 large_arc 1 x2,y2`
- Length: `radius × angle_radians`

**Full Circle:**
- Parameters: center, radius
- SVG path: Two 180° arcs (full circle)
- Length: `2π × radius`

**Rosette Pattern:**
- Parameters: center, outer_radius, inner_radius, petal_count
- SVG path: Alternating outer/inner vertices
- Length: `2π × avg_radius × petal_count` (approximate)

**Radius Validation:**
- Min radius: `blade_diameter / 2`
- Safety margin: `(requested - min) / min × 100`
- Status: OK (>20%), WARN (5-20%), ERROR (<5%)

---

## Integration Points

### **CP-S50: Blade Registry**
```typescript
// Load blades
const blades = await fetch('/api/saw/blades').then(r => r.json())

// Display blade info
Kerf: {{ selectedBlade.kerf_mm }}mm
Min radius: {{ (selectedBlade.diameter_mm / 2).toFixed(1) }}mm
```

### **CP-S51: Validation**
```typescript
// Validate operation
const payload = {
  blade: selectedBlade,
  op_type: 'slice', // or 'batch', 'contour'
  material_family: 'hardwood',
  planned_rpm: 3600,
  planned_feed_ipm: 120,
  planned_doc_mm: 3.0
}
const result = await fetch('/api/saw/validate/operation', {
  method: 'POST',
  body: JSON.stringify(payload)
}).then(r => r.json())

// Display validation
validationResult.overall_result // 'OK', 'WARN', or 'ERROR'
validationResult.checks // { check_name: { result, message } }
```

### **CP-S52: Learned Overrides**
```typescript
// Merge learned parameters
const laneKey = {
  tool_id: selectedBladeId,
  material: 'hardwood',
  mode: 'slice',
  machine_profile: 'bcam_router_2030'
}
const baseline = { rpm: 3600, feed_ipm: 120, doc_mm: 3.0, safe_z: 5.0 }

const result = await fetch('/api/feeds/learned/merge', {
  method: 'POST',
  body: JSON.stringify({ lane_key: laneKey, baseline })
}).then(r => r.json())

// Apply merged params
rpm.value = result.merged.rpm
feedIpm.value = result.merged.feed_ipm
depthPerPass.value = result.merged.doc_mm
```

### **CP-S59B: Telemetry & JobLog**
```typescript
// Send to job log
const payload = {
  op_type: 'slice',
  machine_profile: 'bcam_router_2030',
  material_family: 'hardwood',
  blade_id: 'tenryu_gm-25560d_...',
  safe_z: 5.0,
  depth_passes: 4,
  total_length_mm: 600.0,
  planned_rpm: 3600,
  planned_feed_ipm: 120,
  planned_doc_mm: 3.0,
  operator_notes: 'Slice from (0,0) to (100,0)'
}

const run = await fetch('/api/saw/joblog/run', {
  method: 'POST',
  body: JSON.stringify(payload)
}).then(r => r.json())

// run.run_id for telemetry ingestion
```

---

## User Workflow

### **Typical Slice Operation:**
1. Select blade from registry → Displays kerf, diameter, teeth
2. Set machine profile and material → Enables learned override merging
3. Define cut geometry (start/end points) → SVG preview updates
4. Set depth parameters (total, per-pass) → Calculates passes
5. Click "Validate Parameters" → CP-S51 safety checks (6 checks)
6. Click "Apply Learned Overrides" → CP-S52 merges lane parameters
7. Review merged params (baseline → learned) → Shows scale factor
8. Click "Generate G-code" → Creates multi-pass NC program
9. Review G-code preview (20 lines + stats) → Verify moves
10. Click "Send to JobLog" → Creates run record in CP-S59B
11. **Execute operation** → Telemetry ingested automatically
12. **System learns** → Risk scores → Lane scale updates

### **Typical Batch Operation:**
1. Select blade → Same as slice
2. Configure batch (10 slices, 25mm spacing) → Stats grid updates
3. Validate → Check all slices are safe
4. Apply learned → Batch-level optimization
5. Generate → Multi-slice G-code (all passes)
6. Send to JobLog → Single run record for entire batch
7. Execute → System tracks batch completion

### **Typical Contour Operation:**
1. Select blade → Radius validation activates
2. Choose contour type (arc/circle/rosette) → Different params
3. Set radius/angles → Real-time SVG preview
4. Validate radius → Min radius check (blade_diameter/2)
5. Validate operation → Full safety checks
6. Apply learned → Curve-specific lane
7. Generate → Arc/G2/G3 commands
8. Send to JobLog → Contour run record

---

## Technical Details

### **SVG Preview System**
All panels include real-time SVG canvas with:
- Grid pattern for spatial reference
- Cut path visualization (blue)
- Kerf boundary lines (orange, dashed)
- Start/end markers (green/red circles)
- Radius indicators (purple, dashed)
- Numbered slice labels (batch panel)
- Dynamic viewBox calculation

**ViewBox calculation:**
```typescript
const padding = 20
const minX = Math.min(...allX) - padding
const minY = Math.min(...allY) - padding
const maxX = Math.max(...allX) + padding
const maxY = Math.max(...allY) + padding
return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`
```

### **G-code Generation**
Multi-pass strategy with safety moves:
```gcode
G21  ; Metric
G90  ; Absolute
G17  ; XY plane
(Metadata)

G0 Z5.0  ; Safe Z
G0 X0.0 Y0.0  ; Move to start

; Pass 1 (depth: 3mm)
G1 Z-3.0 F600  ; Plunge (feed/5)
G1 X100.0 Y0.0 F3048  ; Cut (120 IPM × 25.4)
G0 Z5.0  ; Retract

; Pass 2 (depth: 6mm)
G0 X0.0 Y0.0  ; Return
G1 Z-6.0 F600
G1 X100.0 Y0.0 F3048
G0 Z5.0

M30  ; End
```

### **Validation Display**
Three-tier color coding:
- **OK** (green): All checks passed
- **WARN** (yellow): Caution, but can proceed
- **ERROR** (red): Must fix before generating G-code

**Check items:**
- ✓ Contour radius check
- ✓ Depth of cut vs kerf
- ✓ RPM range (2000-6000)
- ✓ Feed rate range (10-300 IPM)
- ✓ Chipload validation
- ✓ Blade design ratio

---

## Installation

### **1. Copy components to client:**
```powershell
# Components already created at:
packages/client/src/components/saw_lab/SawSlicePanel.vue
packages/client/src/components/saw_lab/SawBatchPanel.vue
packages/client/src/components/saw_lab/SawContourPanel.vue
```

### **2. Register in router:**
```typescript
// packages/client/src/router/index.ts
{
  path: '/saw-lab/slice',
  name: 'SawSlice',
  component: () => import('@/components/saw_lab/SawSlicePanel.vue')
},
{
  path: '/saw-lab/batch',
  name: 'SawBatch',
  component: () => import('@/components/saw_lab/SawBatchPanel.vue')
},
{
  path: '/saw-lab/contour',
  name: 'SawContour',
  component: () => import('@/components/saw_lab/SawContourPanel.vue')
}
```

### **3. Add navigation menu:**
```vue
<nav>
  <RouterLink to="/saw-lab/slice">Slice</RouterLink>
  <RouterLink to="/saw-lab/batch">Batch</RouterLink>
  <RouterLink to="/saw-lab/contour">Contour</RouterLink>
</nav>
```

---

## API Dependency Summary

**All panels require these endpoints:**
- `GET /api/saw/blades` - Load blade registry (CP-S50)
- `POST /api/saw/validate/operation` - Validate parameters (CP-S51)
- `POST /api/saw/validate/contour` - Radius validation (CP-S51, contour only)
- `POST /api/feeds/learned/merge` - Merge learned params (CP-S52)
- `POST /api/saw/joblog/run` - Create run record (CP-S59B)

**Optional but recommended:**
- `POST /api/saw/telemetry/ingest` - Ingest telemetry (CP-S59B, auto-called after execution)
- `GET /api/saw/telemetry/risk_summary` - View learning progress

---

## Styling

**Consistent design system:**
- Primary color: `#3498db` (blue)
- Success color: `#27ae60` (green)
- Warning color: `#f39c12` (orange)
- Error color: `#e74c3c` (red)
- Background: `#f8f9fa` (light gray)
- Border: `#dee2e6` (medium gray)

**Layout:**
- Two-column grid (380-400px left, 1fr right)
- Form groups with 15px margin
- Actions column with 10px gap
- Preview sections with 20px margin-bottom

**Typography:**
- Headers: 16px, bold, colored underline
- Labels: 14px, medium weight
- Values: 14px, regular or bold (for emphasis)
- Code: 12px, Courier New monospace

---

## Testing Checklist

### **SawSlicePanel:**
- [ ] Load blades from registry
- [ ] Select blade → kerf info displayed
- [ ] Change start/end points → SVG updates
- [ ] Validate → all 6 checks shown
- [ ] Apply learned → params update (RPM/feed/DOC)
- [ ] Generate G-code → multi-pass program created
- [ ] Download G-code → file saved
- [ ] Send to JobLog → run ID returned

### **SawBatchPanel:**
- [ ] Configure 10 slices, 25mm spacing
- [ ] Stats grid shows correct totals
- [ ] SVG shows 10 numbered slices
- [ ] Validate → batch-level checks
- [ ] Generate → all slices in one program
- [ ] Send → batch run record created

### **SawContourPanel:**
- [ ] Select blade → min radius displayed
- [ ] Arc type → start/end angles work
- [ ] Circle type → full circle path
- [ ] Rosette type → petal pattern
- [ ] Radius validation → OK/WARN/ERROR status
- [ ] SVG shows radius indicator
- [ ] Generate → arc commands (G2/G3)
- [ ] Send → contour run record

---

## Next Steps

1. **Wire to main navigation** - Add Saw Lab menu item
2. **Test with real blades** - Import PDF blade specs via CP-S50
3. **Execute operations** - Send to machine controller
4. **Ingest telemetry** - Live learning from actual runs
5. **Monitor risk scores** - View learning progress dashboard
6. **Promote overrides** - Convert successful learnings to presets

---

## Completion Status

**✅ All 3 panels complete**  
**✅ Full integration with CP-S50, CP-S51, CP-S52, CP-S59B**  
**✅ Interactive SVG previews**  
**✅ G-code generation**  
**✅ JobLog integration**  
**✅ Learned parameter application**  
**✅ Validation display**  

**Total: ~2400 lines of production Vue 3 + TypeScript code**

---

## See Also

- [CP_S50_SAW_BLADE_REGISTRY.md](./CP_S50_SAW_BLADE_REGISTRY.md) - Blade CRUD
- [CP_S51_SAW_BLADE_VALIDATOR.md](./CP_S51_SAW_BLADE_VALIDATOR.md) - Safety checks
- [PATCH_L2_MERGED_SUMMARY.md](./PATCH_L2_MERGED_SUMMARY.md) - Learned overrides pattern
- [CNC_SAW_LAB_AUDIT.md](./CNC_SAW_LAB_AUDIT.md) - Original requirements
