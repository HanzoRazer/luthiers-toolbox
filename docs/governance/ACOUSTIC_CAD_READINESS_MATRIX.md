# Acoustic CAD Readiness Matrix

**Sprint:** MRP-5E  
**Status:** ACTIVE  
**Authority:** CAD Translation Governance

---

## Purpose

Classify instrument body types by their readiness for acoustic CAD translation. This matrix guides sprint planning and identifies blockers for each instrument family.

---

## Readiness Classifications

### PRODUCTION_READY

**Criteria:**
- Schema fields defined and populated
- Translator implemented and regression-tested
- External validation complete
- Manufacturing tested

**Current:** None (acoustic bodies)

### CAD_CANDIDATE

**Criteria:**
- Schema fields defined
- IBG data available
- Translator design documented
- Regression corpus exists

**Current:** None (acoustic bodies)

### SCHEMA_READY

**Criteria:**
- Semantic fields identified
- Data sources mapped
- No translator implementation yet

**Current:** Acoustic guitar family (MRP-5E output)

### RESEARCH_REQUIRED

**Criteria:**
- Semantic model incomplete
- Data sources unclear
- Significant design work needed

**Current:** Archtop, mandolin, ukulele families

### OUT_OF_SCOPE

**Criteria:**
- Specialized topology beyond current architecture
- No near-term implementation planned

**Current:** Violin family, resonator guitars, multi-piece assemblies

---

## Instrument Family Matrix

### Guitar Family

| Instrument | Readiness | Blockers | Target Sprint |
|------------|-----------|----------|---------------|
| Dreadnought | SCHEMA_READY | Translator impl | MRP-5G |
| OM/000 | SCHEMA_READY | Translator impl | MRP-5G |
| Parlor | SCHEMA_READY | Translator impl | MRP-5G |
| Jumbo | SCHEMA_READY | Translator impl | MRP-5G |
| Classical | SCHEMA_READY | Translator impl | MRP-5G |
| Flamenco | SCHEMA_READY | Translator impl | MRP-5G |
| 12-string | SCHEMA_READY | Same as base | MRP-5G |

**Family Notes:**
- All steel-string acoustics share same topology model
- Classical/flamenco differ only in dimensions
- IBG already supports guitar family morphology

### Archtop Family

| Instrument | Readiness | Blockers | Target Sprint |
|------------|-----------|----------|---------------|
| Jazz archtop | RESEARCH_REQUIRED | Carved surfaces, f-holes | MRP-5J+ |
| Semi-hollow | RESEARCH_REQUIRED | Center block, binding | MRP-5K+ |
| Thinline | RESEARCH_REQUIRED | Shallow chamber | MRP-5K+ |

**Family Notes:**
- Requires G2 continuity for carved surfaces
- F-hole topology is complex (multiple openings)
- Center block creates assembly semantics

### Electric Family (Acoustic Chamber)

| Instrument | Readiness | Blockers | Target Sprint |
|------------|-----------|----------|---------------|
| Hollow electric | RESEARCH_REQUIRED | Cap + back assembly | MRP-5K+ |
| Chambered solid | SCHEMA_READY | Internal routing | MRP-5H |

**Family Notes:**
- Hollow electrics have acoustic body topology
- Chambered solids are flat-body + internal voids
- Internal routing is subtractive from flat body

### Mandolin Family

| Instrument | Readiness | Blockers | Target Sprint |
|------------|-----------|----------|---------------|
| A-style | RESEARCH_REQUIRED | Small scale, carved | MRP-6+ |
| F-style | RESEARCH_REQUIRED | Scroll, complex carve | MRP-6+ |
| Flatback | SCHEMA_READY | Similar to guitar | MRP-5I |

**Family Notes:**
- Carved mandolins require archtop technology
- Flatback mandolins can use guitar acoustic model
- Smaller scale may need adjusted tolerances

### Ukulele Family

| Instrument | Readiness | Blockers | Target Sprint |
|------------|-----------|----------|---------------|
| Soprano | SCHEMA_READY | Scale adjustment | MRP-5I |
| Concert | SCHEMA_READY | Scale adjustment | MRP-5I |
| Tenor | SCHEMA_READY | Scale adjustment | MRP-5I |
| Baritone | SCHEMA_READY | Similar to small guitar | MRP-5I |

**Family Notes:**
- Topology identical to acoustic guitar
- Dimensions much smaller
- IBG may need ukulele-specific specs

### Out of Scope

| Instrument | Reason | Future Possibility |
|------------|--------|-------------------|
| Violin family | Sound post, arched plates, compound curves | MRP-7+ |
| Resonator guitar | Cone assembly, metal components | Never (specialized) |
| Harp guitar | Extended body, sub-bass chamber | MRP-7+ |
| Bass guitar | Large scale, specialized | MRP-6+ |

---

## Capability Requirements by Family

### Acoustic Guitar (SCHEMA_READY)

| Capability | Status | Notes |
|------------|--------|-------|
| Profile outline | AVAILABLE | BOE provides |
| Side depth profile | AVAILABLE | IBG side_heights_mm |
| Top/back thickness | AVAILABLE | INSTRUMENT_SPECS |
| Back radius | AVAILABLE | INSTRUMENT_SPECS |
| Surface types | DEFINED | flat, radiused |
| Continuity model | DEFINED | G0/G1 |
| Thickness hierarchy | DEFINED | Levels 1-3 |

### Archtop (RESEARCH_REQUIRED)

| Capability | Status | Notes |
|------------|--------|-------|
| Profile outline | AVAILABLE | BOE provides |
| Carved top surface | MISSING | Requires NURBS |
| Carved back surface | MISSING | Requires NURBS |
| F-hole geometry | MISSING | Complex topology |
| Binding ledge | MISSING | Assembly semantics |
| G2 continuity | MISSING | Requires kernel |

### Electric Chambered (SCHEMA_READY)

| Capability | Status | Notes |
|------------|--------|-------|
| Profile outline | AVAILABLE | BOE provides |
| Flat body extrusion | AVAILABLE | MRP-5C translator |
| Internal chambers | PARTIAL | Subtractive from solid |
| Pickup routing | PARTIAL | Standard dimensions |
| Control cavity | PARTIAL | Standard dimensions |

---

## Blocker Analysis

### Blocker: Carved Surface Representation

**Affects:** Archtop, mandolin (A/F-style), violin family

**Current State:** No NURBS surface generation capability

**Resolution Path:**
1. MRP-5H: CAD kernel evaluation (CadQuery/OCC)
2. MRP-5I: Surface generation prototype
3. MRP-5J: Carved surface governance

### Blocker: Assembly Semantics

**Affects:** Multi-piece backs, binding, bracing

**Current State:** Single-body export only

**Resolution Path:**
1. MRP-5G: Assembly planning (research)
2. MRP-6+: Assembly export prototype

### Blocker: Multiple Openings

**Affects:** F-holes, multiple soundholes

**Current State:** Single soundhole only

**Resolution Path:**
1. Define multi-opening schema
2. Extend translator for multiple voids
3. Validate topology with multiple shells

### Blocker: IBG Specifications

**Affects:** Ukulele, mandolin, bass

**Current State:** IBG specs guitar-focused

**Resolution Path:**
1. Add instrument family to INSTRUMENT_SPECS
2. Validate IBG morphology calculations
3. Add regression fixtures

---

## Sprint Alignment

| Sprint | Primary Focus | Instruments Advanced |
|--------|---------------|---------------------|
| MRP-5E | Semantic research | All (schema definitions) |
| MRP-5F | External validation | Flat-body (verification) |
| MRP-5G | Side/rim topology | Acoustic guitar |
| MRP-5H | CAD kernel eval | (Infrastructure) |
| MRP-5I | Acoustic STEP | Acoustic guitar, ukulele |
| MRP-5J | Carved topology | Archtop research |
| MRP-6+ | Advanced surfaces | Archtop, mandolin |

---

## Readiness Promotion Criteria

### RESEARCH_REQUIRED → SCHEMA_READY

- [ ] Semantic model documented
- [ ] IBG data sources identified
- [ ] Authority boundaries defined
- [ ] Blocker resolution path documented

### SCHEMA_READY → CAD_CANDIDATE

- [ ] Translator design documented
- [ ] Regression fixtures defined
- [ ] Prototype implementation started
- [ ] No BLOCKING errors in prototype

### CAD_CANDIDATE → PRODUCTION_READY

- [ ] Translator promoted to GOVERNED_EXPERIMENTAL
- [ ] External CAD validation passed
- [ ] 30 days stable operation
- [ ] Manufacturing test completed

---

## Related Documents

- `ACOUSTIC_BODY_SEMANTIC_MODEL.md`
- `ACOUSTIC_CAD_SEMANTIC_RULES.md`
- `THICKNESS_HIERARCHY_MODEL.md`
- `CAD_TRANSLATOR_PROMOTION_THRESHOLDS.md`
