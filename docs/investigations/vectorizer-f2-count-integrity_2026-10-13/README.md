# F-2 count integrity

F-2 was a test that could not fail. `test_entity_count_reduction` read `result.entity_count`. `BlueprintResult` has no such attribute, so `getattr(..., 0)` made both sides zero and `0 <= 0 + 1000` passed.

## What this repair does

The Melody Maker regression now reads `result.dxf.entity_count` directly. A missing `dxf` or `entity_count` fails the test. Each run's already-emitted DXF is parsed with ezdxf, and the reported count must equal the `LINE` and `LWPOLYLINE` entities in modelspace. That check does not run another conversion.

The parse is deliberate. The orchestrator's encode stage derives `entity_count` by counting `"\nLINE\n"` substrings in the same bytes. A first draft of this repair repeated that substring count, which agrees with production by construction and so could not fail. A structured parse reads group-code pairs: a TEXT value or layer name spelled `LINE` is not an entity. A fast test pins this — it fails if the helper reverts to the substring rule. The pipeline writes CRLF line endings, which ezdxf reads as zero entities unless normalized, so the helper normalizes them first; a CRLF fast test pins that too.

The test is renamed `test_melody_maker_reports_entity_counts`. It reports the two counts. It does not assert that masking reduced them. Production does not yet say whether masking was applied. F-3 will add that disposition. Until then a strict `masked < unmasked` check would claim a runtime fact the result does not report.

The strict check exists only as a fast helper. It passes when `applied=True` and the masked count is smaller. Equal counts fail. `applied=False`, `applied=None`, or an omitted disposition refuse the comparison. Those tests use synthetic results. They do not convert Melody Maker.

The module fixture still computes each flag once. Masked and unmasked remain two conversions. The shared cache is the same function the fast test exercises.

## What this repair does not do

No change to `edge_to_dxf.py`, the orchestrator, result models, DXF generation, OCR installation, the vectorizer workflow, or default API CI. The real-plan tests stay on the `vectorizer_regression` marker and out of default API CI.

The 2026-10-03 census still names `test_entity_count_reduction`. That name is the historical measurement. The evidence test maps it to the new name and does not rewrite the census.

The dogfood record in `docs/investigations/code-tool-dogfood_2026-10-05/` stays the acceptance basis for `CODE-TOOL-SIGNATURES-004` in `HanzoRazer/code-analysis-tool`. `code_audit` 0.1.0 at `c2c1ea8` was not rerun. The regression file it scanned is preserved at `docs/investigations/code-tool-dogfood_2026-10-05/pins/test_text_masking_regression.py`; the evidence test accepts that snapshot when the live file no longer matches the pinned digest. F-3 is a separate repair.
