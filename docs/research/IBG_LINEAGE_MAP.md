# IBG Lineage Map

**Purpose:** Preserve IBG intent across vectorizer sandbox migration — **performance objective and constitutional boundary** must not be lost when cognition code moves to `vectorizer-sandbox`.

**Status:** Research memory (Wave Index 1A)  
**Authority:** Documentary only — production behavior is defined in `docs/governance/IBG_*` and code under `services/api/app/instrument_geometry/body/ibg/`

---

## IBG performance objective (canonical — ratified 1A)

```text
IBG exists to produce provenance-bearing,
human-reviewable body evidence
for governed geometric workflows.
```

**Not:** fully autonomous body completion.

IBG supports **semantic operationalization**, not autonomous semantic authority.

Operational implications:

- Incomplete vectorizer DXF → recovered topology → ranked body candidates
- Provenance and confidence **declared** before any “approved for generation” state
- **No silent bypass** of intake gate for commercial outputs

Vectorizer migration must not collapse this into “more extraction modes.”

---

## Lineage diagram

```text
2026-04  Wave A prototypes (sandbox/arc_reconstructor)
            │
            ▼
2026-04-16  Production IBG package (ibg/*.py)
            │     arc_reconstructor, body_contour_solver,
            │     constraint_extractor, instrument_body_generator,
            │     reference_outline_bridge
            ▼
2026-04+    body_grid/ (zones, morphology_descriptor, primitives)
            │
2026-05     morphology_harvest/ (PDF inventory, harvest coordinator)
            │
2026-05-18  workflow/ DEV ORDER 1A-WORKFLOW
            │     ibg_workflow_pipeline → review_package
            │     BodyEvidenceCandidate + IBGIntakeGate
            ▼
2026-05-20  vectorizer-sandbox gets archaeology copies only
            (NOT production IBG)
```

---

## Component lineage

### Arc reconstruction

| Stage | Location | Role |
|-------|----------|------|
| R&D prototype | `vectorizer-sandbox/src/archaeology/arc_reconstructor/arc_reconstructor.py` | 4-tier gap closure experiments |
| **Production** | `ibg/arc_reconstructor.py` | Authoritative gap closure for IBG spine |
| Related topology | `ibg/workflow/topology_recovery.py` | Contour/loop recovery in workflow |

**Risk if forgotten:** Production and archaeology diverge; engineers tune sandbox DXF while IBG behavior drifts.

---

### Body grid

| Stage | Location | Role |
|-------|----------|------|
| Schema | `ibg/body_grid/body_grid_schema.py` | `BodyEvidence`, zones, morphology |
| Grammar | `variant_grammar.py`, `primitives.py`, `grid_normalizer.py` | Structural semantics of body regions |
| R&D grids | `vectorizer-sandbox/src/archaeology/extract_body_grid_v*.py` | Historical grid extraction iterations (**not** production) |

**Risk if forgotten:** Grid archaeology mistaken for active body grid logic.

---

### Morphology harvest

| Stage | Location | Role |
|-------|----------|------|
| Harvest spine | `ibg/morphology_harvest/harvest_coordinator.py` | PDF/DXF harvest orchestration |
| Evidence adapter | `artifact_body_evidence_adapter.py` | Artifact → evidence shapes |
| Inventory | `pdf_inventory.py` | Pattern from evaluation-era DXF inventory |
| Governance | `docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md` | Extend vs replace BodyEvidence |

**Unresolved:** `HarvestRecord.to_body_evidence()` parity; harvest not same as Workflow 1A review package.

---

### BodyEvidence → BodyEvidenceCandidate

| Type | File | Role |
|------|------|------|
| `BodyEvidence` | `body_grid/body_grid_schema.py` | Geometry + morphology payload |
| `BodyEvidenceCandidate` | `body_evidence_candidate.py` | Constitutional wrapper (authority_state, provenance hooks) |

**Semantic rule:** Candidates carry **metadata for gates**; evidence alone does not imply fabrication approval.

---

### IBGIntakeGate

| Item | Location |
|------|----------|
| Implementation | `ibg/ibg_intake_gate.py` |
| Tests | `services/api/tests/test_ibg_constitutional_integration.py` |
| Foundation doc | `docs/governance/IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` |

**States (research summary):** e.g. sandbox → advisory candidate → blocked / approved paths (see constitutional tests). Intake gate is **operational authority** boundary.

**Risk if forgotten:** Vectorizer outputs wired directly to CAM without candidate + gate → semantic collapse.

---

## Morphology Harvest vs Workflow 1A

| System | Role | Status |
|--------|------|--------|
| **Morphology Harvest** | Semantic extraction + evidence preparation | Active R&D / production adapters |
| **Workflow Pipeline 1A** | Governed intake + runtime orchestration | **Internal** infrastructure |

**Shared intake lineage** — may converge later; **do not collapse** in documentation yet.

---

## Workflow Pipeline 1A (DEV ORDER 1A-WORKFLOW)

**Visibility:** **Internal / developmental** — not public API product surface yet. Document for architecture and lineage; do not market as stable operator workflow.

**Canonical entry:** `ibg/workflow/ibg_workflow_pipeline.py`

| Step | Module | Output |
|------|--------|--------|
| 1 | `artifact_preservation.py` | Preserved DXF/SVG as produced |
| 2 | `topology_recovery.py` | Contours, loops, gap statistics |
| 3 | `candidate_scoring.py` | Ranked regions |
| 4 | wrap | `BodyEvidenceCandidate[]` with provenance |
| 5 | `ibg_intake_gate.py` | Gate result (expect block until approved) |
| 6 | `review_package.py` | Human-review disk package |

**Success condition (from module docstring):** Provenance-bearing, confidence-declared, gate-blocked candidates + review package — **not** silent G-code.

**Relation to vectorizer:** Accepts **artifacts from extraction runtime** (REFINED, V2_RAW, photo_v2, etc.); does not replace vectorizer orchestrators.

---

## Review package

| Item | Location |
|------|----------|
| Emitter | `ibg/workflow/review_package.py` |
| Purpose | Operator-facing bundle for constitutional review |

Preserves **human ratification** step from incubation architecture.

---

## Separation from vectorizer cognition

| Concern | IBG (this map) | Vectorizer cognition |
|---------|----------------|----------------------|
| Repo home | `luthiers-toolbox` `ibg/` | `vectorizer-sandbox` |
| Question | “May this body evidence fabricate?” | “What contours/classes exist?” |
| Graduation | Into fabrication only via gate | Into spine only via bridge |

---

## Preservation actions (1A)

1. Never delete production `ibg/` when cleaning sandboxes.
2. Point archaeology questions to `vectorizer-sandbox/src/archaeology/arc_reconstructor/`.
3. Treat Workflow 1A as the **integration contract** between extraction waves and IBG authority.
4. Update [RESEARCH_WAVE_INDEX.md](RESEARCH_WAVE_INDEX.md) when new DEV ORDERs extend workflow.

---

## Related governance (not duplicated here)

- `docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md`
- `docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md`
- `docs/governance/IBG_CONSTITUTIONAL_RUNTIME_1A_COVERAGE_NOTE.md`

---

*IBG Lineage Map — Research Wave 1A — 2026-05-20*
