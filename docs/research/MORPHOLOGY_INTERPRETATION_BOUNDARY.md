# Morphology Interpretation Boundary

**Wave:** 1B  
**Purpose:** Define where **topology evidence** ends and **morphology inference** begins — and where **semantic authority must stop**.

Constitutional invariants (unchanged): `visibility ≠ legitimacy`, `semantic influence ≠ semantic authority`, `confidence ≠ canonization`.

---

## Three-layer split (required)

| Layer | Location | Role | Authority |
|-------|----------|------|-----------|
| **Morphology Harvest** | `ibg/morphology_harvest/` (`harvest_coordinator`, `e2e_spine_runner`) | Semantic extraction + evidence preparation; coordinates Phase 4 / calibration / body_grid adapters | **No fabrication gate** — prep only |
| **body_grid / MorphologyDescriptor** | `ibg/body_grid/` (`MorphologyAnalyzer`, `MorphologyDescriptor`, `zones`, `primitives`) | Morphology interpretation (zones, variant grammar, primitives, descriptor confidence) | **Advisory** to IBG — optional evidence |
| **Workflow Pipeline 1A** | `ibg/workflow/ibg_workflow_pipeline.py` | Governed intake: preserve → topology → candidates → `BodyEvidenceCandidate` → `IBGIntakeGate` → review package | **Operational boundary** — internal infrastructure, not public operator API |

Do not collapse harvest, grid, and workflow into one “morphology system.”

---

## Evidence types

| Type | Schema | Wrapper | Meaning |
|------|--------|---------|---------|
| **BodyEvidence** | `body_grid_schema.BodyEvidence` | — | Geometry + morphology payload container |
| **BodyEvidenceCandidate** | `body_evidence_candidate.BodyEvidenceCandidate` | Governance provenance + `AuthorityState` | Constitutional intake object — **not auto-approved** |
| **MorphologyDescriptor** | `morphology_descriptor.MorphologyDescriptor` | — | Interpreted zones, primitives, `variant_match`, `confidence` |

`create_candidate_from_evidence()` bridges evidence → candidate with explicit confidence declaration (`create_heuristic_confidence`, etc.).

---

## What morphology currently infers (runtime)

From `MorphologyDescriptor` and analyzers (verified on disk):

- Centerline and asymmetry descriptors
- Left/right flank profiles and zone assignments
- `MorphologyPrimitive` lists via `PrimitiveDetector`
- `VariantMatch` / `BodyMorphologyClass` via variant grammar
- `confidence` (float) on descriptor — **heuristic composite**, not RMOS
- `missing_regions`, `hardware_regions` (non-authoritative observations)
- Docstring states: consumed as **optional advisory evidence without changing solver behavior**

**Heuristic / not authoritative:** variant grammar match, zone coverage thresholds, hardware region tagging.

---

## Confidence semantics (dual track)

### Runtime confidence (spine)

| Source | Module | Canonical? |
|--------|--------|------------|
| Candidate scoring | `candidate_scoring.ScoringSignals.composite_score` | Ranking only — not fabrication |
| Morphology descriptor | `MorphologyDescriptor.confidence` | Advisory |
| Constitutional declaration | `ConfidenceDeclaration` on `BodyEvidenceCandidate` | Declared, review-gated |
| RMOS | Governance / API routers | Operational safety band — not body morphology canon |

### Sandbox ML confidence (research-only)

| Label | Required |
|-------|----------|
| non-authoritative | yes |
| research-only | yes |
| non-canonical | yes |

Location: `vectorizer-sandbox` cognitive / classifier archaeology — **must not** wire to `IBGIntakeGate` default path. See lifecycle: `TrainingDataCollector`, `submit_correction` **DEAD** on spine.

---

## Review boundaries

| Boundary | Enforcement |
|----------|-------------|
| Candidate → fabrication | `IBGIntakeGate` + `ReviewEnforcement` |
| Descriptor → solver | Advisory only — PENDING / external verification for all solver call sites |
| Harvest → production default | Adapter path only; no silent promotion |
| Review package | `emit_review_package()` — human-readable bundle, gate-blocked expectation |

Workflow 1A success condition (module docstring): provenance-bearing, confidence-declared, **gate-blocked** candidates + review package.

---

## What morphology must NOT do (1B scope)

- Populate long-term IBG memory / ontology federation
- Auto-approve candidates from high descriptor confidence
- Export public “canonical morphology” API (Workflow 1A remains internal)

---

## Cross-links

- Runtime bridge: [IBG_RUNTIME_POSITION.md](IBG_RUNTIME_POSITION.md)
- Lineage: [IBG_LINEAGE_MAP.md](IBG_LINEAGE_MAP.md)
- Trace: [SEMANTIC_INTERPRETATION_TRACE.md](SEMANTIC_INTERPRETATION_TRACE.md)
- Observability: [SEMANTIC_OBSERVABILITY_MAP.md](SEMANTIC_OBSERVABILITY_MAP.md)

---

*Research Wave 1B — 2026-05-20*
