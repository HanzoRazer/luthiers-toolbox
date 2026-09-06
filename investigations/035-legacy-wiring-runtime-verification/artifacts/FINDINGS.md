# FINDINGS

Assigned after runtime evidence freeze (`artifacts/RUNTIME_WITNESSES.md`).

LW = Legacy Wiring bounded finding. Not a production patch.

---

## Status vocabulary (applied)

```text
S1 D6  DEAD          FE URL not in live table; 404; intended sim lives elsewhere
S2 D2  WRONG IMPL    HTTP first-match is instrument_router, not geometry router
                     (same facade compute; not an obsolete calculator)
S3 D2  WRONG IMPL    HTTP first-match is N17 utility, not governed NC
S4 D2  WRONG IMPL    FE hits legacy polyline DXF, not governed translator
S5 D5  END-TO-END    preview entrypoint reached preview_fret_slots; preview JSON returned
```

```text
D0 = 0
D1 = 0
D2 = 3
D3 = 0
D4 = 0
D5 = 1
D6 = 1
D7 = 0
```

D3 was not used: N17 is a real implementation, not a placeholder. S5 yellow
gate / missing-model default is not automatically D3 (IW-04).

---

## LW-035-01 — SimLab FE URL is not mounted

S1. Production entrypoint `POST /api/cam/simulate_gcode` returns 404.
Intended `simulate_gcode_json` is mounted at `POST /api/cam/sim/gcode` and was
not called. Tests exercise the live path, not the FE path.

This is false integration of the **UI contract**, not a missing simulator.

---

## LW-035-02 — Soundhole POST first-match is instrument_router

S2. Geometry `calculate_soundhole` did not run. `get_soundhole_spec` ran and
called the bound facade `compute_soundhole_spec`. Spiral payload was produced.
`docs/INSTRUMENT_ROUTER_OVERLAP.md` already records parallel mounts.

Ownership diverges from the “canonical split router” story. Capability physics
does not.

---

## LW-035-03 — Polygon offset NC first-match is N17, not governed (SEVERE)

S3. OffsetLab posts governed-shaped JSON (`stepover=0.4`, `link_mode`, `units`)
to `POST /api/cam/polygon_offset.nc`. Runtime executed
`app.cam.routers.utility.polygon_router.polygon_offset`. G-code banner is N17.
Pass insets step by 0.4 mm, i.e. stepover-as-millimetres, not 0.4 × 6 mm.

```text
SEVERE STOP TRIGGERED = YES
```

All three stop predicates held. Remaining sampling was not required; S4/S5
were already in the same batch.

Future remediation (not authorized here) would be bounded to: which handler
owns `POST /api/cam/polygon_offset.nc` versus OffsetLab’s schema, without
silently deleting the N17 consumer if it still has a legitimate client
(`n17_n18.ts`).

---

## LW-035-04 — CurveMath DXF uses the legacy export router

S4. `export_polyline_dxf` ran (count 1). Governed `translate_to_dxf` did not
(count 0). The request terminated HTTP 500. Helper source-module spies were
IW-02 (0).

Handler identity is witnessed. **The cause of the 500 is not** — see the
withdrawn "ezdxf activity" note in `RUNTIME_WITNESSES.md`; no frozen artifact
records ezdxf running on this request. Note also that
`app.routers.export.dxf_translate_router.translate_to_dxf` is not mounted at
`/exports/polyline_dxf` at all (`CURRENT_LIVE_ROUTES.json` lists exactly one
handler for that path), so its 0 is a property of the route table, not a
first-match race.

---

## LW-035-05 — Fret slots preview reaches the intended HTTP handler

S5. `preview_fret_slots` ran; 200 preview envelope. Generator source-module
spy 0 (likely bound import). Not a false-integration specimen at the HTTP
layer.

---

## Operational severity is a different axis from D-status (added 2026-09-06)

Raised during PR #356 review. This adds **no new evidence and changes no
D-status**; it separates two things the packet currently reads as one.

`SEVERE STOP = YES (S3)` is a statement about the **sampling protocol** — the
predicates that told the investigation to stop sampling. It is not a ranking of
user impact. Read only the D-column and RESULTS, and it is easy to conclude
that S3 is the one urgent item. Two others are hard failures on live frontend
call paths at this SHA:

```text
S1  POST /api/cam/simulate_gcode  → HTTP 404
    five production call sites, not one:
      GeometryOverlay.vue:259
      SimLab.vue:292, SimLab.vue:329
      SimLabWorker.vue:161
      bridge_lab/composables/useGcodeSimulation.ts:47
    the FE api() helper does not rewrite the path (API_BASE defaults to ''),
    so the 404 is the shipped behaviour, not a harness artefact.

S4  POST /exports/polyline_dxf   → HTTP 500
    single call site: utils/curvemath_dxf.ts:57

S3  POST /api/cam/polygon_offset.nc → HTTP 200, wrong stepover semantics
```

The distinction that matters for triage:

- S3 fails **silently and plausibly**. It returns 200 and valid-looking G-code
  with a 6× denser toolpath than the operator's control implies. Nothing in the
  response says anything is wrong. That is why it is the severe stop.
- S1 and S4 fail **loudly**. A 404 and a 500 are visible to the user and cannot
  be mistaken for a good result — but they are still two broken production
  features, and S1 is broken at five call sites.

Correct reading: S3 is the highest **risk** finding; S1 and S4 are the most
immediately **broken** features. Nothing here is authorized for repair in this
increment (`PATCH_PROPOSAL.md`), and none of it is offered as a patch.

---

## Mechanism (bounded)

Recurring class in this sample:

```text
FRONTEND OR DOCS CONTRACT
    → wire URL
        → FastAPI first-match among dual mounts / relocated prefixes
            → not the implementation the contract was written against
```

Seen independently as:

- relocated prefix (S1: `/simulate_gcode` vs `/sim/gcode`)
- dual POST handlers (S2 soundhole, S3 polygon_offset.nc)
- legacy vs governed export URL (S4)

Not every static collision is this class (health, routing-truth, etc.).
