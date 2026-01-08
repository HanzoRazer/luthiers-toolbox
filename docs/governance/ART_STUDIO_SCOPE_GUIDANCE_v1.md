# Art Studio Scope Guidance v1.0

**Document Type:** Architectural Guidance
**Authority:** FENCE_REGISTRY.json / ART_STUDIO_SCOPE_GOVERNANCE_v1.md
**Last Updated:** 2026-01-07
**Status:** ACTIVE

---

## 1. Purpose

This document provides actionable guidance for developers implementing or extending Art Studio features. It ensures all work remains within Art Studio's defined architectural boundaries.

**Use this document when:**
- Planning new Art Studio features
- Reviewing Art Studio pull requests
- Resolving scope ambiguity during development
- Onboarding team members to Art Studio

---

## 2. Art Studio Identity

### What Art Studio IS

Art Studio is a **high-precision ornamental authoring environment**.

| Produces | Does NOT Produce |
|----------|------------------|
| Ornamental intent | Host geometry |
| Planar decorative specifications | Structural definitions |
| Human-driven design iteration | Toolpaths or G-code |
| UI-level suggestions | Run artifacts |
| Snapshot/history metadata | Manufacturing approval |

### Canonical Output Types

```
RosetteParamSpec     → Ring-based ornament definition
InlayPatternSpec     → Decorative inlay parameters
SnapshotMetadata     → Design state + history
UISuggestion         → Correction hints (display only)
```

### The Golden Rule

> **Art Studio never decides. Art Studio only describes.**

All feasibility decisions are delegated to RMOS. Art Studio reacts to RMOS output but never generates approval, rejection, or manufacturing authority.

---

## 3. Feature Scope Decision Tree

Use this flowchart when evaluating whether a feature belongs in Art Studio:

```
START: New Feature Idea
         │
         ▼
┌─────────────────────────────────────┐
│ Can this be fully expressed as      │
│ planar ornament intent?             │
└─────────────────────────────────────┘
         │
    YES  │  NO
         │   └──────────► STOP: Not Art Studio scope
         ▼
┌─────────────────────────────────────┐
│ Does it require knowledge of        │
│ host geometry (body, neck, etc.)?   │
└─────────────────────────────────────┘
         │
    NO   │  YES
         │   └──────────► STOP: Use Placement Adapter pattern
         ▼
┌─────────────────────────────────────┐
│ Does it create RunArtifacts or      │
│ persist to RMOS directly?           │
└─────────────────────────────────────┘
         │
    NO   │  YES
         │   └──────────► STOP: Violates artifact_authority fence
         ▼
┌─────────────────────────────────────┐
│ Does it make feasibility decisions  │
│ (approve/reject/block)?             │
└─────────────────────────────────────┘
         │
    NO   │  YES
         │   └──────────► STOP: Feasibility is RMOS authority
         ▼
    ✅ APPROVED: Implement in Art Studio
```

---

## 4. Approved Feature Categories

### Category A: Core Ornament Design (Always Safe)

| Feature Type | Examples | Guidance |
|--------------|----------|----------|
| Rosette generators | Spanish mosaic, concentric rings | Pure ornament, no host knowledge |
| Pattern libraries | Storage, CRUD, presets | Stores ornament definitions only |
| Ring/tile tools | Width macros, color palettes | Parameter manipulation only |
| Mosaic builders | Tile-based patterns | Planar, decorative intent |

### Category B: Design Iteration (Always Safe)

| Feature Type | Examples | Guidance |
|--------------|----------|----------|
| History management | Undo/redo stacks | Design iteration only |
| Snapshots | Export/import/compare | Ornament state only |
| Replay systems | Sequence playback | Replays ornament deltas |
| Diff visualization | Parameter comparison | Visual + param diffs |

### Category C: RMOS Integration (Safe if Passive)

| Feature Type | Examples | Guidance |
|--------------|----------|----------|
| Feasibility banners | Risk indicators | Display RMOS output only |
| Ring warnings | Color-coded alerts | Visualization, not decision |
| Fix suggestions | Ranked corrections | Consume RMOS scores, don't generate |
| What-if calls | Speculative checks | Delegate to RMOS, display result |

**Critical Rule:** Art Studio displays feasibility. Art Studio never determines feasibility.

---

## 5. Forbidden Patterns

### Pattern F1: Host Geometry Ownership

```python
# FORBIDDEN - Art Studio defining structural geometry
class HeadstockDesigner:
    def generate_outline(self): ...
    def define_tuner_holes(self): ...

# CORRECT - Art Studio defining ornament only
class HeadstockInlaySpec:
    pattern: InlayPatternSpec  # Ornament definition
    # No knowledge of headstock shape
```

### Pattern F2: Direct Artifact Creation

```python
# FORBIDDEN - Art Studio creating run artifacts
from app.rmos.runs_v2.store import persist_run
artifact = RunArtifact(...)
persist_run(artifact)

# CORRECT - Art Studio outputs intent, RMOS creates artifacts
return RosetteParamSpec(rings=[...])
# RMOS pipeline handles artifact creation
```

### Pattern F3: Feasibility Decision-Making

```python
# FORBIDDEN - Art Studio making approval decisions
if ring.width < MIN_WIDTH:
    return {"approved": False, "blocked": True}

# CORRECT - Art Studio displaying RMOS decision
feasibility = await rmos_client.check_feasibility(spec)
return {"rmos_result": feasibility}  # Display only
```

### Pattern F4: Manufacturing Language in UI

```python
# FORBIDDEN - Implying Art Studio has approval authority
button_text = "Approve Design"
button_text = "Accept & Manufacture"
button_text = "Final Approval"

# CORRECT - Neutral iteration language
button_text = "Save Design"
button_text = "Export Spec"
button_text = "Send to RMOS"
```

---

## 6. Integration Patterns

### Correct: Layered Architecture

```
┌─────────────────────┐
│     Art Studio      │  ← Ornament authoring
│  (OrnamentSpec)     │
└─────────┬───────────┘
          │ OrnamentSpec only
          ▼
┌─────────────────────┐
│  Placement Adapter  │  ← Projection, clipping, scale
│  (Stateless)        │
└─────────┬───────────┘
          │ Positioned ornament
          ▼
┌─────────────────────┐
│  Host Geometry      │  ← Owns structure, shape, load paths
│  (Body/Neck/etc.)   │
└─────────┬───────────┘
          │ Complete geometry
          ▼
┌─────────────────────┐
│       RMOS          │  ← Feasibility, artifacts, authority
└─────────────────────┘
```

### Incorrect: Merged Concerns

```
# WRONG - Art Studio knowing about host geometry
┌─────────────────────────────────┐
│  Art Studio + Host Geometry     │  ← Violation!
│  (OrnamentSpec + BodyOutline)   │
└─────────────────────────────────┘
```

---

## 7. Anti-Creep Checklist

Before merging any Art Studio PR, verify:

- [ ] **No host geometry imports** - Art Studio doesn't import body/neck/headstock modules
- [ ] **No RunArtifact creation** - Art Studio doesn't call `persist_run()`
- [ ] **No feasibility decisions** - Art Studio displays but doesn't determine
- [ ] **No approval language** - UI avoids "approve", "accept", "final"
- [ ] **Planar only** - All outputs are 2D ornamental specifications
- [ ] **RMOS delegation** - Feasibility checks delegate to RMOS endpoints
- [ ] **Stateless adapters** - Any placement logic is pure transformation

---

## 8. Drift Risk Vectors

### Watch These Areas

| Risk Vector | Symptom | Mitigation |
|-------------|---------|------------|
| Placement adapters getting "smart" | Adapter stores state or makes decisions | Keep adapters as pure functions |
| UI implying approval authority | Buttons labeled "Approve" or "Accept" | Use neutral language: "Save", "Export" |
| Generators encoding host assumptions | Generator knows about body shape | Keep generators planar and host-agnostic |
| Feasibility logic leaking in | `if width < MIN: block()` | All feasibility via RMOS API |

### CI Enforcement

The `check_art_studio_scope.py` script enforces these boundaries:

```bash
# Run locally before commit
python services/api/app/ci/check_art_studio_scope.py

# Runs automatically in CI via:
make check-boundaries
```

---

## 9. Quick Reference Card

### Art Studio CAN:
- Generate ornament specifications
- Store/load pattern presets
- Display RMOS feasibility results
- Manage design history/snapshots
- Provide UI suggestions and corrections
- Export ornament intent to downstream systems

### Art Studio CANNOT:
- Define host geometry (body, neck, headstock)
- Create RunArtifacts directly
- Make feasibility decisions
- Approve or reject manufacturing
- Generate toolpaths or G-code
- Know what surface ornament will be placed on

### The Litmus Test

> "Can this feature be fully expressed as planar ornament intent without knowledge of the host surface?"

If YES → Art Studio scope
If NO → Not Art Studio scope

---

## 10. Related Documents

| Document | Purpose |
|----------|---------|
| `ART_STUDIO_SCOPE_GOVERNANCE_v1.md` | Formal scope contract |
| `FENCE_REGISTRY.json` | Machine-readable boundary rules |
| `FENCE_ARCHITECTURE.md` | Fence system documentation |
| `FENCE_SYSTEM_SUMMARY.md` | Implementation status |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-07 | Initial guidance document (converted from drift audit) |
