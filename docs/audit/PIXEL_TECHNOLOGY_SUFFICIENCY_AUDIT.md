# Pixel Technology — Development, Testing, and the Sufficiency Verdict

**Date:** 2026-08-28
**Base:** `origin/main` @ `9d5d9001`
**Checkpoint 3.** Companions: `PIXEL_PLATFORM_LOOP1_FORENSIC_AUDIT.md` (checkpoint 1),
`PIXEL_PLATFORM_SUPERVISORY_CAPABILITY_MAP.md` (checkpoint 2).

**Question:** when was the pixel extraction technology developed and tested, what
documentation did that produce, and why was it judged insufficient as a standalone
technology?

**Answer in one line:** it was never judged insufficient in the abstract — it was measured,
repeatedly, against real inputs, and the measurements are the reason. The verdict is written
down explicitly, with a named lifecycle state and a ten-item gate.

---

## 1. The verdict exists in writing

`docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md` defines a lifecycle state whose
definition **is** the answer:

| State | Meaning | Blueprint Reader default? | May auto-feed IBG fabrication? |
|---|---|---|---|
| **`EXPORT_SAFE`** | Export landmine fixed (non-empty when contours exist; fail-closed for fab-bound) | No | **No — not sufficient for commercial viability** |

The technology reached *"produces a valid, non-empty DXF"* and stopped there. The registry
draws the distinction sharply in its own purpose statement for the readiness gate:

> Prevent assigning **ACTIVE** … until SIMPLE is commercially defensible — **not merely
> non-empty DXF**.

So the judgement was never "it doesn't work." It was **"working is not the bar."**

### 1.1 The ten-item gate it did not pass

`SIMPLE Commercial Readiness Gate` — all required for `PRODUCTION_ACTIVE`:

```text
G1  Export integrity          >=1 LINE entity; fab-bound fails closed on zero export
G2  No fab-bound SIMPLE without explicit experimental / reject-by-default label
G3  Body semantics            a defensible BODY_OUTLINE, or a documented reject
G4  Scale parity              Cuatro golden asset within protection-table tolerance
G5  Entity volume bounded     no 100k+ unreviewed dumps
G6  Topology provenance       failures must be attributable
G7  IBG contract              SIMPLE-sourced DXF is review-only, intake gate tested
G8  Regression suite          dedicated tests, CI job, no regression on refined golden
G9  Governance approval       Ross, explicitly
G10 Lifecycle doc updated     registry row -> ACTIVE with sign-off
```

> **Until G1–G10 pass:** lifecycle state remains **EXPORT_SAFE** or **SANDBOX** (maximum).

**G3, G4 and G6 are the substantive ones**, and §3 below is the measurement record showing
why they were not met. G1 is the only one the technology demonstrably reached.

### 1.2 What it was explicitly *not* allowed to substitute for

```text
- fixing Les Paul slab_body at low confidence (morphology interpretation)
- replacing `refined` as the blueprint-reader default
- satisfying Cuatro golden DXF parity without measurement
- enabling correction-based learning (submit_correction, TrainingDataCollector)
```

The third line is the discipline that decided this: **parity claims require measurement.**

---

## 2. Development timeline

| Date | Commit | Event |
|---|---|---|
| 2026-03-05 | `1dc68d8d` | `VECTORIZER_UPGRADE_PLAN.md` — the plan predates the code |
| 2026-03-05 | `d052de8d` | LeaderLineAssociator ranking algorithm |
| 2026-03-06 | `994c3453` | **pixel calibration module + grid zone classifier** — and three test reports the same day |
| 2026-03-09 | `4ddf35aa` | grid zone re-classification |
| 2026-03-09 | `4cd1b2bb` | `DEVELOPER_HANDOFF.md` |
| 2026-03-14 | `39482abb` | Patches 14+13+15 — gated closer, family classifier, feature-scale calibration |
| 2026-03-14 | `7d5d86c0` | **Patch 17** — ContourMerger, X-extent guard, coin position filter |
| 2026-04-01 | `ced75eaa` | `BLUEPRINT_CALIBRATION_METHODOLOGY.md` |
| 2026-04-06 | `7117e083` | `PHOTO_INPUT_SPEC.md` |
| 2026-04-06 | `d39d3ac9` | **`validation/sprint4/README.md`** — the decisive measurements |
| 2026-04-18 | `cbfee5ea` | Sprint 5 — grid reclassification on blueprint path |
| 2026-04-28 | — | `el_cuatro_extraction_comparison_2026-04-28.md` |
| 2026-05-20 | `4cbe56ed` | `ARCHAEOLOGY_RELOCATION.md` + `PHASE2_RELOCATION.md` — **retirement** |

Roughly **eleven weeks** from first plan to relocation.

---

## 3. The testing record — three measurements, in escalating severity

### 3.1 2026-03-06 — `DIMENSIONS_REPORT.md`: zero body dimensions on 28 blueprints

The first empirical test, `994c3453`:

| Metric | Value |
|---|---|
| Total blueprints | 28 |
| Scale length found | 9 (**32%**) |
| High confidence | 10 (**36%**) |
| **Body dimensions found** | **0** |

Zero. Across twenty-eight real blueprints, the extraction produced **no body dimensions at
all**. The report's own explanation: *"Many blueprints are scanned images without embedded
text."* That is the first recorded encounter with the boundary the technology never crossed —
**pixels are not semantics.**

### 3.2 2026-03-14 — Patch 17: fixes that trade one error for another

`7d5d86c0` reports its own results against a baseline, and does not flatter them:

```text
Archtop W:       111.7% -> 22.6%   (improved -89pp)  X-extent guard working
Smart Guitar H:   41.3% -> 32.9%   (improved -8pp)   merger partially helped
Smart Guitar W:    5.2% -> 95.4%   (REGRESSED)       needs investigation
Benedetto:        unchanged                          coin filter did not trigger
```

A width error of **5.2%** became **95.4%** as a side effect of fixing a height error. Two of
four targets improved, one regressed catastrophically, one did not respond. This is the
signature of point-fixing a system with no closed validation — and it is precisely the
motivation later written into `CLAUDE.md` for the (unbuilt) feedback loops.

### 3.3 2026-04-06 — `validation/sprint4/README.md`: the decisive split

The clearest evidence in the record, because it isolates the variable:

| Input | Kind | Expected | Measured | Error |
|---|---|---|---|---|
| Smart Guitar | **AI-generated image** | 368 × 444 mm | **368.3 × 444.5** | **~0.1%** |
| Archtop (v2) | **real studio photo** | 520 × 432 mm | **535.8 × 636.1** | height **+47%** — *"stand included in extraction"* |
| Archtop (v3) | same photo, height-cap fix | 520 × 432 mm | **623.8 × 535.8** | still wrong; *"Body height capped: trimmed 15px (likely guitar stand)"* |

**On synthetic input the technology is near-exact. On a real photograph it is not.** The v3
"fix" did not converge on the right answer — it produced a *different* wrong answer, and the
warning text shows why: the pipeline cannot distinguish a guitar from the stand holding it.
That is not a tuning failure. It is the absence of a model of what a guitar *is*.

---

## 4. Why the measurements produced this verdict and not another

The three measurements agree on one thing: the pixel technology has **no way to know when it
is wrong**.

```text
28 blueprints  -> 0 body dimensions       it cannot find what it is looking for
Patch 17       -> 5.2% becomes 95.4%      it cannot tell a fix from a regression
Archtop photo  -> stand read as body      it cannot tell the subject from the furniture
```

Every remedy in the record is an *external* constraint bolted on afterwards: an X-extent
guard (reject > `body_region.width * 1.30`), a height cap, a coin-position filter, family
priors in millimetres. None of them is derived from the pixels. Each encodes knowledge about
what an instrument *is* — knowledge the pixel layer does not have and cannot acquire.

This is why the supervisory layer that grew around it (checkpoint 2) reasons in
**millimetres and instrument-family priors rather than pixels** (checkpoint 1, §4.4). The
architecture is the verdict, expressed as code: the pixel technology was retained as a
**worker** and denied **authority**.

Stated plainly:

```text
sufficient as an extractor        yes  -- it produces contours and a valid DXF (G1)
sufficient as an authority        no   -- it cannot certify its own output (G3, G4, G6)
therefore standalone              no
```

---

## 5. Retirement, and what was kept

`ARCHAEOLOGY_RELOCATION.md` (2026-05-20, `4cbe56ed`) records `RELOCATED_EXTERNAL` to
`vectorizer-sandbox`, source commit `f1e11d99`, sandbox tag `v0.2.0-semantic-lineage-import`:

```text
cognitive_extractor.py, cognitive_extraction_engine.py   -> src/semantic/
body_dimension_reference.json                            -> src/semantic/
extract_body_grid.py ... _v5.py                          -> src/archaeology/
vectorizer_phase2.py                                     -> src/archaeology/
```

Re-import is blocked by a precommit gate,
`scripts/governance/check_semantic_sandbox_imports.py`.

**The production path was not retired.** The same document states it plainly:

```text
POST /api/blueprint/vectorize/async -> CleanupMode.REFINED -> edge_to_dxf.py
```

`REFINED` remained the default; `SIMPLE` and the cognitive/grid modules did not. So this was
**not a rejection of pixel extraction** — it was a refusal to promote the *experimental*
modes to commercial status, and a relocation of the research lineage to where research
belongs.

---

## 6. Documentation produced, in full

| Date | Commit | Document | Kind |
|---|---|---|---|
| 2026-03-05 | `1dc68d8d` | `blueprint-import/docs/VECTORIZER_UPGRADE_PLAN.md` | plan |
| 2026-03-06 | `994c3453` | `blueprint-import/DIMENSIONS_REPORT.md` | **test result** |
| 2026-03-06 | `994c3453` | `blueprint-import/CALIBRATION_REPORT.md` | **test result** |
| 2026-03-06 | `994c3453` | `blueprint-import/BATCH_CLASSIFICATION_REPORT.md` | **test result** |
| 2026-03-09 | `4cd1b2bb` | `photo-vectorizer/DEVELOPER_HANDOFF.md` | handoff |
| 2026-04-01 | `ced75eaa` | `photo-vectorizer/BLUEPRINT_CALIBRATION_METHODOLOGY.md` | method |
| 2026-04-06 | `7117e083` | `photo-vectorizer/PHOTO_INPUT_SPEC.md` | input contract |
| 2026-04-06 | `d39d3ac9` | `photo-vectorizer/validation/sprint4/README.md` | **test result** |
| 2026-04-28 | — | `docs/investigations/el_cuatro_extraction_comparison_2026-04-28.md` | comparison |
| 2026-05-20 | `4cbe56ed` | `photo-vectorizer/ARCHAEOLOGY_RELOCATION.md` | **retirement** |
| 2026-05-20 | `4cbe56ed` | `blueprint-import/PHASE2_RELOCATION.md` | **retirement** |
| — | — | `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md` | **the verdict** |

Four are test results. Two are retirement records. One is the governing judgement.

---

## 7. Not established

- `CALIBRATION_REPORT.md` and `BATCH_CLASSIFICATION_REPORT.md` were inventoried, not read in
  full; their contribution to the verdict is assumed from date and title, not quoted.
- Patches 1–12 and 16 are referenced by number in commit bodies but were not located as
  discrete commits. The series may predate these service paths.
- Whether any G1–G10 criterion was later satisfied and the registry left un-updated.
- The `el_cuatro_extraction_comparison` recommendation table was not read in full.
- No runtime re-measurement of the **2026 figures** was performed. Every figure in §3 is
  quoted from the record as written at the time, not reproduced.

**Amendment 2026-08-28 — one contemporary runtime confirmation now exists.** A live run of
the photo pipeline on `El Cuatro 1.pdf` (recorded in
`PIXEL_PLATFORM_LOOP1_FORENSIC_AUDIT.md` §3.3a) produced:

```text
ownership_score 0.501 < 0.600  -> coach action "rerun_body_isolation", retry_count 1
elect_body_contour_v2: ownership gate rejected all plausible body contours   (x3)
Export blocked: No contour passed body ownership threshold 0.60
SVG/DXF/JSON export skipped due to low plausibility
```

This does not re-measure the 2026 accuracy figures, and does not attempt to. What it
confirms is the §4 thesis, live and today: the pixel layer could not resolve a body, the
metrological supervisor detected that from a scalar score, and **the platform exported
nothing.** Sufficient as an extractor, not sufficient as an authority — and the authority
boundary is observably load-bearing rather than aspirational.

---

## 8. Checkpoint

```text
DEVELOPED       2026-03-05 -> 2026-04-18   (~11 weeks)
TESTED          2026-03-06, 2026-03-14, 2026-04-06, 2026-04-28
RETIRED         2026-05-20  RELOCATED_EXTERNAL -> vectorizer-sandbox
VERDICT         EXPORT_SAFE -- "not sufficient for commercial viability"
CAUSE           measured: cannot find (0/28), cannot self-check (5.2% -> 95.4%),
                cannot distinguish subject from furniture (+47% on real photo)
PRODUCTION      REFINED path retained and unchanged
```
