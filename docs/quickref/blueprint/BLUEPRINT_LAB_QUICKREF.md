# Blueprint Lab - Quick Reference

**Status:** ✅ Complete (Phase 1 + Phase 2 UI)  
**Location:** `packages/client/src/views/BlueprintLab.vue`

---

## 🚀 Quick Start

### **1. Start Services**

```powershell
# Terminal 1: Start API
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Client  
cd packages/client
npm run dev
# Opens http://localhost:5173
```

### **2. Configure API Key**

```powershell
# Option A: Emergent LLM (preferred)
$env:EMERGENT_LLM_KEY = "your-api-key-here"

# Option B: Anthropic Direct
$env:ANTHROPIC_API_KEY = "your-api-key-here"
```

### **3. Test Backend**

```powershell
# Health check
.\test_blueprint_lab.ps1

# Expected output:
# ✓ Status: healthy
# ✓ Phase: 1+2
# ✓ All tests passed!
```

### **4. Access UI**

Navigate to: **`http://localhost:5173/lab/blueprint`**  
*(Requires router configuration - see Integration section)*

---

## 📋 Workflow

### **Phase 1: AI Analysis** (30-120s)

1. **Upload blueprint** (PDF, PNG, JPG - max 20MB)
2. Click **"Start Analysis"**
3. Wait for Claude Sonnet 4 to analyze
4. **Results:**
   - Detected scale (1:1, 1:2, etc.)
   - Blueprint type (guitar body, neck, etc.)
   - Dimension list (up to 50 dimensions)
5. **Optional:** Export SVG with dimension annotations

### **Phase 2: Vectorization** (0.2-2s)

1. Adjust parameters (optional):
   - **Scale Factor:** Correct AI scale if wrong
   - **Edge Thresholds:** Control edge detection sensitivity
   - **Min Area:** Filter small noise
2. Click **"Vectorize Geometry"**
3. **Results:**
   - Contour count (closed shapes)
   - Line count (straight segments)
   - Processing time
4. **Export:**
   - SVG (geometry visualization)
   - DXF R2000 (CAM-ready with LWPOLYLINEs)

---

## 🎛️ Parameters

### **Vectorization Controls**

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| Scale Factor | 1.0 | 0.1–10.0 | Adjust if scale detection wrong |
| Low Threshold | 50 | 10–200 | **Lower** = more edges |
| High Threshold | 150 | 50–300 | **Higher** = stricter detection |
| Min Area | 100 px² | 10–1000 | Filter noise |

**Tips:**
- **Noisy scans:** Increase Low to 80-100
- **Missing edges:** Decrease Low to 30-40
- **Small artifacts:** Increase Min Area to 500-1000
- **Wrong scale:** Adjust Scale Factor (e.g., 2.0 for 1:2 blueprint)

---

## 🔌 API Endpoints

### **Health Check**
```bash
curl http://localhost:8000/api/blueprint/health
```

### **Analyze Blueprint**
```bash
curl -X POST http://localhost:8000/api/blueprint/analyze \
  -F "file=@blueprint.pdf"
```

### **Vectorize Geometry**
```bash
curl -X POST http://localhost:8000/api/blueprint/vectorize-geometry \
  -F "file=@blueprint.pdf" \
  -F "analysis_data={\"scale\":\"1:1\",\"dimensions\":[]}" \
  -F "scale_factor=1.0" \
  -F "low_threshold=50" \
  -F "high_threshold=150" \
  -F "min_area=100"
```

---

## 🐛 Troubleshooting

### **"Analysis failed" Error**

**Cause:** Missing API key  
**Fix:**
```powershell
$env:EMERGENT_LLM_KEY = "your-key"
# Restart API server
```

### **"Phase 2 Not Available" Warning**

**Cause:** OpenCV not installed  
**Fix:**
```powershell
cd services/blueprint-import
pip install opencv-python==4.12.0 scikit-image==0.25.2
# Restart API server
```

### **DXF Import Fails in Fusion 360**

**Cause:** Unclosed polylines or no geometry  
**Fix:**
- Lower edge thresholds to detect more geometry
- Check SVG preview first
- Verify DXF has LWPOLYLINE entities (open in text editor)

### **Upload Zone Not Responding**

**Cause:** File too large or wrong type  
**Fix:**
- Max size: 20MB
- Supported: PDF, PNG, JPG only
- Check browser console for errors

---

## 📊 File Exports

### **Phase 1: SVG (Dimensions Only)**
- **Content:** Dimension annotations from AI analysis
- **Use Case:** Visual review of detected dimensions
- **Format:** SVG with text labels

### **Phase 2: SVG (Vectorized)**
- **Content:** Detected contours (blue) + lines (red)
- **Use Case:** Visual verification before DXF export
- **Format:** SVG with path elements

### **Phase 2: DXF R2000 (CAM-Ready)**
- **Content:** Closed LWPOLYLINEs on separate layers
- **Layers:**
  - `GEOMETRY` - Contours
  - `LINES` - Hough lines
  - `DIMENSIONS` - Annotations
- **Use Case:** Import into Fusion 360, VCarve, Mach4
- **Format:** DXF R2000 (AC1015)

---

## 🔗 Integration

### **Add to Router** (Vue Router)

```typescript
// packages/client/src/router/index.ts
import BlueprintLab from '@/views/BlueprintLab.vue'

const routes = [
  // ... existing routes
  {
    path: '/lab/blueprint',
    name: 'blueprint-lab',
    component: BlueprintLab
  }
]
```

### **Add to Navigation**

```vue
<!-- Navigation component -->
<nav>
  <router-link to="/lab/blueprint">Blueprint Lab</router-link>
</nav>
```

### **Standalone Usage**

```vue
<script setup>
import BlueprintLab from '@/views/BlueprintLab.vue'
</script>

<template>
  <BlueprintLab />
</template>
```

---

## 📈 Performance

| Operation | Duration | Notes |
|-----------|----------|-------|
| **AI Analysis** | 30-120s | Claude Sonnet 4 API (network dependent) |
| **Vectorization** | 0.2-2s | OpenCV (image size dependent) |
| **SVG Export** | <1s | Local generation |
| **DXF Export** | <1s | Local generation |

**File Size Limits:**
- Max upload: 20MB
- Typical PDF: 2-10MB
- Typical PNG: 5-15MB
- Typical JPG: 1-5MB

---

## ✅ Testing Checklist

### **Backend**
- [ ] Health check returns `{"status":"healthy","phase":"1+2"}`
- [ ] API key configured (EMERGENT_LLM_KEY or ANTHROPIC_API_KEY)
- [ ] OpenCV installed (check health endpoint)

### **UI**
- [ ] Upload zone accepts PDF/PNG/JPG
- [ ] Upload zone rejects invalid files
- [ ] Analysis starts and shows progress timer
- [ ] Analysis results display correctly
- [ ] Dimensions table populates
- [ ] Phase 1 SVG export works
- [ ] Phase 2 section appears after analysis
- [ ] Vectorization controls adjustable
- [ ] Vectorization completes with stats
- [ ] Phase 2 SVG download works
- [ ] Phase 2 DXF download works
- [ ] "Re-vectorize" resets controls
- [ ] "Upload New Blueprint" resets workflow
- [ ] Errors display in banner
- [ ] Error banner closeable

### **E2E**
- [ ] Upload real guitar blueprint
- [ ] Verify scale detection accuracy
- [ ] Check dimension count and quality
- [ ] Export DXF and import to Fusion 360
- [ ] Verify closed polylines in Fusion 360
- [ ] Test with noisy scan (adjust parameters)

---

## 🎯 Next Features (Phase 3)

### **CAM Integration** (~2 hours)
```vue
<!-- Phase 3 section -->
<button @click="sendToAdaptiveLab">
  Send to Adaptive Lab
</button>
```

**Implementation:**
- Auto-populate tool diameter from scale
- Extract loops from vectorized DXF
- Bridge to `/cam/plan_from_dxf` endpoint
- Pre-fill adaptive pocketing parameters

### **Real-time Preview** (~1 hour)
```vue
<canvas ref="previewCanvas" class="svg-preview"></canvas>
```

**Features:**
- Inline SVG rendering
- Zoom/pan controls
- Toggle contours/lines visibility

### **Preset Management** (~1 hour)
```typescript
const presets = {
  'guitar-body': { lowThreshold: 40, highThreshold: 120, minArea: 200 },
  'guitar-neck': { lowThreshold: 60, highThreshold: 180, minArea: 100 }
}
```

---

## 📚 Related Docs

- [Blueprint Lab Integration Complete](./BLUEPRINT_LAB_INTEGRATION_COMPLETE.md) - Full implementation guide
- [Blueprint Phase 1 Summary](./BLUEPRINT_IMPORT_PHASE1_SUMMARY.md) - AI analysis backend
- [Blueprint Phase 2 Complete](./BLUEPRINT_IMPORT_PHASE2_COMPLETE.md) - OpenCV vectorization
- [CAM Pipeline Integration](./CAM_PIPELINE_INTEGRATION_PHASE1.md) - Future integration target

---

## 🆘 Support

**Common Commands:**

```powershell
# Check health
curl http://localhost:8000/api/blueprint/health

# Test with real file
.\test_blueprint_lab.ps1

# View logs
cd services/api
# Check terminal for errors

# Restart services
# Ctrl+C in terminals, then re-run start commands
```

**If Stuck:**
1. Check health endpoint
2. Verify API key configured
3. Check API server logs
4. Test with minimal test file (small PNG)
5. Refer to [BLUEPRINT_LAB_INTEGRATION_COMPLETE.md](./BLUEPRINT_LAB_INTEGRATION_COMPLETE.md)

---

**Status:** ✅ **Ready for Integration**  
**Backend:** ✅ **Phase 1 + Phase 2 Complete**  
**Frontend:** ✅ **BlueprintLab.vue Complete**  
**Next:** Add to router and test with real blueprints
