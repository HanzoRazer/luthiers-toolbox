# Feedback Loop System — Developer Handoff

**Date:** 2026-04-19  
**Author:** Claude Code Session  
**Status:** REGRESSION IDENTIFIED — restoration path documented

---

## Executive Summary

The Photo Vectorizer was designed with a three-loop feedback architecture to ensure extraction quality. **Loop 1 is fully implemented and working in the photo pipeline. Loops 2 and 3 are implemented but disabled. None of the loops are wired into the current blueprint pipeline.**

The `blueprint_orchestrator.py` (created April 13, 2026) bypasses all validation systems. This explains why extraction failures like the "28% body capture" issue pass through without detection or retry.

### Key Finding

This is **regression, not absence**. The code exists. The fix is wiring, not writing.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THREE-LOOP FEEDBACK SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LOOP 1: Intra-Frame Validation (within single extraction)          │   │
│  │                                                                     │   │
│  │   Input ──► Extract ──► Validate ──┬──► Accept ──► Export          │   │
│  │                            │       │                                │   │
│  │                            │       └──► Retry with different       │   │
│  │                            │            strategy (max 2 retries)   │   │
│  │                            │                                        │   │
│  │                            └──► Reject ──► Manual Review Required  │   │
│  │                                                                     │   │
│  │   Status: IMPLEMENTED (photo pipeline), ORPHANED (blueprint)       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LOOP 2: Cross-Image Learning (across extractions)                  │   │
│  │                                                                     │   │
│  │   Image A ──► Strategy X works ──► Cache (signature → strategy)    │   │
│  │   Image B ──► Similar signature ──► Start with Strategy X          │   │
│  │                                                                     │   │
│  │   Status: DESIGN ONLY (in CLAUDE.md), NOT IMPLEMENTED              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LOOP 3: User Correction Retraining (feedback → model update)       │   │
│  │                                                                     │   │
│  │   Bad Output ──► User Correction ──► FeedbackSystem.submit()       │   │
│  │                                              │                      │   │
│  │   TrainingDataCollector ◄──────────────────-─┘                      │   │
│  │          │                                                          │   │
│  │          └──► train_classifier() ──► Updated Model                 │   │
│  │                                                                     │   │
│  │   Status: IMPLEMENTED, DISABLED (enable_feedback=False default)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Status Matrix

| Loop | Component | Location | Implemented | Wired | Active |
|------|-----------|----------|-------------|-------|--------|
| **1** | `GeometryCoachV2` | `photo-vectorizer/geometry_coach_v2.py` | ✅ Mar 15 | ✅ photo | ✅ |
| **1** | `validate_scale_before_export` | `blueprint-import/vectorizer_phase3.py:2327` | ✅ Apr 3 | ❌ | ❌ |
| **1** | (missing) | `api/services/blueprint_orchestrator.py` | ❌ | — | — |
| **2** | `strategy_cache` | — | ❌ | — | — |
| **3** | `FeedbackSystem` | `blueprint-import/vectorizer_phase3.py:1181` | ✅ Mar 4 | ❌ | ❌ |
| **3** | `TrainingDataCollector` | `blueprint-import/vectorizer_phase3.py:1273` | ✅ Mar 4 | ❌ | ❌ |

---

## Timeline of Events

```
2026-03-04  ┃  66894d49  ┃  FeedbackSystem + TrainingDataCollector IMPLEMENTED
            ┃            ┃  (Loop 3 complete, but enable_feedback=False default)
            ┃
2026-03-15  ┃  190adf66  ┃  GeometryCoachV2 IMPLEMENTED (Loop 1 for photo pipeline)
            ┃            ┃  - geometry_authority.py (family priors)
            ┃            ┃  - body_isolation_result.py (6-signal breakdown)
            ┃            ┃  - body_isolation_stage.py (stage wrapper)
            ┃            ┃  - geometry_coach_v2.py (Rules A-D, retry logic)
            ┃            ┃  - Wired into photo_vectorizer_v2.py Stage 8.5
            ┃
2026-04-02  ┃  dc7d397d  ┃  CLAUDE.md architecture doc added
            ┃            ┃  (incorrectly states loops "never implemented")
            ┃
2026-04-03  ┃  76b1ff98  ┃  validate_scale_before_export IMPLEMENTED
            ┃            ┃  (Loop 1 partial for blueprint-import)
            ┃
2026-04-13  ┃  e6950d25  ┃  blueprint_orchestrator.py CREATED
            ┃            ┃  ⚠️  Does not import vectorizer_phase3.py
            ┃            ┃  ⚠️  Does not import geometry_coach_v2.py
            ┃            ┃  ⚠️  All validation bypassed
            ┃
2026-04-19  ┃  (today)   ┃  Regression identified in this session
```

---

## File Locations

### Loop 1 — Intra-Frame Validation

**Photo Pipeline (WORKING):**
```
services/photo-vectorizer/
├── geometry_coach_v2.py      # Main coach: Rules A-D, evaluate()
├── geometry_authority.py     # Family priors, dimension fit scoring
├── body_isolation_result.py  # Typed result with 6-signal breakdown
├── body_isolation_stage.py   # Stage wrapper with save/restore
└── photo_vectorizer_v2.py    # Integration at Stage 8.5 (line ~4108)
```

**Blueprint Pipeline (ORPHANED):**
```
services/blueprint-import/
└── vectorizer_phase3.py
    └── validate_scale_before_export()  # Line 2327, called at 3559
                                        # BUT: orchestrator doesn't import this file
```

**Current Blueprint Pipeline (NO VALIDATION):**
```
services/api/app/services/
├── blueprint_orchestrator.py  # Main entry point — NO validation
├── blueprint_extract.py       # Extraction logic
├── blueprint_clean.py         # Cleanup modes
├── layer_builder.py           # Layer classification
└── layered_dxf_writer.py      # DXF export
```

### Loop 3 — User Correction (DISABLED)

```
services/blueprint-import/vectorizer_phase3.py
├── class FeedbackSystem        # Line 1181
│   ├── record_classification() # Records predictions
│   ├── submit_correction()     # User submits fix
│   ├── get_training_data()     # Returns corrected samples
│   └── get_low_confidence_samples()
│
└── class TrainingDataCollector # Line 1273
    ├── add_sample()            # Collect labeled data
    ├── save() / load()         # Persistence
    └── train_classifier()      # RandomForest training
```

---

## Diagnostic Scripts

### 1. Verify Loop 1 exists in photo pipeline

```bash
# Should return Stage 8.5 integration
grep -n "geometry_coach_v2.evaluate" services/photo-vectorizer/photo_vectorizer_v2.py
```

### 2. Verify Loop 1 is orphaned in blueprint pipeline

```bash
# Should return NO results — this is the bug
grep -rn "validate_scale\|geometry_coach\|GeometryCoach" \
  services/api/app/services/blueprint_orchestrator.py
```

### 3. Verify Loop 3 code exists but is disabled

```bash
# Classes exist
grep -n "class FeedbackSystem\|class TrainingDataCollector" \
  services/blueprint-import/vectorizer_phase3.py

# Default is False — never enabled
grep -n "enable_feedback" services/blueprint-import/vectorizer_phase3.py
```

### 4. Find all commits affecting the feedback system

```bash
git log --all --oneline -S "FeedbackSystem"
git log --all --oneline -S "GeometryCoachV2"
git log --all --oneline -S "validate_scale_before_export"
```

### 5. Show the original Loop 1 implementation

```bash
git show 190adf66 --stat
```

---

## Restoration Options

### Option A: Port GeometryCoachV2 to Blueprint Orchestrator

**Effort:** Medium (2-3 days)  
**Risk:** Low  
**Benefit:** Full retry logic, monotonic improvement gates

```python
# In blueprint_orchestrator.py, add:
from services.photo_vectorizer.geometry_coach_v2 import GeometryCoachV2

# After extraction, before export:
coach = GeometryCoachV2(config)
body_result, contour_result, decision = coach.evaluate(...)

if decision.action == "manual_review_required":
    result.recommendation = Recommendation(action="reject", ...)
```

### Option B: Port validate_scale_before_export to Orchestrator

**Effort:** Low (1 day)  
**Risk:** Low  
**Benefit:** Basic scale validation, blocks obviously wrong output

```python
# In blueprint_orchestrator.py, add:
from services.blueprint_import.vectorizer_phase3 import validate_scale_before_export

# Before DXF export:
scale_factor, scale_valid = validate_scale_before_export(
    mm_per_px, scale_factor, contours, spec_name
)
if not scale_valid:
    result.recommendation = Recommendation(action="review", ...)
```

### Option C: Enable Loop 3 (FeedbackSystem)

**Effort:** Low (0.5 day)  
**Risk:** Low  
**Benefit:** Collect user corrections for future model training

```python
# Change default in vectorizer_phase3.py:
enable_feedback: bool = True  # was False

# Or pass explicitly:
vectorizer = Phase3Vectorizer(enable_feedback=True)
```

### Option D: Full Rebuild

**Effort:** High (1-2 weeks)  
**Risk:** Medium  
**Benefit:** Clean architecture, all three loops integrated

Not recommended until Options A-C are evaluated.

---

## Recommended Sprint Plan

### Sprint 3A: Restore Loop 1 (1-2 days)

1. Import `validate_scale_before_export` into `blueprint_orchestrator.py`
2. Call it before DXF export
3. Add test case: "12 StringDreadnaught_2.jpg" must trigger validation failure
4. If validation fails, set `recommendation.action = "review"`

### Sprint 3B: Wire GeometryCoachV2 (2-3 days)

1. Evaluate if photo-vectorizer's coach can be imported directly
2. If not, port core logic: Rules A-D, retry profiles
3. Add integration at the equivalent of "Stage 8.5"
4. Test with corpus: `Guitar Plans/`

### Sprint 3C: Enable Loop 3 (0.5 day)

1. Set `enable_feedback=True` as default
2. Add API endpoint: `POST /api/blueprint/correction`
3. Wire to `FeedbackSystem.submit_correction()`

### Sprint 3D: Implement Loop 2 (3-5 days)

1. Add `strategy_cache` to orchestrator
2. Compute image signature (perceptual hash or feature vector)
3. Cache successful strategy per signature
4. On new image, check cache before default strategy

---

## Test Cases

### Must-Fail Inputs (Loop 1 should reject)

| File | Issue | Expected Behavior |
|------|-------|-------------------|
| `12 StringDreadnaught_2.jpg` | 28% body capture | Retry or reject |
| Any image producing >700mm body | Scale error | Apply correction factor |
| Any image producing <200mm body | Scale error | Apply correction factor |

### Must-Pass Inputs

| File | Expected |
|------|----------|
| `12 String Dreadnaught_1.jpg` | 450×466mm, ACCEPT |
| `Gibson-Double-Neck-esd1275.png` | Full extraction, ACCEPT |

---

## Verification Command

After restoration, this command should show validation being called:

```bash
cd services/api
VECTORIZER_DEBUG=1 python -c "
from app.services.blueprint_orchestrator import BlueprintOrchestrator
from app.services.blueprint_clean import CleanupMode

o = BlueprintOrchestrator()
with open('../../Guitar Plans/12 StringDreadnaught_2.jpg', 'rb') as f:
    r = o.process_file(file_bytes=f.read(), filename='test.jpg',
                       target_height_mm=500.0, mode=CleanupMode.LAYERED_DUAL_PASS,
                       debug=True)
print(f'Recommendation: {r.recommendation.action}')
print(f'Reasons: {r.recommendation.reasons}')
" 2>&1 | grep -E "validation|Validation|BODY|body_area|scale"
```

**Before fix:** No validation output, returns ACCEPT  
**After fix:** Shows validation, returns REVIEW or triggers retry

---

## References

- CLAUDE.md: Vectorizer Architecture Decision (lines ~200-400)
- Commit `190adf66`: Original Loop 1 implementation
- Commit `66894d49`: Loop 3 implementation
- Commit `76b1ff98`: Scale validation gate
- Commit `dc7d397d`: Architecture documentation

---

## Contact

For questions about this handoff, review the session transcript or run:

```bash
git log --oneline --since="2026-04-19" --until="2026-04-20"
```
