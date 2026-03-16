# ADR-002 — Instrument Project Graph as Platform Center

**Date:** 2026-03-15  
**Status:** Accepted  
**Supersedes:** ARCHITECTURE_MIGRATION_ASSESSMENT.md (2026-02-23)

---

## Context

The Production Shop codebase has grown through feature-by-feature addition without a shared data model. The result is scattered state across 30+ Pinia stores, disconnected backend calculators, and no canonical place for a builder's instrument design to persist between sessions.

Three planning sessions (March 2026) converged on an architectural elevation: the platform is not a toolbox of independent tools. It is a design operating system for musical instruments, centered on one shared object: `InstrumentProjectData`.

---

## Decision

We adopt a **four-layer architecture** with the Instrument Project Graph as the center:

```
Layer 0 — Instrument Project Graph   ← InstrumentProjectData, persisted in Project.data JSONB
Layer 1 — Engines                    ← Geometry Engine, Materials Intelligence, Analyzer
Layer 2 — Workspaces                 ← Blueprint Reader, Instrument Hub, Bridge Lab, Art Studio
Layer 3 — Utilities                  ← Stateless calculators, dual-mode (standalone + project context)
```

### Locked decisions (not to be re-litigated without a new ADR)

1. **`Project.data` JSONB** is the persistence home for `InstrumentProjectData`. No new database tables.
2. **Blueprint Reader** is the top-level design intake tool (Layer 2 Source). It is cross-instrument, not nested under any instrument hub.
3. **Instrument Hub** is the primary editor of project state. It is an orchestrator, not a calculator.
4. **Bridge Lab** is the first bounded workspace. It is the template for Neck Lab, Body Lab, and Bracing Lab.
5. **Utilities are ephemeral** unless invoked from project context. They never auto-persist.
6. **Analyzer enriches project state** with `AnalyzerObservation`. It never overrides `bridge_state`, `material_selection`, or `spec`.
7. **CAM reads validated project state** — never raw UI state.
8. **Router and folder consolidation is Phase 7** — after schema and ownership lines are established (Phases 1–6).
9. **Materials Intelligence is a reasoning engine**, not just a database wrapper. It serves Utilities, Instrument Hub, Analyzer, and CAM as a shared platform capability.
10. **No geometry formulas in Vue files.** All math lives in `instrument_geometry/` (backend) or composables that call the backend.

### Persistence rules

**Persist (in `InstrumentProjectData`):**
- `instrument_type`
- `spec` (scale length, fret count, neck angle, nut/heel widths)
- `blueprint_geometry` (with source + confidence + provenance)
- `bridge_state` (saddle location, compensation inputs, saddle projection)
- `neck_state`
- `material_selection` (per-role species IDs)
- `analyzer_observations` (append-only, advisory)
- `manufacturing_state`

**Derive on demand (never store):**
- Fret positions
- Break angle
- String tension
- Saddle compensation offsets
- Stiffness indices
- CAM toolpaths

---

## Implementation sequence

```
Phase 0 — Architecture freeze (this ADR + PLATFORM_ARCHITECTURE.md) ← DONE
Phase 1 — InstrumentProjectData schema + project state API
Phase 2 — Blueprint Reader writes BlueprintDerivedGeometry to project
Phase 3 — Instrument Hub reads/writes project state
Phase 4 — Bridge Lab as first bounded workspace
Phase 5 — Materials Intelligence Phase 1 (wire orphaned wood DB)
Phase 6 — Utilities dual-mode (standalone + project context)
Phase 7 — Router and folder structural consolidation
```

Phases 1–4 must execute sequentially. Phases 5–7 can partially overlap once Phase 1 is complete.

---

## Consequences

**Positive:**
- Every future feature has a clear home — the decision tree in `PLATFORM_ARCHITECTURE.md` resolves ambiguity
- Project state survives sessions, can be versioned, and can be shared
- Derived values are always correct because they are computed from canonical inputs
- The architecture supports future multi-instrument builds, team collaboration, and version history
- Router consolidation (Phase 7) becomes mechanical once domain ownership is clear

**Negative / risks:**
- Schema definition must be done carefully upfront — breaking changes require migration
- Stale Pinia stores must be actively retired as each phase completes
- `material_router.py` (CNC cutting energy data) must be merged into `materials/machining/` before it becomes a second permanent material authority

---

## Superseded approaches

- Per-feature Pinia stores as primary state — **superseded by project graph**
- `/calculators` under Business nav — **superseded by Utilities under Design nav**
- Router-first reorganization — **superseded by schema-first approach (Phase 7 is last, not first)**
- Separate acoustic/electric/violin hubs — **superseded by single Instrument Hub covering all instruments**
