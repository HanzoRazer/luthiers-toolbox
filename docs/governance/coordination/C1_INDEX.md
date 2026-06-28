# C1 Coordination Phase Index

**Phase:** C1 — Collection  
**Date:** 2026-05-18  
**Status:** FROZEN — C2 Arbitration Ready

---

## Purpose

This index tracks all C1 inventory documents across sprint workstreams. C1 collects semantic evidence without making decisions.

---

## Core Principle

```
C1 makes semantic collisions visible.
C1 does not make semantic decisions.
```

---

## Inventory Documents

### Completed

| Document | Workstream | Status |
|----------|------------|--------|
| `C1_RUNTIME_CAM_INVENTORY.md` | Runtime/CAM | Complete |
| `C1_GEOMETRY_TOPOLOGY_INVENTORY.md` | Geometry/Morphology/Topology | Complete |
| `C1_ACOUSTICS_INVENTORY.md` | Acoustics/Observational | Complete |
| `C1_GOVERNANCE_INVENTORY.md` | Governance Integration | Complete |
| `SEMANTIC_COLLISION_LOG.md` | Cross-sprint | Complete |
| `RUNTIME_ASSUMPTION_INVENTORY.md` | Cross-sprint | Complete |

### All Inventories Complete

All four C1 inventory documents have been completed. Proceeding to strategic synthesis.

---

## Collection Statistics

### Semantic Collisions

| Category | Count |
|----------|-------|
| Same term, different meaning | 5 |
| Same concept, different term | 4 |
| Duplicate definitions | 7 |
| Authority overlap | 1 |
| **Total** | 17 |

### Runtime Assumptions

| Category | Count |
|----------|-------|
| Authority dependency | 5 |
| Contract assumption | 5 |
| Ownership ambiguity | 1 |
| Implicit flow | 1 |
| Enforcement gap | 2 |
| **Total** | 15 |
| **Critical** | 8 |

---

## Domains Inventoried

### CAM Runtime (Complete)

- Result status vocabulary (4 terms)
- Dispatch status vocabulary (4 terms)
- Validation gate vocabulary (3 terms)
- Translator maturity vocabulary (5 terms)
- Execution state vocabulary (5 terms)
- Geometry resolution status (4 terms)
- Planning/preview/export stages (9 terms)
- Provenance chain formats (9 patterns)
- ID prefix conventions (3 patterns)

### Governance (Complete)

- Lifecycle registry (17 canonical terms) — operational
- Semantic registry (10 canonical concepts) — operational
- Authority chain registry (6 declared chains) — operational
- Domain ownership (8 domains) — operational
- Alias registry (14 active, 2 transitional) — operational
- CI enforcement (4 checks, severity-based) — operational

**Critical Finding:**
- Governance infrastructure IS NOT meta-governance — it is operational
- IBG is NOT FEDERATED (72 terms in sandbox state)
- IBG federation is the primary C2 reconciliation target

### Geometry/Topology (Complete)

- CadSemantics vocabulary (7 enums, 24 terms) — defining semantic source
- TopologyRuntimeSupport vocabulary (4 terms) — defined topology contract
- TopologyBuilder contracts (3 enums, 10 terms)
- IBG Body Grid (4 enums, 30+ terms) — sandbox/pre-governance
- IBG Variant Grammar (4 enums, 40+ terms) — sandbox/pre-governance
- Morphology Harvest (2 enums, 13 terms) — sandbox/staging

**IBG Sandbox Pressure:**
- 72 terms across 12 vocabularies
- Constitutional status: unratified
- Semantic pressure: HIGH

### Acoustics (Complete)

- MeasurementArchive vocabulary (6 terms) — observational preservation
- AcousticState vocabulary (9 terms) — estimate/measurement separation
- MeasuredResponse vocabulary (9 terms) — observed values
- TapTone Manifest vocabulary (schema pins) — import contract
- RMOS Pipeline vocabulary (18 terms) — risk/operation state

**Observational Discipline Pattern:**
- Explicit estimate vs measurement separation
- Mandatory assumptions and confidence
- Hard invariant: `observationalOnly: true`

---

## Cross-Reference Status

### lifecycle_registry.json

| Status | Count |
|--------|-------|
| CAM terms in registry | 3 |
| CAM terms not in registry | 8+ |
| Collision candidates | 4 |

### semantic_registry.json

| Status | Count |
|--------|-------|
| CAM concepts in registry | 4 |
| CAM concepts not in registry | 3+ |

### authority_chain_registry.json

| Status | Count |
|--------|-------|
| CAM chains declared | 0 |
| CAM chains needed | 1+ |

---

## C2 Handoff Candidates

Based on C1 findings, the following require C2 reconciliation:

### High Priority

1. **Geometry authority chain** — undeclared in CAM runtime
2. **`unsupported` vocabulary mapping** — CAM ↔ Topology ↔ CadSemantics
3. **Translator lifecycle alignment** — CAM ↔ Governance
4. **IBG sandbox constitutional review** — 72 terms in pre-governance state, high pressure
5. **Zone boundary governance** — IBG Y-ranges becoming implicit authority

### Medium Priority

4. **CamGate consolidation** — 3 duplicate definitions
5. **MaterialType disambiguation** — 3 conflicting definitions
6. **Validation gate mapping** — green/yellow/red ↔ blocking/warning

### Low Priority

7. **Provenance format formalization**
8. **Artifact type extensibility**

---

## Next Steps

1. ~~Complete `C1_GEOMETRY_TOPOLOGY_INVENTORY.md`~~ ✓ Done
2. ~~Complete `C1_ACOUSTICS_INVENTORY.md`~~ ✓ Done
3. ~~Complete `C1_GOVERNANCE_INVENTORY.md`~~ ✓ Done
4. ~~Create `C1_STRATEGIC_FINDINGS.md`~~ ✓ Done — ontology emergence synthesis
5. ~~Create `IBG_SANDBOX_SEMANTIC_CLASSIFICATION.md`~~ ✓ Done — sandbox pressure surface
6. ~~Create `C1_FREEZE_PREPARATION.md`~~ ✓ Done — observational state frozen
7. ~~Inventory export/serialization~~ Deferred to C2 scope (covered in existing inventories)
8. ~~Begin C2 arbitration planning~~ ✓ Done — C2_CONSTITUTIONAL_FEDERALISM_HANDOFF.md

**C1 PHASE COMPLETE — FROZEN**

---

## C2 Arbitration Status

| Packet | Status | Next Action |
|--------|--------|-------------|
| C2-A | **RATIFIED** (2026-05-18) | Complete — proceed to C2-D |
| C2-B | Not started | Topology namespace arbitration |
| C2-C | Not started | IBG federation planning (deferred) |
| C2-D | **NEXT** | Continuity constitutional integration |
| C2-E | Queued | Export propagation continuity |

**C2-A Key Decisions:**
- IBG zones: `sandbox_operational_partition` (visible, not governed)
- Vectorizer: Included as `derived_geometry_consumer`
- 2a/2b/2c tiers: Approved provisionally (operational, not immutable)

---

## Related Documents

### C1 Inventories
- `docs/governance/coordination/C1_RUNTIME_CAM_INVENTORY.md`
- `docs/governance/coordination/C1_GEOMETRY_TOPOLOGY_INVENTORY.md`
- `docs/governance/coordination/C1_ACOUSTICS_INVENTORY.md`
- `docs/governance/coordination/C1_GOVERNANCE_INVENTORY.md`

### C1 Synthesis
- `docs/governance/coordination/C1_STRATEGIC_FINDINGS.md`
- `docs/governance/coordination/IBG_SANDBOX_SEMANTIC_CLASSIFICATION.md`
- `docs/governance/coordination/SEMANTIC_COLLISION_LOG.md`
- `docs/governance/coordination/RUNTIME_ASSUMPTION_INVENTORY.md`
- `docs/governance/coordination/C1_FREEZE_PREPARATION.md`

### C2 Arbitration
- `docs/handoffs/C2_CONSTITUTIONAL_FEDERALISM_HANDOFF.md`
- `docs/governance/coordination/C2A_GEOMETRY_AUTHORITY_PACKET.md` — **RATIFIED**
- `docs/governance/coordination/GAMS_GEOMETRY_AUTHORITY_MAPPING_SPEC.md` — coordination spec mapping C2 geometry authority distinctions to implementation roles; does not decide geometry-origin authority
- `docs/governance/coordination/GEOMETRY_OWNERSHIP_TOPOLOGY.md` (T1)
- `docs/governance/coordination/RUNTIME_GEOMETRY_BOUNDARY_MAP.md` (T2)
- `docs/governance/coordination/EXPORT_GEOMETRY_AUTHORITY_REVIEW.md` (T5)

### Governance Infrastructure
- `docs/governance/ontology/lifecycle_registry.json`
- `docs/governance/ontology/semantic_registry.json`
- `docs/governance/ontology/authority_chain_registry.json`
- `docs/governance/ontology/ontology_alias_registry.json`
- `docs/governance/ontology/ontology_ci_policy.json`

### Reference
- `docs/handoffs/MRP_5K_ONTOLOGY_GOVERNANCE_CI_INTEGRATION.md`
- `docs/architecture/MEASUREMENT_ARCHIVE_ARCHITECTURE.md`
