# Instrument Body Generator (IBG) — Role Definition

**Status:** ACTIVE GOVERNANCE
**Effective:** 2026-05-11 — **amended 2026-08-29**

**APPROVED BY:** Ross (repository owner), 2026-08-29, by direct instruction in session.

---

> ## NAMESPACE CORRECTION (2026-08-29)
>
> This document was previously titled **"Image Body Generator (IBG)"**. That expansion is
> **not canonical and never was**. The owner has identified it as his own conflation and
> ruled the canonical namespace:
>
> ```text
> IBG = Instrument Body Generator
> ```
>
> Supporting record: the April source of truth. `instrument_body_generator.py` module
> docstring — *"Instrument Body Generator — Complete Body from Partial Vectorizer Output,
> Date: 2026-04-16, Sprint: 9"*. The production path is
> `services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py`; the class is
> `InstrumentBodyGenerator`. The first git occurrence of the string "Image Body Generator" is
> `ccb30161` (2026-05-11) — twenty-four days after the code, with **no `git mv`, no class
> rename, and no code change accompanying it**. It was a documentation drift, not a rename.
>
> The prior title also contradicted this document's own opening line, which states that IBG is
> not an image processor.
>
> **Reading rule:** "Image Body Generator" appearing in any document dated 2026-05-11 or later
> refers to this same system. Do not infer an image-processing capability from it, and do not
> propagate the expansion.

---

> ## AMENDMENT RECORD (2026-08-29)
>
> **What changed:** two prohibition rows and one pipeline-position statement. Nothing else.
>
> **Why:** the 2026-05-11 text forbade *strategy caching (Loop 2)* and declared *"no feedback
> loop exists upstream."* Read literally — and it has been read literally — those two lines
> prohibit the render-lane selector the owner has been directing toward since April. Engineers
> declining that work have been correctly following this document. The prohibition was
> structural, not technical, and it is removed here by owner decision.
>
> **What did not change:** the solver's math, its determinism, its locked interfaces, and its
> exclusion from image processing. IBG renders nothing. That remains true after this amendment
> and is restated in §3.
>
> **What this amendment is not:** it is not an assertion that a selector exists, not a claim
> that one is owed, and not authorization to build one. It removes a governance bar. Building
> requires its own Dev Order.
>
> The `APPROVED BY` line above is the decision record. A future session finding this document
> marked ACTIVE should check that line rather than re-derive authority from citation count.

---

## 1. Canonical role

IBG is a **parametric geometry completor**, not an image processor.

```text
Input:   Partial DXF outline, or landmark points
Process: Landmark extraction → constraint solving → outline generation
Output:  Solved body model (closed outline, side heights, zone radii, confidence)
```

The system is named for what it generates — an instrument body — not for what it consumes.

---

## 2. What IBG does

| Function | Method | Status |
|----------|--------|--------|
| Complete partial DXF from vectorizer | `complete_from_dxf()` | PRODUCTION |
| Complete from user landmarks | `complete_from_landmarks()` | PRODUCTION |
| Generate from family defaults | `generate_from_defaults()` | PRODUCTION |
| Export solved model to DXF | `save_dxf()` | PRODUCTION |
| Calculate side heights | `solve_side_height()` | PRODUCTION |

---

## 3. What IBG does NOT do

| Capability | Status | Reason |
|------------|--------|--------|
| Image processing | **NEVER** | Works on DXF geometry and landmarks only |
| Photo / raster input | **NEVER** | Requires vectorizer preprocessing |
| Non-deterministic math in the solver | **NEVER** | `BodyContourSolver` is published lutherie math; see §5 |
| Silent canonical authority | **NEVER** | Semantic discovery is permitted; ontology authority is not (see §7) |

These four are unchanged in substance and are not open for amendment without a separate
owner decision.

**Removed by the 2026-08-29 amendment:**

| Former row | Disposition |
|---|---|
| *Strategy caching (Loop 2) — NEVER — Not a learning system* | **REPLACED** by §4 |
| *ML classification — NEVER — Uses deterministic lutherie math* | **NARROWED** to §3 row 3: the prohibition applies to the solver, not to evaluation |

---

## 4. Evaluation and selection scope (new, 2026-08-29)

The repository holds several render technologies, none of which satisfies quality, file size,
and text fidelity simultaneously. Selecting and composing among them requires a component that
knows what an instrument body is. IBG is the only production component that holds that
knowledge.

IBG **may** therefore:

| Capability | Scope | Constraint |
|---|---|---|
| Evaluate a candidate outline against instrument-domain knowledge | `INSTRUMENT_SPECS`, `FAMILY_DEFAULTS`, landmark constraints, expected dimensions | Returns a judgement, never a mutation of the input |
| Evaluate **several** candidate outlines from different render lanes in one call | A portfolio, not a single result | Same constraint |
| Return a selection and a stated reason to an upstream caller | Advisory response only | The caller decides; IBG does not invoke a renderer |
| Persist which lane succeeded against which document signature | The Loop 2 strategy cache | Cache is advisory; a cache hit never bypasses evaluation |
| Use non-deterministic reasoning **in the evaluator** | Evaluation and selection only | The solver stays deterministic (§3 row 3); an evaluator's verdict may not alter solver output |

Superseded statement: *"IBG is a one-way consumer of vectorizer output. No feedback loop
exists upstream."*

Replacement:

```text
IBG is a downstream consumer of render output AND an advisory evaluator of it.
An upstream feedback path is permitted. It is advisory in both directions:
IBG does not select on the caller's behalf, and the caller does not gain
authority over IBG's math by supplying candidates.
```

---

## 5. Math authority (unchanged)

IBG math is **LOCKED**. Source references:

- **Jon Sevy** — "Calculating Arc Parameters," *American Lutherie* #58
- **R. Mottola** — "Calculating Side Contours," *American Lutherie* #78

Verification: ±0.01 inch tolerance against published spreadsheet values.

Changes to IBG core math require: a published lutherie reference, verification against known
instruments, regression test passage, and explicit owner approval. §4 does not create an
exception to this.

---

## 6. Position in pipeline

```text
Render lanes (upstream, plural)
    │  candidate outlines
    ▼
IBG evaluator ──────── advisory selection + reason ────► caller
    │  selected outline
    ▼
IBG solver  (deterministic, locked)
    │  solved body model
    ▼
CAM pipeline (downstream)
```

The evaluator and the solver are separate concerns inside one package. The solver's contract is
unchanged by the presence of the evaluator, and the solver must remain callable without it.

---

## 7. Protected interfaces (unchanged)

| Interface | Protection |
|-----------|------------|
| `SolvedBodyModel` schema | LOCKED |
| `BodyContourSolver` math | LOCKED |
| API response contract | LOCKED |
| DXF layer naming | LOCKED |

The constitutional intake layer (`BodyEvidenceCandidate`, `IBGIntakeGate`, DEV ORDER 1D) is
unaffected by this amendment. Its principle stands: *IBG semantic discovery is permitted; IBG
ontology authority is not.* An evaluator verdict is discovery. It does not populate IBG memory,
does not become canonical, and does not bypass the intake gate.

---

## 8. Open items created by this amendment

1. The selector itself is **not authorized here** and does not exist. `VectorizerAGE`,
   `AdaptiveExtractor`, `strategy_cache`, and `try_all_strategies` return zero hits in both
   `luthiers-toolbox` and `vectorizer-sandbox`. Building requires a Dev Order.
2. A selector needs a score over lanes. `vectorizer-sandbox/src/evaluation/text_geometry_eval/`
   specifies one (geometry score, text legibility) and does not currently run.
3. Documents that cite the removed rows as authority need review — notably any that inherit
   "no upstream feedback" as a constraint on loop work.

---

*IBG = Instrument Body Generator. Deterministic solver; advisory evaluator. No image processing.*
