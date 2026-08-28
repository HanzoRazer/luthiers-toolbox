# IBG / AGE / Three-Loop Semantic Drift Ledger

**Sprint:** IBG/AGE Precursor Forensic Sprint (read-only)  
A terminology change is **not** an implementation change unless code evidence shows it.

Transition classes: `DOCUMENTED_RENAME` · `ROLE_EXPANSION` · `ROLE_CONTRACTION` · `CONFLATION` · `SEMANTIC_DRIFT` · `UNRESOLVED`

April IBG expansion remains **Instrument Body Generator** unless quoting later text.

---

## IBG

### 1. Instrument Body Generator (origin)

| Field | Value |
| ----- | ----- |
| When | 2026-04-16 (docstrings / Dev Order date); git 2026-04-17 `ca2b2347` |
| What it meant | Parametric completor: partial DXF + instrument class → closed outline, side heights, zone radii, confidence |
| Code | `class InstrumentBodyGenerator`; `complete_from_dxf` |
| Classification of this node | Origin, not a transition |

### 2. Instrument Body Generator → “Image Body Generator”

| Field | Value |
| ----- | ----- |
| When | First string `ccb30161` 2026-05-11 10:50 (`VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md`); title form `b5c51220` 11:54; governance `c9da01bd` 12:36 `IBG_ROLE_DEFINITION.md` |
| Code change? | **No.** Same solver; assessment even says “Despite the name suggesting image processing, it is actually a parametric geometry solver.” |
| Class | `SEMANTIC_DRIFT` + `CONFLATION` (acronym IBG kept; expansion swapped). **Not** `DOCUMENTED_RENAME` of a module (no `git mv` / no class rename). |
| Counter | April headers still “Instrument Body Generator.” Production path still `instrument_body_generator.py`. |

### 3. IBG → Body Solver

| Field | Value |
| ----- | ----- |
| When | HTTP: `c9ebf8a8` 2026-04-18; OpenAPI: `118e7850` 2026-04-22 |
| What changed | A FastAPI wrapper named **Body Solver** was added in front of IBG. IBG remained the library. Yaml: “IBG is a separate geometry correction library… no direct API endpoint.” |
| Commit-message claim | “renamed from IBG API per ADR” |
| ADR file | **NOT_FOUND** |
| Prior IBG OpenAPI | **NOT_FOUND** |
| Class | **API naming / wrapper** = `ROLE_EXPANSION` (IBG gains an HTTP façade). The phrase “renamed from IBG API” = `UNRESOLVED` as a documented rename (claim without artifact) and `CONFLATION` if read as IBG the library becoming Body Solver the product. |
| Code change? | New router; IBG class not renamed. |

### 4. IBG → BOE (alleged absorption)

| Field | Value |
| ----- | ----- |
| April fact | BOE HTML `4f3ee9e2` 2026-04-05 **precedes** IBG. Separate tool. |
| Later | Router “BOE ↔ IBG”; BOE calls `/api/body` (`70a0d3ee`); `BOE_IBG_FAMILY_CONFLATION.md` (2026-05-28) treats two systems with overlapping outline artifacts |
| Class | Integration boundary, not rename. Family-conflation doc is later governance. **Not** “IBG became BOE.” |
| Code change? | Client wiring, not a merge of implementations in April. |

### 5. IBG role: completor → “provenance-bearing evidence” / not autonomous

| Field | Value |
| ----- | ----- |
| When | `docs/research/IBG_LINEAGE_MAP.md` / `IBG_RUNTIME_POSITION.md` 2026-05-20 |
| April fact | Dev Order and class docs: complete the body mathematically; paid-tier product |
| Class | `ROLE_EXPANSION` / `SEMANTIC_DRIFT` in **research/governance** (constitutional evidence-bridge language). April code was already a solver with confidence scores, not an agent. Do not claim the May prose changed `complete_from_dxf`. |

### 6. Incubation window widened to March

| Field | Value |
| ----- | ----- |
| When | `SANDBOX_FOLDER_REMEDIATION_HANDOFF.md` 2026-05-20 “circa March-April 2026” |
| April git | First IBG file 2026-04-17 |
| Class | `SEMANTIC_DRIFT` in later hygiene docs. `HISTORY_PROVEN` does not support March IBG code in this repo. |

---

## AGE

### 1. Agentic Guidance Engine (origin)

| Field | Value |
| ----- | ----- |
| When | `6075db47` 2026-04-02 CLAUDE.md |
| Meaning | `VectorizerAGE`: Claude API evaluates extraction, picks strategy, silent fallback; **above Loop 1**; patterned (claimed) on tap_tone_pi |
| Code | **None** in this repo |

### 2. AGE → “must be built / do not drop”

| Field | Value |
| ----- | ----- |
| When | Same April 2 block, “Rules for Future Sessions” item 3 |
| Class | `ROLE_EXPANSION` of **obligation language** in docs, not code |

### 3. AGE → Analyzer Guidance Engine (tap-tone contract)

| Field | Value |
| ----- | ----- |
| When | `docs/handoffs/imports/.../AGE_CONTRACT.md` 2026-05-23 |
| Meaning | Different expansion: **Analyzer** Guidance Engine; advisory; must not modify measurements |
| Class | `CONFLATION` if treated as the same AGE as VectorizerAGE. April vectorizer text *invited* that conflation by citing tap_tone_pi. May 30 retracts the port analogy. |
| Code change in luthiers-toolbox? | No |

### 4. AGE → experimental / sandboxed / never approved

| Field | Value |
| ----- | ----- |
| When | `8fad48d9` 2026-05-30 and conflation packet |
| Meaning | April “APPROVED DESIGN” framing declared false; embodiment claimed in sandbox `agentic_supervisor.py` |
| Class | Later governance correction (`ROLE_CONTRACTION` of authority). Does not prove April authors did not *write* “approved.” It disputes whether that writing was a valid approval. |
| Sandbox file | `UNKNOWN` this run |

### 5. AGE → IBG

| Field | Value |
| ----- | ----- |
| Transition | **Does not occur** |
| Class | n/a. H0 stands. |

---

## Three-loop

### 1. April definition (`6075db47`)

| Loop | April meaning |
| ---- | ------------- |
| Loop 1 | Intra-frame validate + retry before export (`ValidatedExtractor`) |
| Loop 2 | Cross-image `strategy_cache` (`AdaptiveExtractor`) |
| Loop 3 | User correction → existing `FeedbackSystem` / `TrainingDataCollector` |

Status in the same document: **not implemented** (Loop 3: classes exist, never called). AGE above Loop 1, also not built. Immediate code target: scale gate.

### 2. April 3 code vs April 2 doc

| Field | Value |
| ----- | ----- |
| Event | `bf5b2d48` implements `validate_scale_before_export` |
| Class | Implementation of **one listed check**, not Loop 1 as defined. If later prose calls this “Loop 1,” that is `CONFLATION`. |

### 3. April 19 handoff (`2b94549c`)

| Field | Value |
| ----- | ----- |
| Claim | “Loop 1 is fully implemented and working in the photo pipeline. Loops 2 and 3 are implemented but disabled.” (body then says Loop 2 is design only — internally conflicted) |
| Class | `CONFLATION` + `SEMANTIC_DRIFT`: organically built coach/gate/feedback **relabeled** as the named architecture. |
| Code change? | No, documentation only. |

### 4. May 11 governance (`THREE_LOOP_ARCHITECTURE_REFRAMED.md` via `c9da01bd`)

| Field | Value |
| ----- | ----- |
| Claim | Still describes the three loops; AGE above Loop 1; Loop 1 status PARTIAL (scale only); adds **BOE authority** constraint (“No loop may bypass BOE”) |
| Class | `ROLE_EXPANSION` of the loop system into MRP/BOE governance. Not an April BOE relationship. |
| Later | Demoted 2026-05-30 (`SUPERSEDED`). |

### 5. May 30 conflation removal (`8fad48d9`)

| Field | Value |
| ----- | ----- |
| Claim | Named three-loop/AGE never approved, never implemented; sandbox-owned; keep scale gate; do not treat coach as Loop 1 proof |
| Class | Governance correction. **Preserves disagreement** with April 2 “APPROVED DESIGN” wording rather than editing history out of `6075db47` (the commit still exists). |

### 6. Three-loop governed IBG?

| Field | Value |
| ----- | ----- |
| April | **No** (IBG Dev Order silent on loops) |
| May IBG_ROLE | IBG must **never** do Loop 2 strategy caching |
| Class | Later boundary-setting, not evidence that loops ran inside IBG |

---

## CLAUDE.md status line (vectorizer architecture block)

| Date | Commit | Status phrase |
| ---- | ------ | ------------- |
| 2026-04-02 | `6075db47` | `APPROVED DESIGN — awaiting implementation` |
| 2026-05-30 | `8fad48d9` | Experimental, sandboxed, not approved (current runtime instructions) |

This is a **documentation status** change, not a code regression of AGE (AGE had no code).

---

## Summary of transitions (no silent code claims)

```text
IBG:
  Instrument Body Generator     (Apr 16–17 code)
        ↓ SEMANTIC_DRIFT / CONFLATION (docs only, May 11)
  "Image Body Generator"
        ↓ ROLE_EXPANSION (HTTP wrapper Apr 18; not a library rename)
  Body Solver API
        ↓ NOT A RENAME (BOE pre-existed; later client)
  BOE  (separate)

AGE:
  Agentic Guidance Engine       (Apr 2 docs, no code)
        ↓ CONFLATION risk with tap-tone Analyzer Guidance Engine
        ↓ ROLE_CONTRACTION of approval (May 30)
  experimental / sandbox / UNKNOWN embodiment

Three-loop:
  April definition              (docs; classes unbuilt except Loop 3 scaffolding)
        ↓ CONFLATION (Apr 19 relabel of coach/gate)
  May MRP interpretation        (BOE constraints)
        ↓ ROLE_CONTRACTION
  August/May-30 governance      (experimental, not a yardstick for IBG)
```
