# Instrument router overlap (split vs parallel)

The main `instrument_router` was reduced on **2026-03-29** to **four** endpoints that remain as **parallel implementations** while schemas and clients are reconciled with the split instrument-geometry routers (registered in the router manifest under `6ffb0bf9`).

**Retained on `/api/instrument`:**

| Method | Path | Notes |
|--------|------|--------|
| POST | `/nut-compensation` | GEOMETRY-007 |
| POST | `/nut-compensation/compare` | GEOMETRY-007 |
| POST | `/soundhole` | GEOMETRY-002 |
| POST | `/soundhole/check-position` | GEOMETRY-002 |

All other former `instrument_router` handlers (bridge, radius, presets, string tension, kerfing, tuning machine, extra nut/soundhole GETs, saddle force, top deflection, brace sizing, etc.) live on the **split routers** only.
