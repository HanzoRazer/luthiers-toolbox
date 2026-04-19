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

## Code at Each Stage

### Stage 1: Loop 3 Implementation (Mar 4, 2026)

**Commit:** `66894d49`  
**File:** `services/blueprint-import/vectorizer_phase3.py`

```python
class FeedbackSystem:
    """
    Collects and manages user feedback for continuous improvement.
    """

    def __init__(self, feedback_dir: str = ".feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.pending_reviews: List[Dict] = []

    def record_classification(
        self,
        contour_hash: str,
        predicted_category: str,
        confidence: float,
        features: np.ndarray,
        source_file: str
    ):
        """Record a classification for potential review."""
        record = {
            "contour_hash": contour_hash,
            "predicted": predicted_category,
            "confidence": confidence,
            "features": features.tolist(),
            "source": source_file,
            "timestamp": datetime.now().isoformat(),
            "reviewed": False,
            "correct_label": None
        }
        self.pending_reviews.append(record)

    def submit_correction(self, contour_hash: str, correct_category: str, 
                          reviewer: str = "user") -> bool:
        """Submit a correction for a classification."""
        for record in self.pending_reviews:
            if record["contour_hash"] == contour_hash:
                record["correct_label"] = correct_category
                record["reviewed"] = True
                self._save_feedback(record)
                return True
        return False
```

**Wiring (disabled by default):**
```python
# Line 2741 - default is False
def __init__(self, ..., enable_feedback: bool = False, ...):
    self.feedback = FeedbackSystem(feedback_dir) if enable_feedback else None
```

---

### Stage 2: Loop 1 Full Implementation (Mar 15, 2026)

**Commit:** `190adf66`  
**File:** `services/photo-vectorizer/geometry_coach_v2.py`

```python
class GeometryCoachV2:
    """
    Coach V2 widens scope from contour-only retries to body-ownership retries.

    Primary responsibilities:
      1. Inspect BodyIsolationResult
      2. Inspect ContourStageResult
      3. Choose the *next safest rerun target*
      4. Enforce guardrails:
         - max retries
         - monotonic improvement
         - no silent downgrade
         - terminal manual review state
    """

    def __init__(self, config: Optional[CoachV2Config] = None):
        self.config = config or CoachV2Config()

    def should_retry(
        self,
        *,
        body_result: BodyIsolationResult,
        contour_result: Any,
        retry_count: int = 0,
    ) -> bool:
        if retry_count >= self.config.max_retries:
            return False

        body_score = float(getattr(body_result, "completeness_score", 0.0))
        contour_score = float(getattr(contour_result, "best_score", 0.0))

        if contour_score < self.config.contour_target_threshold:
            return True

        if body_score < self.config.body_isolation_review_threshold:
            return True

        return False

    def evaluate(self, *, body_stage_runner, contour_stage_runner, 
                 body_result, contour_result, **kwargs):
        """Main entry point - returns (body_result, contour_result, decision)"""
        # ... retry logic with monotonic improvement gates
```

**Wiring in photo_vectorizer_v2.py (Stage 8.5):**
```python
# Line ~4108
if coach_enabled:
    body_isolation_result, contour_result, coach_decision = (
        self.geometry_coach_v2.evaluate(
            body_stage_runner=self.body_isolation_stage,
            contour_stage_runner=self.contour_stage,
            body_result=body_isolation_result,
            contour_result=contour_result,
            ...
        )
    )
    
    if coach_decision.action == "manual_review_required":
        result.warnings.append(coach_decision.reason)
```

---

### Stage 3: Loop 1 Partial (Scale Validation) (Apr 3, 2026)

**Commit:** `76b1ff98`  
**File:** `services/blueprint-import/vectorizer_phase3.py`

```python
def validate_scale_before_export(
    mm_per_px: float,
    scale_factor: float,
    classified: Dict[ContourCategory, List[ContourInfo]],
    spec_name: Optional[str] = None
) -> Tuple[float, bool]:
    """
    Validate scale produces plausible instrument dimensions before export.
    If not plausible, attempts correction.

    Called BEFORE export_to_dxf().
    
    Returns:
        Tuple of (corrected_scale_factor, validation_passed)
    """
    effective_mm_per_px = mm_per_px * scale_factor

    # Find body outline from classified dict
    body_list = classified.get(ContourCategory.BODY_OUTLINE, [])
    if not body_list:
        # Fallback to largest contour
        all_contours = [c for cat_list in classified.values() for c in cat_list]
        if not all_contours:
            logger.warning("Scale validation: no contours to validate")
            return scale_factor, False
        largest = max(all_contours, key=lambda c: c.area_px)
    else:
        largest = body_list[0]

    body_w_mm = largest.width_mm * scale_factor
    body_h_mm = largest.height_mm * scale_factor

    logger.info(f"Scale validation: body={body_w_mm:.0f}x{body_h_mm:.0f}mm")

    # Check against spec if available
    if spec_name and spec_name in INSTRUMENT_SPECS:
        spec = INSTRUMENT_SPECS[spec_name]
        expected_w = (spec.body_width_range[0] + spec.body_width_range[1]) / 2
        expected_h = (spec.body_length_range[0] + spec.body_length_range[1]) / 2
        
        ratio_w = body_w_mm / expected_w
        ratio_h = body_h_mm / expected_h

        if 0.8 < ratio_w < 1.2 and 0.8 < ratio_h < 1.2:
            return scale_factor, True
        else:
            correction = (expected_w / body_w_mm + expected_h / body_h_mm) / 2
            logger.warning(f"Scale validation FAILED. Correction: {correction:.3f}x")
            return scale_factor * correction, False

    # Generic plausibility (no spec)
    max_dim = max(body_w_mm, body_h_mm)
    if max_dim > 700:
        correction = 500 / max_dim
        return scale_factor * correction, False

    return scale_factor, True
```

**Wiring in vectorizer_phase3.py:**
```python
# Line 3559
scale_factor, scale_valid = validate_scale_before_export(
    mm_per_px, scale_factor, classified, spec_name
)
```

---

### Stage 4: Orchestrator Created WITHOUT Validation (Apr 13, 2026)

**Commit:** `e6950d25`  
**File:** `services/api/app/services/blueprint_orchestrator.py`

```python
# Imports - NOTE: No validation imports
from .blueprint_extract import (
    ExtractionResult,
    extract_blueprint_to_dxf,
    extract_pdf_page,
    DualPassResult,
    extract_dual_pass,  # <-- New dual-pass, no validation
)
from .blueprint_clean import (
    CleanResult,
    CleanupMode,
    ...
)

# No import of:
#   - validate_scale_before_export (from vectorizer_phase3)
#   - GeometryCoachV2 (from photo-vectorizer)
#   - FeedbackSystem (from vectorizer_phase3)

class BlueprintOrchestrator:
    def process_file(self, ...):
        # ... extraction code ...
        
        # LAYERED_DUAL_PASS mode - no validation gate
        if mode == CleanupMode.LAYERED_DUAL_PASS:
            dual_result = extract_dual_pass(
                source_path=str(input_path),
                output_path=str(raw_dxf_path),
                target_height_mm=target_height_mm,
                warnings=warnings,
            )
            # Proceeds directly to export
            # NO call to validate_scale_before_export
            # NO call to GeometryCoachV2.evaluate
            # NO feedback recording
```

**What's Missing (the regression):**
```python
# THIS CODE SHOULD EXIST BUT DOESN'T:

# Option A: Import scale validation
from services.blueprint_import.vectorizer_phase3 import validate_scale_before_export

# Option B: Import full coaching
from services.photo_vectorizer.geometry_coach_v2 import GeometryCoachV2

# Before DXF export:
scale_factor, valid = validate_scale_before_export(mm_per_px, scale_factor, classified)
if not valid:
    result.recommendation = Recommendation(action="review", reasons=["Scale validation failed"])
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
