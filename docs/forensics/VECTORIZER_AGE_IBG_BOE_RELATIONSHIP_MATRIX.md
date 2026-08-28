# Vectorizer × AGE × Loops × IBG × BOE — Relationship Matrix

**Sprint:** IBG/AGE Precursor Forensic Sprint (read-only)  
**HEAD:** `2646992fc294a904438042d529b939ec6db80662`  
**Sandbox:** UNAVAILABLE — any cell that would require `vectorizer-sandbox` is `UNKNOWN` if not already decidable from `luthiers-toolbox`.

Vocabulary (one token per cell):

| Token | Meaning |
| ----- | ------- |
| `PROVEN` | Direct code or git-history coupling, with a source cited below |
| `SUPPORTED` | Multiple independent in-repo facts, not a single smoking gun |
| `ADJACENT` | Same era / shared topic; no coupling shown |
| `CONFLICTED` | Sources disagree |
| `NONE_FOUND` | Searched; no relationship in this repo |
| `UNKNOWN` | Missing evidence (typically sandbox or uncommitted artifacts) |

**PROVEN cells cite a concrete source.** Diagonal (system vs itself) is omitted conceptually; the table still fills “same-system” as `PROVEN` identity.

IBG = Instrument Body Generator (April). BOE = Body Outline Editor.

---

## Matrix

| System | Vectorizer | AGE | Loop 1 | Loop 2 | Loop 3 | IBG | BOE |
| ------ | ---------- | --- | ------ | ------ | ------ | --- | --- |
| **Vectorizer** | PROVEN | SUPPORTED | CONFLICTED | NONE_FOUND | PROVEN | SUPPORTED | ADJACENT |
| **AGE** | SUPPORTED | PROVEN | SUPPORTED | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND |
| **Loop 1** | CONFLICTED | SUPPORTED | PROVEN | ADJACENT | ADJACENT | NONE_FOUND | NONE_FOUND |
| **Loop 2** | NONE_FOUND | NONE_FOUND | ADJACENT | PROVEN | ADJACENT | NONE_FOUND | NONE_FOUND |
| **Loop 3** | PROVEN | NONE_FOUND | ADJACENT | ADJACENT | PROVEN | NONE_FOUND | NONE_FOUND |
| **IBG** | SUPPORTED | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | PROVEN | SUPPORTED |
| **BOE** | ADJACENT | NONE_FOUND | NONE_FOUND | NONE_FOUND | NONE_FOUND | SUPPORTED | PROVEN |

Symmetric by construction except where noted in the cell notes (none).

---

## Cell notes (every non-identity claim)

### Vectorizer — AGE = `SUPPORTED`

- April `6075db47` CLAUDE.md places `VectorizerAGE` in the vectorizer pipeline (Claude API over extraction quality).
- **Not PROVEN:** no Python `VectorizerAGE`, no call sites.
- Sandbox embodiment: `UNKNOWN`.

### Vectorizer — Loop 1 = `CONFLICTED`

- April 2 doc: Loop 1 not implemented; sketch `ValidatedExtractor`.
- April 3 code: scale gate only (`bf5b2d48`).
- March 15 code: GeometryCoachV2 retry (not named Loop 1).
- April 19 doc: “Loop 1 is fully implemented” (`2b94549c`).
- May 30 doc: named Loop 1 never built; keep the gate/coach as themselves.

### Vectorizer — Loop 2 = `NONE_FOUND`

- No `AdaptiveExtractor` / `strategy_cache` in `*.py`.
- May 11 audit: never built (`ccb30161`).

### Vectorizer — Loop 3 = `PROVEN`

- Source: `1ce27294` / `6075db47` `vectorizer_phase3.py` `class FeedbackSystem` and `class TrainingDataCollector`; April 2 text names those exact classes. Default off.

### Vectorizer — IBG = `SUPPORTED`

- IBG docstring and `complete_from_dxf` treat input as “partial vectorizer DXF” (`ca2b2347`).
- **Not PROVEN as import/copy:** no IBG `import` of vectorizer packages; `fit_circle_3pts` is not the same function body.
- Classification vs §8 vocabulary: **DATA CONSUMER**, not IMPORT/COPY.

### Vectorizer — BOE = `ADJACENT`

- Both appear in April 2026 lutherie tooling; BOE HTML (`4f3ee9e2`) has no vectorizer import. Later product diagrams place Blueprint Reader → DXF → IBG/BOE. That is document adjacency, not April code coupling.

### AGE — Loop 1 = `SUPPORTED`

- Single contemporaneous placement: “decision layer above Loop 1” (`6075db47`). One document, explicit. Not code.

### AGE — Loop 2 / Loop 3 = `NONE_FOUND`

- April sketches do not put AGE on Loop 2 or Loop 3.

### AGE — IBG = `NONE_FOUND`

- Special test H0 stands. No shared symbols, commits, or April docs linking them. Later `ccb30161` even asks whether Loop 2 moved into “Image Body Generator” and answers **no**.

### AGE — BOE = `NONE_FOUND`

- No references.

### Loop 1 / 2 / 3 — IBG = `NONE_FOUND`

- IBG Dev Order and April IBG code do not mention loops. May `IBG_ROLE_DEFINITION.md` *forbids* Loop 2 inside IBG — that is later governance, consistent with absence, not April coupling.

### Loop * — BOE = `NONE_FOUND`

- May reframing says loops must not bypass BOE authority (`THREE_LOOP_ARCHITECTURE_REFRAMED.md`). That is later constraint language, not an April implementation link. Matrix stays `NONE_FOUND` for April coupling; later doc is recorded in the drift ledger.

### IBG — BOE = `SUPPORTED`

- Independent origins: BOE `4f3ee9e2` 2026-04-05; IBG `ca2b2347` 2026-04-17.
- Integration: `c9ebf8a8` router docstring “Body Outline Editor ↔ IBG”; OpenAPI `118e7850`; BOE client `/api/body` `70a0d3ee` 2026-05-12.
- **Not identity.** Not “IBG became BOE.”

---

## Extra: Body Solver (not a matrix column; required by Dev Order §9)

| Relation | Ruling | Source |
| -------- | ------ | ------ |
| Body Solver vs IBG | **API wrapper**, not module rename | `c9ebf8a8` creates `body_solver_router.py` importing `InstrumentBodyGenerator`; tags `["Body Solver"]` |
| Body Solver vs “IBG API” rename | **CONFLICTED** | Commit `118e7850` *says* “renamed from IBG API per ADR”. No ADR file. No prior OpenAPI titled IBG. Yaml already titled Body Solver; text says IBG has no direct endpoint |
| Body Solver vs BOE | **Integration boundary** | Same router docstring; BOE is the named UI client |

What “renamed from IBG API per ADR” **actually** can be shown to have named: the **HTTP documentation/product label** for the wrapper around IBG (`docs/api/body_solver_openapi.yaml`), not a git mv of `instrument_body_generator.py`, not a replacement of IBG by BOE.

---

## Diagram (question marks preserved)

```text
     CANONICAL VECTOR TECHNOLOGY
     (blueprint-import / photo-vectorizer)
                 │
                 │ DATA CONSUMER (DXF files)
                 │ SUPPORTED — not IMPORT
                 ▼
              IBG  Instrument Body Generator
              (ca2b2347 / 471bc902)
                 │
                 │ HTTP WRAPPER  PROVEN  c9ebf8a8
                 ▼
           Body Solver API
                 │
                 │ later client  SUPPORTED  70a0d3ee
                 ▼
                BOE  (existed first: 4f3ee9e2)

     AGE + three-loop sketches (6075db47)
                 │
                 │ intended: AGE above Loop 1 on VECTORIZER
                 │ SUPPORTED as documentation
                 │ NONE_FOUND as code in this repo
                 │ UNKNOWN in vectorizer-sandbox
                 ▼
              (no arrow to IBG)  NONE_FOUND
```

---

## Section 8 classifications (vectorizer implementations)

| Pair | Class |
| ---- | ----- |
| IBG ↔ blueprint `vectorizer_phase3.py` | DATA CONSUMER + DOCUMENT REFERENCE |
| IBG ↔ `services/photo-vectorizer/` | NO CONNECTION FOUND (plus one mixed-commit ADJACENT file edit `40d5e3f9`) |
| AGE sketch ↔ vectorizer | DOCUMENT REFERENCE (intended IMPORT never performed) |
| GeometryCoach ↔ AGE | CONCEPTUAL SIMILARITY only (retry vs LLM) |
