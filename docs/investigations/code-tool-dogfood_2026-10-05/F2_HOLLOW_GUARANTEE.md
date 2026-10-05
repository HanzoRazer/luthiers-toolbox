# F-2 — hollow guarantee

**Classification: `SIGNATURE_GAP`.**

## Code flow

`TestTextMaskingComparison.test_entity_count_reduction` in `services/api/tests/test_text_masking_regression.py` loads a `BlueprintResult` from `melody_maker_run` and then:

```python
masked_count = getattr(result_masked, "entity_count", 0)
unmasked_count = getattr(result_unmasked, "entity_count", 0)
assert masked_count <= unmasked_count + 1000
```

`BlueprintResult` (`services/api/app/services/blueprint_orchestrator.py`) has no `entity_count` attribute. The count the rest of that module prints is `result.dxf.entity_count` on `DXFArtifact`. `getattr` therefore substitutes the default `0` for both sides. `0 <= 0 + 1000` is true for every result, including a result that increased the entity count.

## Reproduction in this increment

Constructing `BlueprintResult(ok=True)` and evaluating the same `getattr` expression:

| Observation | Value |
|---|---|
| `hasattr(result, "entity_count")` | `False` |
| both `getattr` results | `0` and `0` |
| `result.dxf.entity_count` | `0` |
| `masked <= unmasked + 1000` | `True` |

The Melody Maker conversion was not rerun. The census already records that this test's real counts, when read at `result.dxf.entity_count`, are 223,427 masked and 266,359 unmasked locally, and 266,359 for both on CI. The assertion never reads those fields.

## Detector results

| Scan | Result for F-2 |
|---|---|
| Normal / full repository (`python -m code_audit <repo> --json`) | Exit 2 (confidence 0/100, scan completed). 8,111 findings, of which 2 are `hollow_guarantee`. Both are `.github/workflows/client_lint_build.yml` lines 54 and 68. Zero findings whose message mentions this test's `entity_count` fallback. |
| Direct (`python -m code_audit <test-file> --json`) | The CLI scans the parent directory `services/api/tests/`, not the single file. Exit 2. 1,714 findings. `hollow_guarantee` count 0. One finding names the file (`context_pinned_hash` on `melody_maker_run`); it is not the hollow assertion. |
| Analyzer protocol `HollowGuaranteeAnalyzer.run(repo, [this file, ...])` | The `files` argument is ignored. Same two workflow findings as the repository scan. The test file is not opened. |

`HOLLOW_GUARANTEE_001` is enabled in the default analyzer list. Its signatures are `continue-on-error: true` and a swallowed exit on a verification command inside `.github/workflows`. A Python `getattr` default that makes an assertion tautological is not one of those signatures.

## Why the other labels do not fit

- `REACH_GAP` would require a direct scan to report this defect. The direct scan does not.
- `CONFIGURATION_GAP` would require a suitable rule that is disabled. The hollow rule ran.
- `DETECTED_UNDISPOSITIONED` would require an existing finding for this assertion. There is none.
- `TOOL_UNAVAILABLE` would require the detector or its rule to be missing. Self-tests: 18 passed. The rule fired on `client_lint_build.yml`.
