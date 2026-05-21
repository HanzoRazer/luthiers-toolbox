# Semantic Interpretation Trace

**Wave:** 1B — Semantic Interpretation Trace (subordinate phase, May 2026+)  
**Status:** ACTIVE — continuity tracing only; no operational authority  
**Spine:** Primary Wave 1B document

Cross-links (do not duplicate full narratives): [SEMANTIC_DISCOVERY_MATRIX.md](SEMANTIC_DISCOVERY_MATRIX.md), [TOPOLOGY_IDEA_REGISTRY.md](TOPOLOGY_IDEA_REGISTRY.md), [IBG_LINEAGE_MAP.md](IBG_LINEAGE_MAP.md).

Citation: `runtime spine @ pending tag` · `vectorizer-sandbox @ pending tag`

---

## Purpose

Trace how **semantic meaning survives or collapses** from vectorizer DXF through IBG governed intake to review package — without granting new authority.

```text
DXF → contour reconstruction → topology continuity → candidate isolation
    → BodyEvidence → primitive extraction → morphology interpretation
    → confidence propagation → review package
```

---

## Stage trace

| Stage | Primary modules | Inputs | Outputs | Semantic assumption | Known collapse modes | Current instrumentation | Missing observability |
|-------|-----------------|--------|---------|---------------------|----------------------|-------------------------|------------------------|
| **1. DXF intake** | `vectorizer_phase3.py`, `edge_to_dxf.py`, API orchestrators | Raster/vector sources, cleanup mode | DXF bytes, entity inventory | Exported geometry = extraction evidence, not fabrication approval | SIMPLE empty export; UNKNOWN exclusion; mode mis-label | PR-1 tests `test_vectorizer_simple_export.py`; mode in API response | Per-mode semantic loss budget |
| **2. Contour reconstruction** | `ibg/workflow/topology_recovery.py` → `recover_topology()` | DXF bytes | `ContourCandidate[]`, `TopologyStats` | Chained segments approximate body topology | Open chains; near-closed gaps; fallback path `_fallback_topology_recovery` | Stage result in `IBGWorkflowPipeline.run()` | Entity-level chain provenance in review package |
| **3. Topology continuity** | `topology_recovery._chain_segments`, arc recon (`ibg/arc_reconstructor.py`) | Primitives/segments | Closed/near-closed loops, gap_distance | Gap closure tiers preserve fabricatability | Loop fragmentation; false closure — see [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md) | `TopologyStats` (open/closed/near_closed counts) | Tier-used telemetry per contour |
| **4. Candidate isolation** | `IBGWorkflowPipeline.isolate_candidates()` | Contours | Ranked body region candidates | Largest closed region ≈ body hypothesis | Partial body isolation; wrong contour ownership | Scoring signals in `candidate_scoring.py` | Contour ownership graph |
| **5. BodyEvidence wrap** | `IBGWorkflowPipeline._contour_to_evidence()`, `body_grid_schema.BodyEvidence` | Contour geometry | `BodyEvidence` (normalized segments) | Evidence container ≠ approved morphology | Normalization hides source scale errors | `EvidenceSource` on schema | Full DXF→normalized transform log |
| **6. BodyEvidenceCandidate** | `body_evidence_candidate.create_candidate_from_evidence()` | `BodyEvidence` | `BodyEvidenceCandidate` + provenance | **Confidence declared, not canonical** | Treating candidate as approved body | Governance `ProvenanceRecord`, `ConfidenceDeclaration` | End-to-end provenance on review disk |
| **7. Primitive extraction (spine)** | `vectorizer_phase3` `PrimitiveDetector` / `export_primitives_to_dxf`; `body_grid/primitives.py` | Contours / grid | `GeometricPrimitive`, `MorphologyPrimitive` | Primitives support CAM holes/routes | **Primitive starvation** — see [PRIMITIVE_FLOW_ANALYSIS.md](PRIMITIVE_FLOW_ANALYSIS.md) | `primitives_count` in phase3 results; descriptor primitive list | Primitive survival rate DXF→grid |
| **8. Morphology interpretation** | `body_grid/morphology_descriptor.MorphologyAnalyzer` → `MorphologyDescriptor` | `BodyEvidence` | Zones, variant_match, descriptor confidence | **Advisory** semantics for IBG | **slab_body collapse** (occupancy → single region) | `morphology_class`, `confidence` in harvest E2E logs | Zone-level collapse detector |
| **9. Morphology harvest (prep)** | `morphology_harvest/harvest_coordinator.py`, `e2e_spine_runner._stage_body_grid` | Harvest inputs | Harvest records → body_grid adapter | Harvest prepares evidence, does not gate fabrication | Skipping gate via harvest-only path | `E2ESpineResult.body_grid_success` | Harvest→candidate provenance bridge |
| **10. Confidence propagation** | `candidate_scoring.ScoringSignals.composite_score`; RMOS; `MorphologyDescriptor.confidence`; sandbox ML | Multi-source signals | Rankings, advisory labels | **confidence ≠ canonization** | High ML score → false legitimacy | Partial — see [SEMANTIC_OBSERVABILITY_MAP.md](SEMANTIC_OBSERVABILITY_MAP.md) | Unified confidence lineage ID |
| **11. Intake gate** | `ibg_intake_gate.IBGIntakeGate` | `BodyEvidenceCandidate[]` | `IntakeValidationResult` (expect block) | Gate = commercial boundary | Bypass gate → fabrication without review | `test_ibg_constitutional_integration.py` | Gate reason codes in review package |
| **12. Review package** | `workflow/review_package.emit_review_package()` | Candidates + gate results | On-disk review bundle | Human review required | Package without provenance | `ReviewPackage` JSON structure | Candidate trace dump (deferred instrumentation) |

---

## Layer boundaries (1B)

| Layer | Repo path | Role |
|-------|-----------|------|
| Vectorizer spine | `services/blueprint-import/`, `services/photo-vectorizer/` | Extraction evidence |
| Cognition lab | `vectorizer-sandbox` | **non-authoritative** research-only ML/eval |
| IBG runtime | `services/api/.../body/ibg/` | Governed operationalization |
| Workflow 1A | `ibg/workflow/ibg_workflow_pipeline.py` | Internal intake orchestration |

Detail: [MORPHOLOGY_INTERPRETATION_BOUNDARY.md](MORPHOLOGY_INTERPRETATION_BOUNDARY.md), [IBG_RUNTIME_POSITION.md](IBG_RUNTIME_POSITION.md).

---

## Verified example (grouping fallback)

| Field | Value |
|-------|--------|
| fixture_status | partially_verified |
| artifact_path | `services/photo-vectorizer/grouping_telemetry.py`; call sites `edge_to_dxf.py` (~L1252+); test `services/api/tests/test_vectorizer_grouping_telemetry.py` |
| verification_state | telemetry counters + API `build_topology_provenance()` on spine |

---

## Related Wave 1B docs

| Need | Document |
|------|----------|
| Primitive loss | [PRIMITIVE_FLOW_ANALYSIS.md](PRIMITIVE_FLOW_ANALYSIS.md) |
| Morphology vs authority | [MORPHOLOGY_INTERPRETATION_BOUNDARY.md](MORPHOLOGY_INTERPRETATION_BOUNDARY.md) |
| Failure catalog | [TOPOLOGY_CONTINUITY_FAILURES.md](TOPOLOGY_CONTINUITY_FAILURES.md) |
| Observability gaps | [SEMANTIC_OBSERVABILITY_MAP.md](SEMANTIC_OBSERVABILITY_MAP.md) |
| Open questions | [WAVE_1B_RESEARCH_QUESTIONS.md](WAVE_1B_RESEARCH_QUESTIONS.md) |

---

*Research Wave 1B — 2026-05-20*
