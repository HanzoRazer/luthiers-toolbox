# Systems Engineering Review: Instrument Body Generator (IBG)

**Date:** 2026-04-19  
**Reviewer:** Production Shop  
**Sprint:** 9 — InstrumentBodyGenerator  
**Status:** Code Complete, Pending Production Validation

---

## 1. Purpose

The Instrument Body Generator (IBG) solves the "82-88% capture" problem in blueprint vectorization. When the vectorizer extracts a guitar body outline from a scanned blueprint, gaps remain where edges were unclear, lines crossed, or detail was lost. IBG takes this partial outline and completes it into a manufacturable closed contour.

**Core problem statement:**  
Given a partial DXF outline + instrument class → produce a complete parametric body model with:
- Closed, clean outline (no gaps, no self-intersections)
- Side heights at every point (Sevy formula)
- Zone radii for brace fitting
- Confidence score for quality gating

**Business value:**  
- Enables luthiers to use scanned blueprints directly without manual cleanup
- Differentiates free tier (vectorizer only) from paid tier (IBG completion + manual override)

---

## 2. Users

| User Type | Interaction Mode | Tier |
|-----------|------------------|------|
| Hobbyist luthier | Upload partial DXF via web UI, receive completed outline | Free |
| Professional luthier | Upload + manual landmark override | Paid |
| Production shop | API integration, batch processing | Paid |
| Frontend (Body Outline Editor v2.x) | `/api/body/solve-from-dxf` endpoint | Both |

---

## 3. Requirements Traceability

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Complete partial outline to closed contour | `BodyContourSolver._generate_outline()` | DONE |
| Calculate side heights at every point | `solve_side_height()` using Sevy formula | DONE |
| 4-tier gap bridging with graceful degradation | `ArcReconstructor.complete()` | DONE |
| Reference outline from known instrument specs | `ReferenceOutlineBridge.bridge_gap()` | DONE |
| Extract landmarks from partial DXF | `ConstraintExtractor.extract_landmarks_from_dxf()` | DONE |
| Validate dimensions against spec | `InstrumentBodyGenerator.validate_against_expected()` | DONE |
| Self-intersection detection | `check_self_intersection()` | DONE |
| DXF export (R12 format) | `outline_to_dxf()` | DONE |
| Async API endpoints | `body_solver_router.py` with `run_in_executor` | DONE |
| Session persistence | In-memory dict (TODO: Redis) | PARTIAL |
| Paid tier authentication | Decorator stub (TODO: real auth) | STUB |

---

## 4. Strengths

### 4.1 Mathematical Foundation
The system is built on peer-reviewed lutherie mathematics:
- **Sevy formula** (American Lutherie #58): High point calculation from body length, depths, and back radius
- **Mottola formula** (American Lutherie #78): Side height at distance D from high point
- **Woodworker's radius formula**: R = (C²/8S) + (S/2) for arc fitting

Verification block in `body_contour_solver.py:832-913` validates against Mottola spreadsheet values:
```
P = 3.093 in (expect 3.093, tolerance +/- 0.01)
H = 3.824 in (expect 3.824, tolerance +/- 0.01)
```

### 4.2 Graceful Degradation
4-tier gap bridging ensures the system never fails silently:
- **Tier 0**: Reference outline from `body_outlines.json` (most accurate)
- **Tier 1**: Radius measured from adjacent chain
- **Tier 2**: Spherical arch formula (when arch radius known)
- **Tier 3**: Zone lookup table (fallback)

If scipy is unavailable, `reference_outline_bridge.py:98` falls back to linear interpolation.

### 4.3 Edge Case Guards
Guards throughout prevent domain errors on solid-body electrics:
```python
# body_contour_solver.py:88-90
if math.isinf(R) or R > 1e9:
    return L / 2  # Flat body — high point at center
```

### 4.4 Clean Module Structure
The `__init__.py` exports provide a clear public API:
```python
from app.instrument_geometry.body.ibg import InstrumentBodyGenerator
gen = InstrumentBodyGenerator(spec_name='dreadnought')
```

### 4.5 Async-Ready API Layer
`body_solver_router.py` uses `run_in_executor` for all blocking ezdxf calls, preventing event loop starvation in production.

---

## 5. Weaknesses

### 5.1 In-Memory Session Storage
`body_solver_router.py:59-60`:
```python
# TODO: Migrate to Redis before multi-worker deployment.
_sessions: Dict[str, Dict] = {}
```
Sessions are lost on restart and don't work with multiple workers.

### 5.2 Auth Stub
`body_solver_router.py:37-51`:
```python
def requires_paid_tier(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # TODO: Implement real auth check
        return await func(*args, **kwargs)
    return wrapper
```
Paid tier endpoints are currently unprotected.

### 5.3 Limited Instrument Specs
Only 4 specs defined in `INSTRUMENT_SPECS`:
- dreadnought
- cuatro_venezolano
- stratocaster
- jumbo

Missing: OM, parlour, classical, archtop, F-style mandolin.

### 5.4 Reference Outline Alignment
`reference_outline_bridge.py:149-181` uses bounding box matching (scale + translate, no rotation). If the extracted geometry is rotated relative to the reference, alignment fails.

### 5.5 No Production Tests
`Glob("**/ibg/test_*.py")` returned no files. The module has verification blocks (`if __name__ == "__main__"`) but no pytest test suite.

---

## 6. Failure Modes

| Failure Mode | Detection | Mitigation |
|--------------|-----------|------------|
| Self-intersecting outline | `check_self_intersection()` warns at export | Review geometry before cutting |
| Landmark extraction fails (all confidence < 0.5) | Confidence score in response | Fall back to family defaults |
| Gap too large (> 50mm from reference) | `ReferenceOutlineBridge.bridge_gap()` returns None | Tier 2/3 fallback |
| Chord > 2*radius in arc generation | `_circle_center()` returns None | Double radius and retry |
| scipy unavailable | `SCIPY_AVAILABLE` flag | Linear interpolation fallback |
| Session lost on restart | No detection | TODO: Redis persistence |

---

## 7. Alternatives Considered

### 7.1 Pure Edge Detection (rejected)
Edge detection alone cannot close gaps caused by blueprint defects. IBG's constraint-based completion is more robust.

### 7.2 ML-based Outline Prediction (deferred)
Training a model to predict guitar outlines was considered but requires large labeled dataset. IBG's parametric approach works with 4 landmarks.

### 7.3 Manual-only Completion (rejected)
Requiring users to manually close all gaps is too labor-intensive for hobbyist tier.

---

## 8. Recommendations

### 8.1 Critical (before production)
1. **Implement Redis session storage** — current in-memory dict breaks with multiple workers
2. **Implement real auth check** — paid tier endpoints are unprotected
3. **Add pytest test suite** — module has no automated tests

### 8.2 Important (before scale)
1. **Add more instrument specs** — OM, parlour, classical at minimum
2. **Add rotation to alignment** — current bbox-only alignment fails on rotated inputs
3. **Integrate with feedback loop** — wire successful completions back to vectorizer training

### 8.3 Nice-to-have
1. **Batch processing endpoint** — for production shops processing multiple blueprints
2. **Export to other formats** — STEP, SVG for broader CAM compatibility
3. **Side height visualization** — 3D preview in Body Outline Editor

---

## 9. Open Questions

1. **Cuatro back radius**: `body_contour_solver.py:177` notes "Estimated — needs physical measurement". What is the actual back radius for cuatro venezolano?

2. **Confidence threshold**: What confidence score should gate "ready for CAM" vs "needs review"? Currently no threshold enforced.

3. **Reference outline source**: `body_outlines.json` contains 110KB of waypoint data. What was the source? Measured from physical instruments or derived from blueprints?

4. **Temp file cleanup**: `instrument_body_generator.py:208-210` has best-effort cleanup. Should this be more robust (atexit handler)?

---

## 10. File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 55 | Module exports |
| `instrument_body_generator.py` | 433 | Main generator class, spec library |
| `body_contour_solver.py` | 914 | Sevy formulas, outline generation, DXF export |
| `constraint_extractor.py` | 305 | Landmark extraction from partial DXF |
| `arc_reconstructor.py` | 1,612 | 4-tier gap bridging, chain consolidation |
| `reference_outline_bridge.py` | 485 | Tier 0 reference outline from JSON |
| `body_solver_router.py` | 435 | FastAPI endpoints |
| **Total** | **4,239** | |

---

## 11. API Endpoints

| Endpoint | Method | Tier | Description |
|----------|--------|------|-------------|
| `/api/body/solve-from-dxf` | POST | Free | Upload partial DXF, receive solved model |
| `/api/body/solve-from-landmarks` | POST | Paid | Submit user-provided landmarks |
| `/api/body/session/{id}` | GET | Both | Retrieve previously solved session |
| `/api/body/session/{id}/landmarks` | PUT | Paid | Override landmarks and re-solve |

---

## 12. Dependencies

| Dependency | Purpose | Optional? |
|------------|---------|-----------|
| ezdxf | DXF read/write | Required |
| scipy | Spline interpolation | Optional (graceful fallback) |
| numpy | Array operations | Required |
| fastapi | API framework | Required for endpoints |
| pydantic | Request validation | Required for endpoints |

---

## 13. Conclusion

The IBG module is **architecturally sound** and implements the correct lutherie mathematics. The 4-tier gap bridging with graceful degradation is well-designed. The async API layer is production-ready.

**Critical gaps** before production:
1. Redis session storage
2. Real authentication
3. Automated test suite

**Ready for:** Development/staging testing with known blueprints  
**Not ready for:** Multi-worker production deployment or paid tier billing

---

*Review conducted against commit: ec4844bd (feat(ibg): Week 2 — run_in_executor + DXF export as base64)*
