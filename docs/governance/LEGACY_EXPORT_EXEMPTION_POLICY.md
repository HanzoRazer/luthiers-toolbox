# Legacy Export Exemption Policy

**Date:** 2026-05-14  
**Sprint:** MRP-4B  
**Status:** ACTIVE

---

## Purpose

Defines criteria and process for exempting legacy DXF export paths from migration to the governed translator architecture (MRP-4A).

---

## Exemption Criteria

A legacy export path may be exempted from migration if it meets ONE OR MORE of the following criteria:

### 1. Fallback Safety Net

The module serves as a fallback when governed translators are unavailable.

**Example:** `app.exports.dxf_helpers` provides ASCII R12 fallback when ezdxf fails to load.

**Requirement:** Must be invoked only when primary path fails.

### 2. Legacy API Compatibility

The endpoint exists solely for backward compatibility with external consumers.

**Example:** `app.routers.legacy_dxf_exports_router` maintains the original `/exports/*` API surface.

**Requirement:** Must emit deprecation warnings. Must have documented sunset date.

### 3. Development/Test Tooling

The module is used only for development, testing, or debugging.

**Example:** `scripts/generate_smart_guitar_v3_dxf.py` is a CLI test harness.

**Requirement:** Must not be reachable from production API routes.

### 4. Archived Code

The module is in `archive/` directory or marked with `STATUS: ARCHIVED` governance header.

**Example:** `app.toolpath.dxf_io_legacy` is retained for historical reference.

**Requirement:** Must not be imported by production code.

---

## Exemption Process

### Step 1: Declaration

Add governance header to the exempted module:

```python
# GOVERNANCE:
# SYSTEM: DXF_COMPAT_LAYER
# STATUS: LEGACY_EXEMPT
# EXEMPTION: {fallback_safety_net|legacy_api_compat|dev_tooling|archived}
# REASON: {one-line justification}
# SUNSET: {YYYY-MM-DD or INDEFINITE}
# DOC: docs/governance/LEGACY_EXPORT_EXEMPTION_POLICY.md
```

### Step 2: Matrix Registration

Add entry to `docs/governance/EXPORT_PATH_MIGRATION_MATRIX.md` with `EXEMPT` status.

### Step 3: Review Gate

Exemptions for production endpoints require governance approval (PR review by maintainer).

---

## Currently Exempted Modules

| Module | Exemption Type | Sunset Date | Rationale |
|--------|----------------|-------------|-----------|
| `app.exports.dxf_helpers` | fallback_safety_net | INDEFINITE | ASCII R12 fallback when ezdxf unavailable |
| `app.routers.legacy_dxf_exports_router` | legacy_api_compat | 2026-09-01 | Original API surface for external consumers |
| `scripts.generate_smart_guitar_v3_dxf` | dev_tooling | INDEFINITE | CLI test harness |
| `app.toolpath.dxf_io_legacy` | archived | INDEFINITE | Historical reference only |

---

## Non-Exempt Modules (Migration Required)

The following modules use direct `ezdxf.new()` calls and are NOT exempt:

| Module | Migration Priority | Blocking Issue |
|--------|-------------------|----------------|
| `app.instrument_geometry.body.smart_guitar_dxf` | P1 | Production endpoint |
| `app.instrument_geometry.bridge.archtop_floating_bridge` | P1 | Production endpoint |
| `app.instrument_geometry.soundhole.spiral_geometry` | P1 | Production endpoint |
| `app.routers.blueprint.edge_to_dxf_router` | P1 | Vectorizer pipeline |

These modules must migrate to the translator architecture or use `dxf_writer.DxfWriter`.

---

## Sunset Protocol

When a sunset date arrives:

1. Remove exemption header from module
2. Update migration matrix to `DEPRECATED`
3. Add route deprecation warning if API endpoint
4. Schedule removal in next major version

---

## Governance Check

```bash
# List all exempted modules
python scripts/governance/list_legacy_exemptions.py

# Validate exemption headers match matrix
python scripts/governance/validate_exemption_matrix.py
```

---

## References

- `docs/governance/EXPORT_PATH_MIGRATION_MATRIX.md` — full inventory
- `docs/governance/TRANSLATOR_LAYER_RULES.md` — translator governance
- `docs/handoffs/MRP_4A_MULTI_TARGET_TRANSLATOR_HANDOFF.md` — architecture
