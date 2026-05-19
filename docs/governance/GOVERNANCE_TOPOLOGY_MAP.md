# Governance Topology Map

**Date:** 2026-05-15 (updated from 2026-05-12)  
**Status:** RECONCILED (CAM-6J)  
**Purpose:** Inventory and map all governance systems in luthiers-toolbox

**Reconciliation:** CAM-6J verified topology accuracy. See `GOVERNANCE_RECONCILIATION_PLAN.md` for consolidation strategy.

---

## Governance System Inventory

The repository contains **7 distinct governance systems** operating across different domains.

---

## 1. RMOS 2.0 (Rosette Manufacturing Operating System)

**Primary Documents:**
- `docs/canonical/governance/RMOS_2.0_Specification.md`
- `docs/canonical/governance/GOVERNANCE.md`
- `docs/RMOS_CONCEPTS_GUIDE.md`
- `docs/cam/safety-rmos.md`

**Scope:** Manufacturing feasibility, toolpath generation, run artifacts, audit trails

**Key Concepts:**
| Concept | Definition |
|---------|------------|
| Risk Levels | GREEN (safe), YELLOW (review), RED (blocked) |
| Run ID | Unique identifier per manufacturing run |
| Operator Pack | ZIP bundle with G-code, DXF, manifest, feasibility |
| Content-Addressed Storage | SHA256 hash-based artifact storage |
| Feasibility Rules | F001-F029 safety rule set |

**Subsystems:**
1. Material & Tool Models
2. Calculator Layer (Physics Engine)
3. Feasibility Scoring Layer
4. Geometry Engine (Shapely + ML)
5. Toolpath Engine (CAM_N16)
6. BOM / Tiling / Glue-Up Planner

**Registries:**
- `services/api/app/rmos/engines/registry.py`
- `services/api/app/rmos/feasibility/rule_registry.py`

**Authority Claim:** "RMOS is the Manufacturing Brain of the ToolBox"

---

## 2. CAM Governed Export Architecture (6A Chain)

**Primary Documents:**
- `docs/architecture/CAM_GOVERNED_EXPORT_ARCHITECTURE.md`
- `docs/architecture/CAM_EXPORT_LIFECYCLE.md`
- `docs/architecture/CAM_EXPORT_OBJECT_MODEL.md`
- `docs/architecture/CAM_POSTPROCESSOR_BOUNDARY.md`
- `docs/architecture/CAM_EXPORT_GOVERNANCE_POLICY.md`
- `docs/architecture/CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md`

**Scope:** 7-layer export pipeline from geometry to machine output

**Layer Architecture:**
| Layer | Name | Classification | Status |
|-------|------|----------------|--------|
| 1 | Geometry | NEUTRAL | Complete |
| 2 | Toolpath | NEUTRAL | Complete |
| 3 | Governed Preview | PREVIEW | Complete |
| 4 | Export Object | EXPORT | Architecture defined |
| 5 | RMOS Persistence | GOVERNANCE | Partial |
| 6 | Postprocessor | MACHINE OUTPUT | Interface defined |
| 7 | Machine Output | MACHINE OUTPUT | Not implemented |

**Classifications:**
- NEUTRAL — No governance requirements
- PREVIEW — Human-inspection oriented, gate-evaluated
- EXPORT — Portable manufacturing representation
- GOVERNANCE — System artifacts and tracking
- MACHINE OUTPUT — Machine-executable representation

**Manifests:**
- `docs/architecture/governed_export_manifest.json`
- `docs/architecture/cam_preview_standard_manifest.json`
- `docs/architecture/cam_machine_output_manifest.json`

**Authority Claim:** Canonical export model connecting preview, export, and machine output

---

## 3. MRP Governance Enforcement (Morphology Reconstruction Platform)

**Primary Documents:**
- `docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md`
- `docs/governance/BLUEPRINT_READER_PROTECTION_RULES.md`
- `docs/governance/IBG_ROLE_DEFINITION.md`

**Scope:** Protected systems, pre-commit enforcement, governance headers

**Protected Systems:**
| System ID | Protection Level | Path Count |
|-----------|------------------|------------|
| BLUEPRINT_READER_MVP | LOCKED | 7 |
| RESTORED_BASELINE_MODE | LOCKED | 2 |
| DXF_COMPAT_LAYER | LOCKED | 3 |
| IBG_CORE | LOCKED | 4 |
| MORPHOLOGY_GOVERNANCE_DOCS | STABILIZED | 1 |

**Enforcement Mechanism:**
- `docs/governance/governance_manifest.json` — Machine-readable registry
- `scripts/check_protected_paths.py` — Pre-commit hook
- `scripts/check_sprint_namespace.py` — Namespace validation
- Environment variable: `GOVERNANCE_APPROVED_CHANGE=1`

**Authority Claim:** "Protect the production MVP while evolving morphology intelligence"

---

## 4. CAM Capability Registry (6H/6I)

**Primary Documents:**
- `services/api/docs/handoffs/CAM_6H_CAPABILITY_REGISTRY_HANDOFF.md`
- `services/api/docs/handoffs/CAM_6I_POLICY_ENGINE_HANDOFF.md`

**Scope:** Operation self-description, lifecycle policy enforcement

**Code Location:**
- `services/api/app/cam/cam_operation_registry.py`
- `services/api/app/cam/cam_lifecycle_policy_engine.py`

**Exportability Classes:**
| Class | Description |
|-------|-------------|
| preview_only | Preview generation only |
| governed_export | Full export pipeline |
| translator_ready | Export + translator |
| machine_candidate | Export + translator + machine validation |

**Maturity Levels:**
| Level | Gate Behavior |
|-------|---------------|
| experimental | YELLOW warning |
| candidate | YELLOW warning |
| governed | GREEN |
| canonical | GREEN |

**Authority Claim:** "Operations are self-describing governed capabilities"

---

## 5. Foundational Governance Methodology

**Primary Documents:**
- `docs/governance/REPOSITORY_REMEDIATION_GOVERNANCE_METHODOLOGY.md`
- `docs/governance/REPOSITORY_EXPANSION_GUIDANCE_DIRECTIVE.md`

**Scope:** Canonical ontology authority, remediation methodology, expansion direction

**Key Concepts:**
| Concept | Definition |
|---------|------------|
| Architectural Thesis | What the repository fundamentally represents |
| Reconstruction Methodology | How fragmented repos evolve safely |
| Canonical Ontology Authority | Single semantic truth requirement |
| Parallel Ontology Drift | Late-stage failure pattern to prevent |

**Core Principles:**
1. One subsystem owns one kind of truth
2. Contracts are ontology (domain vocabulary)
3. Intent is separate from execution
4. Runtime cannot redefine ontology
5. Experimental systems must remain contained

**Remediation Phases:**
1. Archaeology — Reveal actual behavior
2. Instrumentation — Force assumptions observable
3. Boundary Formalization — Separate authority domains
4. Governance Layering — Prevent future collapse
5. Controlled Extension — Extend without destabilization

**Authority Claim:** "Formalized lutherie knowledge expressed as executable systems"

---

## 6. Architecture Invariants (6-Layer Placement)

**Primary Document:**
- `docs/governance/ARCHITECTURE_INVARIANTS.md`

**Scope:** Code placement rules, layer boundaries

**Layer Model:**
| Layer | Folder | Purpose |
|-------|--------|---------|
| 1 | geometry/ | Pure math functions |
| 2 | instrument_geometry/ | Instrument-specific math |
| 3 | calculators/ | Calculation orchestration |
| 4 | rmos/, saw_lab/, cam/ | Domain modules |
| 5 | services/ | Cross-domain orchestration |
| 6 | routers/ | HTTP handling only |

**Hard Rules:**
1. No math in routers (Fortran Rule)
2. No hardcoded Pi
3. Cross-domain glue goes in services/
4. Domain modules are self-contained
5. Required invariants enforced

**Enforcement:**
- `tests/test_route_governance.py`

**Authority Claim:** "The source of truth for code placement"

---

## 7. Feature Parity Migration Policy

**Primary Document:**
- `FEATURE_PARITY_MIGRATION_POLICY.md`

**Scope:** Migration governance, canonical vs shell status

**Migration States:**
| State | Name | Description |
|-------|------|-------------|
| 1 | Canonical | Trusted production implementation |
| 2 | Mounted Legacy | Legacy embedded in new workspace |
| 3 | Beta Consolidation Shell | Workspace exists, parity incomplete |
| 4 | Parity Verified | Replacement may proceed |

**Parity Requirements:**
1. Functional parity
2. Export parity
3. Visualization parity
4. Workflow parity
5. Preset parity
6. Mathematical parity
7. API parity
8. Runtime verification
9. Regression testing

**Authority Claim:** "No existing canonical implementation may be removed until parity is verified"

---

## Additional Governance Documents

| Document | Domain |
|----------|--------|
| `REPOSITORY_REMEDIATION_GOVERNANCE_METHODOLOGY.md` | Foundational methodology |
| `REPOSITORY_EXPANSION_GUIDANCE_DIRECTIVE.md` | Expansion direction |
| `INSTRUMENT_DATA_STORAGE_AUDIT.md` | Instrument data topology audit |
| `ontology/INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` | Dimensional semantics (DRAFT) |
| `ontology/PROMOTION_REVIEW_MANIFEST_V1.md` | Tier 3→2 review contract (DRAFT) |
| `SPRINT_NAMESPACE_STANDARD.md` | Sprint naming conventions |
| `SEMANTIC_GEOMETRY_CONTINUITY.md` | Geometry semantics |
| `THREE_LOOP_ARCHITECTURE_REFRAMED.md` | Vectorizer feedback loops |
| `AI_SANDBOX_EXECUTION_AUTHORITY_CONTRACT_v1.md` | AI boundary |
| `SECURITY_TRUST_BOUNDARY_CONTRACT_v1.md` | Security boundaries |
| `SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md` | Feasibility enforcement |
| `ART_STUDIO_SCOPE_GOVERNANCE_v1.md` | Art Studio boundaries |
| `FENCE_ARCHITECTURE.md` | Fence layer governance |

---

## Registry/Manifest Inventory

| File | Purpose | Owner System |
|------|---------|--------------|
| `governance_manifest.json` | Protected systems | MRP |
| `governed_export_manifest.json` | Export architecture | CAM 6A |
| `cam_preview_standard_manifest.json` | Preview standards | CAM 5C |
| `cam_machine_output_manifest.json` | Machine output | CAM |
| `rosette_cam_route_manifest.json` | Rosette routes | RMOS |
| `rosette_governance_gate_manifest.json` | Rosette gates | RMOS |
| `tests/regression_corpus/manifest.json` | Regression artifacts | MRP |
| `benchmark_manifest.json` | Benchmarks | Vectorizer |

---

## Code Registry Inventory

| File | Purpose |
|------|---------|
| `cam_operation_registry.py` | CAM operation capabilities |
| `dxf_registry.py` | DXF generator registry |
| `rule_registry.py` | RMOS feasibility rules |
| `engines/registry.py` | RMOS engine registry |
| `cam_profile_registry.py` | CAM machine profiles |
| `saw_blade_registry.py` | Saw blade catalog |
| `tools/registry.py` | Tool library |
| `preset_registry.py` | Rosette presets |
| `store_registry.py` | Store registry |
| `endpoint_registry.py` | Endpoint governance |
| `metrics_registry.py` | Metrics collection |

---

*Governance Topology Map — 2026-05-07*
