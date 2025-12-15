# Phase 27 Complete Analysis - "Art Studio Compare Mode"

**Date:** November 19, 2025  
**Source:** Phase 27.1_ Rosette Compare Mode_Overlay Coloring _Legend.txt (2,509 lines)  
**Status:** 🟡 **PARTIAL** - Only Phase 27.1 integrated, 5 phases remaining

---

## 🔍 **Critical Discovery**

The file "Phase 27.1_..." actually contains **ALL 6 PHASES** of the Rosette Compare Mode feature:

**What we integrated:**
- ✅ Phase 27.0 - Compare Mode MVP (already existed)
- ✅ Phase 27.1 - Overlay Coloring & Legend (~150 lines) ✅ **COMPLETE**

**What remains:**
- 🔴 Phase 27.2 - Snapshot Diff → Risk Pipeline (~600 lines)
- 🔴 Phase 27.3 - Export CSV & Sparklines (~500 lines)
- 🔴 Phase 27.4 - Compare Presets Toggle (~400 lines)
- 🔴 Phase 27.5 - Risk Metrics Bar (~300 lines)
- 🔴 Phase 27.6 - Preset Scorecards (~300 lines)

---

## 📦 **Phase Inventory**

| Phase | Feature | Backend | Frontend | Lines | Priority | Status |
|-------|---------|---------|----------|-------|----------|--------|
| **27.0** | Compare MVP | ✅ Exists | ✅ Exists | - | ⭐⭐⭐⭐⭐ | ✅ Complete |
| **27.1** | Overlay Coloring | ✅ No change | ✅ Done | 150 | ⭐⭐⭐⭐⭐ | ✅ Complete |
| **27.2** | Risk Snapshots | 🔴 NEW table | 🔴 Button | 600 | ⭐⭐⭐⭐⭐ | 🔴 Missing |
| **27.3** | CSV Export | 🔴 Endpoint | 🔴 Sidebar | 500 | ⭐⭐⭐⭐ | 🔴 Missing |
| **27.4** | Preset Toggle | ✅ No change | 🔴 Toggle UI | 400 | ⭐⭐⭐ | 🔴 Missing |
| **27.5** | Risk Metrics | ✅ No change | 🔴 Metrics bar | 300 | ⭐⭐⭐⭐ | 🔴 Missing |
| **27.6** | Preset Scorecards | ✅ No change | 🔴 Scorecard UI | 300 | ⭐⭐⭐ | 🔴 Missing |

**Total Missing:** ~2,100 lines across 5 phases

---

## 🎯 **Phase Details**

### **Phase 27.2: Snapshot Diff → Risk Pipeline** ⭐⭐⭐⭐⭐
**Goal:** Store comparison snapshots in risk timeline for trend analysis

**Backend Changes:**
- **NEW Table:** `rosette_compare_risk` in SQLite
  - Fields: `job_id_a`, `job_id_b`, `lane`, `risk_score`, `diff_json`, `note`, `created_at`
- **UPDATE:** `art_studio_rosette_store.py` - Add risk snapshot CRUD
- **UPDATE:** `art_studio_rosette_router.py` - Add `/snapshot` POST and GET endpoints

**Frontend Changes:**
- **UPDATE:** `ArtStudioRosetteCompare.vue` - Add "Save to Risk Timeline" button
- Saves current comparison as risk snapshot
- Calculates risk score based on segment delta

**Files:**
1. `services/api/app/art_studio_rosette_store.py` (PATCH - add table + functions)
2. `services/api/app/routers/art_studio_rosette_router.py` (PATCH - add 2 endpoints)
3. `client/src/views/ArtStudioRosetteCompare.vue` (PATCH - add button + API call)
4. `services/api/tests/test_art_studio_rosette_snapshot.py` (NEW - pytest)

**Time:** 1.5 hours  
**Priority:** ⭐⭐⭐⭐⭐ (Enables risk tracking)

---

### **Phase 27.3: CSV Export & Sparklines** ⭐⭐⭐⭐
**Goal:** Export comparison history as CSV + show sparkline trend charts

**Backend Changes:**
- **NEW Endpoint:** `/api/art/rosette/compare/export_csv?job_id_a=X&job_id_b=Y`
- Returns CSV with columns: timestamp, segments_delta, inner_radius_delta, outer_radius_delta, risk_score

**Frontend Changes:**
- **NEW Component:** History sidebar in compare view
- Shows list of previous comparisons for these job IDs
- Inline sparklines showing trend over time
- "Export CSV" button per comparison

**Files:**
1. `services/api/app/routers/art_studio_rosette_router.py` (PATCH - add CSV export)
2. `client/src/views/ArtStudioRosetteCompare.vue` (PATCH - add sidebar + sparklines)
3. `services/api/tests/test_rosette_compare_export.py` (NEW - pytest)

**Time:** 1.5 hours  
**Priority:** ⭐⭐⭐⭐ (Export for analysis)

---

### **Phase 27.4: Compare Presets Toggle** ⭐⭐⭐
**Goal:** Group comparison history by preset (Safe, Aggressive, etc.)

**Backend Changes:**
- ✅ No backend changes (uses existing compare endpoint)

**Frontend Changes:**
- **UPDATE:** `ArtStudioRosetteCompare.vue` - Add toggle for "Group by Preset"
- When enabled, groups history by `preset_a` and `preset_b` combinations
- Shows collapsible sections per preset pair

**Files:**
1. `client/src/views/ArtStudioRosetteCompare.vue` (PATCH - add toggle + grouping logic)

**Time:** 1 hour  
**Priority:** ⭐⭐⭐ (UI organization)

---

### **Phase 27.5: Risk Metrics Bar** ⭐⭐⭐⭐
**Goal:** Show aggregate risk metrics across all snapshots

**Backend Changes:**
- ✅ No backend changes (computes from existing data)

**Frontend Changes:**
- **UPDATE:** `ArtStudioRosetteCompare.vue` - Add metrics bar above history
- Shows: Total snapshots, Avg risk, High-risk count, Low-risk count
- Color-coded risk bands (Low=green, Medium=yellow, High=red)

**Files:**
1. `client/src/views/ArtStudioRosetteCompare.vue` (PATCH - add metrics bar)

**Time:** 45 minutes  
**Priority:** ⭐⭐⭐⭐ (Quick overview)

---

### **Phase 27.6: Preset Scorecards** ⭐⭐⭐
**Goal:** Per-preset analytics cards with mini-dashboards

**Backend Changes:**
- ✅ No backend changes (computes from existing data)

**Frontend Changes:**
- **UPDATE:** `ArtStudioRosetteCompare.vue` - Add horizontal scrolling scorecard strip
- One card per preset showing:
  - Total snapshot count
  - Low/Medium/High risk breakdown
  - Average risk score
  - Tiny sparkline of risk evolution
- Appears between metrics bar and history list

**Files:**
1. `client/src/views/ArtStudioRosetteCompare.vue` (PATCH - add scorecard strip)

**Time:** 1 hour  
**Priority:** ⭐⭐⭐ (Advanced analytics)

---

## 🚀 **Integration Roadmap**

### **Tier 1: Critical Foundation** (1.5 hours)
**Goal:** Enable risk tracking for all comparisons

1. **Phase 27.2 - Risk Snapshots** (1.5 hours)
   - Database table for snapshot storage
   - API endpoints for save/load
   - "Save to Risk Timeline" button
   
**Deliverable:** Every comparison can be saved as risk snapshot

---

### **Tier 2: Analytics & Export** (2.5 hours)
**Goal:** Historical analysis and data export

2. **Phase 27.3 - CSV Export** (1.5 hours)
   - CSV export endpoint
   - History sidebar with sparklines
   - Export button per comparison

3. **Phase 27.5 - Risk Metrics Bar** (45 min)
   - Aggregate metrics display
   - Risk band visualization

**Deliverable:** Historical trends visible, data exportable

---

### **Tier 3: Advanced UI** (2 hours)
**Goal:** Better organization and per-preset insights

4. **Phase 27.4 - Preset Toggle** (1 hour)
   - Group by preset toggle
   - Collapsible preset sections

5. **Phase 27.6 - Preset Scorecards** (1 hour)
   - Per-preset analytics cards
   - Risk band breakdown per preset
   - Preset-level sparklines

**Deliverable:** Full-featured compare mode with preset-level analytics

**Total Time: 6 hours**

---

## 📋 **Files to Create/Modify**

### **Backend**

**Existing files to modify:**
- `services/api/app/art_studio_rosette_store.py` (+200 lines)
  - Add `rosette_compare_risk` table in `init_db()`
  - Add `save_risk_snapshot()`, `list_risk_snapshots()`, `get_risk_snapshot()`
  
- `services/api/app/routers/art_studio_rosette_router.py` (+150 lines)
  - Add `POST /snapshot` (save risk snapshot)
  - Add `GET /snapshots` (list risk snapshots)
  - Add `GET /export_csv` (CSV export)

**New files to create:**
- `services/api/tests/test_art_studio_rosette_snapshot.py` (NEW - 150 lines)
- `services/api/tests/test_rosette_compare_export.py` (NEW - 100 lines)

### **Frontend**

**Existing files to modify:**
- `client/src/views/ArtStudioRosetteCompare.vue` (+1,500 lines total across 5 phases)
  - Phase 27.2: +200 lines (Save snapshot button + API)
  - Phase 27.3: +400 lines (History sidebar + sparklines + export)
  - Phase 27.4: +300 lines (Preset toggle + grouping)
  - Phase 27.5: +300 lines (Metrics bar)
  - Phase 27.6: +300 lines (Scorecard strip)

**No new frontend files needed** - all changes are patches to existing compare view

---

## 🔥 **Critical Missing Capabilities**

Without these phases, the Rosette Compare Mode:

❌ **Can't track comparison history** (no database)  
❌ **Can't identify risky pattern changes** (no risk scoring)  
❌ **Can't export for external analysis** (no CSV)  
❌ **No historical trend visualization** (no sparklines)  
❌ **No preset-level insights** (no per-preset analytics)  
❌ **Limited usefulness for production** (one-off comparisons only)

**Impact:** Compare Mode is functional but disposable - no memory, no trends, no actionable intelligence.

---

## ⚡ **Quick Wins**

### **If Time-Constrained, Prioritize:**

1. **Phase 27.2** (1.5 hrs) - ⭐⭐⭐⭐⭐  
   Gets risk tracking working - foundation for all other features
   
2. **Phase 27.5** (45 min) - ⭐⭐⭐⭐  
   Adds metrics bar for quick overview (doesn't require 27.2 database)
   
3. **Phase 27.3** (1.5 hrs) - ⭐⭐⭐⭐  
   CSV export + history sidebar (requires 27.2 database)

**Total: 3.75 hours for 80% of value**

---

## 🔗 **Dependencies**

```
27.0 (MVP) ✅
  └─> 27.1 (Coloring) ✅
       ├─> 27.2 (Snapshots) 🔴 ← START HERE
       │    ├─> 27.3 (CSV Export) 🔴
       │    ├─> 27.4 (Preset Toggle) 🔴
       │    ├─> 27.5 (Metrics Bar) 🔴 (can be standalone)
       │    └─> 27.6 (Scorecards) 🔴 (requires 27.2)
```

**Phase 27.2 is blocking:** All other phases require the snapshot database table.

**Exception:** Phase 27.5 (Metrics Bar) can be implemented standalone without 27.2, but becomes more powerful with snapshot history.

---

## 📊 **Complexity Assessment**

| Phase | Backend Complexity | Frontend Complexity | Database Changes | Test Coverage |
|-------|-------------------|--------------------|--------------------|---------------|
| 27.2 | 🟡 Medium | 🟢 Low | 🔴 New table | ✅ Required |
| 27.3 | 🟢 Low | 🟡 Medium | ✅ No change | ✅ Required |
| 27.4 | ✅ None | 🟢 Low | ✅ No change | ⚪ Optional |
| 27.5 | ✅ None | 🟢 Low | ✅ No change | ⚪ Optional |
| 27.6 | ✅ None | 🟡 Medium | ✅ No change | ⚪ Optional |

**Most Complex:** Phase 27.2 (database schema change)  
**Easiest:** Phase 27.5 (pure frontend computed properties)

---

## ✅ **Integration Checklist**

### **Phase 27.2**
- [ ] Update `init_db()` to create `rosette_compare_risk` table
- [ ] Add `save_risk_snapshot()` function to store
- [ ] Add `list_risk_snapshots()` function to store
- [ ] Add `POST /snapshot` endpoint to router
- [ ] Add `GET /snapshots` endpoint to router
- [ ] Add "Save to Risk Timeline" button to compare view
- [ ] Implement risk score calculation (based on segment delta)
- [ ] Create pytest for snapshot CRUD

### **Phase 27.3**
- [ ] Add CSV export endpoint `/export_csv`
- [ ] Add history sidebar component to compare view
- [ ] Implement sparkline rendering function
- [ ] Add "Export CSV" button per comparison
- [ ] Create pytest for CSV export format

### **Phase 27.4**
- [ ] Add "Group by Preset" toggle checkbox
- [ ] Implement preset grouping computed property
- [ ] Add collapsible preset sections
- [ ] Update history rendering to support grouped mode

### **Phase 27.5**
- [ ] Add metrics bar component above history
- [ ] Compute total snapshots, avg risk, risk band counts
- [ ] Add color-coded risk chips (Low/Medium/High)

### **Phase 27.6**
- [ ] Add preset scorecard strip (horizontal scroll)
- [ ] Compute per-preset analytics
- [ ] Implement mini-sparkline rendering
- [ ] Add risk band breakdown per preset

---

**Recommendation:** Start with Phase 27.2 (risk snapshots) as it's the foundation for 27.3, 27.4, and 27.6. Phase 27.5 (metrics bar) can be done independently if needed for quick wins.
