# Instrument Body Generator (IBG) — Role Definition

**Status:** ACTIVE GOVERNANCE  
**Effective:** 2026-05-11 — **amended 2026-08-29**

---

> ## AMENDMENT — 2026-08-29 (descriptive-capture correction)
>
> **APPROVED BY:** Ross (repository owner), 2026-08-29, by direct instruction in session.
>
> **Defect corrected:** *descriptive capture*. On 2026-05-11 three documents were written in
> 106 minutes: `VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md` (`ccb30161`, 10:50) reported findings;
> `IBG_FUNCTIONAL_CAPABILITY_ASSESSMENT` (`b5c51220`, 11:54) restated them as status; this
> document (`c9da01bd`, 12:36) restated them a third time as `NEVER`. Observation became
> status became prohibition. **No decision was ever recorded barring the capability.** The
> prohibition arose from the imperative register of a canonical document, not from an argument.
>
> **Diagnostic signature:** a prohibition whose reason column restates the prohibition. The
> Math Authority section below cites Sevy (*American Lutherie* #58), Mottola (#78), and a
> plus/minus 0.01 inch tolerance. The four corrected rows cited nothing. The document
> convicted itself by contrast.
>
> **Rule applied:** permanent prohibition -> present-tense description. The prohibition table
> is split so that sourced boundaries and present-state facts no longer share one header.
>
> **Changes to the 2026-05-11 text:**
>
> | Line | Was | Now |
> |---|---|---|
> | 1 | `# Image Body Generator` | `# Instrument Body Generator` (owner namespace ruling) |
> | 32 | `## What IBG Does NOT Do` | split into two sections |
> | 37 | `Strategy caching (Loop 2) \| NEVER \| Not a learning system` | `Not currently implemented` |
> | 38 | `ML classification \| NEVER \| Uses deterministic lutherie math` | scoped to the math solver |
> | 64 | `No feedback loop exists upstream.` | `As currently implemented...` |
> | 89 | `No learning systems.` | `Learning systems: not currently implemented` |
>
> **What did NOT change:** Image processing and Photo input remain `NEVER`. IBG math remains
> `LOCKED` under Sevy/Mottola with its change-control procedure intact. Protected interfaces
> stand. **IBG still renders nothing.**
>
> **Namespace.** `IBG = Instrument Body Generator`. The April source is authoritative:
> `instrument_body_generator.py`, class `InstrumentBodyGenerator`, docstring dated 2026-04-16.
> The first git occurrence of "Image Body Generator" is `ccb30161` (2026-05-11) — 24 days
> after the code, with no `git mv`, no class rename, and no code change. Documents dated
> 2026-05-11 or later using the other expansion refer to this same system; do not infer an
> image-processing capability from them.
>
> **Known defect left uncorrected.** The Canonical Role block states an input of
> "82-88% complete". That figure originated as a shop note from a test during the March 2026
> sprint, not as a specification or a measured ceiling. It is **out of scope for this
> amendment** and needs its own decision.
>
> **This amendment authorizes nothing.** `VectorizerAGE`, `AdaptiveExtractor`,
> `strategy_cache`, and `try_all_strategies` return zero hits in both `luthiers-toolbox` and
> `vectorizer-sandbox`. Nothing here asserts a selector exists or that one is owed. It removes
> a governance bar that was never deliberately raised. Implementation requires its own Dev Order.

---

## Canonical Role

IBG is a **parametric geometry completor**, not an image processor.

```
Input: Partial DXF outline (82-88% complete)
Process: Landmark extraction → Constraint solving → Outline generation
Output: Solved body model (100% complete)
```

---

## What IBG Does

| Function | Method | Status |
|----------|--------|--------|
| Complete partial DXF from vectorizer | `complete_from_dxf()` | PRODUCTION |
| Complete from user landmarks | `complete_from_landmarks()` | PRODUCTION |
| Generate from family defaults | `generate_from_defaults()` | PRODUCTION |
| Export solved model to DXF | `save_dxf()` | PRODUCTION |
| Calculate side heights | `solve_side_height()` | PRODUCTION |

---

## Out of Scope (permanent)

These are boundaries on what IBG *is*. Changing one requires an explicit decision recorded
in this document.

| Capability | Status | Reason |
|------------|--------|--------|
| Image processing | NEVER | Works on DXF geometry only |
| Photo input | NEVER | Requires vectorizer preprocessing |

---

## Not Currently Implemented

Present-state descriptions, not prohibitions. A row here records what IBG does not do today.
It does not forbid future development, which proceeds under the `EVOLUTIONARY` governance of
the IBG Morphology Layer and the Mandatory Requirements in
`MORPHOLOGY_RECONSTRUCTION_PLATFORM.md` (feature flags, regression corpus, audit logs,
rollback paths, documented confidence).

| Capability | Status | Note |
|------------|--------|------|
| Strategy caching (Loop 2) | Not currently implemented | IBG presently uses deterministic solving |
| ML classification | Not used in the IBG math solver | The solver uses deterministic lutherie math — see Math Authority |

---

## Math Authority

IBG math is LOCKED. Source references:

- **Jon Sevy** — "Calculating Arc Parameters," American Lutherie #58
- **R. Mottola** — "Calculating Side Contours," American Lutherie #78

Verification: ±0.01 inch tolerance against published spreadsheet values.

---

## Position in Pipeline

```
Blueprint Reader (upstream)
  → Partial DXF
  → IBG (this system)
  → Solved Body Model
  → CAM pipeline (downstream)
```

As currently implemented, IBG consumes vectorizer output without an upstream feedback loop.
This describes the present wiring, not a constraint on future work.

---

## Protected Interfaces

| Interface | Protection |
|-----------|------------|
| `SolvedBodyModel` schema | LOCKED |
| `BodyContourSolver` math | LOCKED |
| API response contract | LOCKED |
| DXF layer naming | LOCKED |

---

## Governance Authority

Changes to IBG core math require:
1. Published lutherie reference
2. Verification against known instruments
3. Regression test passage
4. Explicit approval

---

*IBG role definition. No image processing. Learning systems: not currently implemented — see "Not Currently Implemented".*
