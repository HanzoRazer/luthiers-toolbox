# Acoustic CAD Semantic Rules

**Sprint:** MRP-5E  
**Status:** ACTIVE  
**Authority:** CAD Translation Governance

---

## Purpose

Define the authority boundaries and semantic rules governing acoustic body CAD translation. These rules extend the existing CAD translator governance for the acoustic body domain.

---

## Authority Hierarchy

```
┌─────────────────────────────────────────────────┐
│           BOE (Body Outline Engine)             │
│         GEOMETRY APPROVAL AUTHORITY             │
│   - Profile outline (x, y coordinates)          │
│   - Approved via RMOS green-gate                │
│   - READ-ONLY to all downstream consumers       │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│        IBG (Instrument Body Generator)          │
│         ADVISORY MORPHOLOGY AUTHORITY           │
│   - Side depths, radii, dimensions              │
│   - Lutherie-derived measurements               │
│   - May be overridden by user input             │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              cad_semantics Extension            │
│           CAD CONSTRUCTION HINTS                │
│   - Body type classification                    │
│   - Thickness hierarchy level                   │
│   - Surface type selections                     │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              CAD Translator                     │
│        TOPOLOGY CONSTRUCTION AUTHORITY          │
│   - STEP entity generation                      │
│   - Surface construction                        │
│   - Topology validation                         │
└─────────────────────────────────────────────────┘
```

---

## Core Semantic Rules

### Rule 1: Geometry Non-Mutation

**Statement:** The CAD translator may NOT alter, reinterpret, or substitute coordinates approved by BOE.

**Applies To:**
- Profile outline points
- Spline control points
- Arc/circle centers and radii

**Allowed:**
- Format conversion (JSON → STEP)
- Precision formatting (6 decimal places)
- Entity ordering for determinism

**Violation Examples:**
- Smoothing sharp corners
- Resampling profile points
- Adjusting dimensions for "better" proportions

### Rule 2: Semantic Extension Only

**Statement:** cad_semantics may EXTEND context from IBG. It may NOT OVERRIDE geometry approved by BOE.

**Extension Examples (ALLOWED):**
- Adding `body_type: "acoustic"` classification
- Adding `back_surface_type: "radiused"`
- Adding thickness values from IBG

**Override Examples (FORBIDDEN):**
- Changing outline coordinates
- Substituting a "standard" body shape
- Adjusting soundhole position

### Rule 3: Advisory Consumption

**Statement:** IBG morphology data is advisory. Translator CONSUMES but does not require all fields.

**Required Fields (for acoustic body):**
- None mandatory at MRP-5E

**Optional Fields (consumed if present):**
- `side_heights_mm` → rim depth profile
- `butt_depth_mm` → tail depth
- `shoulder_depth_mm` → neck joint depth
- `back_radius_mm` → back arch radius
- `top_thickness_mm` → soundboard thickness
- `back_thickness_mm` → back plate thickness

**Fallback Behavior:**
- Missing depth → use `uniform_thickness_mm` as extrusion
- Missing radius → assume flat surface
- Missing thickness → use default (see Thickness Hierarchy)

### Rule 4: Continuity Construction

**Statement:** Translator may CONSTRUCT topology to achieve required continuity level.

**Allowed Construction:**
- Generating intermediate vertices for smooth curves
- Creating fillet edges for G1 continuity
- Lofting surfaces between profile sections

**Constraints:**
- Constructed geometry must pass through approved points
- Construction must not alter exterior boundary
- Construction parameters must be deterministic

### Rule 5: Classification Fidelity

**Statement:** Translator must respect `cad_intent` classification.

| cad_intent | Expected Topology |
|------------|-------------------|
| `flat_body` | Uniform extrusion |
| `acoustic_body` | Shell with variable depth |
| `archtop_body` | Carved surfaces |

**Violation:** Generating acoustic shell when `cad_intent: "flat_body"`.

---

## Semantic Field Authority

### BOE-Owned (Read-Only)

| Field | Authority | Translator Access |
|-------|-----------|-------------------|
| `outline_points` | BOE | READ |
| `outline_type` | BOE | READ |
| `soundhole_position` | BOE | READ |
| `soundhole_dimensions` | BOE | READ |

### IBG-Advisory (Consume)

| Field | Authority | Translator Access |
|-------|-----------|-------------------|
| `side_heights_mm` | IBG | CONSUME |
| `radii_by_zone` | IBG | CONSUME |
| `dimensions` | IBG | CONSUME |
| `back_radius_mm` | INSTRUMENT_SPECS | CONSUME |
| `butt_depth_mm` | INSTRUMENT_SPECS | CONSUME |
| `shoulder_depth_mm` | INSTRUMENT_SPECS | CONSUME |

### User-Input (Override IBG)

| Field | Authority | Translator Access |
|-------|-----------|-------------------|
| `top_arch_height_mm` | User | CONSUME |
| `side_thickness_mm` | User | CONSUME |
| `surface_type_overrides` | User | CONSUME |

### Translator-Computed (Derive)

| Field | Authority | Computation |
|-------|-----------|-------------|
| `rim_centerline` | Translator | profile + thickness offset |
| `interpolated_depths` | Translator | butt → shoulder interpolation |
| `fillet_radii` | Translator | continuity requirements |

---

## Validation Rules

### Pre-Translation Validation

Before translation begins:

1. **Profile Closure Check**
   ```
   IF NOT is_closed(outline_points):
       REJECT with BLOCKING error
   ```

2. **cad_semantics Presence**
   ```
   IF cad_semantics IS NULL:
       REJECT with BLOCKING error
   ```

3. **Gate Status Check**
   ```
   IF gate_status != GREEN:
       REJECT with BLOCKING error
   ```

### Post-Translation Validation

After translation completes:

1. **Shell Closure**
   ```
   VERIFY CLOSED_SHELL present
   VERIFY all edges have 2 adjacent faces
   ```

2. **Geometry Preservation**
   ```
   FOR EACH outline_point:
       VERIFY point exists in STEP output (within tolerance)
   ```

3. **Determinism Check**
   ```
   VERIFY topology_signature matches expected
   ```

---

## Error Classifications

### BLOCKING (Reject Translation)

| Error | Trigger |
|-------|---------|
| Open profile | Profile not closed |
| Missing cad_semantics | Extension required but absent |
| Red gate | Export not approved |
| Geometry mutation detected | Output differs from input |

### MAJOR (Warning + Flag)

| Error | Trigger |
|-------|---------|
| Continuity failure | G1 not achieved at junction |
| Thickness fallback | No thickness data, using default |
| IBG data missing | Advisory fields absent |

### MODERATE (Warning)

| Error | Trigger |
|-------|---------|
| Non-standard body type | Unrecognized acoustic_type |
| Deprecated field used | Legacy cad_semantics field |

---

## Acoustic-Specific Extensions

### Body Type Rules

| body_type | Required Fields | Optional Fields |
|-----------|-----------------|-----------------|
| `flat_body` | uniform_thickness_mm | — |
| `acoustic_body` | — | butt_depth_mm, shoulder_depth_mm, back_radius_mm |
| `archtop_body` | — | top_arch_height_mm, back_arch_height_mm |

### Surface Type Rules

| surface_type | CAD Representation |
|--------------|-------------------|
| `flat` | Planar face |
| `radiused` | Spherical cap (single radius) |
| `arched` | NURBS surface (RESEARCH_ONLY) |

### Thickness Level Rules

| Level | Translator Responsibility |
|-------|--------------------------|
| 1 | Use uniform_thickness_mm |
| 2 | Use component thickness values |
| 3 | Interpolate between zone values |
| 4 | NOT SUPPORTED (requires kernel) |

---

## Compliance Verification

### Test Categories

1. **Authority Tests**
   - Verify BOE geometry unchanged
   - Verify IBG fields consumed correctly
   - Verify user overrides applied

2. **Classification Tests**
   - Verify body_type respected
   - Verify surface_type applied
   - Verify thickness_level honored

3. **Semantic Tests**
   - Verify cad_semantics extension valid
   - Verify fallback behavior correct
   - Verify error classification accurate

---

## Related Documents

- `ACOUSTIC_BODY_SEMANTIC_MODEL.md`
- `ACOUSTIC_TOPOLOGY_CONTINUITY_MODEL.md`
- `THICKNESS_HIERARCHY_MODEL.md`
- `CAD_TRANSLATOR_GOVERNANCE_RULES.md`
- `CAD_REGRESSION_CLASSIFICATION_MODEL.md`
