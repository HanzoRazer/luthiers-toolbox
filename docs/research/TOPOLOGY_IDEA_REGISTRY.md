# Topology Idea Registry

**Purpose:** Register topology ideas that were **rediscovered** or are **at risk of being forgotten** during sandbox migration and constitutional stabilization.

**Status:** Seed registry (Wave Index 1A) — extend in place  
**Authority:** Research memory only

---

## How to read entries

| Field | Meaning |
|-------|---------|
| **Origin wave** | [RESEARCH_WAVE_INDEX.md](RESEARCH_WAVE_INDEX.md) |
| **Known implementations** | Production path, sandbox path, or both |
| **Current status** | ACTIVE / PARTIAL / ARCHAEOLOGICAL / AT_RISK |
| **Risk if forgotten** | What breaks when the idea vanishes from team memory |
| **Next investigation** | Suggested follow-up (Lane 4+), not a commitment |
| **Risk** | High / Medium / Low (formal) |
| **Links** | ADR → governance → handoff → archaeology (when available) |

### Ownership (ratified)

- **Primary:** author of semantic/topology PR updates entry when behavior changes.
- **Secondary:** topology steward / curator.

---

## Registry

### 1. LINE chaining

| Field | Value |
|-------|--------|
| **Idea** | Connect fragmented LINE/edge segments into continuous chains before body selection |
| **Origin wave** | B (evaluation), D (blueprint_clean tiers) |
| **Known implementations** | `services/api/app/services/blueprint_clean.py` (REFINED tiers); `edge_to_dxf.py` grouping |
| **Current status** | **ACTIVE** (production) |
| **Risk if forgotten** | Open contours misclassified as noise; false “component sheet” |
| **Risk** | **Medium** |
| **Next investigation** | Compare chain quality REFINED vs V2_RAW on Les Paul corpus (Lane 4 fixture TBD) |

---

### 2. Closed-loop recovery

| Field | Value |
|-------|--------|
| **Idea** | Detect and close nearly-closed contours for CAM-ready outlines |
| **Origin wave** | A |
| **Known implementations** | `ibg/arc_reconstructor.py`; `ibg/workflow/topology_recovery.py` |
| **Current status** | **ACTIVE** (IBG); archaeology in `vectorizer-sandbox` |
| **Risk if forgotten** | Open loops reach CAM; machining stalls or gouges |
| **Next investigation** | Golden DXF loop-closure metrics per instrument class |

---

### 3. Near-closed loop detection

| Field | Value |
|-------|--------|
| **Idea** | Treat small gap as closeable when gap length / perimeter below threshold |
| **Origin wave** | A |
| **Known implementations** | Arc reconstruction tiers; contour plausibility |
| **Current status** | **ACTIVE** |
| **Risk if forgotten** | Over-closure bridges text; under-closure drops bouts |
| **Next investigation** | Document thresholds per acoustic vs electric |

---

### 4. Gap closure (multi-tier)

| Field | Value |
|-------|--------|
| **Idea** | Progressive gap closure (tier 0 reference bridge → tier N arc promote) |
| **Origin wave** | A |
| **Known implementations** | `reference_outline_bridge.py`, `arc_reconstructor.py` (prod + archaeology) |
| **Current status** | **ACTIVE** prod; **ARCHAEOLOGICAL** sandbox copy |
| **Risk if forgotten** | Engineers re-implement single-pass close; lose tier discipline |
| **Next investigation** | Map tiers to Workflow 1A `recover_topology` outputs |

---

### 5. Arc reconstruction

| Field | Value |
|-------|--------|
| **Idea** | Promote arc hypotheses from gap geometry instead of dense polyline noise |
| **Origin wave** | A |
| **Known implementations** | `ibg/arc_reconstructor.py`; `arc_reconstructor.py` in sandbox archaeology |
| **Current status** | **ACTIVE** |
| **Risk if forgotten** | DXF file size explodes; feeds/speeds unstable on jagged fits |
| **Next investigation** | `ibg/arc_reconstructor.py` vs sandbox test DXF parity report |

---

### 6. Contour ordering

| Field | Value |
|-------|--------|
| **Idea** | Order contours (parent/child, hierarchy) before election of body outline |
| **Origin wave** | B, D |
| **Known implementations** | `contour_hierarchy.py`; `edge_to_dxf.py` (TODO: consolidate) |
| **Current status** | **PARTIAL** (duplicated logic — maintainability debt) |
| **Risk if forgotten** | Wrong outer contour selected; voids attached to wrong parent |
| **Next investigation** | Shared hierarchy module (governance debt item) |

---

### 7. Body isolation

| Field | Value |
|-------|--------|
| **Idea** | Isolate instrument body from background/page border using grouping + scores |
| **Origin wave** | C (photo), D |
| **Known implementations** | `photo-vectorizer/body_isolation_stage.py`; `edge_to_dxf` grouping + fallback |
| **Current status** | **ACTIVE**; fallback **AT_RISK** (telemetry added) |
| **Risk if forgotten** | Silent fallback to legacy isolation degrades topology |
| **Next investigation** | Metric rate of `grouping_fallback_used` in production logs |

---

### 8. Centerline estimation

| Field | Value |
|-------|--------|
| **Idea** | Infer symmetry axis / centerline for bout analysis and mirroring |
| **Origin wave** | A, C |
| **Known implementations** | Constraint landmarks; cognitive/grid archaeology (unwired) |
| **Current status** | **PARTIAL** |
| **Risk if forgotten** | Asymmetric bodies mis-normalized; mirror tools fail |
| **Next investigation** | Whether body outline editor should expose centerline constraint |

---

### 9. Asymmetry preservation

| Field | Value |
|-------|--------|
| **Idea** | Preserve intentional asymmetry (arm cut, belly) vs forced symmetry |
| **Origin wave** | A |
| **Known implementations** | Body solver sections; traced outlines (`smart_guitar_traced_outline.py`) |
| **Current status** | **ACTIVE** (data + solver); design tools partial |
| **Risk if forgotten** | Mirror-symmetric defaults destroy maker intent |
| **Next investigation** | Link outline editor void loops to solver voids |

---

### 10. Semantic occupancy

| Field | Value |
|-------|--------|
| **Idea** | Grid/cell occupancy semantics for “what region means” (pocket, bout, route) |
| **Origin wave** | C |
| **Known implementations** | `ibg/body_grid/`; `extract_body_grid_v*` archaeology |
| **Current status** | **ACTIVE** grid; archaeology **RELOCATED_EXTERNAL** |
| **Risk if forgotten** | Slab_body collapse — entire plate one semantic class |
| **Next investigation** | Lane 4 morphology trace for occupancy → primitives |

---

### 11. Primitive extraction

| Field | Value |
|-------|--------|
| **Idea** | Detect circles, slots, routes as primitives after contour election |
| **Origin wave** | B, C |
| **Known implementations** | `vectorizer_phase3` primitive detector; Phase3 SMART path |
| **Current status** | **PARTIAL** (mode-dependent) |
| **Risk if forgotten** | Primitive starvation — CAM ops missing holes/routes |
| **Next investigation** | Matrix row in [SEMANTIC_DISCOVERY_MATRIX.md](SEMANTIC_DISCOVERY_MATRIX.md) |

---

## Adding entries

1. Assign next ID.
2. Tie to a wave in [RESEARCH_WAVE_INDEX.md](RESEARCH_WAVE_INDEX.md).
3. Do **not** mark ACTIVE without a file path in `luthiers-toolbox` or explicit sandbox repo path.
4. Cross-link discoveries in [SEMANTIC_DISCOVERY_MATRIX.md](SEMANTIC_DISCOVERY_MATRIX.md).

---

*Topology Idea Registry — seed 11 entries — Research Wave 1A — 2026-05-20*
