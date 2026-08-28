# Three-Loop Architecture — Forensic Reconstruction

**Sprint:** IBG/AGE Precursor Forensic Sprint (read-only)  
**Contemporaneous source of record for April definitions:** commit `6075db47ec23528022e6fb3b60a51caf18dd1c10` (2026-04-02) adding the block to `CLAUDE.md`.

Later documents (`FEEDBACK_LOOP_SYSTEM_HANDOFF.md` 2026-04-19, `THREE_LOOP_ARCHITECTURE_REFRAMED.md` 2026-05-11, conflation removal 2026-05-30) are **reinterpretations**. They are quoted as later claims, not used to fill April gaps.

`vectorizer-sandbox` is **UNAVAILABLE**. Claims that the “real embodiment” is `src/incubation/agentic_supervisor.py` remain `UNKNOWN`.

---

## LOOP 1

**Contemporaneous definition** (`6075db47` CLAUDE.md):

> Loop 1 — Intra-Frame Validation (within one run)  
> After extraction, BEFORE export, validate the result is plausible.  
> If validation fails, retry with a different strategy automatically.  
> Do NOT export garbage — fail loudly and try again.

Sketch class: `ValidatedExtractor.extract_with_self_check`.

Checks listed: reasonable size, continuous boundary, no spikes, aspect ratio, scale — all vs instrument spec JSON. Fallback `strategy='fallback'`. Examples: cuatro 524×951mm vs spec ~260×375mm; Explorer 302×419mm vs spec 460×475mm.

**Implementation evidence in this repo:**

| Artifact | Date | Match to April sketch? |
| -------- | ---- | ---------------------- |
| `class ValidatedExtractor` | — | **NONE** (`git log -S 'class ValidatedExtractor' -- '*.py'` empty) |
| `validate_scale_before_export` `bf5b2d48` 2026-04-03 | Next morning | **Partial:** scale plausibility + correction only. Commit says “as specified in CLAUDE.md”. Not the five-check / fallback-strategy class. |
| GeometryCoachV2 `50123379` 2026-03-15 | Before the doc | **Behavioral similarity:** intra-run retry with profiles, score gate. Not named Loop 1. No LLM. |
| `2b94549c` 2026-04-19 handoff | +17 days | **Later claim:** “Loop 1 is fully implemented and working in the photo pipeline.” Retrospective label. |

**Input (April doc):** one extraction result + optional `spec_name` / image.  
**Output (April doc):** accepted result or fallback re-extract.  
**Persistent state:** none specified for Loop 1 (in-run only).  
**Agentic involvement (April doc):** none *inside* Loop 1; AGE is described separately as sitting above it.  
**Known status:** named class **not implemented**. Scale gate **was** implemented 2026-04-03. Coach retry **pre-existed** and was later *called* Loop 1.  
**Unknowns:** whether Ross’s sessions equated GeometryCoach with Loop 1 in April (no extra-repo chat used). Whether sandbox later implemented `ValidatedExtractor` (`UNKNOWN`).

---

## LOOP 2

**Contemporaneous definition:**

> Loop 2 — Cross-Image Learning (across runs)  
> Cache which extraction strategy worked for which image signature.  
> When a similar image arrives, start with the strategy that worked.

Sketch class: `AdaptiveExtractor` with `strategy_cache: image_signature → winning_strategy`, `try_all_strategies`, `pick_best`.

**Implementation evidence:**

| Artifact | Result |
| -------- | ------ |
| `class AdaptiveExtractor` / `strategy_cache` / `try_all_strategies` in `*.py` | **NONE** (`git log -S` empty) |
| `ccb30161` 2026-05-11 VECTOR-1B audit | Later claim: Loop 2 never built; **not relocated to Image Body Generator** |

**Input:** image + spec; image signature.  
**Output:** chosen strategy + cached winner.  
**Persistent state (April doc):** in-process `self.strategy_cache` dict — **no durability specified**.  
**Agentic involvement:** none in the sketch (heuristic pick_best).  
**Known status:** **NOT IMPLEMENTED** in this repository.  
**Unknowns:** sandbox copy (`UNKNOWN`).

---

## LOOP 3

**Contemporaneous definition:**

> Loop 3 — User Correction Retraining  
> When a user corrects a bad DXF, that correction is ground truth.  
> Feed it back into the classifier. The FeedbackSystem and TrainingDataCollector already exist in the code but are NEVER CALLED.

**Implementation evidence:**

| Artifact | Result |
| -------- | ------ |
| `class FeedbackSystem` / `class TrainingDataCollector` | **CODE_PROVEN** in `vectorizer_phase3.py` since `1ce27294` 2026-03-04 |
| Wiring on correction | April 2 text: never called. At `6075db47`, constructor uses `enable_feedback: bool = False` and `self.feedback = FeedbackSystem(...) if enable_feedback else None` |
| `train_classifier` live path | Not established as on in April (later handoffs: dormant) |

**Input:** user-corrected DXF (ground truth).  
**Output:** training update to classifier (intended).  
**Persistent state:** feedback directory (when enabled).  
**Agentic involvement:** none in the April sketch (supervised retrain).  
**Known status:** scaffolding **exists**; **not wired** in the default path.  
**Unknowns:** any production enablement after the window (out of scope unless it changes April meaning — it does not).

---

## Relationship to extraction (April)

All three loops are defined as operating on the **blueprint/photo vectorizer** (`vectorizer_phase3.py` named as the open-loop system). They are **not** defined as IBG loops. IBG’s April Dev Order never mentions Loop 1/2/3.

Feedback direction (April):

```text
extract → (Loop 1 validate/retry) → export
         ↑ AGE (intended) chooses strategy
across runs: Loop 2 cache
after user edit: Loop 3 retrain classifier
```

IBG sits **downstream of a DXF file**, mathematically completing gaps. That is not a loop over extraction strategy.

---

## AGENTIC LAYER

**Proven purpose (April `6075db47`):**

> The AGE pattern from tap_tone_pi … belongs in the vectorizer pipeline as the decision layer **above Loop 1**.  
> Instead of heuristic strategy selection, the AGE evaluates extraction quality using Claude API and selects the next strategy with reasoning.

Sketch: `class VectorizerAGE` with `evaluate_extraction` → Claude JSON `{plausible, strategy, reason}`; silent fallback to `_heuristic_evaluation`.

Commit message: “AGE integration requested and dropped from scope in prior sessions.” Body: “AGE integration is required, not optional.” Implementation priority **item 4 of 5** (after scale gate, Loop 1, Loop 2).

**Proven implementation in this repo:** **NONE.** `git log --all -S 'class VectorizerAGE' -- '*.py'` empty. No IBG coupling.

**Candidate placement(s) — April text only; this sprint does not choose:**

| Placement | Evidence | Status |
| --------- | -------- | ------ |
| AGE above Loop 1 | Explicit in `6075db47` (“decision layer above Loop 1”; priority list “wire VectorizerAGE above Loop 1”) | **DOC_PROVEN intent** |
| AGE before Loop 1 | Not stated | No April evidence |
| AGE within Loop 1 | Sketch is a separate class evaluating *after* extraction, like Loop 1’s moment in the pipeline | **SUPPORTED_INFERENCE** that it occupies the same *when* as Loop 1, as a decision layer rather than the heuristic checks |
| AGE between Loop 1 and Loop 2 | Not stated | No April evidence |
| AGE above Loop 2 | Not stated; Loop 2 is a cache | No April evidence |
| AGE across multiple loops | Not stated | No April evidence |
| Placement deliberately unresolved | April text is specific (above Loop 1) | **Not unresolved in the April document.** Later governance demotes the whole design (`8fad48d9`). |

**tap_tone_pi reference:** April text cites `tap_tone_pi/tap_tone/analyzer_guidance_engine.py`. May 23 `AGE_CONTRACT.md` (imported handoff) defines **Analyzer Guidance Engine** in tap-tone as advisory/read-only. May 30 conflation packet retracts the “port AGE from tap_tone_pi” analogy. Those are **later** statements. This sprint does not verify tap_tone_pi (out of repo).

**Unresolved questions:**

1. Did any working Claude-guided extractor exist under another name in April? GeometryCoachV2 is rule-based, not AGE. **NONE_FOUND** in this repo.
2. Does `vectorizer-sandbox` `agentic_supervisor.py` implement April AGE? **UNKNOWN** (sandbox unavailable). Later (May 30) documents *claim* it is the embodiment; that is not April proof.

---

## Code vs contemporary docs vs later governance (not reconciled)

| Column | Loop 1 | Loop 2 | Loop 3 | AGE |
| ------ | ------ | ------ | ------ | --- |
| **Code (Apr)** | Scale gate + pre-existing coach; no `ValidatedExtractor` | Absent | Classes present, default off | Absent |
| **CLAUDE.md 2026-04-02** | Defined, not built | Defined, not built | “Already exist… NEVER CALLED” | Required, above Loop 1, not built |
| **Handoff 2026-04-19** | “Fully implemented” in photo pipeline | Design only | Implemented, disabled | (not the named VectorizerAGE) |
| **Governance 2026-05-11** | Partial (scale only) | Not implemented | Orphaned | Not implemented, above Loop 1 |
| **Governance 2026-05-30** | Named architecture never approved/implemented; keep scale gate; coach is not proof of Loop 1 | Unchanged absence | Dormant scaffolding | Experimental/sandboxed; tap_tone analogy retracted |

Preserve the disagreement. Do not pick an architecture.
