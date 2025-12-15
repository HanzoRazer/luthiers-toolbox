# Neck Profile Bundle Analysis & Integration Plan

**Source:** `GitHub-Neck _Profile_ bundle.txt`  
**Date:** November 25, 2025  
**Status:** Ready for Integration

---

## 📋 Executive Summary

This document contains a **complete neck profile generation system** for electric guitar necks (Stratocaster, Telecaster, Les Paul) with:
- DXF cross-section export for Fusion 360 import
- SVG preview generation
- Profile types: C, V, U shapes
- FastAPI backend integration
- Vue 3 frontend (NeckLab)
- Compare Mode integration for neck comparisons
- Diff tracking for neck section variations

**Redundancy Note:** The file contains **3 iterations** of the same core code with progressive enhancements. Each iteration builds on the previous but is **fully self-contained**.

---

## 🗂️ Content Structure Analysis

### **Section 1: Standalone CLI Tool** (Lines 1-1200)
**Purpose:** GitHub-ready standalone Python package  
**Redundancy:** Foundation code - keep as reference

**Key Files:**
```
neck-dxf-gen/
├─ README.md
├─ requirements.txt
├─ src/neck_dxf_gen/
│  ├─ __init__.py
│  ├─ geometry.py          # Core profile generators (C/V/U)
│  ├─ dxf_writer.py         # ezdxf LWPOLYLINE export
│  ├─ svg_writer.py         # SVG preview generation
│  └─ cli.py                # Command-line interface
└─ config/
   ├─ strat_modern_c.json   # Fender Strat Modern C
   ├─ tele_modern_c.json    # Fender Tele Modern C/U
   └─ les_paul_59.json      # Gibson Les Paul '59 Round
```

**What's Unique:**
- CLI entry point (`python -m neck_dxf_gen.cli`)
- File-based DXF/SVG output
- Standalone package structure

**Status:** ✅ Complete - Can be GitHub repo or integrated

---

### **Section 2: FastAPI Backend Integration** (Lines 1200-2500)
**Purpose:** Integration into existing Luthier's Tool Box backend  
**Redundancy:** **Primary implementation** - use this

**Key Files:**
```
services/api/
├─ util/neck_profiles/
│  ├─ __init__.py
│  ├─ geometry.py          # ✅ KEEP - Profile generators with dataclasses
│  ├─ dxf_writer.py         # ✅ KEEP - Both file + in-memory DXF export
│  ├─ svg_writer.py         # ✅ KEEP - SVG generation
│  └─ engine.py             # ✅ KEEP - Config loader + high-level API
├─ data/neck_profiles/
│  ├─ strat_modern_c.json
│  ├─ tele_modern_c.json
│  └─ les_paul_59.json
└─ routers/
   └─ neck_profile_router.py # ✅ KEEP - REST API endpoints
```

**API Endpoints:**
```
GET  /cam/neck/profiles           # List available neck profiles
GET  /cam/neck/profile?profile_id=strat_modern_c  # Get profile with section points
GET  /cam/neck/section_dxf?profile_id=X&section=nut  # Download DXF for single section
```

**What's Unique:**
- FastAPI router integration
- In-memory DXF generation (no temp files)
- JSON-based profile storage
- Pydantic models for validation

**Status:** ✅ Complete - Ready to integrate

---

### **Section 3: Vue Frontend (NeckLab)** (Lines 2500-3500)
**Purpose:** Interactive UI for neck profile visualization  
**Redundancy:** Builds on Section 2 backend

**Key File:**
```
packages/client/src/views/NeckLabView.vue  # ✅ KEEP - Complete Vue component
```

**Features:**
- Profile selector dropdown (Strat/Tele/LP)
- Section list (nut, fret_1, fret_3, ..., heel)
- SVG cross-section preview with auto-scaling
- Download DXF button (per section)
- "Send to Compare Mode" integration (baseline/candidate)

**UI Pattern:**
```vue
<template>
  <div class="p-4 space-y-4">
    <h2>Neck Lab</h2>
    
    <!-- Profile selector -->
    <select v-model="selectedProfileId" @change="onProfileChange">
      <option v-for="p in profiles" :value="p.id">{{ p.name }}</option>
    </select>
    
    <!-- Sections list -->
    <button v-for="sec in currentProfile.sections" @click="selectSection(sec)">
      {{ sec.name }} @ {{ sec.position_mm }} mm
    </button>
    
    <!-- SVG preview -->
    <svg :viewBox="svgViewBox">
      <polyline :points="svgPolyline" />
    </svg>
    
    <!-- Actions -->
    <button @click="downloadDxf">Download DXF</button>
    <button @click="sendToCompare('baseline')">Send as Baseline</button>
    <button @click="sendToCompare('candidate')">Send as Candidate</button>
  </div>
</template>
```

**Status:** ✅ Complete - Ready to integrate

---

### **Section 4: Compare Mode Integration** (Lines 3500-4449)
**Purpose:** Neck-specific comparison tracking and diff storage  
**Redundancy:** Extension of Section 2+3, adds diff persistence

**New Files:**
```
services/api/
├─ util/neck_diffs_store.py     # ✅ ADD - JSONL-based diff storage
└─ routers/neck_diffs_router.py # ✅ ADD - Diff tracking endpoints

services/api/data/
└─ neck_diffs.jsonl             # Created automatically
```

**API Endpoints:**
```
POST /cam/neck/diffs  # Save neck comparison record
GET  /cam/neck/diffs?limit=50  # List recent comparisons
```

**CompareLabView.vue Updates:**
- Detect when both panes are neck sources
- "Save neck comparison" button
- Compute thickness/width deltas
- POST to `/cam/neck/diffs`

**Diff Record Schema:**
```json
{
  "id": "uuid",
  "created_at": "2025-11-25T...",
  "section_name": "fret_12",
  "section_position_mm": 185.0,
  "baseline_profile_id": "strat_modern_c",
  "baseline_profile_name": "Fender Stratocaster – Modern C",
  "baseline_scale_length_mm": 647.7,
  "baseline_width_mm": 56.9,
  "baseline_height_mm": 23.6,
  "candidate_profile_id": "tele_modern_c",
  "candidate_profile_name": "Fender Telecaster – Modern C/U",
  "candidate_scale_length_mm": 647.7,
  "candidate_width_mm": 57.2,
  "candidate_height_mm": 24.4,
  "thickness_delta_mm": 0.8,
  "width_delta_mm": 0.3,
  "note": null,
  "source": "compare_lab"
}
```

**Status:** ✅ Complete - Ready to integrate

---

## 🔑 Core Code Snippets (Non-Redundant)

### **1. Profile Geometry Generator**
**File:** `services/api/app/util/neck_profiles/geometry.py`  
**Purpose:** Generate C/V/U profile shapes

```python
@dataclass
class SectionSpec:
    name: str
    position_mm: float
    width_mm: float
    thickness_mm: float
    samples_per_half: int = 32
    profile_type: str = "C"  # "C", "V", or "U"

def generate_c_profile(sec: SectionSpec) -> List[Point]:
    """Symmetric ellipse profile (Modern C)"""
    a = sec.width_mm / 2.0      # semi-width
    b = sec.thickness_mm / 2.0  # semi-thickness
    
    # Upper half ellipse: left -> right
    for i in range(sec.samples_per_half + 1):
        x = -a + (2.0 * a) * (i / sec.samples_per_half)
        val = 1.0 - (x * x) / (a * a)
        y = b * math.sqrt(max(val, 0.0))
        pts.append((x, y))
    
    # Mirror for lower half
    return pts + [(x, -y) for x, y in reversed(pts)]

def generate_v_profile(sec: SectionSpec) -> List[Point]:
    """Sharp V profile (vintage necks)"""
    # Top ellipse + sharp bottom point

def generate_u_profile(sec: SectionSpec) -> List[Point]:
    """Flat-bottom U profile (Les Paul '59)"""
    # Ellipse with flattened bottom 70% zone
```

**Key Features:**
- Centered at (0, 0)
- X-axis: width (left/right)
- Y-axis: thickness (up/down)
- Closed polyline compatible with LWPOLYLINE

---

### **2. DXF Export (In-Memory)**
**File:** `services/api/app/util/neck_profiles/dxf_writer.py`

```python
def dxf_bytes_from_points(points: List[Point], layer: str = "SECTION") -> bytes:
    """Generate DXF bytes for HTTP download (no temp file)"""
    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()
    msp.add_lwpolyline(points, dxfattribs={"layer": layer}, close=True)
    
    buf = io.BytesIO()
    doc.write(buf)
    return buf.getvalue()
```

**Why Important:**
- No filesystem operations in production
- Direct HTTP streaming
- Clean LWPOLYLINE format (Fusion 360 compatible)

---

### **3. Config Loader**
**File:** `services/api/app/util/neck_profiles/engine.py`

```python
@dataclass
class NeckProfileConfig:
    id: str
    name: str
    scale_length_mm: float
    sections: List[SectionSpec]

def load_neck_profile(profile_id: str) -> NeckProfileConfig:
    """Load JSON config by id or filename stem"""
    # Search data/neck_profiles/*.json
    # Parse sections with profile_type inheritance
    # Return structured config
```

**Key Features:**
- Supports both explicit `id` field and filename stem lookup
- Default profile_type inheritance from top-level config
- Per-section profile_type override

---

### **4. FastAPI Router**
**File:** `services/api/app/routers/neck_profile_router.py`

```python
@router.get("/profiles", response_model=List[NeckProfileSummary])
async def get_neck_profiles():
    """List available neck profiles"""
    profiles = list_neck_profiles()
    return [NeckProfileSummary(**p) for p in profiles]

@router.get("/section_dxf")
async def get_neck_section_dxf(
    profile_id: str = Query(...),
    section: str = Query(...)
):
    """Download DXF for single section"""
    cfg = load_neck_profile(profile_id)
    sections_points = generate_neck_profile_sections(cfg)
    pts = sections_points[section]
    dxf_bytes = dxf_bytes_from_points(pts)
    
    return StreamingResponse(
        iter([dxf_bytes]),
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{profile_id}__{section}.dxf"'}
    )
```

---

### **5. Vue NeckLab Component**
**File:** `packages/client/src/views/NeckLabView.vue`

```typescript
// Load profiles on mount
async function loadProfiles() {
  const resp = await fetch('/cam/neck/profiles')
  profiles.value = await resp.json()
  if (profiles.value.length > 0) {
    await loadProfile(profiles.value[0].id)
  }
}

// Load specific profile with sections
async function loadProfile(profileId: string) {
  const resp = await fetch(`/cam/neck/profile?profile_id=${profileId}`)
  currentProfile.value = await resp.json()
  selectedSection.value = currentProfile.value.sections[0]
}

// Download DXF for selected section
async function downloadDxf() {
  if (!selectedProfileId.value || !selectedSection.value) return
  const url = `/cam/neck/section_dxf?profile_id=${selectedProfileId.value}&section=${selectedSection.value.name}`
  window.open(url, '_blank')
}

// Send to Compare Mode
function sendToCompare(role: 'baseline' | 'candidate') {
  if (!selectedProfileId.value || !selectedSection.value) return
  router.push({
    path: '/lab/compare',
    query: {
      [`${role}_type`]: 'neck',
      [`${role}_profile`]: selectedProfileId.value,
      [`${role}_section`]: selectedSection.value.name
    }
  })
}
```

---

### **6. Diff Storage**
**File:** `services/api/app/util/neck_diffs_store.py`

```python
@dataclass
class NeckDiffRecord:
    id: str
    created_at: str
    section_name: str
    baseline_profile_id: str
    candidate_profile_id: str
    thickness_delta_mm: float
    width_delta_mm: float
    # ... full metadata fields

def append_neck_diff(**kwargs) -> NeckDiffRecord:
    """Append diff record to JSONL"""
    rec = NeckDiffRecord(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow().isoformat(),
        **kwargs
    )
    
    with open(NECK_DIFFS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec.__dict__) + "\n")
    
    return rec

def list_neck_diffs(limit: int = 50) -> List[NeckDiffRecord]:
    """Load recent diff records"""
    # Read JSONL, parse, return sorted by created_at desc
```

---

## 🚀 Integration Roadmap

### **Phase 1: Backend Core** (Standalone, No UI)
**Goal:** Get neck profile API working

**Files to Add:**
```
services/api/app/
├─ util/neck_profiles/
│  ├─ __init__.py           # ✅ Create (Section 2)
│  ├─ geometry.py           # ✅ Create (Section 2)
│  ├─ dxf_writer.py         # ✅ Create (Section 2)
│  ├─ svg_writer.py         # ✅ Create (Section 2)
│  └─ engine.py             # ✅ Create (Section 2)
├─ data/neck_profiles/
│  ├─ strat_modern_c.json   # ✅ Create (Section 2)
│  ├─ tele_modern_c.json    # ✅ Create (Section 2)
│  └─ les_paul_59.json      # ✅ Create (Section 2)
└─ routers/
   └─ neck_profile_router.py # ✅ Create (Section 2)
```

**Router Registration:**
```python
# services/api/app/main.py
from .routers.neck_profile_router import router as neck_profile_router
app.include_router(neck_profile_router)
```

**Dependencies:** Add to `requirements.txt` if missing:
```
ezdxf>=1.1.0
```

**Test:**
```bash
# Start server
cd services/api
uvicorn app.main:app --reload --port 8000

# Test endpoints
curl http://localhost:8000/cam/neck/profiles
curl "http://localhost:8000/cam/neck/profile?profile_id=strat_modern_c"
curl "http://localhost:8000/cam/neck/section_dxf?profile_id=strat_modern_c&section=fret_12" -o test_section.dxf
```

**Validation:**
- ✅ Profiles list returns 3 configs
- ✅ Profile detail shows sections with points
- ✅ DXF downloads open in Fusion 360

---

### **Phase 2: Frontend NeckLab** (Interactive UI)
**Goal:** Visual neck section browser

**Files to Add:**
```
packages/client/src/views/NeckLabView.vue  # ✅ Create (Section 3)
```

**Router Integration:**
```typescript
// packages/client/src/router/index.ts
import NeckLabView from '@/views/NeckLabView.vue'

const routes = [
  // ... existing routes
  {
    path: '/lab/neck',
    name: 'NeckLab',
    component: NeckLabView
  }
]
```

**Navigation Link** (add to main nav if exists):
```vue
<router-link to="/lab/neck">Neck Lab</router-link>
```

**Test:**
```bash
# Start client
cd packages/client
npm run dev

# Navigate to http://localhost:5173/lab/neck
# 1. Select profile (Strat/Tele/LP)
# 2. Click section (fret_12)
# 3. View SVG preview
# 4. Click "Download DXF" - should download file
```

**Validation:**
- ✅ Profile dropdown loads 3 options
- ✅ Sections list shows 9 items per profile
- ✅ SVG preview renders correctly (centered, scaled)
- ✅ DXF download button triggers file save

---

### **Phase 3: Compare Mode Bridge** (Baseline/Candidate Navigation)
**Goal:** Send neck sections to Compare Mode for side-by-side comparison

**Files to Modify:**
```
packages/client/src/views/NeckLabView.vue        # ✅ Already has buttons (Section 3)
packages/client/src/views/CompareLabView.vue     # ❌ Add neck source detection
```

**CompareLabView.vue Updates:**
```typescript
// Detect query params: ?baseline_type=neck&baseline_profile=strat_modern_c&baseline_section=fret_12
onMounted(() => {
  const query = route.query
  if (query.baseline_type === 'neck') {
    loadNeckAsBaseline(query.baseline_profile, query.baseline_section)
  }
  if (query.candidate_type === 'neck') {
    loadNeckAsCandidate(query.candidate_profile, query.candidate_section)
  }
})

async function loadNeckAsBaseline(profileId: string, sectionName: string) {
  const resp = await fetch(`/cam/neck/profile?profile_id=${profileId}`)
  const profile = await resp.json()
  const section = profile.sections.find(s => s.name === sectionName)
  
  // Set baseline pane
  baselineNeck.value = {
    profileId,
    profileName: profile.name,
    scaleLengthMm: profile.scale_length_mm,
    sectionName,
    sectionPositionMm: section.position_mm,
    widthMm: section.width_mm || computeWidth(section.points),
    heightMm: section.height_mm || computeHeight(section.points),
    points: section.points
  }
}
```

**Test:**
```bash
# From NeckLab
# 1. Select Strat / fret_12
# 2. Click "Send as Baseline to Compare Mode"
# → Should navigate to /lab/compare?baseline_type=neck&baseline_profile=strat_modern_c&baseline_section=fret_12
# 3. CompareLabView should load Strat fret_12 in left pane
# 4. Manually switch to NeckLab, select Tele / fret_12, "Send as Candidate"
# → Should populate right pane with Tele fret_12
```

**Validation:**
- ✅ Baseline pane shows correct profile name
- ✅ Candidate pane shows correct profile name
- ✅ Delta chips show thickness/width differences
- ✅ SVG overlays align correctly

---

### **Phase 4: Diff Tracking** (Persistent Comparison Records)
**Goal:** Save neck comparisons for future analysis

**Files to Add:**
```
services/api/app/
├─ util/neck_diffs_store.py      # ✅ Create (Section 4)
└─ routers/neck_diffs_router.py  # ✅ Create (Section 4)

services/api/data/
└─ neck_diffs.jsonl              # Auto-created
```

**Router Registration:**
```python
# services/api/app/main.py
from .routers.neck_diffs_router import router as neck_diffs_router
app.include_router(neck_diffs_router)
```

**CompareLabView.vue Updates:**
```typescript
const canSaveNeckDiff = computed(() => {
  return !!(baselineNeck.value && candidateNeck.value)
})

async function saveNeckDiff() {
  if (!baselineNeck.value || !candidateNeck.value) return
  
  const payload = {
    section_name: baselineNeck.value.sectionName,
    section_position_mm: baselineNeck.value.sectionPositionMm,
    baseline_profile_id: baselineNeck.value.profileId,
    baseline_profile_name: baselineNeck.value.profileName,
    baseline_width_mm: baselineNeck.value.widthMm,
    baseline_height_mm: baselineNeck.value.heightMm,
    candidate_profile_id: candidateNeck.value.profileId,
    candidate_profile_name: candidateNeck.value.profileName,
    candidate_width_mm: candidateNeck.value.widthMm,
    candidate_height_mm: candidateNeck.value.heightMm,
    thickness_delta_mm: candidateNeck.value.heightMm - baselineNeck.value.heightMm,
    width_delta_mm: candidateNeck.value.widthMm - baselineNeck.value.widthMm,
    source: 'compare_lab'
  }
  
  await fetch('/cam/neck/diffs', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  })
}
```

**Test:**
```bash
# From CompareLabView with Strat vs Tele loaded
# 1. Click "Save neck comparison"
# 2. Check services/api/data/neck_diffs.jsonl exists
# 3. Verify JSONL line contains correct deltas
# 4. Test GET /cam/neck/diffs?limit=10
# → Should return saved comparison
```

---

## ✅ Integration Checklist

### **Backend Files**
- [ ] Create `services/api/app/util/neck_profiles/__init__.py`
- [ ] Create `services/api/app/util/neck_profiles/geometry.py`
- [ ] Create `services/api/app/util/neck_profiles/dxf_writer.py`
- [ ] Create `services/api/app/util/neck_profiles/svg_writer.py`
- [ ] Create `services/api/app/util/neck_profiles/engine.py`
- [ ] Create `services/api/app/routers/neck_profile_router.py`
- [ ] Create `services/api/app/util/neck_diffs_store.py`
- [ ] Create `services/api/app/routers/neck_diffs_router.py`
- [ ] Create `services/api/app/data/neck_profiles/strat_modern_c.json`
- [ ] Create `services/api/app/data/neck_profiles/tele_modern_c.json`
- [ ] Create `services/api/app/data/neck_profiles/les_paul_59.json`
- [ ] Register routers in `services/api/app/main.py`
- [ ] Add `ezdxf>=1.1.0` to `requirements.txt`

### **Frontend Files**
- [ ] Create `packages/client/src/views/NeckLabView.vue`
- [ ] Add `/lab/neck` route to `packages/client/src/router/index.ts`
- [ ] Update `CompareLabView.vue` with neck source detection (query params)
- [ ] Update `CompareLabView.vue` with "Save neck comparison" button
- [ ] Add navigation link to NeckLab in main nav (optional)

### **Testing**
- [ ] Backend: `curl` tests for all 3 profiles
- [ ] Backend: DXF download opens in Fusion 360
- [ ] Frontend: NeckLab loads 3 profiles correctly
- [ ] Frontend: SVG preview renders all 9 sections
- [ ] Frontend: DXF download button works
- [ ] Frontend: "Send to Compare" navigation works
- [ ] Frontend: CompareLabView loads neck sources from query params
- [ ] Frontend: "Save neck comparison" creates JSONL entry
- [ ] End-to-end: Strat vs Tele comparison shows correct deltas

### **Documentation**
- [ ] Add NeckLab to main README navigation
- [ ] Document JSON config format (profile_type, sections)
- [ ] Document Compare Mode neck source query params
- [ ] Document neck diff JSONL schema
- [ ] Create smoke test script (`test_neck_profiles.ps1`)

---

## 🎯 Next Steps Recommendation

**Priority Order:**
1. **Phase 1 (Backend Core)** - Standalone API, no UI dependencies
2. **Phase 2 (NeckLab UI)** - Visual neck browser
3. **Phase 3 (Compare Bridge)** - Navigation integration
4. **Phase 4 (Diff Tracking)** - Persistent records (optional)

**Estimated Integration Time:**
- Phase 1: 1-2 hours (backend only)
- Phase 2: 2-3 hours (Vue component)
- Phase 3: 1-2 hours (CompareLabView updates)
- Phase 4: 1 hour (diff storage)

**Total:** 5-8 hours for complete integration

**Dependencies:**
- Existing Compare Mode (`CompareLabView.vue`)
- Existing router structure
- `ezdxf` library (may already be in repo)

**No Conflicts:** All new code, no overwrites of existing files.

---

## 📚 Key Takeaways

**What Makes This Bundle Valuable:**
1. ✅ **Production-ready code** - No placeholders, full implementation
2. ✅ **Clean separation** - Backend util, API router, frontend view
3. ✅ **Multi-format export** - DXF (Fusion 360), SVG (preview), JSON (API)
4. ✅ **Profile flexibility** - C/V/U shapes, per-section overrides
5. ✅ **Compare Mode native** - Built-in diff tracking for neck variations
6. ✅ **Zero dependencies on legacy code** - Standalone module

**What to Skip:**
- ❌ Section 1 (Standalone CLI) - Already integrated in Section 2
- ❌ Redundant geometry.py in Section 3 - Use Section 2 version

**Critical Success Factors:**
- Router registration in `main.py` (both routers)
- Correct data directory path (`services/api/data/neck_profiles/`)
- Query param handling in `CompareLabView.vue` for navigation bridge
- JSONL file permissions for diff storage

---

**Ready for Integration:** All code is production-ready and non-redundant when following this analysis.
