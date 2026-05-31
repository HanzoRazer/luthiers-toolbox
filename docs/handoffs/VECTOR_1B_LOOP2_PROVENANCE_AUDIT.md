# VECTOR-1B: Loop 2 Provenance Audit

**Date:** 2026-05-11  
**Status:** AUDIT COMPLETE  
**Scope:** Determine whether Loop 2 cross-image learning was relocated, abandoned, or never implemented

> **CONFLATION CORRECTION (2026-05-30).** This audit treats Loop 2 as "approved in CLAUDE.md but
> never built." Per ground truth from Ross (2026-05-30): the entire three-loop architecture
> (incl. Loop 2) was **experimental and never approved** — its absence from the runtime is
> expected, not a remediation gap. The work is **sandbox-owned** (`vectorizer-sandbox`). The
> "approved in CLAUDE.md" premise is corrected at the source. See
> `docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md`.
>
> **Live-code carve-out:** Loop 2 specifically (`strategy_cache` cross-image learning) is genuinely
> absent. But "never implemented" across the loops means the *named, unified* architecture only —
> `GeometryCoachV2` (photo-vectorizer, retro-labeled "Loop 1") is real, **API-reachable** runtime
> code. Do NOT delete or sandbox it; deletion degrades a live endpoint path. See handoff §2 + §9b.

---

## Classification

**LOOP2_NOT_IMPLEMENTED**

Loop 2 cross-image learning was approved in CLAUDE.md but never built. No relocation to Image Body Generator or any other system. The design exists only as documentation.

---

## Audit Questions & Findings

### Q1: Does Image Body Generator contain strategy caching?

**No.**

IBG (`app/instrument_geometry/body/ibg/`) is a **downstream geometry completor**, not an image extraction learner:
- Takes partial vectorizer DXF output as input
- Extracts landmark points from DXF geometry
- Solves complete body model using Sevy formula (lutherie math)
- No image processing whatsoever

Files examined:
- `instrument_body_generator.py` — main generator class
- `constraint_extractor.py` — DXF landmark extraction
- `body_contour_solver.py` — parametric body solver

### Q2: Does it compute image signatures?

**No.**

No perceptual hashing, dhash, phash, or image fingerprinting anywhere in the codebase:
```
Grep: perceptual.?hash|phash|imagehash|dhash → No files found
```

### Q3: Does it compare multiple extraction strategies?

**No.**

"Strategy" in vectorizer_phase3.py refers to **scale inference fallbacks** (neck pocket width → pickup routes → bridge route → body outline ratio), not extraction strategies. These are sequential fallbacks, not parallel comparison.

No `try_all_strategies()` or `pick_best()` methods exist.

### Q4: Does it persist best/winning strategies?

**No.**

The only cache in the vectorizer is `ImageCache` (lines 504-538), which is an **LRU file-loading cache** to avoid re-reading images from disk. It does not cache extraction strategies.

```
Grep: winning|best_strategy|strategy_result → No files found
```

### Q5: Does it feed anything back into Blueprint Reader/vectorizer?

**No.**

IBG is a one-way consumer of vectorizer output. No feedback loop exists.

### Q6: Is it reusable infrastructure or product-specific logic?

**Product-specific.** IBG is hardcoded to guitar body completion. It has no learning layer.

---

## What DOES Exist

### Loop 3 Infrastructure (Orphaned)

**FeedbackSystem** (`vectorizer_phase3.py:1181-1267`):
- Records classifications for review
- Accepts user corrections via `submit_correction()`
- Persists corrections to `.feedback/` directory
- Provides `get_training_data()` for retraining

**TrainingDataCollector** (`vectorizer_phase3.py:1273+`):
- Collects labeled training samples
- Stores to `.training_data/` directory

Both are instantiated when `enable_feedback=True` (line 2805) but **never wired to API endpoints**.

### RMOS Pipeline Feedback (Different Domain)

`app/rmos/pipeline/feedback/` is a CAM job execution feedback system:
- Job logging for operator feedback
- Learning events for feeds & speeds
- Metrics rollups for execution statistics

This is **not vectorizer-related** — it learns CAM parameters, not image extraction strategies.

### Photo Vectorizer (R&D Sandbox)

`services/photo-vectorizer/` is excluded per EXCLUDED_R_AND_D_SANDBOX. Examined for Loop 2 patterns — none found. Uses same edge detection approach as Blueprint Reader.

---

## Approved Design vs Reality

### CLAUDE.md Specification (Line ~415)

```python
class AdaptiveExtractor:
    def __init__(self):
        self.strategy_cache = {}  # image_signature → winning_strategy

    def extract(self, image, spec_name=None):
        sig = self.get_image_signature(image)
        if sig in self.strategy_cache:
            return self.extract_with_strategy(image, self.strategy_cache[sig])
        results = self.try_all_strategies(image, spec_name)
        best = self.pick_best(results, spec_name)
        self.strategy_cache[sig] = best.strategy
        return best
```

### Reality

| Component | Specified | Implemented |
|-----------|-----------|-------------|
| `strategy_cache` attribute | Yes | No |
| `get_image_signature()` | Yes | No |
| `try_all_strategies()` | Yes | No |
| `pick_best()` | Yes | No |
| Cache persistence (JSON) | Yes | No |

---

## Root Cause Analysis

Loop 2 was never prioritized. Sessions focused on:

1. **Loop 1 (scale validation)** — partially implemented via `validate_scale_before_export()` (lines 2327-2425)
2. **DXF compliance** — remediated in VECTOR-1A
3. **Point fixes** — epsilon tuning, version strings, simplification tolerances

The approved architecture was documented but not queued for implementation.

---

## Recommendations

### If Loop 2 is still desired:

1. **Scope it as VECTOR-2A** — dedicated sprint for cross-image learning
2. **Start with image signatures** — perceptual hash or learned embedding
3. **Define strategy set** — what are the "strategies" to compare?
   - Current candidates: aggressive, simple, canny_only, scale_correction
4. **Add cache persistence** — JSON file or SQLite
5. **Wire to extraction pipeline** — before Loop 1 validation

### If Loop 2 is deprioritized:

1. **Archive the design** — move from active CLAUDE.md to docs/archive/
2. **Update audit handoff** — mark as "design only, not implemented"
3. **Focus on Loop 1 completion** — retry logic, multi-factor validation

---

## Files Examined

| File | Purpose | Loop 2 Evidence |
|------|---------|-----------------|
| `vectorizer_phase3.py` | Main vectorizer | None (has FeedbackSystem for Loop 3) |
| `ibg/instrument_body_generator.py` | Body completor | None (downstream of vectorizer) |
| `ibg/constraint_extractor.py` | DXF landmark extraction | None |
| `ibg/body_contour_solver.py` | Parametric solver | None |
| `rmos/pipeline/feedback/` | CAM job feedback | Different domain |
| `photo-vectorizer/` | R&D sandbox | None |

---

*Audit complete. No code changes made.*
