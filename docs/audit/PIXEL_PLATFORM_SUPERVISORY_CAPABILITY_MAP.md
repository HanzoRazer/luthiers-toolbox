# Pixel Platform — Supervisory Capability Map

**Date:** 2026-08-28
**Base:** `origin/main` @ `9d5d9001`
**Checkpoint 2.** Companion to `PIXEL_PLATFORM_LOOP1_FORENSIC_AUDIT.md`, which stays fixed
as checkpoint 1.
**Question answered:** what control, arbitration, memory, replay, learning, correction and
reconstruction capabilities exist around the pixel workers; which exchange information;
which are isolated.

> **Naming discipline.** Capabilities are named for what they do. Loop vocabulary is not
> applied until §8, and only as a mapping question, not as a framing.
>
> **Anchor discipline.** `GeometryCoachV2` is not the origin of this map. It appears where
> the exchange graph puts it.

**Evidence classes, never merged:** production call graph = **actual** wiring · tests =
**intended** contract · commit messages/docs = **stated** architecture.

---

## 0. Method correction, recorded before any finding

The first exchange scan reported `blueprint_orchestrator` as having **no importer at all**.
That was a defect in my scanner, not a fact: it recorded only the first dotted component of
each import, so `from app.services.blueprint_orchestrator import X` was filed under `app`.
Corrected to record every component plus imported symbol names; `blueprint_orchestrator`
has **2** production importers.

The corrected matcher deliberately over-matches. This map's most consequential outputs are
claims that something has **no** consumer, and in that direction a false negative — claiming
isolation that is not real — is far more damaging than a false positive. Every isolation
claim below survived the corrected pass and was then confirmed by direct grep.

---

## 1. The natural joints

Seven distinct responsibilities exist. None of them is named "loop" anywhere in the code.

| # | Joint | Responsibility | Modules |
|---|---|---|---|
| 1 | **Staging** | wrap a pixel worker so its result is typed, scored and restorable | `body_isolation_stage`, `contour_stage` |
| 2 | **Scoring / evidence typing** | convert a raster outcome into dimensionless signals + issues | `body_isolation_result` |
| 3 | **Metrological authority** | judge a result against millimetre-space instrument-family priors | `geometry_authority` |
| 4 | **Control / bounded retry** | decide whether to re-task a stage, with which parameters, and when to stop | `geometry_coach`, `geometry_coach_v2` |
| 5 | **Arbitration** | choose *which* candidate contour is the body | `elect_body_contour_v2` and `elect_body_contour_against_expected_outline` (inline in `photo_vectorizer_v2`), `contour_election` (unadopted) |
| 6 | **Replay / regression memory** | preserve prior executions and re-run them for comparison | `replay_execution`, `replay_fixture_loader`, `replay_objects`, `replay_summary` |
| 7 | **Telemetry / observation** | record what happened, with no return path into control | `grouping_telemetry`, `contour_debug_overlay`, `live_test_run`, `live_test_summary` |

Two candidates sit outside these joints: `multi_view_reconstructor` (cross-evidence
reconstruction, CLI + tests only) and `march_pipeline_restore` (state restoration, one
production consumer).

**No learning joint exists.** Nothing in the pixel platform adapts future behaviour from
past outcomes. Joint 6 is *memory* — it preserves and compares — and joint 7 is *observation*.
Neither feeds back. This is stated as a finding, not as a gap in the search; see §5.

---

## 2. Exchange table

`prod_in` counts production importers; `test_in` counts test importers. They are never
summed.

| Module | Joint | prod_in | test_in | out | Exchange state |
|---|---|---:|---:|---:|---|
| `body_isolation_result` | scoring | 7 | 12 | 0 | `LIVE_EXCHANGE` — the platform's most-consumed type |
| `vectorizer_phase3` | worker | 8 | 3 | 1 | `LIVE_EXCHANGE` |
| `photo_vectorizer_v2` | worker + arbitration | 6 | 13 | 6 | `LIVE_EXCHANGE` |
| `geometry_coach_v2` | control | 4 | 10 | 4 | `LIVE_EXCHANGE` |
| `contour_stage` | staging | 3 | 3 | 1 | `LIVE_EXCHANGE` |
| `body_isolation_stage` | staging | 3 | 5 | 1 | `LIVE_EXCHANGE` |
| `geometry_authority` | authority | 2 | 3 | 0 | `LIVE_EXCHANGE` |
| `replay_objects` | replay memory | 2 | 1 | 2 | `LIVE_EXCHANGE` (within replay only) |
| `grouping_telemetry` | telemetry | 2 | 0 | 0 | **`WRITE_ONLY`** — consumed by no control path |
| `blueprint_orchestrator` | orchestration | 2 | 0 | 0 | `LIVE_EXCHANGE` |
| `geometry_coach` (v1) | control | 1 | 1 | 2 | `READ_ONLY` — imported solely by v2 |
| `contour_plausibility` | validation | 1 | 2 | 0 | `LIVE_EXCHANGE` — sole consumer is `APP:blueprint_clean` |
| `replay_fixture_loader` | replay memory | 1 | 5 | 2 | `READ_ONLY` (within replay only) |
| `replay_summary` | replay memory | 1 | 2 | 0 | `READ_ONLY` (within replay only) |
| `march_pipeline_restore` | restoration | 1 | 0 | 0 | `LIVE_EXCHANGE` |
| `contour_debug_overlay` | telemetry | 1 | 0 | 0 | **`WRITE_ONLY`** |
| `calibration_integration` | calibration | 1 | 0 | 0 | `LIVE_EXCHANGE` — via `APP:constants.py`, behind `CALIBRATION_AVAILABLE` |
| `contour_election` | **arbitration** | **0** | 1 | 0 | **`NO_PRODUCTION_CONSUMER`** — see §4 |
| `replay_execution` | replay driver | **0** | 1 | 6 | **`TEST_DRIVEN_ONLY`** — see §5 |
| `multi_view_reconstructor` | reconstruction | **0** | 1 | 1 | `CLI_PLUS_TESTS` — has `__main__` |
| `live_test_run` | telemetry | **0** | **0** | 1 | **`NO_CONSUMER_FOUND`** — and no `__main__` |
| `live_test_summary` | telemetry | **0** | **0** | 1 | **`NO_CONSUMER_FOUND`** — and no `__main__` |

---

## 3. The architectural event was a six-day burst, not a single component

```text
2026-03-14 19:51  7d5d86c0  Patch 17 -- ContourMerger, elect_body_contour_v2 (X-extent
                            guard), filter_coin_by_position. Arbitration and validation
                            exist here, INLINE, with measured before/after error rates.
                            live_test_summary.py born.
2026-03-15 00:18  c958ccfa  "extract Stage 8 into ContourStage + GeometryCoachV1"
                            -> contour_stage.py, geometry_coach.py
2026-03-15 13:09  50123379  V2 coaching pipeline -> geometry_coach_v2, geometry_authority,
                            body_isolation_stage, body_isolation_result
2026-03-16 10:43  3a24683e  live_test_run.py
2026-03-17 18:30  ebfc8b8a  contour_election.py, contour_plausibility.py
2026-03-18 02:14  8c553069  replay_summary.py
2026-03-19 22:33  bfffc7af  replay framework -> replay_execution, _fixture_loader, _objects
2026-03-23 3d8cfa0d         multi_view_reconstructor.py
2026-04-12 9cc92ba9         contour_debug_overlay.py
2026-04-19 3e75a7cb         march_pipeline_restore.py
2026-05-20 9eba933a         grouping_telemetry.py
```

**What existed "before GeometryCoachV2" is not nothing, and not a named layer.** Patch 17
(2026-03-14) already performed arbitration and validation — `elect_body_contour_v2`'s
X-extent guard rejects contours wider than `body_region.width * 1.30` — **inline in the
pipeline**. The March 15 commits did not invent supervision; they **extracted** it. v1's own
message says so: *"extract Stage 8 into ContourStage + GeometryCoachV1."*

The "before" state is therefore: **supervision present, unnamed, and not separable from the
worker it supervised.**

---

## 4. v1 → v2 is ancestry, and it is proven

Both coaches were born 2026-03-15, which is why checkpoint 1 declined to narrate evolution.
Git settles it:

```text
c958ccfa  2026-03-15 00:18:46   GeometryCoachV1
50123379  2026-03-15 13:09:22   GeometryCoachV2
git merge-base --is-ancestor c958ccfa 50123379  ->  TRUE
```

`c958ccfa` **is** an ancestor of `50123379`, ~13 hours earlier. This is **sequence, not
parallel introduction**. v1 survives today as `READ_ONLY`: its sole production importer is
v2, which imports `CoachDecision` from it — the older type is still the currency, while the
older controller is not.

## 5. Arbitration was extracted into a module and then not adopted

This is the sharpest finding in the map.

```text
photo_vectorizer_v2.py:2598   def elect_body_contour_v2(...)                  <- LIVE
photo_vectorizer_v2.py:....   def elect_body_contour_against_expected_outline <- LIVE
        consumed by contour_stage.py:337, :356, :370

contour_election.py:6         def elect_body_contour_with_ownership(...)      <- NO PRODUCTION CONSUMER
```

Three election functions exist. The two that run are the **inline** ones from Patch 17,
imported by `contour_stage` out of `photo_vectorizer_v2`. The one in the module actually
named `contour_election.py` is **ownership-aware** — it speaks the same vocabulary the coach
uses for its gate — and **nothing in production calls it**. Its only importer is a test,
`test_contour_election_ownership_gate.py`.

So the platform extracted its arbitration into a named, more capable module two days after
the coach landed, and then kept using the inline version. The intended contract (test) and
the actual wiring (production) disagree, and both are recorded rather than reconciled.

## 6. Isolation findings, as first-class results

- **`replay_execution` — `TEST_DRIVEN_ONLY`.** Six outbound edges, zero production
  importers, no `__main__`. A four-module regression-memory subsystem that only the test
  suite drives. It **preserves and compares** prior executions; it does not modify future
  behaviour. Calling it learning would be wrong.
- **`grouping_telemetry` and `contour_debug_overlay` — `WRITE_ONLY`.** Two production
  importers between them, zero outbound edges, no control path reads them. Information
  leaves the control system and does not return.
- **`live_test_run` / `live_test_summary` — `NO_CONSUMER_FOUND`.** No importer of any kind,
  and no `__main__`, so they are not CLI entry points either. `live_test_summary` (2026-03-14)
  is the **earliest** artifact in this whole map, and nothing reaches it today.
- **`multi_view_reconstructor` — `CLI_PLUS_TESTS`.** Has `__main__`, so "no production
  importer" does **not** mean orphaned; it is invocable, just not wired into the pipeline.

## 7. The correction pathways that exist

| Pathway | Mechanism | State |
|---|---|---|
| Automatic re-tasking | coach re-invokes stage runners with escalated params | **live, default-on** |
| Monotonic guard | retry cannot replace a better result with a worse one | live |
| Human escalation | `action = "manual_review_required"` appended to `result.warnings` | live, terminal |
| User-correction capture | `FeedbackSystem` / `TrainingDataCollector` (blueprint-import) | **`WIRED_FLAG_OFF`** — `enable_feedback=False` |

Only the last is a *learning* pathway, and it is switched off. The first three are control
and escalation: they change this run, and leave no trace that changes the next one.

---

## 8. Only now: does any cluster map to the loop vocabulary?

| Historical concept | Nearest real cluster | Fit |
|---|---|---|
| Loop 1 — intra-frame validation | joints 1+2+3+4 (staging → scoring → authority → control) | **partial, and larger than the label.** The real cluster spans four responsibilities and reasons in millimetres, not pixels |
| Loop 2 — cross-image learning | **nothing** | `strategy_cache`, `get_image_signature`, `try_all_strategies`, `pick_best` absent from both repos. Joint 6 (replay) occupies adjacent territory but is memory-for-comparison, not adaptation. **NOT ESTABLISHED** |
| Loop 3 — correction retraining | `FeedbackSystem` / `TrainingDataCollector` | present, wired, flag-off |
| — | **arbitration (joint 5)** | **the loop vocabulary never had a name for this**, and it is the joint with the clearest live/unadopted split |
| — | **telemetry (joint 7)** | no loop concept covers write-only observation |

Two of the seven joints the code actually contains have no counterpart in the three-loop
vocabulary at all. That is the strongest evidence yet that the vocabulary was fitted to the
system afterwards rather than describing it.

---

## 9. Not established

- Runtime confirmation that `contour_election` is unreachable — established statically and
  by grep, not by execution.
- Whether the inline `elect_body_contour_v2` and the module's
  `elect_body_contour_with_ownership` are behaviourally equivalent. Not diffed.
- Whether `grouping_telemetry`'s output is read by anything **outside** this repository.
- What `blueprint_orchestrator` bypassed relative to the photo path — still outstanding from
  checkpoint 1.
- Exchange media beyond import edges: shared mutable state, persisted-artifact
  producer→consumer pairs, and configuration signals were **not** traced. This map is an
  import/call-graph map, and calling it a full data-flow map would overstate it.

---

## 10. Checkpoint

```text
JOINTS FOUND        7  (staging, scoring, authority, control, arbitration,
                        replay memory, telemetry)
LEARNING JOINT      NONE
ISOLATED            live_test_run, live_test_summary          NO_CONSUMER_FOUND
                    contour_election                          NO_PRODUCTION_CONSUMER
                    replay_execution                          TEST_DRIVEN_ONLY
WRITE_ONLY          grouping_telemetry, contour_debug_overlay
v1 -> v2            ANCESTRY PROVEN (not parallel introduction)

STOP FOR OWNER REVIEW BEFORE ASSIGNING LOOPS 2 AND 3
```
