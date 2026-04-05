# The Production Shop — Sprint Registry
Last updated: 2026-04-05
Maintained by: Ross Echols (HanzoRazer)

---

## ACTIVE

### Sprint 1 — Vectorizer Reconciliation
**Status:** Phase 4 DONE, Phase 5 NEXT
**Branch:** main

| Phase | Description | Commit | Status |
|-------|-------------|--------|--------|
| 1 | Raw mode restoration — `--raw` flag, CHAIN_APPROX_NONE, CONTOURS layer, R12 | 04735bd4 | ✅ Done |
| 2 | Classification layer fixes — jack route guard, body size ceiling, solidity scoring, instrument detector | 72bfffc9 | ✅ Done |
| 3 | BlueprintAnalyzer wire-in — scale pre-pass, async wrapper, DPI fallback | 059cf5b0 | ✅ Done |
| 4 | Docker fix — raw mode → production | a76102c2 | ✅ Done |
| 4b | Docker deploy hardening (2026-04-05) | 5a145e90 | ✅ Done |
| 5 | Classified mode root cause fixes | — | ⏭️ NEXT |

**Phase 4b — Docker deploy hardening (2026-04-05):**
Commit chain fixing Railway deploy blockers:
- `67c4b68b` fix: libgl1-mesa-glx → libgl1 (Debian Trixie)
- `78c44886` fix: unterminated f-string in photo_vectorizer_router
- `cf162d9f` fix: remove broken sys.stderr.write lines
- `782dea1e` fix: explicit uvicorn+fastapi install before requirements
- `b6159dca` fix: comment out emergentintegrations (not on PyPI)
- `4334e378` fix: libgl1 in docker/api/Dockerfile
- `49ba3547` fix: uvicorn port 8000 → 8080 (Railway)
- `4674720c` fix: add RMOS_RUNS_DIR env var
- `5a145e90` fix: correct data paths — app/data not data at root

**graceful-luck service:** CLOSED — deleted from Railway 2026-04-05.

**Phase 5 — Classified mode root cause fixes (QUEUED):**
- Root cause 1: Scale detection — BlueprintAnalyzer not firing locally (no ANTHROPIC_API_KEY). Set key and retest.
- Root cause 2: Feature cross-contamination — CONTROL_CAVITY and RHYTHM_CIRCUIT on acoustics, BRACING on electrics. Les Paul auto-detected as acoustic (aspect ratio bug).
- Root cause 3: Body contour election unstable — Dreadnought shows 826x552mm in DXF vs 277x377mm reported (3x discrepancy).
- Root cause 4: Scale correction overcorrecting — Cuatro 0.511x correction produces 500mm vs 430mm target (16% error).
- Root cause 5: DXF write truncation on large outputs. Raw mode producing >195K LINE entities truncates ENDSEC/EOF. File required repair. Affects high-density blueprints in production. Investigate flush/buffer behavior in doc.saveas() for large R12 files.

**Quality Test Verdict:**
```
RAW MODE:    PASS — production ready. 3/3 files.
             1.99M segments (Dreadnought), 277K (Les Paul), 1.15M (Cuatro).
             AC1009, CONTOURS layer, zero open endpoints.

CLASSIFIED:  FAIL — not ready. 0/3 files within ±20% spec.
             Scale calibration and feature classification unreliable
             without ANTHROPIC_API_KEY in local environment.
```

**Strategic decision:** Ship raw mode via Docker fix (Phase 4).
Classified mode is the premium path — Sprint 1 Phase 5.

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
- [x] Move archtop_floating_bridge.py → app/instrument_geometry/bridge/ *(already in correct location)*
- [x] ~~Move wooden_floating_bridge.py~~ → Removed as redundant *(commit 1b61f219)*
- [x] Reconcile floating_bridge.py — resolved by removing redundant file; bridge module complete
- [ ] Define publish workflow for 8 standalone repos
- [ ] Populate ltb-acoustic-design-studio from SoundholeCalculator.vue + spiral_geometry.py
- [ ] Sync blueprint-reader with Sprint 1 Phase 1-3 commits
- [ ] Wire BlueprintAnalyzer scale pre-pass into photo_vectorizer_v2.py
      (same pattern as blueprint reader Phase 3 — PNG already in memory)
- [ ] Build body isolation pre-processor (neck-to-body crop before edge detection)
- [ ] Wire INSTRUMENT_CATALOG Tier 1 working set into photo_vectorizer_v2.py
- [ ] Confirm edge_to_dxf.py is available as high-fidelity fallback path
      for photo inputs where classification fails
- [ ] Install ODA File Converter locally to convert DWG files to DXF.
      Batch convert Guitar Plans/ DWG inventory: 59_Flying_V.dwg,
      Flying_V_11.dwg, Classical-02-MM.dwg, DWG-00/01/02/03-Gibson-SG.dwg,
      Acoustic Guitar Neck Profiles DWGs.
- [ ] Fix flying_v_1958.json schema mismatch with loader.py.
      load_model_spec("flying_v_1958") crashes on KeyError for "scale" key.
      Needs scale_length_mm → scale.scale_length_in conversion,
      body_height_mm array → loader expected format. (Committed 9cdad75b)
- [ ] Fix instrument_model_registry.json phantom entry: flying_v points to
      specs/gibson_flying_v_1958.json which does not exist. Align registry
      path with flying_v_1958.json committed at 9cdad75b.

---

## QUEUED

### Sprint 3 — Remediation and Gap Closure
**Status:** Queued — blocked on dxf_writer.py

**Task list:**
- [ ] Commit dxf_writer.py — currently untracked on disk, zero callers.
      CLAUDE.md blocking rule not satisfied until committed AND existing
      generators refactored. Generators still calling ezdxf.new() directly:
      archtop_floating_bridge.py, spiral_geometry.py, curve_export_router.py.
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

### Sprint 4 — Photo Vectorizer Production Readiness
**Status:** Queued — blocked on Sprint 1 Phase 4 Docker fix

**Task list:**
- [ ] Docker fix brings photo_vectorizer_router online (shared with Sprint 1 Phase 4)
- [ ] Validate photo vectorizer quality against SG Custom PNG after Docker fix
- [ ] BlueprintAnalyzer wire-in for photo path scale calibration
- [ ] Body isolation pre-processor (neck crop)
- [ ] INSTRUMENT_CATALOG Tier 1 integration
- [ ] Extend BlueprintAnalyzer prompt to identify decorative elements
      (rosettes, inlays, binding patterns) visible in blueprint images

**Note:** edge_to_dxf.py is the proven high-fidelity path for photos.
photo_vectorizer_v2.py classification path is supplementary.

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

## POST-DEPLOYMENT RESEARCH

### AI Visual Training — Decorative Element Recognition

**Target recognition categories:**
- Rosettes (concentric rings, mosaic patterns, spiral slots)
- Inlays (position markers, headstock logos, vine patterns)
- Binding patterns (herringbone, checkered, multi-ply)
- Materials (abalone, mother of pearl, wood species, plastic)

**Training corpus:**
- Source: 97 PDF-only instruments + Guitar Plans archive
- Ground truth: Manual annotation by Ross during vectorizer QA
- Delivery: JSON annotation files alongside source PDFs

**Implementation path:**
1. BlueprintAnalyzer prompt extension (Sprint 4 task)
2. Vision API structured output capture
3. Annotation validation UI (compare AI vs manual)
4. Fine-tuning data export for future model specialization

**Strategic value:** Decorative element recognition enables automatic
layer separation in DXF output — rosette geometry, inlay pockets, and
binding channels become distinct CAM-ready layers without manual editing.

---

### Physical Template Scanner Workflow
**Status:** Technically complete — documentation and UI surface needed
**Depends on:** Sprint 4 photo vectorizer production readiness

**The insight:**
Physical templates are the dominant reference format across all
hand-craft instrument making traditions — not just violin family.
This includes guitar, lute, oud, saz, kora, archtop, cello, bass,
and every non-Western tradition where template-based building
predates CAD by centuries.

**The product statement:**
"Upload a photo of your template. Get a CNC-ready DXF."

**Technical status:**
edge_to_dxf.py already handles this today.
Flatbed scan at 300 DPI → PNG → edge_to_dxf --raw
--height [known_height_mm] → R12 DXF at correct physical scale.
mm_per_px = 25.4/300 = 0.0847 — no BlueprintAnalyzer needed.
Scale is known from scan resolution.

**What is missing:**
- One-page workflow guide for non-CAD users
- UI surface in Blueprint Lab: "Scan a Template" intake path
- Validation step: compare DXF bounding box against
  user-entered physical measurements from calipers
- Documentation in docs/ covering the scanner workflow

**Catalog implications:**
Enables Tier 3 bowed string entries from physical templates:
  violin_strad_model, violin_guarneri_del_gesu,
  violin_montagnana, viola_strad, cello_strad,
  double_bass_flat_back, double_bass_carved_back

**Strategic value:**
No other lutherie software tool makes this offer to all
instrument making traditions simultaneously. The scanner
workflow is the universal onramp for non-Western and
traditional instrument makers who have no digital workflow.

---

*This file is updated at the end of every sprint session.*
*Source of truth for sprint status across all terminals and chat sessions.*
