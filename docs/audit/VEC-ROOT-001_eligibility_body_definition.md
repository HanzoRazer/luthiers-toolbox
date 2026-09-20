# VEC-ROOT-001 — The eligibility block defines "body" in photograph terms, and discards the body on every plan tested

**Subject:** `services/photo-vectorizer/edge_to_dxf.py`, the eligibility block at lines **941–950**,
inside `_build_hierarchy_nodes`.
**Status:** primary finding. Not an amendment. It supersedes no order; it strikes named sections of
two, listed in §9.
**Evidence base:** **HEAD of `luthiers-toolbox`, working tree, 2026-09-19.** Not the
`canonical_vectorizer_pipeline.zip` snapshot. Every line number below was read at HEAD. Two runs,
both instrumented by runtime wrapping with no edit to any repo file.

Evidence tags: **[CODE]** read at HEAD · **[RUN]** produced by an instrumented execution ·
**[RENDER]** confirmed by drawing the result on the source and looking · **[INFERRED]** ·
**[NOT TESTED]**.

---

## 0. LINEAGE BOUNDARY — read before using anything in this document

**Everything here concerns `edge_to_dxf.py` only.**

`services/blueprint-import/vectorizer_phase3.py` is a **separate implementation**. It does not
import `edge_to_dxf`, has no `is_eligible_root`, no `too_small` / `child_contour` reject reasons,
and calls `cv2.findContours` itself at 2216, 2867, 3035 and 3836. **Line 943 is not in its call
graph.** **[CODE]**

Therefore:

> **D-13 — the six corner stubs certified as L-00's body — is a `vectorizer_phase3.py` artifact
> (`Gibson-L0-IN_phase3.dxf`) and is NOT explained by anything in this document.** It needs its own
> investigation in its own lineage.

This is stated here because the census below runs on L-00, D-13 is about L-00, and the two are one
click apart in any future reading. They are not the same lane. See §10.

---

## 1. The block

```python
# edge_to_dxf.py:930-950  [CODE]
area       = float(cv2.contourArea(contour))
area_ratio = area / image_area
...
if page_border:                        reject_reason = "page_border"
elif area_ratio < min_area_ratio:      reject_reason = "too_small"      # 0.005
elif area_ratio > max_area_ratio:      reject_reason = "too_large"      # 0.95
elif parent_idx is not None:           reject_reason = "child_contour"
else:                                  is_eligible   = True
```

Ten lines. Everything downstream — grouping, `_score_contour_group`, the DXF writer — sees only
what leaves here as `is_eligible_root`.

The block encodes **three assertions about what a body is**, and each is true of a photographed
subject and false of a drawn one:

| # | assertion | true of a photo | on a plan sheet |
|---|---|---|---|
| A | a body **encloses area** | the subject is a filled region | the subject is a **stroke**; `contourArea` measures the ink of the line, not the shape it draws |
| B | a body is **not nested** | one subject, no enclosing frame | every view sits inside a page border, so under `RETR_TREE` everything is a child |
| C | a body is **not page-sized** | the subject never fills the frame | a body-only template sheet legitimately can |

`cv2.contourArea` on a traced stroke is the same fact as stroke-doubling seen from the other side:
a contour on line art runs up one side of the ink and back down the other, enclosing its own line
width and nothing else. **[INFERRED, from [RUN] below]**

## 2. Two plans, two branches, same premise

Both runs: `extract_blueprint_to_dxf(..., isolate_body=True)`, the production path
(`blueprint_extract.py:259` → `converter.convert(...)`, `convert()` at 1535). **[CODE]**

### 2a. Cuatro — dies at `too_small` (A) **[RUN]**

```
1. cv2.findContours (RETR_TREE)                7,368    1 "body-scale" by bbox
2. after _remove_page_borders_early            7,368    (removed nothing)
3. after _build_hierarchy_nodes                7,332
4. is_eligible_root                                3
   refused: 7,328 too_small · 1 child_contour
5. groups reaching _score_contour_group            3
```

The three survivors are the **fret-interval table** (446 member contours, s=0.7323, 2.92% of the
raster — the winner), the **neck-and-upper-bout** (161, s=0.7023) and the **side profile** (168,
s=0.5760, aspect 7.94). **[RUN] [RENDER]**

In the lower bout: **1,437 contours, 0 eligible, 1,437 refused `too_small`.** **[RUN]**

The perimeter is **traced, completely** — both flanks, the bottom curve, both waist curves — and
every arc of it is refused. **[RENDER]** Substituting convex-hull area for enclosed area, as a
measurement of the gate and **not as a proposed fix**:

```
                              whole sheet   lower bout
eligible under contourArea              3            0
refused too_small                   7,328        1,437
of those, hull >= 0.005                16            9
hull/enclosed multiple        up to 2,288x
```

**The gate cuts the cuatro body in half at the waist.** The upper bout survives because it arrived
attached to the neck, a contour that happens to enclose real area. The lower bout is discarded.
**[RENDER]**

### 2b. L-00 — dies at `child_contour` (B) **[RUN]**

```
contours                       3,053
eligible under contourArea         0      -> run fails: "No valid contours found in edge image"
refused too_small              3,034

rank  arc px      bbox        enclosed    hull     verdict
   1  38,280   1815x1365      0.276110   0.4135   child_contour   <- the body
   3  16,542   2414x1395      0.391920   0.5875   child_contour
   4   8,746   2449x1904      0.962446   0.9624   too_large       <- the page border
   8   8,288    763x1871      0.000683   0.1480   too_small
```

**L-00's body encloses 27.6% of the raster — fifty-five times the 0.005 floor.** Assertion A never
touches it. It is discarded by assertion B. **[RUN] [RENDER]**

## 3. The fourth thing: rejection does not unparent

Structurally distinct from A/B/C, and the mechanism that zeroes L-00.

The page-size contour at 0.962 is rejected as `too_large` — **correctly**, it is not a body. But
rejecting a contour does not remove it from the hierarchy. Under `RETR_TREE` it remains the
`parent_idx` of everything inside it, so `elif parent_idx is not None` then discards the body, the
soundhole, the braces and the whole drawing. **Two independent, individually-correct rejections
compose into a lane that returns nothing.** **[RUN] [INFERRED]**

Note also that `_is_page_border(edge_count, area_ratio)` **did not fire** on L-00's actual page
border — it fell through to `too_large`. **[RUN]** The block assumes border removal succeeded and
has no fallback for the case where it did not.

### 3a. This is the third instance today of one pattern

| retrofit | exists? | reached by production? | what downstream assumes |
|---|---|---|---|
| text masking | yes, EasyOCR installed and working, `edge_to_dxf.py:1950` | **no** — lives in `convert_enhanced()` (1886), whose only caller is the CLI behind `--enhanced` (2827). Production calls `convert()` (1535) | that text was masked |
| page-border removal | yes, `_remove_page_borders_early` | called, but **missed** on L-00 and removed nothing on the cuatro | that the border is gone and nothing is parented by it |
| debug render | yes, `contour_debug_overlay.py` | **no** — gated on `DEBUG_CONTOURS`, set nowhere, and the call sits inside the `isolate_body` branch (`else:` at 1731 → `RETR_LIST`) | — |

**[CODE]** None of these dependencies is written down anywhere. A retrofit exists, and code
downstream proceeds as though it ran.

## 4. Priority — the cuatro's failure mode goes first

L-00 returns nothing, loudly: `No valid contours found in edge image`. The cuatro returns a **fret
table with score 0.732 and a verdict attached**.

A lane that produces nothing announces its own failure. A lane that produces a confident wrong
answer does not. If these are queued against each other, **the cuatro's mode is the one that
survives review**, and it goes first. **[INFERRED]**

This also constrains any fix: see §5.

## 5. On replacing `contourArea` — what was tested, and what it showed

**Convex-hull area** is the right *diagnostic* and the wrong *fix*. It re-introduces an area
assumption on something that has no area, and a sparse text block hulls large. It is used in §2
only to measure the existing gate.

**Arc length was proposed as the more honest primitive** — it measures what exists, how much line
was drawn, and `cv2.arcLength` is already used in the file. Tested by ranking all 7,332 cuatro
contours: **[RUN]**

```
region          count  best rank  median rank  max arc px
LOWER_BOUT      1,422          3        3,155       8,290
FRET_TABLE        478          5        2,096       6,606
TITLE_TEXT        328         54        2,797       1,044
top 50 by arc length:  other 30 · LOWER_BOUT 16 · FRET_TABLE 4
```

**It does not discriminate.** A fret-table contour reaches **rank 5 at 6,606 px**, because a ruled
table is a grid of long connected lines. Arc length promotes the body from invisible to top-5 —
a real improvement in ranking — but it does not exclude text.

**This kills the framing, not just the threshold.** "How much line was drawn" describes a fret
table as faithfully as it describes a body flank. It is the wrong question, in the same way the
question it was meant to replace was the wrong question. **No replacement primitive is proposed by
this document.**

What none of area, hull or arc length asks is whether the contour is *closed*, whether it spans the
drawing's central field, or whether it is symmetric about a datum — the properties that actually
distinguish a body from a table. **[INFERRED]**

### 5a. The lexicon — it exists, and how it must be cited

Those properties are written down. The source is **`body_lexicon.md` (uncommitted draft,
2026-09-14)**, §2, verbatim:

> *"The **closed** geometry that **spans the central field**, **crosses into cyan on both sides**,
> and is **symmetric about the datum**."*

**Citation rules, which are the point of this subsection:**

1. **Cite it as `body_lexicon.md` (uncommitted draft, 2026-09-14). Never by the
   `scripts/vectorize/references/` path.** That path appears in the draft's own header as where it
   *intends* to live. It is not where the file is. A repo-tree search for `body_lexicon*` on
   2026-09-19 returned nothing, because the file has never been committed.
2. **Mark it `DRAFT — unimplemented` at every invocation.** Its own status line, second line of the
   document, reads: *"DRAFT — definitions, not capability. No code implements this. Nothing in
   `scripts/vectorize/` reads it."*
3. **Do not describe the code as failing to implement it.** VEC-PROV-001 §4 says *"The lexicon wrote
   down the right rule. The code scores photo composition."* That frames the code as deviating from
   a specification. It is not a specification. Nothing reads it and it says so. The accurate and
   weaker claim: **a definition exists on paper, nothing reads it, and the code does something
   unrelated to it.**

The rule still stands as the only written definition of what a body is on a drawing, and §1's A/B/C
assertions are what it should be held against. Its authority is that it is the only candidate, not
that it is implemented or approved.

> **Why this is in the document rather than a footnote.** A draft declared an aspirational path in
> its header; the next reader cited the intention as a location; the citation then travelled. That
> is a claim detached from its conditions, where **the condition was printed in the document's
> second line**. It is the same family as the rest of this record, occurring inside the act of
> writing this record. See §10a.

## 6. Fragmentation is real and is not the cause

Lower-bout fragments: median arc **18.24 px**, median endpoint gap **2.00 px**, ratio **9.12** —
the topology signature; the perimeter is broken where other lines cross it. Neck column control:
21.49 / 2.00 = 10.74, near-identical. **[RUN]**

But the 8,290 px and 7,421 px arcs are enormous and still refused. **An unfragmented perimeter
would fail this gate too.** Topology describes the fragmentation mode; the eligibility block is the
cause.

Consequence for the closure order: closure is still needed — a toolpath cannot follow 1,437 arcs —
but it is **not first**. Fixing closure while this gate stands would join fragments that never
reach a consumer.

## 7. What this does not establish

- **Nothing about `vectorizer_phase3.py`.** See §0.
- **No replacement for the gate.** §5.
- **Nothing about whether restored is correct.** Restored takes the `RETR_LIST` branch at 1731 and
  applies no eligibility gate, so all fragments reach the DXF. It is the only lane producing a
  legible file. Its output is **legible, not closed** — a human eye assembles the fragments.
- **The `page_border` miss on L-00 is observed, not diagnosed.** Why `_is_page_border` did not fire
  at area_ratio 0.962 is **[NOT TESTED]**.
- **Nothing was measured on any plan but these two.** The pattern is demonstrated twice by two
  different routes; it is not surveyed.

## 8. First measurements any fix must not break

1. Cuatro: eligible count must exceed 3, and the lower-bout perimeter must appear in the eligible
   set. Render it.
2. L-00: eligible count must exceed 0.
3. Neither plan may certify a text block. The cuatro fret table scoring 0.732 is the control case.
4. Text masking alone is **not** sufficient and must not land alone: it deletes the cuatro's winner
   and promotes the **partial body** at 0.702 — a more plausible wrong answer, harder to catch by
   eye, with every panel score improved. **[INFERRED from [RUN]]**

## 9. Sections struck by this document

| document | section | disposition |
|---|---|---|
| VEC-PROV-001 | §4 (aspect mechanism) | **struck** — refuted; aspect 7.94 took its penalty and placed third **[RUN]** |
| VEC-PROV-001 | §4 (lexicon framing) | **corrected** — *"The lexicon wrote down the right rule. The code scores photo composition"* frames an unimplemented draft as a specification the code deviates from. See §5a. Cite as uncommitted draft; never by the `scripts/vectorize/references/` path, which is aspirational and appears only in the draft's own header |
| VEC-PROV-001 | §6.2 (reasoning) | superseded — conclusion survives, reasoning does not |
| VEC-AMEND-001 | §6, §7 premise | **struck** — "traced nowhere, at any stage, before any filter" is false; the perimeter is traced and then discarded |
| VEC-AMEND-001 | §6 (topology vs dropout) | struck as a dichotomy — neither; see §6 above |
| VEC-RENDER-001 | §3 | strengthened — the overlay filters `is_outer_candidate` (`ContourDebugNode`); production uses `is_eligible_root` (`HierarchyNode`). **Different populations, not just different winners.** **[CODE]** |
| VEC-RENDER-001 | §7.1/§8/§9 | constrained — `ContourGroup.member_contours` retains geometry; `GroupSelectionResult` carries bbox and scores only. Render must be called **inside selection scope**. **[CODE]** |

**VEC-AMEND-001 is left standing untouched, wrong sections and all.** Amending an amendment in
place erases what was believed when.

## 10. Standing method — proposed addition

> **Artifacts do not share a cause because they share a report.**
>
> Two bad outputs in the same investigation, in the same week, invite a single explanation. Check
> the **call graph** before linking two failures, not after. The prediction that L-00's body would
> be in the `too_small` pile could be neither confirmed nor refuted as stated, because its two
> terms — D-13's rectangle and line 943 — do not refer to the same code.

Co-occurrence in an investigation is not shared lineage. This sits alongside name collision,
position implying purpose, and a claim detached from its conditions.

### 10a. Standing method — second proposed addition

> **A draft's declared path is an intention, not a location.**
>
> Documents state where they intend to live before they live there. The next reader cites the
> header path as though the file were at it, and the citation outlives the check. Resolve a path
> before repeating it, and carry the document's **status line** with every citation — a draft that
> says *"no code implements this"* must never be cited as a specification the code violates.

Both this and §10 were produced by failures inside this investigation, not observed in the codebase:
§10 from a prediction whose two terms were in different lineages, §10a from a citation repeated
through four documents without the header being opened. **[INFERRED]**

## 11. The control — the archtop, and what passing does not buy

The three premises in §1 were argued from blueprint failures. This is the positive control.

**Input class correction:** the archtop is an **AI-generated image**, not a photograph — which is the
class `edge_to_dxf` was actually built for, per the owner account in PROV §0. This is a run **on**
the designed input, not adjacent to it. **[OWNER]**

**Confound identified before the run, by looking:** the source is composed against a plank wall with
five or six full-width horizontal seams, a wall/floor boundary and a stand — any of which could
trace larger than the guitar and fire premise B for a reason unrelated to the thesis. A
background-removed version (`_02_foreground.jpg`) was therefore used as the control. **The confound
did not fire**: the guitar's `parent_idx` is `None` in both runs, and the single `child_contour` in
the original is 107×187 px. The original therefore corroborates rather than merely failing to
refute. **[RUN] [RENDER]**

```
                                contours  eligible  verdicts                      winner
CONTROL (background removed)         488         1  too_small=487                 s=0.8464
original (confound present)          634         1  too_small=632, child=1        s=0.9894
```

The eligible contour is **648×1285, area ratio 0.0145 — three times the floor — parent `None`,
edge_count 0.** A, B and C all hold, exactly as the thesis requires. Against the same gate:
cuatro **3 eligible, winner = a fret table at 0.7323**; L-00 **0 eligible, run fails**. **[RUN]**

**§1's A/B/C framing is confirmed by positive control, not only by failure analysis.**

### 11a. Eligibility is not constructibility

Passing the gate does not produce something that can be built, and this is the more important half.

Owner account: *"we never could construct the neck"* — the April 2026 decision to stop. **[OWNER]**
Measured on the eligible contour:

```
13,322 points, arc 14,626 px
39.2% of its points lie in the neck corridor
3,864 vertical-dominant vs 1,352 horizontal-dominant segments
vertical span covered: 569 of 569 px (100%)
```

By those numbers the neck's side edges are continuous and complete. **The render shows why that
reading is wrong.** It is *one path that weaves*: down the fretboard edge, inward to wrap each pearl
inlay block, back out, repeat, and at the top it swallows the headstock and the tuner buttons.
**The neck profile and the ornament printed on it are the same contour, and nothing in it
distinguishes them.** **[RENDER]**

So the April stop was **a representational limit, not a tuning failure or insufficient effort.**
A profile cannot be lifted out without deciding which excursions are decoration, and the contour
carries no information supporting that decision. **[INFERRED]**

**Consequence for this document: fixing the eligibility block is necessary and not sufficient** —
the same shape as the text-masking warning in §8.4. A body that clears the gate as one entangled
path is not a body that can be cut.

### 11b. What the extractor returns, and what lutherie needs

Both failures are one root seen from two sides. On a plan the body is a **stroke**, so
`contourArea` measures ink and the gate discards it (§2a). On an AI image the body is a **region**,
so it passes at 0.99 — and what returns is one boundary containing everything tonally continuous
with it. **The extractor returns boundaries; lutherie needs named features.** Selection can choose
among contours; it cannot decompose one. **[INFERRED]**

**Verified, against a draft claim that was wrong:** `body_lexicon.md` (uncommitted draft — see §5a)
records `PrimitiveType` as "vocabulary, no extraction path reaches it." **That is false.**

| capability | status |
|---|---|
| per-contour **shape** classification (`PrimitiveType`: CIRCLE/ARC/ELLIPSE/LINE/POLYLINE) | **exists and is reached** — `vectorizer_phase3.py:195`, constructed 933/964/1021, consumed 2663–2726 **[CODE]** |
| per-contour **semantic** classification (`ContourCategory`: BODY_OUTLINE, F_HOLE, BRACING, PICKGUARD…) | exists in `vectorizer_phase3.py` (ML + rule-based fallback, ~880) **[CODE]** |
| either of the above in `edge_to_dxf` | **absent** — `grep -c "PrimitiveType\|GeometricPrimitive\|PrimitiveDetector"` = **0** **[CODE]** |
| splitting **one** boundary into semantic parts (profile vs ornament) | **not found anywhere.** `detect_all` (1034) is `for contour in contours:` and `detect_circle` measures circularity of the **whole** contour. It labels contours; it does not split them. **[CODE]** |

So the missing stage is **intra-contour decomposition**, and it is genuinely missing. What is *not*
missing is per-contour primitive detection — and a reuse path for it was written five months ago:

> `docs/investigations/cam_ready_reuse_assessment_2026-04-28.md:70` — *"**No coupling to
> Phase3Vectorizer state.** The only initialization parameter is `mm_per_px`. The `detect_all()`
> method takes a raw `List[np.ndarray]` — the same format EdgeToDXF already produces from
> `cv2.findContours()`. **Reuse path:** Extract `PrimitiveDetector`, `GeometricPrimitive`, and
> `PrimitiveType` to a shared module. Call from EdgeToDXF after contour extraction."* **[CODE]**

Assessed as directly reusable, interface already matching, never executed. **This is a
cross-lineage observation and §0 applies**: moving code from `vectorizer_phase3.py` into
`edge_to_dxf.py` is a deliberate merge, not a finding carried across. It would **not** solve the
archtop, which needs intra-contour decomposition.

## 13. Corpus census, 2026-09-19 — how much of this problem is self-inflicted

Run before committing to any fix, because it changes the scope of the fix.

**Every shipped lane rasterizes.** `vectorizer_phase3.py:1401` calls `page.get_pixmap(matrix=mat)`
and hands a numpy array to `_simple_extraction`, which sees `image: np.ndarray` and has no PDF
object at all. `edge_to_dxf` does the same via `blueprint_extract.render_pdf_page()` at the same
200 DPI cap, and its CLI rejects PDFs outright. **[CODE]**

**Exactly one file in the repository reads content streams**, and nothing calls it:
`scripts/extract_pdf_vectors.py`, committed `e231fe35` on 2026-03-04 and untouched since. It calls
`page.get_drawings()` (:31) and converts with `x_mm = x / 72 * 25.4` (:176) — **absolute scale by
definition, not by assumption.** Zero importers; the only reference to `extract_paths_from_pdf` is
inside its own `main()`. **[CODE]**

### The census **[RUN]**

314 distinct PDFs across `luthiers-toolbox/Guitar Plans`, `My Drive/Guitar Plans` and
`ltb-express`, classified by what page 0 actually carries:

| class | count | share |
|---|---:|---:|
| VECTOR (paths ≥ 20, images ≤ 2) | 215 | 68.5% |
| MIXED | 5 | 1.6% |
| RASTER | 41 | 13.1% |
| EMPTY (prose documents, not plans) | 50 | 15.9% |
| ERROR (macOS `._` resource forks) | 3 | 1.0% |

**Content-stream readable: 220 of 314 (70.1%)**, and higher among actual plans, since EMPTY is
mostly checklists and reports.

### But the plans that defeated this investigation are the scans **[RUN]**

```
cuatro puertorriqueño   RASTER   paths=15       images=10   page 610 x 1092 mm
Gibson L-00             RASTER   paths=1        images=1    page 647 x  503 mm
Carlos Jumbo 3-3        VECTOR   paths=76,063   images=0    page 841 x 1189 mm
plano cuatro venezolano VECTOR   paths=2,513    images=0    page 864 x 1118 mm
```

**This does not dissolve §2.** Both census cases — the cuatro's `too_small` and L-00's
`child_contour` — are scans. Content-stream reading cannot help them, and the eligibility block
remains the correct subject for those plans.

**What it does change is the scope of any fix.** The problem narrows from "fix extraction" to
**"fix extraction for scans"**, which is smaller and better posed, with roughly 70% of the corpus
reachable by a path that needs no scale detector and no decomposition stage.

### The part worth sitting with

**Carlos Jumbo 3-3 — the anchor plan for the entire light-line archaeology — carries 76,063
separated vector paths and zero images.** The April 1 run rasterized it and traced the pixels back
to a 114-point outline whose dimensions were then typed by the operator rather than measured. The
geometry was present as paths, in real millimetres, the whole time.

That is the same pattern as §3a, at the level of the pipeline's first decision rather than a
retrofit: a capability present and unreached, while months of work went at the same problem from
the other side. It is recorded here as scope, **not** as a proposal — see §7, this document
proposes no fix.

## 12. Reproduction

Instrumented runs, runtime wrapping only, no repo file edited. Scripts in the session scratchpad:
`cuatro_stage_census.py`, `where_is_the_perimeter.py`, `whole_sheet_by_reason.py`,
`hull_vs_area.py`, `arclen_discriminates.py`, `l00_prediction.py`.

Renders (each claim above tagged **[RENDER]** rests on one of these):
`CUATRO_scored_groups.png`, `CUATRO_stage_census.png`, `CUATRO_lower_bout_by_reason.png`,
`CUATRO_whole_sheet_by_reason.png`, `CUATRO_the_rejected_body.png`, `L00_too_small_pile.png`.

D-16 guard observed on both runs: source copied to scratch, original hashed before and after,
both `OK`.
