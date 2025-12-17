# B26 Baseline Marking Implementation Summary

**Status:** ✅ Complete  
**Date:** November 25, 2025  
**Commit:** 627711f  
**Bundle:** Compare Mode Phase 2 - B26 Baseline Diff Workflows

---

## 🎯 Overview

B26 adds baseline tracking to CNC production job history, enabling users to:
- Mark winning jobs as baseline reference
- Display baseline indicators throughout the UI
- Quick-compare new jobs against established baselines

This closes the Compare Mode Phase 2 baseline workflows.

---

## 📦 Implementation

### **Backend Changes**

#### 1. `services/api/app/services/job_int_log.py`
**Added:** `update_job_baseline(run_id, baseline_id, path)` function
```python
def update_job_baseline(run_id: str, baseline_id: Optional[str], path: str = DEFAULT_LOG_PATH) -> bool:
    """Update the baseline_id field for an existing job log entry."""
    # Read all entries
    entries = load_all_job_logs(path=path)
    
    # Update matching entry
    for entry in entries:
        if entry.get("run_id") == run_id:
            entry["baseline_id"] = baseline_id
            break
    
    # Rewrite JSONL file
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

**Purpose:** Updates baseline_id in existing JSONL log entries (JSONL doesn't support in-place updates)

#### 2. `services/api/app/routers/cnc_production/compare_jobs_router.py`
**Added:** `POST /cnc/jobs/{run_id}/set-baseline` endpoint
```python
@router.post("/{run_id}/set-baseline")
async def set_job_baseline(run_id: str, body: SetBaselineRequest) -> Dict[str, Any]:
    """Mark a job as a baseline or clear baseline status."""
    # Verify job exists
    entry = find_job_log_by_run_id(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Job {run_id} not found")
    
    # Update baseline_id field
    success = update_job_baseline(run_id, body.baseline_id)
    
    # Return updated entry
    updated = find_job_log_by_run_id(run_id)
    return {"success": True, "run_id": run_id, "baseline_id": body.baseline_id, "job": updated}
```

**Request Body:**
```json
{
  "baseline_id": "job-run-id-123"  // or null to clear
}
```

**Response:**
```json
{
  "success": true,
  "run_id": "job-run-id-123",
  "baseline_id": "job-run-id-123",
  "job": { /* full job entry */ }
}
```

---

### **Frontend Changes**

#### 3. `packages/client/src/components/compare/CompareRunsPanel.vue`
**Added:** `markAsBaseline(runId)` async function
```typescript
async function markAsBaseline(runId: string) {
  try {
    const response = await fetch(`/api/cnc/jobs/${runId}/set-baseline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ baseline_id: runId })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    // Reload comparison to show baseline badge
    await loadComparison()
    
    // Notify parent
    emit('set-baseline', runId)
  } catch (e: any) {
    error.value = `Failed to set baseline: ${e.message}`
  }
}
```

**Updated:** `setBaseline()` button handler
```typescript
function setBaseline() {
  // Find job with most wins
  const wins = comparisonData.value.jobs.map(() => 0)
  Object.values(comparisonData.value.comparison).forEach((metric) => {
    if (metric.winner !== null && metric.winner >= 0) {
      wins[metric.winner]++
    }
  })

  const winnerIdx = wins.indexOf(Math.max(...wins))
  if (winnerIdx >= 0) {
    const winnerId = comparisonData.value.jobs[winnerIdx].run_id
    markAsBaseline(winnerId)  // ← Now calls API
  }
}
```

**UI Button:**
```vue
<button class="secondary" @click="setBaseline" :disabled="!comparisonData">
  Set Winner as Baseline
</button>
```

#### 4. `packages/client/src/views/CncProductionView.vue`
**Added:** `baseline_id` field to `Job` interface
```typescript
interface Job {
  run_id: string
  job_name?: string
  machine_id?: string
  baseline_id?: string | null  // ← NEW
  // ... other fields
}
```

**Added:** Baseline indicator badge in job table
```vue
<td>
  <span v-if="job.baseline_id" class="baseline-badge" title="Baseline">📍</span>
  {{ job.job_name || job.run_id.slice(0, 8) }}
</td>
```

**Added:** CSS for baseline badge
```css
.baseline-badge {
  display: inline-block;
  background: #fef3c7;
  color: #92400e;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  margin-right: 0.5rem;
}
```

**Updated:** `handleSetBaseline()` to reload job list
```typescript
async function handleSetBaseline(runId: string) {
  // Reload jobs to show updated baseline indicator
  await loadJobs()
}
```

---

### **Testing**

#### 5. `scripts/test_b26_baseline.ps1`
**Created:** Automated smoke test suite

**Test Coverage:**
1. ✅ Create sample job log entry
2. ✅ Mark job as baseline (POST endpoint)
3. ✅ Verify baseline_id persisted in JSONL
4. ✅ Verify baseline indicator in job list API
5. ✅ Clear baseline (set to null)
6. ✅ 404 error handling for non-existent jobs

**Test Results:**
```
=== All B26 Tests Passed ===

Summary:
  ✓ POST /cnc/jobs/{run_id}/set-baseline endpoint working
  ✓ Baseline ID persists in JSONL log file
  ✓ Baseline can be cleared (set to null)
  ✓ 404 error handling for non-existent jobs
```

---

## 🔄 User Workflow

1. **Compare Jobs**: User selects 2-4 jobs in CncProductionView
2. **View Winner**: CompareRunsPanel calculates winner (most 🏆 badges)
3. **Set Baseline**: User clicks "Set Winner as Baseline" button
4. **Persist**: API updates baseline_id in JSONL log file
5. **Display**: 📍 badge appears in job history table
6. **Reference**: Baseline jobs serve as reference for future comparisons

---

## 🗂️ Data Flow

```
User Action: "Set Winner as Baseline"
    ↓
CompareRunsPanel.markAsBaseline(runId)
    ↓
POST /api/cnc/jobs/{run_id}/set-baseline
    ↓
update_job_baseline() in job_int_log.py
    ↓
Rewrite cam_job_log.jsonl with updated baseline_id
    ↓
Reload comparison (shows "Baseline" badge in table header)
    ↓
Emit 'set-baseline' event to CncProductionView
    ↓
Reload job history (shows 📍 badge in job name column)
```

---

## 📊 API Endpoints

### **Set Baseline**
```http
POST /api/cnc/jobs/{run_id}/set-baseline
Content-Type: application/json

{
  "baseline_id": "job-abc123"
}
```

**Response:**
```json
{
  "success": true,
  "run_id": "job-abc123",
  "baseline_id": "job-abc123",
  "job": {
    "run_id": "job-abc123",
    "job_name": "Test Job",
    "baseline_id": "job-abc123",
    ...
  }
}
```

### **Clear Baseline**
```http
POST /api/cnc/jobs/{run_id}/set-baseline
Content-Type: application/json

{
  "baseline_id": null
}
```

---

## 🎨 UI Components

### **CompareRunsPanel**
- "Set Winner as Baseline" button (enabled when comparison loaded)
- Automatic winner detection (counts 🏆 badges across metrics)
- Reload comparison after baseline set (shows "Baseline" badge in header)

### **CncProductionView Job Table**
- 📍 badge for jobs with `baseline_id` set
- Badge appears next to job name in first column
- Yellow background (#fef3c7) with brown text (#92400e)

---

## 🔧 Technical Details

### **JSONL Update Strategy**
Since JSONL doesn't support in-place updates, `update_job_baseline()`:
1. Reads all entries into memory
2. Updates matching entry's baseline_id field
3. Rewrites entire file with updated entries

**Performance Note:** This is O(n) but acceptable for job history files (typically < 1000 entries). For larger datasets, consider SQLite migration.

### **Baseline ID Format**
Currently uses the job's own `run_id` as the baseline_id:
```json
{
  "run_id": "job-abc123",
  "baseline_id": "job-abc123"
}
```

**Future:** Could use separate baseline naming system (e.g., "v1-baseline", "production-baseline")

### **Error Handling**
- ❌ **404**: Job not found → `HTTPException(404, "Job {run_id} not found")`
- ❌ **500**: Update failed → `HTTPException(500, "Failed to update job baseline")`
- ✅ **Success**: Returns updated job entry with `success: true`

---

## 🚀 Next Steps

### **B22: SvgDiffDualDisplay** (Next Major Bundle)
- Side-by-side SVG comparison view
- Overlay mode with opacity slider
- Diff highlighting (red/green for deviations)
- Zoom/pan controls

### **Future B26 Enhancements**
- [ ] Baseline management panel (list all baselines, delete, rename)
- [ ] Quick-compare button: "Compare vs Baseline" (1-click)
- [ ] Baseline history tracking (when set, by whom, previous values)
- [ ] Baseline naming: Allow custom names instead of run_id
- [ ] Baseline metrics dashboard: Show baseline stats over time

---

## 📝 Files Changed

```
services/api/app/services/job_int_log.py           # update_job_baseline() helper
services/api/app/routers/cnc_production/compare_jobs_router.py  # POST endpoint
packages/client/src/components/compare/CompareRunsPanel.vue  # markAsBaseline()
packages/client/src/views/CncProductionView.vue    # baseline_id field, 📍 badge
scripts/test_b26_baseline.ps1                      # Smoke test suite
```

---

## ✅ Completion Checklist

- [x] Backend: update_job_baseline() helper function
- [x] Backend: POST /cnc/jobs/{run_id}/set-baseline endpoint
- [x] Frontend: markAsBaseline() in CompareRunsPanel
- [x] Frontend: "Set Winner as Baseline" button
- [x] Frontend: baseline_id in Job interface
- [x] Frontend: 📍 badge in job history table
- [x] Frontend: CSS styling for baseline badge
- [x] Frontend: handleSetBaseline() reload logic
- [x] Testing: test_b26_baseline.ps1 smoke test
- [x] Testing: All 5 test cases passing
- [x] Documentation: This summary document
- [x] Git: Committed and pushed to main branch

---

**Status:** ✅ B26 Complete  
**Ready for:** B22 (SvgDiffDualDisplay)  
**Commit:** 627711f - "feat(compare): B26 baseline marking workflows"
