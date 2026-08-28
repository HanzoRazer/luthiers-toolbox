# Pixel Platform — Loop 1 Forensic Audit

**Date:** 2026-08-28
**Base:** `origin/main` @ `9d5d9001`
**Checkpoint:** Loop 1 only. Loops 2 and 3 are **not** evaluated here by instruction.
**Method:** 157-path mechanical census + static call/data graph + runtime witness on a real input.

> **Reading rule for this document.** It reports capability, responsibility, evidence
> consumed and produced, and what causes a change of course. Execution order is recorded
> as evidence, not as the conclusion. Where a relationship could not be proven it is
> marked `RELATIONSHIP UNPROVEN` rather than inferred from resemblance.

**Provenance vocabulary:** `LTB` = luthiers-toolbox only · `VS` = vectorizer-sandbox only ·
`BOTH` = present in each · `RELATIONSHIP UNPROVEN` = co-existence established, derivation not.

---

## 0. Headline findings

1. **Loop 1 exists in production, is on by default, and predates the concept it is said to
   implement.** `GeometryCoachV2` was born **2026-03-15** (`50123379`). The three-loop
   architecture document was written **2026-04-02** (`6075db47`) — **18 days later**. The
   "Loop 1" label was applied retrospectively to a system that already worked.
2. **The platform's genesis commit is the fail-open.** The first commit in this census,
   `090cd808` (2025-12-15), is titled *"fix: Wrap experimental routers in try/except for
   graceful fallback."* Every silent-degradation problem below descends from it.
3. **`VECTORIZER_AVAILABLE` has been permanently `False` since 2026-03-15** because the
   module it imports was deleted that day and the failure is swallowed by a bare `pass`.
   Five and a half months, no error, no log.
4. **Almost nothing was ever deleted.** Of 157 paths, **1** was deleted outright. The
   platform accreted; it was not pruned.
5. **`agentic_supervisor.py` has never existed in this repository.** Its relationship to
   `GeometryCoachV2` is `RELATIONSHIP UNPROVEN` — they share no file, no commit, and no
   import in either direction.
6. **Loop 1 is not a pixel mechanism.** The coach and its authority layer contain **zero**
   `cv2` call sites. They decide on six dimensionless scores and on **millimetre-space
   instrument-family priors**, and only *actuate* pixel stages. Loop 1 lives in the pixel
   platform; it does not reason in it. The sandbox supervisor, by contrast, has **17** `cv2`
   call sites and inspects masks directly — so the two systems diverge at the mechanism
   level, not merely in maturity (§4.4, §5).

---

## 1. Scope as executed

| Layer | Treatment |
|---|---|
| `services/photo-vectorizer/` (64 `.py`) | legacy pixel platform — **in scope** |
| `services/blueprint-import/` (14 `.py`) | legacy pixel platform — **in scope** |
| `app/services/blueprint_*.py`, `app/routers/blueprint/` | downstream orchestration/consumers — traced at the seam |
| `vectorizer-sandbox` | **read-only**, lineage comparison only. Nothing executed, nothing modified. |

The photo→blueprint succession is preserved as an internal seam rather than a scope boundary.

---

## 2. What constitutes the legacy pixel platform

**157 paths ever created** across the two services.

| State | Count | Meaning |
|---|---:|---|
| `LIVE` | 107 | present at `origin/main`, absent from the sandbox |
| `BOTH` | 37 | present in **both** repositories |
| `MIGRATED_TO_SANDBOX` | 8 | absent here, present in `vectorizer-sandbox` |
| `RELOCATED` | 4 | moved within this repo |
| `DELETED` | 1 | gone from both |

Full table: **Appendix A** (`census_pixel.json`, machine-readable).

### 2.1 The single deletion is load-bearing

```text
services/blueprint-import/vectorizer.py
  born  2025-12-15  090cd808  "Wrap experimental routers in try/except for graceful fallback"
  died  2026-03-15  d9cd4d7d  "cleanup - remove dead code, organize tests"
```

This is the **only** file ever deleted from the platform, and it is precisely the module
that `app/routers/blueprint/constants.py` still tries to import:

```python
VECTORIZER_AVAILABLE = False
create_vectorizer = None
try:
    from vectorizer import create_vectorizer      # deleted 2026-03-15
    VECTORIZER_AVAILABLE = True
except ImportError:
    pass                                          # no log, no warning, no detail
```

Verified: no `vectorizer.py` exists in either service, in either repository. The flag is
not environment-dependent — it is **structurally permanent**. The "graceful fallback"
introduced at genesis converted a deleted dependency into a silent capability loss, and
the cleanup commit that removed the file did not remove its importer.

### 2.2 Migration out was one lineage, on one day

```text
2025-12-15  090cd808  vectorizer_phase2.py            -> VS src/incubation/
2026-03-23  c3a8cecb  cognitive_extraction_engine.py  -> VS src/semantic/
2026-03-23  3e3337b6  cognitive_extractor.py          -> VS src/semantic/
2026-04-19  3e75a7cb  extract_body_grid.py            -> VS src/archaeology/
2026-04-19  3e75a7cb  extract_body_grid_v2.py         -> VS src/archaeology/
2026-04-19  3e75a7cb  extract_body_grid_v3.py         -> VS src/archaeology/
2026-04-19  3e75a7cb  extract_body_grid_v4.py         -> VS src/archaeology/
2026-04-19  3e75a7cb  extract_body_grid_v5.py         -> VS src/archaeology/
```

The entire `extract_body_grid` v1→v5 lineage left in a single commit. The 4 `RELOCATED`
paths are test files moved into `tests/` by `d9cd4d7d` — the same cleanup that deleted
`vectorizer.py`.

---

## 3. Runtime witness

**Input:** `Guitar Plans/El Cuatro/El Cuatro 1.pdf` (13,396 bytes) — the Sprint B test case.
Present, but **gitignored**, which is why it is invisible to `git ls-files`.

### 3.1 `*_AVAILABLE` snapshot — measured, not assumed

```json
{"ANALYZER_AVAILABLE": true,  "CALIBRATION_AVAILABLE": true,
 "PHASE2_AVAILABLE": false,   "PHASE3_AVAILABLE": true,
 "PHASE4_AVAILABLE": true,    "VECTORIZER_AVAILABLE": false}
```

**The two `False` values are not the same kind of fact**, and conflating them would hide
the defect:

| Flag | Mechanism | Character |
|---|---|---|
| `PHASE2_AVAILABLE` | **hardcoded** `False` with a populated `PHASE2_UNAVAILABLE_DETAIL` naming the sandbox destination and the replacement route | **honest** — a documented relocation, no exception involved |
| `VECTORIZER_AVAILABLE` | `except ImportError: pass` against a module deleted 5½ months ago | **silent** — indistinguishable from a transient environment fault |

Phase 2 shows what a truthful unavailability looks like in this codebase. The Phase 1
vectorizer shows what the genesis fail-open produces instead.

### 3.2 Coach reachability

```json
{"entry_class": "PhotoVectorizerV2", "instantiated": true,
 "coach_object": "GeometryCoachV2",
 "enable_body_isolation_coach_default": true}
```

`GeometryCoachV2` is constructed **unconditionally** at pipeline instantiation
(`photo_vectorizer_v2.py:3810-3815`) and its gate defaults **on**:

```python
env_flag_raw = os.getenv("PHOTO_VECTORIZER_ENABLE_BODY_ISOLATION_COACH",
                         "1" if getattr(self, "enable_body_isolation_coach", True) else "0")
env_flag = str(env_flag_raw).strip().lower() not in {"0", "false", "no", "off"}
```

Loop 1 runs unless someone switches it off. This is the opposite posture from the Loop 3
machinery (`enable_feedback=False`), and the contrast is the most important structural
fact about the surviving implementation.

### 3.3 Full-pipeline execution — `PARTIAL`

`PYMUPDF_AVAILABLE` was `False` locally; PyMuPDF **is** declared
(`services/api/requirements.txt:34`), so this was a local environment gap, corrected by
installing it. The end-to-end extraction run exceeded the observation window and is
recorded **`WITNESS_INCOMPLETE_TIMEBOX`** — not as a failure, and not as a pass. Sections
3.1–3.2 stand on completed runs.

**Dependency finding:** `services/photo-vectorizer/` has **no `requirements.txt` at all**.
Its dependencies are satisfied incidentally by the API service's manifest, reached through
`sys.path` injection. The photo pipeline declares nothing about what it needs to run.

### 3.4 The platform rasterizes vector input at the door

`_load_image` (`photo_vectorizer_v2.py:668-686`) renders page 0 of a PDF at 2× via PyMuPDF
and returns a NumPy array. A vector-native PDF is converted to pixels **before** any
extraction decision. The "pixel platform" is pixel-domain by construction, not because its
inputs are pixels.

---

## 4. Loop 1 in the surviving implementation

### 4.1 Identity and provenance

| | |
|---|---|
| **Capability** | `GeometryCoachV2` — bounded, validated retry of body isolation and contour assembly |
| **Born** | **2026-03-15**, commit `50123379` |
| **Provenance** | **`LTB`** — absent from `vectorizer-sandbox` |
| **Reachability** | live, API-reachable, **default-on** |

The birth commit created the whole subsystem at once:

```text
geometry_authority.py     family priors, export tolerance, issue-based retry policy,
                          dimension fit scoring
body_isolation_result.py  typed BodyIsolationResult, 6-signal breakdown + issues
body_isolation_stage.py   BodyIsolationStage wrapping BodyIsolator, save/restore + scoring
geometry_coach_v2.py      GeometryCoachV2, Rules A-D, monotonic improvement gate,
                          evaluate() -> (body, contour, decision)
```

and wired it as **Stage 4.5** (isolation replaces the bare `body_isolator.isolate()`) and
**Stage 8.5** (the guarded retry loop, after contour assembly).

### 4.2 What runs, what it consumes, what it produces

```text
Stage 4.5  BodyIsolationStage.run()
              consumes  image, fg_mask/alpha_mask, family priors
              produces  BodyIsolationResult  (6-signal breakdown, issues, ownership score)
                    |
Stage 8.5  GeometryCoachV2.evaluate(
              body_stage_runner=self.body_isolation_stage,     <-- the runners themselves
              contour_stage_runner=self.contour_stage,         <-- passed as callables
              image, fg_mask, original_image, instrument_family,
              geometry_authority, contour_inputs{edges, alpha_mask, calibration,
                                                 family, image_shape, params},
              body_result, contour_result)
           -> (body_isolation_result, contour_result, CoachDecisionV2)
```

**This is what makes it a closed loop rather than a validator.** The coach does not receive
finished data to judge; it receives the *stage runners as callables* and can re-execute
them, then **replace** the pipeline's stage outputs with the results of its own reruns
(`photo_vectorizer_v2.py:4128-4129`).

### 4.3 What causes a change of course

`CoachV2Config`: `ownership_retry_threshold = 0.60`, `max_retries`,
`body_retry_profiles: List[BodyIsolationParams]`, `contour_retry_profiles: List[StageParams]`.

| Rule | Trigger | Action |
|---|---|---|
| **Rule 0** — ownership gate | `ownership_score < 0.60` | body-isolation retry. **Fires before the retry-budget check**, so the first ownership failure always gets one attempt |
| **Rule A** | lower-bout recovery condition | body retry with next profile |
| **Rule B** | border-contact suspicion | body retry, suppression profile |
| **Rule C** | contour disagreement / merge suspicion | **contour**-stage retry |
| **Budget** | `retry_count >= max_retries` | `action = "manual_review_required"`, surfaced as a warning |

Two design properties worth recording because they are unusual and deliberate:

- **The ownership gate outranks the budget.** Rule 0 is evaluated before the exhaustion
  check, so a low-ownership first result is never refused a retry on budget grounds.
- **A monotonic improvement gate** (per the birth commit) prevents a retry from replacing a
  better result with a worse one — the loop cannot degrade its own output.

Exhaustion terminates in `manual_review_required`, not in a silent best-effort export.

### 4.4 Loop 1 is **not** a pixel mechanism

> **Amendment, 2026-08-28.** The first issue of this audit established *where* Loop 1 lives
> and left its **operating domain** unstated. Location and mechanism are different claims,
> and the answer is not the one the enclosing platform implies.

`GeometryCoachV2` and `geometry_authority.py` perform **no image processing whatsoever**:

| Evidence | `geometry_coach_v2.py` | `geometry_authority.py` |
|---|---|---|
| imports `cv2` | **no** | **no** |
| `cv2.*` call sites | **0** | **0** |
| imports `numpy` | yes — but only as a **type annotation** for pass-through params | **no** |
| direct raster access | **one line**: `h, w = image.shape[:2]` (dimensions, not content) | none |

Every apparent pixel-operation match in the coach (`threshold`) is the config field
`ownership_retry_threshold`, not `cv2.threshold`. The images the coach receives are
**opaque payloads** forwarded to the stage runners.

**What it actually decides on** — `BodyIsolationResult.score_breakdown`, six dimensionless
normalised scalars:

```text
hull_coverage           vertical_extent_ratio    width_stability
border_contact_penalty  center_alignment         lower_bout_presence
```

and the rules read exactly these:

```python
ownership_score = self._ownership_score(contour_result)
if ownership_score < self.config.ownership_retry_threshold: ...          # Rule 0
if body_result.border_contact_likely and \
   body_result.score_breakdown.border_contact_penalty >= \
   self.config.severe_border_penalty_threshold: ...                      # Rule B
ownership_delta = float(ownership_score_after) - float(ownership_score_before)  # monotonic gate
```

**And `geometry_authority` reasons in millimetres, against luthiery priors:**

```python
_FAMILY_BODY_PRIORS_MM   # (height_min_mm, height_max_mm, width_min_mm, width_max_mm)
def score_dimension_fit(..., estimated_height_mm, estimated_width_mm)
    -> {"height_fit": ..., "width_fit": ...}
```

Its entire import list is `json`, `os`, `dataclasses`, `typing`.

**Therefore:**

```text
Loop 1 evidence domain    dimensionless scores + millimetre-space instrument-family priors
Loop 1 actuator domain    pixel stages (body isolation, contour assembly)
Loop 1 mechanism          NOT pixel-based
```

The coach is a **metrological / spec-domain supervisor whose workers happen to be pixel
stages.** It never looks at an image; it looks at how well the extracted body scores as a
*guitar body of its family*, in millimetres, and re-tasks the pixel stages when that score
is poor. "Loop 1 belongs to the pixel platform" is true as a statement of **location** and
false as a statement of **mechanism**.

This is why the surviving implementation is domain-portable in a way the sandbox design is
not — see §5.

### 4.5 Strategy selection exists here — and it is *not* Loop 2

`_choose_body_retry_profile(retry_count, ...)` selects the next `BodyIsolationParams` from
`body_retry_profiles`, indexed by attempt. That **is** strategy selection, and it must be
named as such. But it is **within-run escalation**: no image signature, no cache, no
carry-over between runs. It occupies Loop 1's territory, not Loop 2's.

This is recorded now so the Loop 2 evaluation cannot later mistake it for cross-image
learning.

---

## 5. Relationship to `agentic_supervisor.py` — `RELATIONSHIP UNPROVEN`

| | `GeometryCoachV2` | `agentic_supervisor.py` |
|---|---|---|
| Provenance | **`LTB`** | **`VS`** |
| Ever in the other repo? | never in VS | **never in LTB** (verified across all refs) |
| Shape | 4 rules + ownership gate + budget | 7 agents each returning `AgentVerdict` |
| Status | live, default-on | sandbox-only |
| **imports `cv2`** | **no — 0 call sites** | **yes — 17 call sites** |
| **Operating domain** | **scores + millimetres** | **raster / masks directly** |

They resemble each other functionally. That is not evidence of derivation, and none was
found: **no shared file, no shared commit, no import in either direction.**

**And mechanically they are not the same kind of system.** This is stronger than
"relationship unproven" — it is a positive divergence. The sandbox supervisor inspects
pixels itself: `ContextAgent._detect_image_type(image: np.ndarray)`,
`BackgroundAgent._detect_holes(mask)`, `_evaluate_edge_quality(mask)`. The production coach
inspects **no pixels at all** (§4.4); it judges normalised scores against millimetre-space
instrument priors and re-tasks pixel workers.

So the honest statement is not "two implementations of the same idea, one live and one
incubating." It is: **two closed-loop designs that share a control topology and disagree
about what the controller is allowed to look at.** Any future attempt to "graduate" the
sandbox supervisor into production, or to treat it as the mature form of the coach, would
be swapping a spec-domain controller for a pixel-domain one — a change of kind, not a
change of maturity.

---

## 6. What the three-loop document says, versus the code

| Claim in `THREE_LOOP_ARCHITECTURE_REFRAMED.md` | Evidence |
|---|---|
| Loop 1 "PARTIAL — Scale validation only" | **Understated.** Scale validation is one gate; the coach is a full bounded retry system with 4 rules and a monotonic improvement gate |
| "5-check voting system NOT IMPLEMENTED" | True as stated (no 5-check voter), but a **rules-based retry system** occupies that role in production |
| "Fallback retry logic NOT IMPLEMENTED" | **False.** `body_retry_profiles` / `contour_retry_profiles` with per-attempt escalation are exactly fallback retry logic |
| Loop 1 governance: "improvements must not alter `restored_baseline`" | not evaluated in this checkpoint |

The document was written **18 days after** the coach shipped and does not describe it.

---

## 7. What this checkpoint does **not** establish

- End-to-end extraction output on the cuatro PDF (`WITNESS_INCOMPLETE_TIMEBOX`).
- Whether the coach's reruns improve results — reachability was witnessed, **quality was not**.
- What `blueprint_orchestrator.py` bypassed. The seam is in scope but was not traced in this
  checkpoint; it belongs with the Loop 2 pass or a dedicated one.
- Loop 2 and Loop 3. Not evaluated, by instruction.
- The 37 `BOTH` files are counted, not diffed. Whether they are byte-identical,
  fork-diverged, or independently written is **unestablished**.

---

## 8. Appendix A — 157-path census

Machine-readable: `census_pixel.json` (path, first-seen date, first-seen commit, first-seen
subject, state, sandbox paths, relocation targets).

State is assigned by **positive evidence**: `LIVE` requires the path to exist at
`origin/main`; `MIGRATED_TO_SANDBOX` requires a matching basename in `vectorizer-sandbox`;
`DELETED` requires absence from both. No state is assigned from grep-absence alone.

**Census caveat, recorded rather than silently handled:** the two repositories symlink each
other through `docs/audit-sources/`, producing unbounded recursion
(`vectorizer-sandbox/docs/audit-sources/luthiers-toolbox/docs/audit-sources/vectorizer-sandbox/...`)
until Windows refuses to resolve the path. The walker prunes `audit-sources` and does not
follow symlinks. This is not only a crash guard — following those links would import each
repo's entire tree into the other's index and destroy the `LTB`/`VS`/`BOTH` distinction the
census exists to make.

`BOTH` is decided by **basename**, which is deliberately conservative: it over-reports
shared identity rather than under-reporting it, so no file is wrongly claimed as
repo-exclusive. Confirming true `BOTH` requires content diffing, which §7 lists as
outstanding.

---

## 9. Checkpoint

```text
LOOP 1        FOUND, LIVE, DEFAULT-ON, PREDATES ITS OWN LABEL
              GeometryCoachV2 (LTB, 2026-03-15, 50123379)

LOOP 2        NOT EVALUATED
LOOP 3        NOT EVALUATED

STOP FOR OWNER REVIEW BEFORE EVALUATING LOOPS 2 AND 3
```
