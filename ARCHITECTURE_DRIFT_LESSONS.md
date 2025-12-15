# Architecture Drift Lessons — Wave E1 Case Study

**Date:** December 10, 2025  
**Branch:** feature/client-migration  
**Context:** Post-implementation analysis of Wave E1 RMOS patterns router fix

---

## 🎯 Executive Summary

**Problem:** Wave E1 specification assumed in-memory dictionary storage, but N11.2 had already migrated to SQLite with class-based stores. Implementation followed the spec literally, resulting in runtime crashes.

**Root Cause:** **Architecture drift without specification updates** — the data model shifted from dict → SQLite class between spec authorship and implementation.

**Resolution:** Reverse-engineered actual store API and rewrote all 5 CRUD endpoints to use `SQLitePatternStore` methods instead of dictionary operations.

**Impact:** 5 files created, 3 files modified, all endpoints now operational with database persistence.

---

## 📚 The Seven Lessons

### **Lesson 1: Specifications Lie When Architecture Evolves**

#### **The Problem**

Wave E1 spec (written during dict-store era):
```python
# Wave E1 specification expected this:
stores = get_rmos_stores()
patterns: List[RosettePattern] = stores.get("patterns", [])  # Treat as dict
```

Actual repository (N11.2 migration completed):
```python
# services/api/app/stores/rmos_stores.py (lines 15-52)
class RMOSStores:
    """
    Factory for RMOS store access.
    
    Provides singleton instances of all stores with shared database connection.
    """
    
    def __init__(self, db: Optional[RMOSDatabase] = None):
        self._db = db or get_rmos_db()
        self._patterns: Optional[SQLitePatternStore] = None
        # ... more stores
    
    @property
    def patterns(self) -> SQLitePatternStore:
        """Get pattern store instance."""
        if self._patterns is None:
            self._patterns = SQLitePatternStore(self._db)
        return self._patterns
```

**Result:** `AttributeError: 'RMOSStores' object has no attribute 'get'`

#### **How to Detect This**

**Before implementing ANY spec, run:**
```powershell
# Check what get_rmos_stores() actually returns
cd services/api
python -c "from app.stores.rmos_stores import get_rmos_stores; stores = get_rmos_stores(); print(type(stores)); print(dir(stores))"

# Expected output for N11.2:
# <class 'app.stores.rmos_stores.RMOSStores'>
# ['patterns', 'joblogs', 'strip_families', ...]  # NOT 'get', 'setdefault'
```

#### **The Fix**

**Before (spec-based, broken):**
```python
# services/api/app/routers/rmos_patterns_router.py (WRONG)
@router.get("/", response_model=List[RosettePattern])
async def list_patterns() -> List[RosettePattern]:
    stores = get_rmos_stores()
    patterns: List[RosettePattern] = stores.get("patterns", [])  # ❌ Crashes
    return patterns
```

**After (reality-based, working):**
```python
# services/api/app/routers/rmos_patterns_router.py (FIXED)
@router.get("/", response_model=List[RosettePattern])
async def list_patterns() -> List[RosettePattern]:
    stores = get_rmos_stores()
    pattern_dicts = stores.patterns.list_all()  # ✅ Uses actual API
    patterns = [RosettePattern(**p) for p in pattern_dicts]
    return patterns
```

---

### **Lesson 2: Integration Tests Reveal Architecture Reality**

#### **The Problem**

Without integration tests, specs become the **only source of truth**. But specs can be outdated.

#### **Real Example from ROSETTE_ROUTER_TEST_BUNDLE_SUMMARY.md**

```python
# services/api/app/tests/rmos/test_rosette_patterns_router.py
def test_list_patterns_initially_empty(test_client):
    """Verifies /api/rmos/patterns responds with 200."""
    response = test_client.get("/api/rmos/patterns")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_rosette_pattern_and_fetch(test_client):
    """Creates pattern with pattern_type='rosette', verifies storage and retrieval."""
    payload = {
        "pattern_id": "test-rosette-001",
        "pattern_name": "Test Rosette",
        "pattern_type": "rosette",  # ✅ Tests N11.2 schema
        "outer_radius_mm": 50.0,
        # ...
    }
    response = test_client.post("/api/rmos/patterns", json=payload)
    assert response.status_code == 200
    
    # Verify it was actually saved to database
    fetch_response = test_client.get("/api/rmos/patterns/test-rosette-001")
    assert fetch_response.json()["pattern_type"] == "rosette"
```

**What this test would have caught:**
- ✅ Database has `pattern_type` column (N11.2 schema applied)
- ✅ Store returns `SQLitePatternStore` class (not dict)
- ✅ Endpoint uses correct URL `/api/rmos/patterns` (not `/api/rosette-patterns`)
- ✅ Data actually persists to SQLite (not in-memory)

#### **How to Use This**

**Before implementing Wave E1, run:**
```powershell
cd services/api
pytest app/tests/rmos/test_rosette_patterns_router.py -v

# If tests pass: Infrastructure is ready, spec might be wrong
# If tests fail: Infrastructure needs fixing, spec might be right
# If tests don't exist: CREATE THEM FIRST
```

---

### **Lesson 3: Database Schema Tells the Truth**

#### **The Problem**

Specs assume a schema, but migrations happen without updating specs.

#### **Real Example: N11.2 Schema Migration**

**Spec assumption (Wave E1):**
```python
# Spec assumed patterns table had only basic fields
{
    "id": "pattern-001",
    "name": "Celtic Rosette",
    "ring_count": 5
}
```

**Actual schema (N11.2 applied):**
```python
# services/api/app/core/rmos_db.py (lines 48-60)
CREATE TABLE IF NOT EXISTS patterns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    ring_count INTEGER NOT NULL,
    geometry_json TEXT,
    strip_family_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT,
    pattern_type TEXT NOT NULL DEFAULT 'generic',      -- ✅ N11.1 addition
    rosette_geometry TEXT,                             -- ✅ N11.1 addition
    FOREIGN KEY (strip_family_id) REFERENCES strip_families(id)
)

-- Index for pattern_type queries
CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type 
ON patterns(pattern_type)
```

#### **How to Verify Schema Before Implementation**

```powershell
cd services/api

# Method 1: Read schema initialization
grep -A 20 "CREATE TABLE.*patterns" app/core/rmos_db.py

# Method 2: Inspect live database
python -c "
import sqlite3
conn = sqlite3.connect('data/rmos.db')
cursor = conn.execute('PRAGMA table_info(patterns)')
for row in cursor:
    print(row)
"

# Expected output for N11.2:
# (0, 'id', 'TEXT', 0, None, 1)
# (1, 'name', 'TEXT', 1, None, 0)
# ...
# (8, 'pattern_type', 'TEXT', 1, "'generic'", 0)  # ✅ Column exists
# (9, 'rosette_geometry', 'TEXT', 0, None, 0)     # ✅ Column exists
```

#### **The Fix Pattern**

```python
# services/api/app/routers/rmos_patterns_router.py (create endpoint)
@router.post("/", response_model=RosettePattern)
async def create_pattern(pattern: RosettePattern) -> RosettePattern:
    stores = get_rmos_stores()
    
    # Convert Pydantic model to dict for storage
    pattern_dict = pattern.dict()
    pattern_dict['id'] = pattern_dict.pop('pattern_id')
    pattern_dict['pattern_type'] = 'rosette'          # ✅ Use N11.2 field
    pattern_dict['geometry_json'] = '{}'
    pattern_dict['metadata_json'] = pattern_dict.get('metadata', {})
    
    # Create in database using N11.2 schema
    created = stores.patterns.create(pattern_dict)
    
    # Convert back to Pydantic model
    created['pattern_id'] = created.pop('id')
    return RosettePattern(**created)
```

---

### **Lesson 4: Store API Documentation Lives in Code, Not Specs**

#### **The Problem**

Specs document **what should exist**, not **what actually exists**. The real API contract is in the store implementation.

#### **Real Example: SQLitePatternStore API**

**Spec assumed (Wave E1):**
```python
# Spec said: "Use in-memory dict store"
patterns = stores.get("patterns", [])
patterns.append(new_pattern)
```

**Actual API (services/api/app/stores/sqlite_pattern_store.py):**
```python
# Lines 103-168 show the REAL API

class SQLitePatternStore(SQLiteStoreBase):
    
    # ✅ Actual methods available:
    def list_all(self) -> List[Dict[str, Any]]:
        """List all patterns."""
        pass
    
    def get_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get pattern by ID."""
        pass
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new pattern."""
        pass
    
    def update(self, pattern_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing pattern."""
        pass
    
    def delete(self, pattern_id: str) -> bool:
        """Delete pattern by ID."""
        pass
    
    # ✅ N11.1 rosette-specific methods:
    def list_by_type(self, pattern_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List patterns filtered by pattern_type."""
        pass
    
    def create_rosette(
        self,
        pattern_id: str,
        name: str,
        rosette_geometry: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new RMOS Studio rosette pattern."""
        pass
```

#### **How to Discover Store API**

```powershell
cd services/api

# Read the actual store implementation
cat app/stores/sqlite_pattern_store.py | grep "def " | head -20

# Expected output:
# def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
# def _dict_to_row_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
# def get_by_strip_family(self, strip_family_id: str) -> List[Dict[str, Any]]:
# def search_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
# def list_by_type(self, pattern_type: Optional[str] = None) -> List[Dict[str, Any]]:
# def create_rosette(...) -> Dict[str, Any]:
```

#### **Correct Implementation Pattern**

```python
# services/api/app/routers/rmos_patterns_router.py

# ✅ List all patterns
@router.get("/", response_model=List[RosettePattern])
async def list_patterns():
    stores = get_rmos_stores()
    pattern_dicts = stores.patterns.list_all()  # Uses actual API
    return [RosettePattern(**p) for p in pattern_dicts]

# ✅ Get one pattern
@router.get("/{pattern_id}", response_model=RosettePattern)
async def get_pattern(pattern_id: str):
    stores = get_rmos_stores()
    pattern_dict = stores.patterns.get_by_id(pattern_id)  # Uses actual API
    if not pattern_dict:
        raise HTTPException(404, detail=f"Pattern {pattern_id} not found")
    pattern_dict['pattern_id'] = pattern_dict.pop('id')
    return RosettePattern(**pattern_dict)

# ✅ Create pattern
@router.post("/", response_model=RosettePattern)
async def create_pattern(pattern: RosettePattern):
    stores = get_rmos_stores()
    existing = stores.patterns.get_by_id(pattern.pattern_id)  # Check existence
    if existing:
        raise HTTPException(400, detail="Pattern already exists")
    
    pattern_dict = pattern.dict()
    pattern_dict['id'] = pattern_dict.pop('pattern_id')
    pattern_dict['pattern_type'] = 'rosette'
    created = stores.patterns.create(pattern_dict)  # Uses actual API
    
    created['pattern_id'] = created.pop('id')
    return RosettePattern(**created)
```

---

### **Lesson 5: Architecture Decision Records Prevent Rework**

#### **The Problem**

Without documented decisions, every new implementation rediscovers "why did we choose this pattern?"

#### **Real Example: Phase E Export Architecture Decision**

**From PHASE_D_E_DECISIONS.md:**

> **Question:** Keep coupled in `fret_slots_cam.py` OR extract to `fret_slots_export.py` OR enhance existing?
>
> **Recommendation:** 🎯 **Option C: Enhance existing with internal structure**
>
> **Rationale:**
> - Current `fret_slots_cam.py` is 912 lines (not huge yet)
> - Export logic is already embedded
> - Extraction would require major refactor
> - Internal layering provides clarity without file split
>
> **Decision:** Extract only if exceeds 1500 lines

**Code Location:**
```python
# services/api/app/calculators/fret_slots_cam.py
# Current structure (as of Wave 19):

# Layer 1: Pure geometry calculation
def compute_fret_slots_for_model(
    model_id: str,
    mode: Literal["straight", "fan_fret"],
    fret_count: int,
    slot_depth_mm: float,
) -> List[FretSlotToolpath]:
    """Pure geometry computation, no export logic."""
    pass

# Layer 2: Export helpers (internal)
def _generate_dxf_r12(slots: List[FretSlotToolpath]) -> str:
    """DXF R12 export (existing)."""
    pass

def _generate_gcode_for_post(
    slots: List[FretSlotToolpath],
    post_id: str,
    params: FretSlotsGcodeParams,
) -> str:
    """G-code export with post-processor awareness."""
    pass

# Layer 3: Public API (FastAPI endpoints in router)
```

**Why This Decision Matters for Wave E1:**

If we had this ADR for RMOS stores, it would say:

> **Decision (N11.2):** Migrate from in-memory dict to SQLite class-based stores
>
> **Breaking Changes:**
> - `stores.get("patterns", [])` → `stores.patterns.list_all()`
> - `stores.setdefault("patterns", [])` → `stores.patterns.create()`
> - All future routers MUST use `SQLitePatternStore` API
>
> **Migration Guide:** See PATCH_N11_SCHEMA_FIX.md

**If this existed, Wave E1 spec would have been flagged as outdated immediately.**

---

### **Lesson 6: Version Tagging Prevents "Which Era?" Confusion**

#### **The Problem**

PHASE_D_E_DECISIONS.md discovered:

> **Phases B, C, and Wave 15 are already implemented** at Wave 17-19 maturity level. **The uploads represent earlier iterations.**

**Wave E1 had the same issue:**
- Spec written: Dict-store era (pre-N11.2)
- Implementation happened: SQLite-store era (post-N11.2)
- No version tag to indicate mismatch

#### **Solution: Spec Header Template**

```markdown
# Wave E1: RMOS Patterns Router

**Spec Version:** E1.2
**Target Codebase Version:** Post-N11.2 (SQLite stores)
**Supersedes:** E1.0 (dict stores), E1.1 (mixed)

**Prerequisites:**
- ✅ N11.2 database schema applied (SCHEMA_VERSION = 2)
- ✅ RMOSStores class exists in `stores/rmos_stores.py`
- ✅ SQLitePatternStore implements: list_all(), create(), get_by_id(), update(), delete()
- ✅ Database has `pattern_type` and `rosette_geometry` columns

**Compatibility Check:**
```powershell
# Verify prerequisites before implementing
cd services/api
python -c "
from app.stores.rmos_stores import get_rmos_stores
stores = get_rmos_stores()
assert hasattr(stores, 'patterns'), 'RMOSStores missing patterns property'
assert hasattr(stores.patterns, 'list_all'), 'SQLitePatternStore missing list_all()'
print('✅ All prerequisites met')
"
```

**API Contract (Current Era):**
```python
# services/api/app/routers/rmos_patterns_router.py

# ✅ CORRECT for N11.2 era:
stores = get_rmos_stores()
patterns = stores.patterns.list_all()

# ❌ WRONG (pre-N11.2 era):
stores = get_rmos_stores()
patterns = stores.get("patterns", [])
```
```

#### **How to Add Version Tags to Existing Specs**

```powershell
# Audit all spec files for version tags
cd "c:\Users\thepr\Downloads\Luthiers ToolBox"
grep -L "Spec Version:" *.md Wave*.txt Phase*.txt

# Add version headers to files missing them
```

---

### **Lesson 7: Gap Analysis Before Implementation**

#### **The Problem**

Implementing specs without checking what's already done leads to:
- Duplicate code (reimplementing existing features)
- Breaking changes (overwriting evolved implementations)
- Integration failures (mismatched interfaces)

#### **Real Example: WAVE16_PHASE_D_GAP_ANALYSIS.md**

**Before implementing Wave 16 visualization, the gap analysis found:**

```markdown
#### ✅ What's Implemented (Backend)

**Backend (`services/api/app/routers/cam_fret_slots_router.py`):**
- ✅ Fan-fret mode support: `mode: 'standard' | 'fan'`
- ✅ Treble/bass scale parameters
- ✅ Per-fret risk calculation via `evaluate_per_fret_feasibility()`
- ✅ Response includes `per_fret_risks` array
- ✅ Response includes `risk_summary` with green/yellow/red counts

**Frontend Controls:**
- ✅ Store: `fanFretEnabled` toggle
- ✅ Store: `trebleScaleLength`, `bassScaleLength`, `perpendicularFret` states
- ✅ Panel: Fan-fret checkbox and input controls

#### ❌ What's Missing (Frontend Visualization)

- ❌ TypeScript types: `RiskLevel`, `PerFretDiagnostic`
- ❌ Store state: `perFretDiagnostics` array
- ❌ Canvas rendering: Color-coded risk display
- ❌ Legend widget: Risk level explanation
```

**Code Evidence:**

```typescript
// packages/client/src/stores/instrumentGeometryStore.ts

// ✅ IMPLEMENTED (inputs)
export const useInstrumentGeometryStore = defineStore('instrumentGeometry', {
  state: () => ({
    // ... other state
    fanFretEnabled: false,              // ✅ Exists (line 147)
    trebleScaleLength: 648,             // ✅ Exists (line 148)
    bassScaleLength: 660,               // ✅ Exists (line 149)
    perpendicularFret: 8,               // ✅ Exists (line 150)
  }),
  
  actions: {
    async previewFrets() {
      const payload = {
        // ...
        fan_fret_enabled: this.fanFretEnabled,  // ✅ Sent to API (line 263)
        treble_scale: this.trebleScaleLength,   // ✅ Sent to API (line 264)
        bass_scale: this.bassScaleLength,       // ✅ Sent to API (line 265)
        perpendicular_fret: this.perpendicularFret, // ✅ Sent to API (line 266)
      }
      const response = await api.post('/cam/fret_slots/preview', payload)
      // ❌ MISSING: No extraction of per_fret_risks from response
      // ❌ MISSING: No storage of risk diagnostics
    }
  }
})
```

**What Gap Analysis Prevents:**

Without this analysis, you might:
- ❌ Reimplement backend risk calculation (already done)
- ❌ Create new API endpoint (already exists)
- ❌ Waste time debugging "why isn't risk data available" (it is, just not extracted)

**With gap analysis, you know:**
- ✅ Backend is complete → Focus on frontend only
- ✅ API contract is known → Just extract `per_fret_risks` field
- ✅ Data is flowing → Just add TypeScript types and rendering

---

## 🛠️ Practical Checklist for Future Implementations

### **Phase 1: Specification Validation (Before Writing Code)**

```powershell
# 1. Check codebase version vs spec version
grep "Spec Version:" <spec_file.md>
grep "SCHEMA_VERSION\|VERSION\|version" services/api/app/**/*.py

# 2. Verify dependencies exist
cd services/api
python -c "
# Example: Verify stores for Wave E1
from app.stores.rmos_stores import get_rmos_stores
stores = get_rmos_stores()
print(f'Store type: {type(stores)}')
print(f'Available stores: {[s for s in dir(stores) if not s.startswith(\"_\")]}')
"

# 3. Check database schema matches spec assumptions
python -c "
import sqlite3
conn = sqlite3.connect('data/rmos.db')
cursor = conn.execute('PRAGMA table_info(patterns)')
columns = [row[1] for row in cursor]
print(f'Actual columns: {columns}')
"

# 4. Search for existing implementations
grep -r "rosette.*patterns" services/api/app/routers/
grep -r "class.*Pattern.*Store" services/api/app/stores/

# 5. Run existing tests to understand current behavior
pytest app/tests/rmos/ -v
```

### **Phase 2: Gap Analysis (What Exists vs What's Needed)**

```markdown
## Implementation Gap Matrix

| Component | Spec Expects | Codebase Has | Gap? | Action |
|-----------|--------------|--------------|------|--------|
| Storage | In-memory dict | SQLitePatternStore class | ✅ YES | Use .list_all() not .get() |
| Schema | Basic fields | N11.2 with pattern_type | ✅ YES | Add pattern_type='rosette' |
| Endpoint | /api/rosette-patterns | /api/rmos/patterns | ✅ YES | Update router prefix |
| Tests | None | test_rosette_patterns_router.py | ❌ NO | Tests already exist |
```

### **Phase 3: Architecture Decision (Before Implementing)**

```markdown
## Decision: Wave E1 Router Implementation Strategy

**Options:**
1. Follow spec exactly (in-memory dict)
2. Hybrid (dict wrapper around SQLite)
3. Use actual SQLite store API

**Decision:** Option 3 (Use SQLite API)

**Rationale:**
- N11.2 migration is complete and stable
- Dict stores are deprecated
- Tests validate SQLite implementation
- No reason to maintain backward compatibility

**Breaking Changes from Spec:**
- `stores.get("patterns", [])` → `stores.patterns.list_all()`
- `patterns.append()` → `stores.patterns.create()`
- In-memory → Database persistence

**Migration Path:** None needed (new feature, no existing code)
```

### **Phase 4: Implementation with Evidence Trail**

```python
# services/api/app/routers/rmos_patterns_router.py

# ✅ CORRECT IMPLEMENTATION
# Evidence: services/api/app/stores/sqlite_pattern_store.py lines 103-168
# Evidence: services/api/app/stores/rmos_stores.py lines 15-52
# Evidence: services/api/app/core/rmos_db.py SCHEMA_VERSION = 2

@router.get("/", response_model=List[RosettePattern])
async def list_patterns() -> List[RosettePattern]:
    """
    List all rosette patterns.
    
    Uses SQLitePatternStore.list_all() (N11.2 architecture).
    Returns database-persisted patterns, not in-memory list.
    """
    stores = get_rmos_stores()  # Returns RMOSStores class (rmos_stores.py:15)
    pattern_dicts = stores.patterns.list_all()  # SQLitePatternStore method (sqlite_pattern_store.py:103)
    patterns = [RosettePattern(**p) for p in pattern_dicts]
    return patterns
```

### **Phase 5: Testing & Validation**

```powershell
# 1. Unit test the router
cd services/api
pytest app/tests/rmos/test_rosette_patterns_router.py -v

# 2. Integration test via API
uvicorn app.main:app --reload --port 8000

# In another terminal:
curl http://localhost:8000/api/rmos/patterns
# Expected: 200 with empty array or existing patterns

# 3. Database verification
python -c "
from app.stores.rmos_stores import get_rmos_stores
stores = get_rmos_stores()
patterns = stores.patterns.list_all()
print(f'Pattern count: {len(patterns)}')
for p in patterns:
    print(f'  - {p[\"name\"]} (type: {p.get(\"pattern_type\", \"unknown\")})')
"
```

---

## 🎓 Summary: The Core Problem & Solution

### **The Problem**

```
Time T0: Spec written     → Architecture assumes dict stores
Time T1: N11.2 migration  → Architecture shifts to SQLite stores
Time T2: Implementation   → Follows spec literally (crashes)
Time T3: Discovery        → Reverse-engineer actual API
Time T4: Fix              → Rewrite all endpoints
```

**Wasted Time:** Steps T2-T4 (could have been avoided)

### **The Solution**

```
Time T0: Spec written     → Architecture assumes dict stores
Time T1: N11.2 migration  → ⚠️ UPDATE SPECS, document breaking changes
Time T2: Pre-implementation check → Verify spec matches reality
Time T3: Implementation   → Use actual API from the start
```

**Time Saved:** Entire reverse-engineering cycle

### **Tools to Prevent This**

1. **Version Tags:** Every spec declares target codebase version
2. **Prerequisite Checks:** Scripts verify dependencies before implementation
3. **Gap Analysis:** Compare spec vs reality in matrix format
4. **Architecture Decision Records:** Document why patterns changed
5. **Integration Tests:** Validate infrastructure before implementing on top
6. **Code Evidence Comments:** Link implementations to actual file locations
7. **Migration Guides:** When architecture shifts, document the transition

---

## 📖 Related Documentation

- **PATCH_N11_SCHEMA_FIX.md** — N11.2 database migration that caused this drift
- **PHASE_D_E_DECISIONS.md** — Architecture decision examples
- **WAVE16_PHASE_D_GAP_ANALYSIS.md** — Gap analysis methodology
- **ROSETTE_ROUTER_TEST_BUNDLE_SUMMARY.md** — Integration testing approach
- **AGENTS.md** — Updated with module awareness patterns

---

**Key Takeaway:** Specifications are **documentation of intent**, not **documentation of reality**. Always verify reality first.
