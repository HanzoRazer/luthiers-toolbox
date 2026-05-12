# Manifest Index

**Status:** ACTIVE REGISTRY  
**Date:** 2026-05-12  
**Purpose:** Central registry of all governance manifests in the repository

---

## Overview

This index tracks all governance manifests to prevent duplication and establish clear ownership boundaries. Before creating a new manifest, check this index for existing coverage.

---

## Manifest Registry

| Manifest | Location | Domain | Purpose | Version | Owner System |
|----------|----------|--------|---------|---------|--------------|
| governance_manifest.json | docs/governance/ | MRP | Protected systems, paths, approval mechanism | 1.0.0 | MRP |
| governed_export_manifest.json | docs/architecture/ | CAM | Export architecture layers, classifications, boundaries | 1.0.0 | CAM 6A |
| cam_preview_standard_manifest.json | docs/architecture/ | CAM | Governed preview operations, response schemas | 1.0.0 | CAM 5C |
| cam_machine_output_manifest.json | docs/architecture/ | CAM | Machine output governance, quarantine status | 1.0.0 | CAM |
| rosette_cam_route_manifest.json | docs/architecture/ | CAM | Rosette CAM routes, ownership | 1.0.0 | RMOS |
| rosette_governance_gate_manifest.json | docs/architecture/ | CAM | Rosette governance gates | 1.0.0 | RMOS |
| regression_corpus/manifest.json | tests/ | MRP | Regression test artifacts | 1.0.0 | MRP |
| benchmark_manifest.json | root | Vectorizer | Vectorizer benchmarks | 1.0.0 | VECTOR |

---

## Manifest Relationships

```
governance_manifest.json (MRP)
├── Protects: Blueprint Reader, IBG, DXF Compat
├── Enforced by: check_protected_paths.py
└── Cross-refs: None

governed_export_manifest.json (CAM 6A)
├── Defines: 7-layer export architecture
├── Cross-refs: cam_preview_standard_manifest.json
├── Cross-refs: cam_machine_output_manifest.json
└── Depends on: governance_manifest.json (DXF Compat protection)

cam_preview_standard_manifest.json (CAM 5C)
├── Defines: Governed preview operations
├── Parent: governed_export_manifest.json
└── Cross-refs: rosette_cam_route_manifest.json

rosette_cam_route_manifest.json (RMOS)
├── Defines: Rosette-specific CAM routes
├── Cross-refs: rosette_governance_gate_manifest.json
└── Note: Historical RMOS origin, now CAM-aligned
```

---

## Domain Ownership

| Domain | Primary Manifests | Secondary Manifests |
|--------|-------------------|---------------------|
| MRP | governance_manifest.json | regression_corpus/manifest.json |
| CAM | governed_export_manifest.json | cam_preview_standard_manifest.json, cam_machine_output_manifest.json |
| RMOS | rosette_cam_route_manifest.json | rosette_governance_gate_manifest.json |
| VECTOR | benchmark_manifest.json | - |

---

## Adding New Manifest

### Pre-Flight Check

Before creating a new manifest:

1. **Check this index** — Does existing manifest cover your need?
2. **Check domain ownership** — Which system should own this?
3. **Check for overlap** — Will this duplicate existing governance?

### Creation Process

1. Create manifest with standard schema header:

```json
{
  "$schema": "manifest-schema-v1",
  "manifest_version": "1.0.0",
  "manifest_type": "governance | capability | routing | regression",
  "effective_date": "YYYY-MM-DD",
  "owner_system": "MRP | CAM | RMOS | VECTOR",
  "governance_tier": 1 | 2 | 3,
  
  "entries": [],
  
  "cross_references": []
}
```

2. Add entry to this index
3. Add cross-references to related manifests
4. Update enforcement scripts if needed
5. Document in sprint handoff

### Manifest Type Definitions

| Type | Purpose | Example |
|------|---------|---------|
| governance | Protected systems, approval mechanisms | governance_manifest.json |
| capability | Operation capabilities, maturity | (code registry, not JSON) |
| routing | Route ownership, endpoint mapping | rosette_cam_route_manifest.json |
| regression | Test artifacts, baselines | regression_corpus/manifest.json |
| architecture | Layer definitions, boundaries | governed_export_manifest.json |

---

## Schema Evolution

### Version Numbering

- **Major (1.0.0 → 2.0.0):** Breaking schema changes
- **Minor (1.0.0 → 1.1.0):** New optional fields
- **Patch (1.0.0 → 1.0.1):** Documentation, no schema change

### Migration Rules

1. New required fields require major version bump
2. Old manifests must remain parseable by new readers
3. Document migration in sprint handoff
4. Update all cross-referencing manifests

---

## Validation

### Manual Validation

```bash
# Validate JSON syntax
python -m json.tool docs/governance/governance_manifest.json > /dev/null

# Validate protected paths script can load manifest
python scripts/check_protected_paths.py
```

### Automated Validation (Future)

```python
# TODO: Create scripts/check_manifest_index.py
# - Verify all manifests listed in index exist
# - Verify all manifests in repo are listed in index
# - Verify cross-references are bidirectional
# - Verify version numbers are consistent
```

---

## Anti-Patterns

### DON'T: Create Overlapping Manifests

```text
BAD: Creating "dxf_export_manifest.json" when governed_export_manifest.json
     already covers DXF export governance.
```

### DON'T: Skip Index Update

```text
BAD: Creating new manifest without adding to MANIFEST_INDEX.md.
     This leads to governance drift and discovery problems.
```

### DON'T: Cross Domain Without Explicit Reference

```text
BAD: MRP manifest referencing CAM routes without documenting cross-reference.
     Creates hidden dependencies.
```

---

## Governance Tier Mapping

| Tier | Manifests | Authority |
|------|-----------|-----------|
| Tier 1 (Structural) | governance_manifest.json | Repository-wide code organization |
| Tier 2 (Domain) | governed_export_manifest.json, rosette_cam_route_manifest.json | Domain-specific governance |
| Tier 3 (Operational) | cam_preview_standard_manifest.json, cam_machine_output_manifest.json | Runtime behavior policies |

---

*Manifest Index — Maintained as part of Governance Remediation*
