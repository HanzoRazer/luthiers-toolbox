# Vectorizer Pipeline Audit — Developer Handoff

**Date**: 2026-04-11  
**Status**: PASS 1 COMPLETE (Read-Only Audit)  
**Author**: Production Shop  
**Scope**: Blueprint + Photo vectorization pipelines

---

## Executive Summary

This document maps the **actual behavior** of the vectorization pipelines as implemented, identifying decision ownership, signal flow, and architectural issues. No code changes were made — this is a truth-mapping exercise to inform future refactoring.

### Key Findings

| Finding | Severity | Location | Action |
|---------|----------|----------|--------|
| Photo confidence fabricated | High | `photo_vectorizer_router.py:470` | Use scorer output |
| Ownership gate divergence | Medium | Blueprint soft (10%) vs Photo hard (0.60) | Document or align |
| Duplicate thresholds | Low | Multiple files | Centralize |
| Missing recommendations | Medium | Neither pipeline | Add field |
| Legacy response fields | Low | Photo router | Deprecate |

---

## 1. Pipeline Architecture

### 1.1 Blueprint Pipeline

```
POST /api/blueprint/vectorize
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  vectorize_router.py                                        │
│  - File size validation                                     │
│  - Delegates to orchestrator                                │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  blueprint_orchestrator.py  ◄── CENTRAL OWNER               │
│  - PDF vs image routing                                     │
│  - Stage sequencing                                         │
│  - Warning list ownership                                   │
│  - Artifact validation                                      │
│  - Response construction                                    │
└─────────────────────────────────────────────────────────────┘
         │
         ├──► blueprint_extract.py
         │    - PDF rasterization (DPI capped)
         │    - Image downscaling
         │    - Edge detection via EdgeToDXF
         │
         ├──► blueprint_clean.py
         │    - Chain extraction
         │    - Contour scoring integration
         │    - SVG preview generation
         │
         └──► contour_scoring.py
              - Geometric scoring
              - Ownership as 10% weighted signal
              - Candidate ranking
```

**Code References:**

| Component | File | Key Lines |
|-----------|------|-----------|
| Router | `app/routers/blueprint/vectorize_router.py` | 71-135 |
| Orchestrator | `app/services/blueprint_orchestrator.py` | 144-362 |
| Extraction | `app/services/blueprint_extract.py` | 195-279 |
| Cleanup | `app/services/blueprint_clean.py` | 140-316 |
| Scoring | `app/services/contour_scoring.py` | 176-378 |
| DXF I/O | `app/cam/unified_dxf_cleaner.py` | write_selected_chains, clean_file |

### 1.2 Photo Pipeline

```
POST /api/vectorizer/extract
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  photo_vectorizer_router.py  ◄── THIN WRAPPER + VALIDATION  │
│  - Base64 decode                                            │
│  - Artifact encoding                                        │
│  - Validation (DUPLICATES orchestrator logic)               │
│  - Confidence FABRICATION (0.9 or 0.0)                      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  PhotoVectorizerV2.extract()                                │
│  - Body isolation (rembg / edge detection)                  │
│  - Contour plausibility scoring                             │
│  - Ownership HARD GATE (0.60 threshold)                     │
│  - SVG/DXF generation                                       │
└─────────────────────────────────────────────────────────────┘
         │
         └──► contour_plausibility.py
              - body_ownership_score()
              - ContourPlausibilityScorer
              - Hard gate: ownership_ok = score >= 0.60
```

**Code References:**

| Component | File | Key Lines |
|-----------|------|-----------|
| Router | `app/routers/photo_vectorizer_router.py` | 260-520 |
| Vectorizer | `services/photo-vectorizer/photo_vectorizer_v2.py` | 3820-4200 |
| Plausibility | `services/photo-vectorizer/contour_plausibility.py` | 61-217 |
| Geometry Coach | `services/photo-vectorizer/geometry_coach_v2.py` | 568+ |

---

## 2. Decision Ownership Map

### 2.1 Correctly Owned Decisions

| Decision | Owner | Location | Notes |
|----------|-------|----------|-------|
| PDF vs image detection | Orchestrator | `blueprint_orchestrator.py:210` | By file extension |
| PDF DPI capping | Extract service | `blueprint_extract.py:149` | LIMITS.max_pdf_dpi |
| Image downscaling | Extract service | `blueprint_extract.py:74-105` | LIMITS.max_raster_dim |
| Contour selection (Blueprint) | Scoring module | `contour_scoring.py:340-370` | Ownership as soft signal |
| Contour selection (Photo) | Plausibility scorer | `contour_plausibility.py:192` | Hard gate |
| Export blocking (Blueprint) | Orchestrator | `blueprint_orchestrator.py:322` | svg_valid && dxf_valid |
| R12 DXF format | DXF cleaner | `unified_dxf_cleaner.py` | LINE entities only |

### 2.2 Incorrectly Owned / Missing Decisions

| Decision | Current Owner | Problem | Correct Owner |
|----------|---------------|---------|---------------|
| Confidence (Photo) | Router fabricates | Fake 0.9/0.0 value | Should use scorer |
| Artifact thresholds | Multiple files | SVG_MIN_CHARS duplicated | Centralize |
| Recommendations | None | Not implemented | Orchestrator |
| Warning aggregation | Split across modules | Multiple producers | Single owner |

---

## 3. Canonical Response Schema

### 3.1 Blueprint Pipeline Response

**Endpoint**: `POST /api/blueprint/vectorize`  
**Response Model**: `BlueprintVectorizeResponse`

```python
# app/routers/blueprint/vectorize_router.py:58-66

class BlueprintVectorizeResponse(BaseModel):
    ok: bool
    stage: str = "complete"
    error: str = ""
    warnings: list[str] = []
    artifacts: Artifacts = Artifacts()
    dimensions: Dimensions = Dimensions()
    metrics: dict = {}
    debug: Optional[dict] = None  # Requires VECTORIZER_DEBUG=1
```

**Nested Schemas:**

```python
# app/routers/blueprint/vectorize_router.py:35-56

class SVGArtifact(BaseModel):
    present: bool = False
    content: str = ""           # Full SVG string
    path_count: int = 0

class DXFArtifact(BaseModel):
    present: bool = False
    base64: str = ""            # Base64-encoded DXF
    entity_count: int = 0       # LINE entity count
    closed_contours: int = 0

class Dimensions(BaseModel):
    width_mm: float = 0.0
    height_mm: float = 0.0
```

**Metrics Schema (internal):**

```python
# app/services/blueprint_orchestrator.py:347-354

metrics = {
    "original_entities": int,      # Raw edge count
    "cleaned_entities": int,       # After filtering
    "contours_found": int,         # Closed contours
    "chains_found": int,           # Total chains
    "extraction_ms": float,        # Processing time
    "contour_confidence": float,   # Scorer output (0.0-1.0)
}
```

### 3.2 Photo Pipeline Response

**Endpoint**: `POST /api/vectorizer/extract`  
**Response Model**: `VectorizeResponse`

```python
# app/routers/photo_vectorizer_router.py:157-180

class VectorizeResponse(BaseModel):
    ok: bool
    stage: str = "complete"
    artifacts: Artifacts = Artifacts()
    dimensions: Dimensions = Dimensions()
    
    # Legacy fields (DEPRECATED - use artifacts/dimensions)
    svg_path_d: str = ""        # DEPRECATED
    svg_path: str = ""          # DEPRECATED: file path
    dxf_path: str = ""          # DEPRECATED: file path
    contour_count: int = 0      # DEPRECATED
    line_count: int = 0         # DEPRECATED
    body_width_mm: float = 0.0  # DEPRECATED
    body_height_mm: float = 0.0 # DEPRECATED
    body_width_in: float = 0.0  # DEPRECATED
    body_height_in: float = 0.0 # DEPRECATED
    scale_source: str = ""      # DEPRECATED
    bg_method: str = ""         # DEPRECATED
    perspective_corrected: bool = False  # DEPRECATED
    
    warnings: list[str] = []
    processing_ms: float = 0.0
    export_blocked: bool = False
    export_block_reason: str = ""
    error: str = ""
    debug: Optional[dict] = None
```

**Photo Dimensions (extended):**

```python
# app/routers/photo_vectorizer_router.py:148-154

class Dimensions(BaseModel):
    width_mm: float = 0.0
    height_mm: float = 0.0
    width_in: float = 0.0       # Redundant
    height_in: float = 0.0      # Redundant
    spec_match: Optional[str] = None
    confidence: float = 0.0     # FABRICATED: 0.9 or 0.0
```

---

## 4. Signal Flow Analysis

### 4.1 Ownership Scoring — Behavioral Divergence

**Blueprint Pipeline** (soft signal):

```python
# app/services/contour_scoring.py:286-295

if ownership_fn is not None:
    score = (
        0.35 * min(area_ratio / 0.35, 1.0) +
        0.25 * closure +
        0.10 * aspect_s +
        0.15 * solid_s +
        0.05 * continuity +
        0.10 * ownership  # ◄── 10% WEIGHT, SOFT SIGNAL
    )
```

**Photo Pipeline** (hard gate):

```python
# services/photo-vectorizer/contour_plausibility.py:192-206

ownership_ok = ownership >= self.ownership_threshold  # 0.60

# Hard cap if ownership fails
if not ownership_ok:
    total_score = min(total_score, 0.59)  # ◄── HARD GATE
```

**Impact**: Blueprint pipeline will return low-confidence results with warnings. Photo pipeline will block export entirely if ownership < 0.60.

### 4.2 Confidence Calculation

**Blueprint** (real):
```python
# app/services/contour_scoring.py:352

confidence = float(best.score)  # Actual scorer output
```

**Photo** (fabricated):
```python
# app/routers/photo_vectorizer_router.py:470-471

dimensions = Dimensions(
    ...
    confidence=0.9 if is_valid else 0.0  # ◄── FABRICATED
)
```

**Problem**: Photo frontend receives meaningless confidence. Should use `result.ownership_score` instead.

### 4.3 Warning Aggregation

**Blueprint** (fixed aliasing bug):
```python
# app/services/blueprint_orchestrator.py:185

warnings: list[str] = []

# Warnings appended in-place by:
# - extract_pdf_page() at line 212
# - extract_blueprint_to_dxf() at line 235
# - validate_cleanup_result() at line 274
# - orchestrator directly at lines 318, 320
```

**Photo** (two sources merged):
```python
# app/routers/photo_vectorizer_router.py:483

all_warnings = list(result.warnings) + validation_errors
```

---

## 5. Validation Thresholds

### 5.1 Current Locations (Duplicated)

```python
# app/services/blueprint_orchestrator.py:130-131
SVG_MIN_CHARS = 50
DXF_MIN_BYTES = 800

# app/routers/photo_vectorizer_router.py:185-186
SVG_MIN_CHARS = 50       # DUPLICATE
DXF_MIN_BYTES = 800      # DUPLICATE
```

### 5.2 Recommended Consolidation

```python
# app/services/blueprint_limits.py (add these)

class LIMITS:
    # ... existing limits ...
    
    # Artifact validation thresholds
    svg_min_chars: int = 50
    dxf_min_bytes: int = 800
    
    # Confidence thresholds
    min_confidence_warning: float = 0.45
    
    # Ownership thresholds
    blueprint_ownership_weight: float = 0.10  # Soft signal
    photo_ownership_threshold: float = 0.60  # Hard gate
```

---

## 6. DXF Compatibility Rules

**Documented in**: `CLAUDE.md` "Blueprint Export Compatibility"

```
Output format: R12 (AC1009)
Geometry entities: LINE only
Forbidden: LWPOLYLINE (causes ezdxf errors on R12, Fusion freezes)
```

**Enforced at**:

```python
# app/cam/unified_dxf_cleaner.py

def write_selected_chains(...):
    # BLUEPRINT DXF EXPORT RULE (Fusion compatibility)
    # Output format: R12 (AC1009)
    # Geometry entities: LINE only
    doc = ezdxf.new('R12')
    msp = doc.modelspace()
    for i, (x1, y1, x2, y2) in enumerate(segments):
        msp.add_line((x1, y1), (x2, y2))  # ◄── LINE only
```

**Validation at**:

```python
# app/services/blueprint_orchestrator.py:299-307

# VALIDATION EXPECTATION (Fusion compatibility):
#   - DXF version: R12 (AC1009)
#   - Entity type: LINE only (no LWPOLYLINE)
#   - See CLAUDE.md "Blueprint Export Compatibility"
dxf_entity_count = (
    dxf_text.count("\nLINE\n") +
    dxf_text.count("\nLWPOLYLINE\n")  # Should be 0 for R12
)
```

---

## 7. Identified Issues

### 7.1 High Priority

#### Issue: Photo Confidence Fabrication

**Location**: `app/routers/photo_vectorizer_router.py:470`

```python
# CURRENT (wrong)
confidence=0.9 if is_valid else 0.0

# SHOULD BE
confidence=getattr(result, 'ownership_score', 0.0)
```

**Impact**: Frontend cannot make informed decisions about result quality.

### 7.2 Medium Priority

#### Issue: Missing Recommendation System

**Location**: Neither pipeline

**Proposed Schema**:

```python
class Recommendation(BaseModel):
    action: str  # "accept", "review", "reject", "retry_with_params"
    reason: str
    suggested_params: Optional[dict] = None

# Add to response
recommendation: Optional[Recommendation] = None
```

**Logic**:
- confidence >= 0.70 → "accept"
- 0.45 <= confidence < 0.70 → "review"
- confidence < 0.45 → "retry_with_params" or "reject"

#### Issue: Ownership Behavioral Divergence

**Blueprint**: 10% soft weight, always returns result with warnings  
**Photo**: Hard gate at 0.60, blocks export entirely

**Options**:
1. Document as intentional (different use cases)
2. Align to soft signal for both
3. Make threshold configurable per-request

### 7.3 Low Priority

#### Issue: Legacy Response Fields

**Location**: `app/routers/photo_vectorizer_router.py:163-179`

**Action**: Mark deprecated in OpenAPI schema, remove after frontend migration.

#### Issue: Duplicate Threshold Constants

**Action**: Move to `blueprint_limits.py` as single source of truth.

---

## 8. Test Coverage

### 8.1 Regression Test Set (Validated 2026-04-11)

| Test | Blueprint | Status | Confidence | Contours | Warnings |
|------|-----------|--------|------------|----------|----------|
| 1 | Gibson Explorer PNG | PASS | 0.553 | 11 | 2 |
| 2 | Gibson Explorer PDF | PASS | 0.535 | 6 | 4 |
| 3 | El Cuatro PDF | PASS | 0.670 | 4 | 2 |
| 4 | Melody Maker PDF | PASS | 0.610 | 6 | 4 |

### 8.2 Key Test Files

```
tests/test_blueprint_orchestrator.py
tests/test_contour_scoring.py
tests/test_blueprint_clean.py
services/photo-vectorizer/test_contour_plausibility_ownership.py
services/photo-vectorizer/test_body_ownership_score.py
```

---

## 9. Recommended Actions

### Phase 1: Quick Wins (Low Risk)

1. **Fix Photo confidence** — use `result.ownership_score`
2. **Centralize thresholds** — move to `blueprint_limits.py`
3. **Deprecate legacy fields** — add OpenAPI deprecation markers

### Phase 2: Structural (Medium Risk)

4. **Add recommendation field** — orchestrator decides action
5. **Create Photo orchestrator** — extract business logic from router
6. **Document ownership divergence** — or align to single strategy

### Phase 3: Future (Deferred)

7. **Remove legacy fields** — after frontend migration
8. **Unified scoring module** — share between pipelines
9. **AGE integration** — per CLAUDE.md vectorizer architecture

---

## 10. File Reference Index

| Purpose | Blueprint | Photo |
|---------|-----------|-------|
| Router | `app/routers/blueprint/vectorize_router.py` | `app/routers/photo_vectorizer_router.py` |
| Async Router | `app/routers/blueprint_async_router.py` | N/A |
| Orchestrator | `app/services/blueprint_orchestrator.py` | **Missing (in router)** |
| Extraction | `app/services/blueprint_extract.py` | `services/photo-vectorizer/photo_vectorizer_v2.py` |
| Cleanup | `app/services/blueprint_clean.py` | N/A |
| Scoring | `app/services/contour_scoring.py` | `services/photo-vectorizer/contour_plausibility.py` |
| DXF I/O | `app/cam/unified_dxf_cleaner.py` | `services/photo-vectorizer/edge_to_dxf.py` |
| Limits | `app/services/blueprint_limits.py` | Hardcoded in router |
| Tests | `tests/test_blueprint_*.py` | `services/photo-vectorizer/test_*.py` |

---

## Appendix A: Ownership Score Formula

### Blueprint (Weighted Signal)

```python
# app/services/contour_scoring.py:286-295

score = (
    0.35 * area_ratio_normalized +
    0.25 * closure_score +
    0.10 * aspect_score +
    0.15 * solidity_score +
    0.05 * continuity_score +
    0.10 * ownership_score  # From ContourPlausibilityScorer
)
```

### Photo (Hard Gate)

```python
# services/photo-vectorizer/contour_plausibility.py:89-94

ownership = (
    0.50 * completeness +
    0.25 * vertical_coverage +
    0.10 * (1.0 - border_contact) +
    0.15 * (1.0 - neck_inclusion)
)

# Hard penalties
if vertical_coverage < 0.45: ownership -= 0.15
if border_contact > 0.30: ownership -= 0.10
if neck_inclusion > 0.25: ownership -= 0.20
if completeness < 0.55: ownership -= 0.10

# Gate decision
ownership_ok = ownership >= 0.60
```

---

## Appendix B: Stage Values

| Stage | Meaning | Blueprint | Photo |
|-------|---------|-----------|-------|
| `upload` | File validation failed | Yes | No |
| `image_extract` | PDF rasterization failed | Yes | No |
| `edge_extraction` | Canny/edge detection failed | Yes | No |
| `cleanup` | Contour filtering failed | Yes | No |
| `contour_detection` | Body isolation failed | No | Yes |
| `svg_generation` | SVG creation failed | No | Yes |
| `dxf_generation` | DXF creation failed | No | Yes |
| `validation` | Artifact validation failed | Yes | Yes |
| `complete` | Success | Yes | Yes |
| `error` | Uncaught exception | Yes | No |

---

*End of Developer Handoff Document*
