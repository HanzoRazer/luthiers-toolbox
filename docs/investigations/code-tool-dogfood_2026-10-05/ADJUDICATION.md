# Adjudication

## Disposition

| Fixture | Disposition | Successor |
|---|---|---|
| F-2 | `SIGNATURE_GAP` | `CODE-TOOL-SIGNATURES-004` in `HanzoRazer/code-analysis-tool` |
| F-3 | `SIGNATURE_GAP` | `CODE-TOOL-SIGNATURES-004` in `HanzoRazer/code-analysis-tool` |

One disposition each. Both are the same class for different reasons, and the repair belongs in the detector's repository.

## Why this is a signature gap

`HOLLOW_GUARANTEE_001` is loaded, its own tests pass (18), and on this tree it reports the two `continue-on-error: true` verification steps in `.github/workflows/client_lint_build.yml`. That is the signature it was built for, including the Family III label "failure that mimics success."

F-2 is a test assertion that cannot fail because `getattr` invents `0` for an attribute `BlueprintResult` does not have. F-3 is a requested mask that is skipped when EasyOCR cannot be imported, while `convert_enhanced` still returns `SUCCESS`. The rule never reads either shape. Pointing the CLI at the files scans their parent directories and still does not report them. Passing the files into `HollowGuaranteeAnalyzer.run` does not change its workflow-only scope.

A reach repair would put the current tool on this repository's CI. The default scan of the whole repository already misses both fixtures, so that wiring would stay green on F-2 and F-3. Configuration is not the gap: the rule is not disabled. Disposition is not the gap: the findings that do exist are about `client_lint_build.yml`, not these two defects. The tool is available.

## Cross-repository repair order

Do not implement the new signatures in `luthiers-toolbox`.

Owner repository: `HanzoRazer/code-analysis-tool`.

The signature order should add recognition, inside that tool, for:

1. A test assertion whose compared values come from `getattr` (or an equivalent default) on an attribute the result type does not define, where the default makes the comparison hold for every value.
2. A requested optional capability whose import failure returns an empty result and whose caller still reports success rather than a degraded status.

Those are the shapes. This adjudication does not add the rules, does not tune them to these filenames, and does not vendor the detector.

After that signature order exists and is shown to flag these two fixtures, a separate reach order can decide whether `luthiers-toolbox` CI should invoke the tool. Not before.

## What this decision does not authorize

- Repairing F-2 or F-3.
- Editing `edge_to_dxf.py`, the orchestrator, or the regression test.
- Promoting `CleanupMode.ENHANCED` or resolving F-5.
- Starting VECTORIZER-ADJUDICATION-001. That adjudication waits until this order's detector repair has landed.
