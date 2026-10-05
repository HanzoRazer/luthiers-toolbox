# CODE-TOOL-DOGFOOD-003 — why the code tool missed F-2 and F-3

**Question.** Run the existing code-quality detector, unchanged, against two confirmed vectorizer defects and classify each miss.

**Scope.** Evidence only. No production change, no vectorizer repair, no detector repair, no merge.

**Base.** `6ea31376d04b0b6f7961144f6edb725b3db49edb` (merge of PR #426). PR #425 is merged at `5e3be0694333e04ff0da6db38a55d0aace796349` and is an ancestor of that tip.

**Branch.** `cursor/code-tool-dogfood-003-ffa7`. The order named `cursor/code-tool-dogfood-003`. Platform branch policy requires the `-ffa7` suffix, so that suffix was added and the recommended name was not used.

## Detector

| Field | Value |
|---|---|
| Tool | `code-audit` (`code_audit` 0.1.0) |
| Owner | `HanzoRazer/code-analysis-tool` @ `c2c1ea8fb7abc1221f9c837de645cde1d7b8d61c` |
| Entry point | `python -m code_audit` (`code_audit.__main__:main`) |
| Rule that matches the requested classes | `HollowGuaranteeAnalyzer` 1.0.1, rule `HOLLOW_GUARANTEE_001` |
| What that rule actually matches | A GitHub Actions verification step under `continue-on-error: true`, or the same command with `\|\| true` / `\|\| exit 0` / `; true` |

The analyzer docstring calls this Family III, "failure that mimics success." There is no separate `FAILURE_MIMICS_SUCCESS` rule id. The rule does not read Python tests or the OCR status path.

## Results

| Fixture | Classification | What the scan did |
|---|---|---|
| F-2 hollow guarantee | `SIGNATURE_GAP` | The default repository scan and the direct scan of the test's parent directory both completed. Neither reported the `getattr(..., 0)` assertion. |
| F-3 failure mimics success | `SIGNATURE_GAP` | The same scans completed. Neither reported "EasyOCR missing, `mask_text=True`, status stays `SUCCESS`." |

The default repository scan did emit two `hollow_guarantee` findings. Both are `client_lint_build.yml` (`vue-tsc` and `ESLint` under `continue-on-error: true`). Those are a different defect. They are not F-2 or F-3.

## Next order

`CODE-TOOL-SIGNATURES-004`, as a cross-repository repair in `HanzoRazer/code-analysis-tool`. Adding the signatures in this repository would create a second detector. Wiring the current tool into this repository's CI would still miss both fixtures, because the full default scan already misses them.

## Confirmation

Neither F-2 nor F-3 was repaired. No `xfail`, skip, warning, or corrected assertion was added. EasyOCR was not installed. The Melody Maker conversion was not rerun.
