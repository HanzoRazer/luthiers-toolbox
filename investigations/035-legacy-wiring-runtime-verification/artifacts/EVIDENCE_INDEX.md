# EVIDENCE INDEX

Added 2026-09-06 during PR #356 review. **Nothing here is new evidence.** Every
row points at an artifact already frozen in this packet, or at a production file
at the baseline SHA. The index exists so a reviewer can check one claim without
reading four narrative documents, and so an unbacked claim has nowhere to hide.

Baseline for every row: `cab91edacaedc66a0492c35275ce2c255935bf8e`.

Read the column `BACKED BY` literally:

```text
FROZEN     an artifact in this PR's diff
PRODUCTION a file in services/ or packages/ at the baseline SHA
DERIVED    an inference stated in a narrative doc; the row names its inputs
NOT WITNESSED  claim carries no artifact — kept only where the doc says so
```

---

## Headline conclusions

| # | Conclusion | Backed by | Artifact / file |
| - | ---------- | --------- | --------------- |
| 1 | S1 `POST /api/cam/simulate_gcode` returns 404 | FROZEN | `census/WITNESS_S1.json` → `HTTP_CLI_RESULT.status_code = 404` |
| 2 | S1 path is absent from the live route table | FROZEN | `census/CURRENT_LIVE_ROUTES.json` — `/api/cam/sim/gcode` and `/api/cam/sim/simulate_gcode` present, `/api/cam/simulate_gcode` absent |
| 3 | S1 is a live frontend contract, not a stale doc | PRODUCTION | 5 call sites: `GeometryOverlay.vue:259`, `SimLab.vue:292,329`, `SimLabWorker.vue:161`, `bridge_lab/composables/useGcodeSimulation.ts:47` |
| 4 | S2 first-match is `instrument_router.get_soundhole_spec` | FROZEN | `census/WITNESS_S2.json` → `alternate_legacy_instrument_router = 1`, `expected_geometry_router = 0` |
| 5 | S2 physics is unchanged (same facade object) | FROZEN | `census/WITNESS_S2.json` → `legacy_router_bound_facade = 1` |
| 6 | S3 executed the N17 utility handler | FROZEN | `census/WITNESS_S3.json` → `alternate_utility_n17 = 1`, `expected_governed_nc = 0`; body banner `(N17 Polygon Offset — arcs + feed floors)` |
| 7 | S3 `polygon_offset.nc` is a real dual mount | FROZEN | `census/CURRENT_LIVE_ROUTES.json` — two `POST /api/cam/polygon_offset.nc` rows: `app.cam.routers.utility.polygon_router` then `app.routers.polygon_offset_router` |
| 8 | S3 stepover was applied as **millimetres** | FROZEN | `census/WITNESS_S3.json` G-code pass insets `99.600 → 99.200 → 98.800 → 98.400` = 0.4 mm steps at `tool_dia = 6.0` |
| 9 | The governed handler would have stepped 2.4 mm | PRODUCTION | `services/api/app/routers/polygon_offset_router.py:26` `Field(..., gt=0, le=1.0, description="Fraction of tool_dia")`; `:70` and `:203` `step = req.tool_dia * req.stepover` |
| 10 | The N17 handler's stepover is absolute mm | PRODUCTION | `services/api/app/cam/routers/utility/polygon_router.py:25` `stepover: float = 2.0` — a default of 2.0 is impossible under a 0–1 fraction convention |
| 11 | OffsetLab sends the **fraction** convention | PRODUCTION | `packages/client/src/views/OffsetLabView.vue:209` `ref(0.4)`; UI label `Stepover (0–1)` with `min=0.05 max=0.95` at `:63-70`; posted at `:256,:283` |
| 12 | S4 ran the legacy handler, not the governed translator | FROZEN | `census/WITNESS_S4.json` → `actual_legacy_handler = 1`, `expected_governed_translate = 0` |
| 13 | S4's governed 0 is route-table, not a first-match race | FROZEN | `census/CURRENT_LIVE_ROUTES.json` — exactly one handler on `POST /exports/polyline_dxf` |
| 14 | S4 terminated HTTP 500 | FROZEN | `census/WITNESS_S4.json` → `status_code = 500`, body `"Internal Server Error"` |
| 15 | **Why** S4 returned 500 | NOT WITNESSED | no artifact. The earlier "ezdxf activity in logs" wording was withdrawn — `legacy_ezdxf_helper = 0` and `legacy_ascii_r12_fallback = 0` |
| 16 | S5 reached the intended preview handler | FROZEN | `census/WITNESS_S5.json` → `expected_preview_handler = 1`, HTTP 200 |
| 17 | S5 generator spies read 0 because of import binding | DERIVED | inputs: `WITNESS_S5.json` (`expected_standard_generator = 0`) + IW-02 in `tests/test_instrument_controls.py`. A 0 on a source-module spy is not proof of non-execution |
| 18 | IW-03 control reached `vectorize_blueprint` | FROZEN | `census/WITNESS_IW03.json` → `expected_vectorize_route = 1`, HTTP 200 |
| 19 | Census counts (1157 / 10 / 15 / 23 / 276 / 137) | FROZEN | `census/CURRENT_CENSUS_SUMMARY.json`; the 1157 figure is reproduced row-for-row in `census/CURRENT_LIVE_ROUTES.json` |
| 20 | The production route collector reports 10 | FROZEN | `census/CURRENT_LIVE_ROUTES_DUMP_AS_IS.json` + `CURRENT_CENSUS_SUMMARY.json.dump_and_assert_routes_as_is` |
| 21 | Comparison against Lab PR #17 | NOT WITNESSED | stated as such — PR #17 artifacts were not reachable from the collection environment |

---

## Harness claims (which control covers what)

Cite this table instead of "the instrument controls pass".

| Mechanism | Used for | Control | Kind |
| --------- | -------- | ------- | ---- |
| `install_spies` (module-level patch) | the **0** readings labelled IW-02 | IW-01, IW-02 | positive + negative |
| `install_spies` failure path | evidence integrity across specimens | IW-08 | regression — fails on the pre-fix harness |
| `bind_spies_to_fastapi_routes` (`APIRoute.handle`) | **every S1–S5 handler-identity number** | IW-06 | positive + negative |
| the same hook is observational | the voided `route.endpoint` wrap turned 200 into 422 | IW-06b | equivalence |
| double-wrap refusal | count inflation from a leaked hook | IW-07 | regression — fails on the pre-fix harness |
| D3 / D5 reading conventions | classification vocabulary only | IW-04, IW-05 | **exercise no harness code** |

`EQ-A01-035-12` cited IW-01/IW-02 as the instrument for a claim about
`APIRoute.handle`. That was the wrong instrument — those two validate module
patching. IW-06 is the control that claim needs, and the claim record now cites
it.

---

## Known limits of this index

- Rows 3, 9, 10, 11 read **production files at the baseline SHA**, not frozen
  copies. They are re-checkable but not immutable; re-verify against
  `cab91eda` rather than against a later `main`.
- Row 15 and row 21 are listed precisely because they have no artifact. Do not
  promote either to a finding.
- Nothing in this index assigns D-status. `artifacts/FINDINGS.md` does that.
