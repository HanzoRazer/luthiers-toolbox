# The Production Shop — Sprint Registry
Last updated: 2026-04-04
Maintained by: Ross Echols (HanzoRazer)

---

## ACTIVE

### Sprint 1 — Vectorizer Reconciliation
**Status:** Phase 4 open
**Branch:** main

| Phase | Description | Commit | Status |
|-------|-------------|--------|--------|
| 1 | Raw mode restoration — `--raw` flag, CHAIN_APPROX_NONE, CONTOURS layer, R12 | 04735bd4 | ✅ Done |
| 2 | Classification layer fixes — jack route guard, body size ceiling, solidity scoring, instrument detector | 72bfffc9 | ✅ Done |
| 3 | BlueprintAnalyzer wire-in — scale pre-pass, async wrapper, DPI fallback | 059cf5b0 | ✅ Done |
| 4 | Production Docker fixes | — | 🔄 Open |

**Phase 4 open items:**
- `libxcb.so.1` missing in production Docker image (blocks blueprint router)
- `vectorizer_phase3` not on Python path in API container
- `photo_vectorizer_router` unavailable in production (same libxcb cause)
- Fix location: `services/api/Dockerfile` — add libxcb and cv2 dependencies

**Key decisions recorded:**
- R12 (AC1009) is project-wide DXF standard — enforced in CLAUDE.md
- Raw mode bypasses all classification — produces CONTOURS layer, LINE entities only
- BlueprintAnalyzer uses PNG already in memory from PDF rasterization (no dual upload required)
- CHAIN_APPROX_NONE is non-negotiable for full fidelity extraction
- Instrument type detector is geometric pre-classifier — Phase 3 will replace with vision analysis
- Classification layer bugs were at Stage 6, not Stage 9-10 — fixes applied at correct location

---

### Sprint 2 — Repo Split and Standalone Products
**Status:** In progress
**Branch:** main

**Standalone repo inventory (all created on GitHub):**

| Repo | Description | Status |
|------|-------------|--------|
| HanzoRazer/ltb-acoustic-design-studio | Helmholtz + Gore P:A calculator + soundhole geometry designer | Empty — needs content |
| HanzoRazer/ltb-bridge-designer | Bridge geometry + string spacing | Existing — needs audit |
| HanzoRazer/ltb-fingerboard-designer | Scale length, radius, multiscale | Existing — needs audit |
| HanzoRazer/ltb-headstock-designer | Tuner layout, headstock templates | Existing — needs audit |
| HanzoRazer/ltb-neck-designer | Neck profiles, tapers | Existing — needs audit |
| HanzoRazer/ltb-parametric-guitar | Body shape generator | Existing — needs audit |
| HanzoRazer/ltb-woodworking-studio | Joinery, wood movement, bench woodworking | woodworking_v2 committed |
| HanzoRazer/blueprint-reader | PDF → DXF pipeline (vectorizer) | Existing — needs Sprint 1 sync |

**Strategic note:** Standalone repos are a moat — free tools that establish
The Production Shop as the authoritative lutherie calculator source.
All tools also exist embedded in Pro and Enterprise tiers.
luthiers-toolbox is the source of truth — standalones are published from it.

**Task list:**
- [ ] Move archtop_floating_bridge.py → app/instrument_geometry/bridge/
- [ ] Move wooden_floating_bridge.py → app/instrument_geometry/bridge/
- [ ] Reconcile floating_bridge.py in ltb-woodworking-studio vs main repo
- [ ] Define publish workflow for 8 standalone repos
- [ ] Populate ltb-acoustic-design-studio from SoundholeCalculator.vue + spiral_geometry.py
- [ ] Sync blueprint-reader with Sprint 1 Phase 1-3 commits

---

## QUEUED

### Sprint 3 — Remediation and Gap Closure
**Status:** Queued — blocked on dxf_writer.py

**Task list:**
- [ ] Build dxf_writer.py — central DXF writer enforcing R12, sentinel EXTMIN/EXTMAX,
      ≤3dp coordinates, no LWPOLYLINE. Blocks all new DXF generators.
- [ ] Fix 13 pre-existing test failures (10 soundhole spiral Python 3.14/ezdxf,
      2 debt gate ratchet, 1 vision integration)
- [ ] Resolve 8 gaps awaiting physical measurements
- [ ] Fix PatternRenderer import error in production
- [ ] Fix FastAPI regex deprecation warning (pattern= replacement)
- [ ] Add WeasyPrint dependencies to Docker (PDF export)
- [ ] libxcb Docker fix (shared with Sprint 1 Phase 4)

---

## COMPLETED

### Sprint 1 Phases 1-3 — Vectorizer Reconciliation
Completed: 2026-04-04
Commits: 04735bd4, 72bfffc9, 059cf5b0

**R12 Enforcement sweep** (part of Phase 1):
Files corrected: vectorizer_phase3.py, dxf_postprocessor.py,
phase4/annotations/exporter.py, CLAUDE.md
Config corrected: config/shop_config.yaml (version: R2018 → R12)

**Production environment restored:**
- DATABASE_URL: Supabase postgresql:// connection string set in Railway
- ANTHROPIC_API_KEY: Set in Railway shared variables
- luthiers-toolbox service: Online (was marked for deletion — recovered)
- graceful-luck service: Online
- @luthiers-toolbox/client: Online

---

## ARCHITECTURAL DECISIONS LOG

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-04 | R12 (AC1009) is project-wide DXF standard | CAM compatibility, Fusion 360 freeze prevention, genesis of The Production Shop |
| 2026-04-04 | dxf_writer.py blocks all new DXF generators | Central enforcement of R12 standards until it exists |
| 2026-04-04 | BlueprintAnalyzer uses in-memory PNG from PDF rasterization | No dual upload required — PDF already rasterized internally |
| 2026-04-04 | Standalone repos are a moat, not a code split | Copycats exist — free tools protect the integrated product |
| 2026-04-04 | ltb-woodworking-studio is the canonical woodworking module | app/woodworking/ in main repo is a seam — instrument geometry never goes there |
| 2026-04-04 | Instrument catalog uses tiered schema | Tier 1: validated plans in repo. Tier 2: community submitted. Tier 3: ethno/orchestral |
| 2026-04-04 | ltb-acoustic-design-studio combines Helmholtz calculator + soundhole designer | Physics-to-geometry pipeline is the product — separating breaks the workflow |

---

## INSTRUMENT CATALOG — TIER 1 WORKING SET
27 instruments confirmed TIER_1_READY (both PDF and DXF present):
acoustic_steel: A003-Dreadnought-MM, OM, Jumbo, Gibson L-00, J-45
acoustic_classical: Classical-Etienne-Corbet-MM
electric_solid: Gibson Les Paul 59, Les Paul Custom, Moderne, JS1000, RedSpecial
ukulele: Soprano (x2)
latin_american: cuatro puertoriqueño, plano cuatro venezolano, El Cuatro 1-8

97 PDF-only instruments identified as vectorizer candidates.
Full catalog in: services/api/app/instrument_geometry/models/

---

*This file is updated at the end of every sprint session.*
*Source of truth for sprint status across all terminals and chat sessions.*
