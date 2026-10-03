# VECTORIZER-CI-BOUNDARY-001 — what made default API CI slow, and the Cuatro pair

**Order:** VECTORIZER-CI-BOUNDARY-001. **Base:** `aaf38e4a0437b20d2ad4191f06cb7368a348f9c7`
(`origin/main`, merge of PR #424). **Branch:** `cursor/vectorizer-ci-boundary-001`.

This increment is test, workflow and evidence only. It changes no vectorizer algorithm, output,
threshold, fixture or manufacturing authority, retires nothing, and deletes, moves or rewrites no
DXF. It stops at a draft PR.

## Answers

| Question | Answer | Where |
|---|---|---|
| Which test produced the ~266k entity count? | The two Melody Maker conversions in `tests/test_text_masking_regression.py`: `test_melody_maker_with_text_masking`, `test_melody_maker_without_text_masking`, and `test_entity_count_reduction` (which repeats both). Every CI conversion wrote **266,359** `LINE` entities from 743 contours. Reproduced locally to the entity on the unmasked run | `TEST_RUNTIME_CENSUS.md` |
| Was it the OCR-failure ellipse test? | **No.** That test emits **1,116** entities in about 3 s, identically on CI and locally (twice). It is cleared as a bounded contract test | `TEST_RUNTIME_CENSUS.md` |
| Why was it in default CI? | Core CI runs `pytest -q` with no marker filter and `pytest.ini` deselects nothing, so `@slow` ran. The Melody Maker PDF is committed, so the tests ran rather than skipped. API Verify runs the same tests a second time | `CI_REACHABILITY.md` |
| What was separated, and where does it run now? | The five tests in `test_text_masking_regression.py`, via a new `vectorizer_regression` marker. Default CI excludes only that marker; the new non-required `vectorizer-regression.yml` runs exactly those five | `CI_REACHABILITY.md` |
| Is the OCR-failure contract still fully exercised? | Yes. The real `convert_enhanced` call, DXF emission, `DEGRADED` and `text_detection_failed` assertions are unchanged; one ceiling assertion was added (`line_count <= 5_000`) with no converter cap | `services/api/tests/test_text_masking.py` |
| Why do two identical Cuatro DXFs exist? | Both entered git together in one unrelated 4,553-file commit, `8d91c4c7`, as copies of a file created on Google Drive on 2026-03-06. No record explains two copies | `CUATRO_PROVENANCE.md` |
| Which is the system witness and which the plan-package artifact? | **Unresolved** (`ROLE_UNRESOLVED` for both). The audit that names the 128,997-entity anchor names it by filename only. Neither file is related to the CI delay | `CUATRO_PROVENANCE.md` |
| How does this relate to VEC-ROOT-001? | It does not duplicate it. None of the separated tests implements a VEC-ROOT-001 §8 criterion. The §8 harness, `c8ad3ae4`, is an unmerged artifact on `vec-root-001-harness` and is not touched | `SANDBOX_BOUNDARY.md` |
| What comes next? | One adjudication, named and not executed | `ADJUDICATION.md` |

## What changed

| File | Change |
|---|---|
| `services/api/tests/test_text_masking.py` | one ceiling assertion on the ellipse contract test |
| `services/api/tests/test_text_masking_regression.py` | module marker `vectorizer_regression`; a module-scoped fixture that runs each Melody Maker conversion once (four conversions become two); optional metrics file. Every assertion and print kept |
| `services/api/pytest.ini` | registers the marker (`--strict-markers` is on). `addopts` unchanged |
| `.github/workflows/core_ci.yml` | `pytest -q -m "not vectorizer_regression"` |
| `Makefile` | `api-test` uses `API_TEST_MARKERS ?= not vectorizer_regression` (overridable) |
| `.github/workflows/vectorizer-regression.yml` | new, non-required: manual + path triggers, no schedule, 45 min timeout, uploads compact metrics |
| `scripts/ci/vectorizer_regression_summary.py` | summarizes the run; reports skips as **NOT COVERED** |
| `scripts/investigations/generate_vectorizer_ci_boundary.py` | renders the census Markdown from its JSON |
| `services/api/tests/vectorizer/` | evidence-integrity tests |
| this directory | evidence |
| `.cbsp21/patches/vectorizer-ci-boundary-001.json` | manifest |

## Corrections made during this order

Recorded so they do not travel:

1. The handoff attributed the ~266k count provisionally to the ellipse test. It was the Melody Maker
   tests (frozen decision 1 held: not assumed, measured).
2. The handoff expected PR #424 to be open. It was already merged, and is the base of this branch.
3. `body_lexicon.md` was first reported as not locatable, then as on no remote branch. Both were
   wrong; it is pushed to vectorizer-sandbox on `ibg-grammar-001` (`SANDBOX_BOUNDARY.md`).
4. Retain/replace/retire records were first reported as absent. No record uses those words, but
   `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md` is a committed lifecycle-disposition registry
   and is cited.
5. A first local measurement pass ran in the worktree after the regression module had been edited.
   It was discarded; every baseline in the census comes from an unmodified detached checkout of the
   base commit.
