# Vectorizer / IBG — Cross-Repo Reconciliation 001

**Date:** 2026-08-29
**Custody:** `luthiers-toolbox` (`LTB`). This document does **not** govern or modify
`vectorizer-sandbox` (`VS`). It is Toolbox's production-side reconciliation of evidence held
across both repositories. `VS` was read only.
**Base:** `LTB origin/main` @ `9d5d9001`
**Lane:** B. Read-only against DET-001, which is Lane A and independently active. Nothing here
gates it.

---

## 0. Governing rule

> **Surviving architecture proves what survived. It does not prove original intent,
> deliberate selection, or architectural superiority.**

Applied throughout. Where today's arrangement is described, it is described as *what exists*,
never as *what was chosen*, unless a decision record says otherwise.

**Provenance vocabulary:** `LTB` · `VS` · `BOTH` · `UNVERIFIED`.

---

## 1. Re-grounding verdict on the inherited claims

This reconciliation inherited a set of hypotheses from a prior session. Per instruction they
were re-derived rather than adopted. **Two of five load-bearing claims did not survive.**

| # | Inherited claim | Verdict |
|---|---|---|
| 1 | Production IBG is ~14k LOC with mounted `/api/body/solve-*` routes | **CONFIRMED** |
| 2 | Substantial `arc_reconstructor` and `morphology_harvest` implementations | **CONFIRMED** |
| 3 | Zero capabilities have graduated sandbox → production | **CONFIRMED** |
| 4 | POS-006 forbids the aspect-ratio prior production uses | **REFUTED — wrong mechanism** |
| 5 | Graduation Step 0 is RED because `svgwrite` is absent | **REFUTED — right conclusion, wrong cause** |

Claims 4 and 5 are the two that would have propagated into governance. Both are corrected in
§4 and §5.

Not verified, and therefore not asserted anywhere below: the render-lane portfolio figures
(129k–421k entities, 16–60 MB, high-80s/low-90s clarity). They were not located in `LTB`. If
they are DET-001's measurements they belong to Lane A, and this lane does not absorb them.

---

## 2. What actually shipped, and where

### 2.1 Production IBG — `LTB`, substantial and operational

```text
Source repo:    LTB
Source ref:     services/api/app/instrument_geometry/body/ibg/ @ 9d5d9001
Evidence class: DIRECT_MEASUREMENT
```

| Measure | Value |
|---|---:|
| Python files | **35** |
| Lines | **14,436** |
| `arc_reconstructor.py` | 1 file, **1,614** lines |
| `morphology_harvest/` | 12 files, **4,711** lines |

Mounted routes (`services/api/app/routers/body_solver_router.py`, registered via
`router_registry/manifests/cam_manifest.py:365`):

```text
POST /api/body/solve-from-dxf          upload partial DXF, receive solved model
POST /api/body/solve-from-landmarks    user-provided landmarks
GET  /api/body/session/{session_id}
PUT  /api/body/session/{session_id}/landmarks
```

Subpackages: `body_grid/`, `morphology_harvest/`, `workflow/`, plus
`body_contour_solver.py`, `constraint_extractor.py`, `ibg_intake_gate.py`,
`reference_outline_bridge.py`, `body_evidence_candidate.py`, `session_store.py`.

**Disposition: PRODUCTION.** Any characterisation of this as "concepts" inverts the
relationship — this is the substantial operational implementation of the program.

### 2.2 Sandbox material — `VS`, research and archaeology

```text
Source repo:    VS
Source ref:     src/{semantic,archaeology,incubation}/, docs/handoffs/, docs/architecture/
Evidence class: DIRECT_READ (read-only)
```

The May 20 migration moved **archaeology copies**, not production IBG. `LTB`'s own relocation
record says so (`services/photo-vectorizer/ARCHAEOLOGY_RELOCATION.md`, 2026-05-20 `4cbe56ed`):
`cognitive_extractor`, `cognitive_extraction_engine`, `extract_body_grid` v1–v5, and
`vectorizer_phase2.py` → `src/archaeology/vectorizer_phase2_runtime_spine.py`.

Active `VS` research: the `IBG_POS_*` series, `IBG_MAINT_00N_RESULT` series,
`IBG_BOUNDARY_FIDELITY.md`, `CANONICAL_INSTRUMENT_BODY_MODEL.md`, and `DET_001_DEV_ORDER.md`.

`VS` maintains its own state discipline — `IBG_SESSION_BOOKMARK.md` records a verified anchor
at `f42360b` (110 tests, 0 failures, 3 xfailed, 2026-06-21) with an explicit staleness rule.
That file also states, unprompted, that on any disagreement about C2 governance **`LTB` wins,
always.** The custody direction is asserted from both sides.

---

## 3. Has anything graduated? — **No. Zero.**

The bridge (`LTB docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md` §4) is six steps:

```text
sandbox capability
  → evidence validation (fixtures, golden comparisons, failure taxonomy)   <-- first gate
  → provenance wrapping (source SHA, experiment ID, reviewer)
  → deterministic instrumentation (telemetry, bounded outputs, fail-closed)
  → governance review (ADR, lifecycle registry update)
  → intake gate (IBG / Blueprint Reader contract)
  → production adoption (new code in services/, not symlink or submodule)
```

Graduation requires an **ADR** in `LTB docs/adr/` and a **lifecycle registry promotion**.
Positive checks for both:

| Required artifact | Found |
|---|---|
| ADR citing `vectorizer-sandbox` | **none** |
| `VECTORIZER_COMPONENT_LIFECYCLE.md` row promoted from sandbox to `ACTIVE` | **none** |

`INCUBATING_EXTERNAL` is defined as *"Active R&D in `vectorizer-sandbox`; not graduated to
runtime spine."* Everything sandbox-side sits at or before that state.

**Graduation count: 0.** Re-import is additionally blocked by a precommit gate,
`scripts/governance/check_semantic_sandbox_imports.py` (present and verified).

---

## 4. Boundary fidelity — the aspect-ratio claim, corrected

**Inherited claim:** *POS-006 forbids the aspect-ratio prior that production deliberately
uses, so POS-007/008 investigate a different, more constrained problem.*

**What the evidence says** (`VS docs/handoffs/IBG_POS_007A_FEASIBILITY_RESULT.md` §3):

```text
Source repo:    VS
Source ref:     docs/handoffs/IBG_POS_007A_FEASIBILITY_RESULT.md:76-95
Evidence class: PRIMARY_RESEARCH_RECORD
```

> `GovernedAcceptedOutlineEvidence` stores body-relative UV, whose `bounds_uv` is exactly
> `[0,1]x[0,1]` **by construction**. UV divides u by the bbox width and v by the bbox
> **height** — two different scalars — so it is an anisotropic map… **The aspect ratio has
> already been divided out and is not recoverable from the outline.**

This is **not a prohibition.** No governance rule forbids the prior. The aspect ratio is
*absent from the representation* — an information-theoretic property of the evidence
contract, not a policy.

And POS-007A **did not stop there. It solved it:**

> All measurement therefore happens in **isotropic width-normalized space**, restoring the
> aspect from the cited frame instance's `source_bounds`.

It then amended its own order: the fidelity gate must receive *outline **and** its cited frame
instance*, noting explicitly that this **"does not weaken the geometry-only boundary."** The
record even quantifies the stakes — Melody Maker is 2567×2561 px so distortion is 0.23% and
invisible, while a typical body 1.4–2.0× taller than wide would distort return distances by
**40–100% and could silently flip a verdict.**

**Corrected disposition.** The inherited conclusion — *"graduation cannot be presumed because
POS-007/008 solve a different problem"* — does not follow from this evidence, because the
constraint was a representational artifact that POS-007A identified and repaired inside its
own increment. Whether POS-007/008 are graduation candidates is **still open**, but it must be
argued on other grounds. This row is `UNRESOLVED`, not `BLOCKED`.

---

## 5. Graduation Step 0 — RED confirmed, cause corrected

**Inherited claim:** *Step 0 fails because `vectorizer_phase2.py` and its byte-identical spine
twin cannot import under the sandbox CI dependency set — `svgwrite` absent.*

**`svgwrite` is not absent.**

```text
Source repo:    VS
Source ref:     requirements.txt:12 ; .github/workflows/ci.yml:21
Evidence class: DIRECT_READ
```

```text
requirements.txt:12   svgwrite>=1.4.0              # SVG generation
ci.yml:21             pip install -r requirements.txt pytest numpy opencv-python-headless \
                                  ezdxf Pillow pytest-cov
```

It is declared **and** installed by sandbox CI. The stated cause is refuted.

**The import does fail, for two other reasons.** Static import surface of
`src/archaeology/vectorizer_phase2_runtime_spine.py` against the sandbox manifest:

| Import | Declared in `VS requirements.txt` |
|---|---|
| `cv2` | yes |
| `ezdxf` | yes |
| `numpy` | yes |
| `svgwrite` | **yes** |
| **`fitz`** (PyMuPDF) | **NO** |
| **`dxf_compat`** | **NO** — sibling module at `src/incubation/`, importer at `src/archaeology/` |

**Cause 1 — the dependency did not migrate with the file.** PyMuPDF *is* declared in `LTB`
(`services/api/requirements.txt:34`). The module moved from `LTB` to `VS` in the May 20
migration; its manifest entry did not follow. This is a migration-completeness defect, and it
is the more instructive of the two.

**Cause 2 — a cross-package bare import.** `import dxf_compat` resolves only if both
`src/archaeology/` and `src/incubation/` are on `sys.path`.

**One further correction: "Step 0" is not a step of this bridge.** The bridge's first gate is
*evidence validation*. An import failure sits **upstream of the bridge entirely** — it is a
precondition, not a bridge stage. Recording it as "Step 0 RED" implies the capability entered
the bridge and stalled. It has not entered.

```text
Graduation gate 1 (evidence validation): NOT REACHED
Precondition (module imports):           RED
Cause:                                   fitz/PyMuPDF undeclared in VS requirements.txt;
                                         plus cross-package bare `dxf_compat` import
Candidate repair:                        add PyMuPDF>=1.24.0 to VS requirements.txt;
                                         resolve dxf_compat by package-qualified import
Applied:                                 NO — sandbox is read-only in this lane
Authorization required:                  explicit, separate
```

---

## 6. Two histories

Per the governing rule, these are kept apart. The second is evidenced; the first is
**reconstructed from proposals and is not a decision record.**

### 6.1 Intended / proposed trajectory — `UNVERIFIED AS A DECISION`

```text
multiple rendering technologies
        ↓
AGE / adaptive selection
        ↓
knowledge / learning
        ↓
feedback across attempts
        ↓
best result for the particular input
```

This is the direction described by the three-loop / AGE material. It was **never approved**:
`LTB CLAIM` — the named architecture (`VectorizerAGE`, `AdaptiveExtractor`, `strategy_cache`,
`try_all_strategies`) appears in **zero files in either repository**, and the
`THREE_LOOP_ARCHITECTURE_REFRAMED.md` demotion of 2026-05-30 records that its "approved"
status rested on unsourced provenance.

**Displaced, not disproven.** No record anywhere evaluates the AGE direction and rejects it on
merit. Its absence is an absence of decision, not a decision.

### 6.2 Actual implemented trajectory — evidenced

```text
2026-05-11  governance turn
        ↓   MRP framework, MRP-1A enforcement, IBG capability assessment,
            VECTOR-1B "LOOP2_NOT_IMPLEMENTED"
2026-05-12  GOV-1/2/3 authority hierarchy + topology, tiered enforcement runner
        ↓
2026-05-20  production / research separation (ARCHAEOLOGY_RELOCATION, PHASE2_RELOCATION)
        ↓
            evidence contracts (GovernedAcceptedOutlineEvidence)
        ↓
            admission governance (ibg_intake_gate, check_semantic_sandbox_imports)
        ↓
            boundary-fidelity investigation (IBG_BOUNDARY_FIDELITY)
        ↓
            POS-007/008 recovery research
```

**On the May 11 causal claim.** The cluster is real and dense — 2026-05-11 carries
`c9da01bd` (MRP governance framework), `64ad3a57` (MRP-1A enforcement), `b5c51220` (IBG
capability assessment), `ccb30161` (VECTOR-1B, "LOOP2_NOT_IMPLEMENTED"), `bf3764e4` (CAM
lifecycle policy engine), with GOV-1/2/3 following on 05-12. **Correlation is established;
causation is not.** No document says "the AGE direction is constrained *because of* the
governance turn." Recorded as `TEMPORAL_COINCIDENCE_STRONG / CAUSAL_LINK_UNPROVEN`.

### 6.3 What separates them

The second trajectory produced real engineering assets — evidence contracts, admission gates,
a 14k-line production IBG, a disciplined research repo. **That does not establish it was the
correct destination for the first.** Nor does it establish the opposite. The two questions are
independent and this document does not conflate them.

---

## 7. Findings that can all be true simultaneously

Deliberately not resolved into a single verdict, because the evidence does not support one.

| Statement | Status |
|---|---|
| Custody separation is beneficial | **Supported** — clean production/research boundary, enforced by precommit, asserted from both repos |
| Original AGE trajectory | **DISPLACED, not disproven** — never approved, never built, never evaluated on merit |
| Evidence discipline | **Valuable** — POS-007A caught a 40–100% distortion that would have silently flipped verdicts |
| Commercial convergence | **NOT DEMONSTRATED** — zero graduations, no ACTIVE promotion |
| Some sandbox work non-graduatable | **Open** — the POS-006 basis for asserting this is refuted (§4) |
| Some sandbox work useful research | **Supported** — POS-007A is a substantive result on its own terms |
| Production IBG substantially more mature | **Confirmed** — 14,436 lines, four mounted routes |
| Render-portfolio problem unresolved | **UNVERIFIED here** — Lane A (DET-001) evidence, not absorbed |

---

## 8. Capability-by-capability

| Capability | Intended | Shipped | Lives | Class | Production alternative? | Graduated? |
|---|---|---|---|---|---|---|
| Body solving / completion | parametric body completor | **yes, substantial** | `LTB` | PRODUCTION | n/a — is production | n/a |
| `morphology_harvest` | corpus morphology | **yes, 4,711 L** | `LTB` | PRODUCTION | n/a | n/a |
| `arc_reconstructor` | arc parameter recovery | **yes, 1,614 L** | `LTB` | PRODUCTION | n/a | n/a |
| Boundary fidelity (POS-007/008) | governed fidelity gate | research results | `VS` | RESEARCH | partially — production isolation differs | **no** |
| `agentic_supervisor` (7-agent) | Loop 1 / AGE prototype | prototype only | `VS` | INCUBATION | **yes** — `GeometryCoachV2`, live, default-on | **no** |
| `extract_body_grid` v1–v5 | occupancy semantics | historical | `VS` | ARCHAEOLOGY | production uses other means | **no** |
| `cognitive_extractor` | semantic extraction | historical | `VS` | ARCHAEOLOGY | none | **no** |
| `vectorizer_phase2` | Phase 2 vectorization | superseded | `VS` | ARCHAEOLOGY | `CleanupMode.REFINED` | **no** — cannot import (§5) |
| AGE / adaptive lane selection | portfolio selection | **never built** | — | DISPLACED | **none** | n/a |

The last row is the one with commercial consequence: it is the only capability in the table
with **no production alternative at all**.

---

## 9. Not established

- Render-lane portfolio figures. Lane A. Not absorbed, not asserted.
- Whether POS-007/008 results *should* graduate. §4 removed the stated reason they could not;
  it did not supply a reason they should.
- Causation for the May 11 turn (§6.2).
- Whether the AGE direction was technically sound. Its absence is undecided, not refuted.
- Content equivalence of `BOTH`-state files across repos; matched by path and name, not diffed.

---

## 10. State

```text
Custody separation                 SUCCESS
Commercial convergence             NOT DEMONSTRATED
Sandbox -> production graduations  ZERO
Graduation bridge gate 1           NOT REACHED (precondition RED, cause corrected §5)
AGE / adaptive selection intent    DISPLACED, not disproven
Render-lane portfolio              UNVERIFIED IN THIS LANE (Lane A)
Production IBG                     SUBSTANTIAL OPERATIONAL IMPLEMENTATION
Inherited claims re-derived        5 of 5 — 3 confirmed, 2 refuted
Sandbox modified                   NO
DET-001                            UNTOUCHED, CONTINUES
```
