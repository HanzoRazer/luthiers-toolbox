# Contour Plausibility & Agentic Geometry Coaching — Engineering Specification

**Status:** Phase 1 Complete — Foundation Deployed  
**Author:** Systems Architecture  
**Date:** March 14, 2026  
**Commit:** `739664ff`  
**Module:** `services/photo-vectorizer/photo_vectorizer_v2.py`

---

## 1. Problem Statement

Live testing of the Photo Vectorizer v2 pipeline confirmed that the dominant failure mode is **body contour fidelity and election**, not calibration or scale estimation.

| Image | Failure Mode | Root Cause |
|-------|-------------|------------|
| Smart Guitar | Width correct (5.2%), height off 41.3% | Body contour incomplete — lower bout missing |
| Benedetto | 67.9% H error, 58.9% W error | False reference detection + contour failure |
| Archtop | Width 111.7% error, height 12% | Neck + body silhouette mis-selected |

**Core insight:** The system can sometimes determine scale correctly but cannot reliably identify the correct body contour. Calibration improvements alone cannot correct an incorrect contour hypothesis.

The vectorizer commits too early to a body contour hypothesis during contour assembly. It needs a supervisory layer that evaluates contour plausibility before committing to export.

---

## 2. Strategic Architecture

A three-layer architecture addresses the root cause.

```
Layer 1: Vector Execution Engine     (existing pipeline — unchanged)
Layer 2: Geometry Authority           (contour plausibility + family priors)
Layer 3: Agentic Geometry Coach       (supervisory correction loop — future)
```

### Layer 1 — Vector Execution Engine

The existing pipeline remains the execution engine:

```
Photo → Orientation → Perspective Correction → Background Removal
     → Body Isolation → Edge Detection → Family Classification
     → Calibration → Contour Assembly → Grid Classification → Export
```

### Layer 2 — Geometry Authority (Phase 1 — Deployed)

A geometry knowledge layer that scores contour candidates using instrument family priors, structural signals, and dimension validation. Answers: **"Should this contour be trusted as the body outline?"**

### Layer 3 — Agentic Geometry Coach (Phase 3 — Future)

A supervisory loop that inspects Stage 8 artifacts, consults the Geometry Authority, adjusts parameters, and reruns narrow pipeline stages. The coach does not generate contours — it guides the vectorizer to correct its perception.

---

## 3. Implementation Plan (Agreed Sequence)

```
Step 1: Typed result dataclass          ✅ Deployed
Step 2: Plausibility scoring            ✅ Deployed
Step 3: Export blocking                 ✅ Deployed
Step 4: Module extraction               ⬜ Next
Step 5: Coaching loop                   ⬜ Future
```

---

## 4. Phase 1 Deliverables (Deployed)

### 4.1 ContourScore Dataclass

Plausibility score for a single contour candidate. Seven scoring signals:

| Signal | Weight | What It Measures |
|--------|--------|------------------|
| Solidity | 0.25 | Hull coverage — `contour_area / convex_hull_area` |
| Dimension plausibility | 0.25 | Contour mm dimensions vs family priors |
| Symmetry | 0.15 | Left/right point balance and vertical span match |
| Aspect ratio | 0.15 | Contour H:W ratio vs family-expected range (±40%) |
| Border contact | 0.10 | Contour bbox touching ≥2 image edges (penalty) |
| Neck inclusion | 0.10 | Contour extends significantly above body region (penalty) |

**Output:** Composite score 0.0–1.0, per-signal values, boolean flags, diagnostic issues list.

### 4.2 ContourStageResult Dataclass

Full typed record of Stage 8 processing:

| Field | Type | Purpose |
|-------|------|---------|
| `feature_contours_pre_merge` | `List[FeatureContour]` | Snapshot before morphological merge |
| `merge_result` | `Optional[MergeResult]` | Merger output (if fragments were merged) |
| `feature_contours_post_merge` | `List[FeatureContour]` | Snapshot after merge |
| `body_contour_pre_grid` | `Optional[FeatureContour]` | Elected body before grid reclassification |
| `feature_contours_post_grid` | `List[FeatureContour]` | Final contour list after grid classification |
| `body_contour_final` | `Optional[FeatureContour]` | Final elected body contour |
| `contour_scores_pre` | `List[ContourScore]` | Plausibility scores for pre-merge candidates |
| `contour_scores_post` | `List[ContourScore]` | Plausibility scores for post-merge candidates |
| `elected_source` | `str` | `"pre_merge"` or `"post_merge"` — scorer's recommendation |
| `best_score` | `float` | Highest plausibility score across all candidates |
| `export_blocked` | `bool` | Whether export was blocked due to low plausibility |
| `block_reason` | `Optional[str]` | Human-readable block reason |
| `diagnostics` | `Dict[str, Any]` | Counts, family, debug metadata |

### 4.3 ContourPlausibilityScorer

**Class:** `ContourPlausibilityScorer`

Scores all contour candidates above an area threshold using family-aware dimension priors from `INSTRUMENT_SPECS`.

**Key methods:**

- `score_candidate(fc, idx, body_region, family, mpp, image_shape) → ContourScore` — Score one contour
- `score_all_candidates(contours, body_region, family, mpp, image_shape) → List[ContourScore]` — Score all viable candidates
- `elect_best(pre_merge_scores, post_merge_scores) → (idx, source, score)` — Compare pre-merge vs post-merge best candidates

**Family dimension priors (`_FAMILY_DIMENSION_PRIORS`):**

| Family | Height Range (mm) | Width Range (mm) |
|--------|-------------------|-------------------|
| Solid Body | 350–470 | 280–380 |
| Archtop | 420–560 | 350–460 |
| Acoustic | 440–560 | 350–440 |
| Semi-Hollow | 400–530 | 330–440 |
| Unknown | 300–600 | 250–480 |

### 4.4 Export Blocking

If the best plausibility score across all candidates falls below `EXPORT_BLOCK_THRESHOLD` (0.30), the pipeline:

1. Sets `result.export_blocked = True`
2. Records `result.export_block_reason` with diagnostic detail
3. Emits a warning: `EXPORT BLOCKED: ... manual review required`
4. Skips SVG/DXF/JSON file generation

This prevents the system from silently exporting unreliable geometry.

### 4.5 Diagnostic-Only Election

**Critical design decision:** The scorer operates in **diagnostic mode only** for Phase 1. It scores all candidates and captures the results in `ContourStageResult`, but the actual body contour election continues to use the proven `elect_body_contour_v2` + X-extent guard from Patch 17.

**Rationale:** When tested with active election override, the scorer improved some metrics but regressed others. The existing election pipeline has 127 passing tests and known behavior. The scoring data captured now becomes the foundation for the coaching loop in Phase 3, where parameter adjustment and stage reruns can act on low plausibility scores.

### 4.6 Pipeline Integration

The scorer is wired into `extract()` at Stage 8:

```
Stage 8 flow (post-deployment):
  1. assembler.assemble()           → feature_contours
  2. Snapshot pre_merge              → pre_merge_contours
  3. Score pre-merge candidates      → scores_pre
  4. contour_merger.merge()          → optional merged contour appended
  5. Snapshot post_merge             → post_merge_contours
  6. Score post-merge candidates     → scores_post
  7. Diagnostic election             → (best_idx, source, best_score) — logged only
  8. Actual election                 → elect_body_contour_v2() — proven pipeline
  9. Build ContourStageResult        → captures all scoring data
  10. Export blocking check           → blocks if best_score < 0.30
  11. Grid reclassification          → unchanged
  12. Finalize stage result          → post-grid contours + final body attached
  13. Attach to result               → result.contour_stage = contour_stage
```

---

## 5. Verification

### Unit Tests (31 new — `test_plausibility_scorer.py`)

| Test Class | Count | Coverage |
|-----------|-------|---------|
| `TestContourScore` | 2 | Dataclass creation, issues list |
| `TestContourStageResult` | 2 | Default values, populated state |
| `TestScorerScoreCandidate` | 10 | All 7 signals, edge cases (zero mpp, no body region, unknown family) |
| `TestScorerScoreAll` | 2 | Area filtering, empty list |
| `TestScorerElectBest` | 6 | Pre/post comparison, tie-breaking, empty inputs |
| `TestScorerSymmetry` | 2 | Symmetric contour, insufficient points |
| `TestExportBlocking` | 3 | Threshold constant, low/good score behavior |
| `TestFamilyPriors` | 2 | All families have priors, mm ranges are reasonable |
| `TestScorerIntegration` | 2 | Full scoring flow, export blocking on junk contours |

### Regression

**158/158 tests pass** across all 5 test files. Zero regressions against 127 pre-existing tests.

### Live Validation

Smart Guitar diagnostic output confirms full population:

```
contour_stage populated: True
elected_source: post_merge
best_score: 0.8624
pre_merge contours: 5  →  post_merge contours: 6
scores_pre: 4  →  scores_post: 5
export_blocked: False
family: solid_body

Post-merge candidate scores:
  [0] score=0.862  solidity=0.974  dim=0.480  neck=False  border=False
  [2] score=0.728  solidity=0.557  dim=0.000  issues: small vs body region
  [3] score=0.846  solidity=0.899  dim=0.476
  [4] score=0.551  solidity=0.554  issues: aspect ratio outside range
  [5] score=0.612  solidity=0.000  issues: low solidity
```

---

## 6. Next Steps

### Phase 2 — Module Extraction (Step 4)

Extract Stage 8 (contour assembly + merge + election + grid reclassification) into a standalone callable module:

**Target:** `services/photo-vectorizer/contour_assembly_stage.py`

**Inputs:** edge_map, body_region, instrument_family, calibration, params  
**Outputs:** ContourStageResult (candidate contours, scores, elected body, diagnostics)

This creates the seam required for Stage re-entry — the coaching loop needs to rerun Stage 8 with revised parameters without rerunning the entire pipeline.

### Phase 3 — Geometry Coach v1 (Step 5)

A minimal coaching loop that:

1. Inspects `ContourStageResult` after Stage 8
2. If `best_score < intervention_threshold`: adjusts closure kernel, body isolation bounds, or edge thresholds
3. Reruns the extracted Stage 8 module with revised parameters
4. Compares new result against original — accepts only if score improves
5. Max retry limit with fail-safe "human review required" terminal state

**Coach v1 intervention points:**

| Target | Trigger | Action |
|--------|---------|--------|
| Contour Assembly | Partial silhouette (low completeness) | Increase closure kernel, expand candidate pool |
| Body Isolation | Incomplete body region | Expand region bounds, adjust segmentation threshold |
| Edge Detection | Broken exterior contours | Increase exterior closing kernel, adjust edge thresholds |
| Calibration | Implausible scale estimate | Trigger feature-based calibration, reject weak references |

### Phase 4 — AI Quality Voter (Future)

Render-back similarity system as a final QA gate:

- Detect catastrophic mismatches between source photo and rendered vector
- Rank multiple vector hypotheses
- Route uncertain results to human review

The voter does not replace geometry reasoning — it validates final output.

---

## 7. Success Criteria

Phase 1 (deployed):
- [x] Typed stage artifacts capture full Stage 8 processing state
- [x] Plausibility scoring evaluates all body candidates with 7 signals
- [x] Pre-merge vs post-merge comparison identifies better candidate set
- [x] Export blocking prevents silent export of unreliable geometry
- [x] Zero regression against existing test suite

Coach v1 (Phase 3 target):
- [ ] 50% reduction in catastrophic dimension errors (>25% error)
- [ ] Reliable suppression of unsafe exports
- [ ] Demonstrated correction of at least one contour failure via stage rerun

---

## 8. File Reference

| File | Purpose |
|------|---------|
| `services/photo-vectorizer/photo_vectorizer_v2.py` | Main pipeline — all new classes and wiring |
| `services/photo-vectorizer/test_plausibility_scorer.py` | 31 unit tests for scorer + dataclasses |
| `services/photo-vectorizer/live_test_summary.py` | 3-image live test harness |
| `docs/CONTOUR_PLAUSIBILITY_ENGINEERING_SPEC.md` | This document |

---

## 9. Architectural Constraints

1. **Scorer wraps, does not replace.** `ContourAssembler`, `ContourMerger`, and `elect_body_contour_v2` remain unchanged. The scorer is supervisory.
2. **Pre-merge snapshot is a shallow copy.** `FeatureContour` objects are shared between pre/post merge lists — the merger appends a new contour, it doesn't mutate existing ones.
3. **Curvature profiling deferred.** V1 scoring signals are structural (solidity, dimensions, symmetry, borders). Curvature-based body shape matching is a v2+ feature.
4. **FeatureClassifier relationship.** The classifier answers "what does this contour look like?" — the plausibility scorer answers "should this contour be trusted as the body?" The scorer can demote a BODY_OUTLINE classification, but in v1 it only reports — it does not override.
5. **Coaching loop needs guardrails.** Max-retry limit, comparative acceptance gate (new score must beat old), and a "human review" terminal state when all retries are exhausted.
6. **All geometry in mm.** Dimension priors, plausibility checks, and export thresholds use millimeters internally, consistent with the rest of the luthiers-toolbox codebase.
