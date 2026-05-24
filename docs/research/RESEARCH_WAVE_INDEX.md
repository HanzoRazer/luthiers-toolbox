# Research Wave Index (Dec 2025 → May 2026)

**Primary deliverable — Research Wave Index 1A**  
**Status:** ACTIVE  
**Updates:** Amend in place; do not delete prior waves

---

## Wave 0 — Pre-Constitutional Boundaries

| Field | Value |
|-------|--------|
| **Timeframe** | 2025-12 |
| **Purpose** | Establish AI-assisted development boundaries **before** vectorizer/IBG acceleration — pre-constitutional semantic experimentation |
| **Systems involved** | `ci/ai_sandbox/` (forbidden calls, import boundaries, write paths, RMOS completeness); `.github/workflows/ai_sandbox_enforcement.yml` |
| **Key discoveries** | Governance can be enforced as CI policy separate from product features; many later semantic ideas trace origin here |
| **Topology / semantic ideas** | Policy layer (not geometry) |
| **Semantic ideas** | Boundaries precede semantics — tooling discipline enables later waves |
| **Status** | **ACTIVE** in `luthiers-toolbox` (do not migrate) |
| **Successors** | Waves B–E; Wave D extends authority model to IBG |
| **Unresolved** | Uniform lifecycle gates on all CAM/vectorizer routers |
| **Citation** | `runtime spine @` (tag TBD per release) |

**Do not erase Wave 0** when narrating migration — it is formal lineage, not a footnote.

---

## Wave A — Reconstruction Intelligence

| Field | Value |
|-------|--------|
| **Timeframe** | 2026-04-15 → 2026-04-18 (peak); lineage through 2026-05-20 migration |
| **Purpose** | Turn partial vectorizer DXF output into **closed, fabricatable body outlines** via gap closure, landmarks, and parametric completion |
| **Systems involved** | `sandbox/arc_reconstructor/` (prototypes) → **production IBG** `services/api/app/instrument_geometry/body/ibg/`; archaeology copy: `vectorizer-sandbox/src/archaeology/arc_reconstructor/` |
| **Key discoveries** | 4-tier gap closure; reference-outline bridging (Tier 0); constraint landmarks from DXF; dreadnought/cuatro solver tests as golden stress cases |
| **Topology ideas** | Arc promotion, near-closed loop detection, gap closure tiers, contour ordering before solve — see [TOPOLOGY_IDEA_REGISTRY.md](TOPOLOGY_IDEA_REGISTRY.md) |
| **Semantic ideas** | Body completion is **evidence synthesis**, not raw extraction; asymmetry and waist landmarks carry semantic weight |
| **Status** | Prototypes **RELOCATED_EXTERNAL**; production IBG modules **ACTIVE** |
| **Successors** | Wave E (workflow pipeline consumes topology recovery); Wave D (BodyEvidenceCandidate + intake gate) |
| **Unresolved** | Full parity between sandbox DXF experiments and production `arc_reconstructor.py`; commercial gate for auto-promotion to fabrication |

### Wave A artifact map

| Component | Production | Archaeology (sandbox repo) |
|-----------|------------|----------------------------|
| `arc_reconstructor.py` | `ibg/arc_reconstructor.py` | `src/archaeology/arc_reconstructor/` |
| `body_contour_solver.py` | `ibg/body_contour_solver.py` | same |
| `constraint_extractor.py` | `ibg/constraint_extractor.py` | same |
| `instrument_body_generator.py` | `ibg/instrument_body_generator.py` | same |
| `reference_outline_bridge.py` | `ibg/reference_outline_bridge.py` | same |

---

## Wave B — Evaluation Science

| Field | Value |
|-------|--------|
| **Timeframe** | 2026-04-28 → 2026-05-17 |
| **Purpose** | **Benchmark** vectorizer modes (Phase2, Phase3 SMART/SIMPLE, edge_to_dxf variants) on a fixed blueprint corpus — especially **text preservation** vs geometry density |
| **Systems involved** | **`vectorizer-sandbox/src/evaluation/`** (`text_geometry_eval/`, `adaptive_reconstruction/`) — migration **COMPLETE**; main repo no longer owns eval science |
| **Key discoveries** | March-6 cuatro baseline (~16.3 MB) as fidelity anchor; `morph_close_kernel=0` preserves text; unified runners enable apples-to-apples mode comparison |
| **Topology ideas** | Entity counts alone are insufficient; legibility metrics and DXF inventory matter |
| **Semantic ideas** | Evaluation must be **mode-labeled** (REFINED vs V2_RAW vs photo_v2); “better” is multidimensional |
| **Status** | **COMPLETE** in `vectorizer-sandbox`; main may consume metrics/interfaces only |
| **Successors** | Wave D grouping telemetry; production modes in `VECTORIZER_CAPABILITY_MAP.md` |
| **Unresolved** | Automating corpus regression in CI without 2.8 GB artifacts; SIMPLE mode commercial viability (addressed in runtime PR-1 separately) |

### Wave B golden references

| Artifact | Role |
|----------|------|
| `cuatro_puertorriqueño` March-6 baseline | Recovery fidelity reference |
| 8-blueprint corpus (see eval README in sandbox repo) | Text + geometry scoring |
| `evaluation_results.json` | Run aggregation (local) |

---

## Wave C — Semantic Cognition

| Field | Value |
|-------|--------|
| **Timeframe** | 2026-03-31 → 2026-05-20 |
| **Purpose** | ML/grid **interpretation** of contours — occupancy, classification, multi-pass supervision — orthogonal to deterministic extraction |
| **Systems involved** | `vectorizer-sandbox` (`src/semantic/`, `src/archaeology/extract_body_grid*.py`, `src/incubation/agentic_supervisor.py`, incubation forks of phase2/phase3) |
| **Key discoveries** | Feature-first calibration (Wave 1); agentic PASS/WARN/RETRY/FAIL (Wave 2); grid v1–v5 iteration history; cognitive extractors never wired to production orchestrator |
| **Topology ideas** | Semantic occupancy, body grid zones, primitive starvation when interpretation collapses to slab |
| **Semantic ideas** | **Confidence ≠ authority**; interpretation must not silently override constitutional gates |
| **Status** | Tier A modules **RELOCATED_EXTERNAL** from `luthiers-toolbox`; grep-gated (`check_semantic_sandbox_imports.py`) |
| **Successors** | Graduation bridge only (`SEMANTIC_INCUBATION_ARCHITECTURE.md`) |
| **Unresolved** | **No 2026 graduation targets** for cognition; TrainingDataCollector / submit_correction remain **DEAD** on spine |

---

## Wave D — Constitutional Runtime

| Field | Value |
|-------|--------|
| **Timeframe** | 2026-05-07 → 2026-05-20 |
| **Purpose** | Separate **authority** from extraction: provenance, lifecycle states, intake gates, export boundaries |
| **Systems involved** | IBG constitutional layer (`body_evidence_candidate.py`, `ibg_intake_gate.py`); RMOS; `docs/governance/*`; grouping telemetry (`grouping_telemetry.py`) |
| **Key discoveries** | Orphaned capabilities are an **authority risk**, not merely cleanup; fallback paths must be visible; IBG provenance blocked pending model ratification |
| **Topology ideas** | Grouping fallback → legacy isolation degrades body selection without surfacing reason |
| **Semantic ideas** | `sandbox discovers / runtime ratifies` as institutional rule |
| **Status** | **ACTIVE** governance + partial runtime instrumentation |
| **Successors** | Wave E; research memory (this index) |
| **Unresolved** | IBG `saveas` without full export lifecycle; federation of feedback loop |

---

## Wave E — Workflow / IBG Intake

| Field | Value |
|-------|--------|
| **Timeframe** | 2026-05-18 → present |
| **Purpose** | Staged pipeline from **canonical artifacts** → topology recovery → candidates → **BodyEvidenceCandidate** → **IBGIntakeGate** → **human review package** (no silent auto-fabrication) |
| **Systems involved** | `ibg/workflow/ibg_workflow_pipeline.py` (DEV ORDER **1A-WORKFLOW**), `topology_recovery.py`, `review_package.py`, `artifact_preservation.py` |
| **Key discoveries** | Success = provenance-bearing, confidence-declared, **gate-blocked** candidates + review disk package |
| **Topology ideas** | Contour candidates and gap stats as first-class workflow outputs |
| **Semantic ideas** | Intake gate is the commercial boundary; workflow preserves performance objective during vectorizer migration |
| **Status** | **ACTIVE** (orchestration); fabrication still gated |
| **Successors** | Morphology harvest integration (shared intake lineage) |
| **Non-goals (1A)** | IBG memory population; classifier graduation — see [RESEARCH_PLATFORM_1A_ALIGNMENT.md](RESEARCH_PLATFORM_1A_ALIGNMENT.md) |
| **Unresolved** | End-to-end router exposure; harvest → BodyEvidence adapter completeness |

### Wave E pipeline stages (reference)

1. `preserve_artifacts`
2. `recover_topology`
3. `isolate_candidates` / score
4. `wrap_candidates` → `BodyEvidenceCandidate[]`
5. `run_intake_gate` → `IBGIntakeGate`
6. `emit_review_package`

Detail: [IBG_LINEAGE_MAP.md](IBG_LINEAGE_MAP.md).

---

## Wave 1B — Semantic Interpretation Trace (subordinate phase)

| Field | Value |
|-------|--------|
| **Timeframe** | 2026-05-20+ (after 1A spine on disk) |
| **Purpose** | Trace how semantic meaning survives or collapses across vectorizer → IBG → morphology pipeline |
| **Systems involved** | `ibg/workflow/*`, `body_grid/*`, `morphology_harvest/*`, `vectorizer_phase3`, `edge_to_dxf` + `grouping_telemetry` |
| **Key discoveries** | Continuity breaks at primitive extraction, slab occupancy, grouping fallback; confidence ≠ canonization |
| **Topology ideas** | Cross-links registry — no parallel fork |
| **Semantic ideas** | visibility ≠ legitimacy; semantic influence ≠ authority; three-layer morphology split |
| **Status** | **ACTIVE** (documentation); instrumentation **deferred** |
| **Successors** | Canonical regression fixtures (TBD); future telemetry wave |
| **Unresolved** | Les Paul continuity DXF; slab_body canonical fixture; full provenance chain harvest↔workflow |
| **Spine doc** | [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md) |

Does **not** renumber Waves 0–E. 1B is a research phase within the May 2026 era.

---

## Cross-wave timeline

```text
2025-12  Wave 0 — ci/ai_sandbox (pre-constitutional)
2026-03  vectorizer-sandbox born; Wave C incubation
2026-03-06  cuatro golden (feeds Wave B)
2026-04  Wave A reconstruction + IBG production
2026-04-28  Wave B text_geometry_eval
2026-05  Wave B adaptive_reconstruction; Wave D constitutional; Wave E workflow 1A
2026-05-20  Tier A + arc_reconstructor migration; research memory 1A; Wave 1B semantic trace (docs)
```

---

## Where to go next

| Need | Document |
|------|----------|
| Topology ideas at risk | [TOPOLOGY_IDEA_REGISTRY.md](TOPOLOGY_IDEA_REGISTRY.md) |
| Runtime vs sandbox | [SEMANTIC_DISCOVERY_MATRIX.md](SEMANTIC_DISCOVERY_MATRIX.md) |
| Platform layers | [RESEARCH_PLATFORM_SPINE.md](RESEARCH_PLATFORM_SPINE.md) |
| IBG runtime position | [IBG_RUNTIME_POSITION.md](IBG_RUNTIME_POSITION.md) |
| IBG lineage | [IBG_LINEAGE_MAP.md](IBG_LINEAGE_MAP.md) |
| Constitutional Q&A | [RESEARCH_PLATFORM_1A_ALIGNMENT.md](RESEARCH_PLATFORM_1A_ALIGNMENT.md) |
| Wave 1B trace | [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md) |

---

*Research Wave Index 1A — 2026-05-20*
