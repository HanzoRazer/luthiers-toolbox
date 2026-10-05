# F-3 — failure mimics success

**Classification: `SIGNATURE_GAP`.**

## Code flow

`EdgeToDXF.convert_enhanced` defaults `mask_text=True`. When that flag is set it calls `detect_text_regions`.

`_get_easyocr_reader` treats `ImportError` as "EasyOCR not available" and returns `None`. `detect_text_regions` then returns `[]`. Its docstring states that an empty list covers both "OCR is unavailable" and "OCR ran and found no text," and that both mean there is nothing to mask.

`TextDetectionError` is the path that sets `text_detection_failed` and `ConversionStatus.DEGRADED` (BR-037). A missing library does not raise that error. `text_detection_failed` stays false, and the result status is `ConversionStatus.SUCCESS`.

Requested capability: mask text before gap closing. Actual behavior when EasyOCR is absent: no regions are masked, and the conversion is reported as success.

## Frozen counts

From `TEST_RUNTIME_CENSUS.json` on this base. Not remeasured here.

| Run | Entities |
|---|---|
| CI, EasyOCR absent, `mask_text=True` (T-02) | 266,359 |
| CI, EasyOCR absent, `mask_text=False` (T-03) | 266,359 |
| Local, EasyOCR present, `mask_text=True` (T-02) | 223,427 |
| Local, EasyOCR present, `mask_text=False` (T-03) | 266,359 |

This environment has no EasyOCR (`find_spec("easyocr")` is `None`). That confirms the missing-library condition. It was not changed, and the conversion was not run again.

## Detector results

| Scan | Result for F-3 |
|---|---|
| Normal / full repository | Same run as F-2. Exit 2. Two `hollow_guarantee` findings, both on `client_lint_build.yml`. No finding on `edge_to_dxf.py` or `blueprint_orchestrator.py` whose message mentions EasyOCR, `mask_text`, or a success status after a skipped mask. |
| Direct, `edge_to_dxf.py` | CLI scans the parent `services/photo-vectorizer/`. Exit 2. 211 findings, `hollow_guarantee` 0. Complexity and broad-`except` findings name `edge_to_dxf.py` at other lines (116, 545, 1361, 1768, 2631, and several complexity sites). The `ImportError` handler and the `SUCCESS` assignment are not among them. |
| Direct, `blueprint_orchestrator.py` | CLI scans the parent `services/api/app/services/`. Exit 2. 161 findings, `hollow_guarantee` 0. Nothing describes F-3. |
| Analyzer protocol with both files in the `files` list | Still only the two workflow findings. The Python files are not the scan scope of `HOLLOW_GUARANTEE_001`. |

The rule's own metadata labels its workflow findings `family: III (failure mimics success)`. That family name is the F-3 class, and the implemented signature is still a workflow step whose exit cannot fail. Silent `SUCCESS` after an optional import returns `None` is a different shape.

## Why the other labels do not fit

- `REACH_GAP`: direct scans of both controlling files' parent directories do not report F-3.
- `CONFIGURATION_GAP`: `HollowGuaranteeAnalyzer` is in `_DEFAULT_ANALYZERS` and produced findings on this tree. No disabled OCR/success rule was found.
- `DETECTED_UNDISPOSITIONED`: F-3 is not in the 8,111-finding report.
- `TOOL_UNAVAILABLE`: the Family III rule exists, its self-tests passed, and it ran. It does not recognize this defect.
