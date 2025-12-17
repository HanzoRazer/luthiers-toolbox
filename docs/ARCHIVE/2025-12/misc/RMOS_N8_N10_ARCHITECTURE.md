# RMOS N8–N10 Architecture: Integration Blueprint for Rosette Generator

**Version:** 1.0  
**Date:** November 30, 2025  
**Purpose:** Define N8–N10 architecture to guide Rosette Studio integration  
**Audience:** Developers implementing rosette pattern generation features

---

## 📋 Executive Summary

This document describes the **current RMOS architecture (N8–N10 bundles)** to enable integration of the **RMOS Studio rosette generator** specifications. It provides:

- Current data structures and stores
- API endpoint patterns
- Frontend component architecture
- Integration points for new rosette features
- Migration path from specs to implementation

**Key Finding:** Current RMOS focuses on **preset management, analytics, and safety** rather than **rosette design tools**. The Studio specs describe aspirational geometry-focused features that can be integrated as **N11 bundles**.

---

## 🏗️ Current Architecture Overview (N8–N10)

### **Three-Layer Stack**

```
┌─────────────────────────────────────────┐
│   Frontend Layer (Vue 3 + TypeScript)   │
│   - Pinia stores for state management   │
│   - Views: Analytics, LiveMonitor, etc  │
│   - Components: Safety banner, grids    │
└──────────────┬──────────────────────────┘
               │ REST + WebSocket
┌──────────────┴──────────────────────────┐
│   Backend Layer (FastAPI + Python)      │
│   - RMOS API routes (/api/rmos/*)       │
│   - SQLite stores (patterns, joblogs)   │
│   - Safety policy engine (N10.2)        │
└──────────────┬──────────────────────────┘
               │ File I/O + DB
┌──────────────┴──────────────────────────┐
│   Persistence Layer                     │
│   - SQLite databases (N8.6)             │
│   - JSON migration support (N8.7)       │
└─────────────────────────────────────────┘
```

---

## 📦 N8: Migration & Storage Architecture

### **N8.1–N8.2: Store Normalization**

**Data Model:**
```python
# Pattern Store Entity
{
  "pattern_id": "preset_abc123",
  "name": "Spanish Traditional",
  "ring_count": 5,
  "geometry": {
    "rings": [
      {"radius_mm": 20, "width_mm": 3, "tile_length_mm": 8},
      # ... more rings
    ]
  },
  "strip_family_id": "maple_walnut_001",
  "metadata": {
    "complexity": "medium",
    "fragility_score": 0.42,
    "risk_grade": "GREEN"
  }
}

# JobLog Store Entity
{
  "job_id": "JOB-20251130-103045",
  "job_type": "slice_batch",
  "pattern_id": "preset_abc123",
  "status": "completed",
  "start_time": "2025-11-30T10:30:45Z",
  "end_time": "2025-11-30T10:45:12Z",
  "duration_seconds": 867,
  "parameters": {...},
  "results": {...}
}
```

**Storage Implementation:**
```python
# services/api/app/stores/rmos_stores.py
from .pattern_store import PatternStore
from .joblog_store import JobLogStore
from .strip_family_store import StripFamilyStore

class RmosStores:
    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self.patterns = PatternStore(self.db)
        self.joblogs = JobLogStore(self.db)
        self.strip_families = StripFamilyStore(self.db)
```

### **N8.3–N8.5: Export Pipelines**

**Export Architecture:**
```
Pattern Data
    ↓
Export Pipeline
    ├─→ PDF (design sheet)
    ├─→ JSON (CAM parameters)
    └─→ G-code (CNC operations)
```

**API Endpoint:**
```python
POST /api/rmos/patterns/{pattern_id}/export
{
  "format": "pdf|json|gcode",
  "include_preview": true,
  "cam_settings": {...}
}
```

### **N8.6: SQLite Persistence**

**Database Schema:**
```sql
-- Patterns table
CREATE TABLE patterns (
    pattern_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    ring_count INTEGER,
    geometry TEXT,  -- JSON
    strip_family_id TEXT,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- JobLogs table
CREATE TABLE joblogs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    pattern_id TEXT,
    status TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds REAL,
    parameters TEXT,  -- JSON
    results TEXT,     -- JSON
    FOREIGN KEY (pattern_id) REFERENCES patterns(pattern_id)
);

-- StripFamilies table
CREATE TABLE strip_families (
    family_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    strip_width_mm REAL,
    strip_thickness_mm REAL,
    material_type TEXT,
    strips TEXT,  -- JSON array
    metadata TEXT
);
```

### **N8.7: Migration System**

**Migration Flow:**
```
Legacy JSON Files
    ↓
Migration Script (N8.7)
    ├─→ SQLite Database
    ├─→ Migration Report (JSON/PDF)
    └─→ Validation Checks

Dashboard (N8.7.4)
    ├─→ View migration status
    ├─→ Detect drift (N8.7.5)
    └─→ Auto-fix mismatches
```

**API Endpoints:**
```python
GET  /api/rmos/stores/migration/status
POST /api/rmos/stores/migration/run
GET  /api/rmos/stores/migration/report
POST /api/rmos/stores/migration/fix-drift
```

---

## 📊 N9: Analytics & Artifacts Architecture

### **N9.0: Analytics Engine**

**Domain Model:**
```typescript
// Pattern Analytics
interface PatternComplexity {
  simple: number;      // count
  medium: number;
  complex: number;
  expert: number;
}

interface RingStatistics {
  min_rings: number;
  max_rings: number;
  avg_rings: number;
  median_rings: number;
}

// Material Analytics
interface MaterialDistribution {
  material_type: string;
  count: number;
  percentage: number;
}

interface MaterialConsumption {
  total_strips: number;
  total_length_mm: number;
  avg_width_mm: number;
  avg_thickness_mm: number;
}
```

**API Endpoints:**
```python
# Pattern Analytics
GET /api/analytics/patterns/complexity
GET /api/analytics/patterns/rings
GET /api/analytics/patterns/geometry
GET /api/analytics/patterns/families
GET /api/analytics/patterns/{pattern_id}/details

# Material Analytics
GET /api/analytics/materials/distribution
GET /api/analytics/materials/consumption
GET /api/analytics/materials/efficiency
GET /api/analytics/materials/dimensions

# Job Analytics
GET /api/analytics/jobs/success-trends?days=30
GET /api/analytics/jobs/duration
GET /api/analytics/jobs/throughput
```

### **N9.1: Strip Family Manager**

**UI Component:**
```vue
<!-- packages/client/src/components/rmos/MixedMaterialStripFamilyEditor.vue -->
<template>
  <div class="strip-family-editor">
    <div class="family-header">
      <input v-model="family.name" placeholder="Family name" />
    </div>
    <div class="strips-list">
      <div v-for="strip in family.strips" :key="strip.id" class="strip-row">
        <input v-model.number="strip.width_mm" type="number" />
        <input v-model.number="strip.thickness_mm" type="number" />
        <select v-model="strip.material_type">
          <option value="maple">Maple</option>
          <option value="walnut">Walnut</option>
          <!-- ... more materials -->
        </select>
      </div>
    </div>
  </div>
</template>
```

**Pinia Store:**
```typescript
// packages/client/src/stores/useStripFamilyStore.ts
export const useStripFamilyStore = defineStore('stripFamily', () => {
  const families = ref<StripFamily[]>([]);
  
  async function fetchFamilies() {
    const res = await fetch('/api/rmos/strip-families');
    families.value = await res.json();
  }
  
  async function createFamily(data: StripFamilyCreate) {
    const res = await fetch('/api/rmos/strip-families', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return await res.json();
  }
  
  return { families, fetchFamilies, createFamily };
});
```

### **N9.2–N9.9: Advanced Analytics**

**Promotion Impact (N9.2):**
```python
# Track preset promotions across lanes
{
  "preset_id": "preset_abc123",
  "promotion_history": [
    {"from": "experimental", "to": "tuned_v1", "timestamp": "...", "reason": "Passed validation"},
    {"from": "tuned_v1", "to": "safe", "timestamp": "...", "reason": "8/10 clean runs"}
  ],
  "impact_metrics": {
    "fragility_trend": [0.82, 0.76, 0.54, 0.42],
    "success_rate": 0.90,
    "avg_duration_s": 823
  }
}
```

**Artifact Auto-Preview (N9.4):**
```python
# WebSocket event stream
{
  "event_type": "artifact_generated",
  "artifact_id": "art_20251130_103045",
  "artifact_type": "gcode",
  "pattern_id": "preset_abc123",
  "file_path": "/exports/patterns/preset_abc123/program.nc",
  "preview_data": {
    "line_count": 1247,
    "tool_changes": 2,
    "estimated_time_s": 1823
  }
}
```

---

## 🛡️ N10: Real-Time Operations (LiveMonitor + Safety)

### **N10.0: LiveMonitor Base**

**Event Stream Architecture:**
```
Backend Worker
    ↓ (generates events)
WebSocket Server (/ws/monitor)
    ↓ (broadcasts)
Frontend Store (useLiveMonitorStore)
    ↓ (updates UI)
LiveMonitor Component
```

**Event Types:**
```typescript
interface JobEvent {
  event_type: "job_started" | "job_completed" | "job_failed";
  job_id: string;
  pattern_id?: string;
  status: string;
  timestamp: string;
  metadata: {
    materials?: string[];
    worst_fragility_score?: number;
    fragility_band?: string;
    lane_hint?: string;
  };
}

interface PatternEvent {
  event_type: "pattern_created" | "pattern_updated" | "pattern_promoted";
  pattern_id: string;
  name: string;
  timestamp: string;
}
```

**Frontend Store:**
```typescript
// packages/client/src/stores/useLiveMonitorStore.ts
export const useLiveMonitorStore = defineStore('liveMonitor', () => {
  const events = ref<Event[]>([]);
  const counts = ref({
    job: 0,
    pattern: 0,
    material: 0,
    alert: 0
  });
  
  function connectWebSocket() {
    const ws = new WebSocket('/ws/monitor');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      events.value.unshift(data);
      counts.value[data.event_type.split('_')[0]]++;
    };
  }
  
  return { events, counts, connectWebSocket };
});
```

### **N10.1: Drill-Down**

**Subjob Tracking:**
```python
# Hierarchical job structure
{
  "job_id": "JOB-20251130-103045",
  "subjobs": [
    {
      "subjob_id": "SUBJOB-1",
      "operation": "ring_slice_1",
      "status": "completed",
      "duration_s": 124,
      "cam_events": [
        {"event": "tool_change", "timestamp": "...", "tool_id": "thin_kerf_001"},
        {"event": "feed_override", "timestamp": "...", "new_feed": 1080}
      ]
    },
    # ... more subjobs
  ]
}
```

**API Endpoint:**
```python
GET /api/rmos/live-monitor/{job_id}/drilldown
```

### **N10.2: Safety System**

**Architecture:**
```
User Action Request
    ↓
guardedAction() helper (store)
    ↓
POST /rmos/safety/evaluate
    ↓
Safety Policy Engine
    ├─→ Classify risk (lane, fragility, grade)
    ├─→ Apply mode rules (unrestricted, apprentice, mentor_review)
    └─→ Return decision (allow, require_override, deny)
    ↓
Frontend handles:
    - allow → execute action
    - require_override → prompt for token
    - deny → show error
```

**Safety Modes:**
```typescript
type SafetyMode = "unrestricted" | "apprentice" | "mentor_review";

interface SafetyDecision {
  decision: "allow" | "require_override" | "deny";
  mode: SafetyMode;
  risk_level: "low" | "medium" | "high";
  requires_override: boolean;
  reason: string;
}
```

**API Endpoints:**
```python
# Mode Management
GET  /rmos/safety/mode
POST /rmos/safety/mode  # Set new mode

# Action Evaluation
POST /rmos/safety/evaluate
{
  "action": "promote_preset",
  "lane": "safe",
  "fragility_score": 0.75,
  "risk_grade": "YELLOW",
  "preset_id": "preset_abc123"
}

# Override Tokens
POST /rmos/safety/create-override
{
  "action": "promote_preset",
  "created_by": "mentor_alice",
  "ttl_minutes": 15
}
```

---

## 🔌 Integration Points for Rosette Generator

### **Recommended Integration Path: N11 Bundle**

**N11.0: Rosette Pattern Designer (Visual Editor)**

**New Components:**
```
packages/client/src/components/rmos/
├── RosettePatternDesigner.vue       # Main visual editor
├── RingConfigPanel.vue              # Per-ring parameters
├── ColumnStripEditor.vue            # Vertical column editing
└── TilePreviewCanvas.vue            # Horizontal tile output
```

**New Store:**
```typescript
// packages/client/src/stores/useRosetteDesignerStore.ts
export const useRosetteDesignerStore = defineStore('rosetteDesigner', () => {
  const currentPattern = ref<RosettePattern | null>(null);
  const rings = ref<Ring[]>([]);
  const columns = ref<Column[]>([]);
  
  async function savePattern(pattern: RosettePattern) {
    const res = await fetch('/api/rmos/patterns', {
      method: 'POST',
      body: JSON.stringify(pattern)
    });
    return await res.json();
  }
  
  function addRing(ring: Ring) {
    rings.value.push(ring);
    updateTileSegmentation();
  }
  
  function updateTileSegmentation() {
    // Call geometry engine (N11.1)
  }
  
  return { currentPattern, rings, columns, savePattern, addRing };
});
```

**N11.1: Tile Segmentation Engine**

**New Backend Module:**
```python
# services/api/app/cam/rosette/
├── __init__.py
├── tile_segmentation.py    # Algorithms from RMOS_STUDIO_ALGORITHMS.md
├── kerf_compensation.py    # Kerf math
├── herringbone.py          # Angle calculations
└── saw_batch_generator.py  # Slice ordering
```

**Core Algorithm Implementation:**
```python
# services/api/app/cam/rosette/tile_segmentation.py
def compute_tile_segmentation(ring: Ring, tile_length_mm: float) -> SegmentationData:
    """
    Segment ring circumference into uniform tiles.
    
    Algorithm from RMOS_STUDIO_ALGORITHMS.md Section 4.
    """
    # 4.1: Compute circumference
    C = 2 * math.pi * ring.radius_mm
    
    # 4.2: Compute tile count
    N = math.floor(C / tile_length_mm)
    N = max(2, min(N, 300))  # Constraints
    
    # 4.3: Effective tile length (eliminates fractional leftover)
    tile_effective = C / N
    
    # 4.4: Tile angular bounds
    tiles = []
    for i in range(N):
        theta_start = (i / N) * 360
        theta_end = theta_start + (360 / N)
        tiles.append({
            "tile_index": i,
            "theta_start_deg": theta_start,
            "theta_end_deg": theta_end,
            "arc_length_mm": tile_effective
        })
    
    return SegmentationData(
        segmentation_id=f"seg_{ring.ring_id}",
        ring_id=ring.ring_id,
        tile_count=N,
        tile_length_mm=tile_effective,
        tiles=tiles
    )
```

**API Endpoints:**
```python
# New rosette-specific endpoints
POST /api/rmos/rosette/segment-ring
POST /api/rmos/rosette/generate-slices
POST /api/rmos/rosette/compute-material-usage
GET  /api/rmos/rosette/patterns
POST /api/rmos/rosette/patterns
```

**N11.2: Manufacturing Planner Integration**

**Extend Existing Analytics:**
```python
# services/api/app/api/routes/rmos_analytics_api.py
@router.get("/rosette/material-requirements")
def get_rosette_material_requirements(pattern_id: str):
    """
    Calculate strip-family requirements for rosette pattern.
    
    Uses algorithms from RMOS_STUDIO_MANUFACTURING_PLANNER.md.
    """
    pattern = pattern_store.get(pattern_id)
    
    # Aggregate strip lengths across all rings
    requirements = {}
    for ring in pattern.rings:
        C = 2 * math.pi * ring.radius_mm
        for strip_family_id in ring.strip_families:
            if strip_family_id not in requirements:
                requirements[strip_family_id] = 0
            requirements[strip_family_id] += C
    
    # Apply scrap factor (default 5%)
    for family_id in requirements:
        requirements[family_id] *= 1.05
    
    return requirements
```

---

## 📐 Data Structure Mapping

### **Pattern Store → Rosette Pattern**

**Current Pattern Store:**
```python
{
  "pattern_id": str,
  "name": str,
  "ring_count": int,
  "geometry": {
    "rings": [...]  # Generic structure
  },
  "strip_family_id": str,
  "metadata": {...}
}
```

**Extended for Rosette:**
```python
{
  "pattern_id": str,
  "name": str,
  "pattern_type": "rosette",  # NEW: Distinguish from other patterns
  "ring_count": int,
  "geometry": {
    "rings": [
      {
        "ring_id": int,
        "radius_mm": float,
        "width_mm": float,
        "tile_length_mm": float,
        "twist_angle_deg": float,           # NEW: Rosette-specific
        "slice_angle_deg": float,           # NEW: For herringbone
        "column": {                         # NEW: Strip column definition
          "strips": [
            {
              "width_mm": float,
              "color": str,
              "material_id": str,
              "strip_family_id": str
            }
          ]
        }
      }
    ],
    "segmentation": {                       # NEW: Precomputed tiles
      "tile_count_total": int,
      "rings": [...]
    }
  },
  "strip_family_id": str,  # Primary family (kept for compatibility)
  "metadata": {
    "rosette_type": "traditional_spanish | herringbone | custom",
    "complexity": str,
    "fragility_score": float
  }
}
```

### **JobLog Extensions**

**Add rosette-specific job types:**
```python
{
  "job_id": str,
  "job_type": "rosette_slice_batch",  # NEW
  "pattern_id": str,
  "status": str,
  "parameters": {
    "rings_processed": int,
    "total_slices": int,
    "kerf_mm": float,
    "saw_blade_id": str
  },
  "results": {
    "tiles_generated": int,
    "actual_kerf_mm": float,
    "waste_percentage": float
  }
}
```

---

## 🔄 Migration Strategy

### **Phase 1: Core Geometry Engine (N11.0)**

**Add without breaking existing patterns:**
```python
# services/api/app/stores/pattern_store.py
class PatternStore:
    def get(self, pattern_id: str) -> dict:
        pattern = self.db.get(pattern_id)
        
        # Detect pattern type
        if pattern.get("pattern_type") == "rosette":
            # Return with rosette-specific fields
            return self._enrich_rosette_pattern(pattern)
        else:
            # Return standard pattern (backward compatible)
            return pattern
```

### **Phase 2: UI Integration (N11.1)**

**Add new route without disrupting existing views:**
```typescript
// packages/client/src/router/index.ts
{
  path: '/rmos/rosette-designer',
  name: 'RosetteDesigner',
  component: () => import('@/views/RosetteDesignerView.vue')
}
```

**Add navigation link:**
```vue
<!-- In RMOS navigation -->
<router-link to="/rmos/rosette-designer">
  Rosette Designer
</router-link>
```

### **Phase 3: Analytics Extension (N11.2)**

**Add rosette-specific analytics without breaking existing:**
```python
# services/api/app/api/routes/rmos_analytics_api.py
@router.get("/patterns/rosette/tile-distribution")
def get_rosette_tile_distribution():
    """New endpoint for rosette patterns only."""
    patterns = pattern_store.query(pattern_type="rosette")
    # ... rosette-specific analytics
    return distribution
```

---

## ✅ Integration Checklist

### **Backend Tasks**
- [ ] Create `services/api/app/cam/rosette/` module
- [ ] Implement `tile_segmentation.py` (algorithms from specs)
- [ ] Implement `kerf_compensation.py`
- [ ] Implement `herringbone.py` (angle calculations)
- [ ] Create `services/api/app/api/routes/rmos_rosette_api.py`
- [ ] Extend `PatternStore` with rosette type detection
- [ ] Add rosette job types to `JobLogStore`
- [ ] Create rosette-specific analytics endpoints

### **Frontend Tasks**
- [ ] Create `packages/client/src/stores/useRosetteDesignerStore.ts`
- [ ] Create `RosettePatternDesigner.vue` component
- [ ] Create `RingConfigPanel.vue` (per-ring params)
- [ ] Create `ColumnStripEditor.vue` (vertical editing)
- [ ] Create `TilePreviewCanvas.vue` (horizontal output)
- [ ] Add route `/rmos/rosette-designer`
- [ ] Update navigation to include Rosette Designer link

### **Data Migration Tasks**
- [ ] Add `pattern_type` field to patterns table (default "generic")
- [ ] Add `rosette_geometry` JSON column for extended data
- [ ] Create migration script to mark existing rosette patterns
- [ ] Test backward compatibility with non-rosette patterns

### **Testing Tasks**
- [ ] Unit tests for tile segmentation algorithms
- [ ] Unit tests for kerf compensation math
- [ ] Integration tests for pattern save/load
- [ ] UI tests for rosette designer
- [ ] End-to-end test: design → save → export → CAM

---

## 📚 Key References

**Current RMOS Docs:**
- `docs/RMOS_MASTER_TREE.md` - Development roadmap
- `docs/N9_0_ANALYTICS_QUICKREF.md` - Analytics architecture
- `docs/N10_2_APPRENTICESHIP_MODE_QUICKREF.md` - Safety system
- `projects/rmos/ARCHITECTURE.md` - Original RTL design

**Rosette Studio Specs (Archive):**
- `docs/specs/rmos_studio/RMOS_STUDIO_ALGORITHMS.md` - Tile segmentation math
- `docs/specs/rmos_studio/RMOS_STUDIO_SAW_PIPELINE.md` - Slicing operations
- `docs/specs/rmos_studio/RMOS_STUDIO_DATA_STRUCTURES.md` - Object schemas
- `docs/specs/rmos_studio/RMOS_STUDIO_MANUFACTURING_PLANNER.md` - Material calculations
- `docs/specs/rmos_studio/RMOS_STUDIO_CNC_EXPORT.md` - CNC toolpath generation, G-code export
- `docs/specs/rmos_studio/RMOS_STUDIO_VALIDATION.md` - Validation framework, constraint enforcement
- `docs/specs/rmos_studio/RMOS_STUDIO_DEVELOPER_GUIDE.md` - Developer integration, coding standards
- `docs/specs/rmos_studio/RMOS_STUDIO_OPERATIONS_GUIDE.md` - Shop-floor workflow, production procedures
- `docs/specs/rmos_studio/RMOS_STUDIO_USER_MANUAL.md` - End-user operating guide

**Implementation Files:**
- `services/api/app/stores/rmos_stores.py` - Current stores
- `services/api/app/api/routes/rmos_stores_api.py` - Current API
- `packages/client/src/stores/useRosettePatternStore.ts` - Existing pattern store
- `packages/client/src/stores/useStripFamilyStore.ts` - Existing strip families

---

## 🎯 Summary

**Current State (N8–N10):**
- ✅ SQLite-backed pattern/joblog/strip-family stores
- ✅ Analytics engine with 18 REST endpoints
- ✅ Safety policy system with apprentice/mentor modes
- ✅ Live monitoring with WebSocket events
- ✅ Export pipelines (PDF/JSON/G-code)

**Missing for Rosette Generator:**
- ❌ Visual pattern design UI
- ❌ Tile segmentation algorithms
- ❌ Kerf compensation math
- ❌ Herringbone/twist angle calculations
- ❌ Column → tile transformation logic

**Integration Approach:**
Create **N11 bundle** that extends existing RMOS infrastructure with rosette-specific features while maintaining backward compatibility with current pattern management system.

**Estimated Effort:** 2-3 bundles (N11.0, N11.1, N11.2) implementing ~15 new files and ~3,000 lines of code.
