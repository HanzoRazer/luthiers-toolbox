Below is a drop-in draft you can commit as
docs/CONSOLIDATION_PHASE.md.

It is written to reframe the audit findings as intentional architecture, not debt, and to give you (and future contributors) a clear, defensible contract for what is live vs planned.

CONSOLIDATION_PHASE.md
# CONSOLIDATION PHASE — SYSTEM STATUS & INTENT

**Project:** Luthier’s ToolBox / RMOS / CAM Platform  
**Date:** 2025-12-14  
**Purpose:**  
This document formally classifies all major subsystems into one of three states:

- **ACTIVE** — production-grade, trusted, and allowed to execute
- **SCAFFOLD** — interfaces defined, behavior intentionally incomplete
- **EXPERIMENTAL** — exploratory, isolated, not allowed to affect production

This classification is intentional and explains the presence of stubs, TODOs,
phantom imports, and archived data identified in the repository audit.

---

## 1. Architectural Philosophy (Why this exists)

This platform was designed **interface-first** to support:

- safety-critical CAM operations
- long-lived geometry correctness
- future AI-assisted planning without risk to operators or machines

As a result:
- Interfaces were stabilized early
- Execution logic was gated or stubbed
- Experimental systems were isolated
- No unsafe “partial implementations” were allowed into production paths

This document is the missing **activation map** that converts that scaffold
into a deliberate roadmap.

---

## 2. ACTIVE SYSTEMS (Production-Grade)

These subsystems are trusted, tested, and may execute in production.

### Core Platform
- `services/api/app/core/`
- `services/api/app/util/`
- `services/api/app/config/`
- `services/api/app/schemas/`
- `services/api/app/services/`
- `services/api/app/stores/`

### Calculators & Data Spine
- `services/api/app/calculators/`
- `services/api/app/data/`
- `services/api/app/tools/`

> These form the **physics / math / material truth layer** of the platform.

### Instrument Geometry (Current Focus)
- `instrument_geometry/`
- Fretboard geometry
- Neck outline & pocket geometry
- Sidewall meshes & solid meshes
- DXF-lite & GRBL-safe exports

### CAM Readiness Layer
- `services/api/app/cam_core/`
- `services/api/app/toolpath/`
- ProfileOpPlan
- Clearance offsets
- Ramp & helix entry logic
- GRBL G-code generation

### RMOS Core (Non-AI)
- `services/api/app/rmos/api/`
- `services/api/app/rmos/models/`
- `services/api/app/rmos/services/`

> RMOS defines *what may run*, not *how it runs*.

---

## 3. SCAFFOLD SYSTEMS (Intentional Stubs)

These subsystems have **defined interfaces** but **intentionally incomplete behavior**.
They represent **future phases**, not missing work.

### Geometry & CAM Extensions
- Advanced pocket strategies
- Multi-tool operations
- Post-processor variants beyond GRBL
- Step-over / step-down optimizers

### CNC Production (Non-Saw)
- `services/api/app/cnc_production/`
- Production orchestration hooks
- Job lifecycle management

### Saw Lab (Legacy / One-Pass Bundles)
- Legacy Saw Lab data
- Archived saw runs & telemetry
- Fixture-rich datasets preserved for schema evolution

> These are preserved as **fixtures**, not production dependencies.

### Why stubs exist here
- Prevent unsafe execution
- Preserve API contracts
- Allow parallel development
- Avoid rewriting downstream integrations later

---

## 4. EXPERIMENTAL SYSTEMS (Isolated by Design)

These systems are **explicitly excluded from production execution**.

They may:
- fail tests
- contain phantom imports
- change rapidly
- be incomplete

### AI & Analytics
- `services/api/app/_experimental/ai_core/`
- `services/api/app/_experimental/ai_cam/`
- `services/api/app/_experimental/ai_graphics/`
- `services/api/app/_experimental/analytics/`

### Experimental Infrastructure
- legacy `app/app/` namespace artifacts
- prototype orchestration code
- abandoned or exploratory pipelines

**Rules:**
- Experimental modules must never emit G-code
- Experimental modules must never bypass RMOS policy
- Experimental routers may remain unregistered

---

## 5. Interpretation of Audit Findings

### Phantom Imports
- Represent **declared future intent**
- Must be commented, not deleted
- Often reference SCAFFOLD or EXPERIMENTAL systems

### Stubs / TODOs
- Are *intentional safety gates*
- Mark planned activation points
- Must remain until the owning subsystem is promoted to ACTIVE

### Archived Data
- Represents **schema richness**, not obsolescence
- Preserved under `tests/fixtures/`
- Used to harden future loaders and validators

---

## 6. Promotion Rules (How systems move forward)

A subsystem may be promoted from:

### SCAFFOLD → ACTIVE only when:
- Execution paths are fully deterministic
- Safety invariants are enforced
- Golden snapshot tests exist
- RMOS policy coverage is explicit

### EXPERIMENTAL → SCAFFOLD only when:
- Interfaces stabilize
- Side effects are isolated
- Execution is gated behind feature flags

---

## 7. What NOT to do

- ❌ Do not delete stubs to “clean the repo”
- ❌ Do not comment out phantom imports
- ❌ Do not merge experimental logic into CAM paths
- ❌ Do not treat archived data as obsolete

These actions would destroy architectural signal.

---

## 8. Current Consolidation Goal

The goal of this phase is **clarity, not completion**.

Specifically:
- Make ACTIVE systems unquestionably solid
- Make SCAFFOLD systems obviously intentional
- Keep EXPERIMENTAL systems safely contained

Once consolidation is complete, activation can proceed subsystem by subsystem
without destabilizing the platform.

---

**Status:**  
This document defines the authoritative interpretation of repo state
as of December 2025.

Any future audit should be evaluated *against this classification*,
not against raw lint or static analysis counts.

Why this document matters (my closing thought)

With this file in place:

The audit report becomes evidence of maturity, not disorder

Orphaned code becomes intentional scaffolding, not debris

Future contributors won’t “clean” away your roadmap

You gain permission to move slowly and correctly on CAM safety

If you want, next I recommend we draft:

SUBSYSTEM_PROMOTION_CHECKLIST.md
→ a concrete checklist for moving one SCAFFOLD module to ACTIVE at a time (e.g., next CAM feature, next post-processor).