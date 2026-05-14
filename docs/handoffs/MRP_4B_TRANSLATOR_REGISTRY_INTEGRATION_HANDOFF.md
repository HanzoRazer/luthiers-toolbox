# MRP-4B: Translator Registry Integration & Legacy Export Migration Map

**Date:** 2026-05-14  
**Sprint:** MRP-4B  
**Status:** COMPLETE

---

## Executive Summary

MRP-4B inventories all DXF/SVG/G-code export paths in the codebase, classifies them by serialization ownership, and establishes migration governance toward the MRP-4A translator architecture.

**42 export paths identified. 4 governed. 20 compliant. 14 require migration. 4 exempted.**

---

## Deliverables

### 1. Export Path Migration Matrix

**Location:** `docs/governance/EXPORT_PATH_MIGRATION_MATRIX.md`

Complete inventory of all export paths with:
- Classification (GOVERNED, COMPLIANT, LEGACY, EXEMPT)
- Migration priority (P1-P4)
- Target format and endpoint

**Statistics:**
| Category | Count |
|----------|-------|
| Governed (MRP-4A) | 4 |
| Compliant (dxf_writer/compat) | 20 |
| Legacy (needs migration) | 14 |
| Exempt (authorized legacy) | 4 |

### 2. Legacy Export Exemption Policy

**Location:** `docs/governance/LEGACY_EXPORT_EXEMPTION_POLICY.md`

Defines four exemption categories:
1. **Fallback Safety Net** — ASCII R12 fallback when ezdxf unavailable
2. **Legacy API Compatibility** — backward-compat endpoints with sunset dates
3. **Development/Test Tooling** — CLI test harnesses
4. **Archived Code** — historical reference only

**Currently Exempted:**
- `app.exports.dxf_helpers` — fallback_safety_net
- `app.routers.legacy_dxf_exports_router` — legacy_api_compat (sunset: 2026-09-01)
- `scripts.generate_smart_guitar_v3_dxf` — dev_tooling
- `app.toolpath.dxf_io_legacy` — archived

### 3. Translator Onboarding Rules

**Location:** `docs/governance/TRANSLATOR_ONBOARDING_RULES.md`

8-step process for adding new translators:
1. Create translator module
2. Define capabilities
3. Register with registry
4. Add target mapping
5. Update package exports
6. Write tests
7. Update documentation
8. Add API endpoint (optional)

Includes complete implementation template with gate enforcement and provenance.

### 4. Governance Visibility Utilities

**Location:** `scripts/governance/`

| Script | Purpose |
|--------|---------|
| `list_translators.py` | List registered translators with capabilities |
| `list_legacy_exemptions.py` | Scan for LEGACY_EXEMPT headers |

**Usage:**
```bash
# List all translators
python scripts/governance/list_translators.py

# List governed translators only
python scripts/governance/list_translators.py --governed-only

# Filter by target format
python scripts/governance/list_translators.py --target dxf

# JSON output
python scripts/governance/list_translators.py --json

# List exemptions
python scripts/governance/list_legacy_exemptions.py

# Validate exemptions against policy
python scripts/governance/list_legacy_exemptions.py --validate
```

---

## Migration Priority Summary

### P1 — Direct ezdxf.new() in Production (Target: MRP-5A)

These modules use direct ezdxf.new() calls and must migrate first:

| Module | Issue |
|--------|-------|
| `smart_guitar_dxf.py` | Production endpoint |
| `archtop_floating_bridge.py` | Production endpoint |
| `spiral_geometry.py` | Production endpoint |
| `edge_to_dxf_router.py` | Vectorizer pipeline |
| `phase2_router.py` | Vectorizer pipeline |
| `phase3_router.py` | Vectorizer pipeline |

### P2 — Compliant Ready for Upgrade (Target: MRP-5B)

These modules use dxf_writer/dxf_compat and can migrate to translator consumption:

| Module | Current |
|--------|---------|
| `headstock/dxf_export.py` | dxf_compat |
| `archtop_contour_generator.py` | dxf_compat |
| `inlay_calc.py` | dxf_compat |
| `contour_reconstruction.py` | dxf_compat |

---

## Canonical Export Routing Model

```
User Request
    │
    ├── Governed Path (MRP-4A)
    │       │
    │       └── POST /api/translate/{target}
    │               │
    │               └── resolve_translator(target, version)
    │                       │
    │                       └── translator.translate(export_object)
    │                               │
    │                               └── TranslatorResult → Response
    │
    ├── Compliant Path (Migration-Ready)
    │       │
    │       └── [Endpoint] → DxfWriter → dxf_compat → ezdxf
    │
    └── Legacy Path (Requires Migration)
            │
            └── [Endpoint] → ezdxf.new() (DIRECT)
```

**Target State:** All export paths flow through `/api/translate/{target}` or translator consumption.

---

## Governance Invariants

| Invariant | Status |
|-----------|--------|
| No new ezdxf.new() calls outside dxf_compat | ENFORCED |
| All translators registered in registry | VERIFIED |
| Red gate blocks all translation | VERIFIED |
| Exemptions documented in policy | VERIFIED |
| Migration priorities assigned | COMPLETE |

---

## Files Created

| File | Purpose |
|------|---------|
| `docs/governance/EXPORT_PATH_MIGRATION_MATRIX.md` | Full export path inventory |
| `docs/governance/LEGACY_EXPORT_EXEMPTION_POLICY.md` | Exemption criteria and process |
| `docs/governance/TRANSLATOR_ONBOARDING_RULES.md` | Adding new translators |
| `scripts/governance/list_translators.py` | Registry visibility utility |
| `scripts/governance/list_legacy_exemptions.py` | Exemption scanning utility |

---

## Next Steps (MRP-5A+)

1. **MRP-5A**: Migrate P1 legacy modules to dxf_compat
2. **MRP-5B**: Upgrade P2 compliant modules to translator consumption
3. **MRP-6A**: Address vectorizer pipeline (blueprint readers)
4. **MRP-6B**: Sunset legacy API endpoints per policy

---

## References

- `docs/handoffs/MRP_4A_MULTI_TARGET_TRANSLATOR_HANDOFF.md`
- `docs/governance/TRANSLATOR_LAYER_RULES.md`
- `docs/governance/MULTI_TARGET_TRANSLATOR_POLICY.md`
- `CLAUDE.md` — DXF output standard section

---

*MRP-4B complete. Export paths inventoried. Migration governance established.*
