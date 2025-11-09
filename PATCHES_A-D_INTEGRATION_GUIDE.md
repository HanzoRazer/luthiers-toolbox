# Patches A-D Integration - Complete Documentation

## Overview
This document details the complete integration of Patches A, B, C, and D into the Luthier's Tool Box repository.

---

## ✅ Patch A: Server Export History + DXF Stamping

### Files Created/Modified

#### ✅ `server/env_cfg.py` (NEW)
**Purpose**: Environment configuration management  
**Environment Variables**:
- `EXPORTS_ROOT` - Export history storage directory (default: `./exports/logs`)
- `UNITS` - Default units (`in` or `mm`, default: `in`)
- `TOOLBOX_VERSION` - Version string for DXF comments (default: `ToolBox MVP`)
- `GIT_SHA` - Git commit SHA for traceability (default: `unknown`)

#### ✅ `server/history_store.py` (NEW)
**Purpose**: Export history management  
**Key Functions**:
- `start_entry(kind, meta)` - Create new export entry with UUID
- `write_file(entry, name, data)` - Save file to export directory
- `write_text(entry, name, text)` - Save text file
- `finalize(entry, extra_meta)` - Update metadata on completion
- `list_entries(limit)` - List recent exports (newest first)
- `read_meta(entry_id)` - Get metadata for specific export
- `file_bytes(entry_id, filename)` - Retrieve file from history

**Directory Structure**:
```
exports/logs/
  2025-11-04/
    {uuid}/
      meta.json       # Export metadata
      polyline.dxf    # DXF file
      summary.json    # Detailed geometry summary
      *.md            # Markdown reports (optional)
```

#### ✅ `server/dxf_exports_router.py` (ENHANCED)
**New Imports**:
```python
from .history_store import start_entry, write_file, write_text, finalize, list_entries, read_meta, file_bytes
from .env_cfg import get_units, get_version, get_git_sha
```

**New Helper Functions**:
- `_utc_now_iso()` - Generate ISO 8601 UTC timestamp
- `_comment_stamp(extra)` - Generate DXF comment header with version, Git SHA, timestamp, units

**Enhanced Endpoints**:

1. **POST /exports/polyline_dxf**
   - Now saves to history with UUID
   - Adds DXF comment stamp (999 group code)
   - Returns `X-Export-Id` header with entry UUID
   - Saves `summary.json` with geometry details

2. **POST /exports/biarc_dxf**
   - Now saves to history with UUID
   - Adds DXF comment with arc statistics
   - Returns `X-Export-Id` header
   - Saves `summary.json` with arc/line counts, min/max radii

3. **GET /exports/history?limit=50** (NEW)
   - List recent export entries
   - Sorted newest first
   - Returns: `{items: [{id, kind, created_utc, ...}]}`

4. **GET /exports/history/{entry_id}** (NEW)
   - Get metadata for specific export
   - Returns full metadata dict

5. **GET /exports/history/{entry_id}/file/{filename}** (NEW)
   - Download specific file from export
   - Auto-detects media type (.dxf, .json, .md, .svg)

#### ✅ `server/dxf_helpers.py` (ENHANCED)
**Modified Functions**:
- `_ascii_r12_header(comment)` - Now accepts optional comment parameter
- `build_ascii_r12(entities, comment)` - Embeds comment in DXF header (999 group code)
- `try_build_with_ezdxf(entities)` - Extracts comment from entity params and adds to header

**DXF Comment Format**:
```
999
# ToolBox MVP | # Git: abc123 | # UTC: 2025-11-04T12:00:00Z | # Units: in | # POLYLINE VERTS=42
```

### Testing

#### Manual Test:
```bash
# Export polyline
curl -X POST http://localhost:8000/exports/polyline_dxf \
  -H "Content-Type: application/json" \
  -d '{"polyline":{"points":[[0,0],[100,0],[100,50]]},"layer":"TEST"}' \
  -D headers.txt -o test.dxf

# Check export ID
cat headers.txt | grep X-Export-Id

# List history
curl http://localhost:8000/exports/history?limit=5 | jq

# Get specific export
EXPORT_ID="<uuid-from-headers>"
curl http://localhost:8000/exports/history/$EXPORT_ID | jq

# Download file
curl http://localhost:8000/exports/history/$EXPORT_ID/file/summary.json | jq
```

#### Verify DXF Stamp:
```bash
head -30 test.dxf | grep -A 1 "999"
```

Expected output:
```
999
# ToolBox MVP | # Git: unknown | # UTC: 2025-11-04T12:00:00Z | # Units: in | # POLYLINE VERTS=3
```

---

## ✅ Patch B: CI Workflows

### Files Created/Modified

#### ✅ `ci/devserver.py` (NEW)
**Purpose**: Minimal dev server for CI/CD testing  
**Features**:
- Auto-discovers existing app (`main:app`, `app.main:app`, etc.)
- Falls back to minimal test server
- Auto-includes DXF and SVG routers
- Configurable via `SERVER_PORT` and `SERVER_HOST` env vars

**Usage**:
```bash
python -m ci.devserver
# or
SERVER_PORT=8080 python -m ci.devserver
```

#### ✅ `ci/wait_for_server.sh` (NEW)
**Purpose**: Wait for server to become responsive  
**Usage**:
```bash
bash ci/wait_for_server.sh http://127.0.0.1:8000/exports/dxf/health
```

**Features**:
- Max 30 attempts (30 seconds)
- Exits 0 on success, 1 on failure
- Progress logging

#### ✅ `.github/workflows/api_dxf_tests.yml` (ENHANCED)
**New Tests**:
1. **Verify DXF Comment Stamp**
   ```bash
   grep -E "999|POLYLINE|ToolBox" test_polyline.dxf
   ```

2. **Verify Export History Header**
   ```bash
   grep "X-Export-Id:" polyline_headers.txt
   ```

3. **Test Export History Endpoints** (NEW STEP)
   ```bash
   # List history
   curl http://localhost:8000/exports/history?limit=5 -o history.json
   
   # Verify history available
   cat history.json | jq '.items | length'
   
   # Retrieve first export
   FIRST_ID=$(cat history.json | jq -r '.items[0].id')
   curl http://localhost:8000/exports/history/$FIRST_ID
   ```

#### ✅ `.github/workflows/client_smoke.yml` (ENHANCED)
**Improved Script Detection**:
```yaml
- name: Lint (if present)
  run: |
    if jq -e '.scripts.lint' package.json >/dev/null 2>&1; then
      npm run lint
    else
      echo "⚠ No lint script found"
    fi
```

Similar improvements for `typecheck` and `type-check` detection.

---

## 🔄 Patch C: Client QoL (Requires Manual Integration)

### Features to Add to `client/src/components/CurveLab.vue`

#### 1. Units Toggle (in/mm)
**Location**: Top toolbar  
**Implementation**:
```vue
<div class="ml-auto flex items-center gap-2">
  <label class="text-xs">Units</label>
  <select v-model="units" @change="persistSettings" class="border rounded p-1 text-xs">
    <option value="in">in</option>
    <option value="mm">mm</option>
  </select>
</div>
```

**Script**:
```typescript
const units = ref<'in'|'mm'>( (localStorage.getItem('tb_units') as 'in'|'mm') || 'in' )

function persistSettings(){
  localStorage.setItem('tb_units', units.value)
  localStorage.setItem('tb_overlay', showBiarcOverlay.value ? '1' : '0')
}

// Load overlay setting on mount
const overlayStored = localStorage.getItem('tb_overlay')
if (overlayStored !== null) showBiarcOverlay.value = overlayStored === '1'
```

#### 2. Copy Markdown Button
**Location**: Preflight modal  
**Implementation**:
```vue
<button class="border px-3 py-1.5 rounded" @click="copyMarkdown">
  Copy Markdown
</button>
```

**Script**:
```typescript
async function copyMarkdown(){
  try {
    await navigator.clipboard.writeText(toMarkdown())
    alert('Markdown copied to clipboard')
  } catch (e) {
    console.warn('Clipboard copy failed, downloading instead')
    downloadMarkdownReport()
  }
}
```

#### 3. Keyboard Hotkeys
**Keys**:
- `M` - Download Markdown report (when preflight modal open)
- `J` - Download JSON summary (when preflight modal open)
- `E` - Export DXF (when preflight modal open)
- `O` - Toggle bi-arc overlay

**Implementation**:
```typescript
window.addEventListener('keydown', (e)=>{
  if (e.key === 'Shift') cvShiftDown.value = true
  if (e.key.toLowerCase() === 'o') {
    showBiarcOverlay.value = !showBiarcOverlay.value
    persistSettings()
  }
  if (e.key.toLowerCase() === 'm' && showPreflight.value) downloadMarkdownReport()
  if (e.key.toLowerCase() === 'j' && showPreflight.value) downloadJSONSummary()
  if (e.key.toLowerCase() === 'e' && showPreflight.value){
    if (preflightMode.value==='poly') confirmExportPolyline()
    else confirmExportBiarc()
  }
})
```

#### 4. Markdown Generation with Units
**Function**:
```typescript
function toMarkdown(): string {
  const ts = new Date().toISOString()
  let md = `# ToolBox DXF Preflight Report\n\n`
  md += `**Timestamp:** ${ts}\n\n`
  md += `**Mode:** ${preflightMode.value==='poly' ? 'Polyline' : 'Bi-arc'}\n\n`
  md += `**Units:** ${units.value}\n\n`
  // ... format points/arcs with unit conversion
}
```

#### 5. JSON Summary with Units
**Function**:
```typescript
function downloadJSONSummary(){
  const payload:any = {
    mode: preflightMode.value,
    timestamp: new Date().toISOString(),
    units: units.value,
  }
  // ... include geometry with unit conversion
}
```

#### 6. Enhanced Preflight Modal
**Additions**:
- Copy Markdown button
- Download JSON button
- Download Markdown button
- Keyboard shortcuts hint: `Tip: J=JSON, M=Markdown, O=Overlay`

### Status Badge Color Coding
```typescript
computed: {
  biarcStatusClass(): string {
    const s = this.biarcStatus
    if (!s) return 'bg-slate-100 text-slate-700'
    if (s.includes('2 arcs')) return 'bg-emerald-100 text-emerald-700'
    if (s.includes('1 arc')) return 'bg-amber-100 text-amber-800'
    return 'bg-rose-100 text-rose-700'
  }
}
```

---

## 🔄 Patch D: SVG Export + Layers + Tolerance (Requires Integration)

### Server Files to Create

#### 📄 `server/svg_helpers.py` (NEW)
**Key Functions**:
```python
def write_polyline_svg(points, layers, units, meta) -> str:
    # Generate SVG with polyline path
    # Include <desc> metadata
    # CSS styling for layers

def write_biarc_svg(entities, layers, units, meta) -> str:
    # Generate SVG with arc paths
    # Convert DXF arcs to SVG arc format
    # Include center markers overlay
```

**SVG Structure**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
  <desc>ToolBox SVG Export — polyline verts=10, units=in</desc>
  <style>
    .curve { fill:none; stroke:#111; stroke-width:1; }
    .arc { fill:none; stroke:#0a0; stroke-width:1; }
    .center { fill:none; stroke:#888; stroke-dasharray:4 4; }
  </style>
  <g id="CURVE">
    <path class="curve" d="M 0 0 L 100 0 L 100 50"/>
  </g>
  <g id="CENTER">
    <circle cx="50" cy="25" r="2" class="center"/>
  </g>
</svg>
```

#### 📄 `server/svg_exports_router.py` (NEW)
**Endpoint**:
```python
@router.post("/svg")
def export_svg(req: Dict[str, Any]):
    # Detect polyline vs biarc mode
    # Generate SVG
    # Save to history
    # Return SVG file
```

**Request Format**:
```json
{
  "polyline": {"points": [[0,0], [100,0]]},
  "layers": {
    "CURVE": "CURVE",
    "ARC": "ARC",
    "CENTER": "CENTER",
    "ANNOTATION": "ANNOTATION"
  }
}
```

**OR**:
```json
{
  "arcs": [
    {"type": "arc", "center": [50,50], "radius": 25, "start_angle": 0, "end_angle": 90},
    {"type": "line", "A": [0,0], "B": [100,0]}
  ],
  "layers": {...}
}
```

### Client Features to Add

#### Settings Drawer (⚙️ icon)
**Location**: Top toolbar  
**Implementation**:
```vue
<button @click="showSettings = !showSettings" title="Settings">⚙️</button>

<!-- Settings Drawer -->
<div v-if="showSettings" class="fixed inset-y-0 right-0 w-80 bg-white shadow-xl z-50">
  <div class="p-4 space-y-4">
    <h4 class="font-semibold">Settings</h4>
    
    <!-- Layer Names -->
    <div class="space-y-2">
      <label class="text-xs">Layer: CURVE <input v-model="layers.CURVE"/></label>
      <label class="text-xs">Layer: ARC <input v-model="layers.ARC"/></label>
      <label class="text-xs">Layer: CENTER <input v-model="layers.CENTER"/></label>
      <label class="text-xs">Layer: ANNOTATION <input v-model="layers.ANNOTATION"/></label>
    </div>
    
    <!-- Tolerance -->
    <label class="text-xs">
      Tolerance (mm) <input type="number" v-model.number="tolerance" step="0.01"/>
    </label>
    
    <!-- Units (already in Patch C) -->
    <label class="text-xs">
      Units <select v-model="units"><option>in</option><option>mm</option></select>
    </label>
  </div>
</div>
```

**Persistence**:
```typescript
const layers = ref({
  CURVE: localStorage.getItem('tb_layer_curve') || 'CURVE',
  ARC: localStorage.getItem('tb_layer_arc') || 'ARC',
  CENTER: localStorage.getItem('tb_layer_center') || 'CENTER',
  ANNOTATION: localStorage.getItem('tb_layer_annotation') || 'ANNOTATION'
})
const tolerance = ref(parseFloat(localStorage.getItem('tb_tolerance') || '0.12'))

function persistSettings(){
  localStorage.setItem('tb_layer_curve', layers.value.CURVE)
  localStorage.setItem('tb_layer_arc', layers.value.ARC)
  localStorage.setItem('tb_layer_center', layers.value.CENTER)
  localStorage.setItem('tb_layer_annotation', layers.value.ANNOTATION)
  localStorage.setItem('tb_tolerance', tolerance.value.toString())
  localStorage.setItem('tb_units', units.value)
}
```

#### SVG Preview in Preflight Modal
**Implementation**:
```vue
<div class="mt-3 border rounded p-2 bg-slate-50">
  <div class="text-xs mb-1">SVG Preview:</div>
  <iframe
    :srcdoc="svgPreviewData"
    class="w-full h-48 border rounded bg-white"
    sandbox="allow-same-origin"
  ></iframe>
</div>
```

**Script**:
```typescript
const svgPreviewData = ref<string>('')

async function openPreflight(mode: 'poly'|'biarc'){
  preflightMode.value = mode
  showPreflight.value = true
  
  // Generate SVG preview
  const payload = mode === 'poly' 
    ? { polyline: { points: pts.value.map(p=>[p.x, p.y]) }, layers: layers.value }
    : { arcs: lastBiarc.value, layers: layers.value }
  
  try {
    const resp = await fetch('/exports/svg', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    })
    svgPreviewData.value = await resp.text()
  } catch (e) {
    console.warn('SVG preview failed:', e)
  }
}
```

#### Download SVG Button
**Location**: Preflight modal  
**Implementation**:
```vue
<button class="border px-3 py-1.5 rounded" @click="downloadSVG">
  Download SVG
</button>
```

**Script**:
```typescript
async function downloadSVG(){
  const payload = preflightMode.value === 'poly' 
    ? { polyline: { points: pts.value.map(p=>[p.x, p.y]) }, layers: layers.value }
    : { arcs: lastBiarc.value, layers: layers.value }
  
  const resp = await fetch('/exports/svg', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  })
  
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = preflightMode.value === 'poly' ? 'polyline.svg' : 'biarc.svg'
  a.click()
  URL.revokeObjectURL(url)
}
```

### Testing

#### Test SVG Export (curl):
```bash
# Polyline SVG
curl -X POST http://localhost:8000/exports/svg \
  -H "Content-Type: application/json" \
  -d '{"polyline":{"points":[[0,0],[100,0],[100,50]]},"layers":{"CURVE":"CURVE"}}' \
  -o test_poly.svg

# Bi-arc SVG
curl -X POST http://localhost:8000/exports/svg \
  -H "Content-Type: application/json" \
  -d '{"arcs":[{"type":"arc","center":[80,20],"radius":30,"start_angle":180,"end_angle":270}]}' \
  -o test_biarc.svg

# Open in browser
firefox test_poly.svg
```

---

## Integration Summary

### ✅ Completed (Server-Side)
- [x] Patch A: Export history system
- [x] Patch A: DXF comment stamping
- [x] Patch A: History API endpoints
- [x] Patch B: CI dev server
- [x] Patch B: Enhanced GitHub Actions

### 🔄 Manual Integration Required (Client-Side)
- [ ] Patch C: Units toggle (in/mm)
- [ ] Patch C: Sticky settings (localStorage)
- [ ] Patch C: Copy Markdown button
- [ ] Patch C: Keyboard hotkeys (M/J/E/O)
- [ ] Patch C: Status badge color coding
- [ ] Patch D: Settings drawer (layers, tolerance)
- [ ] Patch D: SVG preview in preflight
- [ ] Patch D: Download SVG button

### 📋 Next Steps

1. **Test Server Integration**:
   ```bash
   cd server
   python -m ci.devserver
   
   # In another terminal:
   curl http://localhost:8000/exports/dxf/health
   curl http://localhost:8000/exports/history?limit=5
   ```

2. **Update CurveLab.vue**:
   - Add units toggle and persistence
   - Add keyboard hotkeys
   - Add Copy Markdown button
   - Add settings drawer for layers/tolerance
   - Add SVG preview to preflight modal

3. **Create SVG Server Files**:
   ```bash
   # Copy from patches:
   cp ToolBox_PatchD_SVG_Layers_Tolerance_Preview/patch_d_svg_layer_tol_preview/server/svg_helpers.py server/
   cp ToolBox_PatchD_SVG_Layers_Tolerance_Preview/patch_d_svg_layer_tol_preview/server/svg_exports_router.py server/
   ```

4. **Wire SVG Router**:
   ```python
   # In server/app.py or main app file:
   from server.svg_exports_router import router as svg_router
   app.include_router(svg_router)
   ```

5. **Run Tests**:
   ```bash
   # CI tests
   .github/workflows/api_dxf_tests.yml
   
   # Manual tests
   pytest server/tests/test_curvemath_dxf.py -v
   ```

---

## Environment Variables Reference

### Required for Production
```bash
# Export history
export EXPORTS_ROOT="/var/lib/toolbox/exports"

# Metadata stamping
export TOOLBOX_VERSION="ToolBox v1.0.0"
export GIT_SHA="$(git rev-parse --short HEAD)"
export UNITS="in"

# Server
export SERVER_PORT="8000"
export SERVER_HOST="0.0.0.0"
```

### Optional for Development
```bash
# Use defaults
# EXPORTS_ROOT → ./exports/logs
# TOOLBOX_VERSION → ToolBox MVP
# GIT_SHA → unknown
# UNITS → in
```

---

## API Endpoints Reference

### Export Endpoints
- `POST /exports/polyline_dxf` - Export polyline to DXF
- `POST /exports/biarc_dxf` - Export bi-arc to DXF
- `POST /exports/svg` - Export to SVG (Patch D)

### History Endpoints (Patch A)
- `GET /exports/history?limit=50` - List recent exports
- `GET /exports/history/{id}` - Get export metadata
- `GET /exports/history/{id}/file/{filename}` - Download file

### Health Endpoints
- `GET /exports/dxf/health` - Check DXF capabilities
- `GET /health` - General health check

---

## File Locations

### Server Files (✅ Integrated)
```
server/
  env_cfg.py              ← NEW (Patch A)
  history_store.py        ← NEW (Patch A)
  dxf_exports_router.py   ← ENHANCED (Patch A)
  dxf_helpers.py          ← ENHANCED (Patch A)
  svg_helpers.py          ← TODO (Patch D)
  svg_exports_router.py   ← TODO (Patch D)

ci/
  devserver.py            ← NEW (Patch B)
  wait_for_server.sh      ← NEW (Patch B)

.github/workflows/
  api_dxf_tests.yml       ← ENHANCED (Patch B)
  client_smoke.yml        ← ENHANCED (Patch B)
```

### Client Files (🔄 Manual Integration)
```
client/src/components/
  CurveLab.vue            ← TODO (Patches C & D)
```

---

## Troubleshooting

### Export History Not Working
**Symptom**: No X-Export-Id header, history endpoints 404  
**Fix**:
```bash
# Ensure history_store is imported
grep "from .history_store import" server/dxf_exports_router.py

# Verify EXPORTS_ROOT directory
ls -la exports/logs/
```

### DXF Comments Not Appearing
**Symptom**: No 999 group code in DXF files  
**Fix**:
```bash
# Check comment generation
grep "_comment_stamp" server/dxf_exports_router.py

# Verify comment in output
head -30 test.dxf | grep -A 1 "999"
```

### CI Server Won't Start
**Symptom**: `python -m ci.devserver` fails  
**Fix**:
```bash
# Check imports
cd server
python -c "from dxf_exports_router import router"

# Verify dependencies
pip install fastapi uvicorn pydantic ezdxf
```

---

## Version History

- **v1.0** - Initial integration of Patches A & B (server-side complete)
- **v1.1** - Client-side integration (Patches C & D) - IN PROGRESS

---

**Last Updated**: November 4, 2025  
**Integration Status**: Server-side complete ✅ | Client-side pending 🔄
