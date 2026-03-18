# Neck Suite Integration Corrections
# luthiers-toolbox-main — Production Shop

Applies four corrections from the repo audit, then wires the headstock
suite composables alongside the existing `cam/neck/` pipeline.

---

## Correction 1 — `useNeckTaper.ts`: distance-based width formula

**File:** `ps-vue/src/composables/useNeckTaper.ts`
**Status:** Applied — see updated file in outputs.

Old behaviour used `t = fret / fretCount` (index ratio).
Correct formula from `services/api/app/instrument_geometry/neck_taper/taper_math.py`:

```
x_f = scale - scale / 2^(f/12)      # physical distance from nut
L_N = scale - scale / 2^(N/12)      # physical distance to reference fret
W_f = W_nut + (x_f / L_N) × (W_end - W_nut)
```

The `NeckTaperSpec.scaleLengthMm` field is now used in `neckWidthAtFret()`.
All four taper types (linear, convex, concave, stepped) use distance-based
interpolation internally.

---

## Correction 2 — `useCamSpec.ts` / `CamSpecPanel.vue`: truss rod defaults

**Files:** `ps-vue/src/composables/useCamSpec.ts`
         `ps-vue/src/components/CamSpecPanel.vue`
**Status:** Applied — see updated files in outputs.

Old defaults were approximate.  Correct values from
`services/api/app/cam/neck/config.py` `TrussRodConfig`:

| Field          | Old value | Corrected value | Source           |
|----------------|-----------|-----------------|------------------|
| `rodWidthMm`   | 6mm       | **6.35mm** (¼") | `TrussRodConfig` |
| `rodDepthMm`   | 11mm      | **9.525mm** (⅜")| `TrussRodConfig` |
| `rodLengthMm`  | 445mm     | **406.4mm** (16")| `TrussRodConfig` |
| `endMillMm`    | 6mm       | **3.175mm** (⅛")| Tool T2 in repo  |

---

## Correction 3 — `neck_profile_export.py`: delegate to `NeckPipeline`

**File:** `neck_profile_export.py` (outputs root)
**Status:** Applied — see updated file in outputs.

Old file reimplemented G-code generation inline.
Corrected file delegates to the existing repo pipeline:

```python
from app.cam.neck.orchestrator import NeckPipeline
from app.cam.neck.config import NeckPipelineConfig, ...

cfg    = build_pipeline_config(req)   # maps NeckRequest → NeckPipelineConfig
result = NeckPipeline(cfg).generate(  # runs OP10 + OP40 + OP45 + OP50
    include_truss_rod=True,
    include_profile_rough=True,
    include_profile_finish=True,
    include_fret_slots=req.include_fret_slots,
)
code = result.get_gcode()
```

Crown compensation is computed from the fretboard spec before
`NeckPipelineConfig` is built, so the pipeline receives
pre-compensated `depth_at_nut_mm` / `depth_at_12th_mm` / `depth_at_heel_mm`.

New endpoint added: `POST /api/neck/pipeline/preview` — returns the
orchestrator's station list and fret positions without producing G-code.

---

## Correction 4 — Integration into `luthiers-toolbox-main`

### 4a. Place the Vue composables

Copy the four new composables into the existing neck module:

```
packages/client/src/
└── design-utilities/
    └── lutherie/
        └── neck/                   ← create this folder
            ├── useNeckTaper.ts     ← from outputs
            ├── useFretboard.ts     ← from outputs
            ├── useNeckProfile.ts   ← from outputs
            ├── useCamSpec.ts       ← from outputs
            ├── drawCamOverlay.ts   ← from outputs
            └── index.ts            ← re-export all
```

`index.ts`:
```typescript
export { useNeckTaper }   from './useNeckTaper'
export { useFretboard }   from './useFretboard'
export { useNeckProfile } from './useNeckProfile'
export { useCamSpec }     from './useCamSpec'
export { drawCamOverlay } from './drawCamOverlay'
```

### 4b. Register backend routers

In `services/api/app/main.py`, add alongside existing neck routers:

```python
# Existing (already in repo)
from app.routers.neck import gcode_router, geometry
app.include_router(gcode_router.router,  prefix="/api/neck")
app.include_router(geometry.router,      prefix="/api/neck")

# New — add these
from neck_profile_export   import router as neck_profile_router
from fretboard_export       import router as fb_router
app.include_router(neck_profile_router, prefix="/api/neck")
app.include_router(fb_router,           prefix="/api/fretboard")
```

### 4c. Coordinate convention — VINE-05

All neck G-code in the repo uses:
    Y = 0   at nut centerline
    +Y      toward bridge
    X = 0   centerline

The headstock suite composables use:
    canvas units (0–200 × 0–320), MM_PER_UNIT = 0.215
    Y origin at nut bottom (canvas Y = 298)

The `neck_profile_export.py` `build_pipeline_config()` function converts
canvas-space depth values to VINE-05 convention before passing to the pipeline.
No changes needed in the composables themselves.

### 4d. Import path for NeckPipeline

`neck_profile_export.py` imports:
```python
from app.cam.neck.orchestrator import NeckPipeline
```

This requires the file to run inside the `services/api/` Python package context.
If running standalone, set `PYTHONPATH`:
```bash
PYTHONPATH=services/api uvicorn neck_profile_export:router ...
```

The file gracefully degrades (`PIPELINE_AVAILABLE = False`) if the import
fails, falling back to the inline G-code generator so the endpoint stays
functional during development.

---

## Summary checklist

- [x] `useNeckTaper.ts` — distance-based taper formula (Correction 1)
- [x] `useCamSpec.ts` — truss rod defaults from repo (Correction 2)
- [x] `CamSpecPanel.vue` — slider min updated for 3.175mm end mill (Correction 2)
- [x] `neck_profile_export.py` — delegates to NeckPipeline (Correction 3)
- [ ] Copy Vue composables to `design-utilities/lutherie/neck/` (Correction 4a)
- [ ] Register routers in `main.py` (Correction 4b)
- [ ] Verify VINE-05 coordinate convention in G-code output (Correction 4c)
- [ ] Set PYTHONPATH for pipeline import (Correction 4d)
