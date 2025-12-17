# Batch Export Subset Upgrade - Implementation Summary

**Date:** November 5, 2025  
**Status:** ✅ **COMPLETE**  
**Upgrade:** Custom mode subsets for batch export (any combination of comment/inline_f/mcode)

---

## 🎯 What Changed

Upgraded the batch export system from "always export all 3 modes" to **"export any subset of modes"** selected by the user.

**Key Enhancements:**
- ✅ **API accepts `modes` parameter** - Optional list like `["comment","mcode"]`
- ✅ **Smart defaults** - If modes omitted or empty, falls back to all three
- ✅ **Client checkboxes** - Three checkboxes to select desired modes
- ✅ **Dynamic filename** - ZIP named by selected modes (e.g., `ToolBox_MultiMode_comment-mcode.zip`)
- ✅ **localStorage persistence** - Checkbox state persists across sessions
- ✅ **CI validation** - Automated test verifies subset exports work correctly

---

## 📦 API Changes

### **New Model: BatchExportIn**

**Location:** `services/api/app/routers/adaptive_router.py`

```python
# Allowed adaptive feed modes
ALLOWED_MODES = ("comment", "inline_f", "mcode")

class BatchExportIn(GcodeIn):
    """Extended GcodeIn with optional modes subset for batch export"""
    modes: Optional[List[str]] = Field(
        default=None, 
        description="Subset of modes to export (comment, inline_f, mcode)"
    )
```

**Backward Compatible:** Existing requests without `modes` field still work (defaults to all 3).

### **Updated Endpoint Logic**

```python
@router.post("/batch_export")
def batch_export(body: BatchExportIn):
    """
    Returns a ZIP with NC files for requested modes.
    If modes is omitted or empty, defaults to all three.
    """
    # Normalize modes - filter to allowed values
    modes = [m for m in (body.modes or []) if m in ALLOWED_MODES]
    if not modes:
        modes = list(ALLOWED_MODES)  # Fallback to all three
    
    # Build ZIP with requested modes only
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for m in modes:
            z.writestr(f"{stem}_{m}.nc", render_with_mode(m))
        
        # Manifest now includes modes list
        manifest = {
            "modes": modes,  # 🆕 Tracks which modes are in the ZIP
            "post": post_id,
            "units": body.units,
            # ... other fields
        }
        z.writestr(f"{stem}_manifest.json", json.dumps(manifest, indent=2))
```

**Key Changes:**
1. Filter input modes to only allowed values (`ALLOWED_MODES`)
2. Loop over `modes` list instead of hardcoded ["comment", "inline_f", "mcode"]
3. Add `modes` field to manifest for traceability

---

## 🎨 Client UI Changes

### **New State: exportModes**

**Location:** `packages/client/src/components/AdaptivePocketLab.vue`

```typescript
// Batch export mode selection state (localStorage persisted)
const exportModes = ref<{comment: boolean, inline_f: boolean, mcode: boolean}>(() => {
  try {
    return JSON.parse(localStorage.getItem('toolbox.af.modes') || '')
  } catch {
    return {comment: true, inline_f: true, mcode: true}  // Default: all checked
  }
})

// Auto-save to localStorage on change
watch(exportModes, () => {
  localStorage.setItem('toolbox.af.modes', JSON.stringify(exportModes.value))
}, { deep: true })
```

**Default Behavior:** All three checkboxes checked (exports all modes by default).

### **New Helper: selectedModes()**

```typescript
function selectedModes(): string[] {
  const sel: string[] = []
  if (exportModes.value.comment) sel.push('comment')
  if (exportModes.value.inline_f) sel.push('inline_f')
  if (exportModes.value.mcode) sel.push('mcode')
  return sel
}
```

### **Updated Template**

```vue
<div class="flex items-center gap-3 flex-wrap pt-2 border-t">
  <div class="flex items-center gap-2">
    <label class="text-sm font-medium">Export modes:</label>
    <label class="text-xs flex items-center gap-1">
      <input type="checkbox" v-model="exportModes.comment" class="w-3 h-3"/>
      comment
    </label>
    <label class="text-xs flex items-center gap-1">
      <input type="checkbox" v-model="exportModes.inline_f" class="w-3 h-3"/>
      inline_f
    </label>
    <label class="text-xs flex items-center gap-1">
      <input type="checkbox" v-model="exportModes.mcode" class="w-3 h-3"/>
      mcode
    </label>
  </div>
  <button class="px-3 py-1 border rounded bg-orange-50" 
    @click="batchExport" :disabled="!moves.length">
    Batch Export (subset ZIP)
  </button>
</div>
```

**Visual Flow:**
```
┌────────────────────────────────────────────────────┐
│ Export modes: ☑ comment  ☑ inline_f  ☐ mcode      │
│ [Batch Export (subset ZIP)]                        │
└────────────────────────────────────────────────────┘
```

### **Updated batchExport() Function**

```typescript
async function batchExport(){
  const body = buildBaseExportBody()
  body.post_id = postId.value
  body.modes = selectedModes()  // 🆕 Include selected modes
  
  try {
    const r = await fetch('/api/cam/pocket/adaptive/batch_export', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    })
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    
    // 🆕 Dynamic filename based on selected modes
    const modeLabel = selectedModes().join('-') || 'all'
    a.download = `ToolBox_MultiMode_${modeLabel}.zip`
    
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (err) {
    console.error('Batch export failed:', err)
    alert('Failed to batch export: ' + err)
  }
}
```

**Filename Examples:**
- All checked: `ToolBox_MultiMode_comment-inline_f-mcode.zip`
- Comment + mcode: `ToolBox_MultiMode_comment-mcode.zip`
- Inline_f only: `ToolBox_MultiMode_inline_f.zip`
- None checked (fallback): `ToolBox_MultiMode_all.zip`

---

## 🧪 CI Validation

### **New Test: Subset Export**

**Location:** `.github/workflows/adaptive_pocket.yml`

```yaml
- name: Batch ZIP with subset ["comment","mcode"]
  run: |
    python - <<'PY'
    import urllib.request, json, zipfile, io
    
    body = {
      "loops": [
        {"pts": [[0,0],[120,0],[120,80],[0,80]]},
        {"pts": [[40,20],[80,20],[80,60],[40,60]]}
      ],
      # ... other params
      "modes": ["comment", "mcode"]  # 🆕 Subset request
    }
    
    req = urllib.request.Request(
      "http://127.0.0.1:8000/cam/pocket/adaptive/batch_export",
      data=json.dumps(body).encode(),
      headers={"Content-Type": "application/json"}
    )
    
    data = urllib.request.urlopen(req).read()
    z = zipfile.ZipFile(io.BytesIO(data), 'r')
    names = sorted(z.namelist())
    
    # Verify only requested modes present
    assert any(n.endswith("_comment.nc") for n in names), "Missing comment.nc"
    assert any(n.endswith("_mcode.nc") for n in names), "Missing mcode.nc"
    assert not any(n.endswith("_inline_f.nc") for n in names), "inline_f.nc should NOT be present"
    
    # Verify manifest
    manifest = json.loads(z.read("..._manifest.json").decode())
    assert sorted(manifest["modes"]) == ["comment", "mcode"]
    
    print("✓ Subset batch export validated")
    print(f"  Files: {names}")
    PY
```

**Validates:**
- Only comment and mcode NC files in ZIP
- inline_f NC file correctly excluded
- Manifest `modes` field matches request
- ZIP structure valid

---

## 📊 Example Workflows

### **Workflow 1: Export Only Comment Mode**

**Use Case:** User only needs FEED_HINT comments (no active feed override).

```
1. User unchecks "inline_f" and "mcode"
2. Only "comment" checkbox remains checked
3. Clicks "Batch Export (subset ZIP)"
4. Downloads: ToolBox_MultiMode_comment.zip
5. ZIP contains:
   - pocket_<timestamp>_comment.nc
   - pocket_<timestamp>_manifest.json
   ✅ Smaller ZIP, faster download
```

### **Workflow 2: Export Comment + M-code (Skip Inline F)**

**Use Case:** User wants both annotation modes but not inline F overrides.

```
1. User checks "comment" and "mcode"
2. Unchecks "inline_f"
3. Clicks "Batch Export (subset ZIP)"
4. Downloads: ToolBox_MultiMode_comment-mcode.zip
5. ZIP contains:
   - pocket_<timestamp>_comment.nc (FEED_HINT comments)
   - pocket_<timestamp>_mcode.nc (M52 P wrappers)
   - pocket_<timestamp>_manifest.json
   ✅ Two variants for comparison, no inline F clutter
```

### **Workflow 3: Export All Three (Default)**

**Use Case:** User wants comprehensive comparison (same as before upgrade).

```
1. All three checkboxes checked (default state)
2. Clicks "Batch Export (subset ZIP)"
3. Downloads: ToolBox_MultiMode_comment-inline_f-mcode.zip
4. ZIP contains all 3 NC files + manifest
✅ Backward compatible behavior
```

### **Workflow 4: Persistent Preferences**

**Use Case:** User always wants comment + inline_f, never mcode.

```
1. User unchecks "mcode" checkbox
2. localStorage saves state: {comment: true, inline_f: true, mcode: false}
3. Refreshes page
4. Checkboxes restore to previous state (comment + inline_f checked)
5. Future exports automatically use saved preferences
✅ No need to reselect modes every time
```

---

## 🔍 Technical Details

### **Validation Logic**

**Input Filtering:**
```python
# Only allow valid modes
modes = [m for m in (body.modes or []) if m in ALLOWED_MODES]

# Fallback to all three if empty
if not modes:
    modes = list(ALLOWED_MODES)
```

**Edge Cases Handled:**
- `modes: null` → defaults to all three ✅
- `modes: []` → defaults to all three ✅
- `modes: ["comment", "invalid", "mcode"]` → filters to `["comment", "mcode"]` ✅
- `modes: ["GRBL"]` → ignored (not in ALLOWED_MODES), defaults to all three ✅

### **localStorage Schema**

**Key:** `toolbox.af.modes`

**Value:**
```json
{
  "comment": true,
  "inline_f": false,
  "mcode": true
}
```

**Read/Write:**
```typescript
// Read on mount
const exportModes = ref(() => {
  try {
    return JSON.parse(localStorage.getItem('toolbox.af.modes') || '')
  } catch {
    return {comment: true, inline_f: true, mcode: true}
  }
})

// Write on change
watch(exportModes, () => {
  localStorage.setItem('toolbox.af.modes', JSON.stringify(exportModes.value))
}, { deep: true })
```

### **Manifest Enhancement**

**Before:**
```json
{
  "post": "GRBL",
  "units": "mm",
  "tool_d": 6.0,
  "timestamp": 1699137600
}
```

**After:**
```json
{
  "modes": ["comment", "mcode"],  // 🆕 Tracks exported modes
  "post": "GRBL",
  "units": "mm",
  "tool_d": 6.0,
  "timestamp": 1699137600
}
```

**Benefit:** When opening old ZIPs, manifest documents which modes were exported.

---

## 📈 Benefits

### **For Users**
1. ✅ **Faster workflows** - Only export modes they need (smaller ZIPs, faster downloads)
2. ✅ **Reduced clutter** - Fewer NC files to sift through in CAM software
3. ✅ **Persistent preferences** - Set once, use forever (localStorage)
4. ✅ **Flexible testing** - Try different mode combinations without full re-export

### **For Developers**
1. ✅ **Backward compatible** - Existing code/scripts still work (defaults to all three)
2. ✅ **Input validated** - Invalid modes filtered out automatically
3. ✅ **CI validated** - Automated tests catch regressions
4. ✅ **Extensible** - Easy to add new modes in future (just add to `ALLOWED_MODES`)

### **For CAM Workflows**
1. ✅ **Focused comparison** - Only import modes relevant to target CNC
2. ✅ **Manifest documentation** - Always know which modes are in a ZIP
3. ✅ **Bandwidth savings** - Smaller ZIPs for remote/cloud workflows

---

## 🚀 Testing

### **Manual Testing**

**Test 1: Single Mode Export**
```powershell
# Start dev stack
cd packages/client && npm run dev

# In browser:
1. Uncheck "inline_f" and "mcode"
2. Only "comment" checked
3. Click "Batch Export (subset ZIP)"
4. Extract ZIP
5. Verify only pocket_*_comment.nc and manifest present
```

**Test 2: Two-Mode Combination**
```powershell
# In browser:
1. Check "comment" and "mcode"
2. Uncheck "inline_f"
3. Click "Batch Export (subset ZIP)"
4. Extract ZIP
5. Verify pocket_*_comment.nc and pocket_*_mcode.nc present
6. Verify NO pocket_*_inline_f.nc
```

**Test 3: localStorage Persistence**
```powershell
# In browser:
1. Uncheck "mcode"
2. Refresh page (F5)
3. Verify "mcode" still unchecked after reload
4. Check DevTools → Application → Local Storage
5. Verify toolbox.af.modes key exists
```

**Test 4: API Direct Call**
```powershell
# With API running
curl -X POST http://localhost:8000/cam/pocket/adaptive/batch_export `
  -H 'Content-Type: application/json' `
  -d '{
    "loops": [{"pts": [[0,0],[60,0],[60,40],[0,40]]}],
    "units": "mm",
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 1.5,
    "strategy": "Spiral",
    "post_id": "GRBL",
    "modes": ["comment", "inline_f"]
  }' `
  -o subset_test.zip

# Verify
unzip -l subset_test.zip  # Should show 2 NC files + manifest
unzip -p subset_test.zip pocket_*_manifest.json | jq .modes
# Output: ["comment", "inline_f"]
```

### **Automated CI Testing**

**Run CI Test:**
```powershell
# GitHub Actions will automatically test on push
git add .
git commit -m "feat: batch export subset mode selection"
git push

# Or run locally with API server
cd services/api
uvicorn app.main:app --port 8000 &

# In another terminal
python -c "exec(open('.github/workflows/adaptive_pocket.yml').read().split('Batch ZIP with subset')[1].split('PY')[1])"
```

**Expected Output:**
```
Fetching subset batch export ZIP (comment + mcode only)...
  ZIP contains 3 files:
    - pocket_1699137600_comment.nc
    - pocket_1699137600_mcode.nc
    - pocket_1699137600_manifest.json

✓ Subset batch export validated
  Requested modes: ['comment', 'mcode']
  Manifest modes: ['comment', 'mcode']
  Files: ['pocket_1699137600_comment.nc', 'pocket_1699137600_manifest.json', 'pocket_1699137600_mcode.nc']
```

---

## 🔄 Upgrade Path

### **Existing Users**

**No Breaking Changes:**
- Old code that doesn't send `modes` parameter still works (defaults to all three)
- Existing ZIPs remain valid (no manifest format changes, just added `modes` field)
- UI defaults to all checkboxes checked (same as old "Batch Export (3 modes)" behavior)

**Migration Steps:**
1. Pull latest code
2. Restart API server (new BatchExportIn model)
3. Refresh client (new checkbox UI)
4. (Optional) Uncheck modes you don't need
5. Export as usual

**Rollback:**
- If needed, simply check all three checkboxes to restore old behavior
- Or omit `modes` parameter in API calls

---

## 📚 See Also

- [Batch Export Summary](./BATCH_EXPORT_SUMMARY.md) - Original batch export system (Phase 10)
- [Adaptive Feed Override Complete](./ADAPTIVE_FEED_OVERRIDE_COMPLETE.md) - Per-export mode override
- [Phase 8 Summary](./PHASE_8_ADAPTIVE_OVERRIDE_SUMMARY.md) - Adaptive feed implementation
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md) - Core CAM system

---

## 📊 Implementation Stats

| Component | LOC Changed | Type |
|-----------|-------------|------|
| adaptive_router.py | ~20 | Modified (BatchExportIn model, loop logic) |
| AdaptivePocketLab.vue | ~40 | Added (exportModes state, UI checkboxes, selectedModes helper) |
| adaptive_pocket.yml | ~60 | Added (CI subset test) |
| **Total** | **~120** | **Non-breaking enhancement** |

---

**Status:** ✅ **Production Ready**  
**Backward Compatible:** Yes (defaults to all modes if omitted)  
**User Impact:** Positive (more flexibility, faster workflows)  
**Next Steps:** Monitor user feedback on most-used mode combinations
