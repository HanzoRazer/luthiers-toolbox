# CLAUDE.md — Production Shop / luthiers-toolbox
# Read this file at the start of every session before making any changes.
# Last updated: 2026-03-30

---

## Who owns this repo

Ross L. Echols Jr., P.E. #78195
Texas Guitar Exchange LLC, Bellaire TX
Solo developer + luthier.

---

## What this repo is

The Production Shop — a Vue 3 + TypeScript + FastAPI platform serving as
ERP/CAM for instrument makers. It is NOT a calculator app. It is production
infrastructure: RMOS workflow engine, G-code generation, risk assessment
gates, SHA256 audit trails, CNC toolpath management.

Origin: built because novice luthiers cannot get mentorship. The platform
encodes lutherie knowledge systematically so builders can teach themselves.
Every feature decision traces back to this mission.

---

## Stack

- Frontend: Vue 3 + TypeScript, Pinia, packages/client/
- Backend: FastAPI (Python), services/api/
- Database: SQLite (migrating to PostgreSQL — see DB section)
- CNC: BCAMCNC 2030A router
- Hardware target: Raspberry Pi 5 (tap_tone_pi integration)

---

## COMPLETED WORK — DO NOT REDO

### Router migrations (Sprint 3, 2026-03-29)
instrument_router.py has been REDUCED from 1,291 to ~215 lines.
19 endpoints were migrated to split routers in:
  app/routers/instrument_geometry/
    geometry_calculator_router.py    (5 endpoints)
    tuning_machine_router.py         (4 endpoints)
    construction_router.py           (4 endpoints)
    string_tension_router.py         (3 endpoints)
    nut_fret_router.py               (extended)
    soundhole_router.py              (extended)

The 4 remaining endpoints in instrument_router.py are INTENTIONAL
PARALLEL IMPLEMENTATIONS with different schemas. Do NOT remove them.
See docs/INSTRUMENT_ROUTER_OVERLAP.md.

### Woodworking module (Sprint 2, 2026-03-28)
app/woodworking/ is COMPLETE with these canonical files:
  archtop_floating_bridge.py  ← CANONICAL archtop bridge (Benedetto-style)
  floating_bridge.py          ← electric bridge action
  board_feet.py               ← board feet, wood weight, seasonal movement
  joinery.py                  ← dovetail, box joints, mortise & tenon
  panels.py                   ← floating panel gaps

archtop_bridge.py was DELETED. It was a redundant subset.
Do NOT recreate it. Use archtop_floating_bridge.py.

### Endpoint count (confirmed 2026-03-29)
Decorator grep count: 941 (ratchet target: 945)
Registered routes: 898
Debt gate target: ≤945 decorators
Do NOT lower the ratchet below 945 — it uses decorator counting,
not registered route counting. The 43 difference is intentional.

### Manifest cleanup
These routers were DOUBLE-REGISTERED and fixed:
  machines_consolidated_router — was in cam_manifest.py twice
  materials.router — was in system_manifest.py twice
  workflow.sessions.routes — was in rmos_manifest.py + system_manifest.py
  photo_vectorizer_router — was in business_manifest.py + cam_manifest.py
  governance_router — was in main.py + manifest

Do NOT re-register any of these.

### Monolith unregistered
app.routers.instrument_geometry_router is COMMENTED OUT in
business_manifest.py. It is NOT deleted (file retained for reference).
Do NOT uncomment or re-register it.

### Database migration stack (built, not yet deployed)
  app/db/alembic_models.py    — SQLAlchemy models for 5 tables
  app/db/migrations/          — Alembic migrations (initial generated)
  app/db/dual_write.py        — DualWriteStore for cutover period
  app/db/pg_pool.py           — Async PostgreSQL connection pool
PostgreSQL instance NOT yet provisioned. Do not run alembic upgrade
against any production database until explicitly instructed.

---

## DO NOT TOUCH — ACTIVE CONSTRAINTS

### Safety gaps (logged, not yet implemented)
CCEX-GAP-ISLAND-01: Island subtraction in adaptive_core_l1.py
  Logger warning added. DO NOT implement — BCAM first article required.

CCEX-GAP-ASSETS-01: project_assets_router.py is a stub
  Returns empty data. Logger warning added. DO NOT remove the stub.
  DO NOT add real implementation without explicit instruction.

CCEX-GAP-SIM-01: sim_validate returns mock data
  Logger warning added. DO NOT change behavior.

### CAM layer architecture
adaptive_core_l1.py, l2.py, feedtime_l3.py, time_estimator_v2.py
are LAYERED ARCHITECTURE, not versioned duplicates.
They have 20+ active imports each. DO NOT delete or consolidate them.

### WAV I/O (tap_tone_pi)
All WAV read/write must go through modes/_shared/wav_io.py.
Direct scipy.io.wavfile usage anywhere else is a bug.
CI enforces this with wav-io-guard.yml.

---

## SMART GUITAR SPEC — KEY FACTS

File: services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json

Two variants:
  Production — headless, Steinberger-style tuner housing (primary build)
  Pro — Flying V inline-6 headstock, 14° angle (build after first article)

Body shape is an ORIGINAL ERGONOMIC DESIGN by Ross L. Echols Jr.
Visual similarity to Klein guitar is COINCIDENTAL — independent convergence.
DO NOT describe it as derived from or based on the Klein guitar.

Parent instruments for geometry reference:
  Primary: Gibson Explorer (neck angle 3.5°, scale 628.65mm, neck thickness)
  Secondary: Gibson Les Paul (set neck construction philosophy)

Explorer blueprint is committed at:
  docs/archive/instrument_references/gibson_explorer/
  Source commit: a8e4f5a9

Verified neck dimensions (from Explorer blueprint):
  Neck thickness 1st fret: 20.32mm (neck only) + 5mm fretboard = 25.32mm total
  Neck thickness 12th fret: 21.59mm (neck only) + 5mm fretboard = 26.59mm total
  Joint angle: 3.5° (corrected from 4.5°)
  Headstock angle: N/A (Production is headless)
  Body length: 438.15mm (corrected from 444.5mm)
  Body join fret: TBD — 19 or 20, pending first article

---

## INSTRUMENT SPEC LIBRARY — CURRENT STATE

All specs in: services/api/app/instrument_geometry/specs/
All blueprints in: docs/archive/instrument_references/

| Instrument          | Spec file              | Blueprints       |
|---------------------|------------------------|------------------|
| Gibson Explorer     | gibson_explorer.json   | 3 PDFs           |
| Gibson ES-335       | gibson_es_335.json     | 6 PDFs           |
| Gibson SG           | gibson_sg.json         | 8 PDFs+DXF+3DWGs |
| Gibson EDS-1275     | reference only         | 1 PDF            |
| Gibson Melody Maker | gibson_melody_maker.json | 1 PDF          |
| Gibson Les Paul     | gibson_les_paul.json   | 15 files         |
| Fender Telecaster   | fender_telecaster.json | 8 PDFs + 2 PSDs  |
| Fender Stratocaster | fender_stratocaster.json | 8 PDFs + 2 PSDs|

---

## SCORE IMPROVEMENT PLAN — STATUS

Starting score: 74.3/100 (B-)
Target: 85+/100 (B+)

| Phase | Status |
|---|---|
| Week 1 — fix tests + safety warnings | COMPLETE |
| Week 2-3 — endpoint consolidation | COMPLETE (949→898) |
| Week 4 — PostgreSQL migration | IN PROGRESS (stack built, needs instance) |
| Week 5 — Redis caching | NOT STARTED |
| Week 6 — Celery task queue | NOT STARTED |

PostgreSQL gate: 900 endpoints (PASSED — actual 898 registered)

---

## ROUTER REGISTRY PATTERN

Routers are registered via manifests in:
  app/router_registry/manifests/
    cam_manifest.py
    business_manifest.py
    system_manifest.py
    rmos_manifest.py

To add a new router: add a RouterSpec entry to the appropriate manifest.
Do NOT register routers directly in main.py (except health/core).
Do NOT register the same router in two manifests.

---

## TESTING RULES

Run tests before committing any router or calculator change:
  cd services/api
  python -m pytest --tb=short -q

Manufacturing candidate tests (test_manufacturing_candidates.py):
  These require monkeypatch for AUTH_MODE — already implemented.
  If they fail in full suite, the fix is test isolation, NOT mock changes.
  Root cause commit: 8ee1083e (AUTH_MODE monkeypatch)

TestClient must be function-scoped, not module-level.
Root cause commit: 06f6351a

---

## GIT DISCIPLINE

Always check before starting work:
  git status
  git log --oneline -5
  git pull origin main

Never force push without --force-with-lease.
Never commit binary files (PDFs, PSDs, DXFs) in the same commit
as code changes. Separate commits for reference assets vs code.

Commit message format:
  type(scope): description
  Types: feat, fix, refactor, test, docs, chore, perf

---

## CBSP21 PROTOCOL

Before modifying any file, scan ≥95% of its content.
Do not reason from partial inputs.
Applies equally to AI agents and human contributors.
Full protocol: CBSP21.md in tap_tone_pi repo.

---

## OPEN ITEMS FOR NEXT SESSION

1. PostgreSQL instance provisioning (Docker or Supabase)
2. Smart Guitar Klein reference removal from spec
3. woodworking_router.py Phase B audit (596 lines)
4. binding_design_router.py audit (589 lines)
5. Archtop Measurements + Benedetto folder reference commit
6. Redis caching setup
7. tap_tone_pi sandbox prototype build
