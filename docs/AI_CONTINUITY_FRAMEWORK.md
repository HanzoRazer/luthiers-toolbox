# AI Continuity Framework

**Purpose:** Stabilize guidance across AI sessions working on this repository.  
**Audience:** Future Claude instances, AI coding assistants, and the humans reviewing their output.  
**Last verified:** 2026-05-07  
**Supporting evidence:** `docs/audits/ARCHITECTURAL_GOVERNANCE_HANDOFF_2026-05-07.md`

> **CONFLATION CORRECTION (2026-05-30).** This framework treats the three-loop architecture / AGE
> as "approved design … largely unbuilt" and frames the fork as "build or remove from CLAUDE.md."
> Per ground truth from Ross (2026-05-30), the answer is **remove-from-runtime / keep-in-sandbox**:
> the work was **experimental, never approved, never implemented** here, and is now **sandbox-owned**
> (`vectorizer-sandbox`). Flip any "approved design" references to "experimental, sandboxed." See
> `docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md`.
>
> **Live-code carve-out:** "never implemented" means the *named, unified* architecture only.
> `GeometryCoachV2` (photo-vectorizer) is real, **API-reachable** runtime code — its "Loop 1" name
> is retrospective labeling, NOT the approved architecture. Do NOT delete or sandbox it; deletion
> degrades a live endpoint path. See handoff §2 + §9b.

---

## Why This Document Exists

AI sessions working on this repository face a recurring problem: each session starts fresh, encounters a large codebase with historical context, and must rapidly form judgments about what to modify, preserve, or consolidate.

Without stable anchors, these sessions:
- Propose rewrites of systems that are intentionally designed as-is
- Consolidate code that exists in parallel for valid migration reasons
- Recommend deleting "dead code" that is scaffolded infrastructure awaiting integration
- Drift toward speculative architectural advice disconnected from operational reality

This document provides the anchors needed to prevent that drift.

**This is not enterprise process. This is operational continuity.**

---

## The Four Pillars

### Pillar 1: Executable Canonicality

A system is canonical if it is the **authoritative implementation** of a capability. Other implementations must defer to it or be explicitly marked as migration candidates.

**Canonicality is not determined by:**
- Recency (newer is not automatically better)
- Lines of code (smaller is not automatically cleaner)
- Naming conventions (Shell/Workspace suffix doesn't confer authority)
- Documentation claims alone

**Canonicality IS determined by:**
- Production usage (users interact with this implementation)
- Platform integration (other systems depend on this implementation)
- Behavioral completeness (this implementation has the required affordances)
- Explicit declaration (this document or CANONICAL.md names it)

**Rule:** Before recommending replacement of any system, verify its canonicality status. If canonical, replacement requires parity verification.

### Pillar 2: AI Continuity Stabilization

AI sessions should produce **convergent guidance** — advice that moves the repository toward a stable state rather than oscillating between competing visions.

**Convergent guidance:**
- Reinforces existing architectural decisions
- Completes in-progress migrations rather than proposing new ones
- Addresses documented gaps before identifying new ones
- Respects the historical context that shaped current design

**Divergent guidance (avoid):**
- Proposes rewrites without understanding why current design exists
- Identifies "problems" that are intentional tradeoffs
- Recommends consolidation during active migration windows
- Prioritizes theoretical cleanliness over operational stability

**Rule:** When uncertain whether guidance is convergent or divergent, default to observation and documentation rather than modification recommendations.

### Pillar 3: Topology Freeze

The repository's structural topology (routes, stores, major component boundaries) should be treated as **frozen** unless explicit migration is authorized.

**Frozen means:**
- New routes follow existing patterns (nested under domain prefix)
- New stores follow existing patterns (Composition API, domain-scoped)
- New components integrate with existing shells rather than creating parallel structures
- Consolidation happens through completion, not addition

**Not frozen:**
- Bug fixes within existing structures
- Feature additions within existing component boundaries
- Performance improvements that don't change interfaces
- Documentation and test coverage

**Rule:** Proposals that change structural topology require explicit justification referencing this document's canonical inventory.

### Pillar 4: Manufacturing Workflow Gravity

This is a **manufacturing platform**. All architectural decisions should be evaluated against their impact on the core workflow:

```
Design → CAM → Simulation → Verification → Export → Execution
```

**Manufacturing gravity means:**
- Systems closer to physical output (G-code, DXF, RMOS runs) are more critical
- UI polish matters less than manufacturing correctness
- Risk gating and audit trails are non-negotiable
- Feasibility checking exists for safety, not bureaucracy

**Rule:** When prioritizing work, manufacturing workflow proximity determines importance. ToolpathPlayer issues outrank rosette color palette issues.

---

## Confidence Anchors

For AI guidance to reach ~95% accuracy, these five anchors must be verified:

### Anchor 1: Verified Canonical Inventories

Every subsystem has an explicit list of canonical implementations. These lists are verified against production usage, not assumed from code structure.

**Current inventory is in Section: Canonical System Inventory (below).**

**Verification criteria:**
- [ ] Listed as canonical in this document
- [ ] Actually used in production paths
- [ ] Other implementations explicitly marked as alternatives/migrations

### Anchor 2: Executable Verification

Canonicality claims can be verified by running the system, not just reading code.

**Verification methods:**
- Route exists and renders expected component
- API endpoint returns expected schema
- Tests pass and cover stated behavior
- Manual verification confirms behavioral claims

**Rule:** If a canonicality claim cannot be verified by execution, mark it as UNVERIFIED.

### Anchor 3: Stable Platform Identity

The platform's identity is explicit, not inferred:

**This is:** A CAD/CAM manufacturing optimization platform for guitar builders.

**Primary workflow:** DXF → G-code (80% of usage)  
**Secondary workflow:** Parametric design → G-code (15%)  
**Supporting features:** Calculators, design tools, business planning (5%)

**This is NOT:**
- A general-purpose CAD platform
- A music education tool
- A guitar sales marketplace
- A social platform for luthiers

**Rule:** Feature proposals should be evaluated against platform identity. Features outside identity require explicit justification.

### Anchor 4: Human-Validated Ground Truth

Certain architectural decisions have been validated by the human maintainer (Ross) and should not be second-guessed:

**Validated decisions:**
- DXF dual-format policy (R12 free, R2000 paid) — confirmed 2026-04-28
- RMOS four-stage pipeline design — production since 2025
- Feature parity migration policy — explicitly authored
- ToolpathPlayer behavioral spec — verified complete
- FretboardEcosphere as canonical schema — Phase 1 complete

**Rule:** AI sessions should not propose alternatives to human-validated decisions unless asked to evaluate them.

### Anchor 5: Explicit Experimentation Policy

Code can exist in one of four states:

| State | Definition | AI Guidance |
|-------|------------|-------------|
| **Canonical** | Authoritative production implementation | Preserve, enhance, do not replace |
| **Migration** | Being replaced by canonical; both exist | Complete migration, do not extend legacy |
| **Experimental** | Scaffolded, not yet production | Wire to production OR delete within 60 days |
| **Deprecated** | Marked for removal | Do not extend, remove after deprecation period |

**Rule:** Before modifying any system, identify its state. Guidance differs by state.

---

## Canonical System Inventory

### Tier 1: Manufacturing Core (Do Not Modify Without Explicit Request)

| System | Location | State | Notes |
|--------|----------|-------|-------|
| **ToolpathPlayer** | `components/cam/toolpath-player/` | Canonical | 100% spec compliance, production-ready |
| **RMOS Pipeline** | `services/api/app/rmos/` | Canonical | Four-stage artifact model, immutable runs |
| **DxfToGcodeView** | `views/cam/DxfToGcodeView.vue` | Canonical | Primary user workflow |
| **useToolpathPlayerStore** | `stores/useToolpathPlayerStore.ts` | Canonical | Simulation state, P1-P5 enhancements |
| **dxf_writer.py** | `services/api/app/cam/dxf_writer.py` | Canonical | Central DXF generation (use dxf_compat) |
| **gcode_parser.py** | `services/api/app/cam/gcode/` | Canonical | G-code simulation, 28 tests passing |

### Tier 2: Design Systems (Stable, Complete)

| System | Location | State | Notes |
|--------|----------|-------|-------|
| **Body Outline Editor** | `hostinger/body-outline-editor.html` | Canonical | 94% behavioral compliance, v3.5.0 |
| **FretboardEcosphere** | `instrument_geometry/neck/fretboard_ecosphere.py` | Canonical | Phase 1 complete, 7 temperaments |
| **rosetteStore** | `stores/rosetteStore.ts` | Canonical | Design-first editor, undo/redo, MFG checks |
| **InlayWorkspaceShell** | `views/art-studio/InlayWorkspaceShell.vue` | Canonical | 5-stage workspace, composable isolation |
| **GuidedWorkflow** | `components/guided/GuidedWorkflow.vue` | Canonical | Step lifecycle, validation gates |

### Tier 3: Migration In Progress (Both Exist, Complete Migration)

| Legacy | Replacement | Migration State | Action |
|--------|-------------|-----------------|--------|
| **SpiralSoundholeDesigner** | ApertureWorkspace | State 3 (Beta Shell) | Complete parity verification |
| **fret_slots_cam.py** | fret_slots_from_ecosphere.py | Dual-path | Route new CAM through ecosphere |
| **rmosRunsStore** | useRmosRunsStore | Duplicate | Delete rmosRunsStore |
| **useUiToastStore** | useToastStore | Duplicate | Delete useUiToastStore |
| **fretwork_router.py** | nut_fret_router.py | Duplicate | Delete fretwork_router |

### Tier 4: Experimental/Scaffolded (Wire or Delete)

| System | Location | Status | Deadline |
|--------|----------|--------|----------|
| **FeedbackSystem** | vectorizer_phase3.py:1181 | Scaffolded, never called | Wire submit_correction() or delete |
| **TrainingDataCollector** | vectorizer_phase3.py:1273 | Never instantiated | Instantiate or delete |
| **Phase 4 Dimension Linking** | services/blueprint-import/phase4/ | Complete, standalone | Integrate or document as optional |
| **calibration_integration.py** | services/blueprint-import/ | Complete, not called | Wire to vectorizer pipeline |
| **AGE Integration** | Not implemented | Approved design, 0 lines | Build or remove from CLAUDE.md |

### Tier 5: Deprecated (Remove After Period)

| System | Deprecation Date | Removal Date | Reason |
|--------|------------------|--------------|--------|
| **DxfToGcodeWizard** | 2026-05-07 | 2026-06-07 | Calls 404 endpoints |
| **simulation_consolidated_router.py** | 2026-05-07 | 2026-05-21 | Dead code, commented import |
| **Legacy route shortcuts** | 2026-05-07 | 2026-07-07 | Redirects to canonical routes |

---

## Route Topology Rules

### Canonical Route Patterns

All new routes must follow nested domain patterns:

```
/lab/*           — Laboratory/experimental tools
/cam/*           — CAM operations
/art-studio/*    — Art/design tools
/rmos/*          — Manufacturing management
/tools/*         — Utility tools
/settings/*      — Configuration
/business/*      — Business tools
```

### Forbidden Patterns

- Root-level routes (except `/`, `/login`, `/signup`, `/upgrade`)
- Duplicate routes to same component
- Routes without navigation visibility (unless intentionally hidden)

### Legacy Routes (Redirect, Do Not Extend)

| Legacy Route | Canonical Route | Status |
|--------------|-----------------|--------|
| `/bridge` | `/lab/bridge` | Redirect |
| `/saw` | `/lab/saw/*` | Redirect |
| `/pipeline` | `/lab/pipeline` | Redirect |
| `/cam-settings` | `/settings/cam` | Redirect |

---

## Store Architecture Rules

### Canonical Store Pattern

All new stores must use Composition API (Pinia setup syntax):

```typescript
export const useExampleStore = defineStore('example', () => {
  // State as refs
  const items = ref<Item[]>([])
  const loading = ref(false)
  
  // Actions as functions
  async function fetchItems() { ... }
  
  // Computed as computed()
  const itemCount = computed(() => items.value.length)
  
  return { items, loading, fetchItems, itemCount }
})
```

### Anti-Patterns (Do Not Create)

- Options API stores (legacy pattern)
- Stores mixing multiple unrelated domains
- Stores exceeding 500 lines without extraction discussion
- Duplicate stores for same domain

### Stores Requiring Extraction (Future Work)

| Store | Lines | Issue | Target |
|-------|-------|-------|--------|
| useInstrumentGeometryStore | 1,360 | 7 workflow phases mixed | Extract to 3 domain stores |

---

## Backend Architecture Rules

### Router Registration

All routers must be registered in `app/router_registry/manifest.py`:

```python
RouterEntry(
    module="app.routers.example_router",
    router_attr="router",
    prefix="/api/example",
    tags=["Example"],
    category="example_domain",
    required=False
)
```

### Calculator Purity

All calculators in `app/calculators/` must be pure functions:
- Input → Output, no side effects
- No HTTP/routing logic
- No database access
- Reusable across routers

### DXF Generation

All DXF generation must use `dxf_compat` layer:

```python
# CORRECT
from app.cam.dxf_compat import create_dxf, add_polyline
doc = create_dxf(version='R2000')

# FORBIDDEN
import ezdxf
doc = ezdxf.new("R2010")  # Direct ezdxf.new() violates policy
```

---

## Vectorizer Guidance

### Current Production State

Phase 3.6 vectorizer is canonical. Scale validation gate is implemented and active.

### Approved But Unimplemented

The three-loop architecture is approved design but largely unbuilt:

| Loop | Status | Guidance |
|------|--------|----------|
| Loop 1 (Scale Validation) | Implemented | Preserve, enhance |
| Loop 1 (Retry Logic) | Not implemented | Build if working on vectorizer |
| Loop 2 (Strategy Cache) | Not implemented | High value, ~200 lines |
| Loop 3 (User Correction) | Scaffolded | Wire FeedbackSystem or delete |
| AGE Integration | Not implemented | Requires Claude API access |

### Rule for Vectorizer Work

Do not add tactical fixes (epsilon tweaks, cache headers) without also advancing the approved architecture. Point fixes address symptoms; architecture addresses trajectory.

---

## RMOS Integration Requirements

### All Manufacturing Operations Must Create RMOS Runs

Any operation that:
- Generates G-code
- Produces DXF for manufacturing
- Makes irreversible manufacturing decisions

Must create an RMOS run with:
- Spec artifact (input)
- Plan artifact (processing)
- Decision artifact (approval)
- Execution artifact (output)

### Current Gaps

| System | RMOS Integration | Status |
|--------|------------------|--------|
| DxfToGcodeView | Full | Canonical |
| CamWorkspaceView | None | **GAP — Must add** |
| Fret slot generation | Partial | Needs audit |

---

## What AI Sessions Should Do

### On Session Start

1. Read this document
2. Identify the task's relationship to canonical systems
3. Verify any systems you'll modify against the inventory
4. Check if work involves migration-state systems (both exist, complete migration)

### When Recommending Changes

1. State which pillar the change supports
2. Identify the canonicality state of affected systems
3. Explain whether this is convergent or divergent guidance
4. For topology changes, provide explicit justification

### When Uncertain

1. Document observations rather than recommending changes
2. Ask clarifying questions about intent
3. Reference this document and the governance audit
4. Default to preservation over modification

### When Asked to "Clean Up" or "Consolidate"

1. Verify the target is not canonical
2. Check for migration-in-progress state (don't consolidate during migration)
3. Confirm scaffolded code is truly dead, not awaiting integration
4. Propose deprecation timeline, not immediate deletion

---

## What AI Sessions Should NOT Do

### Do Not Propose

- Rewrites of canonical systems
- Deletion of scaffolded infrastructure without deadline context
- Consolidation of migration-state systems (complete migration instead)
- New parallel implementations when canonical exists
- Route/store patterns that violate topology rules

### Do Not Assume

- Newer code is better code
- Shell/Workspace suffix indicates canonical
- Unused code is dead code (may be scaffolded)
- Documentation claims without verification
- All gaps are problems (some are intentional)

### Do Not Optimize For

- Theoretical cleanliness over operational stability
- Generic patterns over domain-specific needs
- Micro-performance over maintainability
- Code reduction without behavioral verification

---

## Confidence Verification Checklist

Before finalizing major recommendations, verify:

- [ ] Canonical inventory consulted (Anchor 1)
- [ ] Claims verified by execution or tests (Anchor 2)
- [ ] Recommendation aligns with platform identity (Anchor 3)
- [ ] Not contradicting human-validated decisions (Anchor 4)
- [ ] System state (canonical/migration/experimental/deprecated) identified (Anchor 5)

If any anchor cannot be verified, state the uncertainty explicitly.

---

## Document Maintenance

### This Document Should Be Updated When

- Canonical inventory changes (system promoted or deprecated)
- Migration completes (remove from migration section)
- Experimental code wired or deleted (update Tier 4)
- Human validates new architectural decisions (update Anchor 4)

### This Document Should NOT Be Updated For

- Bug fixes within existing systems
- Feature additions within canonical boundaries
- Test coverage improvements
- Documentation improvements elsewhere

### Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-05-07 | Initial framework based on governance audit | Claude (with Ross direction) |

---

## References

- **Governance Audit:** `docs/audits/ARCHITECTURAL_GOVERNANCE_HANDOFF_2026-05-07.md`
- **Spec Nuance Audit:** `docs/audits/SPEC_NUANCE_RECOVERY_AUDIT_2026-05-07.md`
- **Feature Parity Policy:** `FEATURE_PARITY_MIGRATION_POLICY.md`
- **Project Instructions:** `CLAUDE.md`
