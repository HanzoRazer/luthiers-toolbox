# FEATURE_PARITY_MIGRATION_POLICY.md

## Purpose

This document establishes the repository-wide policy for migrating legacy tools, generators, analyzers, and interactive widgets into consolidated workspace architectures.

The goal is:

$$
\boxed{
\text{consolidation without regression}
}
$$

This policy exists because several completed/canonical implementations were unintentionally displaced by newer incomplete shells or refactors before feature parity was achieved.

---

# Core Principle

$$
\boxed{
\text{A new architecture must never replace a working canonical implementation before parity is verified.}
}
$$

Workspace consolidation is allowed.

Feature regression is not.

---

# Definitions

## Canonical Implementation

A tool, widget, calculator, or workflow that:

* is functional
* is user-usable
* produces validated outputs
* has complete interaction flow
* is relied upon operationally
* may exist in:

  * Vue
  * HTML prototype
  * archived utility
  * standalone generator
  * legacy route

Canonical status is based on functionality, not code age.

---

## Consolidation Shell

A newer architecture intended to unify multiple tools into:

* shared workspaces
* shared stores
* shared rendering systems
* shared export systems
* shared routing
* shared diagnostic workflows

Examples:

```text
ApertureWorkspace
NeckSetupWorkspace
ArtStudioWorkspace
```

A consolidation shell is NOT automatically canonical.

---

## Migration

Migration means:

* replacing
* redirecting
* hiding
* deprecating
* embedding
* superseding
* or disabling

an existing implementation.

---

# Mandatory Rule

## No Replacement Before Parity

$$
\boxed{
\text{No existing canonical implementation may be removed or superseded until parity is verified.}
}
$$

This includes:

* route replacement
* menu replacement
* tool registry replacement
* workspace replacement
* UI hiding
* archive relocation
* silent deprecation

---

# Feature Parity Requirements

Before a replacement is allowed, the new implementation MUST demonstrate parity in all applicable areas.

---

## 1. Functional Parity

The new implementation must support:

* equivalent inputs
* equivalent outputs
* equivalent interaction flow
* equivalent calculations
* equivalent geometry behavior

---

## 2. Export Parity

The replacement must preserve existing exports where applicable:

* DXF
* SVG
* JSON
* G-code
* CSV
* presets
* screenshots
* measurement packs

---

## 3. Visualization Parity

The replacement must preserve:

* live preview behavior
* rendering updates
* overlays
* geometry visualization
* interactive controls

---

## 4. Workflow Parity

The replacement must preserve:

* user workflow order
* interaction expectations
* editing flow
* parameter manipulation behavior

---

## 5. Preset Parity

The replacement must preserve:

* existing presets
* default values
* saved parameter behavior
* existing serialized configurations

---

## 6. Mathematical Parity

The replacement must preserve:

* validated formulas
* numerical behavior
* derived metrics
* inverse calculations
* tolerances

Any intentional math changes MUST be documented.

---

## 7. API Parity

The replacement must preserve:

* request schemas
* response schemas
* endpoint behavior

unless a documented breaking change process exists.

---

## 8. Runtime Verification

Before replacement:

* browser verification must pass
* runtime console errors must be resolved
* rendering regressions must be checked
* interaction regressions must be checked

---

## 9. Regression Testing

The migration must preserve:

* existing tests
* expected outputs
* validated geometry
* export correctness

New parity tests should be added where practical.

---

# Required Migration States

Every migration MUST explicitly declare its state.

---

## State 1 — Canonical

```text
Canonical Production Tool
```

The currently trusted implementation.

---

## State 2 — Mounted Legacy Component

```text
Mounted Legacy Component
```

Used when:

* a legacy component is embedded into a new workspace
* but still owns its own logic/state

Example:

```text
SpiralSoundholeDesigner.vue mounted inside ApertureWorkspace.vue
```

This is a transitional state.

---

## State 3 — Beta Consolidation Shell

```text
Beta Consolidation Shell
```

Used when:

* the workspace architecture exists
* but parity is incomplete

Example:

```text
ApertureWorkspace
```

during migration.

---

## State 4 — Parity Verified

```text
Parity Verified
```

Used when the replacement has passed all parity checks.

Only then may canonical replacement occur.

---

# Required Parity Checklist

Every migration PR should include a parity checklist.

Example:

```markdown
## Parity Checklist

- [ ] Inputs equivalent
- [ ] Outputs equivalent
- [ ] DXF export preserved
- [ ] SVG export preserved
- [ ] Presets preserved
- [ ] Live preview preserved
- [ ] Browser verification complete
- [ ] Existing tests passing
- [ ] Manual regression check complete
```

---

# Repository Guidance

## Preserve Legacy Until Proven

Legacy code is not automatically obsolete.

Older implementations may contain:

* validated geometry
* working interaction patterns
* production math
* complete workflows
* hidden domain knowledge

---

## "Archived" Does Not Mean Disposable

Archived implementations MUST be audited before removal.

Several archived files in this repository were discovered to contain:

* production-quality acoustic solvers
* inverse Helmholtz logic
* two-cavity Selmer/Maccaferri calculations
* advanced geometry systems
* interactive workflows absent from newer tools

---

# Current Repository Application

This policy currently applies to:

* SpiralSoundholeDesigner
* ApertureWorkspace
* NeckSetupWorkspace
* soundhole_designer.html
* rosette-designer-v5
* headstock generators
* pattern generators
* inverse acoustic solvers

---

# Aperture Workspace Specific Guidance

Current status:

```text
SpiralSoundholeDesigner.vue = canonical implementation
ApertureWorkspace.vue = beta consolidation shell
```

The workspace shell may mount the legacy component.

It may NOT replace or remove the legacy implementation until parity is verified.

---

## Current Spiral Soundhole State

**Updated:** 2026-05-07 (Dev Order 9)

**Canonical production route:** `/calculators/acoustics/spiral-soundhole`  
**Beta consolidation route:** `/art-studio/aperture`  
**Canonical implementation:** `SpiralSoundholeDesigner.vue`  
**Migration state:** Mounted canonical component inside beta shell  
**Replacement allowed:** No, not until feature parity checklist passes

| Component | Status | Migration State |
|-----------|--------|-----------------|
| `SpiralSoundholeDesigner.vue` | Canonical | State 1 — Canonical Production Tool |
| `ApertureWorkspace.vue` | Beta shell | State 3 — Beta Consolidation Shell |

**Registry entries:**
- `spiral-soundhole` — stable, canonical: true
- `aperture-workspace` — beta, canonical: false, mounts canonical component

**Replacement allowed:** No, not until parity checklist passes.

**Audit document:** `docs/architecture/SPIRAL_COMPONENT_CONTAINMENT_AUDIT.md`

**Known issues blocking parity:**
- ~~Component calls wrong API endpoints~~ RESOLVED (Dev Order 8, 2026-05-07)
- No consumption of backend presets (`/api/instrument/soundhole/spiral/default`)
- No display of `aperture_geometry` response fields (equivalent_diameter_mm, etc.)

---

# Approved Migration Strategy

Preferred migration order:

$$
\boxed{
\text{mount} \rightarrow \text{verify} \rightarrow \text{audit} \rightarrow \text{extract} \rightarrow \text{normalize} \rightarrow \text{replace}
}
$$

NOT:

```text
rewrite → replace → discover regressions later
```

---

# Anti-Patterns

The following are prohibited:

---

## 1. Shell-First Replacement

Replacing a complete tool with an incomplete workspace shell.

---

## 2. Implicit Deprecation

Removing routes or menu visibility before parity verification.

---

## 3. Archive Without Audit

Moving working tools into archive status without reviewing functionality.

---

## 4. "Newer Means Better"

Assuming newer code is more complete than older code.

---

## 5. Premature Shared Abstractions

Forcing tools into shared systems before understanding their ownership boundaries.

---

# Architectural Principle

$$
\boxed{
\text{Working behavior is more important than architectural purity.}
}
$$

Architecture exists to preserve and extend capability.

Not erase it.

---

# Final Rule

If a migration creates uncertainty:

$$
\boxed{
\text{the canonical implementation stays active until proven otherwise}
}
$$

No exceptions.
