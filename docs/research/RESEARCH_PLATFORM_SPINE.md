# Research Platform Spine

**Purpose:** Define the formal stack from **archaeology** through **graduation** so semantic work does not suffer **amnesia** when code moves or modes multiply.

**Status:** Research Wave 1A stable on disk; **Wave 1B ACTIVE** (semantic trace docs)  
**Companion:** `docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md` (authority)  
**Ratified Q&A:** [RESEARCH_PLATFORM_1A_ALIGNMENT.md](RESEARCH_PLATFORM_1A_ALIGNMENT.md)

---

## Problem statement

Between Dec 2025 and May 2026 the program produced:

- Multiple sandboxes (arc recon, text eval, cognitive, adaptive)
- Multiple extraction modes (REFINED, V2_RAW, photo_v2, SIMPLE, …)
- Constitutional IBG gates arriving **after** extraction experiments

Without a memory spine, each new engineer **rediscovers** topology ideas and mistakes abandoned modules for production.

---

## Platform layers (bottom → top)

```text
┌─────────────────────────────────────────────────────────────┐
│  GRADUATION  — production ratifies (new code, ADR, tests)    │
├─────────────────────────────────────────────────────────────┤
│  INCUBATION  — multi-pass agents, phase forks (sandbox only) │
├─────────────────────────────────────────────────────────────┤
│  COGNITION   — meaning: class, occupancy, grid (sandbox)     │
├─────────────────────────────────────────────────────────────┤
│  RECONSTRUCTION — close loops, complete bodies (IBG + arch)  │
├─────────────────────────────────────────────────────────────┤
│  EVALUATION  — corpus benchmarks, mode comparison (sandbox)  │
├─────────────────────────────────────────────────────────────┤
│  ARCHAEOLOGY — preserved lineage, unwired but informative    │
└─────────────────────────────────────────────────────────────┘
         Evidence enters from EXTRACTION RUNTIME (deterministic)
         luthiers-toolbox: orchestrators, edge_to_dxf, phase3
```

---

## Layer definitions

### Archaeology

| Aspect | Detail |
|--------|--------|
| **What** | Code and docs preserved when unwired or superseded |
| **Where** | `vectorizer-sandbox/src/archaeology/`, `src/semantic/`; handoffs in `docs/handoffs/` |
| **Prevents amnesia by** | Keeping Tier A history grep-visible without polluting `services/` |
| **Must not** | Auto-import into Blueprint Reader default |

Examples: `extract_body_grid_v3`, arc_reconstructor prototypes, `vectorizer_phase2_runtime_spine.py`.

---

### Evaluation

| Aspect | Detail |
|--------|--------|
| **What** | Repeatable measurement of modes on fixed corpus |
| **Where** | `vectorizer-sandbox/src/evaluation/text_geometry_eval/`, `adaptive_reconstruction/` |
| **Prevents amnesia by** | Storing *why* March-6 cuatro and text-preserving kernels matter |
| **Must not** | Declare commercial viability without spine tests + gates |

Examples: Phase2/Phase3 runners, legibility metrics, `evaluation_results.json` (local).

---

### Reconstruction

| Aspect | Detail |
|--------|--------|
| **What** | Geometry completion from partial evidence |
| **Where** | **Production:** `ibg/*`; **Archaeology:** sandbox `arc_reconstructor/` |
| **Prevents amnesia by** | [IBG_LINEAGE_MAP.md](IBG_LINEAGE_MAP.md) separating prod from copy |
| **Must not** | Conflate with raw vectorizer extraction |

Examples: gap tiers, `topology_recovery` in Workflow 1A.

---

### Cognition

| Aspect | Detail |
|--------|--------|
| **What** | Interpretation — what regions *mean* |
| **Where** | `vectorizer-sandbox/src/semantic/`, incubation classifiers |
| **Prevents amnesia by** | Documenting unwired ML as **ARCHAEOLOGICAL_RESEARCH**, not DEAD noise |
| **Must not** | Set `confidence` = fabrication approval |

Examples: cognitive extractors, body grid archaeology, agentic supervisor.

---

### Incubation

| Aspect | Detail |
|--------|--------|
| **What** | Multi-pass supervision, experimental phase3/phase4 forks |
| **Where** | `vectorizer-sandbox/src/incubation/` |
| **Prevents amnesia by** | Keeping Wave 1–3 experiments runnable without forking production |
| **Must not** | Replace `services/blueprint-import/vectorizer_phase3.py` by copy-paste |

Examples: `agentic_supervisor.py`, incubation `vectorizer_phase3.py` (behind main on scale validation).

---

### Graduation

| Aspect | Detail |
|--------|--------|
| **What** | Evidence → provenance → governance → intake → **new** production code |
| **Where** | Process in `SEMANTIC_INCUBATION_ARCHITECTURE.md` |
| **Prevents amnesia by** | Requiring explicit ADR + lifecycle promotion per capability |
| **Must not** | Skip intake gate for IBG fabrication |

Artifacts: tests, `VECTORIZER_COMPONENT_LIFECYCLE.md`, ADRs, telemetry.

---

## How layers interact

```text
Extraction runtime produces artifacts (DXF/SVG)
        │
        ├─► Evaluation scores extraction modes (sandbox)
        │
        ├─► Reconstruction / Workflow 1A builds candidates (IBG)
        │         │
        │         └─► IBGIntakeGate (authority)
        │
        └─► Cognition proposes interpretations (sandbox only)
                  │
                  └─► Graduation (if ever) → new spine code
```

---

## Amnesia failure modes (watch list)

| Failure | Layer violated | Symptom |
|---------|----------------|---------|
| “Delete cognitive_extractor, it’s unused” | Archaeology | Lose occupancy experiments |
| “SIMPLE mode works” (empty DXF) | Evaluation + runtime | False evidence |
| “High ML score → cut G-code” | Cognition + graduation | Authority bypass |
| “Fix in sandbox arc_reconstructor only” | Reconstruction | Prod IBG unchanged |
| “Merge sandbox phase3 into main” | Incubation + graduation | Scale/regression collapse |

---

## Capability registry pointer

Operational mode list: `docs/governance/VECTORIZER_CAPABILITY_MAP.md`  
Lifecycle states: `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md`  
This research spine: waves + topology + matrix in `docs/research/`.

---

## Research Wave 1A scope boundary

1A **creates memory** (markdown indexes). It does **not**:

- Move or delete code
- Populate IBG memory stores
- Promote sandbox systems to ACTIVE
- Alter governance canonical routes

**Wave 1B** (after PR-1–3 + separation): morphology interpretation trace, canonical fixtures (Les Paul, slab_body, primitive starvation).

Committed index: `reports/research/research_index.json` via `scripts/research/build_research_index.py` (deterministic).

---

*Research Platform Spine — 2026-05-20*
