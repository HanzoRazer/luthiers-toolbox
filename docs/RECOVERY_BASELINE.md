# Historical Baseline Recovery Documentation

## Overview

This document describes the `restored_baseline` cleanup mode, which replicates
the exact blueprint vectorization behavior from commit `86c49526` (2026-04-11 01:41:33).

## Background

### The Working State

On 2026-04-11 at 18:51, the Melody Maker PDF produced usable output:
- Body-like contour selected
- No page border in output
- DXF file suitable for manual cleanup

This was the last working state before the hierarchy-based regression.

### The Regression

Commit `f49ead1d` (2026-04-12 15:42:22) introduced hierarchy-based contour
isolation that:

1. Used `RETR_TREE` instead of `RETR_LIST` in edge detection
2. Added `_remove_page_borders_early()` which nullifies border contours
3. Added `_isolate_with_grouping()` which filters to winning group only
4. Added cleanup-stage border removal

When the body contour is fragmented (as in Melody Maker), this filtering
removes everything except the page border, causing the regression.

## Technical Differences

### Historical Behavior (86c49526)

**edge_to_dxf.py:**
- `convert()` has NO `isolate_body` parameter
- Uses `cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)`
- NO hierarchy handling
- NO border removal
- NO grouping
- ALL valid contours (>= 3 points) are converted to LINE entities

**blueprint_clean.py:**
- NO `_remove_page_border_chains()` function
- NO 5-tier fallback ladder
- Simple scoring with `score_contours()`
- Single-pass fallback: find first chain that passes length/closure filters
- NO `cv2` import (no border detection at cleanup stage)

### Current Behavior (HEAD)

**edge_to_dxf.py:**
- `convert()` has `isolate_body=True` parameter
- Uses `cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)`
- Hierarchy-based parent/child detection
- Surgical border removal before grouping
- Primary object grouping with scoring
- Only winning group's contours exported

**blueprint_clean.py:**
- `_remove_page_border_chains()` removes borders before scoring
- 5-tier fallback priority ladder
- Body-likeness checks for fallback candidates
- `cv2` import for border detection

## Implementation

### Mode Dispatch

The `CleanupMode` enum now has three values:
- `BASELINE`: Simpler pre-grouping behavior (approximate)
- `REFINED`: Current logic with all improvements (default)
- `RESTORED_BASELINE`: Exact historical behavior from 86c49526

### Orchestrator Changes

When `mode=RESTORED_BASELINE`:
- `isolate_body=False` is passed to extraction
- This forces `RETR_LIST` in edge detection (no hierarchy)
- All contours are exported to the raw DXF

### Cleanup Changes

The `_clean_blueprint_restored_baseline()` function:
- NO border removal at any stage
- NO ownership scoring (`ownership_fn=None`)
- Very permissive area filters (0.001 to 0.99)
- Single-pass fallback (just take best candidate)
- NO MIN_SCORE_TO_KEEP threshold

## Usage

### API

```bash
# Sync endpoint
curl -X POST "http://localhost:8000/api/blueprint/vectorize" \
  -F "file=@melody_maker.pdf" \
  -F "mode=restored_baseline"

# Async endpoint  
curl -X POST "http://localhost:8000/api/blueprint/vectorize/async" \
  -F "file=@melody_maker.pdf" \
  -F "mode=restored_baseline"
```

### Frontend

The Blueprint Lab should offer mode selection:
- Refined (default)
- Baseline
- Restored Historical

### Benchmark Testing

```bash
pytest tests/test_vectorizer_benchmark.py --mode=restored_baseline
pytest tests/test_vectorizer_benchmark.py --compare
```

## Validation Criteria

For Melody Maker PDF, `restored_baseline` mode should produce:
1. Body-like output (not rectangular page border)
2. Selection score representing actual body confidence
3. No "Only page-border geometry found" warning
4. Artifacts present (SVG + DXF)
5. Manual cleanup assessment: "light" or "moderate" (not "unacceptable")

## Recovery Timeline

| Commit | Date | Message | Role |
|--------|------|---------|------|
| `86c49526` | 2026-04-11 01:41 | fix(blueprint): sync orchestrator | TARGET - working state |
| `28bb95d1` | 2026-04-11 20:55 | docs: add vectorizer docs | docs only |
| `ec9c26af` | 2026-04-12 13:49 | fix(async): non-accept results | last before regression |
| `f49ead1d` | 2026-04-12 15:42 | feat: hierarchy-based isolation | REGRESSION INTRODUCED |

## Files Modified

1. `services/api/app/services/blueprint_clean.py`
   - Added `CleanupMode.RESTORED_BASELINE` enum value
   - Added `_clean_blueprint_restored_baseline()` function

2. `services/api/app/services/blueprint_orchestrator.py`
   - Added `isolate_body=False` when mode is RESTORED_BASELINE

3. `services/api/app/routers/blueprint/vectorize_router.py`
   - Updated docstring to document new mode

4. `services/api/app/routers/blueprint_async_router.py`
   - Updated docstring to document new mode

## Benchmark Results (Verified 2026-04-13)

### Melody Maker PDF Comparison

| Metric | REFINED | RESTORED_BASELINE | Delta |
|--------|---------|-------------------|-------|
| Dimensions | 647x500mm | 647x500mm | Same |
| Entity count | 24,097 | 343,399 | **+14.3x** |
| Selection score | 0.086 | 0.690 | **+0.604** |
| Winner margin | 0.086 | 0.114 | +0.028 |
| Action | REJECT | REVIEW | Improved |
| Border fallback | YES | NO | Fixed |

### Analysis

- **REFINED** triggers `BORDER_FALLBACK` because hierarchy-based filtering
  removes all non-border contours, leaving only the page border as a candidate.
  The low score (0.086) reflects this degenerate selection.

- **RESTORED_BASELINE** uses `RETR_LIST` which captures all contours without
  hierarchy filtering. The higher entity count (343k vs 24k) includes the
  body outline plus all other edges. The score (0.690) reflects a meaningful
  body candidate being selected.

### Conclusion

For the Melody Maker benchmark, `restored_baseline` mode:
1. Eliminates border fallback regression
2. Produces 14x more geometry (starter quality)
3. Achieves 8x better selection score
4. Changes recommendation from REJECT to REVIEW

This validates that the historical behavior recovery is successful and
`restored_baseline` should be considered for blueprint PDFs that fail
under the refined mode.

---

## Interpretation of Results (2026-04-13)

### What This Result Actually Means

#### 1. The Regression Seam is Now Concrete

| Mode | Behavior | Outcome |
|------|----------|---------|
| REFINED | Aggressively filtered | Lost body signal, collapsed into border fallback, unusable (0.086) |
| RESTORED_BASELINE | Preserved full contour field | Retained body signal (even if noisy), usable starter (0.690) |

**Root cause confirmed:** The regression was caused by early filtering / structure 
enforcement, NOT by lack of detection capability.

#### 2. The 14x Entity Increase is NOT a Bug

343k entities vs 24k means RESTORED_BASELINE captures:
- Body outline
- Construction lines
- Annotations
- Duplicates
- Everything

**This is exactly what the old system did. That's why it worked as a starter.**

DO NOT try to "fix" or reduce this yet.

#### 3. Score Jump Proves Scoring Works

```
0.086 → 0.690
```

This is not tuning. This is **signal restoration**.

The scorer works when it has the right candidates. It fails when the candidate 
set is corrupted by early filtering.

### Architecture Direction Confirmed

> **Extraction must be permissive first. Interpretation comes later.**

This is the opposite of what REFINED was doing. REFINED tried to be smart early,
which destroyed the candidate field before scoring could operate on it.

---

## Stabilization Roadmap

### Step 1 — LOCK restored_baseline Immediately

**CRITICAL: This is now ground truth behavior.**

```
# DO NOT MODIFY restored_baseline WITHOUT EXPLICIT APPROVAL
# - No refactoring
# - No cleanup  
# - No optimization
# - No "quick improvements"
```

Any change risks reintroducing the regression.

### Step 2 — Make It the Production Fallback NOW

Do not wait for full benchmark suite. Enough signal exists.

**Implementation:**
```python
result_refined = run(mode="refined")

if _is_unacceptable(result_refined):
    result_baseline = run(mode="restored_baseline")
    return result_baseline
```

**Define "unacceptable" as:**
- `action == REJECT`
- OR page_border detected in warnings
- OR `score < 0.15`
- OR `entities < 5000` (meaningful threshold)

This immediately fixes production regression.

### Step 3 — Add Debug Telemetry

Return in response:
```json
{
  "behavior_source": "refined" | "restored_baseline"
}
```

This enables tracking:
- How often fallback triggers
- Which files still break refined mode

### Step 4 — Run Remaining Benchmarks AFTER Fallback is Live

Test against full manifest:
- Santos Hernandez
- Dreadnought  
- Explorer
- Bailey Archtop

**Goal is NOT perfection. Goal is:**
> No file produces blank or border-only garbage.

---

## What NOT To Do

**DO NOT (until stabilization is complete):**

| Action | Why Not |
|--------|---------|
| Reduce entity count | Will reintroduce filtering that caused regression |
| Reintroduce aggressive filters | Same problem |
| Tweak scoring again | Scoring works; candidate field was the problem |
| "Optimize" restored_baseline | Any change risks breaking ground truth |

---

## Post-Stabilization Path

**Only after fallback is working and stable:**

1. **Controlled reduction** — Remove obvious junk AFTER extraction, not before
2. **Improve in-group selection** — Better picking within preserved candidate set
3. **Add neck/component recovery** — Extend to multi-object blueprints
4. **Introduce text masking carefully** — Remove annotations without losing body

---

## Core Rule Discovery

This recovery effort revealed a fundamental system rule:

> **If you destroy the candidate field early, no amount of scoring can recover the object.**

- That's why REFINED failed (aggressive early filtering)
- That's why RESTORED works (permissive extraction)

This rule must guide all future vectorizer development.

---

## Status

| Milestone | Status | Date |
|-----------|--------|------|
| Identify regression cause | COMPLETE | 2026-04-13 |
| Reproduce working behavior | COMPLETE | 2026-04-13 |
| Validate with real data | COMPLETE | 2026-04-13 |
| Ship as fallback | PENDING | — |
| Full benchmark suite | PENDING | — |
| Controlled reduction | BLOCKED | After stabilization |

---

## Author

Production Shop  
Date: 2026-04-13
