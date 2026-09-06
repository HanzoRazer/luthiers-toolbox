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

S4. `export_polyline_dxf` ran. Governed `translate_to_dxf` did not. HTTP 500
after ezdxf R12 activity. Helper source-module spies were IW-02 (0). Terminal
500 is not fully explained; handler identity is.

---

## LW-035-05 — Fret slots preview reaches the intended HTTP handler

S5. `preview_fret_slots` ran; 200 preview envelope. Generator source-module
spy 0 (likely bound import). Not a false-integration specimen at the HTTP
layer.

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
