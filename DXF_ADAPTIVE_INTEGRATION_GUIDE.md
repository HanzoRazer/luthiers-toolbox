# 🚀 DXF → Adaptive Integration Guide

**Status:** Architecture Analysis Complete  
**Date:** November 8, 2025  
**Context:** Adapting external code proposal to Luthier's Tool Box existing architecture

---

## 📋 Current State Analysis

### ✅ What You Already Have

**Backend (services/api/):**
1. ✅ **blueprint_cam_bridge.py** - Already has DXF → Adaptive integration
   - Endpoint: `POST /cam/blueprint/to-adaptive`
   - Function: `extract_loops_from_dxf()` - Extracts LWPOLYLINE loops
   - Function: Already calls `plan_adaptive_l1()` from adaptive_core_l1.py
   - Returns: Loops + toolpath moves + stats

2. ✅ **dxf_preflight.py** - DXF validation (Phase 3.2)
   - Endpoint: `POST /cam/blueprint/preflight`
   - Returns: Issue list + HTML report

3. ✅ **adaptive_router.py** - Core adaptive pocketing (Module L.3)
   - Endpoint: `POST /api/cam/pocket/adaptive/plan`
   - Accepts: Loops JSON directly

**Frontend (packages/client/):**
1. ✅ **PipelineLab.vue** - Full DXF workflow (913 lines)
   - Stage 1: DXF upload
   - Stage 2: Preflight validation
   - Stage 3: Contour reconstruction (optional)
   - Stage 4: Adaptive pocket generation

2. ✅ **AdaptiveKernelLab.vue** - Adaptive parameter testing (704 lines)
   - Manual loops JSON editor
   - Full L.3 parameters (trochoids, jerk-aware, curvature)
   - Toolpath preview
   - Pipeline snippet export

---

## 🎯 What's Missing (From Your Proposal)

### Proposed Code Analysis

Your code suggests:
```
Backend:  server/routers/dxf_plan_router.py  ❌ Different path structure
Function: dxf_bytes_to_adaptive_plan_request  ❌ Not in codebase
Function: preflight_dxf_bytes                 ❌ Different API

Frontend: client/src/views/AdaptiveLabView.vue  ❌ Duplicate of AdaptiveKernelLab
```

**Reality Check:**
- Your code is from a **different project** (uses `server/` not `services/api/`)
- Luthier's Tool Box **already has this functionality** but in different locations
- **No duplication needed** - just wire existing components together

---

## 🔌 Integration Plan (Minimal Changes)

### Option A: Enhance AdaptiveKernelLab with DXF Import ⭐ RECOMMENDED

**Goal:** Add DXF upload button to AdaptiveKernelLab that populates loops JSON

**Changes Required:** ~100 lines in AdaptiveKernelLab.vue

**What It Does:**
1. User uploads DXF file
2. Frontend calls existing `/cam/blueprint/to-adaptive` endpoint
3. Response contains `loops` array
4. Auto-populate `loopsText` ref with loops JSON
5. User adjusts parameters if needed
6. Clicks "Run Adaptive" (existing flow)

**Benefits:**
- ✅ Zero backend changes (uses existing endpoint)
- ✅ Leverages Phase 3.2 work (blueprint_cam_bridge.py)
- ✅ Simple UI enhancement (file input + fetch call)
- ✅ No code duplication

---

### Option B: Create Simplified /cam/plan_from_dxf Endpoint

**Goal:** New endpoint that returns **just loops** (no toolpath generation)

**Use Case:** When you want loops extraction separate from planning

**Implementation:**

```python
# services/api/app/routers/blueprint_cam_bridge.py

@router.post("/extract-loops")
async def extract_loops(
    file: UploadFile = File(...),
    layer_name: str = "GEOMETRY"
):
    """
    Extract loops from DXF without running adaptive planner.
    Returns just the geometry for manual planning.
    """
    dxf_bytes = await file.read()
    loops, warnings = extract_loops_from_dxf(dxf_bytes, layer_name)
    
    return {
        "loops": [{"pts": loop.pts} for loop in loops],
        "warnings": warnings,
        "layer_name": layer_name,
        "loops_count": len(loops)
    }
```

**Benefits:**
- ✅ Lightweight (no toolpath computation)
- ✅ Fast response
- ✅ Useful for debugging DXF geometry

---

## 🛠️ Recommended Implementation (Option A)

### Step 1: Add DXF Import to AdaptiveKernelLab.vue

**Location:** `packages/client/src/views/AdaptiveKernelLab.vue`

**Changes:**

```vue
<script setup lang="ts">
// ... existing imports ...

// NEW: DXF import state
const dxfFile = ref<File | null>(null);
const dxfImporting = ref(false);
const dxfError = ref<string | null>(null);

// NEW: Handle DXF file selection
function onDxfFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  dxfFile.value = input.files?.[0] || null;
  dxfError.value = null;
}

// NEW: Import DXF → populate loops
async function importDxfToLoops() {
  if (!dxfFile.value) return;
  
  dxfImporting.value = true;
  dxfError.value = null;
  
  try {
    const formData = new FormData();
    formData.append('file', dxfFile.value);
    formData.append('layer_name', 'GEOMETRY'); // Or make configurable
    formData.append('tool_d', String(toolD.value));
    formData.append('stepover', String(stepover.value));
    formData.append('stepdown', String(stepdown.value));
    formData.append('margin', String(margin.value));
    formData.append('strategy', strategy.value);
    formData.append('feed_xy', String(feedXY.value));
    formData.append('safe_z', String(safeZ.value));
    formData.append('z_rough', String(zRough.value));
    
    const response = await fetch('/cam/blueprint/to-adaptive', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }
    
    const data = await response.json();
    
    // Populate loops text area
    loopsText.value = JSON.stringify(data.loops, null, 2);
    
    // Show success message
    errorMsg.value = null;
    alert(`✅ Imported ${data.loops_extracted} loops from DXF`);
    
  } catch (e: any) {
    dxfError.value = e?.message || String(e);
  } finally {
    dxfImporting.value = false;
  }
}
</script>

<template>
  <div class="adaptive-kernel-lab">
    <!-- NEW: DXF Import Section (add before loops editor) -->
    <div class="card">
      <div class="card-header">
        <h3>📁 Import DXF → Loops</h3>
      </div>
      <div class="card-body">
        <div class="form-group">
          <label>DXF File:</label>
          <input 
            type="file" 
            accept=".dxf" 
            @change="onDxfFileChange"
            :disabled="dxfImporting"
          />
        </div>
        
        <div v-if="dxfFile" class="file-selected">
          <span>📄 {{ dxfFile.name }}</span>
          <button 
            @click="importDxfToLoops" 
            class="btn btn-primary"
            :disabled="dxfImporting"
          >
            {{ dxfImporting ? '⏳ Importing...' : '🔄 Import → Loops JSON' }}
          </button>
        </div>
        
        <div v-if="dxfError" class="alert alert-error">
          {{ dxfError }}
        </div>
        
        <div class="help-text">
          <p>💡 This will extract closed LWPOLYLINE loops from your DXF.</p>
          <p>First loop = outer boundary, additional loops = islands/holes.</p>
        </div>
      </div>
    </div>
    
    <!-- Existing loops editor below... -->
  </div>
</template>
```

### Step 2: Test the Integration

```powershell
# Start API server
cd services/api
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000

# Start client (separate terminal)
cd packages/client
npm run dev

# Open browser
# Navigate to: http://localhost:5173/adaptive-kernel-lab
# (Or wherever AdaptiveKernelLab is routed)
```

**Test Flow:**
1. Click "Choose File" → Select DXF
2. Click "Import → Loops JSON"
3. Verify loops appear in text area
4. Adjust tool parameters if needed
5. Click "Run Adaptive" (existing button)
6. View toolpath in preview

---

## 📊 Comparison: Your Code vs Existing

| Feature | Your Proposal | Luthier's Tool Box (Existing) |
|---------|---------------|-------------------------------|
| **Backend Path** | `server/routers/` | `services/api/app/routers/` |
| **DXF → Loops** | `dxf_bytes_to_adaptive_plan_request()` | `extract_loops_from_dxf()` ✅ Already exists |
| **Preflight** | `preflight_dxf_bytes()` | `DXFPreflight` class ✅ Already exists |
| **Adaptive Endpoint** | `/cam/plan_from_dxf` | `/cam/blueprint/to-adaptive` ✅ Already exists |
| **Frontend View** | `AdaptiveLabView.vue` (new) | `AdaptiveKernelLab.vue` ✅ Already exists |
| **Pipeline View** | `PipelineLabView.vue` (new) | `PipelineLab.vue` ✅ Already exists |

**Conclusion:** Your proposal is **100% redundant** with existing code. Just need to **wire AdaptiveKernelLab to existing backend**.

---

## 🎯 Action Items

### Immediate (Today) - Option A Implementation
- [ ] Add DXF file input to AdaptiveKernelLab.vue (~50 lines)
- [ ] Add `importDxfToLoops()` function (~30 lines)
- [ ] Test with Gibson L-00 DXF
- [ ] Verify loops populate correctly
- [ ] Run adaptive kernel with imported loops

### Optional (Future) - Option B Simplified Endpoint
- [ ] Add `/cam/blueprint/extract-loops` endpoint (~20 lines)
- [ ] Returns loops only (no toolpath computation)
- [ ] Useful for debugging geometry extraction

### Documentation
- [ ] Update AdaptiveKernelLab.vue component docs
- [ ] Add DXF import section to ADAPTIVE_POCKETING_MODULE_L.md
- [ ] Create video demo of DXF → Adaptive workflow

---

## 💡 Key Insights

**What You Asked For:**
> "Backend: /cam/plan_from_dxf → DXF → Adaptive Plan (loops JSON)"
> "Frontend: /lab/adaptive → Adaptive Lab with DXF import + backplot"

**What You Actually Have:**
- ✅ Backend: `/cam/blueprint/to-adaptive` (already does this)
- ✅ Frontend: `AdaptiveKernelLab.vue` (already has backplot)
- ⚠️ **Missing:** DXF import UI in AdaptiveKernelLab

**Solution:** Add ~80 lines to AdaptiveKernelLab.vue to wire existing backend endpoint.

---

## 🚀 Quick Start (Copy-Paste Ready)

See implementation code in **Step 1** above. This is the **minimum viable change** to get your requested workflow working.

---

**Next Action:** Do you want me to implement Option A (DXF import in AdaptiveKernelLab) or create a new simplified endpoint (Option B)?
