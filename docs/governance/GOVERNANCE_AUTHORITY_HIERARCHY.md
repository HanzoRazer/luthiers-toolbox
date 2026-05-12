# Governance Authority Hierarchy

**Date:** 2026-05-07  
**Status:** AUDIT DELIVERABLE  
**Purpose:** Establish clear authority boundaries between governance systems

---

## The Problem

Six governance systems currently operate without explicit authority hierarchy:

1. RMOS 2.0
2. CAM Governed Export Architecture
3. MRP Governance Enforcement
4. CAM Capability Registry
5. Architecture Invariants
6. Feature Parity Migration Policy

Each claims authority over overlapping concerns. Without hierarchy, enforcement ambiguity arises.

---

## Proposed Authority Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIER 1: STRUCTURAL INVARIANTS                        │
│                                                                              │
│  Architecture Invariants (6-layer placement)                                │
│  Feature Parity Migration Policy                                            │
│                                                                              │
│  Scope: Repository-wide code organization and migration discipline          │
│  Authority: Where code goes, when replacement is allowed                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIER 2: DOMAIN GOVERNANCE                            │
│                                                                              │
│  MRP Governance (protected systems, pre-commit enforcement)                 │
│  CAM Governed Export Architecture (export lifecycle, boundaries)            │
│  RMOS 2.0 (manufacturing feasibility, run artifacts)                        │
│                                                                              │
│  Scope: Domain-specific governance within repository structure              │
│  Authority: What operations are allowed within each domain                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIER 3: OPERATIONAL POLICIES                         │
│                                                                              │
│  CAM Capability Registry (operation maturity, lifecycle stages)             │
│  Sprint Namespace Standard (naming conventions)                             │
│  Other domain-specific contracts (AI Sandbox, Security Trust, etc.)         │
│                                                                              │
│  Scope: Runtime behavior within governed domains                            │
│  Authority: How operations execute within tier 2 boundaries                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tier Definitions

### Tier 1: Structural Invariants

**Purpose:** Foundational placement and migration rules that all other governance must respect.

**Documents:**
- `docs/governance/ARCHITECTURE_INVARIANTS.md`
- `FEATURE_PARITY_MIGRATION_POLICY.md`

**Authority Scope:**
- Code placement (6-layer model)
- Migration discipline (parity verification)
- Router governance tests
- Cross-domain boundaries

**Conflict Resolution:** Tier 1 wins. No domain governance may violate structural invariants.

---

### Tier 2: Domain Governance

**Purpose:** Domain-specific governance that operates within Tier 1 boundaries.

**MRP Domain:**
- Blueprint Reader protection
- IBG core protection
- DXF compat layer protection
- Governance manifest enforcement

**CAM Export Domain:**
- Export lifecycle stages
- Preview/Export/Machine Output boundaries
- Gate propagation rules
- Postprocessor interface

**RMOS Domain:**
- Manufacturing feasibility
- Risk evaluation
- Run artifacts
- Audit trails

**Conflict Resolution:** Each domain owns its scope. Cross-domain conflicts escalate to Tier 1 principles.

---

### Tier 3: Operational Policies

**Purpose:** Runtime behavior policies within Tier 2 domain boundaries.

**Examples:**
- CAM operation maturity levels
- Exportability classifications
- Sprint naming conventions
- AI sandbox boundaries
- Security trust boundaries

**Conflict Resolution:** Defer to owning Tier 2 domain.

---

## Domain Ownership Map

| Domain | Owner System | Tier |
|--------|--------------|------|
| Code placement | Architecture Invariants | 1 |
| Migration discipline | Feature Parity Migration | 1 |
| Blueprint Reader | MRP | 2 |
| IBG math | MRP | 2 |
| DXF output | CAM Export + MRP (shared) | 2 |
| Export lifecycle | CAM Export | 2 |
| Manufacturing feasibility | RMOS | 2 |
| Run artifacts | RMOS | 2 |
| Operation maturity | CAM Capability Registry | 3 |
| Sprint naming | Sprint Namespace Standard | 3 |
| AI boundaries | AI Sandbox Contract | 3 |

---

## Shared Domain: DXF Output

**Conflict:** Both MRP and CAM Export govern DXF output.

**Resolution:**

1. **MRP governs DXF_COMPAT_LAYER** — Protected paths, implementation stability
2. **CAM Export governs DXF lifecycle** — When DXF export is allowed, what validation applies

```
MRP: "You cannot change dxf_compat.py without approval"
CAM: "You cannot export DXF until preview gate is GREEN/YELLOW"
```

These are complementary, not conflicting:
- MRP protects implementation
- CAM governs usage

---

## Shared Domain: RMOS Persistence

**Conflict:** CAM Export Layer 5 is "RMOS Persistence" but RMOS 2.0 defines RMOS scope.

**Resolution:**

1. **RMOS 2.0 owns RMOS identity** — API contracts, subsystems, naming
2. **CAM Export integrates RMOS** — Uses RMOS as persistence layer

```
RMOS: "Defines what RMOS is and does"
CAM: "Uses RMOS for layer 5 persistence"
```

CAM Export should reference RMOS, not redefine it.

---

## Authority Resolution Rules

### Rule 1: Tier Precedence

Higher tier wins in conflicts:
- Tier 1 > Tier 2 > Tier 3

### Rule 2: Domain Isolation

Within same tier, domains are isolated:
- MRP does not govern CAM internals
- CAM Export does not govern Blueprint Reader internals
- RMOS does not govern IBG math

### Rule 3: Integration Points

Cross-domain integration happens via:
- services/ layer (Architecture Invariants)
- Explicit interface contracts (documented in governance docs)

### Rule 4: Escalation Path

When governance conflict arises:
1. Check Tier 1 principles
2. Check domain ownership
3. If ambiguous, document and request human decision

---

## Enforcement Mechanism Ownership

| Mechanism | Owner |
|-----------|-------|
| `tests/test_route_governance.py` | Architecture Invariants |
| `scripts/check_protected_paths.py` | MRP |
| `scripts/check_sprint_namespace.py` | Sprint Namespace |
| `governance_manifest.json` | MRP |
| `cam_operation_registry.py` | CAM Capability |
| `cam_lifecycle_policy_engine.py` | CAM Capability |
| `rmos/feasibility/rule_registry.py` | RMOS |

---

## Recommended Consolidation

### Immediate (no code change):

1. **Document Tier 1 supremacy** in all Tier 2/3 governance docs
2. **Add cross-references** between related governance docs
3. **Clarify RMOS scope** — RMOS 2.0 Spec should explicitly state relationship to CAM Export Layer 5

### Near-term (low risk):

1. **Consolidate gate terminology** — All systems use GREEN/YELLOW/RED
2. **Consolidate maturity terminology** — Canonical/governed/candidate/experimental
3. **Add authority hierarchy reference** to CLAUDE.md

### Future (requires design):

1. **Unified governance manifest** — Single machine-readable registry with all protected systems
2. **Unified maturity model** — One lifecycle for all components
3. **Unified enforcement** — Single pre-commit hook checking all governance

---

*Governance Authority Hierarchy — 2026-05-07*
