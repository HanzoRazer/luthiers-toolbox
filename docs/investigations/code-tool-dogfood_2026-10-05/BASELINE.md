# Baseline

## Merges and tree

| Check | Result |
|---|---|
| PR #425 | Merged. Merge commit `5e3be0694333e04ff0da6db38a55d0aace796349`. Ancestor of current `main`. |
| PR #426 | Merged. Merge commit `6ea31376d04b0b6f7961144f6edb725b3db49edb`, which is the tip of `origin/main` used here. |
| Branch point | `6ea31376d04b0b6f7961144f6edb725b3db49edb` |
| Worktree at branch creation | Clean. |
| Open pull requests | None. No overlap on detector code, the F-2/F-3 sources, this bundle, or a CBSP21 manifest. |

## F-2 / F-3 paths

The order's expected test path `services/api/tests/core/test_text_masking_regression.py` is not in the tree. The test that contains F-2 is `services/api/tests/test_text_masking_regression.py`.

| Path | Git blob | Content SHA-256 | Role |
|---|---|---|---|
| `services/api/tests/test_text_masking_regression.py` | `0bbc72d56eac600a695105976578cb46930b5c1f` | `6f256e19226f8b06f75e882dfc382decd1e9135051d6306d53aee9b8289dfd03` | F-2 assertion; F-3 regression caller |
| `services/photo-vectorizer/edge_to_dxf.py` | `c847c04365d37230d7d43d8e872909fbbee942cd` | `8809c15c0af9e0b53bc2e78dd26a772793d5760623b55ef09b80203a931a1fae` | OCR availability, masking, `SUCCESS` / `DEGRADED` |
| `services/api/app/services/blueprint_orchestrator.py` | `5418ce3fba5fdc51cf88d545113a26db6af3d23a` | `06adc5090bca839a4b38e9ab368817105f71d6932fb8e4b36201f04505d22093` | `BlueprintResult` has no `entity_count`; `DXFArtifact.entity_count` does |

## Detector availability and ownership

The detector is not implemented in this repository. It is `HanzoRazer/code-analysis-tool` at `c2c1ea8fb7abc1221f9c837de645cde1d7b8d61c` (`code_audit` 0.1.0). This increment did not edit that repository.

This repository does not invoke `code-audit` from any workflow. That is recorded as topology, not as the classification: the tool was run here in its own default mode, and that run still missed both fixtures.

An older `scripts/code_quality` package is described in archived handoffs and is not the hollow-guarantee detector. It was not the tool under test.

## What was not done

- No edit under `services/photo-vectorizer/`, `services/api/app/`, or `services/blueprint-import/`.
- No edit of `services/api/tests/test_text_masking_regression.py`.
- EasyOCR is not installed in the environment used for this run (`importlib.util.find_spec("easyocr")` is `None`). It was left that way.
- The 266,359-entity Melody Maker conversion was not repeated. Counts are the frozen census in `docs/investigations/vectorizer-ci-boundary_2026-10-03/TEST_RUNTIME_CENSUS.json`.
