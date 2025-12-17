# N11.1 — Rosette Pattern Scaffolding Quick Reference

**Bundle:** N11.1 (Drop-in Style)  
**Status:** ✅ Complete  
**Date:** November 30, 2025  
**Dependencies:** N8.6 (SQLite Stores), N9.0 (Analytics Engine)

---

## 🎯 Overview

N11.1 adds **RMOS Studio rosette pattern** storage and CRUD capabilities to the Luthier's Tool Box without breaking existing generic pattern functionality. This is the foundational scaffolding for the full RMOS Studio rosette designer (N11.2+).

**What's New:**
- ✅ SQL migration: `pattern_type` and `rosette_geometry` columns
- ✅ PatternStore: 4 rosette-specific methods
- ✅ JobLog: 6 rosette job type constants + creation helper
- ✅ API: 5 REST endpoints at `/api/rmos/patterns/rosette`
- ✅ Smoke test: 10 comprehensive validation cases

**Backward Compatibility:** 100% compatible with existing patterns (default `pattern_type='generic'`)

---

## 📦 Components

### **1. SQL Migration**

**File:** `migrations/patch_n11_rosette_scaffolding.sql`

```sql
-- Add pattern_type column (default 'generic' for existing patterns)
ALTER TABLE patterns ADD COLUMN pattern_type TEXT NOT NULL DEFAULT 'generic';

-- Add rosette_geometry JSON storage
ALTER TABLE patterns ADD COLUMN rosette_geometry TEXT;

-- Index for efficient filtering
CREATE INDEX idx_patterns_pattern_type ON patterns(pattern_type);
```

**Apply Migration:**
```powershell
# Using Alembic (if configured)
alembic upgrade head

# Or manually
sqlite3 your_database.db < migrations/patch_n11_rosette_scaffolding.sql
```

### **2. PatternStore Extensions**

**File:** `services/api/app/stores/sqlite_pattern_store.py`

**New Methods:**

```python
# Filter patterns by type
patterns = store.list_by_type('rosette')  # Returns only rosette patterns

# Create rosette pattern
pattern = store.create_rosette(
    pattern_id="rosette_001",
    name="Spanish Traditional 5-Ring",
    rosette_geometry={
        "rings": [
            {
                "ring_id": 1,
                "radius_mm": 40.0,
                "width_mm": 3.0,
                "tile_length_mm": 2.5,
                "twist_angle_deg": 0.0,
                "slice_angle_deg": 0.0,
                "column": {
                    "strips": [
                        {"width_mm": 1.0, "color": "maple", "material_id": "wood_001"}
                    ]
                }
            }
        ],
        "segmentation": {"tile_count_total": 94}
    },
    metadata={"complexity": "medium", "fragility_score": 0.42}
)

# Update rosette geometry only
updated = store.update_rosette_geometry(
    pattern_id="rosette_001",
    rosette_geometry={
        "rings": [...],  # Updated ring definitions
        "segmentation": {...}
    }
)

# Get geometry field only (lightweight)
geometry = store.get_rosette_geometry("rosette_001")
```

### **3. JobLog Extensions**

**File:** `services/api/app/stores/sqlite_joblog_store.py`

**New Constants:**

```python
JOB_TYPE_ROSETTE_SLICE_BATCH = "rosette_slice_batch"
JOB_TYPE_ROSETTE_PATTERN_GENERATION = "rosette_pattern_generation"
JOB_TYPE_ROSETTE_PREVIEW = "rosette_preview"
JOB_TYPE_ROSETTE_CNC_EXPORT = "rosette_cnc_export"
JOB_TYPE_ROSETTE_SEGMENTATION = "rosette_segmentation"
JOB_TYPE_ROSETTE_VALIDATION = "rosette_validation"
```

**New Method:**

```python
# Create rosette job entry
job = joblog_store.create_rosette_job(
    job_type=JOB_TYPE_ROSETTE_PATTERN_GENERATION,
    pattern_id="rosette_001",
    parameters={
        "ring_count": 5,
        "tile_count": 94,
        "complexity": "medium"
    },
    status="completed"
)

# Job ID format: JOB-ROSETTE-20251130-143052-abc123
```

### **4. REST API Endpoints**

**Base Path:** `/api/rmos/patterns/rosette`  
**Router File:** `services/api/app/api/routes/rmos_pattern_api.py`

#### **POST `/api/rmos/patterns/rosette`**
Create new rosette pattern.

**Request:**
```json
{
  "pattern_id": "rosette_001",
  "name": "Spanish Traditional 5-Ring",
  "rosette_geometry": {
    "rings": [
      {
        "ring_id": 1,
        "radius_mm": 40.0,
        "width_mm": 3.0,
        "tile_length_mm": 2.5,
        "twist_angle_deg": 0.0,
        "slice_angle_deg": 0.0,
        "column": {
          "strips": [
            {
              "width_mm": 1.0,
              "color": "maple",
              "material_id": "wood_maple_001"
            }
          ]
        }
      }
    ],
    "segmentation": {
      "tile_count_total": 94
    }
  },
  "metadata": {
    "complexity": "medium",
    "fragility_score": 0.42,
    "rosette_type": "traditional_spanish"
  }
}
```

**Response:** `200 OK`
```json
{
  "pattern_id": "rosette_001",
  "name": "Spanish Traditional 5-Ring",
  "pattern_type": "rosette",
  "ring_count": 1,
  "rosette_geometry": { ... },
  "metadata": { ... },
  "created_at": "2025-11-30T14:30:52Z",
  "updated_at": "2025-11-30T14:30:52Z"
}
```

**Errors:**
- `409 Conflict` - Pattern ID already exists
- `400 Bad Request` - Invalid geometry structure (missing 'rings' array)

---

#### **GET `/api/rmos/patterns/rosette`**
List all rosette patterns.

**Response:** `200 OK`
```json
[
  {
    "pattern_id": "rosette_001",
    "name": "Spanish Traditional 5-Ring",
    "pattern_type": "rosette",
    "ring_count": 1,
    "rosette_geometry": { ... },
    "metadata": { ... },
    "created_at": "2025-11-30T14:30:52Z",
    "updated_at": "2025-11-30T14:30:52Z"
  }
]
```

---

#### **GET `/api/rmos/patterns/rosette/{pattern_id}`**
Get specific rosette pattern by ID.

**Response:** `200 OK`
```json
{
  "pattern_id": "rosette_001",
  "name": "Spanish Traditional 5-Ring",
  "pattern_type": "rosette",
  "ring_count": 1,
  "rosette_geometry": { ... },
  "metadata": { ... },
  "created_at": "2025-11-30T14:30:52Z",
  "updated_at": "2025-11-30T14:30:52Z"
}
```

**Errors:**
- `404 Not Found` - Pattern doesn't exist
- `400 Bad Request` - Pattern exists but is not a rosette type

---

#### **PATCH `/api/rmos/patterns/rosette/{pattern_id}/geometry`**
Update rosette geometry only.

**Request:**
```json
{
  "rosette_geometry": {
    "rings": [ ... ],
    "segmentation": { ... }
  }
}
```

**Response:** `200 OK`
```json
{
  "pattern_id": "rosette_001",
  "name": "Spanish Traditional 5-Ring",
  "pattern_type": "rosette",
  "rosette_geometry": { ... },
  "updated_at": "2025-11-30T14:35:00Z"
}
```

**Errors:**
- `404 Not Found` - Pattern doesn't exist

---

#### **GET `/api/rmos/patterns/rosette/{pattern_id}/geometry`**
Get rosette geometry field only (lightweight).

**Response:** `200 OK`
```json
{
  "rings": [
    {
      "ring_id": 1,
      "radius_mm": 40.0,
      "width_mm": 3.0,
      "tile_length_mm": 2.5,
      "twist_angle_deg": 0.0,
      "slice_angle_deg": 0.0,
      "column": { ... }
    }
  ],
  "segmentation": {
    "tile_count_total": 94
  }
}
```

**Errors:**
- `404 Not Found` - Pattern not found or has no rosette_geometry

---

## 🧪 Testing

### **Run Smoke Tests**

**Prerequisites:**
```powershell
# Start API server
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Execute Tests:**
```powershell
cd tests
.\test_n11_rosette_scaffolding.ps1
```

**Expected Output:**
```
========================================
  N11.1 Rosette Scaffolding Smoke Test
========================================

[Test 1] Create Rosette Pattern via API
✓ Pattern created with correct ID
✓ Pattern type set to 'rosette'
✓ Ring count correct (2 rings)
✓ rosette_geometry field present
✓ Geometry rings array preserved

[Test 2] List Rosette Patterns
✓ List endpoint returns array
✓ At least one rosette pattern exists
✓ Test pattern found in list
✓ List filters by pattern_type='rosette'

[Test 3] Get Rosette Pattern by ID
✓ GET returns correct pattern
✓ Pattern type verified
✓ Geometry field present
✓ Metadata preserved

[Test 4] Get Rosette Geometry (geometry-only endpoint)
✓ Geometry has rings array
✓ Correct number of rings
✓ Ring 1 radius correct
✓ Ring 2 radius correct
✓ Segmentation field present

[Test 5] Update Rosette Geometry (PATCH)
✓ Geometry updated (radius)
✓ Geometry updated (width)
✓ Segmentation updated

[Test 6] Validate Pattern Type Filtering
✓ Generic pattern NOT in rosette list
✓ Rosette pattern IS in rosette list

[Test 7] Error Handling - Duplicate Pattern ID (HTTP 409)
✓ HTTP 409 returned for duplicate pattern ID

[Test 8] Error Handling - Invalid Geometry Structure (HTTP 400)
✓ HTTP 400 returned for invalid geometry structure

[Test 9] Error Handling - Pattern Not Found (HTTP 404)
✓ HTTP 404 returned for nonexistent pattern

[Test 10] JobLog Integration - Rosette Job Created
✓ Rosette job created in JobLog
✓ Job linked to correct pattern
✓ Job status is 'completed'

========================================
  Test Results Summary
========================================
  Passed: 31
  Failed: 0
  Total:  31

✓ All N11.1 scaffolding tests passed!
```

### **Test Coverage**

| Test Case | Coverage |
|-----------|----------|
| Test 1 | POST endpoint, pattern creation, field validation |
| Test 2 | GET list endpoint, pattern_type filtering |
| Test 3 | GET by ID endpoint, full pattern retrieval |
| Test 4 | GET geometry endpoint, lightweight fetch |
| Test 5 | PATCH endpoint, geometry updates |
| Test 6 | Pattern type isolation (rosette vs generic) |
| Test 7 | HTTP 409 error handling (duplicate ID) |
| Test 8 | HTTP 400 error handling (invalid geometry) |
| Test 9 | HTTP 404 error handling (not found) |
| Test 10 | JobLog integration (rosette job creation) |

---

## 📊 Data Structures

### **Rosette Geometry Schema**

```typescript
interface RosetteGeometry {
  rings: RosetteRing[]
  segmentation: {
    tile_count_total: number
    tile_count_per_ring?: number[]
  }
}

interface RosetteRing {
  ring_id: number
  radius_mm: number
  width_mm: number
  tile_length_mm: number
  twist_angle_deg: number
  slice_angle_deg: number
  column: {
    strips: Strip[]
  }
}

interface Strip {
  width_mm: number
  color: string
  material_id: string
}
```

### **Pattern Response Schema**

```typescript
interface RosettePattern {
  pattern_id: string
  name: string
  pattern_type: 'rosette'
  ring_count: number
  rosette_geometry: RosetteGeometry | null
  metadata: {
    complexity?: string
    fragility_score?: number
    rosette_type?: string
    [key: string]: any
  }
  created_at: string  // ISO 8601 timestamp
  updated_at: string  // ISO 8601 timestamp
}
```

---

## 🔧 Usage Examples

### **Example 1: Create Simple 3-Ring Rosette**

```typescript
const response = await fetch('/api/rmos/patterns/rosette', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    pattern_id: 'rosette_simple_001',
    name: 'Simple 3-Ring Test',
    rosette_geometry: {
      rings: [
        {
          ring_id: 1,
          radius_mm: 30.0,
          width_mm: 2.5,
          tile_length_mm: 2.0,
          twist_angle_deg: 0.0,
          slice_angle_deg: 0.0,
          column: {
            strips: [
              {width_mm: 1.0, color: 'maple', material_id: 'maple_001'}
            ]
          }
        },
        {
          ring_id: 2,
          radius_mm: 32.5,
          width_mm: 2.0,
          tile_length_mm: 2.0,
          twist_angle_deg: 5.0,
          slice_angle_deg: 0.0,
          column: {
            strips: [
              {width_mm: 1.0, color: 'walnut', material_id: 'walnut_001'}
            ]
          }
        },
        {
          ring_id: 3,
          radius_mm: 34.5,
          width_mm: 2.5,
          tile_length_mm: 2.0,
          twist_angle_deg: 0.0,
          slice_angle_deg: 0.0,
          column: {
            strips: [
              {width_mm: 1.0, color: 'cherry', material_id: 'cherry_001'}
            ]
          }
        }
      ],
      segmentation: {
        tile_count_total: 141
      }
    },
    metadata: {
      complexity: 'low',
      fragility_score: 0.25,
      rosette_type: 'simple_test'
    }
  })
})

const pattern = await response.json()
console.log('Created rosette:', pattern.pattern_id)
```

### **Example 2: Update Rosette Geometry**

```typescript
// Fetch current pattern
const current = await fetch('/api/rmos/patterns/rosette/rosette_simple_001')
  .then(r => r.json())

// Modify geometry
current.rosette_geometry.rings[0].radius_mm = 35.0
current.rosette_geometry.rings[0].width_mm = 3.0

// Update via PATCH
const updated = await fetch(
  '/api/rmos/patterns/rosette/rosette_simple_001/geometry',
  {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      rosette_geometry: current.rosette_geometry
    })
  }
).then(r => r.json())

console.log('Updated radius:', updated.rosette_geometry.rings[0].radius_mm)
```

### **Example 3: List and Filter Rosette Patterns**

```typescript
// Get all rosette patterns
const rosettes = await fetch('/api/rmos/patterns/rosette')
  .then(r => r.json())

// Filter by complexity
const simpleRosettes = rosettes.filter(p => 
  p.metadata?.complexity === 'low'
)

console.log(`Found ${simpleRosettes.length} simple rosettes`)
```

---

## 🚀 Integration Points

### **N11.2: Geometry Engine (Next Bundle)**

N11.2 will add:
- `/api/rmos/rosette/segment-ring` - Ring segmentation algorithm
- `/api/rmos/rosette/generate-slices` - Tile slice generation
- `cam/rosette/` backend package skeleton

**Example N11.2 Flow:**
```typescript
// 1. Create pattern (N11.1)
const pattern = await createRosettePattern(...)

// 2. Segment rings (N11.2)
const segmentation = await fetch('/api/rmos/rosette/segment-ring', {
  method: 'POST',
  body: JSON.stringify({
    pattern_id: pattern.pattern_id,
    ring_id: 1
  })
}).then(r => r.json())

// 3. Generate slices (N11.2)
const slices = await fetch('/api/rmos/rosette/generate-slices', {
  method: 'POST',
  body: JSON.stringify({
    pattern_id: pattern.pattern_id,
    segmentation_result: segmentation
  })
}).then(r => r.json())

// 4. Update pattern with slice data (N11.1)
await updateRosetteGeometry(pattern.pattern_id, {
  rings: pattern.rosette_geometry.rings,
  segmentation: {
    ...pattern.rosette_geometry.segmentation,
    slices: slices.slices
  }
})
```

### **N11.3: Pinia Store + UI Components (Future)**

N11.3 will add:
- `useRosetteDesignerStore.ts` - Pinia store for rosette state
- `RosetteDesigner.vue` - Main UI component
- `RosetteRingEditor.vue` - Ring parameter controls

**Example N11.3 Integration:**
```typescript
// stores/useRosetteDesignerStore.ts
import { defineStore } from 'pinia'

export const useRosetteDesignerStore = defineStore('rosetteDesigner', {
  state: () => ({
    patterns: [] as RosettePattern[],
    currentPattern: null as RosettePattern | null
  }),
  
  actions: {
    async loadPatterns() {
      const response = await fetch('/api/rmos/patterns/rosette')
      this.patterns = await response.json()
    },
    
    async createPattern(payload: RosettePatternCreateRequest) {
      const response = await fetch('/api/rmos/patterns/rosette', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
      const newPattern = await response.json()
      this.patterns.push(newPattern)
      this.currentPattern = newPattern
    },
    
    async updateGeometry(patternId: string, geometry: RosetteGeometry) {
      const response = await fetch(
        `/api/rmos/patterns/rosette/${patternId}/geometry`,
        {
          method: 'PATCH',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ rosette_geometry: geometry })
        }
      )
      const updated = await response.json()
      
      // Update local state
      const index = this.patterns.findIndex(p => p.pattern_id === patternId)
      if (index !== -1) {
        this.patterns[index] = updated
      }
      if (this.currentPattern?.pattern_id === patternId) {
        this.currentPattern = updated
      }
    }
  }
})
```

---

## 🐛 Troubleshooting

### **Issue: HTTP 409 on pattern creation**
**Cause:** Pattern ID already exists  
**Solution:** Use unique pattern_id or query existing patterns first

```typescript
// Check if pattern exists before creating
const existing = await fetch('/api/rmos/patterns/rosette/my_pattern_id')
if (existing.status === 404) {
  // Safe to create
  await createRosettePattern(...)
}
```

### **Issue: HTTP 400 "must contain 'rings' array"**
**Cause:** Invalid rosette_geometry structure  
**Solution:** Ensure geometry has required `rings` array

```typescript
// ✗ Invalid
const invalid = {
  rosette_geometry: {
    segmentation: { tile_count_total: 50 }
    // Missing 'rings' array
  }
}

// ✓ Valid
const valid = {
  rosette_geometry: {
    rings: [],  // Must be present (can be empty array)
    segmentation: { tile_count_total: 50 }
  }
}
```

### **Issue: Generic pattern appears in rosette list**
**Cause:** Pattern created with wrong endpoint  
**Solution:** Use `/api/rmos/patterns/rosette` for rosette patterns, `/api/rmos/patterns` for generic

```typescript
// ✗ Wrong - creates generic pattern
await fetch('/api/rmos/patterns', {...})

// ✓ Correct - creates rosette pattern
await fetch('/api/rmos/patterns/rosette', {...})
```

### **Issue: Geometry not updating**
**Cause:** Using wrong HTTP method  
**Solution:** Use `PATCH` for updates, not `PUT` or `POST`

```typescript
// ✗ Wrong
await fetch('/api/rmos/patterns/rosette/id/geometry', {
  method: 'POST',  // Wrong method
  body: ...
})

// ✓ Correct
await fetch('/api/rmos/patterns/rosette/id/geometry', {
  method: 'PATCH',  // Correct method
  body: ...
})
```

---

## ✅ Validation Checklist

**Before deploying N11.1:**

- [x] SQL migration file created and syntax-validated
- [x] PatternStore methods tested with sample data
- [x] JobLog methods tested with rosette job types
- [x] API endpoints registered in `main.py`
- [x] Router imports use try/except for graceful degradation
- [x] Smoke test script runs without errors
- [x] All 10 test cases pass (31 assertions)
- [x] Error handling validated (409/400/404 responses)
- [x] Backward compatibility verified (generic patterns unaffected)
- [x] Documentation complete with usage examples

**Post-deployment verification:**

```powershell
# 1. Verify server starts without errors
cd services/api
uvicorn app.main:app --reload

# 2. Check router registration
# Look for: "N11.1 — RMOS Rosette Pattern API" in startup logs

# 3. Run smoke tests
cd ../../tests
.\test_n11_rosette_scaffolding.ps1

# 4. Check API docs
# Visit: http://localhost:8000/docs
# Verify: /api/rmos/patterns/rosette endpoints appear in Swagger UI
```

---

## 📚 See Also

- [RMOS N8-N10 Architecture](./RMOS_N8_N10_ARCHITECTURE.md) - Current RMOS implementation overview
- [RMOS Studio Specifications](./specs/rmos_studio/README.md) - Full rosette algorithm specs
- [N11 Rosette Scaffolding Plan](./N11_ROSETTE_SCAFFOLDING_PLAN.md) - Complete N11 bundle roadmap
- [RMOS Master Tree](./RMOS_MASTER_TREE.md) - RMOS feature hierarchy

---

## 🎯 Next Steps: N11.2

**N11.2 Bundle: Geometry Engine**

Components:
1. `/api/rmos/rosette/segment-ring` endpoint
2. `/api/rmos/rosette/generate-slices` endpoint
3. `cam/rosette/` backend package with algorithms:
   - `tile_segmentation.py`
   - `slice_generator.py`
   - `herringbone_calculator.py`
4. Smoke test: `test_n11_geometry_engine.ps1`

**N11.2 Prerequisites:**
- N11.1 deployed and tested ✅
- RMOS Studio algorithm specs reviewed (see `docs/specs/rmos_studio/`)
- Python geometry libraries available: `shapely`, `numpy`, `scipy`

---

**Status:** ✅ N11.1 Bundle Complete  
**Next:** N11.2 (Geometry Engine)  
**Final Goal:** Full RMOS Studio rosette designer integrated into Luthier's Tool Box
