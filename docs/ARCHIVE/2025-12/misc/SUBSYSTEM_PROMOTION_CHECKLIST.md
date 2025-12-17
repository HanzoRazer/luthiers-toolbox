# SUBSYSTEM_PROMOTION_CHECKLIST.md

**Project:** Luthier’s ToolBox / RMOS / CAM Platform  
**Date:** 2025-12-15  
**Purpose:** A repeatable, auditable checklist to promote a subsystem from **EXPERIMENTAL → SCAFFOLD → ACTIVE** without destabilizing the monorepo or compromising CAM safety.

---

## 0) Definitions

### States
- **EXPERIMENTAL**
  - Exploratory code, unstable interfaces, may fail tests.
  - Must be isolated (e.g., `_experimental/`) and must not influence production outputs.
- **SCAFFOLD**
  - Interfaces are stable. Behavior may be incomplete.
  - Execution paths must be gated (no unsafe defaults).
- **ACTIVE**
  - Deterministic, tested, documented, and allowed to execute in production.

### Promotion Types
- **Type A:** EXPERIMENTAL → SCAFFOLD (interface stabilization + isolation)
- **Type B:** SCAFFOLD → ACTIVE (behavior completion + safety + tests)

---

## 1) Pre-Promotion Gate (Required for any promotion)

### 1.1 Identify the subsystem boundary
- [ ] Subsystem name and directory root declared (e.g., `services/api/app/cam_core/`)
- [ ] Owner modules listed (top-level Python packages / Vue packages)
- [ ] Public entrypoints listed:
  - [ ] API routers
  - [ ] Query keys (InstrumentGeometry API keys)
  - [ ] CLI commands
  - [ ] Background jobs / tasks (if any)

### 1.2 Dependency graph is explicit
- [ ] List inbound dependencies (who imports/calls this subsystem)
- [ ] List outbound dependencies (what it imports/calls)
- [ ] Confirm no circular imports across core boundaries
- [ ] Confirm experimental modules are not imported by ACTIVE paths

### 1.3 Repo hygiene gate
- [ ] No unanchored `.gitignore` rules that can hide production code
- [ ] No unexpected untracked files required for subsystem runtime
- [ ] Any required fixture files live under `tests/fixtures/` (not under `data/`)

---

## 2) EXPERIMENTAL → SCAFFOLD Checklist (Type A)

### 2.1 Isolation & gating
- [ ] Subsystem is located under `_experimental/` **OR** clearly marked as experimental
- [ ] No production router registration by default
- [ ] No ability to emit G-code or write machine-affecting outputs
- [ ] Feature flag or explicit enable switch exists (config/env)
- [ ] All external side effects disabled by default (file IO, network, device calls)

### 2.2 Interface stabilization
- [ ] Pydantic schemas defined for inputs/outputs
- [ ] Stable function signatures (no “wild” `**kwargs` without schema)
- [ ] Versioned payload format (e.g., `schema_version: 1`)
- [ ] Minimal docs for what is promised and what is stubbed

### 2.3 Safety policy declaration (CAM-related)
- [ ] Explicit statement: “This module may not output toolpaths/gcode”
- [ ] If it proposes plans, they must be “advisory” objects only (no execution)

### 2.4 Minimal tests
- [ ] One import test per module (ensures packaging correctness)
- [ ] One schema validation test per major payload
- [ ] One “no side effects” test (ensures no files written, no gcode produced)

**Exit criteria:** interfaces stable, no production coupling, tests validate no side effects.

---

## 3) SCAFFOLD → ACTIVE Checklist (Type B)

### 3.1 Determinism & invariants
- [ ] Deterministic output for same input (no random seeds, no time-based outputs)
- [ ] Inputs fully validated (schemas, bounds, units)
- [ ] Invariants declared and enforced:
  - [ ] Unit consistency (mm, degrees)
  - [ ] Coordinate system and datum rules
  - [ ] Winding/orientation conventions
  - [ ] No self-intersecting geometry produced (or handled safely)
  - [ ] Z-safe plane respected

### 3.2 Safety gates (CAM execution)
- [ ] Tool diameter, stepover, stepdown validated against material/tool policies
- [ ] Clamp/fixture safe margins enforced (Z-safe and entry strategies)
- [ ] No rapid moves inside material volume
- [ ] All plunge moves are controlled (ramp/helix policies available)
- [ ] Post processor output is bounded and validated (GRBL header/footer templates)

### 3.3 Golden tests (required for promotion to ACTIVE)
- [ ] At least 1 golden case exists (`tests/golden/cases/*.json`)
- [ ] Golden snapshot saved for:
  - [ ] 2D outlines (SVG or JSON polyline)
  - [ ] Mesh outputs (JSON vertex/tri counts + stable hashes)
  - [ ] OpPlan JSON (ProfileOpPlan)
  - [ ] G-code output (GRBL)
- [ ] Golden updater CLI exists and is documented
- [ ] Golden diffs reviewed and explainable

### 3.4 Performance & scalability checks
- [ ] Complexity bounded (O(n) / O(n log n) where appropriate)
- [ ] Worst-case polygon sizes tested (resampling limits enforced)
- [ ] No unbounded recursion or unbounded sampling loops
- [ ] Time budget measured for common cases (recorded in docs)

### 3.5 API wiring checks (if applicable)
- [ ] Router registration added (FastAPI)
- [ ] Route prefix matches conventions (`/api/...`)
- [ ] OpenAPI schema is stable and documented
- [ ] Auth/middleware policies applied (registry entitlements, security checks)
- [ ] Error responses are structured (no raw tracebacks)

### 3.6 Documentation minimums
- [ ] `docs/<SUBSYSTEM>.md` exists with:
  - [ ] Purpose + scope
  - [ ] Input schema examples
  - [ ] Output examples
  - [ ] Safety invariants
  - [ ] Known limitations
  - [ ] Roadmap for next steps
- [ ] Operator notes included where relevant (CAM usage, datum, zeroing)

**Exit criteria:** deterministic, safe, tested with golden snapshots, and documented.

---

## 4) Test Matrix (Minimum)

### Geometry-only subsystems
- [ ] Import + schema tests
- [ ] Golden outline snapshots
- [ ] Edge cases: tiny radii, concave outlines, degenerate points

### CAM/toolpath subsystems
- [ ] OpPlan JSON golden snapshot
- [ ] G-code golden snapshot
- [ ] Z-safe invariant test
- [ ] Entry strategy test (ramp/helix)
- [ ] Clearance envelope tests

### RMOS subsystems
- [ ] Context validation tests
- [ ] Policy enforcement tests
- [ ] “Refuse unsafe plan” test cases

---

## 5) Promotion Commit Protocol

### Required commit structure
- [ ] **Commit 1:** packaging + `__init__.py` + imports fixed (no behavior)
- [ ] **Commit 2:** schema + validators (still no execution)
- [ ] **Commit 3:** implementation + unit tests
- [ ] **Commit 4:** golden snapshots + updater CLI
- [ ] **Commit 5:** docs + router wiring

### Commit messages (recommended)
- `chore(<subsystem>): package hygiene + init files`
- `feat(<subsystem>): add schemas + validation`
- `feat(<subsystem>): implement <capability> + tests`
- `test(<subsystem>): add golden snapshots + updater`
- `docs(<subsystem>): add operator + dev docs`

---

## 6) Promotion Decision Log (Required)

For every subsystem promotion, append:

- Subsystem:
- From state → To state:
- Inputs/outputs stabilized:
- Safety invariants added:
- Golden cases added:
- Test pass rate before/after:
- Commit hashes:
- Reviewer notes:

---

## 7) Templates

### 7.1 Subsystem header comment (recommended)
Add to the root module:

```python
"""
SUBSYSTEM: <name>
STATE: SCAFFOLD|ACTIVE|EXPERIMENTAL
OWNER: <person/team>
INVARIANTS: <brief list>
"""
7.2 Golden case acceptance note
text
Copy code
Golden snapshots must not change without:
- a documented reason
- a version bump (schema_version or output_version)
- an updated operator note if CAM output changes
8) Common Failure Modes (What to watch)
Overbroad .gitignore hiding real code

Mixing experimental AI modules into CAM execution paths

“Works on my machine” fixtures stored under data/

Non-deterministic ordering in polygon resampling or triangulation

Silent unit mismatches (inch vs mm)

Unbounded stepdown loops causing infinite toolpath generation

9) Quick Start: Promoting one CAM feature (example)
If promoting “Pocket Solid Mesh (earclip caps)”:

 Deterministic triangulation order

 Golden mesh snapshot (counts + hash)

 OBJ export smoke test

 Degenerate polygon cleanup

 Document winding conventions (+Z top cap, -Z floor cap)

 Add “concave outline” golden case

css
Copy code
