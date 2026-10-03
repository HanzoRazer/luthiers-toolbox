# CI reachability — which lanes ran the real-plan vectorizer tests

Traced on `origin/main` `aaf38e4a0437b20d2ad4191f06cb7368a348f9c7`, against Core CI run
`37135089404` and API Verify run `37135089420` (both on that commit, both green).

## Before this change

| Lane (check name) | Workflow → command | Required? | Includes `@slow` | Runs the Melody Maker PDF | Parses the Cuatro DXFs | Job timeout | Entity / resource budget |
|---|---|---|---|---|---|---|---|
| **API Tests** (Core CI) | `core_ci.yml` → `cd services/api && python -m pytest -q` | yes, via `Core CI Summary` | **yes** — no `-m`, and `pytest.ini` has no marker filter | **yes** — 3 tests, 4 conversions | no (path enumeration only) | none set (GitHub default 360 min) | none |
| **api-verify** | `api_verify.yml` → `make api-verify` → `pytest -q tests/ app/tests/` | **no** | **yes** | **yes** — the same 3 tests | no | none set | none |
| **api-smoke** (`API Tests` workflow) | `api_tests.yml` → `pytest -q app/tests/` | yes | n/a — `app/tests/` has none of these tests | no | no | none set | none |
| DXF Asset Validation / DXF Validation Gate | `dxf_validation*.yml` → `scripts/validate_dxf_assets.py` | no | n/a | no | **yes, but only when a `.dxf` under `instrument_geometry/` changes** | — | — |

`api-verify` triggers on `services/api/**`, `packages/client/**`, `scripts/**`, `Makefile`, so
most API pull requests ran the Melody Maker conversions **twice** — once per lane.

Timings from those runs: Core CI `API Tests` pytest step 1600.37 s (`9362 passed, 62 skipped`);
API Verify 1578.54 s. The three Melody Maker tests account for 1,148 s of the 1,562 s spanned by
test-start timestamps in the Core CI log (73%). The next-slowest test took 13.4 s.

## The other `@slow` tests

`@pytest.mark.slow` is also on `tests/test_adaptive_router.py:462` (`TestAdaptiveIntegration`) and
`tests/test_geometry_router.py:358` (`TestGeometryIntegration`): four router integration tests
taking 0.1 s in total on CI. Excluding `slow` wholesale would have dropped them from default CI for
no time saved. **The default expression therefore excludes only `vectorizer_regression`**, a
deviation from the handoff's example (`not slow and not vectorizer_regression and not
vectorizer_stress`). No `vectorizer_stress` marker is introduced: no test needs one.

## After this change

| Lane | Command | Effect |
|---|---|---|
| API Tests (Core CI) | `python -m pytest -q -m "not vectorizer_regression"` | deselects exactly the 5 tests in `tests/test_text_masking_regression.py` |
| api-verify | `make api-verify` → `pytest -q -m "$(API_TEST_MARKERS)" …`, `API_TEST_MARKERS ?= not vectorizer_regression` | same 5 deselected; `make api-test API_TEST_MARKERS=""` restores them locally |
| api-smoke | unchanged | — |
| **Vectorizer Regression** (new) | `vectorizer-regression.yml` → `pytest -m vectorizer_regression --no-cov` | runs exactly those 5; not required; `workflow_dispatch` + path triggers; no schedule; 45 min timeout |

`pytest.ini` `addopts` is unchanged, so a developer's bare `pytest` still collects everything.

## What the new lane covers, honestly

| Test | In the new lane |
|---|---|
| `test_melody_maker_with_text_masking` | runs |
| `test_melody_maker_without_text_masking` | runs |
| `test_entity_count_reduction` | runs — but its assertion is vacuous (`TEST_RUNTIME_CENSUS.md`, finding F-2) |
| `test_cuatro_with_text_masking` | **collected, always skipped** — `cuatro puertoriqueño.pdf` is not committed |
| `test_cuatro_without_text_masking` | **collected, always skipped** — same |

The summary step reports the two skips as **NOT COVERED**. This lane provides **no Cuatro
regression coverage**.

On CI runners EasyOCR is not installed (`EasyOCR not available` in the Core CI log), so the
"with text masking" conversion does no masking and is identical to the unmasked one (finding F-3).
