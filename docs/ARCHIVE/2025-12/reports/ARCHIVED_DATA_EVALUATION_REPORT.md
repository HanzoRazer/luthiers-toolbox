# Archived Data Evaluation Report

**Date:** December 14, 2025  
**Source:** `.archive_app_app_20251214/` (from `services/api/app/app/` namespace collision)  
**Evaluator:** AI Agent during .gitignore Recovery  
**Decision Required:** Merge, Archive Permanently, or Delete

---

## 1. Executive Summary

During the .gitignore recovery operation, a pathological namespace collision was discovered: `services/api/app/app/data/`. This nested `app/` directory was archived to `.archive_app_app_20251214/` rather than deleted, pending evaluation.

**Finding:** The archived data contains **development/test fixture data** that is **MORE DETAILED** than the canonical production data but represents **DIFFERENT test runs**. Both datasets have value for different purposes.

| Recommendation | Action |
|----------------|--------|
| **saw_runs.json** | ⚠️ MERGE valuable schema fields into canonical data |
| **saw_telemetry.json** | ✅ KEEP as reference test fixture, do not merge |
| **Archive directory** | 📁 Move to `_fixtures/` for test suite use |

---

## 2. File Comparison

### 2.1 saw_runs.json

| Property | Archived (app/app/) | Canonical (data/) |
|----------|---------------------|-------------------|
| **File Size** | 4,654 bytes | 1,617 bytes |
| **Last Modified** | Nov 27, 2025 9:37 AM | Nov 27, 2025 2:17 PM |
| **Run Count** | 5+ runs | 3 runs |
| **Run ID Format** | `test_20251127_*`, `run_20251127_*` | `SAW_20251127_*` |

**Schema Comparison:**

| Field | Archived | Canonical | Notes |
|-------|----------|-----------|-------|
| `run_id` | ✅ | ✅ | Different naming conventions |
| `created_at` | ✅ ISO format | ✅ ISO format | Same |
| `status` | ✅ | ✅ | Same |
| `meta.op_type` | ✅ | ✅ | Same |
| `meta.machine_profile` | ✅ `SAW_LAB_01` | ✅ `Saw_Alpha_01` | Different names |
| `meta.material_family` | ✅ `hardwood` | ✅ `hardwood_maple` | Canonical more specific |
| `meta.blade_id` | ✅ `BLADE_10IN_60T` | ✅ `TCT_250_80T` | Different conventions |
| `meta.program_id` | ✅ | ❌ | **Archived has extra field** |
| `meta.program_comment` | ✅ | ❌ | **Archived has extra field** |
| `meta.rpm` | ✅ (null) | ❌ | **Archived has extra field** |
| `meta.feed_ipm` | ✅ (null) | ❌ | **Archived has extra field** |
| `meta.plunge_ipm` | ✅ (null) | ❌ | **Archived has extra field** |
| `meta.safe_z_mm` | ✅ | ❌ | **Archived has extra field** |
| `meta.doc_per_pass_mm` | ✅ (null) | ❌ | **Archived has extra field** |
| `meta.total_depth_mm` | ✅ (null) | ❌ | **Archived has extra field** |
| `meta.risk_grade` | ✅ (null) | ❌ | **Archived has extra field** |
| `meta.risk_warnings` | ✅ [] | ❌ | **Archived has extra field** |
| `meta.notes` | ✅ (null) | ❌ | **Archived has extra field** |
| `meta.extra` | ✅ {} | ❌ | **Archived has extra field** |
| `gcode` | ✅ inline | ✅ inline | Same |
| `started_at` | ✅ | ❌ | **Archived has extra field** |
| `completed_at` | ✅ | ❌ | **Archived has extra field** |
| `error_message` | ✅ (null) | ❌ | **Archived has extra field** |
| `stats` | ❌ | ✅ | **Canonical has extra object** |
| `stats.duration_s` | ❌ | ✅ | **Canonical has extra field** |

**Analysis:**
- Archived schema is **richer** with 14 additional fields for CAM workflow tracking
- Canonical schema is **cleaner** with aggregated `stats` object
- These represent **two different schema evolution stages**

---

### 2.2 saw_telemetry.json

| Property | Archived (app/app/) | Canonical (data/) |
|----------|---------------------|-------------------|
| **File Size** | 43,539 bytes | 3,385 bytes |
| **Last Modified** | Nov 27, 2025 9:37 AM | Nov 27, 2025 2:30 PM |
| **Total Lines** | 1,479 | ~100 |
| **Sample Count** | ~50+ per run | 5 per run |
| **Sample Interval** | 15 seconds | ~4-6 seconds |

**Schema Comparison:**

| Field | Archived | Canonical | Notes |
|-------|----------|-----------|-------|
| `timestamp` | ✅ ISO | ✅ ISO | Same |
| `x_mm` | ✅ | ✅ | Same |
| `y_mm` | ✅ (null) | ✅ | Canonical more complete |
| `z_mm` | ✅ (null) | ✅ | Canonical more complete |
| `rpm_actual` | ✅ | ✅ | Same |
| `spindle_load_percent` | ✅ | ✅ | Same |
| `feed_actual_mm_min` | ✅ | ✅ | Same |
| `vibration_mg` | ✅ | ✅ | Same |
| `motor_current_amps` | ✅ (null) | ❌ | Archived has extra |
| `temp_c` | ✅ (null) | ❌ | Archived has extra |
| `alarm` | ✅ | ❌ | Archived has extra |
| `extra` | ✅ {} | ❌ | Archived has extra |
| `in_cut` | ✅ | ✅ | Same |

**Analysis:**
- Archived telemetry is **MUCH DENSER** (50+ samples vs 5)
- Archived is better for **machine learning training** (more data points)
- Canonical is better for **API response size** (compact)
- Archived has more instrumentation fields (motor current, temp, alarm)

---

## 3. Data Quality Assessment

### 3.1 Archived Data Quality

| Criterion | Assessment | Score |
|-----------|------------|-------|
| **Completeness** | Many null values indicate placeholders | ⚠️ 6/10 |
| **Consistency** | Uniform schema across all runs | ✅ 9/10 |
| **Test Coverage** | Multiple scenarios (hardwood, softwood, batch) | ✅ 8/10 |
| **Realism** | Synthetic timestamps, round numbers | ⚠️ 5/10 |
| **Documentation Value** | Good for schema reference | ✅ 8/10 |

**Overall:** Development fixture data, good for testing but not production telemetry.

### 3.2 Canonical Data Quality

| Criterion | Assessment | Score |
|-----------|------------|-------|
| **Completeness** | No null values, all fields populated | ✅ 9/10 |
| **Consistency** | Clean naming conventions | ✅ 9/10 |
| **Test Coverage** | 3 distinct operation types | ✅ 7/10 |
| **Realism** | More realistic sample intervals | ✅ 7/10 |
| **Documentation Value** | Clean production format | ✅ 9/10 |

**Overall:** Cleaner production-ready format, but less comprehensive.

---

## 4. Use Case Mapping

| Use Case | Best Source | Reason |
|----------|-------------|--------|
| **API Documentation** | Canonical | Cleaner, minimal |
| **Schema Reference** | Archived | Shows all possible fields |
| **Unit Tests** | Archived | More edge cases |
| **Integration Tests** | Canonical | Production-like |
| **ML Training Data** | Archived Telemetry | Dense samples |
| **Performance Testing** | Both | Different load profiles |
| **RMOS Feasibility** | Archived | Has risk fields |

---

## 5. Recommended Actions

### Action 1: Promote Archived Schema Fields (OPTIONAL)

The archived `saw_runs.json` schema includes valuable fields not present in canonical:
- `program_id`, `program_comment` — Job tracking
- `safe_z_mm`, `doc_per_pass_mm`, `total_depth_mm` — CAM parameters
- `risk_grade`, `risk_warnings` — RMOS integration
- `started_at`, `completed_at`, `error_message` — Lifecycle tracking

**Recommendation:** Consider updating the canonical schema to include these fields in a future RMOS integration ticket.

### Action 2: Move Archive to Test Fixtures

```powershell
# Move to _fixtures for test suite access
$src = "services/api/app/.archive_app_app_20251214"
$dst = "services/api/app/_fixtures/cnc_production_dev"
Move-Item -Path "$src/app/data/cnc_production" -Destination $dst -Force
Remove-Item -Recurse -Force $src  # Clean up empty archive
```

**Benefits:**
- Preserved for unit tests
- Not in production code path
- Discoverable by test suite

### Action 3: Document Schema Divergence

Create a Pydantic model that supports both schemas:

```python
# services/api/app/schemas/saw_run.py
class SawRunMeta(BaseModel):
    op_type: str
    machine_profile: str
    material_family: str
    blade_id: str
    depth_passes: int = 1
    total_length_mm: float
    # Optional fields from archived schema
    program_id: Optional[str] = None
    safe_z_mm: Optional[float] = None
    risk_grade: Optional[str] = None
    risk_warnings: List[str] = []
```

---

## 6. Decision Matrix

| Option | Pros | Cons | Effort |
|--------|------|------|--------|
| **A: Delete Archive** | Clean, no confusion | Lose test fixtures | Low |
| **B: Keep in .archive** | Zero effort | Hidden, may rot | None |
| **C: Move to _fixtures** | Discoverable, useful | Minor refactor | Low |
| **D: Merge Schemas** | Best of both | Code changes needed | Medium |

**Recommended:** Option C (Move to _fixtures) as immediate action, Option D as future enhancement.

---

## 7. Orphan File Status Summary

After the .gitignore recovery, the orphan status is:

| Category | Count | Status |
|----------|-------|--------|
| **Backend (services/api/app/)** | 423 files | ✅ Committed |
| **Experimental (_experimental/)** | 56 files | ✅ Isolated & Committed |
| **Archived (app/app/)** | 2 files | ⏳ Pending Decision |
| **Legitimately Ignored** | 7 files | ✅ Correctly Ignored |
| **Remaining Untracked** | 0 files | ✅ Complete |

---

## 8. Next Steps

1. **Decide on Archive Fate:**
   - [ ] Option C: Move to `_fixtures/` (recommended)
   - [ ] Option A: Delete permanently
   - [ ] Option B: Leave in `.archive`

2. **Schema Enhancement (Future):**
   - [ ] Create ticket to add archived fields to canonical schema
   - [ ] Update Pydantic models to support optional fields
   - [ ] Add migration script for existing data

3. **Test Suite Integration:**
   - [ ] Add fixture loading utility
   - [ ] Reference archived data in unit tests

---

## Appendix: Full File Listings

### Archived saw_runs.json Run IDs
1. `test_20251127_150930` — Hardwood, BLADE_10IN_60T, slice
2. `run_20251127_133237` — Softwood, BLADE_10IN_40T, slice  
3. `run_20251127_133713` — Softwood, BLADE_10IN_40T, slice
4. `run_20251127_140713` — Hardwood, BLADE_10IN_60T, batch
5. (additional runs...)

### Canonical saw_runs.json Run IDs
1. `SAW_20251127_001` — Hardwood maple, TCT_250_80T, slice
2. `SAW_20251127_002` — Plywood birch, ATB_300_60T, contour
3. `SAW_20251127_003` — Softwood pine, TCT_250_80T, slice

---

**Status:** Awaiting decision on archive disposition  
**Owner:** Developer  
**Priority:** Low (non-blocking)
