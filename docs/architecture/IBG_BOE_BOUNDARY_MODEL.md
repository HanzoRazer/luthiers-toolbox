# IBG / BOE Boundary Model

**Status:** CANONICAL ARCHITECTURE  
**Effective:** 2026-05-12  
**Source:** IBG-2A Audit

---

## Boundary Definition

```
IBG (Image Body Generator)
  = Deterministic morphology reconstruction
  = Parametric geometry solver
  = Math authority (Sevy/Mottola)
  = Confidence-weighted output

BOE (Body Outline Editor)
  = Human correction surface
  = Visual editing authority
  = Approval gate
  = Export origin
```

---

## Authority Model

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   IBG: SOLVER AUTHORITY                                      │
│   - Owns: Lutherie math, constraint solving, gap bridging    │
│   - Produces: Confidence-weighted geometry                   │
│   - Cannot: Override human decisions                         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   BOUNDARY: JSON API Response                                │
│   - outline_points, dimensions, confidence                   │
│   - No direct file exchange (DXF flows via API)              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   BOE: HUMAN AUTHORITY                                       │
│   - Owns: Final geometry approval                            │
│   - Can: Edit any IBG output                                 │
│   - Produces: Approved body geometry (truth for downstream)  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Primary Path (API Integration)

```
Vectorizer partial DXF
    │
    ▼
IBG: complete_from_dxf()
    │
    ▼
SolvedBodyModel (JSON)
    │
    ├─► outline_points ──► BOE: replace path
    ├─► dimensions ──────► BOE: display
    ├─► confidence ──────► BOE: badge
    └─► session_id ──────► BOE: localStorage
    
    ▼
User edits in BOE
    │
    ▼
BOE: DXF/JSON export
    │
    ▼
CAM pipeline
```

### Correction Path (Re-solve)

```
BOE: User edits landmarks
    │
    ▼
BOE: pathToLandmarks()
    │
    ▼
PUT /session/{id}/landmarks
    │
    ▼
IBG: complete_from_landmarks()
    │
    ▼
New SolvedBodyModel
    │
    ▼
BOE: replace path (optional)
```

---

## Schema Contracts

### IBG → BOE

```typescript
interface IBGResponse {
  session_id: string;
  status: "completed";
  confidence: number;           // 0.0-1.0
  dimensions: {
    body_length_mm: number;
    lower_bout_mm: number;
    upper_bout_mm: number;
    waist_mm: number;
    waist_y_norm: number;       // 0.0-1.0
  };
  outline_points: [number, number][];  // [[x, y], ...]
  side_heights?: number[];
  radii_by_zone?: Record<string, number>;
  missing_landmarks: string[];
  back_radius_source: "spec" | "estimated" | "measured";
}
```

### BOE → IBG

```typescript
interface LandmarkInput {
  label: "lower_bout_max" | "waist_min" | "upper_bout_max" | 
         "butt_center" | "neck_center";
  x_mm: number;
  y_mm: number;
  source: "user_input" | "user_override" | "user_added";
  confidence: number;           // 0.0-1.0
}

interface SolveRequest {
  instrument_spec: string;      // "dreadnought" | "cuatro_venezolano" | etc.
  landmarks: LandmarkInput[];
  options?: {
    return_side_heights?: boolean;
    return_zone_radii?: boolean;
    return_dxf?: boolean;
  };
}
```

---

## Governance Alignment

| System | MRP Layer | Protection Level |
|--------|-----------|------------------|
| IBG math engine | IBG Morphology Layer | LOCKED |
| IBG API contract | IBG Morphology Layer | LOCKED |
| BOE editing | BOE Layer | AUTHORITATIVE |
| BOE export | BOE Layer | AUTHORITATIVE |

From `MORPHOLOGY_RECONSTRUCTION_PLATFORM.md`:

> Agents may NOT... Bypass BOE authority

---

## Ownership Boundaries

### IBG Owns

- Landmark extraction from DXF
- Constraint solving (Sevy/Mottola formulas)
- Gap bridging (4-tier fallback)
- Side height calculation
- Zone radius calculation
- Confidence scoring
- DXF generation (via dxf_writer)

### BOE Owns

- Visual geometry editing
- Node/handle manipulation
- Calibration from reference images
- Template library
- Mirror mode symmetry
- Export format selection
- Final approval decision

### Neither Owns (Platform)

- Session persistence (Redis — backend)
- Authentication (backend)
- User identity (backend)
- Morphology corpus (future)
- CAM toolpath generation (downstream)

---

## Integration Points

| Point | Type | Status |
|-------|------|--------|
| `/api/body/solve-from-dxf` | POST | Free tier |
| `/api/body/solve-from-landmarks` | POST | Paid tier |
| `/api/body/session/{id}` | GET | Both tiers |
| `/api/body/session/{id}/landmarks` | PUT | Paid tier |

All endpoints return `IBGResponse` schema.

---

## Non-Goals

This boundary model does NOT address:

- Loop 2 learning (cross-image caching) — IBG is deterministic
- Loop 3 retraining (user corrections → ML) — IBG uses math, not ML
- STEP/CAD export — future Export Object layer
- 3D visualization — future BOE feature
- Morphology corpus — future platform feature

---

*Canonical boundary model. IBG = solver. BOE = human authority.*
