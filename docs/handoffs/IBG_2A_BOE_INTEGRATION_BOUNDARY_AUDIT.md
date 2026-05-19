# IBG-2A: BOE Integration Boundary Audit

**Date:** 2026-05-12  
**Sprint:** IBG-2A  
**Status:** AUDIT COMPLETE

---

## Executive Summary

This audit defines the boundary between IBG (deterministic morphology reconstruction) and BOE (human-authoritative correction/editing surface). The integration path is **largely compatible** — BOE already has an API client for IBG, and schema alignment is close. No adapters are required for the core flow.

**Key finding:** The integration is already scaffolded but operates in mock mode only. Production deployment is blocked by backend infrastructure (Redis, auth).

---

## 1. IBG Output Contract

### 1.1 SolvedBodyModel Dataclass

**Location:** `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py:58-72`

```python
@dataclass
class SolvedBodyModel:
    body_length_mm: float
    lower_bout_width_mm: float
    upper_bout_width_mm: float
    waist_width_mm: float
    waist_y_norm: float                         # 0.0-1.0
    outline_points: List[Tuple[float, float]]   # full perimeter, clockwise
    side_heights_mm: List[float]                # height at each outline point
    radii_by_zone: Dict[str, float]             # waist, lower_bout, upper_bout
    confidence: float
    missing_landmarks: List[str]
    landmarks: Dict[str, LandmarkPoint]
    back_radius_source: str                     # "spec" | "estimated" | "measured"
```

### 1.2 API Response Schema

**Location:** `services/api/app/routers/body_solver_router.py:155-189`

```json
{
  "session_id": "sess_abc12345",
  "status": "completed",
  "confidence": 0.87,
  "dimensions": {
    "body_length_mm": 521.3,
    "lower_bout_mm": 382.1,
    "upper_bout_mm": 293.5,
    "waist_mm": 240.8,
    "waist_y_norm": 0.442
  },
  "outline_points": [[0, 0], [190.5, 80.0], ...],
  "side_heights": [94.2, 95.1, ...],
  "radii_by_zone": {
    "lower_bout": 265.3,
    "waist": 85.2,
    "upper_bout": 175.6
  },
  "missing_landmarks": [],
  "landmarks_extracted": [...],
  "back_radius_source": "spec",
  "dxf_data": "<base64>" // optional
}
```

### 1.3 DXF Output

- Format: R12 via `dxf_writer.py`
- Layers: `BODY_SOLVED` (red), `CENTERLINE` (blue), `LANDMARKS` (green)
- Entities: LINE only (R12 standard)
- Validated for self-intersection before export

---

## 2. BOE Input Contract

### 2.1 Current Input Methods

**Location:** `hostinger/body-outline-editor.html`

| Input Method | Description | Status |
|--------------|-------------|--------|
| Direct drawing | Bezier path editing with nodes/handles | PRODUCTION |
| Template loading | 8 built-in presets (Dreadnought, Jumbo, etc.) | PRODUCTION |
| Image calibration | Reference photos with scale calibration | PRODUCTION |
| Session files | `.sgession` JSON state restore | PRODUCTION |
| IBG API response | `outline_points` from solve endpoint | MOCK ONLY |

### 2.2 What BOE CANNOT Import

| Format | Status | Notes |
|--------|--------|-------|
| DXF files | NOT SUPPORTED | Export only, no import parser |
| Raw SVG | NOT SUPPORTED | Export only |
| IBG DXF output | NOT SUPPORTED | Must use API response instead |

### 2.3 Landmark Schema (BOE → IBG)

**Location:** `hostinger/body-outline-editor.html:1072-1153` (`pathToLandmarks()`)

```javascript
{
  label: "lower_bout_max" | "waist_min" | "upper_bout_max" | "butt_center" | "neck_center",
  x_mm: float,
  y_mm: float,
  source: "user_input",
  confidence: 1.0
}
```

This matches the `LandmarkInput` Pydantic model in `body_solver_router.py:66-72`.

---

## 3. Schema Compatibility Table

| IBG Output Field | BOE Consumer | Compatibility | Notes |
|------------------|--------------|---------------|-------|
| `outline_points` | Path replacement | **DIRECT_COMPATIBLE** | BOE converts [[x,y],...] to Bezier path |
| `dimensions.*` | Bounding box display | **DIRECT_COMPATIBLE** | Displayed in UI |
| `confidence` | Confidence badge | **DIRECT_COMPATIBLE** | Green/amber/orange based on value |
| `session_id` | Session resume | **DIRECT_COMPATIBLE** | Stored in localStorage |
| `side_heights` | N/A | **FUTURE_LEARNING** | No 3D visualization yet |
| `radii_by_zone` | N/A | **FUTURE_LEARNING** | Could inform brace fitting UI |
| `landmarks_extracted` | Landmark overlay | **ADAPTER_REQUIRED** | BOE doesn't visualize landmarks |
| `dxf_data` | N/A | **BLOCKED** | BOE cannot import DXF |

| BOE Output | IBG Consumer | Compatibility | Notes |
|------------|--------------|---------------|-------|
| `pathToLandmarks()` | `/solve-from-landmarks` | **DIRECT_COMPATIBLE** | Schema matches exactly |
| User corrections | Session override | **DIRECT_COMPATIBLE** | Via `PUT /session/{id}/landmarks` |
| Exported DXF | IBG input | **INDIRECT** | Would need `/solve-from-dxf` endpoint |

---

## 4. Correction Authority Model

### 4.1 Design Decision: CONFIRMED

**Source:** `docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md:46`

```
| BOE | Human correction/editor | AUTHORITATIVE |
```

**Governance rule:** `docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md:111`

```
Agents may NOT... Bypass BOE authority
```

### 4.2 Authority Flow

```
IBG Solved Geometry (confidence-weighted)
  → BOE receives outline_points
  → User edits/approves in BOE
  → BOE-approved geometry becomes AUTHORITATIVE
  → Downstream consumers (CAM, export) use BOE output
```

### 4.3 Implementation Status

| Aspect | Status | Evidence |
|--------|--------|----------|
| Design decision | DESIGN_DECISION_CONFIRMED | MRP governance doc |
| IBG → BOE flow | IMPLEMENTATION_PRESENT | `InstrumentBodyAPI` in BOE |
| BOE authority | IMPLEMENTATION_PRESENT | User can edit any solved geometry |
| BOE → downstream | IMPLEMENTATION_PRESENT | DXF/JSON export from BOE |
| Feedback loop (BOE → IBG learning) | IMPLEMENTATION_MISSING | No correction capture |

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UPSTREAM                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Blueprint Reader Vectorizer                                         │
│      │                                                               │
│      ▼ partial DXF (82-88% complete)                                │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │ IBG: Morphology Reconstruction                             │      │
│  │   - complete_from_dxf() or                                 │      │
│  │   - complete_from_landmarks()                              │      │
│  │   - generate_from_defaults()                               │      │
│  └───────────────────────────────────────────────────────────┘      │
│      │                                                               │
│      ▼ SolvedBodyModel (JSON response)                              │
├─────────────────────────────────────────────────────────────────────┤
│                    INTEGRATION BOUNDARY                              │
├─────────────────────────────────────────────────────────────────────┤
│      │                                                               │
│      ▼ outline_points, dimensions, confidence                       │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │ BOE: Human Authority Layer                                 │      │
│  │   - Display solved geometry                                │      │
│  │   - User edits (move nodes, adjust curves)                 │      │
│  │   - Confidence-informed review                             │      │
│  │   - Manual landmark override → re-solve                    │      │
│  └───────────────────────────────────────────────────────────┘      │
│      │                                                               │
│      ▼ APPROVED BODY GEOMETRY (user-approved truth)                 │
├─────────────────────────────────────────────────────────────────────┤
│                         DOWNSTREAM                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Export: DXF / JSON / SVG                                           │
│      │                                                               │
│      ▼                                                               │
│  CAM Pipeline / Fusion 360 / Manufacturing                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Missing Adapters

### 6.1 Landmark Visualization (ADAPTER_REQUIRED)

**Gap:** IBG returns `landmarks_extracted` but BOE doesn't display them.

**Impact:** User cannot see which landmarks IBG detected, making it harder to understand why confidence is low.

**Proposed adapter:**
```javascript
function displayExtractedLandmarks(landmarks) {
  landmarks.forEach(lm => {
    // Draw circle at lm.x, lm.y
    // Color by lm.confidence (green > 0.7, amber 0.4-0.7, red < 0.4)
    // Label with lm.label
  });
}
```

**Priority:** Medium — improves UX but not blocking.

### 6.2 DXF Import (BLOCKED)

**Gap:** BOE cannot import DXF files. IBG can output DXF (`save_dxf()`) but BOE cannot consume it.

**Impact:** Users cannot load IBG DXF output into BOE for editing. Must use API response path.

**Resolution:** Not needed for primary flow (API response provides `outline_points`). DXF import would be a separate feature request.

**Priority:** Low — API flow is sufficient.

### 6.3 Side Heights Visualization (FUTURE_LEARNING)

**Gap:** IBG provides `side_heights_mm` at every outline point but BOE cannot visualize 3D geometry.

**Impact:** Lutherie-critical information (side height for bending) is available but not visible.

**Future work:** 3D preview mode in BOE or separate viewer.

**Priority:** Future sprint — documented in IBG_SYSTEMS_ENGINEERING_REVIEW.md.

---

## 7. Integration Blockers

| Blocker | Owner | Impact | Status |
|---------|-------|--------|--------|
| Mock mode only | Backend | BOE cannot call real IBG API | BLOCKED |
| In-memory sessions | Backend | Sessions lost on restart | BLOCKED |
| Auth stub | Backend | Paid tier unprotected | BLOCKED |
| Redis not wired | Backend | Multi-worker fails | BLOCKED |
| DXF import | Frontend | Cannot load DXF directly | LOW PRIORITY |

**Primary blocker:** Backend infrastructure from `IBG_BACKEND_COORDINATION.md`:
1. Redis session storage
2. Real Bearer token auth
3. Rate limiting
4. CORS configuration

---

## 8. Persistence Model

### 8.1 Current State

| Layer | Persistence | Location |
|-------|-------------|----------|
| BOE local state | localStorage | Browser (24h auto-save) |
| BOE session files | .sgession JSON | User download |
| IBG session | In-memory dict | API server (dies on restart) |

### 8.2 Proposed Model

| Stage | Persistence | Owner |
|-------|-------------|-------|
| IBG solved geometry | Redis session (24h TTL) | API server |
| BOE working state | localStorage | Browser |
| BOE-approved geometry | Export (DXF/JSON) | User |
| Future: RMOS artifact | Database | Platform |
| Future: morphology corpus | Versioned store | Platform |

---

## 9. Feedback Direction

### 9.1 Current State

**BOE → IBG correction feedback:** NOT IMPLEMENTED

When a user corrects IBG geometry in BOE, the correction is:
- Saved locally (localStorage)
- Exported to DXF/JSON
- NOT sent back to IBG for learning

### 9.2 Future Architecture (Document Only)

Per CLAUDE.md "VECTORIZER ARCHITECTURE DECISION":

```
Loop 3 — User Correction Retraining
  When a user corrects a bad DXF, that correction is ground truth.
  Feed it back into the classifier. The FeedbackSystem and
  TrainingDataCollector already exist in the code but are NEVER CALLED.
```

**For IBG specifically:**
- FeedbackSystem: Does not exist in IBG (vectorizer only)
- Correction capture: Would need new endpoint
- Learning system: Out of scope (IBG is deterministic math, not ML)

**Recommendation:** Corrections should flow to morphology corpus (future), not to IBG math. IBG math is LOCKED per governance.

---

## 10. Classification Summary

| Integration Point | Classification | Notes |
|-------------------|----------------|-------|
| IBG outline_points → BOE path | DIRECT_COMPATIBLE | Works today (mock mode) |
| IBG dimensions → BOE display | DIRECT_COMPATIBLE | Works today |
| IBG confidence → BOE badge | DIRECT_COMPATIBLE | Works today |
| BOE landmarks → IBG solve | DIRECT_COMPATIBLE | Schema matches |
| BOE corrections → IBG session | DIRECT_COMPATIBLE | PUT endpoint exists |
| IBG DXF → BOE import | BLOCKED | BOE cannot import DXF |
| IBG landmarks → BOE visualization | ADAPTER_REQUIRED | BOE needs landmark overlay |
| IBG side_heights → BOE 3D | FUTURE_LEARNING | No 3D viewer |
| BOE corrections → Learning | FUTURE_LEARNING | Out of IBG scope |

---

## 11. Recommended Next Sprint

**Sprint IBG-2B: Production Infrastructure**

1. Implement Redis session storage
2. Implement real Bearer token auth
3. Configure rate limiting (10/hr free, 100/hr paid)
4. Configure CORS for production domain
5. Set `useMock = false` in BOE
6. End-to-end integration test

**Sprint IBG-2C: UX Improvements (Optional)**

1. Add landmark visualization to BOE
2. Add confidence explanation tooltip
3. Add "why low confidence" diagnostic

---

## 12. Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| No code behavior changed | ✅ Audit only |
| IBG output schema documented | ✅ Section 1 |
| BOE input schema documented | ✅ Section 2 |
| Integration gap is clear | ✅ Sections 3, 6, 7 |
| Correction authority is defined | ✅ Section 4 |
| Next implementation step is obvious | ✅ Section 11 |

---

## References

- `docs/handoffs/IBG_FUNCTIONAL_CAPABILITY_ASSESSMENT_2026-05-11.md`
- `docs/handoffs/IBG_BACKEND_COORDINATION.md`
- `docs/handoffs/BODY_OUTLINE_EDITOR_V2_HANDOFF.md`
- `docs/Body_Outline_Editor_User_Manual.md`
- `docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md`
- `docs/governance/IBG_ROLE_DEFINITION.md`
- `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py`
- `services/api/app/routers/body_solver_router.py`
- `hostinger/body-outline-editor.html`

---

*IBG-2A audit complete. Integration boundary defined. Next: IBG-2B production infrastructure.*
