# Sprint Namespace Standard

**Status:** ACTIVE GOVERNANCE  
**Effective:** 2026-05-11

---

## Purpose

Standardize sprint ticket and audit naming to prevent namespace collisions and enable traceability.

---

## Namespace Registry

| Prefix | Domain | Owner |
|--------|--------|-------|
| `VECTOR` | Blueprint Reader vectorizer | Frozen (Ross) |
| `IBG` | Image Body Generator | Production |
| `BOE` | Body Outline Editor | Production |
| `DXF` | DXF compliance and export | Production |
| `CAM` | CAM pipeline and toolpaths | Production |
| `RMOS` | Router Machine OS | Production |
| `SPIRAL` | Spiral soundhole system | Production |
| `MRP` | Morphology Reconstruction Platform | Governance |

---

## Naming Convention

```
{PREFIX}-{NUMBER}{SUFFIX}: {Description}
```

### Examples

| Ticket | Description |
|--------|-------------|
| `VECTOR-1A` | DXF compliance remediation |
| `VECTOR-1B` | Loop 2 provenance audit |
| `VECTOR-2A` | Loop 2 implementation (future) |
| `IBG-1` | IBG functional assessment |
| `DXF-1` | dxf_compat enforcement |
| `CAM-1` | Nut slot preview |
| `CAM-6A` | Governed export architecture |

---

## Registered Sprint Chains

Sprint chains are multi-phase efforts with sequential deliverables.

| Chain | Prefix | Range | Description |
|-------|--------|-------|-------------|
| CAM Governed Export | `CAM-6` | 6A-6J | Governed export pipeline, lifecycle orchestration |

### CAM-6 Chain (2026-05)

| Sprint | Deliverable |
|--------|-------------|
| `CAM-6A` | Governed Export Architecture |
| `CAM-6B` | Export Object Prototype |
| `CAM-6C` | Postprocessor Boundary |
| `CAM-6D` | DXF Translator Alignment |
| `CAM-6E` | Export Lifecycle Orchestrator |
| `CAM-6F` | RMOS Export Object Integration |
| `CAM-6G` | Drilling Lifecycle Integration |
| `CAM-6H` | Capability Registry |
| `CAM-6I` | Policy Engine |
| `CAM-6J` | Governance Reconciliation |

---

## Suffix Semantics

| Suffix | Meaning |
|--------|---------|
| None | Primary sprint work |
| `A` | First sub-task or audit |
| `B` | Second sub-task or audit |
| `C` | Third sub-task or audit |

---

## Handoff Document Naming

```
{PREFIX}_{NUMBER}{SUFFIX}_{DESCRIPTION}_{DATE}.md
```

### Examples

| File | Sprint |
|------|--------|
| `VECTOR_1A_DXF_COMPLIANCE_CLOSEOUT.md` | VECTOR-1A |
| `VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md` | VECTOR-1B |
| `IBG_FUNCTIONAL_CAPABILITY_ASSESSMENT_2026-05-11.md` | IBG-1 |

---

## Audit Document Naming

```
{DOMAIN}_{AUDIT_TYPE}_AUDIT_{DATE}.md
```

### Examples

| File | Domain |
|------|--------|
| `VECTORIZER_GEOMETRY_AUDIT_HANDOFF_2026-05-11.md` | VECTOR |
| `CAM_SIMULATION_AUDIT_2026-05-06.md` | CAM |

---

## Governance Document Naming

```
{CONCEPT}_STANDARD.md
{CONCEPT}_RULES.md
{CONCEPT}_DEFINITION.md
```

No date suffix for governance documents — they are living documents.

---

## Collision Prevention

Before creating new prefix:

1. Check this registry
2. If prefix exists, use suffix increment
3. If new domain, add to registry first
4. Document in commit message

---

*Sprint namespace standard. Traceability over convenience.*
