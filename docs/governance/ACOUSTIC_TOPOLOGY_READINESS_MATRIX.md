# Acoustic Topology Readiness Matrix

**Sprint:** MRP-5G  
**Status:** ACTIVE  
**Authority:** CAD Topology Governance

---

## Purpose

Classify instrument body types by their readiness for acoustic topology runtime generation. This matrix guides sprint planning and identifies semantic sufficiency for each instrument family.

---

## Readiness Classifications

### PROTOTYPE_POSSIBLE

**Criteria:**
- Semantic schema complete
- Flat extrusion sufficient
- No loft required
- G0 continuity acceptable

### MODERATE

**Criteria:**
- Semantic schema complete
- Basic loft may be needed
- G1 continuity desirable
- No complex surfaces

### RESEARCH_REQUIRED

**Criteria:**
- Semantic gaps exist
- Loft generation required
- G1 continuity required
- Additional research needed

### COMPLEX

**Criteria:**
- Multiple semantic gaps
- Advanced surface generation
- G2 continuity may be needed
- Significant research required

### FUTURE

**Criteria:**
- Semantic model incomplete
- NURBS/carved surfaces required
- Beyond current architecture scope

### OUT_OF_SCOPE

**Criteria:**
- Fundamentally different topology
- Not planned for MRP scope

---

## Instrument Readiness Matrix

### Guitar Family

| Instrument | Runtime Readiness | Semantic Sufficiency | Key Blockers |
|------------|-------------------|---------------------|--------------|
| Electric solid body | PROTOTYPE_POSSIBLE | COMPLETE | None |
| Flat-top acoustic (uniform rim) | PROTOTYPE_POSSIBLE | COMPLETE | None |
| Flat-top acoustic (tapered rim) | RESEARCH_REQUIRED | PARTIAL | Loft generation |
| Classical/nylon | RESEARCH_REQUIRED | PARTIAL | Loft generation |
| 12-string | RESEARCH_REQUIRED | PARTIAL | Same as steel-string |

### Hollow Body Family

| Instrument | Runtime Readiness | Semantic Sufficiency | Key Blockers |
|------------|-------------------|---------------------|--------------|
| Semi-hollow electric | MODERATE | MOSTLY_COMPLETE | Center block semantics |
| Thinline electric | MODERATE | MOSTLY_COMPLETE | Shallow chamber |
| Full hollow electric | MODERATE | MOSTLY_COMPLETE | Binding semantics |

### Archtop Family

| Instrument | Runtime Readiness | Semantic Sufficiency | Key Blockers |
|------------|-------------------|---------------------|--------------|
| Jazz archtop | COMPLEX | PARTIAL | Carved surfaces, f-holes |
| Gypsy jazz | COMPLEX | PARTIAL | Oval hole, carved top |

### Other Families

| Instrument | Runtime Readiness | Semantic Sufficiency | Key Blockers |
|------------|-------------------|---------------------|--------------|
| Flatback mandolin | MODERATE | MOSTLY_COMPLETE | Scale adjustment |
| A-style mandolin | COMPLEX | PARTIAL | Carved surfaces |
| F-style mandolin | COMPLEX | PARTIAL | Scroll, carved |
| Ukulele (all sizes) | PROTOTYPE_POSSIBLE | COMPLETE | Scale only |
| Violin family | OUT_OF_SCOPE | INCOMPLETE | Sound post, complex arch |
| Resonator | OUT_OF_SCOPE | INCOMPLETE | Metal cone, specialized |

---

## Semantic Sufficiency Analysis

### Electric Solid Body

**Status:** COMPLETE

| Semantic | Available | Source |
|----------|-----------|--------|
| Profile outline | ✓ | BOE |
| Uniform thickness | ✓ | cad_semantics.flat_body |
| Body category | ✓ | cad_semantics.body_category |

**Blockers:** None

### Flat-Top Acoustic (Uniform Rim)

**Status:** COMPLETE

| Semantic | Available | Source |
|----------|-----------|--------|
| Profile outline | ✓ | BOE |
| Side depth | ✓ | cad_semantics.acoustic.thickness |
| Top thickness | ✓ | cad_semantics.acoustic.thickness |
| Back thickness | ✓ | cad_semantics.acoustic.thickness |
| Continuity target | ✓ | cad_semantics.acoustic.rim |
| Plate types | ✓ | cad_semantics.acoustic.plate_relationship |

**Blockers:** None (uniform rim = no loft needed)

### Flat-Top Acoustic (Tapered Rim)

**Status:** PARTIAL

| Semantic | Available | Source | Gap |
|----------|-----------|--------|-----|
| Profile outline | ✓ | BOE | — |
| Taper max/min depth | ✓ | side_profile | — |
| Per-point depth profile | △ | IBG advisory | Not authoritative |
| Interpolation method | ✗ | — | Not defined |
| Loft construction | ✗ | — | Not implemented |

**Blockers:**
- Loft generation not implemented
- Per-point depth profile authority unclear
- Interpolation strategy not defined

### Semi-Hollow Electric

**Status:** MOSTLY_COMPLETE

| Semantic | Available | Source | Gap |
|----------|-----------|--------|-----|
| Profile outline | ✓ | BOE | — |
| Chamber depth | ✓ | cad_semantics | — |
| Center block | △ | — | Semantics missing |
| F-hole positions | △ | — | Semantics missing |

**Blockers:**
- Center block semantics not defined
- Multiple-void topology validation

### Jazz Archtop

**Status:** PARTIAL

| Semantic | Available | Source | Gap |
|----------|-----------|--------|-----|
| Profile outline | ✓ | BOE | — |
| Arch height | △ | — | Not in schema |
| Arch profile | ✗ | — | NURBS required |
| F-hole geometry | ✗ | — | Complex topology |
| Binding ledge | ✗ | — | Assembly semantics |

**Blockers:**
- NURBS surface generation required
- F-hole topology (multiple openings)
- Carved surface construction
- G2 continuity for smooth arch

---

## Topology Construction Requirements

### PROTOTYPE_POSSIBLE Instruments

| Capability Required | Status |
|---------------------|--------|
| Flat extrusion | Implemented (MRP-5C) |
| Closed shell validation | Implemented |
| G0 continuity | Implemented |

### MODERATE Instruments

| Capability Required | Status |
|---------------------|--------|
| Flat extrusion | Implemented |
| Basic loft (linear) | Not implemented |
| Variable depth | Not implemented |
| G1 continuity | Not implemented |

### RESEARCH_REQUIRED Instruments

| Capability Required | Status |
|---------------------|--------|
| Spline loft | Research only |
| Radiused surface | Research only |
| G1 enforcement | Research only |
| Per-point depth | Research only |

### COMPLEX Instruments

| Capability Required | Status |
|---------------------|--------|
| NURBS surface | Out of scope |
| Carved topology | Out of scope |
| Multiple openings | Research only |
| G2 continuity | Out of scope |

---

## Promotion Path

### PROTOTYPE_POSSIBLE → Production

**Requirements:**
- MRP-5H: Validate topology builder pattern
- MRP-5I: Implement shell validation
- Regression fixtures passing

### MODERATE → PROTOTYPE_POSSIBLE

**Requirements:**
- Basic loft implementation
- Variable depth support
- G1 continuity at junctions

### RESEARCH_REQUIRED → MODERATE

**Requirements:**
- Per-point depth authority resolved
- Interpolation strategy defined
- Loft algorithm selected

### COMPLEX → RESEARCH_REQUIRED

**Requirements:**
- NURBS/surface strategy selected
- CAD kernel selected
- F-hole topology research complete

---

## Sprint Alignment

| Sprint | Instruments Advanced | New Capabilities |
|--------|---------------------|------------------|
| MRP-5G | (Governance only) | — |
| MRP-5H | Electric solid, flat acoustic | Topology builder prototype |
| MRP-5I | Flat acoustic (uniform) | Shell validation |
| MRP-5J | Ukulele, flatback mandolin | Scale adjustment |
| MRP-5K+ | Tapered acoustic | Loft generation |
| MRP-6+ | Semi-hollow | Center block, multi-void |
| Future | Archtop, carved | NURBS, G2 |

---

## Related Documents

- `ACOUSTIC_CAD_READINESS_MATRIX.md` — Semantic readiness (MRP-5E)
- `ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md` — Runtime constraints
- `TOPOLOGY_FAILURE_CLASSIFICATION.md` — Error classification
- `CAD_KERNEL_BOUNDARY_ANALYSIS.md` — Kernel evaluation
