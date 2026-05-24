# Semantic Discovery Matrix

**Purpose:** Connect **what we learned** to **where it lives now** and **what breaks** if research is ignored.

**Rule:** Research artifacts do **not** grant operational authority.  
**Separation:** `luthiers-toolbox` = runtime spine + constitutional IBG; `vectorizer-sandbox` = cognition + evaluation archaeology.

Columns: **Discovery | Original Context | Current Runtime Equivalent | Sandbox Equivalent | Risk (H/M/L) | Preservation Action**

Risk scale is **formal** for 1A (no scoring engine). See [RESEARCH_PLATFORM_1A_ALIGNMENT.md](RESEARCH_PLATFORM_1A_ALIGNMENT.md).

---

## Matrix

| Discovery | Original Context | Current Runtime Equivalent | Sandbox Equivalent | Risk | Preservation Action |
|-----------|------------------|----------------------------|--------------------|------------------|---------------------|
| **sandbox discovers / runtime ratifies** | Incubation architecture (May 2026) | Enforced via lifecycle + graduation bridge | All `src/incubation/*` experiments | **High** | Document in [RESEARCH_PLATFORM_SPINE.md](RESEARCH_PLATFORM_SPINE.md); CI `check_semantic_sandbox_imports.py` |
| **Grouping fallback visibility** | Photo pipeline `edge_to_dxf` exception → legacy isolation | `grouping_telemetry.py` + `topology_provenance` in results | Archaeology edge experiments | **High** | Monitor `grouping_fallback_total`; never hide in debug-only |
| **primitive starvation** | SMART extraction + IBG primitive expectations | `vectorizer_phase3` primitives path (SMART); IBG primitives in body_grid | `agentic_supervisor` retries (incubation) | **High** | Registry #11; **Lane 4** canonical fixture TBD (Les Paul candidate) |
| **slab_body collapse** | Grid/cognitive occupancy (Wave C) | `body_grid` zones (when wired) | `extract_body_grid_v*` archaeology | **High** | Keep grid archaeology in sandbox; **Lane 4** fixture TBD |
| **confidence ≠ authority** | ML classifier + FeedbackSystem partial wiring | `BodyEvidenceCandidate` + `IBGIntakeGate`; RMOS GREEN/YELLOW/RED | `cognitive_extractor` (unwired) | **High** | Lifecycle: DEAD intake paths; gate required |
| **visibility ≠ legitimacy** | Debug overlays, grouping telemetry, “we can see it” in eval | Logs/metrics may expose topology without granting promotion | Eval dashboards in `vectorizer-sandbox` | **High** | Never treat observability as graduation; gate + lifecycle only |
| **semantic influence ≠ semantic authority** | Classifier scores, grid occupancy hints, harvest descriptors | Influence may inform **advisory** candidates only | Cognition archaeology, incubation forks | **High** | [IBG_RUNTIME_POSITION.md](IBG_RUNTIME_POSITION.md); no auto-fabrication from influence alone |
| **SIMPLE mode empty DXF** | Phase3 SIMPLE + UNKNOWN export exclude | PR-1: SIMPLE exports UNKNOWN; fail-closed if zero entities | N/A (spine fix) | **Medium** | Test `test_vectorizer_simple_export.py`; EXPORT_SAFE lifecycle |
| **V2_RAW fidelity anchor** | March-6 cuatro baseline | `CleanupMode.V2_RAW` CANONICAL_RECOVERY | Incubation `vectorizer_phase3` fork (do not back-merge) | **High** | Protect recovery modes; golden artifact in handoffs |
| **Text-preserving photo extract** | `morph_close_kernel=0` eval | `photo_refined` / EdgeToDXF variant | `vectorizer-sandbox/src/evaluation/` | **Medium** | Wave B COMPLETE in sandbox; document mode matrix |
| **5-tier blueprint fallback** | `blueprint_clean` REFINED | Exposed `fallback_tier` in API response | N/A | **Medium** | Log tier in orchestrator responses |
| **Calibration API vs vectorize** | `calibration_integration` “orphan” audit | `calibration_router` PARTIAL; not main vectorize | `vectorizer_enhancements` Wave 1 | **Medium** | Lifecycle MEDIUM; document scope split |
| **IBG Workflow 1A** | DEV ORDER 1A-WORKFLOW | `ibg_workflow_pipeline.py` (internal) | N/A | **High** | [IBG_LINEAGE_MAP.md](IBG_LINEAGE_MAP.md); not public API yet |
| **Arc recon prototype ≠ prod** | `sandbox/arc_reconstructor` | `ibg/arc_reconstructor.py` | `vectorizer-sandbox/.../arc_reconstructor/` | **Medium** | Name collision on `body_contour_solver` — use paths |
| **Feedback submit_correction dead** | vectorizer_phase3 scaffold | **DEAD** — no API | N/A | **Low** | PR-3 lifecycle gate only |
| **record_classification partial** | SMART + enable_feedback | PARTIAL single call site | N/A | **Low** | Mark PARTIAL in lifecycle registry |
| **Contour hierarchy duplication** | edge_to_dxf + api contour_hierarchy | Both ACTIVE (duplicated) | N/A | **Medium** | Extract shared module when allowed |
| **IBG provenance on saveas** | Runtime boundary inventory | IBG solvers emit DXF without full lifecycle | N/A | **Medium** | Provenance model ratification pending |
| **Tier A grep gate** | Migration plan Phase 0.5 | `check_semantic_sandbox_imports.py` | Files only in sandbox | **High** | Precommit in `check_all.py` |
| **Wave C graduation 2026** | Cognitive/grid research | None targeted | `src/semantic/`, `src/archaeology/` | **Low** (if assumed) | Alignment: no 2026 promotion assumed |

---

## Sandbox / runtime separation (explicit)

| Class | May run in production default? | Home |
|-------|-------------------------------|------|
| Extraction evidence (DXF bytes, contours) | Yes (named canonical modes) | `luthiers-toolbox` orchestrators |
| Interpretation (ML class, grid occupancy) | No unless graduated | `vectorizer-sandbox` |
| Authority (intake, provenance, RMOS) | Yes (gates) | `luthiers-toolbox` governance + IBG |
| Evaluation benchmarks | No (manual/CI optional) | `vectorizer-sandbox/src/evaluation/` |

---

## Risk heatmap (summary)

Formal **High / Medium / Low** ratings are required on matrix rows (ratified 1A). Narrative-only risk is deprecated.

| Severity | Discoveries |
|----------|-------------|
| **High** | Grouping fallback silent history; confidence≠authority; sandbox→prod bypass; IBG gate skip |
| **Medium** | Primitive starvation; slab collapse; calibration path split; hierarchy duplication |
| **Low** | Archive path confusion; stale handoff URLs to old sandbox dirs |

---

## Related registries

- Topology mechanisms: [TOPOLOGY_IDEA_REGISTRY.md](TOPOLOGY_IDEA_REGISTRY.md)
- Waves: [RESEARCH_WAVE_INDEX.md](RESEARCH_WAVE_INDEX.md)
- IBG: [IBG_LINEAGE_MAP.md](IBG_LINEAGE_MAP.md)

---

*Semantic Discovery Matrix — Research Wave 1A — 2026-05-20*
