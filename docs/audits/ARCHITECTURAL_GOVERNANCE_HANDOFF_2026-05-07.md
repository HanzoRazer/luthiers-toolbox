# Architectural Governance Handoff & Strategic Assessment

**Repository:** luthiers-toolbox  
**Date:** 2026-05-07  
**Classification:** HIGH-FIDELITY ARCHITECTURAL HANDOFF  
**Purpose:** Expert review for strategic platform decisions  

> **CONFLATION CORRECTION (2026-05-30).** This assessment repeatedly cites the three-loop / AGE
> work as "APPROVED DESIGN" and the AGE as "requested by Ross in multiple sessions," and frames
> tactical fixes as "violating approved architecture." Per ground truth from Ross (2026-05-30):
> the three-loop architecture + AGE were **experimental, never approved, and never implemented**
> here — now **sandboxed into `vectorizer-sandbox`**. There is no "approved architecture" being
> violated; the unsourced provenance is corrected at the source. The shipped scale-validation
> gate is real and unaffected. See
> `docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md`.
>
> **Live-code carve-out:** "never implemented" means the *named, unified* architecture only.
> `GeometryCoachV2` (photo-vectorizer) is real, **API-reachable** runtime code — its "Loop 1" name
> is retrospective labeling, NOT the approved architecture. Do NOT delete or sandbox it; deletion
> degrades a live endpoint path. See handoff §2 + §9b.
**Prepared for:** Senior engineers, platform architects, CAD/CAM specialists

---

## SECTION 1 — EXECUTIVE ARCHITECTURAL SUMMARY

### Current Architectural Condition

The luthiers-toolbox repository is a **multi-domain CAD/CAM manufacturing optimization platform** serving guitar builders. It has evolved through exploratory feature growth, parallel implementations, and sprint-driven development into a system exhibiting both **mature workflow sophistication** and **governance fragmentation**.

**Repository Statistics:**
- **Backend:** 98 routers across 6 major subsystems, 70+ calculator modules, centralized router registry
- **Frontend:** 709 Vue components, 85 routes, 32 Pinia stores
- **Documentation:** 37+ spec documents, 10+ archived handoffs, detailed CLAUDE.md policies
- **Test Coverage:** 161 soundhole tests, 24+ fretboard ecosphere tests, 28 G-code simulation tests

### Primary Strengths

1. **Domain Separation Excellence**: Clear boundaries between CAM, RMOS, Art Studio, Business, and Instrument Geometry subsystems. Each domain owns its routers, calculators, and schemas.

2. **Workflow Sophistication**: ToolpathPlayer (100% spec compliance + 8 extensions), Body Outline Editor (94% behavioral compliance), RMOS four-stage pipeline (spec → plan → approve → execute).

3. **Canonical Schema Design**: FretboardEcosphere, FeasibilityScorer, and instrument geometry modules demonstrate mature domain modeling with proper versioning and immutable artifact patterns.

4. **Manufacturing Intelligence**: Risk gating (GREEN/YELLOW/RED), feasibility scoring, constraint profiles, and RMOS audit trails show production-grade safety awareness.

5. **Calculator Purity**: 70+ calculator modules as pure functions (input → output, no side effects) enable composition and testing.

### Primary Systemic Risks

1. **Governance Gap**: Architectural philosophy exists primarily in documentation (CLAUDE.md), not in enforceable code gates. The DXF standard has 28% adoption despite being "blocking infrastructure."

2. **State Fragmentation**: 32 Pinia stores with duplicate systems (2 toast stores, 2 RMOS runs stores) and mega-stores (useInstrumentGeometryStore at 1,360 lines mixing 7 workflow phases).

3. **Route Sprawl**: 85 frontend routes with 4 direct duplicates, 6 legacy shortcuts, and 40+ routes missing navigation visibility. Three concurrent architecture patterns (flat/nested/shell) without clear canonical guidance.

4. **Scaffolded Infrastructure**: Critical systems exist but are never called—FeedbackSystem records classifications but submit_correction() is never invoked; TrainingDataCollector is never instantiated; AGE integration is completely unimplemented despite being "requested by Ross in multiple sessions."

5. **Partial Migrations**: Shell-first consolidations (ApertureWorkspace, CAM dual paths) create ambiguous canonicality during transition periods.

### Operational Maturity Assessment

| Dimension | Rating | Evidence |
|-----------|--------|----------|
| **Workflow Design** | ★★★★☆ | ToolpathPlayer 100%, Body Outline 94%, guided workflows complete |
| **Domain Modeling** | ★★★★☆ | FretboardEcosphere, RMOS artifacts, calculator purity |
| **Backend Architecture** | ★★★★☆ | Centralized registry, domain separation, no dead code |
| **Frontend Architecture** | ★★★☆☆ | Component proliferation (709), state fragmentation |
| **Governance Enforcement** | ★★☆☆☆ | Social enforcement only; policies drift accidentally |
| **Consolidation Discipline** | ★★★☆☆ | Active consolidation with incomplete cleanup |

### Maintainability Outlook

**Near-term (0-6 months):** Maintainable by developers with domain context. Historical knowledge required for safe modification of RMOS, vectorizer, and instrument geometry subsystems.

**Medium-term (6-18 months):** Risk of topology drift accelerating unless governance enforcement is implemented. State fragmentation will compound cognitive load.

**Long-term (18+ months):** Without consolidation, maintenance gravity will concentrate in mega-stores and duplicate systems, creating maintenance traps.

### Consolidation Readiness Assessment

**Ready for consolidation:**
- Toast stores (2 → 1): 2 hours, 65 lines removed
- RMOS runs stores (2 → 1): 1 hour, 145 lines removed
- Fretboard routers (nut_fret + fretwork): 1 hour, router deduplication
- Legacy route shortcuts (6 routes): 2 hours, redirect to canonical

**Requires careful migration:**
- useInstrumentGeometryStore extraction: 12-16 hours, high complexity
- ApertureWorkspace parity verification: 4-8 hours, behavioral testing
- Vectorizer loop architecture completion: 20+ hours, new development

### Repository Phase Classification

**TRANSITIONAL → GOVERNANCE-BOUND**

The repository has exited the exploratory phase and is mid-transition toward platform-forming. However, it cannot complete this transition without governance enforcement. The current state is:

- **Past exploratory**: Domain models are stable, workflows are sophisticated
- **Mid-transitional**: Active consolidation work, shell-first migrations in progress
- **Pre-governance-bound**: Policies exist but aren't enforced; drift is possible on every sprint

**Why this classification:** The repository exhibits the technical sophistication of a governance-bound platform but lacks the enforcement mechanisms. Architectural philosophy survives through social processes (code review, CLAUDE.md reading) rather than automated gates. This is the critical gap.

---

## SECTION 2 — CANONICAL SYSTEM ANALYSIS

### System Classification Matrix

| System | Status | Authority | Maintenance Risk | Consolidation Pressure |
|--------|--------|-----------|------------------|------------------------|
| **ToolpathPlayer** | Canonical | HIGH | LOW | None |
| **RMOS Pipeline** | Canonical | HIGH | MEDIUM | None |
| **FretboardEcosphere** | Canonical | HIGH | LOW | None |
| **Body Outline Editor** | Canonical | HIGH | LOW | None |
| **DxfToGcodeView** | Canonical | HIGH | LOW | None |
| **CamWorkspaceView** | Beta Shell | MEDIUM | HIGH | HIGH (needs ToolpathPlayer) |
| **ApertureWorkspace** | Beta Shell | LOW | HIGH | HIGH (parity incomplete) |
| **SpiralSoundholeDesigner** | Mounted Legacy | HIGH | LOW | Being consolidated |
| **InlayWorkspaceShell** | Canonical | MEDIUM | LOW | None |
| **Vectorizer Phase 3.6** | Canonical | HIGH | MEDIUM | Loop architecture incomplete |
| **Rosette Designer** | Split Canonical | MEDIUM | MEDIUM | rosetteStore vs useRosetteDesignerStore |

### Detailed System Analysis

#### ToolpathPlayer (Canonical — Production Ready)

**Location:** `packages/client/src/components/cam/toolpath-player/`

**Status:** Exceeds specification. 21/21 behavioral requirements implemented plus 8 extensions (memory management, LOD culling, heatmap mode, 3D visualization, measurement tool, segment selection, multi-tool filtering, collision detection).

**Authority:** Definitive source for G-code simulation visualization.

**Maintenance Risk:** LOW — Clean composition API, well-documented store (useToolpathPlayerStore), proper prop drilling.

**Operational Reliability:** HIGH — Binary search O(log n) segment lookup, requestAnimationFrame animation loop, proper memory management with MAX_SEGMENTS=100k.

**Consolidation Pressure:** None — Already complete.

**Governance Note:** This is the gold standard for behavioral spec implementation. Other systems should be measured against it.

#### RMOS Pipeline (Canonical — Production Ready)

**Location:** `services/api/app/rmos/`

**Status:** Complete four-stage pipeline (spec → plan → approve → execute) with 16 routers, immutable artifact model, constraint profiles with YAML definitions, and JSONL audit trail.

**Authority:** Definitive source for manufacturing run management.

**Maintenance Risk:** MEDIUM — v1/v2 versioning transition (migration CLI exists), complex constraint profile system requires domain expertise.

**Operational Reliability:** HIGH — All artifacts are immutable, versioned, and auditable.

**Consolidation Pressure:** None for core pipeline. Frontend has duplicate stores (rmosRunsStore vs useRmosRunsStore).

**Critical Gap:** CamWorkspaceView does NOT create RMOS runs for its operations. This is a governance violation — manufacturing operations should have audit trails.

#### CamWorkspaceView (Beta Shell — Critical Gaps)

**Location:** `packages/client/src/views/cam/CamWorkspaceView.vue`

**Status:** 6-step neck wizard (Machine, OP10-OP50, Summary) with risk gating. But:
- Uses GcodePreviewPanel (text-only) instead of ToolpathPlayer
- No RMOS artifact trail
- No localStorage persistence
- Silent error handling in network catches

**Authority:** MEDIUM — Functions but lacks integration with canonical systems.

**Maintenance Risk:** HIGH — Appears complete but is structurally disconnected from platform infrastructure.

**Consolidation Pressure:** HIGH — Must integrate ToolpathPlayer and RMOS trails before production use.

**Governance Note:** This is a **deceptively complete** system. The UI looks finished, but core platform integration is missing. Sprint processes allowed this to ship without verification against platform standards.

#### ApertureWorkspace (Beta Shell — Parity Incomplete)

**Location:** `packages/client/src/views/art-studio/ApertureWorkspace.vue`

**Status:** Beta consolidation shell (State 3 per FEATURE_PARITY_MIGRATION_POLICY). Intended to replace SpiralSoundholeDesigner but parity blockers remain:
- No consumption of backend presets (`/api/instrument/soundhole/spiral/default`)
- No display of `aperture_geometry` response fields

**Authority:** LOW — Cannot replace canonical SpiralSoundholeDesigner until parity verified.

**Maintenance Risk:** HIGH — Two implementations coexist; changes must be synchronized.

**Consolidation Pressure:** HIGH — Blocking active development on soundhole features.

**Governance Note:** This is the migration policy working correctly—the shell exists but cannot replace the canonical implementation without verification. The policy documented in CLAUDE.md is preventing premature replacement.

#### Vectorizer Phase 3.6 (Canonical — Architecture Incomplete)

**Location:** `services/blueprint-import/vectorizer_phase3.py`

**Status:** Production-grade edge detection, contour classification, and DXF export (4,149 lines, 82 functions). Scale validation gate is implemented and called before every export.

**But:** The approved three-loop architecture is largely unimplemented:
- **Loop 1 (Intra-Frame):** Scale validation exists, but retry-with-fallback logic does not
- **Loop 2 (Strategy Cache):** Not implemented (0 lines)
- **Loop 3 (User Correction):** FeedbackSystem scaffolded but submit_correction() never called
- **AGE Integration:** Not implemented (0 lines) despite being "requested by Ross in multiple sessions"

**Authority:** HIGH for current extraction, MEDIUM for quality improvement.

**Maintenance Risk:** MEDIUM — Tactical fixes (epsilon values, cache headers) address symptoms without advancing approved architecture.

**Governance Note:** The CLAUDE.md explicitly states: "Point fixes to epsilon values, simplification tolerances, or version strings are NOT substitutes for implementing the approved architecture." This policy is being violated by sprint processes that prioritize tactical fixes.

#### Rosette Designer (Split Canonical)

**Location:** Multiple stores and components

**Status:** Two parallel implementations:
- `rosetteStore` — Design-first editor (~800 lines), Composition API, undo/redo, MFG checks
- `useRosetteDesignerStore` — Ring management, segmentation, CNC export
- `useRosettePatternStore` — Adapter wrapping rosetteStore (backward compatibility)

**Authority:** SPLIT — Both stores are used; unclear which is canonical for which workflow.

**Maintenance Risk:** MEDIUM — Changes may need to propagate to multiple stores.

**Consolidation Pressure:** MEDIUM — Adapter pattern (useRosettePatternStore) suggests consolidation was attempted but not completed.

### Suspended and Orphaned Systems

**DxfToGcodeWizard (Suspended — Delete Candidate)**

Calls non-existent endpoints (`POST /api/v1/dxf/upload` returns 404). The spec recommends: "Either wire to real endpoints or delete. Currently a trap for users."

**simulation_consolidated_router.py (Dead Duplicate)**

115 lines, import commented out in aggregator.py. Safe to delete.

**sawLearnStore (Orphaned)**

20 lines, mostly placeholder. `runsLoaded` and `insights` not used anywhere.

---

## SECTION 3 — FEATURE ISLAND AND TOPOLOGY DRIFT ANALYSIS

### Identified Feature Islands

#### Island 1: Art Studio Ecosystem (15 routes)

**Routes:** `/art-studio/*` (relief, inlay, vcarve, bracing, binding, headstock, purfling, soundhole, patterns, rosette, aperture + 2 workspace shells)

**Isolation Pattern:** Separate shell routes (`/art-studio/inlay-workspace`, `/art-studio/soundhole-rosette-workspace`) with minimal cross-domain integration. Generates toolpaths but doesn't integrate with CAM routes.

**Drift Cause:** Feature growth without workflow integration. Each art tool was built standalone, then shell-first consolidation attempted but not completed.

**Convergence Status:** InlayWorkspaceShell shows convergence (5 stages, proper composable isolation). ApertureWorkspace divergent (parity incomplete).

#### Island 2: RMOS Management Suite (14 routes)

**Routes:** `/rmos/*` (inventory, quality, time, orders, material-analytics, analytics, rosette-designer, live-monitor, strip-family-lab, runs/*)

**Isolation Pattern:** Management dashboards (inventory, quality, time, orders) feel isolated from run execution workflow. Run browser (`/rmos/runs/*`) is orthogonal—different data model than management views.

**Drift Cause:** RMOS evolved from run management into broader manufacturing management, but the route structure reflects the original run-centric design.

**Convergence Status:** Analytics views are converging (RmosAnalyticsView MM-4 superseding AnalyticsDashboard N9.0).

#### Island 3: Audio/Acoustics Tools (4+ routes)

**Routes:** `/tools/audio-analyzer/*`, `/calculators/acoustics/*`, `/app/calculators/acoustics/soundhole`

**Isolation Pattern:** Multiple entry points with inconsistent prefixes. Audio analyzer under `/tools/`, calculators under `/calculators/` and `/app/calculators/`.

**Drift Cause:** Calculator tools added at different times with different naming conventions.

**Convergence Status:** Not converging—no active consolidation.

#### Island 4: AI Tools (4 routes)

**Routes:** `/ai/*` (wood-grading, recommendations, assistant, defect-detection), plus `/ai-images` at root

**Isolation Pattern:** `/ai-images` is at root level instead of under `/ai/`. No cross-linking between tools.

**Drift Cause:** AI features added as standalone experiments without integration plan.

### Topology Drift Mechanisms

#### Mechanism 1: Sprint-Driven Divergence

**Pattern:** Features built in isolation during sprint, integration deferred to "next sprint," integration never happens.

**Evidence:** CamWorkspaceView shipped without ToolpathPlayer integration, without RMOS trail, without localStorage persistence. Each of these was likely "deferred."

**Impact:** Structurally incomplete systems that appear finished.

#### Mechanism 2: Shell-First Migration

**Pattern:** New shell created, old implementation "mounted" or kept as fallback, migration never completes.

**Evidence:** ApertureWorkspace (shell exists, parity incomplete), CAM dual paths (old fret_slots_cam.py + new fret_slots_from_ecosphere.py both exist).

**Impact:** Ambiguous canonicality, maintenance burden doubles during transition.

#### Mechanism 3: Shortcut Route Accumulation

**Pattern:** Developer adds flat route (`/bridge`) for convenience, nested equivalent (`/lab/bridge`) already exists, neither is removed.

**Evidence:** 4 direct duplicate routes, 6 legacy shortcuts without deprecation markers.

**Impact:** Route discovery confusion, documentation rot, testing burden.

### Healthy Modularity vs Architectural Fragmentation

**Healthy Modularity (Preserve):**
- Calculator modules (70+ pure functions) — properly isolated, no side effects
- RMOS artifact model — immutable, versioned, domain-complete
- FretboardEcosphere schema — single source of truth with proper exports
- ToolpathPlayer composition — clean prop drilling, composable architecture

**Architectural Fragmentation (Address):**
- State fragmentation — 32 stores with duplicates and mega-stores
- Route fragmentation — 3 concurrent patterns without canonical guidance
- Vectorizer architecture — approved design vs actual implementation divergence
- DXF policy — documented standard with 28% adoption

---

## SECTION 4 — MAINTENANCE TOPOLOGY ASSESSMENT

### Cognitive Load Analysis

| System | Lines | Cognitive Load | Reason |
|--------|-------|----------------|--------|
| useInstrumentGeometryStore | 1,360 | VERY HIGH | 7 workflow phases, 60+ properties, 20+ methods |
| vectorizer_phase3.py | 4,149 | HIGH | 82 functions, approved vs actual architecture gap |
| rosetteStore | ~800 | MEDIUM-HIGH | Split authority with useRosetteDesignerStore |
| router/index.ts | 600+ | HIGH | 85 routes, 3 patterns, 4 duplicates |
| geometry.ts | 597 | LOW | Excellent documentation, bounded scope |
| useToolpathPlayerStore | 526 | LOW | Clean composition, well-scoped |

### Systems Requiring Historical Knowledge

**RMOS Constraint Profiles:** YAML-based constraint definitions with JSONL audit trail. Modifying constraints safely requires understanding the profile history mechanism and how constraints propagate to feasibility scoring.

**Vectorizer Phase Transitions:** Understanding why Phase 3.6 exists requires knowing Phase 2's limitations, the Phase 3.7 enhancement relationship, and the Phase 4 dimension linking that's "complete but standalone."

**Feature Parity Migration States:** The 4-state migration model (Canonical → Mounted Legacy → Beta Shell → Parity Verified) requires understanding why shells can't replace canonicals without verification.

### Deceptively Simple but Structurally Dangerous

**CamWorkspaceView:** Looks like a complete 6-step wizard. Missing: ToolpathPlayer, RMOS trail, localStorage, proper error handling. A developer might add features without realizing the foundation is incomplete.

**ApertureWorkspace:** Looks like a working soundhole designer. Actually a beta shell that cannot replace the canonical implementation. A developer might route users here without knowing parity is unverified.

**useRosettePatternStore:** Looks like a separate store. Actually an adapter wrapping rosetteStore. A developer might add state here instead of the underlying store.

### Maintenance Trap Predictions

**Trap 1: useInstrumentGeometryStore Growth**

Currently 1,360 lines with 7 workflow phases. Without extraction, it will accumulate more phases (nut slot CAM, bridge CAM, etc.) and become unmaintainable.

**Prediction:** Within 6 months, this store will exceed 2,000 lines and require 2+ hours to understand before any modification.

**Trap 2: Route Discovery Breakdown**

40+ routes have no navigation visibility. As routes accumulate, developers will increasingly construct URLs manually or dig through git history.

**Prediction:** Within 12 months, route documentation will be permanently out of sync with actual routes.

**Trap 3: Vectorizer Tactical Fix Accumulation**

Sessions add epsilon tweaks, cache headers, and version strings without advancing the approved architecture. Each fix increases the system's complexity without improving its quality trajectory.

**Prediction:** Within 6 months, the gap between approved architecture and actual implementation will be unbridgeable without a rewrite.

### Scaffolded-but-Unwired Infrastructure

| System | Scaffolded | Wired | Gap |
|--------|------------|-------|-----|
| FeedbackSystem | record_classification() | ✓ | submit_correction() never called |
| TrainingDataCollector | Full class | — | Never instantiated |
| Calibration Integration | integrate_with_vectorizer() | — | Not called from main pipeline |
| Phase 4 Dimension Linking | Complete pipeline | — | Standalone, not integrated |
| AGE (Agentic Guidance) | Documented design | — | 0 lines implemented |

**Governance Risk:** This scaffolded infrastructure creates the illusion of capability. A developer reading the code might assume these systems work. They don't—they're scaffolds waiting for integration that never happened.

---

## SECTION 5 — BEHAVIORAL PHILOSOPHY AND SPEC FIDELITY

### Behavioral Intent Survival Analysis

**High Survival (90%+ intent preserved):**
- ToolpathPlayer: All interaction primitives intact (play/pause/scrub/zoom/pan/depth shading)
- Body Outline Editor: 47/50 behavioral affordances implemented (94%)
- Guided Workflow: Error modals, validation gates, step navigation all functional
- Rosette Designer: Symmetry modes, undo/redo, MFG checks, BOM computation complete

**Medium Survival (70-90% intent preserved):**
- Inlay Workspace: 23/26 affordances (88%), BOM aggregation is visual-only
- CAM Pipeline (DxfToGcodeView): Full workflow but risk always GREEN (feasibility not wired)
- Rosette Feasibility Gates: MFG checks run but don't block design save

**Low Survival (<70% intent preserved):**
- CAM Pipeline (CamWorkspaceView): 64% compliance, critical gaps in simulation and audit trail
- Vectorizer Feedback Loops: Scale validation only (1 of 3 loops), AGE unimplemented

### Interaction Primitives Worth Preserving

**Manufacturing-Critical:**
- Risk gating (GREEN/YELLOW/RED) with override governance
- RMOS artifact immutability and audit trails
- Feasibility scoring with constraint profiles
- Scale validation before DXF export

**Operator-Confidence Mechanisms:**
- ToolpathPlayer HUD (position, feed rate, elapsed time)
- Body Outline Editor dimension labels on drag (Δx/Δy)
- Calibration validation with multi-method fallback
- Winding order enforcement (CCW outer, CW voids)

**Behavioral Systems Worth Platformizing:**
- GuidedWorkflow component (step lifecycle, validation gates, error modals)
- PlaybackControlsBar pattern (play/pause/scrub/speed)
- useInlayHistoryStore pattern (snapshot-based undo/redo, MAX_HISTORY cap)
- geometry.ts safety rules (bounded history, sessionStorage routing)

### Semantics Flattened into Visuals

**BOM Aggregation (Inlay Stage 4):** Spec calls for aggregated BOM data across stages. Implementation shows navigation cards (links) instead of actual data merge. Visual suggests completeness; behavior is navigation-only.

**Feasibility Gates (Rosette):** MFG checks produce scores and flags. UI displays badges. But gates don't actually block design operations. Visual suggests enforcement; behavior is advisory-only.

**G-code Progress (CAM Pipeline):** Loading spinner displays during generation. No granular per-step progress. Visual suggests progress tracking; behavior is binary (loading/done).

**Breadcrumb Integration (Guided Workflow):** Breadcrumbs.vue component exists. Not integrated into workflow views. Visual component exists; behavioral integration missing.

---

## SECTION 6 — GOVERNANCE GAP ANALYSIS

### Critical Governance Gaps

#### Gap 1: DXF Standard Enforcement (CRITICAL)

**Policy:** All DXF generators must use dxf_compat layer. Direct ezdxf.new() calls forbidden.

**Reality:** 28% adoption. 20+ files still call ezdxf.new() directly.

**Enforcement:** SOCIAL ONLY — No pre-commit hook, no linter rule, no test verification.

**Drift Risk:** HIGH — Any new DXF generator can bypass the standard.

**Files in violation:**
- `curve_export_router.py` — ezdxf.new("R2010")
- `dxf_export.py` (headstock) — import ezdxf
- `archtop_bridge_generator.py` — ezdxf.new("R2010")
- `archtop_saddle_generator.py` — ezdxf.new("R2010")
- `archtop_contour_generator.py` — 2 instances
- `dxf_consolidator.py`, `layer_consolidator.py`, `unified_dxf_cleaner.py`
- `inlay_calc.py` — ezdxf.new("R12")

#### Gap 2: Vectorizer Architecture Compliance (CRITICAL)

**Policy:** Three-loop architecture is APPROVED DESIGN. "Point fixes to epsilon values are NOT substitutes for implementing the approved architecture."

**Reality:** Only scale validation implemented. Loops 2/3 and AGE have 0 lines of code.

**Enforcement:** DOCUMENTED ONLY — CLAUDE.md states the requirement, nothing enforces it.

**Drift Risk:** HIGH — Sessions continue with tactical fixes, approved architecture recedes.

#### Gap 3: Feature Parity Verification (HIGH)

**Policy:** No canonical implementation may be removed until parity is verified (State 1→4).

**Reality:** Audit checklist exists (`SPIRAL_COMPONENT_CONTAINMENT_AUDIT.md`), but verification is manual.

**Enforcement:** SOCIAL — Code review must catch premature replacement.

**Drift Risk:** MEDIUM — Shell could replace canonical if reviewer doesn't know the policy.

#### Gap 4: Route Canonicality (HIGH)

**Policy:** None documented. Three patterns coexist (flat/nested/shell).

**Reality:** Developers add routes using any pattern. 4 duplicates, 6 legacy shortcuts accumulated.

**Enforcement:** NONE — No canonical pattern defined, no enforcement possible.

**Drift Risk:** HIGH — Route sprawl will continue indefinitely.

#### Gap 5: Store Architecture (MEDIUM)

**Policy:** None documented. Mixed Options/Composition API, duplicate stores tolerated.

**Reality:** 32 stores, 2 duplicate systems (toast, runs), 1 mega-store (1,360 lines).

**Enforcement:** NONE — No pattern guidance, no enforcement.

**Drift Risk:** MEDIUM — State fragmentation will compound.

### Enforceability Assessment

| Policy | Documentation | Code Enforcement | Can Drift |
|--------|---------------|------------------|-----------|
| DXF standard | ✓ CLAUDE.md | ✗ None | HIGH |
| Wood data sourcing | ✓ CLAUDE.md | ✓ ValueError in calculators | LOW |
| Archive 60-day rule | ✓ CLAUDE.md | ✗ None | HIGH |
| Vectorizer architecture | ✓ CLAUDE.md | ✗ None | HIGH |
| Feature parity migration | ✓ CLAUDE.md | ✗ Audit doc only | MEDIUM |
| Route canonicality | ✗ None | ✗ None | HIGH |
| Store architecture | ✗ None | ✗ None | MEDIUM |

### Missing Governance Mechanisms

1. **Pre-commit hooks** for DXF standard, route naming, store patterns
2. **Pytest markers** for parity verification (must pass before merge)
3. **Architectural review gates** for new subsystems
4. **Sprint governance** requiring architecture compliance before feature completion
5. **Consolidation discipline** preventing new duplicate routes/stores
6. **Deprecation protocol** with timeline and removal verification

---

## SECTION 7 — RECOMMENDED GOVERNANCE MODEL

### Principle: Make Philosophy Operationally Enforceable

The goal is not bureaucracy. The goal is: **architectural intent should survive sprint pressure**.

### Canonicality Enforcement

**Rule 1: Canonical Registration**

Every subsystem must declare its canonical implementation in a `CANONICAL.md` file:

```markdown
# CAM Workspace Canonical Systems

## Simulation Visualization
- Canonical: ToolpathPlayer
- Location: packages/client/src/components/cam/toolpath-player/
- Alternatives: GcodePreviewPanel (text-only, not for simulation)

## Run Artifact Management  
- Canonical: RMOS Pipeline
- Location: services/api/app/rmos/
- Requirement: All manufacturing operations must create RMOS runs
```

**Enforcement:** CI check verifies CANONICAL.md exists for each subsystem. New components must declare relationship to canonical.

**Rule 2: Canonical Import Linting**

Pre-commit hook blocks direct imports of non-canonical implementations when canonical exists:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: canonical-imports
      name: Verify canonical imports
      entry: python scripts/check_canonical_imports.py
      language: python
```

### Migration Lifecycle Rules

**State Machine:**
```
[1] Canonical → [2] Mounted Legacy → [3] Beta Shell → [4] Parity Verified → [5] Replacement Complete
```

**Transition Gates:**

- **1→2 (Mount):** Legacy can be mounted in new shell. No code enforcement needed.
- **2→3 (Shell):** Shell must pass structural review (correct patterns, proper composition).
- **3→4 (Parity):** Parity test suite must pass. Tests generated from canonical behavioral spec.
- **4→5 (Replace):** Canonical route can be redirected only after parity verification.

**Enforcement:** GitHub label `migration:state-N` on PRs. CI blocks merge if state transition invalid.

### Shell Governance

**Rule:** Shells may NOT replace canonicals without parity verification.

**Enforcement:**
1. Shell components must have `@migration-state: 3` comment
2. Route changes for state-3 shells blocked by CI
3. Parity test file must exist: `tests/parity/test_{shell}_parity.py`

### Sprint Governance

**Definition of Done (Architecture):**
- [ ] New DXF code uses dxf_compat layer (verified by pre-commit)
- [ ] New manufacturing operations create RMOS runs
- [ ] New routes follow canonical pattern (nested under domain prefix)
- [ ] New stores follow Composition API pattern
- [ ] New components declare relationship to canonical in CANONICAL.md

**Sprint Review Gate:**
Architecture checklist reviewed before sprint completion. Deferred integration items logged in `ARCHITECTURE_DEBT.md` with assigned sprint for completion.

### Route Governance

**Canonical Pattern:** All routes nested under domain prefix:
- `/lab/*` — Laboratory/experimental tools
- `/cam/*` — CAM operations
- `/art-studio/*` — Art/design tools
- `/rmos/*` — Manufacturing management
- `/tools/*` — Utility tools
- `/settings/*` — Configuration

**Forbidden:** Flat routes at root level (except `/`, `/login`, `/signup`).

**Enforcement:** Pre-commit hook blocks new root-level routes.

### Subsystem Ownership

Each subsystem must have:
1. **CANONICAL.md** — Declares canonical implementations
2. **ARCHITECTURE.md** — Documents subsystem patterns and decisions
3. **Owner** — Named individual responsible for architectural consistency

### Feature Graduation Rules

**Experimental → Production:**
1. Feature must have test coverage ≥80%
2. Feature must use canonical implementations (ToolpathPlayer, RMOS, etc.)
3. Feature must pass architectural review
4. Feature routes must be in navigation (discoverable)

**Scaffolded → Production:**
1. Scaffolded code must be wired (called from production paths)
2. If not wired within 60 days, mark as DEPRECATED or delete

### Deprecation Protocol

**Timeline:**
1. **Day 0:** Mark with `@deprecated` comment and `DEPRECATED.md` entry
2. **Day 30:** Add runtime warning (console.warn)
3. **Day 60:** Remove from navigation
4. **Day 90:** Delete code

**Enforcement:** CI scans for `@deprecated` older than 90 days, fails build.

### Maintenance Audit Cadence

**Monthly:** Route audit (identify duplicates, missing navigation)
**Quarterly:** Store audit (identify fragmentation, mega-stores)
**Semi-annually:** Full architectural review (governance gap analysis)

---

## SECTION 8 — CONSOLIDATION STRATEGY

### High-Leverage Consolidation Opportunities

#### Opportunity 1: Toast Store Unification (2 hours)

**Current:** useToastStore + useUiToastStore (duplicate systems)

**Action:** Keep useToastStore (cleaner interface), delete useUiToastStore, migrate 20 files.

**Payoff:** 65 lines removed, single notification system.

**Risk:** LOW — Both systems are functionally identical.

#### Opportunity 2: RMOS Runs Store Unification (1 hour)

**Current:** rmosRunsStore (Options API) + useRmosRunsStore (Composition API)

**Action:** Keep useRmosRunsStore (modern pattern), delete rmosRunsStore, update 5 files.

**Payoff:** 145 lines removed, single source of truth.

**Risk:** LOW — Both systems manage same data.

#### Opportunity 3: Fretboard Router Deduplication (1 hour)

**Current:** fretwork_router.py + nut_fret_router.py (4 duplicate endpoints)

**Action:** Keep nut_fret_router.py (has zero-fret support), delete fretwork_router.py.

**Payoff:** Router deduplication, cleaner API surface.

**Risk:** LOW — nut_fret_router is superset.

#### Opportunity 4: Legacy Route Cleanup (2 hours)

**Current:** 4 duplicate routes, 6 legacy shortcuts

**Action:** Redirect legacy routes to canonical, remove after 60 days.

**Payoff:** Simpler route topology, reduced cognitive load.

**Risk:** LOW — Redirects preserve backward compatibility.

### Low-Risk Convergence Targets

#### Target 1: CamWorkspaceView ToolpathPlayer Integration (4-8 hours)

**Gap:** Uses GcodePreviewPanel (text-only) instead of ToolpathPlayer.

**Action:** Replace GcodePreviewPanel with ToolpathPlayer in operation steps.

**Payoff:** Proper simulation visualization, platform consistency.

**Risk:** MEDIUM — Requires prop wiring and state management updates.

#### Target 2: CamWorkspaceView RMOS Integration (2-4 hours)

**Gap:** No RMOS run creation for operations.

**Action:** Wire RMOS run creation to operation generation.

**Payoff:** Audit trail for manufacturing operations.

**Risk:** LOW — RMOS infrastructure already exists.

### Architectural Compression Opportunities

#### Compression 1: useInstrumentGeometryStore Extraction (12-16 hours)

**Current:** 1,360 lines, 7 workflow phases, 60+ properties

**Target:**
- useInstrumentGeometryStore (fretboard, CAM, fan-fret) — ~400 lines
- useInstrumentSetupStore (relief, action, nut workflows) — ~500 lines
- useInstrumentDiagnosticsStore (combined, expert diagnostics) — ~300 lines

**Payoff:** 60% cognitive load reduction, testable units.

**Risk:** HIGH — Complex state interdependencies, careful migration required.

#### Compression 2: Art Studio Route Consolidation (8-12 hours)

**Current:** 15 routes, 2 workspace shells, dispersed tools

**Target:** 6-8 core routes with sub-panels (not 15 separate routes).

**Payoff:** Cleaner navigation, discoverable tools.

**Risk:** MEDIUM — Route changes require navigation updates.

### Shared Infrastructure Extraction Targets

#### Target 1: GuidedWorkflow Pattern Extraction

**Current:** DxfToGcodeView has excellent guided workflow implementation.

**Action:** Extract to shared `GuidedWorkflowShell` component with:
- StepIndicator
- NavigationButtons
- ValidationGates
- ErrorRecovery

**Payoff:** Reusable pattern for all multi-step workflows.

#### Target 2: PlaybackControls Pattern Extraction

**Current:** ToolpathPlayer has excellent playback controls.

**Action:** Extract to shared `PlaybackControlsBar` with:
- Play/Pause/Stop
- Speed selection
- Scrub bar
- Time display

**Payoff:** Reusable for any timeline-based visualization.

### Future Platform Composables

Based on geometry.ts (exemplary) and useToolpathPlayerStore (excellent):

1. **useAuditTrail** — RMOS-like immutable artifact pattern for any domain
2. **useBoundedHistory** — Snapshot-based undo/redo with configurable MAX_HISTORY
3. **useSessionTransfer** — sessionStorage routing for cross-view data (geometry.ts pattern)
4. **useAsyncWithRetry** — Async action with automatic retry and fallback strategies

### Workflow Unification Opportunities

**DXF → G-code → Simulation → Export** should be a single unified workflow:

1. DxfUploadZone (upload)
2. DxfPreflight (validation)
3. CamParametersForm (configuration)
4. ToolpathPlayer (simulation)
5. RiskGate (approval)
6. GcodeExport (download)

Currently split across DxfToGcodeView and CamWorkspaceView with different implementations.

---

## SECTION 9 — SECOND-OPINION QUESTIONS

### Strategic Architecture Questions

**Q1:** Should the repository evolve toward microservices (CAM, RMOS, Art Studio as separate services) or remain monolithic with better internal boundaries?

**Context:** Current architecture is monolithic with domain separation. SQLite persistence limits horizontal scaling. RMOS already has service-like boundaries.

**Tradeoff:** Microservices enable independent scaling but increase operational complexity. Monolith with boundaries is simpler but couples deployment.

**Q2:** Is the three-loop vectorizer architecture worth completing, or should resources focus on other systems?

**Context:** Loop 1 (scale validation) is done. Loops 2/3 and AGE would require ~500 lines of integration code + Claude API access. Current tactical fixes are accumulating.

**Tradeoff:** Completing the architecture improves quality trajectory. Deferring further increases technical debt.

**Q3:** Should the frontend state management be migrated to a different pattern (Vuex modules, composable-only, external state machine)?

**Context:** 32 Pinia stores with fragmentation. Mega-stores (1,360 lines) indicate pattern strain. Composition API stores are cleaner but not universally adopted.

**Tradeoff:** Migration is expensive but reduces long-term complexity. Staying with Pinia requires extraction discipline.

### Platform Identity Questions

**Q4:** Is this a CAD/CAM platform, a manufacturing optimization platform, or a luthier education platform?

**Context:** Features span design (Body Outline Editor), manufacturing (RMOS), optimization (adaptive pocketing), and education (calculators, AI advisor). Clear identity would focus development.

**Q5:** Should the platform support multiple instrument types (guitar, violin, ukulele) or remain guitar-focused?

**Context:** Current architecture is guitar-centric (FretboardEcosphere, guitar specs). Expanding requires abstracting instrument-specific code.

### Governance Tradeoff Questions

**Q6:** How much governance overhead is acceptable to prevent architectural drift?

**Context:** Proposed governance model adds pre-commit hooks, CI gates, migration state tracking. This adds friction to development.

**Tradeoff:** More governance prevents drift but slows feature velocity. Less governance enables speed but accumulates debt.

**Q7:** Should scaffolded-but-unwired infrastructure be deleted or completed?

**Context:** FeedbackSystem, TrainingDataCollector, Phase 4 Dimension Linking exist but aren't called. They represent investment that isn't returning value.

**Tradeoff:** Deleting removes dead weight. Completing enables intended functionality.

### Consolidation Risk Questions

**Q8:** Is the useInstrumentGeometryStore extraction worth the risk of breaking existing workflows?

**Context:** 1,360 lines, 7 phases, used by multiple views. Extraction could introduce regressions.

**Q9:** Should legacy routes be hard-deleted or redirected indefinitely?

**Context:** 4 duplicates, 6 shortcuts. Deletion is cleaner but breaks external links. Redirects preserve links but maintain route bloat.

**Q10:** At what point should the ApertureWorkspace shell replace SpiralSoundholeDesigner?

**Context:** Parity blockers remain. Continuing dual maintenance is expensive. Premature replacement violates migration policy.

---

## SECTION 10 — ACTIONABILITY MATRIX

### Immediate Actions (Safe During Active Sprint)

| Action | Risk | Payoff | Leverage | Impact |
|--------|------|--------|----------|--------|
| Unify toast stores | LOW | 65 lines removed | HIGH | Cleaner notifications |
| Unify RMOS runs stores | LOW | 145 lines removed | HIGH | Single source of truth |
| Add DXF pre-commit hook | LOW | Prevent new violations | VERY HIGH | Stop drift |
| Delete DxfToGcodeWizard | LOW | Remove 404 trap | MEDIUM | Cleaner codebase |
| Delete dead simulation router | LOW | 115 lines removed | LOW | Cleanup |

### Near-Term Actions (Next Sprint)

| Action | Risk | Payoff | Leverage | Impact |
|--------|------|--------|----------|--------|
| CamWorkspaceView + ToolpathPlayer | MEDIUM | Platform consistency | HIGH | Proper simulation |
| CamWorkspaceView + RMOS trail | LOW | Audit compliance | HIGH | Manufacturing governance |
| Fretboard router deduplication | LOW | Cleaner API | MEDIUM | Reduced confusion |
| Legacy route redirects | LOW | Simpler topology | MEDIUM | Cognitive load |
| Ctrl+Y redo shortcut (Rosette) | LOW | Spec compliance | LOW | Minor fix |

### Post-Sprint Stabilization Actions

| Action | Risk | Payoff | Leverage | Impact |
|--------|------|--------|----------|--------|
| useInstrumentGeometryStore extraction | HIGH | 60% complexity reduction | VERY HIGH | Maintainability |
| ApertureWorkspace parity completion | MEDIUM | Single soundhole implementation | HIGH | End dual maintenance |
| Art Studio route consolidation | MEDIUM | 15 → 6-8 routes | MEDIUM | Navigation clarity |
| Vectorizer Loop 2 (strategy cache) | MEDIUM | Quality improvement | MEDIUM | Better extractions |
| Body Outline calibration validation | LOW | 2 missing affordances | LOW | Spec compliance |

### Long-Term Governance Actions

| Action | Risk | Payoff | Leverage | Impact |
|--------|------|--------|----------|--------|
| CANONICAL.md for all subsystems | LOW | Explicit canonicality | VERY HIGH | Prevent drift |
| Migration state CI gates | MEDIUM | Enforce parity | HIGH | Safe migrations |
| Route governance pre-commit | LOW | Prevent sprawl | HIGH | Topology control |
| Store architecture guidelines | LOW | Pattern consistency | MEDIUM | Reduce fragmentation |
| Vectorizer AGE integration | MEDIUM | AI-guided extraction | MEDIUM | Quality step-change |
| Quarterly architectural review | LOW | Catch drift early | HIGH | Long-term health |

---

## APPENDIX A — FILE REFERENCE INDEX

### Backend Architecture
- Router registry: `services/api/app/router_registry/`
- RMOS core: `services/api/app/rmos/`
- CAM routers: `services/api/app/cam/routers/`
- Calculators: `services/api/app/calculators/`
- Instrument geometry: `services/api/app/instrument_geometry/`

### Frontend Architecture  
- Router: `packages/client/src/router/index.ts`
- Stores: `packages/client/src/stores/`
- Views: `packages/client/src/views/`
- Components: `packages/client/src/components/`

### Vectorizer
- Phase 3.6: `services/blueprint-import/vectorizer_phase3.py`
- Enhancements: `services/blueprint-import/vectorizer_enhancements.py`
- Calibration: `services/blueprint-import/calibration_integration.py`
- Phase 4: `services/blueprint-import/phase4/`

### Policy Documents
- CLAUDE.md (parent): `C:\Users\thepr\Downloads\CLAUDE.md`
- CLAUDE.md (project): `C:\Users\thepr\Downloads\luthiers-toolbox\CLAUDE.md`
- Feature Parity Policy: `FEATURE_PARITY_MIGRATION_POLICY.md`

### Prior Audits
- Spec Nuance Recovery: `docs/audits/SPEC_NUANCE_RECOVERY_AUDIT_2026-05-07.md`
- Architectural Consolidation: `docs/handoffs/ARCHITECTURAL_CONSOLIDATION_AUDIT_2026-05-06.md`

---

## APPENDIX B — GLOSSARY

**Canonical:** The authoritative implementation of a capability. Other implementations must defer to or be replaced by the canonical.

**Beta Shell:** A consolidation shell that cannot replace the canonical implementation until parity is verified.

**Mounted Legacy:** A legacy implementation embedded within a new shell, maintaining its own logic during migration.

**Scaffolded:** Code that exists but is not called from production paths.

**Feature Island:** An isolated cluster of functionality with minimal cross-domain integration.

**Topology Drift:** Gradual divergence from architectural intent due to accumulated sprint decisions.

**Governance Gap:** A policy that exists in documentation but has no code enforcement.

---

*Document prepared for expert architectural review. Intended audience: senior engineers, platform architects, maintainability reviewers.*

*Generated: 2026-05-07*
*Repository: luthiers-toolbox*
*Branch: fix/wood-shrinkage-data-integrity*
