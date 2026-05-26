# Cross-Repository Authority Crosswalk

**Date:** 2026-05-24  
**Status:** Draft — documentation authority (non-runtime)  
**Scope:** `luthiers-toolbox`, `tap_tone_pi`, `CAM-Assist-Blueprint`, `vectorizer-sandbox` (reference only)  
**Companion:** [`MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md`](../MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md), [`MANIFEST.md`](../handoffs/imports/MANIFEST.md)  
**Research context:** [`docs/research/RESEARCH_WAVE_INDEX.md`](../research/RESEARCH_WAVE_INDEX.md) (non-authoritative institutional memory)

**Constitutional source (verbatim):** [`docs/handoffs/imports/constitutional_stabilization_do_77_82/`](../handoffs/imports/constitutional_stabilization_do_77_82/)

---

## Purpose

Three repositories independently converged on **human authority, non-execution, and fail-closed validation** — but each invented its own vocabulary. This crosswalk maps equivalent concepts, flags non-equivalent collisions, and marks items that could not be verified on disk.

**Rule:** Crosswalk entries describe **semantic intent**, not automatic runtime equivalence. Integration requires explicit Dev Orders.

---

## 1. Authority domain mapping

### 1.1 Primary authority classes

| Concept | tap_tone_pi | luthiers-toolbox | CAM-Assist-Blueprint | Equivalent? |
|---------|-------------|------------------|----------------------|---------------|
| Physical measurement capture | `AuthorityClass.MEASUREMENT` (ADR-0009) | `DxfLifecycleContext` + capture paths | N/A (no measurement) | Partial — different domain |
| Advisory / guidance | `AuthorityClass.DECISION_SUPPORT` (ADR-0010) | Review UX panels, rank signals (non-authoritative) | Review packet prose (advisory) | **Aligned intent** |
| Operator sovereignty | ADR-0010 § operator supreme | 8E: human decides; routing does not | A12: human records decision | **Aligned intent** |
| Machine execution | Forbidden in measurement exports | 8E: `execution_authorized=False` always | `execution_authority_claim=false` always | **Aligned intent** |
| IBG ontology authority | N/A | `AuthorityState` on `BodyEvidenceCandidate` | N/A | luthiers-only |
| R&D cognition | N/A | `R_AND_D_EXCLUDED` lifecycle class | N/A | vectorizer-sandbox external |

### 1.2 tap_tone orthogonal domains (ADR-0010, DO 78)

From Constitutional Stabilization handoff — four domains, not a binary split:

```text
Measurement  |  Advisory  |  Interpretive  |  Operator
```

| Domain | May establish truth? | luthiers analogue | CAM analogue |
|--------|---------------------|-------------------|--------------|
| Measurement | Context-dependent legitimacy (ADR-0011) | OBSERVED/DERIVED export paths (when provenance ratified) | N/A |
| Advisory | **No** — may prioritize attention only | Review routing, heuristic rank | Review packet, strategy JSON |
| Interpretive | **No** — model-dependent | IBG morphology interpretation, `ConfidenceType.HEURISTIC` | Strategy inference notes |
| Operator | **Yes** — final for human decisions | `ReviewDecisionRecord`, operator review panels | A12 human decision record |

---

## 2. Epistemic status ↔ export lifecycle ↔ CAM provenance

### 2.1 tap_tone epistemic taxonomy (ADR-0012, constitutional — not yet in all schemas)

| Epistemic status | Authority level | luthiers lifecycle / posture | CAM manifest field | Notes |
|------------------|-----------------|------------------------------|--------------------|-------|
| **OBSERVED** | Measurement-authoritative | `LIFECYCLE_GOVERNED` / `COMPAT_ONLY` when provenance complete | `provenance.source_spec_id` (external) | tap_tone: sensor capture; luthiers: governed DXF create-save |
| **DERIVED** | Computationally authoritative | `COMPAT_ONLY` + guards | Derived strategy from geometry refs | Does not inherit measurement authority (ADR-0011) |
| **ESTIMATED** | Approximation only | `ConfidenceType.STATISTICAL` / `EPISTEMIC` | — | **PENDING** — no shared enum in CAM |
| **PREDICTED** | Model-dependent | IBG candidates, vectorizer outputs | — | Toolbox import: Predicted only (per tap_tone matrix) |
| **HEURISTIC** | No authority | `rank_score`, advisory panels | Review packet advisory sections | Must not enter tap_tone `viewer_pack_v1` |
| **OPERATOR-ANNOTATED** | Operator only | `ReviewDecisionRecord`, review notes | A12 decision `reviewer_id` | |
| **EXTERNALLY-SOURCED** | External authority | Imported DXF / blueprint paths | `provenance.source_spec_id` | Requires explicit import marking |

### 2.2 luthiers export lifecycle classes

From `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md`:

| Lifecycle class | Meaning | tap_tone epistemic analogue | CAM relevance |
|-----------------|---------|----------------------------|---------------|
| `LIFECYCLE_GOVERNED` | Full orchestrator + gates | OBSERVED/DERIVED (when provenance ratified) | Downstream of approved strategy packages |
| `COMPAT_ONLY` | `dxf_compat` without full orchestrator | DERIVED | Geometry refs in strategy packages |
| `DIRECT_SAVE_GAP` | Read-modify-write without gate | **Risk** — authority laundering if unmarked | — |
| `BLOCKED_PROVENANCE` | IBG paths awaiting ratification | PREDICTED / HEURISTIC until ratified | **PENDING** — 5 IBG save points blocked |
| `R_AND_D_EXCLUDED` | photo-vectorizer / sandbox | HEURISTIC / PREDICTED | Must not feed CAM spine without graduation |

---

## 3. Confidence vocabulary crosswalk

| Field / type | Repo | Semantics | Authoritative? | Maps to |
|--------------|------|-----------|----------------|---------|
| `TypedConfidenceV1` | tap_tone_pi | `domain` + `value` + `source` | **No** for DECISION_SUPPORT | Target canonical pattern |
| `ConfidenceDeclaration` | luthiers IBG | `value`, `confidence_type`, `origin`, `does_not_imply` | **No** — `implies_correctness()` always False | Aligns with TypedConfidence intent |
| `rank_score` | luthiers IBG workflow | Composite ranking 0.0–1.0 | **No** — sort key only | **HEURISTIC** (ADR-0012); not approval |
| `confidence_value` on candidate | luthiers IBG | Copied from `rank_score` in pipeline | **No** | **Collision risk** — label says confidence |
| Bare `confidence: float` | tap_tone (legacy) | Deprecated in directives | **No** | Migrate to TypedConfidenceV1 |
| `Advisory Confidence` (UI) | tap_tone (DO 80 patch) | Presentation-labeled heuristic | **No** | HEURISTIC |
| CAM authority block | CAM-Assist | No confidence field | N/A | Confidence belongs in review packet prose only |

### 3.1 Constitutional non-implications (shared intent)

All three repos agree (explicitly or by invariant):

```text
High score / confidence does NOT imply:
  - correctness
  - approval
  - execution authority
  - review bypass
  - canonical / production readiness
```

**Enforcement:** tap_tone CI + contracts; luthiers Pydantic 8E invariants + `ConfidenceDeclaration`; CAM JSON Schema authority consts.

---

## 4. Review queue semantic mapping

**Critical:** These are **parallel systems**, not drop-in replacements.

### 4.1 System comparison

| Property | luthiers 8E | CAM-Assist A11/A12 | IBG Workflow 1A |
|----------|-------------|--------------------|-----------------|
| **Purpose** | Route human attention | Index staged packages; record decisions | Emit ranked body evidence packages |
| **ID format** | `rqi-{uuid12}`, `rdr-{uuid12}` | Package directory + manifest hash | Workflow run / candidate IDs |
| **Storage** | In-memory registry (**ephemeral**) | Filesystem staged packages | Workflow output artifacts |
| **Makes decisions?** | **No** — routing only | **No** — records human decision | **No** — ranks candidates |
| **Authorizes execution?** | **No** (invariant) | **No** (`execution_authority_claim=false`) | **No** — gate may block export |
| **Human review required** | `human_review_required=True` always | `requires_human_review=true` always | Review package for operator |
| **CI integration** | `ReviewQueueCISummary` | pytest + index scripts | **PENDING** — partial test coverage |

### 4.2 Decision type mapping

| luthiers `DecisionType` (8E) | Effect on queue status | CAM A12 analogue | IBG analogue |
|-------------------------------|------------------------|------------------|--------------|
| `acknowledge` | → `in_review` | — | Operator opens review package |
| `request_more_evidence` | → `needs_more_evidence` | — | Re-run workflow / more inputs |
| `defer` | → `deferred` | Staged package remains queued | Candidate deprioritized |
| `reject` | → `rejected` | Reject decision record | Candidate excluded |
| `mark_reviewed` | → `reviewed` | `approve_for_downstream_cam` (**PENDING** — schema not on disk) | **PENDING** — no equivalent enum |

**Warning:** CAM handoff describes `approve_for_downstream_cam` as an A12 decision type. The schema file `schemas/review_decision_record.schema.json` is **PENDING / not found on disk** — verify before integration.

### 4.3 What each system does NOT authorize

| System | Does NOT authorize |
|--------|-------------------|
| luthiers 8E | Implementation, execution, machine output, auto-approval |
| CAM A11/A12 | G-code, machine execution, downstream CAM without human |
| IBG review package | Ontology promotion, IBG memory write, guarded DXF export (when BLOCKED_PROVENANCE) |

---

## 5. Schema crosswalk

### 5.1 Persisted artifact types

| Artifact | tap_tone_pi | luthiers-toolbox | CAM-Assist-Blueprint |
|----------|-------------|------------------|----------------------|
| Measurement export | `viewer_pack_v1.schema.json` | — | — |
| Advisory directive | `analyzer_attention` contracts | — | — |
| DXF export context | — | `ExportLifecycleContext` / guards | Geometry refs in manifest |
| Strategy intent | — | Strategy export registries (7U+) | `strategy.schema.json` |
| Portable package | — | Federated review packages (8X+) | `strategy_package_manifest.schema.json` |
| Review decision | — | `ReviewDecisionRecord` (Pydantic) | `review_decision_record.schema.json` (**PENDING**) |
| Semantic candidate | — | `BodyEvidenceCandidate` | — |

### 5.2 Authority block patterns

| Field | CAM manifest | CAM strategy | luthiers 8E | tap_tone directive |
|-------|--------------|--------------|-------------|-------------------|
| Non-execution declared | `non_execution_declaration: true` | `execution_authority_claim: false` | N/A (routing layer) | N/A |
| Execution claim | `execution_authority_claim: false` | same | `execution_authorized: false` | Forbidden in exports |
| Human review | `requires_human_review: true` | implied | `human_review_required: true` | Operator for exports |
| Instrument class | N/A | N/A | Review source layer | `authority_class` enum |

### 5.3 Recommended shared schema IDs (future — not implemented)

```text
platform-contracts/authority-v1.json
platform-contracts/epistemic-status-v1.json
platform-contracts/review-decision-v1.json
platform-contracts/confidence-v1.json
```

**Status:** **PENDING** — documentation-only recommendation from convergence report Phase 2.

---

## 6. Governance mechanism crosswalk

| Concern | tap_tone_pi | luthiers-toolbox | CAM-Assist-Blueprint |
|---------|-------------|------------------|----------------------|
| CI entry | `pytest`, `ci/check_*.py` | `scripts/governance/check_all.py` | `pytest` |
| Blocks merge | Export boundary tests, boundary guard | Governance gate (authority chain) | Schema validation |
| Language / vocabulary guard | `check_guidance_language` (non-strict, 13 findings) | Lexical governance inventory | Authority block in JSON Schema |
| Import boundaries | `check_boundary_imports.py` | Vectorizer sandbox import gate | Standalone repo |
| Structural vs lexical | **Structural** (instrument class headers) | **Lexical** (forbidden terms) | Schema const enforcement |

**DO 77 insight:** Combined structural + lexical governance is intentional complementarity — not duplication to merge blindly.

---

## 7. Constitutional Stabilization (DO 77–82) — luthiers impact

Sprint targeted **tap_tone_pi**; luthiers is downstream consumer per handoff.

| Dev Order | tap_tone outcome | luthiers touchpoint |
|-----------|------------------|---------------------|
| **77** | Governance consolidation audit | `docs/handoffs/TAP_TONE_PI_GOVERNANCE_CONSOLIDATION_AUDIT.md` |
| **78** | ADR-0010 + AGE contract | Acoustic/advisory UI in client (EvidenceReviewPanel — **PENDING** integration review) |
| **79–80** | Presentation boundary + patches | Any shared HTML/report surfaces |
| **81** | ADR-0011/12 + epistemic taxonomy | Map to `ConfidenceType`, export lifecycle, IBG provenance |
| **82** | Conditional stabilization mode | Operational dev primary; escalate only on triggers |

**Escalation triggers (DO 82)** — apply cross-repo when integration work begins:

- Authority semantics ambiguity
- Epistemic status conflicts
- Boundary violations
- Provenance questions
- Operator sovereignty bypass
- Authority laundering detected

---

## 8. vectorizer-sandbox posture (reference)

| Property | Value | Crosswalk note |
|----------|-------|----------------|
| Role | Cognition / R&D lab | Not production spine |
| Branch | `master` @ `6390c26` | Synced with origin |
| Production spine | luthiers-toolbox | Tier A migration complete |
| Lifecycle class | `R_AND_D_EXCLUDED` | Outputs default to HEURISTIC/PREDICTED epistemic posture |
| Integration | Import gate CI in luthiers | **PENDING** tag on sandbox release per research docs |

---

## 9. PENDING / external verification registry

| ID | Item | Why pending |
|----|------|-------------|
| P-001 | CAM `review_decision_record.schema.json` | **RESOLVED** — merged to `main` (`6f8947f`) on 2026-05-24 |
| P-002 | CAM → luthiers 8E runtime wire-up | No verified API/import path |
| P-003 | tap_tone 27 commits pushed to origin | **RESOLVED** — `main` tracks `origin/main` at `27478d8` |
| P-004 | IBG BLOCKED_PROVENANCE ratification | **Documented** — `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` |
| P-005 | Research Wave 1A/1B spine files | **Restored** 2026-05-24 from `origin/research/wave-1a-semantic-memory` |
| P-006 | Epistemic status in tap_tone JSON schemas | ADR-0012 doctrine-only; fields in implications memo only |
| P-007 | luthiers untracked CAM 7U–7W implementation | Large working tree not in manifest commits |
| P-008 | `approve_for_downstream_cam` exact semantics | **Verified** on A12 branch schema — does NOT authorize machine execution |

---

## 10. Immediate convergence actions (from crosswalk)

| Priority | Action | Owner repo | Status |
|----------|--------|------------|--------|
| P0 | Push tap_tone 27 commits | tap_tone_pi | **DONE** — synced 2026-05-24 |
| P0 | Rename or git-add constitutional import path (avoid em-dash root folder) | luthiers-toolbox | Pending |
| P0 | Merge CAM A12 to main | CAM-Assist-Blueprint | **DONE** — `6f8947f` merged 2026-05-24 |
| P1 | Restore research 1A/1B from `origin/research/wave-1a-semantic-memory` | luthiers-toolbox | Pending |
| P1 | Add epistemic_status optional field to luthiers review artifacts (additive) | luthiers-toolbox | Pending |
| P2 | Publish shared `review-decision-v1` spec (docs-only) | platform-contracts (future) | Deferred |

---

*Crosswalk version: 2026-05-24*  
*Next update trigger: first cross-repo integration Dev Order or IBG provenance ratification.*
