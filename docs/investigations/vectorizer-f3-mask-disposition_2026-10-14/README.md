# F-3 masking disposition

F-3 was a requested text mask that still reported success. `detect_text_regions` returned `[]` when EasyOCR was missing, and `convert_enhanced` treated that the same as "no text found."

## What this repair does

The conversion result now carries `text_masking`. Enhanced acceptance for a degraded mask lives in `blueprint_text_masking.py`, so the orchestrator and extract modules stay at their file-size baseline. Bounding boxes are measured with plain coordinates because a long pytest session reimports NumPy and `ndarray.astype` then raises `_NoValueType`.

| Field | Meaning |
|---|---|
| `requested` | `mask_text` was true |
| `provider_available` | EasyOCR imported |
| `attempted` | `readtext` ran |
| `applied` | A text region was masked |
| `diagnostic_code` | One of the codes below, or null when masking was not requested |

| Code | Status |
|---|---|
| `OCR_PROVIDER_UNAVAILABLE` | `DEGRADED` |
| `OCR_INITIALIZATION_FAILED` | `DEGRADED` |
| `OCR_EXECUTION_FAILED` | `DEGRADED` |
| `OCR_NO_TEXT_DETECTED` | `SUCCESS` |
| `TEXT_MASK_APPLIED` | `SUCCESS` |

`mask_text=False` stays `SUCCESS` and does not probe OCR. No text detected is a completed pass. A degraded pass still writes the DXF. Enhanced blueprint acceptance is `review` with `ok` false in that case, so the file is not an accepted manufacturing result. The enhanced HTTP response reports `status=DEGRADED` and the same disposition. Existing response fields stay in place.

The Melody Maker regression asserts `masked_count < unmasked_count` only when that run reports `applied=True`. It stays on the `vectorizer_regression` marker. Default API CI is unchanged. `CODE-TOOL-SIGNATURES-004` stays in `HanzoRazer/code-analysis-tool`.

The dogfood scan pins for `edge_to_dxf.py` and `blueprint_orchestrator.py` are stored next to the regression pin. `DETECTOR_RUNS.json` was not rewritten and `code_audit` 0.1.0 was not rerun.

## What this repair does not do

It does not install EasyOCR, change the dedicated workflow, or put the Melody Maker conversion into default API CI. It does not change how `entity_count` is computed.
