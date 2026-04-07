# Next Session Spec
**Date:** 2026-04-06  
**Opens with:** ltb-bridge-designer population → blueprint-reader Hostinger deploy

---

## Task 1 — ltb-bridge-designer Population

### Strategy
Staged Copy Publish — same approach as ltb-acoustic-design-studio and ltb-fingerboard-designer.

### Source Paths (from luthiers-toolbox)

**Python Backend — Calculators:**
```
services/api/app/calculators/bridge_calc.py
services/api/app/calculators/bridge_break_angle.py
services/api/app/calculators/acoustic_bridge_calc.py
services/api/app/calculators/string_tension.py
```

**Python Backend — Geometry:**
```
services/api/app/instrument_geometry/bridge/geometry.py
services/api/app/instrument_geometry/bridge/placement.py
services/api/app/instrument_geometry/bridge/compensation.py
services/api/app/instrument_geometry/bridge/archtop_floating_bridge.py
services/api/app/instrument_geometry/bridge/electric_bridges.py
services/api/app/instrument_geometry/bridge/floyd_rose_tremolo.py
services/api/app/instrument_geometry/bridge/__init__.py
```

**Routers:**
```
services/api/app/routers/instrument_geometry/bridge_router.py
services/api/app/routers/bridge_presets_router.py
services/api/app/cam/routers/bridge_export_router.py
```

**Vue Components:**
```
packages/client/src/components/toolbox/BridgeCalculator.vue
packages/client/src/views/BridgeLabView.vue
packages/client/src/instrument-workspace/acoustic/bridge/BridgeLabPanel.vue
packages/client/src/components/bridge_calculator_panel/BridgeCalculatorPanel.vue
packages/client/src/views/bridge_lab/AdaptiveParamsPanel.vue
packages/client/src/views/bridge_lab/ToolpathResultsPanel.vue
```

### Target Package Structure (actual — do not use `ltb_bridge/geometry/`)

The standalone repo mirrors monolith paths under `ltb_bridge.instrument_geometry` (not a renamed `geometry/` package).

```
ltb-bridge-designer/
├── src/
│   └── ltb_bridge/
│       ├── __init__.py
│       ├── main.py              ← FastAPI: /health; routers below
│       ├── calculators/
│       │   ├── bridge_calc.py
│       │   ├── bridge_break_angle.py
│       │   ├── acoustic_bridge_calc.py
│       │   └── string_tension.py
│       ├── instrument_geometry/
│       │   ├── models.py                    ← InstrumentModelId, specs (shared)
│       │   ├── neck/
│       │   │   └── neck_profiles.py        ← BridgeSpec, InstrumentSpec, …
│       │   └── bridge/
│       │       ├── __init__.py
│       │       ├── geometry.py
│       │       ├── placement.py
│       │       ├── compensation.py
│       │       ├── archtop_floating_bridge.py
│       │       ├── electric_bridges.py
│       │       └── floyd_rose_tremolo.py
│       └── api/
│           ├── bridge_router.py             ← mounted /api/instrument
│           ├── bridge_presets_router.py     ← mounted /api  (prefix /cam/bridge)
│           └── bridge_export_router.py      ← mounted /api/cam
├── scripts/
│   └── populate_imports.py                  ← optional re-sync helper
├── pyproject.toml
├── requirements.txt
├── .gitignore
└── README.md
```

### Import Rewrite Rule
```
Monolith → standalone:
  from app.calculators.* → from ltb_bridge.calculators.*
  from app.instrument_geometry.bridge.* → from ltb_bridge.instrument_geometry.bridge.*
  from app.instrument_geometry.neck.*   → from ltb_bridge.instrument_geometry.neck.*
Relative imports inside instrument_geometry/ may stay as ..neck / ..models / .geometry siblings.
```

### Known Dependencies to Check
```
bridge_break_angle.py may reference string_tension.py
archtop_floating_bridge.py may reference geometry.py
floyd_rose_tremolo.py may reference electric_bridges.py
Check and resolve before committing.
```

### Floating Bridge Spec (Rev 2 — canonical)
```
Base:           155mm
Foot:           4.5mm
Saddle radius:  381mm
Posts:          M4
Base thickness: 10.5mm
Saddle blank:   8mm
```
Verify these values are correctly implemented in archtop_floating_bridge.py before publishing.

### Verify Locally
```
cd C:\Users\thepr\Downloads\ltb-bridge-designer
pip install -e .
uvicorn ltb_bridge.main:app --reload --host 0.0.0.0 --port 8000
Open /docs — confirm bridge endpoints load
```

### Acceptance Criteria
```
✅ Package installs cleanly
✅ All imports resolve
✅ /health endpoint responds
✅ Bridge calculation endpoints load in /docs
✅ No luthiers-toolbox internal paths in any file
✅ README explains what the tool does
✅ Committed and pushed to GitHub
✅ Repo already PUBLIC (free tier)
```

### Commit Message
```
feat(bridge-designer): initial population via Staged Copy Publish

Calculators: bridge_calc, bridge_break_angle,
acoustic_bridge_calc, string_tension

instrument_geometry/bridge: geometry, placement, compensation,
archtop_floating_bridge (Rev 2), electric_bridges,
floyd_rose_tremolo

API: bridge_router /api/instrument; presets+export under /api/cam
Frontend: BridgeCalculator.vue

Floating bridge Rev 2 spec:
base=155mm, foot=4.5mm, saddle_radius=381mm,
M4 posts, base_thickness=10.5mm, saddle_blank=8mm
```

---

## Task 2 — blueprint-reader Hostinger Deploy

### BLOCKED — Hostinger Billing Issue
- **Reason:** Hostinger billing/coupon issue
- **Expected:** Resolved within 24 hours
- **Next action:** Resume after support response

---

### Blocker — choose production domain first

CORS, `VITE_*` / client API base URL, and server `ALLOWED_ORIGINS` (or equivalent) **must** use the final hostname. Decide before running deploy commands.

| Option | Domain |
|--------|--------|
| **A** | `blueprint-reader.theproductionshop.com` |
| **B** | `blueprintreader.app` |
| **C** | `blueprint.theproductionshop.com` |
| **D** | Something else (record full hostname here when chosen) |

**Status:** ☐ Record chosen option and exact URL (including `https://`) in this file or SPRINTS.md when decided.

---

### Current State
```
Repo:     HanzoRazer/blueprint-reader
Branch:   main
Content:  client/ + server/ structure
          Landing page committed (98b33ddc)
          README updated with BLUEPRINT_READER_INPUT_SPEC link
Visibility: PUBLIC
Status:   NOT YET DEPLOYED
```

### Deploy Target
```
Host:     Hostinger
Domain:   See “Blocker — choose production domain first” above (Options A–D).
```

### Pre-Deploy Checklist
```
□ Confirm Hostinger account credentials
□ Decide domain/subdomain
□ Verify client/ build output is production-ready
□ Verify server/ API is production-ready
□ Check environment variables needed
□ Check CORS settings for production domain
□ Confirm no API keys hardcoded in client/
□ Build and test locally before pushing to Hostinger
```

### Deploy Steps
```
Step 1: Build frontend
  cd client/
  npm run build
  Verify dist/ output

Step 2: Configure Hostinger
  Upload dist/ to public_html
  OR configure Node.js hosting for server/

Step 3: Environment variables
  Set production API URL
  Set any required API keys

Step 4: Verify live
  Hit /health on deployed API
  Load landing page
  Test one vectorizer extraction end-to-end

Step 5: Update SPRINTS.md
  Mark blueprint-reader deploy COMPLETE
  Note live URL
```

### Acceptance Criteria
```
✅ Landing page loads at production URL
✅ /health endpoint responds in production
✅ One test extraction succeeds end-to-end
✅ BLUEPRINT_READER_INPUT_SPEC.md linked from page
✅ URL noted in SPRINTS.md
```

---

## Session Order
```
1. ltb-bridge-designer — done (see repo); Rev 2 fields in archtop_floating_bridge Benedetto17Defaults
2. blueprint-reader Hostinger deploy — BLOCKED until domain (A/B/C/D) is chosen
3. Update SPRINTS.md (live blueprint-reader URL when deployed)
```

## After Both Tasks Complete
```
Sprint 2 remaining:
  ltb-express cleanup (contaminated)
  ltb-fingerboard-designer public verify
  Production Shop hub landing page (missing)
  Repo rename: luthiers-toolbox → the_production_shop
```
