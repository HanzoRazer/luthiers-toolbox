# Vectorizer Fallback Behavior Audit

**Date:** 2026-05-20  
**Status:** ARCHAEOLOGY_COMPLETE  
**Sprint:** Vectorizer Technical Debt Archaeology

---

## Overview

This document identifies hidden fallback behaviors that may silently degrade semantic fidelity or topology quality.

**Critical Question:** Do fallbacks preserve semantic authority, or do they silently emit degraded output?

---

## Blueprint Pipeline Fallbacks

### 5-Tier Fallback Ladder (REFINED mode)

**Location:** `services/api/app/services/blueprint_clean.py:206-329`

| Tier | Trigger | Behavior | Logged? | Semantic Risk |
|------|---------|----------|---------|---------------|
| 1 | High confidence + closed + long | Primary selection | Yes | None |
| 2 | Medium confidence + closed | Secondary selection | Yes | Low |
| 3 | Low confidence but long | Length-based fallback | Yes | Medium |
| 4 | Any closed contour | Closure-based fallback | Yes | Medium |
| 5 | Any contour (last resort) | Desperation fallback | Yes | **High** |

**Assessment:** Well-designed graduated fallback with logging at each tier. Fallback tier is exposed in response via `fallback_tier` field.

### BASELINE Mode Simple Fallback

**Location:** `blueprint_clean.py:913-977`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| No high-confidence candidate | 2-pass fallback (length, then any) | Yes | Medium |
| Border detected | Removed before scoring | Yes | Low |

**Assessment:** Simpler than REFINED but still logged. No silent degradation.

### Border Detection Fallback

**Location:** `blueprint_clean.py:352-389`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| Contour matches page dimensions | Removed from candidates | Yes | Low |

**Assessment:** Correctly removes page borders. Logged.

---

## Photo-Vectorizer Fallbacks

### Body Isolation Retry Profiles

**Location:** `services/photo-vectorizer/body_isolation_stage.py`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| Low ownership score | Try next retry profile | Yes | Low |
| All profiles fail | Return best effort | Yes | **Medium** |

**Assessment:** Retry profiles are explicit and logged. Best-effort return could degrade quality.

### Edge-to-DXF Grouping Fallback

**Location:** `services/photo-vectorizer/edge_to_dxf.py:1294`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| Grouping fails with exception | Fall back to `_isolate_body_contours()` | **Warning only** | **High** |

**Code:**
```python
try:
    grouped = self._isolate_with_grouping(contours, ...)
except Exception as e:
    logger.warning(f"Grouping failed, falling back: {e}")
    grouped = self._isolate_body_contours(contours, ...)  # DEPRECATED
```

**Assessment:** **HIDDEN FALLBACK** — catches any exception and falls back silently to deprecated method. High risk of topology degradation.

### Contour Plausibility Import Fallback

**Location:** `services/photo-vectorizer/contour_plausibility.py:10-18`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| `blueprint_view_segmenter` import fails | Border detection disabled | **No** | Medium |

**Assessment:** Silent fallback — border detection may not work if import fails.

### Optional Dependency Fallbacks

**Location:** Multiple files in photo-vectorizer

| Dependency | Fallback | Logged? | Semantic Risk |
|------------|----------|---------|---------------|
| `rembg` not installed | Background removal disabled | Module-level flag | Low |
| `SAM` not installed | SAM masking disabled | Module-level flag | Low |
| `fitz` not installed | PDF extraction fails | Yes (error) | N/A |
| `ezdxf` not installed | DXF export skipped | Yes (print) | Medium |

**Assessment:** Optional deps have graceful fallback with flags. Generally well-handled.

---

## Blueprint-Import Fallbacks

### ML Classifier Fallback

**Location:** `services/blueprint-import/vectorizer_phase3.py:50-60`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| sklearn not installed | ML classification disabled | Module-level flag | Medium |

**Assessment:** SIMPLE mode can work without sklearn. Logged at import time.

### Phase 3.7 Enhancements Fallback

**Location:** `services/blueprint-import/vectorizer_phase3.py:64-74`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| `vectorizer_enhancements` import fails | Enhanced features disabled | Module-level flag | Low |

**Assessment:** Graceful degradation to core functionality.

### Analyzer Vision Fallback

**Location:** `services/blueprint-import/vectorizer_phase3.py:43-48`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| `analyzer.py` import fails | Claude vision disabled | Module-level flag | Low |

**Assessment:** Scale detection may be less accurate without vision.

---

## API Router Fallbacks

### Vectorizer Availability Fallback

**Location:** `services/api/app/routers/photo_vectorizer_router.py:68-108`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| photo-vectorizer not importable | 503 Service Unavailable | Yes | N/A (fails closed) |

**Assessment:** **Good** — fails closed with clear error rather than silent degradation.

### CleanupMode Parse Fallback

**Location:** `services/api/app/routers/blueprint/vectorize_router.py:195-198`

| Trigger | Behavior | Logged? | Semantic Risk |
|---------|----------|---------|---------------|
| Invalid mode string | Default to REFINED | **No** | Low |

**Code:**
```python
try:
    cleanup_mode = CleanupMode(mode.lower())
except ValueError:
    cleanup_mode = CleanupMode.REFINED  # Silent default
```

**Assessment:** Silent fallback to REFINED mode. Low risk but could mask typos.

---

## Summary: Critical Fallbacks

| Fallback | Location | Logged? | Risk | Recommendation |
|----------|----------|---------|------|----------------|
| Edge-to-DXF grouping → deprecated | edge_to_dxf.py:1294 | Warning | **High** | Add telemetry, investigate root cause |
| Contour plausibility import | contour_plausibility.py:10 | No | Medium | Add warning log |
| CleanupMode default to REFINED | vectorize_router.py:195 | No | Low | Log warning for invalid mode |
| Body isolation best-effort | body_isolation_stage.py | Yes | Medium | Ensure confidence exposed |

---

## Semantic Risk Assessment

**Question:** Does fallback behavior silently degrade semantic fidelity?

| Pipeline | Answer | Evidence |
|----------|--------|----------|
| Blueprint (REFINED) | **No** — fallback tier exposed | `fallback_tier` in response |
| Blueprint (V2_RAW) | **No** — no fallback (raw output) | Direct extraction path |
| Photo (photo_v2) | **Partial** — grouping fallback silent | Warning only, no telemetry |
| Photo (ownership) | **No** — retry profiles logged | Coach V2 retry visible |

---

## Recommendations

1. **HIGH:** Add telemetry to `edge_to_dxf.py` grouping fallback — track how often deprecated path is hit.

2. **MEDIUM:** Add logging to `contour_plausibility.py` import fallback — border detection silently disabled is risky.

3. **LOW:** Log warning when `CleanupMode` defaults to REFINED due to invalid input.

4. **AUDIT:** Review all `except Exception:` blocks in photo-vectorizer for silent swallowing.

---

*Vectorizer Fallback Behavior Audit — Archaeology Complete — 2026-05-20*
